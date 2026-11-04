# One tool request can contain several attempts

The learner predicted **“Up to three times”** for a tool-call limit of one with two retries. The fresh native-runtime experiment confirmed that prediction. The limiter allowed one tool request; native retry entered that request's body three times before giving up. A second model request was blocked before its tool body ran.

This extends the retry lesson: an attempt limit inside one call does not stop the model from proposing another call and receiving a fresh retry allowance.

## Four cases, one execution

We ran four scripted Deep Agents graphs once in the verified package environment, in one worker, with zero provider calls. The controlled read always raised `OSError`. The scripted model deliberately proposed another read after each error, up to four requests, then stopped with an explicit failure answer. The baseline was bounded by that script and an outer guard, not an unbounded live-model trial.

| Configuration | Model generations | Tool requests proposed | Tool requests actually executed | Actual tool-body entries |
|---|---:|---:|---:|---:|
| Two retries per call; no native call limiter | 5 | 4 | 4 | 12 |
| Tool-call limit 1 | 2 | 2 | 1 | 3 |
| Model-call limit 2 | 2 | 2 | 2 | 6 |
| Tool-call limit 2 and model-call limit 3 | 3 | 3 | 2 | 6 |

The experiment used twenty-seven actual tool-body entries in total. Every entry failed deliberately, so none of these cases completed the read task. All graphs ended normally: stopping at a configured limit is valid control flow, not task success.

## What each limit means

The installed LangChain `ToolRetryMiddleware` applies its retry allowance inside a tool request. Two retries allow the initial attempt plus two more attempts.

`ToolCallLimitMiddleware` checks model-proposed tool calls after model generation. It can block the next request before executing its body. It does not count each internal retry as a new model request. With one accepted request and two retries, three body entries remain possible.

`ModelCallLimitMiddleware` checks before the next model generation. In its case, two model generations each proposed one read, giving six body entries in total. The third model generation was prevented, and native middleware supplied the final limit message.

In the combined case, two requests each used three body entries. The third model generation proposed another request, but the tool-call limiter blocked it and ended execution. In this serial fixture, the observed maximum is two accepted requests times three attempts: six body entries.

These settings are per graph invocation. We did not test counters across crash/resume, multiple invocations, persistent thread limits, parallel tool batches, provider-internal retries or wall-clock timeouts in this milestone. The earlier timeout evidence remains separate.

## Why the final message says 2/1

The tool-limit-one case returned:

> Tool call limit reached: run limit exceeded (2/1 calls).

The second request was proposed and blocked. The installed middleware's run count includes that blocked request; it does not mean two tool requests executed. Only the first executed, with three body entries. Separate IDs in the published trace make that visible.

The baseline's final failure answer came from the scripted model. The limited cases' final answers were injected by native middleware. They are labelled separately in the evidence. This does not demonstrate that a real model learned to respect a budget.

## Evidence and validation

The [frozen plan](../results/run-budget-plan-v1.json) records the four cases, source fingerprints and execution bound. [The execution export](../results/fresh/run-budget-v1/execution.json) retains each model generation, proposed ID, tool entry ID, returned ToolMessage, final answer and its source. The launcher finished successfully without timeout; there were no runtime reruns.

Review found the first evidence checker accepted a missing blocked-call ToolMessage and a changed final success answer. Two regressions demonstrated those gaps. [Assessment amendment A1](../results/run-budget-assessment-amendment-a1.json) now requires a result for every proposed ID, including blocked ones, and checks the final answer/source against the recorded native behavior or scripted failure. Model input observations are also bound to returned ToolMessages. All original verdicts remained identical and no graph was rerun. Original executed source and assessor bytes are preserved.

Native limit-message rendering is checked against the inspected installed version. This is deterministic evidence consistency, not a general semantic answer-quality judge or protection against coherent artifact fabrication.

```sh
python3 -S -m reliability_lab verify-offline
python3 -S -m unittest discover -s tests -v
```

The `run_budget_evidence` stage checks the four saved graphs and twenty-seven entries without running more graphs. The six existing receiver contracts still execute fresh as a separate stage. The development suite passed 118 tests on Python 3.14.6.

To deliberately start a new four-case attempt with optional runtime dependencies:

```sh
python -m reliability_lab run-budget-check --prediction 'your prediction'
```

The command uses existing native middleware; it does not add an agent loop or change a Deep Agents default. Its scripted read is a controlled failure probe, not a file-operation model evaluation.
