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
from argon_bug.config import UDP_HOST, UDP_PORT
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
    # Sequential test sequence every 500 ms
    QTimer.singleShot(200, lambda: send_test_packet("IDLE", "Тест: Пью чай"))
    QTimer.singleShot(700, lambda: send_test_packet("THINKING", "Тест: Думает Argon"))
    QTimer.singleShot(1200, lambda: send_test_packet("WORKING", "Тест: Flash пилит код!"))
    QTimer.singleShot(1700, lambda: send_test_packet("TESTING", "Тест: Запуск и тесты"))
    QTimer.singleShot(2200, lambda: send_test_packet("LIMIT", "Тест: Жук лимитает"))

    # Quit cleanly after 3 seconds
    QTimer.singleShot(3000, lambda: (widget.close(), app.quit()))


def main():
    parser = argparse.ArgumentParser(description="ArgonBug Desktop Mascot for OpenCode v2.2.7")
    parser.add_argument("--parent-pid", type=int, default=None, help="OpenCode parent process PID to watch")
    parser.add_argument("--test-run", action="store_true", help="Run 3-second smoke test and exit")
    args = parser.parse_args()

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    listener = ArgonUDPListener(parent_pid=args.parent_pid)
    listener.start()

    widget = ArgonBugWidget(listener=listener)
    widget.show()

    if args.test_run:
        print("[ArgonBug] Starting 3-second self-test sequence...")
        run_self_test(widget, app)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
