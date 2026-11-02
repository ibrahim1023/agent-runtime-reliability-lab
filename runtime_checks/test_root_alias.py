"""Opt-in real-runtime contract; requires the recorded runtime dependencies."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RootAliasRuntimeContract(unittest.TestCase):
    def test_middleware_changes_execution_without_rewriting_proposal(self) -> None:
        env = {key: value for key, value in os.environ.items()
               if "KEY" not in key and not key.startswith(("LANG", "GROQ", "OPENAI", "ANTHROPIC", "GOOGLE"))}
        process = subprocess.run([sys.executable, "-m", "reliability_lab", "scripted-root-check"],
                                 cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        report = json.loads(process.stdout)
        self.assertEqual(report["kind"], "fresh scripted graph execution; no live-model evaluation")
        self.assertEqual(report["live_model_calls"], 0)
        baseline, corrected = report["conditions"]
        self.assertEqual(baseline["actual_tool_args"]["path"], "")
        self.assertEqual(corrected["conversation_proposal"]["args"]["path"], "")
        self.assertEqual(corrected["actual_tool_args"], {"path": "/", "pattern": "*.txt"})
        self.assertEqual(corrected["tool_result"]["status"], "success")
        self.assertIn("/incoming/data.txt", corrected["tool_result"]["content"])
        self.assertTrue(corrected["next_model_received_tool_result"])
        self.assertTrue(all(condition["files_unchanged"] for condition in report["conditions"]))
        self.assertNotIn("/Users/", process.stdout)
