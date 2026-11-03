# Reuse and provenance

This inventory is the first packaging milestone, assembled November 2, 2026 (Asia/Dubai).

| Existing cohort | Planned reuse | Current export status |
|---|---|---|
| idempotency | Receiver, crash runner, review logic | Four reviewed event/receipt extracts; source hashes captured |
| approval / reviewer-edit | Durable review and edited-action fixtures | Three sanitized phase/journal/SQL exports; original artifact and runner hashes captured |
| missing-source | Honest stopping and distinct score dimensions | Three valid runs and six excluded attempts exported; feedback and source hashes retained |
| search-improvement | Recorder, seven cases, scorer, conservative middleware | Historical review checked offline; recorder/middleware extracted; all seven middleware fixtures executed with scripted responses; all 25 historical search records now exported/checked |
| rejected recovery middleware | Historical comparison only | Failed ambiguity extract and source hash preserved; never the default |
| explicit-alternative | Optional variant and unresolved regression | Original 16-attempt inventory, separate blocked follow-up, detailed unresolved 120B result; not full optional per-run validation |
| gptoss20b | Separate model cohort | Eight-run inventory retained separately; not a 120B reproduction |
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

## First fresh scripted-runtime milestone

`reliability_lab/runtime/conservative_middleware.py` is byte-identical to the original local lab module. `runtime/recorder.py` preserves the original `Recorder` class source unchanged, with a standalone header and imports. The manifest records original and destination hashes in a separate `scripted_runtime_extractions` list; receiver provenance is unchanged. No upstream framework implementation is copied. `scripted_root.py` adapts the first original contract and scripted-model pattern, adding a baseline, tool-argument recording, next-input observation, extraction hash checks and sanitized reports. It does not import the historical live runner or load .env.

The learner requested immediate execution without supplying a prediction. The assistant hypothesis is labeled as such. The opt-in contract first failed because the CLI command did not exist; that is a harness failure, not a runtime/model result. After implementation, the single opt-in contract passed with two real graph conditions. The saved `results/scripted-root-check-20261102.json` is fresh execution evidence, not a historical export or live-model evaluation. The other six original graph contracts have not been rerun.

The runtime used the existing local environment, with editable Deep Agents source at the tracked-clean checkout revision observed now and selected loaded-module hashes in the result. It does not establish the October execution revision. `requirements-runtime.txt` records selected package versions, not a full transitive lock; a clean package installation has not been validated as equivalent. No dependencies were installed in this milestone.

Tracing is disabled and Python socket operations are blocked before runtime imports. This is not an OS security sandbox. Raw callbacks stay in ignored work directories; only reviewed report fields are committed. The standard-library development suite still passes 48 tests, separate from the one opt-in runtime contract. The default offline verifier does not yet check this new result or the new extraction entries; the scripted command checks extraction hashes before executing. Crash/resume and approval integration remain pending.

## Remaining six scripted middleware fixtures

The original middleware and extracted Recorder bytes remain unchanged. The shared root harness now accepts the remaining original tool arguments/files and records the model-facing ToolMessage separately from the raw tool-end callback. The new `scripted-filesystem-check` command executes six fresh graphs; its opt-in test first failed on the missing command, then passed. The existing two-condition root check passed after the helper change. That is eight scripted graph conditions across two test methods, not eight model evaluations.

`results/scripted-filesystem-check-20261102.json` contains the six per-case observations, package versions, selected loaded-source hashes and current helper hashes. The first root report and all historical evidence remain unchanged; the first report's helper hash identifies its earlier version at commit `2b47bea`. The six new fixtures plus the earlier empty-root fixture cover the seven original contracts. No packages were installed; the editable-dependency and clean-install limitations remain.

In the two empty-listing fixtures, raw tool results matched, but only the truly empty workspace received the added empty-workspace context. The next model-input callback observed the enriched message. These are runtime-mechanics checks, not new semantic judgments or demonstrations of independent model recovery. The default offline verifier does not yet check the saved runtime result files. Approval/crash/resume integration remains pending.

## Full search-export milestone

`search_cases` and `search_fixtures` in the manifest now bind all 25 detailed historical records, original observed/journal identities and the original seven fixtures. The separate `historical_search_evidence` stage checks their consistency without importing runtime dependencies. Earlier exports and the initial decision-review JSON are unchanged. The new validator retains the historical artifact rubric and answer-review identity; it does not implement a new semantic judge.

Earlier record schemas differ from the current runner: some omit result execution IDs, recovery events and final message snapshots. The export labels sequential callback pairing and uses null for missing observations. The baseline nested graph-limit run has no final-state snapshot and is not interpreted as empty or excluded from behavioral results. Source-module hashes observed today do not establish every historical execution's code or settings. See [full export limits](search-export.md).

## Optional-cohort inventory milestone

The manifest hash-links three inventories with 16, 1 and 8 attempt records and a reviewed detailed unresolved 120B failure. Invalid provider attempts retain null behavior/task verdicts. The follow-up preserves three unstarted trials as unstarted, not extra attempts. `optional_cohort_inventory` checks identity, roster/classification and preservation of the unresolved result; it does not perform full optional per-run artifact validation or reissue semantic judgments. See [optional cohort limits](optional-cohorts.md). No optional cohort is merged into search scores or adopted as a default.

## Provenance closeout and next criteria

[The provenance-gap register](provenance-gaps.md) distinguishes observed identities, partial trace metadata and remaining unknowns. `runtime-provenance-20261102.json` records only allowlisted settings/version samples from stored search/optional traces, with source hashes. Diagnostic temperature metadata is retained as reported (`1e-08`), separately from current source requesting 0. No raw trace is published, no wire-payload or immutable provider-revision claim is made, and the original runtime revision remains unknown. This metadata file is hash-linked for review; the default verifier does not independently authenticate original traces or re-evaluate these diagnostic fields.

`next-experiment-plan-v1.json` freezes the bounded five-case approval/commit/crash/resume criteria. It is not execution evidence. The [sprint plan](sprint-experiment-plan.md) records Day 1 closeout, phase boundaries, preflight gates, exact expected effects and failure handling. The next execution and clean-install validation remain pending. Existing live-provider quotas are not assumed available.


## Fresh approval/commit/crash/resume milestone, 2026-11-03

This supersedes the pending integration status in the earlier chronological entries above. [The new fixture](crash-resume-evidence.md) executed the frozen five cases once, using nineteen fresh worker phases and no live provider. Runtime/module fingerprints and execution-time fixture hashes are retained. Commit `7bc4863` preserves the initially executed implementation and its original failed edit assessment. A1 corrects an overly strict receipt-format assumption using only saved evidence; the separate reassessment does not create new runtime trials. Approval, receiver contents, graph completion, expected control duplication and reporting are judged separately.

The default offline verifier now checks these saved observations in a separate `crash_resume_evidence` stage. Development verification has 75 tests. Raw checkpoint databases and private logs remain local; only reviewed synthetic observations are published. The selected environment is still editable, and a clean-install reproduction/full dependency lock remains unverified. No upstream SDK changes, new dependencies or historical-model reruns were made.
