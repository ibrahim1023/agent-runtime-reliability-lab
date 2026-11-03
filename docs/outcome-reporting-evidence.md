# A valid receipt does not establish a single effect

The learner predicted **“Completed once, because the receipt says recorded”** when asked what to report if receiver evidence becomes unreadable after a run. This experiment tests that conclusion separately from graph recovery.

The five clean-install crash runs had already finished. We reused their actual local SQLite receiver databases for five fresh read-only reporting observations. Two additional controlled fixtures used a missing configured receiver path and invalid database bytes, while retaining an earlier valid receipt from a completed run. We did not corrupt, remove or rerun the source receivers.

The seven checks matched the [frozen expectations](../results/outcome-reporting-plan-v1.json). They made zero new graph worker invocations and zero provider calls. Development tests on separate temporary databases are not counted as these seven observations.

## Before and after

Before, the unprotected control's scripted answer echoed its final successful ToolMessage. That message contained one valid receipt. It did not mention that an earlier attempt had also committed.

The new application reporter reads a local receiver snapshot after the isolated graph workers have stopped. For that control, it observed two rows under the same operation ID and reported:

> Duplicate detected: the local receiver contains 2 committed records for this operation. The record-once task was not completed correctly.

The task still failed. The reporter neither deleted a duplicate nor made the receiver idempotent. The improvement is that the application can disclose the discrepancy using independent receiver evidence.

| Observation | Receiver records available to reporter | New application outcome |
|---|---:|---|
| Protected approve 1 | 1 | `completed_once` |
| Protected approve 2 | 1 | `completed_once` |
| Unprotected control | 2 | `duplicate_detected` |
| Protected edit | 1, approved replacement | `completed_once` |
| Protected reject | 0 | `rejected` |
| Missing configured receiver, earlier valid receipt retained | Unknown | `outcome_unknown` |
| Invalid receiver fixture, earlier valid receipt retained | Unknown | `outcome_unknown` |

Both evidence failures produced:

> The outcome is unknown: receiver evidence is unavailable or execution is unfinished. I cannot verify that the action completed exactly once.

The earlier receipt supports “an action committed before.” It cannot establish the current total number of effects. Unknown evidence therefore has `observed_effects: null` and `task_completed: null`, rather than zero effects or successful completion. This is a reporting policy grounded in the missing information, not proof that the earlier action did not happen.

## The architectural change

This adds an application reporting function, `reconcile_action`, outside the graph/model loop. It opens the existing receiver read-only, queries the requested operation in one snapshot, and compares row contents and receipt fields with the persisted approved payload. It uses the reviewer replacement for edit cases. Missing or invalid databases return unknown, and a missing database is not silently created.

The caller supplies review decision and terminal execution context. This fixture establishes that its workers stopped before reconciliation. A running distributed system would need a stronger way to establish that no further attempts can commit. One snapshot cannot promise what future writers will do.

The reporter also has development coverage for a finished graph with no recorded action, rows despite rejection, conflicting contents/receipts, unrelated operation rows and unfinished graph execution. These are development contracts, not extra runtime trials. Eight new tests bring the development suite to 83 tests.

## Evidence and reproduction boundary

[The reviewed execution export](../results/fresh/outcome-reporting-v1/execution.json) retains source SQL observations, original scripted answers, application reports, implementation hash and original database hashes. Source database bytes were unchanged after reads. Raw databases and private logs remain local.

Run the development checks with:

```sh
python3 -S -m unittest discover -s tests -v
```

The tests create disposable local receivers to exercise the reporting behavior. They do not recreate the earlier graph execution or represent a second seven-case experiment. The saved execution is hash-linked in the manifest and separately reviewed; the default offline command does not yet validate this new export automatically.

This does not demonstrate model honesty, change a Deep Agents default, integrate a new tool into the agent, prove authenticated review or solve remote reconciliation. The original model answers remain intact. We have added a small evidence-aware application report that can be connected to the execution flow in a later, separately bounded experiment.
