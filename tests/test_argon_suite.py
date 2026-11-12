import json
import os
import socket
import subprocess
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtCore import QCoreApplication
from argon_bug.config import UDP_HOST, UDP_PORT, BugState, STATE_PHRASES
from argon_bug.udp_listener import is_pid_alive, ArgonUDPListener
from argon_bug.renderer import ArgonBugRenderer


class TestArgonBugSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QCoreApplication.instance() or QCoreApplication(sys.argv)
    def test_01_config_and_palette(self):
        """Test configuration, states, and color definitions."""
        self.assertEqual(len(BugState), 5)
        for state in BugState:
            self.assertIn(state, STATE_PHRASES)
            self.assertGreater(len(STATE_PHRASES[state]), 0)
        self.assertEqual(UDP_HOST, "127.0.0.1")
        self.assertEqual(UDP_PORT, 51515)
        print("\n[OK] Test 1: Config, 5 states, phrases, and socket constants verified.")

    def test_02_renderer_procedural_states(self):
        """Test procedural renderer animations and particle systems."""
        renderer = ArgonBugRenderer()
        for state in BugState:
            renderer.set_state(state, f"Test detail for {state.value}")
            self.assertEqual(renderer.state, state)
            self.assertEqual(renderer.detail_text, f"Test detail for {state.value}")
            for _ in range(10):
                renderer.update_animation()

        # Check particles for WORKING state
        renderer.set_state(BugState.WORKING)
        for _ in range(20):
            renderer.update_animation()
        self.assertGreater(len(renderer.sparks), 0)

        # Check sleep Z particles for LIMIT state
        renderer.set_state(BugState.LIMIT)
        for _ in range(35):
            renderer.update_animation()
        self.assertGreater(len(renderer.sleep_zs), 0)
        print("[OK] Test 2: Renderer procedural state transitions and particles verified.")

    def test_03_winapi_pid_watchdog(self):
        """Test Windows WinAPI OpenProcess PID watchdog."""
        current_pid = os.getpid()
        self.assertTrue(is_pid_alive(current_pid))
        # Non-existent high PID
        self.assertFalse(is_pid_alive(9999999))
        print("[OK] Test 3: WinAPI OpenProcess PID watchdog check verified.")

    def test_04_udp_ipc_packet_exchange(self):
        """Test UDP socket transmission and parsing of JSON payloads."""
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
                ("WORKING", "Working test"),
                ("TESTING", "Testing test"),
                ("LIMIT", "Limit test"),
            ]
            for s, d in test_states:
                payload = json.dumps({"state": s, "detail": d}).encode("utf-8")
                client.sendto(payload, (UDP_HOST, UDP_PORT))
                time.sleep(0.05)

            # Give listener thread a moment to process packets and dispatch Qt events
            for _ in range(10):
                time.sleep(0.05)
                self.app.processEvents()

            self.assertEqual(len(received_events), 5)
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
        print("[OK] Test 4: UDP IPC packet exchange and QUIT signal verified.")

    def test_05_smoke_test_run(self):
        """Test full widget smoke run via subprocess with --test-run."""
        script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "argon_bug", "main.py")
        start = time.time()
        res = subprocess.run([sys.executable, script, "--test-run"], capture_output=True, text=True, timeout=10)
        duration = time.time() - start
        self.assertEqual(res.returncode, 0)
        self.assertIn("Starting 3-second self-test sequence", res.stdout)
        self.assertGreaterEqual(duration, 2.5)
        self.assertLessEqual(duration, 6.0)
        print(f"[OK] Test 5: Smoke test run executed successfully in {duration:.2f}s with code 0.")

    def test_06_node_argon_bridge_end_to_end(self):
        """Test Node.js TypeScript argon-bridge.ts emitting UDP state to Python listener."""
        import urllib.request
        from pathlib import Path
        listener = ArgonUDPListener(parent_pid=os.getpid(), idle_timeout=10.0)
        received = []
        listener.state_received.connect(lambda s, d: received.append((s, d)))
        listener.start()
        time.sleep(0.3)

        try:
            # Run node script that imports argon-bridge.ts via file:// URL
            bridge_file = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / "opencode" / "packages" / "util" / "src" / "argon-bridge.ts"
            bridge_url = bridge_file.as_uri()

            node_cmd = [
                "node",
                "--experimental-strip-types",
                "--input-type=module",
                "-e",
                f"import('{bridge_url}').then(m => m.emitArgonState('WORKING', 'Node E2E verified'))",
            ]
            res = subprocess.run(node_cmd, capture_output=True, text=True, timeout=5)
            if res.returncode != 0:
                print("NODE STDERR:", res.stderr)
            self.assertEqual(res.returncode, 0)

            for _ in range(10):
                time.sleep(0.05)
                self.app.processEvents()

            self.assertEqual(len(received), 1)
            self.assertEqual(received[0][0], "WORKING")
            self.assertEqual(received[0][1], "Node E2E verified")
            print("[OK] Test 6: Node.js argon-bridge.ts E2E UDP delivery verified.")
        finally:
            listener.stop()

    def test_07_embedded_mascot_extraction(self):
        """Test gzip+base64 embedding and atomic extraction in argon-bridge."""
        import tempfile
        import hashlib
        from pathlib import Path

        repo_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        embed_script = repo_root / "scripts" / "embed_mascot.mjs"
        bridge_file = repo_root / "opencode" / "packages" / "util" / "src" / "argon-bridge.ts"
        gen_file = repo_root / "opencode" / "packages" / "util" / "src" / "argon-embedded.gen.ts"

        # 1. Create a test binary file with unique payload
        fake_payload = b"TEST_ARGON_EMBEDDED_EXE_BINARY_PAYLOAD_V227"
        expected_sha256 = hashlib.sha256(fake_payload).hexdigest()
        fake_bin = repo_root / "test_fake_mascot.exe"
        fake_bin.write_bytes(fake_payload)

        try:
            # 2. Run embed_mascot.mjs to embed the binary
            res = subprocess.run(["node", str(embed_script), str(fake_bin)], capture_output=True, text=True)
            self.assertEqual(res.returncode, 0)
            self.assertTrue(gen_file.exists())
            gen_content = gen_file.read_text(encoding="utf-8")
            self.assertIn(expected_sha256, gen_content)

            # 3. Call extractEmbeddedMascot via Node.js
            bridge_url = bridge_file.as_uri()
            node_cmd = [
                "node",
                "--experimental-strip-types",
                "--input-type=module",
                "-e",
                f"import('{bridge_url}').then(m => {{ const p = m.extractEmbeddedMascot(); console.log('EXTRACTED_PATH=' + p); }})",
            ]
            res_ext = subprocess.run(node_cmd, capture_output=True, text=True)
            self.assertEqual(res_ext.returncode, 0)
            self.assertIn("EXTRACTED_PATH=", res_ext.stdout)

            # 4. Verify extracted file in ~/.opencode/bin/argon_bug.exe
            extracted_path = Path(os.path.expanduser("~")) / ".opencode" / "bin" / "argon_bug.exe"
            self.assertTrue(extracted_path.exists())
            extracted_bytes = extracted_path.read_bytes()
            self.assertEqual(extracted_bytes, fake_payload)
            print("[OK] Test 7: Embedded mascot packaging, SHA-256 verification, and extraction verified.")

        finally:
            # 5. Clean up and restore stub
            if fake_bin.exists():
                fake_bin.unlink()
            subprocess.run(["node", str(embed_script), "--stub"], capture_output=True, text=True)
            gen_restored = gen_file.read_text(encoding="utf-8")
            self.assertIn('EMBEDDED_MASCOT_GZ_BASE64 = ""', gen_restored)


if __name__ == "__main__":
    unittest.main(verbosity=2)
