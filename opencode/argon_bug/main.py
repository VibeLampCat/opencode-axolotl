import argparse
import json
import os
import socket
import sys
import time

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from argon_bug.config import UDP_HOST, UDP_PORT, BugState
from argon_bug.udp_listener import ArgonUDPListener
from argon_bug.widget import ArgonBugWidget


def send_test_packet(state: str, detail: str = ""):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        msg = json.dumps({"state": state, "detail": detail}).encode("utf-8")
        sock.sendto(msg, (UDP_HOST, UDP_PORT))
    finally:
        sock.close()


def run_self_test(widget: ArgonBugWidget, app: QApplication):
    # 9-state full preview sequence every 400 ms
    states = [
        ("IDLE", "1/9 IDLE: Чай / Tea"),
        ("THINKING", "2/9 THINKING: Argon думает"),
        ("SEARCHING", "3/9 SEARCHING: Читает доки 🔍"),
        ("WORKING", "4/9 WORKING: Flash пилит код ⚡"),
        ("TESTING", "5/9 TESTING: В очках гоняет тесты 🧪"),
        ("ASKING", "6/9 ASKING: Вопрос / Разрешение ❓"),
        ("SUCCESS", "7/9 SUCCESS: Салют и радость 🎉"),
        ("ERROR", "8/9 ERROR: Конфуз / Ошибка 💧"),
        ("LIMIT", "9/9 LIMIT: Спит / Rate Limit 💤"),
    ]

    for idx, (s, d) in enumerate(states):
        QTimer.singleShot(150 + idx * 400, lambda st=s, dt=d: send_test_packet(st, dt))

    # Quit cleanly after test
    QTimer.singleShot(150 + len(states) * 400 + 400, lambda: (widget.close(), app.quit()))


def main():
    parser = argparse.ArgumentParser(description="ArgonBug Desktop Mascot for OpenCode v2.2.7")
    parser.add_argument("--parent-pid", type=int, default=None, help="OpenCode parent process PID to watch")
    parser.add_argument("--lang", type=str, choices=["ru", "en"], default=None, help="Initial UI language (ru/en)")
    parser.add_argument("--test-run", action="store_true", help="Run self-test sequence of all 9 states and exit")
    args = parser.parse_args()

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    listener = ArgonUDPListener(parent_pid=args.parent_pid)
    listener.start()

    widget = ArgonBugWidget(listener=listener, initial_lang=args.lang)
    widget.show()

    if args.test_run:
        print("[ArgonBug] Starting 9-state self-test sequence...")
        run_self_test(widget, app)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
