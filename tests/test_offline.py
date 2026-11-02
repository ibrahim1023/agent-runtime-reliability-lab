"""Exercise the public offline command, including nonzero validation failures."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]


class OfflineCommandContracts(unittest.TestCase):
    def test_command_has_two_stages_and_preserves_previous_attempts(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "lab"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "work", "__pycache__"))
            env = {k: v for k, v in os.environ.items() if "KEY" not in k and not k.startswith(("LANG", "GROQ", "OPENAI", "ANTHROPIC"))}
            paths = []
            for _ in range(2):
                result = subprocess.run([sys.executable, "-S", "-m", "reliability_lab", "verify-offline"],
                                        cwd=target, env=env, capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
                report = json.loads(result.stdout)
                self.assertEqual(len(report["historical_evidence"]["cases"]), 4)
                self.assertEqual(report["receiver_contracts"]["tests_run"], 6)
                self.assertEqual(report["historical_evidence"]["status"], "passed")
                self.assertEqual(report["receiver_contracts"]["status"], "passed")
                paths.append(target / report["report_path"])
            self.assertNotEqual(paths[0], paths[1])
            self.assertTrue(all(p.is_file() for p in paths))

    def test_corrupt_evidence_returns_nonzero_and_skips_new_contracts(self) -> None:
        with TemporaryDirectory() as directory:
            target = Path(directory) / "lab"
            shutil.copytree(ROOT, target, ignore=shutil.ignore_patterns(".git", "work", "__pycache__"))
            case = target / "results/historical/idempotency/protected-1.json"
            case.write_text(case.read_text() + "\n")
            result = subprocess.run([sys.executable, "-S", "-m", "reliability_lab", "verify-offline"],
                                    cwd=target, capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            report = json.loads(result.stdout)
            self.assertEqual(report["historical_evidence"]["status"], "failed")
            self.assertIn("hash", report["historical_evidence"]["error"])
            self.assertEqual(report["receiver_contracts"]["status"], "not_run")

    def test_offline_guard_blocks_socket_creation(self) -> None:
        script = "from reliability_lab.offline import install_offline_guard; install_offline_guard(); import socket; socket.socket()"
        result = subprocess.run([sys.executable, "-S", "-c", script], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Network disabled for offline verification", result.stderr)
