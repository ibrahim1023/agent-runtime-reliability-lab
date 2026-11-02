"""Remaining original filesystem fixtures through the public runtime command."""

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class FilesystemRuntimeContracts(unittest.TestCase):
    def test_remaining_aliases_scope_and_empty_workspace_observation(self) -> None:
        env = {key: value for key, value in os.environ.items()
               if "KEY" not in key and not key.startswith(("LANG", "GROQ", "OPENAI", "ANTHROPIC", "GOOGLE"))}
        process = subprocess.run([sys.executable, "-m", "reliability_lab", "scripted-filesystem-check"],
                                 cwd=ROOT, env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        report = json.loads(process.stdout)
        self.assertEqual(report["live_model_calls"], 0)
        rows = {row["case"]: row for row in report["conditions"]}
        self.assertEqual(len(rows), 6)
        for name, alias in (("dot", "."), ("dot_slash", "./"), ("slash_dot", "/.")):
            with self.subTest(case=name):
                row = rows[name]
                self.assertEqual(row["conversation_proposal"]["args"]["path"], alias)
                self.assertEqual(row["actual_tool_args"]["path"], "/")
                self.assertIn("/incoming/data.txt", row["model_facing_tool_result"]["content"])
        scoped = rows["explicit_scope"]
        self.assertEqual(scoped["actual_tool_args"]["path"], "/visible")
        self.assertIn("/visible/data.txt", scoped["model_facing_tool_result"]["content"])
        self.assertNotIn("/other/data.txt", scoped["model_facing_tool_result"]["content"])
        empty = rows["empty_workspace"]
        self.assertIn("workspace currently contains zero files", empty["model_facing_tool_result"]["content"])
        self.assertNotIn("zero files", empty["tool_result"]["content"])
        populated = rows["empty_subdirectory"]
        self.assertNotIn("zero files", populated["model_facing_tool_result"]["content"])
        self.assertTrue(all(row["files_unchanged"] and row["next_model_received_tool_result"] for row in rows.values()))
