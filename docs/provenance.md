# Reuse and provenance

This inventory is the first packaging milestone, assembled November 2, 2026 (Asia/Dubai).

| Existing cohort | Planned reuse | Current export status |
|---|---|---|
| idempotency | Receiver, crash runner, review logic | Four reviewed event/receipt extracts; source hashes captured |
| approval / reviewer-edit | Durable review and edited-action fixtures | Not exported yet |
| missing-source | Honest stopping and distinct score dimensions | Not exported yet |
| search-improvement | Recorder, seven cases, scorer, conservative middleware | Not exported yet |
| rejected recovery middleware | Historical comparison only | Not exported yet; never the default |
| explicit-alternative | Optional variant and unresolved regression | Not exported yet |
| gptoss20b | Separate model cohort | Not exported yet |
| InferenceBench | Supporting link only | No code or measurements copied |

The manifest records the checkout revision observed now. The original idempotency execution revision has not been established; do not substitute the observed revision. Model/settings/dependency/scorer provenance still needs inspection before a complete reproducible release.

Original artifacts remain in their original lab folders. Exported receipts contain synthetic `checkpoint-demo` messages, operation IDs, and receipt IDs. Only explicitly reviewed journal fields were retained. Credentials, absolute personal paths, raw checkpoints, full traces, and provider logs were excluded. Source hashes are provenance pointers, not a claim that database dumps are safe for publication.

The earlier October 28 temporary lab is absent and is not a source for this export. Nothing has been published.

## Receiver extraction milestone

At initial extraction, `reliability_lab/receiver.py` was byte-for-byte identical to the original `ledger.py`. A subsequent connection-cleanup fix changed the extracted copy; the original and current hashes and exact change are recorded in the manifest. Tests adapt `run_lab.py::local_checks`, preserving eight-way duplicate, payload-conflict, and distinct-ID behavior. Two additional explicit cases cover reopening the receiver and the unprotected control. `THIRD_PARTY_NOTICES.md` retains upstream attribution and the MIT notice.

Verification executed November 2, 2026: `python3 -S -m unittest discover -s tests -v`, five tests passed. The initial discovery before extraction failed with a missing-package import error; it was a packaging check, not a behavioral test failure. No model, tracing, or networked experiment ran.

## Offline verifier milestone

New code: `evidence.py` validates export hashes, fixed cohort completeness, action identity, event order, separate process IDs, receipt reuse, and committed-effect consistency. `offline.py` executes that validation followed by the extracted receiver contracts; `__main__.py` exposes the command. These are new harness/checking components, not upstream runtime implementations.

A larger test run exposed ResourceWarning messages from the original receiver's unclosed SQLite connections. A new regression test reproduced the warning (failed), then the extracted receiver was changed to nest the existing transaction context inside `contextlib.closing`. The transaction completes before closure. All receiver contracts passed afterward, without suppressing warnings. The original source remains untouched.

The original five-test record in `results/receiver-contract-check.json` describes the earlier byte-identical extraction. The newer combined report in `results/offline-check-20261102.json` supersedes it for the current receiver. They are different check milestones, not two model cohorts.
