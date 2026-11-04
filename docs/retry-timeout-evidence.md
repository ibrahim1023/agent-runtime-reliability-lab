# A timeout does not prove the write stopped

The learner predicted **“No—the timeout prevents the commit”** for a synchronous write already running when a graph step deadline expires. The native-runtime timeout case contradicted that prediction: the receiver committed before the caller received `TimeoutError`.

This milestone inspected the installed runtime source, then executed six scripted Deep Agents graph cases using native LangChain retry middleware and LangGraph synchronous `step_timeout`. There were zero provider calls. Coverage spans a preserved partial attempt and a one-case continuation; it was not one uninterrupted successful suite.

## Where the controls live

The inspected Deep Agents factory assembles middleware and passes it to LangChain's `create_agent`. Caller middleware is a supported extension point. The lab configured the installed `ToolRetryMiddleware`; it did not implement an agent loop or patch SDK dependencies.

`ToolRetryMiddleware.max_retries` counts retries after the initial call. With two retries, one proposed tool call can enter its body three times. `retry_on`, tool-name scope and `on_failure` determine which failures are retried and how exhaustion returns to the graph. This experiment selected `OSError`, zero delay and no jitter. A simulated `ResponseLost` subclasses `TimeoutError`, which is an `OSError` subtype.

LangGraph owns graph execution and the step timeout. Its installed synchronous background executor attempts cancellation of eligible work, then waits for running tasks during cleanup. That is different from forcibly stopping an already running Python tool thread.

These statements concern the recorded installed versions and source hashes, not every future runtime release. The inspected modules and hashes are in the [frozen plan](../results/retry-timeout-plan-v1.json).

## Actual graph cases

| Case | Tool-body entries | Receiver effects | Graph result |
|---|---:|---:|---|
| Temporary read failure | 2 | 0 | Completed; successful read ToolMessage |
| Persistent read failure | 3 | 0 | Completed; error ToolMessage after exhaustion |
| Unprotected write with broad retry | 2 | 2 | Completed; latest receipt returned |
| Unprotected write with retries scoped to reads | 1 | 1 | `ResponseLost` propagated |
| Protected write with retry | 2 | 1 | Completed; exact first receipt reused |
| Running synchronous write with step timeout | 1 | 1 | `TimeoutError` reached caller after commit |

There were six graph invocations and eleven actual tool-body entries. The scripted model proposed one tool call in each case and never reissued it. These limits do not prove a whole agent request is globally bounded if a different model keeps proposing new calls. Retry delays were zero, so backoff behavior and jitter were not tested.

In the persistent-read case, native exhaustion returned an error ToolMessage and the scripted model echoed it. The graph finished, but the read did not succeed. That is another concrete example of graph completion differing from task success.

## Why retry scope matters

For each write case except the native step timeout, the first tool entry committed its note, then raised a controlled lost-response exception before returning its receipt. This was a local fault injection, not a real network request.

Broad retry entered the unprotected write again and produced a second effect. The narrower middleware policy applied only to `read_probe`, so it did not retry `write_probe`. The exception propagated with one committed action. Stopping a retry avoids that duplicate, but a caller still needs reconciliation to establish and report the action's outcome.

The protected case allowed retry with the same application operation ID. The receiver recognized replay and returned the original receipt without another effect. This is a local atomic SQLite property, not arbitrary remote exactly-once delivery.

## The timeout trace

The timeout graph had a 0.050-second step timeout. Its synchronous tool waited behind a controlled gate; the controller released it roughly 0.2 seconds after tool entry. Recorded case-clock events were approximately:

```text
0.049 s  model proposed the write
0.050 s  tool entered
0.252 s  controller released the tool
0.255 s  receiver committed
0.257 s  caller observed TimeoutError
```

The order is the key evidence. The configured timeout did not prevent the running tool from committing. The synchronous graph call waited through cleanup before exposing the timeout to its caller. The internal instant when the runner detected its deadline was not separately instrumented; event times above are observed tool/controller/caller events.

No final ToolMessage reached the next model invocation in that case. The observer nevertheless found the committed receiver row. A timeout error alone therefore does not establish that an action failed or never happened. Blind resubmission can be unsafe.

This tests one local synchronous tool and a native per-step deadline. It does not establish asynchronous cancellation behavior, remote-operation cancellation or a hard wall-clock response bound. The gate had its own bounded wait, and the controller was joined before the case was recorded.

## Preserved interruptions and amendments

Two implementation mistakes interrupted execution:

1. The launcher resolved the virtual environment's Python symlink to the system interpreter. That worker failed with `ModuleNotFoundError` before any graph ran. [A1](../results/native-retry-launch-amendment-a1.json) allowed one corrected launch and explicitly counted the extra process.
2. The corrected worker invoked the first five cases, then failed during timeout-case construction because the fixture assumed `agent.bound`. Inspection showed this installed graph's `with_config` returns a configured graph copy. [A2](../results/native-retry-timeout-amendment-a2.json) corrected the attribute and allowed only the remaining timeout invocation. The first five were not rerun.

Total process accounting is three workers including setup and continuation. The six-graph and tool-entry budgets stayed bounded; original failed/partial artifacts remain published. [Coverage](../results/fresh/native-retry-v1/coverage.json) explicitly marks `single_uninterrupted_successful_attempt: false`.

Review also found that the initial assessor compared model-facing status without binding answer text to the recorded ToolMessage. Two regressions demonstrated the gap. [A3](../results/native-retry-assessment-amendment-a3.json) strengthens content/event/answer consistency and checks successful write responses against the actual receiver receipt. Reassessment changed none of the six saved verdicts and executed no new graph. Original implementation and assessor bytes are preserved.

The first five-case worker recorded installed runtime fingerprints. The continuation used the same virtual-environment executable path but did not independently collect another complete runtime fingerprint. That limitation remains explicit.

## Verification and evidence

- [Initial zero-case setup interruption](../results/fresh/native-retry-v1/setup-interruption.json)
- [Five-case partial attempt](../results/fresh/native-retry-v1/partial-five-cases.json)
- [Timeout-only continuation](../results/fresh/native-retry-v1/timeout-continuation.json)
- [Combined coverage, actual events and separate outcome dimensions](../results/fresh/native-retry-v1/coverage.json)

```sh
python3 -S -m reliability_lab verify-offline
python3 -S -m unittest discover -s tests -v
```

The `native_retry_evidence` stage validates the saved six-case coverage, event order, eleven entries, receipt identity and preserved interruptions. It imports no optional runtime and starts no graphs. The existing six receiver contracts execute fresh in their separate stage. Development verification passed 111 tests on Python 3.14.6.

To deliberately start a new six-case attempt in a compatible optional runtime environment:

```sh
python -m reliability_lab native-retry-check --prediction 'your prediction'
```

The corrected full-suite command has not been rerun as one uninterrupted attempt; recorded coverage is five cases plus one continuation. The earlier unavailable-receiver evidence remains separate and was not counted as another native graph case. Hashes and deterministic consistency checks are not a new semantic model judge or proof against coherent artifact fabrication.
