# A new invocation can get a fresh run allowance

The learner predicted **“No—the checkpoint keeps the run allowance used up”** after a completed turn, a clean process restart and a new user message in the same conversation. The experiment contradicted that prediction for a run-only limit. A conversation-wide thread limit preserved its allowance across the restart.

## What we tested

Two conditions each used two turns in separate fresh processes, with a stable application-generated thread ID and a SQLite checkpoint database shared between their turns. Both invocations supplied a new user message. This is a clean restart/new-turn experiment, not abrupt crash recovery, pending-work resume or `invoke(None)`.

The controlled read always failed. Native retry allowed two retries after the initial attempt: three tool-body entries per executed tool request. Native `ToolCallLimitMiddleware` used `run_limit=1`, with either no thread limit or `thread_limit=1`, and `exit_behavior='end'`.

| Setting | First-turn entries | New-turn entries after restart | Total |
|---|---:|---:|---:|
| Run limit only | 3 | 3 | 6 |
| Run limit plus conversation/thread limit | 3 | 0 | 3 |

Four graph invocations ran in four fresh workers, once each, with nine total tool-body entries and zero provider calls. No read task succeeded. Both conditions correctly reached their native budget stops.

## What the checkpoint preserved

The allowlisted checkpoint observations showed:

| Setting | Conversation counter before/after turn 1 | Before/after turn 2 |
|---|---|---|
| Run only | 0 → 1 | 1 → 2 |
| Run + thread | 0 → 1 | 1 → 1 |

These counters count accepted logical tool requests, not each internal retry. One accepted request can have three body entries. Blocked requests did not increase the persisted accepted-call counter.

The run counter was absent from all recorded checkpoint observations. The installed source declares that field with `UntrackedValue`, whose value is never checkpointed. The thread counter uses a persisted state field. The four workers' inspected module hashes matched the frozen source fingerprints.

The second turn's model inputs contained the previous turn's ToolMessages. The checkpoint therefore preserved conversation history as well as the thread counter. The run allowance renewed on the new invocation; this should not be described as the restart wiping the conversation.

In the run-only condition, another tool request was allowed and used three more attempts. With the thread limit, the first request in the second turn was blocked before entering the tool body. That still required one scripted model generation to propose it: a tool-call cap is not a model-generation cap.

## Identity defines the scope

Each condition used the same thread ID across its two workers. Different conditions had separate thread IDs and databases. A new thread ID would create a different conversation budget scope; the test does not establish a global user/account allowance.

This connects to earlier lessons: the operation ID identifies one intended action for receiver deduplication, while the thread ID identifies the conversation carrying persistent state. They have different jobs, and both must remain stable when their continuity is required.

## Evidence, review and limits

[The frozen plan](../results/budget-lifetime-plan-v1.json) records expected body/model counts and checkpoint counter continuity. [The execution export](../results/fresh/budget-lifetime-v1/execution.json) retains worker PIDs, phase-specific request IDs, actual entries, model observations, native limit messages and selected counter values. Raw checkpoint databases remain private local work artifacts; no raw checkpoint dump is published.

All four workers exited zero without timeout. Review found that the original launcher could accept valid phase JSON even if a worker later exited nonzero. [A1](../results/budget-lifetime-launch-validation-a1.json) adds successful-exit checks to both condition and overall fixture verdicts. The saved worker outcomes already satisfy the stricter checks, so no graph rerun was needed. Executed source and subsequently guarded driver source are retained separately. The corrected full command was not rerun after that launch-guard change.

The offline verifier now checks the saved evidence in `budget_lifetime_evidence`, including fresh PIDs, same-thread continuity, checkpoint fields, prior message history, actual tool entries, native final messages and successful worker exits. It starts no workers and reads no private checkpoints.

```sh
python3 -S -m reliability_lab verify-offline
python3 -S -m unittest discover -s tests -v
```

Development verification passed 124 tests on Python 3.14.6. The existing six receiver contracts remain separately identified as fresh executions. To deliberately create a new four-worker attempt with optional runtime dependencies:

```sh
python -m reliability_lab budget-lifetime-check --prediction 'your prediction'
```

This demonstrates completed sequential turns on one installed runtime, with scripted model behavior. It does not establish budget behavior during an unfinished crash/resume, concurrent invocations, model/provider-internal retries, token costs or a global wall-clock allowance. It changes no Deep Agents default or SDK source. The earlier per-invocation and timeout evidence remains separate.
