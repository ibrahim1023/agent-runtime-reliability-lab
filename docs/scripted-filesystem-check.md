# An empty directory is not an empty workspace

## What ran

We continued the existing scripted middleware experiment without another prediction quiz. No learner prediction was supplied; the assistant hypothesis is recorded separately. Six fresh graph executions reused the remaining original fixtures: `.`, `./`, `/.`, explicit `/visible` search scope, a completely empty workspace, and an empty `/missing` directory while a file existed elsewhere. The original empty-root fixture also passed as a regression after the shared harness was generalized, adding its two conditions to the test execution.

The conservative middleware and extracted Recorder remain unchanged. The first fixture's runner now accepts explicit tool arguments and initial files, including an actually empty mapping. The new command uses that same Deep Agents/StateBackend/model/tool path; it does not implement another agent loop. The model is scripted and makes no independent decisions.

## The decisive observations

| Fixture | Raw tool result | Observation delivered to the model |
|---|---|---|
| Workspace has zero files | `No files found` | Same result plus the verified empty-workspace note |
| `/missing` is empty but `/incoming/data.txt` exists | `No files found` | Same result, with no zero-files claim |

The raw results are identical, but their interpretation differs because the complete unfiltered StateBackend state differs. A search result about one directory cannot establish workspace emptiness.

The added context appeared after the underlying tool-end callback. We therefore record two evidence surfaces: `tool_result` is the original Recorder's raw callback observation, while `model_facing_tool_result` is the actual ToolMessage retained in graph conversation state. A model-input callback confirms the latter reached the next scripted response. It would be misleading to report the middleware's note as text the underlying `ls` tool produced.

The three root aliases were preserved in the model proposals but became `/` at tool execution and found the file. The explicit `/visible` scope stayed `/visible`, returned its visible file and excluded `/other/data.txt`. All six fixtures preserved their initial file contents and delivered their resulting observation to the next scripted model call.

## What passed, and what did not run

[The saved six-case report](../results/scripted-filesystem-check-20261102.json) contains actual per-case arguments, raw/model-facing results and current dependency/source identities. Six fixtures plus the earlier empty-root fixture now cover all seven original middleware contracts with fresh scripted evidence. The two opt-in unittest methods execute eight graph conditions: six here and the earlier baseline/conservative pair. They are not eight live-model evaluations.

The new command's test first failed because that CLI option did not exist, then passed after implementation. No historical model trial was rerun. No package was installed. This does not test whether an LLM follows the enriched observation, whether the note is safe on remote/filtered backends, or how approval/crash/resume interact. The rejected broad middleware remains unselected.

## Run and provenance

With the optional recorded runtime environment:

```sh
python -m reliability_lab scripted-filesystem-check
python -m unittest discover -s runtime_checks -v
```

Tracing is disabled, no .env is loaded, and Python socket operations are blocked before dependency imports. This is not an OS sandbox. The recorded environment still uses editable Deep Agents; selected versions/hashes are recorded, not a full dependency lock or proof of a historical revision. A clean installation has not been verified.

The original first-root report is unchanged and describes the harness at commit `2b47bea`; its source hash need not match the subsequently generalized helper. The new report binds the current helper. Original lab artifacts and historical contract-results remain untouched. The dependency-free offline command still validates its existing evidence and receiver stages; it does not yet validate these fresh scripted-runtime result files.
