import json
import socket
import time
import ctypes
from typing import Optional
from PySide6.QtCore import QThread, Signal
from argon_bug.config import UDP_HOST, UDP_PORT, BugState


def is_pid_alive(pid: int) -> bool:
    if pid <= 0:
        return True
    try:
        import sys
        if sys.platform == "win32":
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            STILL_ACTIVE = 259
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            exit_code = ctypes.c_ulong()
            success = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
            ctypes.windll.kernel32.CloseHandle(handle)
            if not success:
                return False
            return exit_code.value == STILL_ACTIVE
        else:
            import os
            os.kill(pid, 0)
            return True
    except (OSError, Exception):
        return False


class ArgonUDPListener(QThread):
    state_received = Signal(str, str)  # (state, detail)
    parent_exited = Signal()

    def __init__(self, parent_pid: Optional[int] = None, idle_timeout: float = 120.0):
        super().__init__()
        self.parent_pid = parent_pid
        self.idle_timeout = idle_timeout
        self.running = True
        self.last_packet_time = time.time()
        self.last_pid_check_time = time.time()
        self.is_manual_override = False
        self.current_state = BugState.IDLE

    def set_manual_override(self, override: bool):
        self.is_manual_override = override

    def set_current_state(self, state: str):
        try:
            self.current_state = BugState(state)
        except ValueError:
            pass

    def stop(self):
        self.running = False
        self.wait(1000)

    def run(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        except Exception:
            pass

        try:
            sock.bind((UDP_HOST, UDP_PORT))
        except Exception as e:
            print(f"[ArgonUDPListener] Failed to bind {UDP_HOST}:{UDP_PORT}: {e}")
            return

        sock.settimeout(0.2)

        while self.running:
            now = time.time()

            # Parent PID watchdog check every 2 seconds
            if self.parent_pid and (now - self.last_pid_check_time >= 2.0):
                self.last_pid_check_time = now
                if not is_pid_alive(self.parent_pid):
                    print(f"[ArgonUDPListener] Parent PID {self.parent_pid} has exited.")
                    self.parent_exited.emit()
                    break

            # Inactivity timeout (120s) -> return to IDLE
            if (
                not self.is_manual_override
                and self.current_state not in (BugState.IDLE, BugState.LIMIT)
                and (now - self.last_packet_time >= self.idle_timeout)
            ):
                self.current_state = BugState.IDLE
                self.state_received.emit(BugState.IDLE.value, "")
                self.last_packet_time = now

            try:
                data, _ = sock.recvfrom(4096)
                if not data:
                    continue

                self.last_packet_time = time.time()
                try:
                    payload = json.loads(data.decode("utf-8"))
                except Exception:
                    continue

                state_raw = payload.get("state", "").strip().upper()
                detail = payload.get("detail", "").strip()

                if state_raw == "QUIT":
                    print("[ArgonUDPListener] Received QUIT command.")
                    self.parent_exited.emit()
                    break

                if state_raw in BugState._value2member_map_:
                    self.current_state = BugState(state_raw)
                    if not self.is_manual_override:
                        self.state_received.emit(state_raw, detail)

            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    time.sleep(0.05)

        try:
            sock.close()
        except Exception:
            pass
