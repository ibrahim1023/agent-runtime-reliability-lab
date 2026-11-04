# Agent Runtime Reliability Lab

A learning lab that makes agent recovery behavior inspectable through tool attempts, committed receiver effects, and receipts.

## Current milestone

Historical idempotency evidence has been exported and independently inspected. No new experiments ran during packaging. The receiver is extracted with an explicit connection-cleanup fix. The offline command checks sixteen earlier historical records, all twenty-five search records, their decision review and the separate optional inventories, then runs six receiver contracts. The seven original middleware contracts now have fresh opt-in scripted execution evidence through the real graph/tool stack. The [combined approval/crash/resume experiment](docs/crash-resume-evidence.md) now has five fresh scripted cases and nineteen worker phases; its original edit-checker failure and separate corrected reassessment are both retained.

| Historical condition | Cases | Attempts per case | Committed effects per case |
|---|---:|---:|---:|
| Unprotected control | 1 | 2 | 2 |
| Protected receiver | 3 | 2 | 1 |

Start with [the evidence walkthrough](docs/idempotency-evidence.md) and [provenance](docs/provenance.md). Machine-readable evidence is in `results/historical/idempotency/`; source and export hashes are in `results/manifest.json`.

These results demonstrate a local SQLite receiver property at one crash boundary. They do not prove exactly-once effects for arbitrary remote services or general production readiness.

## Attribution

The original AI-assisted experiments were developed by Ibrahim Arshad using Deep Agents, LangChain, and LangGraph. Those projects supply the agent runtime; this lab packages experiment harnesses, receiver logic, evaluators, and evidence. This is not an upstream SDK contribution. No upstream implementation source has been copied in this milestone. Licensing review is required before source extraction.

