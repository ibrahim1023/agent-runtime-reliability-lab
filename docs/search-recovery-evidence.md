# Recovery middleware: correct observations before broader discretion

## Current state checked on November 2, 2026

The lab started clean at `f8837d54c285c0c71720e3faeee7c63a6b3c43f6` on `main`, matching the live GitHub remote. Python 3.14.6 passed all 39 development tests. The offline command validated sixteen historical records and executed six fresh receiver contracts. None of these checks were live-model evaluations.

This milestone reviews the existing search-improvement artifacts. It does not reproduce a graph run, change a runtime default, or select the rejected candidate. The [reviewed JSON](../results/search-recovery-review.json) preserves a retrospective 25-run roster, seven-case matrix, three allowlisted ambiguity extracts, source identities, and seven historical contract outcomes. At initial packaging the offline command did not check this review. It now checks the roster, matrix, hash and three detailed ambiguity extracts in a separate section; the original historical-record count remains sixteen. See [the validation experiment](search-review-validation.md).

## Why the conservative version was retained

The conservative middleware made two narrow changes:

1. Interpret empty or dot root aliases as `/` before a search tool executes. The stored path reproduction shows that an empty path became `/.` and missed a file that a search at `/` found.
2. When the complete unfiltered StateBackend mapping is empty, append that fact to the tool observation. This tells the model why more searching cannot recover the input.

It does not impose a tool-call cap, block discovery, or add broad source-selection instructions to every model call. The empty-workspace note does ask for input, so it still guides behavior; the distinction is the concrete condition supporting that guidance.

Across three recorded empty-workspace attempts per retained variant, baseline tool counts were 4, 4, 4 and conservative counts were 1, 1, 1. These were historically paced requests, not measurements of raw inference speed.

## Why the broad version was rejected

The rejected middleware included those tool-observation changes and also added model-call guidance to use a unique plausible match without redundant confirmation. The user request still explicitly required a choice when several sources were plausible. The rejected policy also mentioned asking when multiple sources remained, but that instruction did not prevent the observed mistake.

Read `ambiguity_extracts` in the reviewed JSON:

| Observation | Baseline | Broad candidate, rejected | Conservative |
|---|---|---|---|
| Root listing | Both `/a/` and `/b/` | Both `/a/` and `/b/` | Both `/a/` and `/b/` |
| Discovery afterward | Listed both directories | Listed only `/a/` | Listed both directories |
| Action | Asked which source | Read `/a/data.txt`, wrote `/out.txt` | Asked which source |
| Correct handling | Yes | No | Yes |

The rejected run's `read_file` returned `north` then `west`. Its write tool reported `Updated file /out.txt`, and the final filesystem contained `west` then `north`. The write succeeded technically, but choosing its source violated the task. The final answer accurately reported that write; the failure was the unsupported source choice, not a fabricated success message.

**One source discovered is not evidence that only one source exists.** This is the architectural lesson: the runtime's reliable facts should support the agent's discretion. Broad instructions cannot replace evidence of uniqueness.

The original rejection-marker JSON includes stale generic scorer-reason text suggesting no output. That text contradicts its own saved output. This review preserves the marker's source hash and the actual observed tool results; it does not use that boilerplate as evidence. The original artifacts remain untouched.

## Seven-case historical comparison

| Case | Baseline | Broad, rejected | Conservative |
|---|---|---|---|
| Empty workspace | Correct stop | Correct stop | Correct stop |
| Wrong directory | Failed | Failed | Completed |
| Nested source | Graph-limit failure | Completed | Completed |
| Suggested alternate filename | Unnecessary question | Unnecessary question | Unnecessary question |
| Ambiguous sources | Correct question | Incorrect source choice | Correct question |
| Temporary read failure | Recovered | Recovered | Recovered |
| Requested file exists | Completed | Completed | Completed |

Correct handling was 4/7, 4/7 and 6/7, respectively. Correct stopping is not task completion. The baseline nested run reached the same twenty-step limit as the others; it remains a behavioral failure, not an excluded infrastructure attempt. The seven-case roster is retrospective: the existing-file control was added after the initial six-case baseline sweep. Do not describe all twenty-five runs as a prospectively frozen design.

The observations support the conservative combination in this small local cohort. They do not isolate each component's contribution, establish statistical significance, or guarantee behavior on other models.

## Reuse without rebuilding

The review hash-links these existing components rather than copying or importing their live-call entry point:

- `run_lab.py`: `Recorder`, seven `CASES`, `query_for`, `score`, and the injected temporary-read backend.
- `conservative_middleware.py`: the retained synchronous StateBackend prototype.
- `recovery_middleware.py`: rejected comparison source only; never the selected default.
- `contract_checks.py`: four root-alias checks, explicit-scope preservation, empty-state observation, and the distinction between an empty directory and an empty workspace.

The seven contract outcomes are stored historical scripted graph results. They were not executed again during this review. Later extraction should reuse those contracts and record source/destination hashes and adaptations. Importing the original runner today would load provider/tracing dependencies and set project configuration, so it is not part of the standard-library offline path.

Historical scorer labels are retained as labels, not reissued by a new semantic judge. The original recorder, full private traces, and checkpoint dumps remain outside the public export. Hashes detect drift against these reviewed files; they cannot authenticate the historical execution revision, which remains unknown.

## Boundaries and next milestone

The conservative rule assumes a synchronous, complete, unfiltered StateBackend. Empty graph state does not prove that a disk, remote backend, or permission-filtered view is empty. Async behavior and concurrent file additions were not evaluated.

The later explicit-alternative and GPT-OSS 20B cohorts remain separate and are not used to improve these seven-case scores. In particular, the unresolved 120B original-present failure remains a failure in its own cohort. This review neither reclassifies it nor promotes the later alternative-selection middleware.

The narrow review now has offline consistency checks and negative tampering tests. A full per-run search export and validation beyond the three ambiguity extracts remain future packaging work. Portable scripted graph execution remains future work. Before any new experiment, record the learner's prediction; live experiments also require a bounded run count and an agreed token budget. Routine artifact packaging requires neither a model call nor a quiz answer.
