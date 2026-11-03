"""Setup failures must not invent a prediction or leak inherited credentials."""

import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from reliability_lab.crash_resume import clean_environment

ROOT = Path(__file__).resolve().parents[1]


class CrashSetupContracts(unittest.TestCase):
    def test_worker_environment_excludes_credentials_and_python_injection(self) -> None:
        with patch.dict(os.environ, {"GROQ_API_KEY": "synthetic", "PRIVATE_TOKEN": "synthetic",
                                    "PYTHONPATH": "synthetic", "LANGSMITH_TRACING": "true"}):
            env = clean_environment()
        self.assertNotIn("GROQ_API_KEY", env)
        self.assertNotIn("PRIVATE_TOKEN", env)
        self.assertNotIn("PYTHONPATH", env)
        self.assertEqual(env["LANGSMITH_TRACING"], "false")

    def test_new_attempt_defaults_to_no_learner_prediction(self) -> None:
        with TemporaryDirectory() as directory:
            script = ('import json; from pathlib import Path; '
                      'from reliability_lab.crash_resume import run_crash_resume; '
                      f'report, code = run_crash_resume(Path({directory!r})); '
                      'print(json.dumps(report))')
            process = subprocess.run([sys.executable, "-S", "-c", script], cwd=ROOT,
                                     capture_output=True, text=True, timeout=10)
            self.assertEqual(process.returncode, 0, process.stderr)
            report = json.loads(process.stdout)
            self.assertEqual(report["learner_prediction"], "not supplied")
            self.assertEqual(report["classification"], "setup interruption")
            self.assertEqual(report["cases"], [])