Supporting work: [InferenceBench](https://github.com/ibrahim1023/inference-bench), a separate local inference benchmarking project outside this lab's implementation scope.

## Run the receiver contracts

From the repository root, using Python 3.10 or newer:

```sh
python3 -S -m unittest discover -s tests -v
```

No dependencies or API keys are needed. `-S` disables site-package loading. This path imports only the standard library and the extracted receiver, contains no provider or tracing client, and uses fresh temporary databases. Test failures return a nonzero exit code. Temporary test databases are cleaned up; historical evidence is not overwritten.

These are fresh deterministic receiver executions, not new LLM evaluations or graph crash/resume runs. The unprotected control is expected to create two effects. Use the combined command below to validate historical artifacts as a separate stage.

## Verify historical evidence and fresh receiver behavior

From the repository root:

```sh
python3 -S -m reliability_lab verify-offline
```

The JSON report separates `historical_evidence` (sixteen stored records checked, including excluded attempts) from `receiver_contracts` (six fresh local checks). Each invocation writes a new `work/attempts/<unique-id>/report.json` and prints its relative path. It never overwrites historical results. The separate `crash_resume_evidence` stage validates the five saved fresh-runtime cases without launching workers. Any evidence, search-review, or receiver failure returns exit code 1. Invalid historical evidence prevents fresh receiver checks from starting.

The command disables tracing and installs a Python audit hook rejecting socket operations before loading receiver tests. No live-provider entry point exists yet. This guard prevents accidental Python network use on this path; it is not an operating-system security sandbox for hostile code.

Run all development checks, including evidence tampering and command failure cases:

```sh
python3 -S -m unittest discover -s tests -v
```

Verified on Python 3.14.6: 130 tests passed. On Python before 3.13, the connection-warning regression test is explicitly skipped because SQLite did not emit that warning; skipped counts are reported. Other contracts remain active.

See [offline verification limits](docs/offline-verification.md) for what the checks do and do not establish.

## Historical approval evidence

| Simulated decision | Effects at pause / after undecided restart | Effects after decision |
|---|---:|---:|
| Approve | 0 / 0 | 1 |
| Reject | 0 / 0 | 0 |
| Edit | 0 / 0 | 1, with replacement contents |

[Read the approval walkthrough](docs/approval-evidence.md). These three cases are historical runtime executions with simulated reviewer inputs, not new approval executions or human authentication tests. The offline command validates their stored records. A separate fresh scripted experiment now combines approval with post-commit crash/resume; it does not rerun these historical model trials.

## Historical missing-source evaluation

The task asked the agent to reverse lines from `/data.txt` into `/out.txt`, but the synthetic StateBackend started empty.

- Three valid runs stopped naturally, created no output, and reported the missing input. Task completion was false; historical assistant review judged failure handling correct.
- Three HTTP 429 provider-interrupted attempts are retained as invalid and inconclusive for behavior.
- Three setup failures occurred before model requests because the model setting was missing. They are retained separately.

[Inspect the task-versus-behavior walkthrough](docs/missing-source-evidence.md). No new model evaluations ran during packaging. The offline command validates these nine records alongside four idempotency and three approval records; sixteen records does not mean sixteen successful experiments.

## Recovery middleware decision review

[Read why the conservative prototype was retained and the broader candidate rejected](docs/search-recovery-evidence.md). The new review preserves the historical seven-case comparison, 25-run roster, and actual ambiguity tool evidence. This is historical artifact inspection, not a new evaluation. The command checks this review in a separate `search_recovery_review` section: a 25-entry retrospective roster and three detailed ambiguity records. Those are not 25 fully validated model trials or new executions. The original historical stage still validates sixteen records; six receiver contracts execute fresh. No runtime default was added. [See the tampering experiment](docs/search-review-validation.md).

## First fresh scripted graph contract

[Inspect proposal versus executed arguments](docs/scripted-root-check.md). With the same scripted empty-root search, the baseline tool reported no files; the extracted conservative middleware changed the executed path to `/` and found `/incoming/data.txt`. The empty-path proposal remained in conversation history. This saved result contains two fresh graph executions, zero live-provider calls, and unchanged source files. It tests a middleware contract, not model decision quality.

This check requires an optional dependency environment and is separate from the standard-library commands above:

```sh
python -m reliability_lab scripted-root-check
python -m unittest discover -s runtime_checks -v
```

See [runtime environment and reproduction limits](runtime_checks/README.md). The recorded check reused an existing editable Deep Agents environment; a later clean installation reproduced the crash/resume fixture; these filesystem fixtures were not rerun there. The default offline verifier does not yet validate the new scripted result. The remaining six now have separate [fresh scripted evidence](docs/scripted-filesystem-check.md), including the distinction between raw tool output and middleware-enriched model observations.

Run the remaining fixtures with `python -m reliability_lab scripted-filesystem-check`. The full opt-in suite has two test methods covering seven middleware cases plus the baseline control. The standard-library development suite remains separate. No live-model evaluation is performed by either scripted command.

## Complete historical search records

All 25 search runs now have [detailed extracts and offline consistency checks](docs/search-export.md), including the rejected ambiguity run and graph-limit failure. `historical_search_evidence` reports them separately from the original sixteen records and the three-record decision review. These are historical artifact validations, not fresh model trials.

## Optional cohort inventory

The [optional inventory](docs/optional-cohorts.md) preserves the original 120B comparison, its separate quota-blocked follow-up and the separate 20B comparison. The original-present 120B failure remains unresolved and has a detailed public extract. Provider interruptions have null behavior verdicts. Inventory checks are not full per-run model evaluation.

## Sprint plan and provenance

The three [Day 1 closeout items and next experiment criteria](docs/sprint-experiment-plan.md) are documented. The frozen approval → commit → crash → resume experiment has [executed once](docs/crash-resume-evidence.md): protected replay kept one effect, while the control duplicated it. [Remaining provenance gaps](docs/provenance-gaps.md) stay explicit: historical revisions, immutable model snapshots and complete clean-install reproduction are not established. New diagnostic metadata is allowlisted from existing local traces; no live calls were made during this closeout.


## Fresh package reproduction

The [clean-install reproduction](docs/clean-install-reproduction.md) installed published packages in a new non-editable environment and repeated the five crash/resume cases once. All expected tool/effect outcomes matched, with nineteen new worker phases and zero provider calls. This verifies the setup on the same host and Python 3.14.6; it is not cross-platform reproduction or a fully locked build. `requirements-runtime.txt` now includes the checkpoint packages. The installed version inventory and separately reviewed new evidence are linked in the manifest; the default verifier now checks this export in `clean_install_evidence`.


## Evidence-aware outcome reporting

[The reporting experiment](docs/outcome-reporting-evidence.md) reused five closed-run receivers and added two controlled unreadable-evidence fixtures. A new read-only application reporter disclosed the duplicate that the original final receipt omitted, and returned unknown when receiver evidence could not be read. This is separate from the original model answer and is not yet integrated into the graph. Seven fresh reporting observations used zero new graph workers or provider calls. That milestone had 83 development tests; the current suite has 96. The export is now checked automatically in `outcome_reporting_evidence`.


## Automatic checks for recent evidence

`verify-offline` now validates the clean-install export in `clean_install_evidence` and the seven reporting observations in `outcome_reporting_evidence`. These stages inspect saved evidence without installing packages, starting graphs or rereading private databases. Tampering tests reject contradictory conclusions even after artifact hashes are updated. This supersedes earlier pending-validator notes. The development suite has 88 tests at this milestone.


## Integrated final application response

[The integration experiment](docs/final-response-integration.md) now routes completed crash/resume results through receiver reconciliation before selecting `user_response`, while preserving `model_answer`. One new five-case execution used nineteen workers and zero provider calls; six response observations disclosed duplicates, named approved edits, handled rejection and reported unknown on unavailable evidence. `final_response_evidence` validates the saved integration without rerunning it. Use `python -m reliability_lab reported-crash-check` only to deliberately start a new bounded attempt. Current development verification: 96 tests.


## Receiver diagnostics failure handling

[The November 4 experiment](docs/receiver-diagnostics-evidence.md) found that preliminary receiver hashing could throw before the ordinary final-response path reached reconciliation. The application now records unavailable diagnostics and continues reporting: missing SQL evidence yields unknown, while readable SQL remains usable despite a failed hash read. Missing hashes never prove unchanged bytes, and unmet experiment criteria remain failed. Three baseline and three corrected application replays reused saved graph output; no new graph or provider call ran. Original integration source bytes are preserved separately. The offline verifier validates the saved replay in `receiver_diagnostics_evidence`; current development verification has 102 tests.


## Native retries and synchronous timeouts

[Six native-runtime cases](docs/retry-timeout-evidence.md) show bounded read retries, exhaustion as an error ToolMessage, duplicate effects under broad unprotected write retry, safe receipt reuse with a protected receiver, and a write committing before a synchronous timeout reaches its caller. Six graphs and eleven tool entries ran with zero provider calls. A setup failure and partial-worker fixture failure are retained with explicit amendments; coverage is five cases plus one continuation, not one uninterrupted successful suite. The default offline verifier checks the saved evidence in `native_retry_evidence`. Current development verification: 111 tests.


## Native limits for one run

[The four-case budget experiment](docs/run-budget-evidence.md) distinguishes model requests from tool-body retry attempts. Four fresh graphs in one worker used twenty-seven controlled failed read entries and zero provider calls. A tool-call cap of one permitted one request with three attempts, then blocked the next request. Combined model/tool limits stopped further work while preserving task failure. The default offline command checks the saved trace in `run_budget_evidence`; development verification has 118 tests. Limits across restarts or multiple invocations remain untested.


## Budget lifetime across clean restarts

[The two-turn experiment](docs/budget-lifetime-evidence.md) used four fresh workers and the same checkpoint thread per condition. Run-only limits allowed three failed tool entries on each new turn; adding a thread limit allowed three on the first and zero on the second. The conversation counter and prior messages persisted, while the run counter was absent from checkpoints. This covers completed turns with new input, not pending-work crash/resume or global user budgets. The default offline verifier checks the saved evidence in `budget_lifetime_evidence`; current development verification has 124 tests.


## Budgeted crash recovery

[The combined experiment](docs/budget-recovery-evidence.md) resumed a pending approved tool while the conversation counter remained spent. Both receivers replayed the body; protected storage kept one effect while the control created two. A genuinely new approved request was budget-blocked in both cases. Two conditions used twelve expected worker exits, four actual tool entries and zero provider calls. Approval-before-budget ordering is retained explicitly. The offline verifier checks the saved evidence in `budget_recovery_evidence`; current development verification has 130 tests.
