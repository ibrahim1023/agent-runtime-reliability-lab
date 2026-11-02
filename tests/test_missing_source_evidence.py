"""Keep validity, task success, and historical behavior review distinct."""

import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from reliability_lab.missing_source_evidence import verify_missing_source_evidence

ROOT=Path(__file__).resolve().parents[1]


class MissingSourceEvidenceContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.directory=TemporaryDirectory(); self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name)
        shutil.copytree(ROOT/'results', self.root/'results')

    def modify(self, name: str, change) -> None:
        path=self.root/f'results/historical/missing-source/{name}.json'
        data=json.loads(path.read_text()); change(data); path.write_text(json.dumps(data))
        path=self.root/'results/manifest.json'; manifest=json.loads(path.read_text())
        entry=next(e for e in manifest['missing_source_cases'] if e['case']==name)
        entry['sha256']=hashlib.sha256((self.root/entry['export']).read_bytes()).hexdigest()
        path.write_text(json.dumps(manifest))

    def test_valid_trials_and_excluded_attempts_remain_separate(self) -> None:
        results=verify_missing_source_evidence(self.root)
        self.assertEqual(len(results),9)
        self.assertEqual(sum(r['valid_trial'] for r in results),3)
        valid=[r for r in results if r['valid_trial']]
        self.assertTrue(all(r['task_completion'] is False for r in valid))
        self.assertTrue(all(r['failure_handling'] is True for r in valid))
        self.assertTrue(all(r['task_completion'] is None for r in results if not r['valid_trial']))

    def test_invented_output_is_rejected(self) -> None:
        self.modify('trial-1',lambda d:d['observed']['files'].update({'/out.txt':'invented'}))
        with self.assertRaises(ValueError): verify_missing_source_evidence(self.root)

    def test_normal_completion_cannot_be_labeled_task_success(self) -> None:
        self.modify('trial-1',lambda d:d.update(task_completion=True))
        with self.assertRaises(ValueError): verify_missing_source_evidence(self.root)

    def test_provider_error_cannot_enter_behavior_denominator(self) -> None:
        self.modify('rate-limited-trial-1',lambda d:d.update(valid_trial=True))
        with self.assertRaises(ValueError): verify_missing_source_evidence(self.root)

    def test_step_limit_cannot_be_relabeled_as_natural_stop(self) -> None:
        self.modify('trial-2',lambda d:d['observed'].update(forced_stop=True))
        with self.assertRaises(ValueError): verify_missing_source_evidence(self.root)

    def test_tool_count_must_match_events(self) -> None:
        self.modify('trial-3',lambda d:d['observed'].update(tool_calls=1))
        with self.assertRaises(ValueError): verify_missing_source_evidence(self.root)

    def test_changed_answer_invalidates_historical_review(self) -> None:
        self.modify('trial-1',lambda d:d['observed'].update(answer='Done'))
        with self.assertRaises(ValueError): verify_missing_source_evidence(self.root)

    def test_setup_failure_cannot_claim_a_model_run(self) -> None:
        self.modify('setup-failed-trial-1',lambda d:d.update(started_model_request=True))
        with self.assertRaises(ValueError): verify_missing_source_evidence(self.root)

    def test_missing_attempt_cannot_silently_improve_denominator(self) -> None:
        path=self.root/'results/manifest.json';data=json.loads(path.read_text())
        data['missing_source_cases'].pop();path.write_text(json.dumps(data))
        with self.assertRaises(ValueError): verify_missing_source_evidence(self.root)
