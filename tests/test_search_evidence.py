"""Protect the full historical search export from altered claims or omissions."""

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SearchEvidenceContracts(unittest.TestCase):
    def setUp(self) -> None:
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name) / 'lab'
        shutil.copytree(ROOT, self.root, ignore=shutil.ignore_patterns('.git', 'work', '__pycache__'))

    def alter(self, label, change):
        p = self.root / f'results/historical/search/{label}.json'
        d = json.loads(p.read_text()); change(d); p.write_text(json.dumps(d))
        p = self.root / 'results/manifest.json'; d = json.loads(p.read_text())
        e = next(e for e in d['search_cases'] if e['label'] == label)
        e['sha256'] = hashlib.sha256((self.root/e['export']).read_bytes()).hexdigest()
        p.write_text(json.dumps(d))

    def command(self):
        p = subprocess.run([sys.executable, '-S', '-m', 'reliability_lab', 'verify-offline'],
                           cwd=self.root, capture_output=True, text=True)
        return p.returncode, json.loads(p.stdout)

    def rejected(self):
        code, report = self.command()
        self.assertEqual(code, 1, 'Altered search evidence accepted')
        self.assertEqual(report['historical_search_evidence']['status'], 'failed')
        self.assertEqual(report['receiver_contracts']['status'], 'not_run')

    def test_all_twenty_five_records_are_checked_separately(self):
        code, report = self.command(); self.assertEqual(code, 0)
        self.assertIn('historical_search_evidence', report)
        checked = report['historical_search_evidence']
        self.assertEqual(checked['records_checked'], 25)
        self.assertEqual(checked['graph_limit_behavior_failures'], 1)
        self.assertEqual(len(report['historical_evidence']['cases']), 16)

    def test_dropped_rejected_run_is_not_hidden(self):
        p = self.root/'results/manifest.json'; d = json.loads(p.read_text())
        d['search_cases'] = [e for e in d['search_cases'] if e['label'] != 'candidate-ambiguous-1']
        p.write_text(json.dumps(d)); self.rejected()

    def test_successful_write_must_agree_with_final_files(self):
        self.alter('conservative-existing-1', lambda d: d['observed']['final_files'].pop('/out.txt'))
        self.rejected()

    def test_graph_limit_is_behavior_failure_not_infrastructure(self):
        self.alter('baseline-nested-1', lambda d: d.update(valid_behavior_trial=False, status='provider_interrupted'))
        self.rejected()

    def test_graph_limit_does_not_have_an_empty_final_state_snapshot(self):
        self.alter('baseline-nested-1', lambda d: d['observed'].update(final_state_available=True, final_files={}))
        self.rejected()

    def test_callback_counts_must_match_journal(self):
        self.alter('baseline-empty-2', lambda d: d['observed'].update(tool_calls=0))
        self.rejected()

    def test_ambiguous_write_cannot_be_relabelled_correct(self):
        self.alter('candidate-ambiguous-1', lambda d: d['historical_scores'].update(behavior_correct=True))
        self.rejected()

    def test_changed_answer_does_not_inherit_the_old_review(self):
        self.alter('conservative-empty-2', lambda d: d['observed'].update(answer='Done'))
        self.rejected()

    def test_twenty_b_cohort_cannot_be_mixed_in(self):
        self.alter('conservative-existing-1', lambda d: d['observed'].update(model='groq:openai/gpt-oss-20b'))
        self.rejected()
