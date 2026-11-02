# Agent Runtime Reliability Lab

A learning lab that makes agent recovery behavior inspectable through tool attempts, committed receiver effects, and receipts.

## Current milestone

Historical idempotency evidence has been exported and independently inspected. No new experiments ran during packaging. The receiver is extracted with an explicit connection-cleanup fix. A combined offline command verifies sixteen historical records, checks the search-recovery review separately, and runs six receiver contracts. The seven original middleware contracts now have fresh opt-in scripted execution evidence through the real graph/tool stack. Approval and graph crash/resume integration are not implemented yet.

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

The JSON report separates `historical_evidence` (sixteen stored records checked, including excluded attempts) from `receiver_contracts` (six fresh local checks). Each invocation writes a new `work/attempts/<unique-id>/report.json` and prints its relative path. It never overwrites historical results. Any evidence, search-review, or receiver failure returns exit code 1. Invalid historical evidence prevents fresh receiver checks from starting.

The command disables tracing and installs a Python audit hook rejecting socket operations before loading receiver tests. No live-provider entry point exists yet. This guard prevents accidental Python network use on this path; it is not an operating-system security sandbox for hostile code.

Run all development checks, including evidence tampering and command failure cases:

```sh
python3 -S -m unittest discover -s tests -v
```

Verified on Python 3.14.6: 61 tests passed. On Python before 3.13, the connection-warning regression test is explicitly skipped because SQLite did not emit that warning; skipped counts are reported. Other contracts remain active.

See [offline verification limits](docs/offline-verification.md) for what the checks do and do not establish.

## Historical approval evidence

| Simulated decision | Effects at pause / after undecided restart | Effects after decision |
|---|---:|---:|
| Approve | 0 / 0 | 1 |
| Reject | 0 / 0 | 0 |
| Edit | 0 / 0 | 1, with replacement contents |

[Read the approval walkthrough](docs/approval-evidence.md). These three cases are historical runtime executions with simulated reviewer inputs, not new approval executions or human authentication tests. The offline command validates their stored records. It does not yet reproduce the approval runtime.

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

See [runtime environment and reproduction limits](runtime_checks/README.md). The recorded check reused an existing editable Deep Agents environment; a clean installation has not been verified. The default offline verifier does not yet validate the new scripted result. The remaining six now have separate [fresh scripted evidence](docs/scripted-filesystem-check.md), including the distinction between raw tool output and middleware-enriched model observations.

Run the remaining fixtures with `python -m reliability_lab scripted-filesystem-check`. The full opt-in suite has two test methods covering seven middleware cases plus the baseline control. The standard-library development suite remains separate. No live-model evaluation is performed by either scripted command.

## Complete historical search records

All 25 search runs now have [detailed extracts and offline consistency checks](docs/search-export.md), including the rejected ambiguity run and graph-limit failure. `historical_search_evidence` reports them separately from the original sixteen records and the three-record decision review. These are historical artifact validations, not fresh model trials.

## Optional cohort inventory

The [optional inventory](docs/optional-cohorts.md) preserves the original 120B comparison, its separate quota-blocked follow-up and the separate 20B comparison. The original-present 120B failure remains unresolved and has a detailed public extract. Provider interruptions have null behavior verdicts. Inventory checks are not full per-run model evaluation.
