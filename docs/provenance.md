# Reuse and provenance

This inventory is the first packaging milestone, assembled November 2, 2026 (Asia/Dubai).

| Existing cohort | Planned reuse | Current export status |
|---|---|---|
| idempotency | Receiver, crash runner, review logic | Four reviewed event/receipt extracts; source hashes captured |
| approval / reviewer-edit | Durable review and edited-action fixtures | Three sanitized phase/journal/SQL exports; original artifact and runner hashes captured |
| missing-source | Honest stopping and distinct score dimensions | Three valid runs and six excluded attempts exported; feedback and source hashes retained |
| search-improvement | Recorder, seven cases, scorer, conservative middleware | Decision review, 25-run roster and three ambiguity extracts checked offline; full per-run export pending |
| rejected recovery middleware | Historical comparison only | Failed ambiguity extract and source hash preserved; never the default |
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

## Approval export milestone

New verifier: `reliability_lab/approval_evidence.py`. Original `initial.json`, `restore.json`, and `decision.json` are reduced to an explicit field allowlist: phase, decision, PID, interrupts, checkpoint-next labels, messages, ledger snapshots, and answer. Synthetic prompt/tool text is retained so proposal and execution can be compared. Model alias and simulated reviewer source come from each original manifest; no immutable model revision is known. Journal fields were reviewed and allowlisted; committed receipts were read directly from each original SQLite database with read-only access and compared with the recorded final snapshot.

`results/manifest.json::approval_cases` maps each export to hashes of original phase records, manifest, journal, and ledger. Runner/reviewer/report hashes are also captured. No approval runner code is copied yet; the existing protected receiver remains the shared implementation planned for runtime extraction. Original checkpoint databases, full traces, provider logs, duration fields, and private filesystem paths are excluded. Source timestamps are not being used to infer a historical runtime revision.

`results/offline-check-approval-20261102.json` records validation of seven historical cases plus six fresh receiver contracts. The previous four-case report remains as a separate packaging checkpoint. All 29 development tests passed on Python 3.14.6. Original labs and historical four-case exports were unchanged by this step.

## Missing-source export milestone

New verifier: `reliability_lab/missing_source_evidence.py`. Observed records are exported through an explicit field allowlist, omitting root tracing IDs and elapsed durations. Synthetic task messages, tool requests/results, callback counts and final filesystem remain available. Callback journal root entries are omitted; model-response and tool start/end events are retained to cross-check counts and message history.

Each original provider error contained account-specific organization details. Public exports retain its type, observed HTTP 429 status, and a reviewed generic token-per-minute error excerpt. Original observed records, journals and uploaded feedback files are hash-linked in the manifest. Setup failures are reduced to the actual missing-setting exception, with source worker-log hashes and no private traceback paths.

The original summary called setup failure a helper path problem. Direct logs show `KeyError: 'DEEPAGENTS_EVALS_MODEL'` before model initialization. This export records that observed symptom; it does not assert a new root-cause diagnosis. Original reports remain untouched.

Failure-handling scores preserve historical manual assistant trace review. The verifier checks objective no-output observations and that the retained reviewed answer has not changed; it is not a new general language judge. Provider/setup attempts have null task and behavior verdicts. The historical prospective attempt count remains unknown; the exported retrospective roster contains nine attempts, with three valid behavioral observations, three provider interruptions and three setup interruptions. No graph-limit failure is discarded as infrastructure in this cohort.

`results/offline-check-missing-source-20261102.json` records the actual combined check: sixteen historical records validated and six fresh receiver checks passed. The full development suite passed 39 tests on Python 3.14.6. No new LLM trial, tracing upload, or original-source mutation occurred.

## Search-recovery decision review

`results/search-recovery-review.json` contains the retrospective roster of twenty-five stored runs, the seven-case matrix, three sanitized ambiguity extracts, and source hashes identifying the existing recorder, suite, scorer, both middleware variants and seven contract checks. Tool call arguments, result contents, synthetic files and final answers are allowlisted in the three extracts. Trace/run IDs, durations, provider logs, private paths and full traces are omitted. Scorer labels remain historical labels, with historical assistant answer review; this packaging step supplies no new semantic judge.

The conservative variant remains a scoped lab prototype. The rejected broad candidate remains failed and is not a default. The original rejection marker contains stale generic reason text; actual observed writes and files establish its ambiguity failure. Its source hash is retained without editing the original. Later explicit-alternative and 20B cohorts are not merged, and the unresolved original-present 120B failure is not removed.

No runtime code was extracted or executed in this milestone. The manifest hash-links this decision review, but `verify-offline` does not yet check that optional entry: its count remains sixteen historical records plus six fresh receiver contracts. Source identities were compared directly against original files during packaging. A full search-evidence validator and portable scripted graph execution remain pending.

## Search-review validation milestone

The earlier decision review remains byte-for-byte unchanged. Its `verification_scope` field describes the initial packaging state, before integration. The current `search_recovery_review` report section checks its manifest hash, fixed retrospective roster, matrix alignment, selected/rejected identities, seven stored contract-outcome entries, and the three detailed ambiguity extracts. The other twenty-two roster entries are not full per-run behavioral validations. The sixteen earlier records stay in their existing historical stage; six receiver contracts still execute fresh.

The learner prediction was unsure. Before implementation, eight tampering tests failed because the command ignored the new review; the unaltered control passed. After integration, a test explicitly confirms that relabeling the rejected run and recomputing the manifest hash passes byte-identity checking, while the recorded write still contradicts the verdict. Nine new tests now pass. These are fresh deterministic validator tests against stored evidence, not fresh graph executions or model evaluations. `results/search-review-check-20261102.json` records the focused probe and development verification.

This closed-fixture checker compares the declared synthetic files and recorded successful writes. It does not run StateBackend, judge natural language, authenticate old artifacts, establish an unknown historical runtime revision, or detect a coherent replacement of both evidence and manifest. No new provider or tracing client was added. Full private traces and original labs remain untouched.
