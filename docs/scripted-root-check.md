# Watch the proposal and execution diverge

## What we ran

Learner prediction: not supplied; the learner requested immediate execution. The assistant hypothesis was that middleware can change execution arguments while retaining the original model proposal. This is explicitly not a prediction attributed to the learner.

We reused the first root-alias fixture and scripted-model pattern from the original seven contracts. Two fresh graphs used the same `/incoming/data.txt` file and the same scripted `glob` proposal. One ran without middleware and one used the byte-identical extracted conservative middleware. We reused the original Recorder class body unchanged, with a standalone module header/imports, and added observation of the next model input. The live runner, `.env` loading and provider setup were not copied.

## Actual evidence

| Observation | Baseline | Conservative middleware |
|---|---|---|
| Proposal retained in conversation | Empty path | Empty path |
| Arguments received by actual tool callback | Empty path | `/` |
| Tool result | `No files found` | `['/incoming/data.txt']` |
| Next scripted model call received that result | Yes | Yes |
| Initial file contents preserved | Yes | Yes |

Read [the saved report](../results/scripted-root-check-20261102.json), especially `conversation_proposal`, `actual_tool_args`, `tool_result`, and `next_model_received_tool_result`. The proposal and executed request are different evidence surfaces. Conversation history alone would hide the correction. The actual argument comes from the tool-start callback, not merely the middleware's own event.

Deep Agents assembles the capabilities around the supplied model. LangChain's agent/tool execution applies the middleware wrapper, whose corrected request reaches the search tool. LangGraph executes those steps and carries messages/state between them. The subsequent model-input callback records the tool observation arriving back at the model. We did not replace their execution loop.

The model here is scripted: it emits the declared tool call and then `done`. It does not independently discover a source, interpret the result or choose a recovery strategy. Two scripted model responses per condition are not two live-provider calls. This establishes the argument/observation contract, not intelligent task completion or general agent reliability.

## Before and after implementation

The opt-in contract initially failed because the CLI did not yet support `scripted-root-check`. That was a missing harness command, not a failed graph or model trial. After extraction and implementation, the same consumer contract passed through the public CLI. The saved execution contains the two actual graph conditions.

The root-alias fixture is one of the original seven contract cases. The other six have not been executed in this milestone. The rejected broad middleware is not imported or selected. No historical model evaluations were rerun.

## Reproduction boundary

Use [the opt-in runtime instructions](../runtime_checks/README.md). The recorded environment used Python 3.14.6, editable Deep Agents 0.7.32, LangChain 1.4.7, LangChain Core 1.7.0, LangGraph 1.2.17, LangGraph Prebuilt 1.1.0 and LangSmith 0.14.12. Selected loaded-source hashes, extracted source/destination hashes and the clean tracked SDK checkout revision observed now are recorded. That revision does not identify the historical October executions. A fresh installation from package requirements alone has not been verified as equivalent; those pins are not a full dependency lock.

Tracing is disabled and Python socket operations are blocked before importing runtime dependencies. No model provider is selected, keys are not needed, and the command does not load `.env`. This is an accidental-network guard, not an OS security sandbox. Raw callback journals remain in ignored local work directories; the public report contains no private paths or tracing IDs.

The standard-library offline verification and development suite remain separate and do not import runtime dependencies. The new command checks extracted component hashes before execution; the default offline command does not yet validate this new saved result. Pending approval and post-commit crash/resume are still untested together.

## Follow-up

The [remaining six fixtures](scripted-filesystem-check.md) subsequently passed in a separate fresh scripted execution. That follow-up generalized the shared helper and added distinct raw-tool and model-facing observations. This document and its saved report describe the earlier first-root milestone.
