import json
import os
import socket
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QCoreApplication
from argon_bug.config import (
    UDP_HOST,
    UDP_PORT,
    BugState,
    STATE_PHRASES,
    PHRASES_RU,
    PHRASES_EN,
    detect_system_language,
    save_language_preference,
)
from argon_bug.udp_listener import is_pid_alive, ArgonUDPListener
from argon_bug.renderer import ArgonBugRenderer


class TestArgonBugSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication(sys.argv)

    def test_01_config_and_palette(self):
        """Test configuration, 9 states, and i18n dictionaries."""
        self.assertEqual(len(BugState), 9)
        for state in BugState:
            self.assertIn(state, PHRASES_RU)
            self.assertIn(state, PHRASES_EN)
            self.assertGreater(len(PHRASES_RU[state]), 0)
            self.assertGreater(len(PHRASES_EN[state]), 0)

        self.assertEqual(UDP_HOST, "127.0.0.1")
        self.assertEqual(UDP_PORT, 51515)

        # Test language detection & persistence
        lang = detect_system_language()
        self.assertIn(lang, ("ru", "en"))
        save_language_preference("en")
        self.assertEqual(detect_system_language(), "en")
        save_language_preference("ru")
        self.assertEqual(detect_system_language(), "ru")

        print("\n[OK] Test 1: Config, 9 states, RU/EN dictionaries, and language persistence verified.")

    def test_02_renderer_procedural_states(self):
        """Test procedural renderer animations, 9 states, confetti, and petting hearts."""
        renderer = ArgonBugRenderer()
        for state in BugState:
            renderer.set_state(state, f"Test detail for {state.value}")
            self.assertEqual(renderer.state, state)
            self.assertEqual(renderer.detail_text, f"Test detail for {state.value}")
            for _ in range(10):
                renderer.update_animation()

        # Check particles for WORKING state (yellow sparks)
        renderer.set_state(BugState.WORKING)
        for _ in range(20):
            renderer.update_animation()
        self.assertGreater(len(renderer.sparks), 0)

        # Check sleep Z particles for LIMIT state
        renderer.set_state(BugState.LIMIT)
        for _ in range(35):
            renderer.update_animation()
        self.assertGreater(len(renderer.sleep_zs), 0)

        # Check confetti particles for SUCCESS state
        renderer.set_state(BugState.SUCCESS)
        for _ in range(20):
            renderer.update_animation()
        self.assertGreater(len(renderer.confetti), 0)

        # Check interactive petting heart
        renderer.trigger_petting()
        self.assertGreater(len(renderer.hearts), 0)
        self.assertGreater(renderer.pet_until, 0)

        print("[OK] Test 2: Renderer 9 states, sparks, sleep Z, confetti, and petting hearts verified.")

    def test_03_winapi_pid_watchdog(self):
        """Test Windows WinAPI OpenProcess PID watchdog."""
        current_pid = os.getpid()
        self.assertTrue(is_pid_alive(current_pid))
        self.assertFalse(is_pid_alive(9999999))
        print("[OK] Test 3: WinAPI OpenProcess PID watchdog check verified.")

    def test_04_udp_ipc_packet_exchange(self):
        """Test UDP socket transmission and parsing for all 9 states."""
        listener = ArgonUDPListener(parent_pid=os.getpid(), idle_timeout=1.0)
        received_events = []

        def on_state(state, detail):
            received_events.append((state, detail))

        listener.state_received.connect(on_state)
        listener.start()
        time.sleep(0.3)

        client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            test_states = [
                ("IDLE", "Idle test"),
                ("THINKING", "Thinking test"),
                ("SEARCHING", "Searching test"),
                ("WORKING", "Working test"),
                ("TESTING", "Testing test"),
                ("ASKING", "Asking test"),
                ("SUCCESS", "Success test"),
                ("ERROR", "Error test"),
                ("LIMIT", "Limit test"),
            ]
            for s, d in test_states:
                payload = json.dumps({"state": s, "detail": d}).encode("utf-8")
                client.sendto(payload, (UDP_HOST, UDP_PORT))
                time.sleep(0.04)

            for _ in range(12):
                time.sleep(0.05)
                self.app.processEvents()

            self.assertEqual(len(received_events), 9)
            for i, (s, d) in enumerate(test_states):
                self.assertEqual(received_events[i][0], s)
                self.assertEqual(received_events[i][1], d)

            # Test QUIT command
            quit_fired = []
            listener.parent_exited.connect(lambda: quit_fired.append(True))
            client.sendto(json.dumps({"state": "QUIT"}).encode("utf-8"), (UDP_HOST, UDP_PORT))
            for _ in range(10):
                time.sleep(0.05)
                self.app.processEvents()
            self.assertTrue(len(quit_fired) > 0)
        finally:
            client.close()
            listener.stop()
        print("[OK] Test 4: UDP IPC exchange for all 9 states and QUIT verified.")

    def test_05_smoke_test_run(self):
        """Test full widget smoke run via subprocess with --test-run."""
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "argon_bug", "main.py")
        start = time.time()
        res = subprocess.run([sys.executable, script, "--test-run"], capture_output=True, text=True, timeout=12)
        duration = time.time() - start
        self.assertEqual(res.returncode, 0)
        self.assertIn("Starting 9-state self-test sequence", res.stdout)
        self.assertGreaterEqual(duration, 3.0)
        self.assertLessEqual(duration, 8.0)
        print("[OK] Test 5: Full 9-state widget smoke test run verified.")


if __name__ == "__main__":
    unittest.main()
