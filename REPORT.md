# When an action finishes but its tool does not

An agent can return a real receipt and still fail a request to perform an action once. This lab makes that gap visible by observing three separate things: tool-body entries, committed receiver effects, and the final application response.

This is an independent, AI-assisted project by Ibrahim Arshad using Deep Agents, LangChain and LangGraph. Those frameworks provide capabilities, agent construction, execution and checkpoints. The lab contributes the experiment harness, SQLite receiver, reporting and evaluators. It does not replace the agent loop or change upstream SDK defaults.

## The central experiment

The [frozen five-case plan](results/next-experiment-plan-v1.json) defined expectations before execution: protected approval twice with independent fresh cases, an unprotected control, reviewer edit and rejection. A deterministic scripted model proposes the tool; a simulated reviewer supplies the decision. These are real graph/process executions with no provider inference.

The failure boundary is deliberate:

```text
Receiver commits and returns a receipt to the tool
    → tool journals and flushes the receipt
    → process exits before the tool returns
    → fresh process restores pending graph work
    → tool body enters again
```

The receiver database and graph checkpoint are separate transactions. The runtime has pending tool work, not a saved completed ToolMessage for the action. A checkpoint can restore that work without knowing that its external effect already happened.

The application persists an operation ID before starting workers. Replay keeps that ID and the approved contents. The protected receiver atomically checks/records the operation in SQLite and returns the exact first receipt on repetition. A different ID would describe a new action and defeat that deduplication. This protects one local operation; it does not make every remote action exactly once.

## Expected and observed

[Original execution](results/fresh/crash-resume-v1/execution.json), [separate corrected assessment](results/fresh/crash-resume-v1/reassessment-a1.json), and [walkthrough](docs/crash-resume-evidence.md):

| Case | Expected entries / effects | Observed entries / effects | User-task interpretation |
|---|---|---|---|
| Protected approve, first case | 2 / 1 | 2 / 1 | Completed once |
| Protected approve, independent repetition | 2 / 1 | 2 / 1 | Completed once |
| Unprotected approve control | 2 / 2 | 2 / 2 | Failed the record-once requirement |
| Protected edit | 2 / 1 | 2 / 1 | Completed with approved replacement |
| Protected reject | 0 / 0 | 0 / 0 | Correctly prevented action; no completed write |

Nineteen fresh workers ran across these five cases. Initial approval and undecided restart produced no effects; the pending review survived. Approved cases crashed after commit, then resumed without another approval. Both edit attempts used `reviewer-approved`, never `original-proposal`. All five graphs finished, including the duplicate control and rejection. Therefore graph completion is not the task-success metric.

Two tool entries versus one committed row are the crucial protected observation. A successful receipt alone cannot establish that count: the control's last receipt was real, but an earlier effect also existed. Timings are recorded, including the two protected repetitions, but process startup, caches and environment differences make them unsuitable as a performance benchmark.

## Reporting the receiver's outcome

The original scripted answer echoed the actual tool result. In the control it described the latest receipt while omitting the duplicate. We added a read-only reconciliation boundary that examines rows for the operation and approved payload, then selects the application response while preserving the graph answer separately.

The [integration execution](results/fresh/final-response-v1/execution.json) contains five graph cases, nineteen new workers and six response observations. The sixth response reuses one completed result with an unavailable configured receiver; it is not a sixth independent graph case.

| Receiver evidence | Selected application response | Task outcome |
|---|---|---|
| One matching effect and finished execution | Reports one committed record and approved contents | Completed |
| Two effects for the same operation | Discloses duplicate and record-once failure | Failed |
| Rejected operation with no effect | Reports rejection | No write completed |
| Receiver evidence unavailable | Reports unknown; keeps graph answer separately | Unknown |

This is deterministic application logic, not evidence that a model learned honesty. See [reporting code](reliability_lab/outcome_reporting.py), [response selection](reliability_lab/final_response.py), and [integrated wrapper](reliability_lab/reported_crash.py).

A later [diagnostic-failure replay](docs/receiver-diagnostics-evidence.md) found a real delivery defect: a preliminary file hash could throw before reconciliation. Three baseline and three corrected application replays reused saved graph output and reconstructed synthetic receivers, with no new graph calls. The correction lets reporting proceed when optional hashing fails. Missing SQL evidence gives unknown; readable SQL can still support the action count when only hashing fails. Missing hashes remain unknown, and the faulted experiment criteria remain failed. Better reporting does not erase incomplete verification.

## Budgets and retries protect different boundaries

The [budget/recovery experiment](results/fresh/budget-recovery-v1/execution.json) combined the central crash with a one-request conversation allowance. Its [frozen plan](results/budget-recovery-plan-v1.json) allowed twelve worker phases: six each for protected and control conditions.

The allowance was spent before commit. On restart, the pending body still entered again: protected storage kept one effect; the control had two. A genuinely new request was blocked before entering its tool. The allowance limits new requests, while the receiver handles duplicate effects from replay. In this installed middleware order, the new request paused for simulated approval before the spent budget denied it. Approval did not override the limit.

The [native retry/timeout evidence](docs/retry-timeout-evidence.md) supports the same distinction. Two retries allow three body attempts for one request. A lost response after an unprotected commit produced another effect under broad write retry. A running synchronous write also committed before its caller received a timeout. An error or deadline does not prove that an action never happened. These are installed-version observations, not guarantees for all runtime releases or asynchronous cancellation.

## Failures are part of the evidence

Historical live-model evaluations are separate from those scripted executions:

- [Missing-source records](docs/missing-source-evidence.md): three valid runs created no output and honestly stopped. The requested transformation failed, but failure handling was judged correct. Three provider-limited attempts and three missing-model-setting setup failures remain excluded/inconclusive for behavior.
- [Search comparison](docs/search-recovery-evidence.md): the retrospective seven-case matrix had correct handling of 4/7 baseline, 4/7 broad candidate and 6/7 conservative. The broad candidate was rejected because it read one of two plausible sources and wrote an output without resolving the ambiguity. A technically successful write was a task failure. The baseline nested graph-limit result remains a behavioral failure. All [25 detailed extracts](docs/search-export.md) are retained; they are not 25 successful tasks or a prospectively frozen study.
- [Optional cohorts](docs/optional-cohorts.md): the original-present 120B failure remains unresolved. Its quota-blocked follow-up is not behavioral evidence. The separate eight-run 20B comparison does not resolve the 120B result or improve the main cohort's scores.

The conservative middleware narrows root-path interpretation and supplies grounded empty-workspace context. Its small cohort result is not a general model-reliability guarantee, and the rejected candidate remains rejected.

## Evaluators can be wrong too

The original crash export has `status: failed` because its first assessor expected the entire edited ToolMessage to be JSON. The runtime actually prepended an authorized-edit explanation before the receipt. [Amendment A1](docs/crash-resume-assessment-amendment-a1.md) corrected that assumption and reassessed the saved data. The failed assessment remains intact; no workers were rerun to obtain a better result.

Review also found validator gaps around checkpoint completion, model-facing answer content and successful worker exits. Regression checks demonstrated covered contradictions; corrected assessors checked saved observations. These corrections did not add model trials or turn the unsafe control into task success.

The native retry fixture had genuine infrastructure interruptions: an incorrect interpreter selection failed before any graph; a later construction error interrupted after five cases. A continuation ran only the remaining timeout case. [Coverage](results/fresh/native-retry-v1/coverage.json) preserves six graph cases across interrupted execution, explicitly not one uninterrupted passing suite. The continuation did not independently recollect a full runtime fingerprint.

## What reproduced, and what a reader can run

A [fresh non-editable installation](docs/clean-install-reproduction.md) repeated the five crash cases once on the same host with Python 3.14.6 and published packages. Nineteen new workers produced the same tool/effect contract outcomes. [Environment](results/fresh/clean-install-v1/environment.json), [comparison](results/fresh/clean-install-v1/comparison.json), selected source hashes and a [59-package inventory](requirements-runtime-resolved-20261103.txt) are retained.

That narrows the editable-checkout concern. It is not independent-host/cross-platform reproduction or a full transitive artifact lock. Raw preflight wording inherited from the older fixture says editable; the separate environment observations establish that this installation was non-editable. Historical runtime revisions and immutable provider model revisions remain unknown.

From the repository root:

```sh
python3 -S -m reliability_lab verify-offline
python3 -S -m unittest discover -s tests -v
```

The first command validates stored evidence and runs six fresh SQLite receiver contracts. The second runs the development suite, including tampering and deterministic application tests. Neither reruns the saved graph experiments. [Reproduction instructions](docs/reproduction.md) give the optional fresh-worker setup, bounds and check record. The [demo](docs/demo.md) uses saved observations by default.

## How to read the evidence types

| Evidence type | What actually happened | What it cannot establish |
|---|---|---|
| Historical live-model extracts | Earlier model/tool attempts, including failures and exclusions | A new evaluation or known immutable historical runtime/model revision |
| Fresh scripted graph/process execution | Installed runtime, deterministic proposals, actual tools, crashes and fresh workers | General model decision quality or authenticated review |
| Application replays | Saved graph output through reporting paths with controlled receiver conditions | A new graph recovery run |
| Stored-evidence validation | Hash and covered consistency checks against reviewed artifacts | Replay, independent authenticity or a new semantic judge |
| Fresh receiver contracts | New local SQLite executions, including duplicate requests | Exactly-once behavior of arbitrary external services |

Evidence hashes are identities, not signatures. Coherently replacing all records and their manifest can evade consistency validation. Raw checkpoints, private traces and credentials are not published. The Python socket guard prevents accidental network use on its guarded path; it is not an OS security boundary.

The defensible result is a bounded recovery demonstration and a reporting improvement: repeated attempts are visible, duplicate effects remain failures, and unavailable outcome evidence stays unknown. The [claim map](docs/claim-evidence.md) and [provenance register](docs/provenance-gaps.md) define the public limits.
