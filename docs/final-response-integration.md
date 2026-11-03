# From a correct report to the application's final response

The learner predicted **“Report uncertainty and preserve the graph answer separately.”** The [frozen experiment](../results/final-response-plan-v1.json) tested that behavior through a new application command, after real scripted graph recovery.

Previously, receiver reconciliation was a separately tested function. The graph's final answer still repeated its ToolMessage, including a successful receipt in the duplicate control. Now `reported-crash-check` runs the existing recovery fixture and passes each graph result through the application final-response boundary. The returned command report contains both `model_answer` and the selected `user_response`.

The application response comes from receiver reconciliation. A successful graph answer is not a fallback when verification fails. For confirmed single-effect actions, the response also names the approved recorded contents.

## One bounded execution

We ran the five frozen crash/resume cases once, using the existing verified fresh-package environment: nineteen new worker processes, zero provider calls, zero provider tokens, no automatic retries. After those workers stopped, we checked five normal responses and one unavailable-receiver response using a missing configured path. That fault check reused the first completed graph result and left the actual receiver intact; it did not run a sixth graph or create a sixth independent task.

| Response observation | Application result | Task completion represented |
|---|---|---|
| Protected approve 1 | One committed record; names `record-once` | True |
| Protected approve 2 | One committed record; names `record-once` | True |
| Unprotected control | Discloses two committed records and record-once failure | False |
| Protected edit | One committed record; names `reviewer-approved` | True |
| Protected reject | Reports rejection and no committed record | False; correct handling |
| First graph result with receiver verification unavailable | Reports unknown; preserves successful model answer separately | Unknown |

The run took about 9.190 seconds of local wall time. That is an observation, not a controlled performance comparison. All six response contracts matched expectations. The five graph cases still include an intentionally duplicated task and a correctly rejected action, so fixture success is not universal task success.

## The important before-and-after

For the unprotected control, the preserved model answer is a valid receipt for its latest committed action. The application now selects:

> Duplicate detected: the local receiver contains 2 committed records for this operation. The record-once task was not completed correctly.

For the controlled unavailable-receiver response, the earlier successful model answer remains in the evidence, but the application selects:

> The outcome is unknown: receiver evidence is unavailable or execution is unfinished. I cannot verify that the action completed exactly once.

For edit, the response names the actual approved replacement:

> The local receiver contains exactly one committed record for this approved operation. Recorded contents: "reviewer-approved".

These are deterministic application responses. This experiment does not claim that a model learned to detect duplicates or express uncertainty, and it changes no Deep Agents default or SDK implementation.

## Automatic evidence checks

The default offline command now includes:

- `clean_install_evidence`: five saved clean-install graph cases and environment/package consistency.
- `outcome_reporting_evidence`: seven saved reporting observations and their original receiver evidence.
- `final_response_evidence`: five saved integrated graph cases and six selected responses.

These are saved-artifact validations, with no new installation, graph execution or private receiver reads. The existing six receiver contracts still execute fresh as a separate stage. Development verification passed 96 tests on Python 3.14.6.

Review found a validator gap: saved clean-install completion claims were not compared with final checkpoint state. A regression first demonstrated acceptance of a contradictory `checkpoint_next: ["tools"]`, then the validator was fixed to bind completion and pending review to the saved observations. The actual saved experiments were consistent and were not rerun. No other important issue was reported in the reviewed delivery path.

## Reproduction and limitations

Validate stored evidence:

```sh
python3 -S -m reliability_lab verify-offline
python3 -S -m unittest discover -s tests -v
```

Deliberately execute a new integration attempt in a compatible optional runtime environment:

```sh
python -m reliability_lab reported-crash-check --prediction 'your prediction'
```

The new command remains outside the two ordinary runtime test methods to avoid automatically repeating nineteen worker phases. [Reviewed execution evidence](../results/fresh/final-response-v1/execution.json) retains raw graph answers, tool results, checkpoint observations, selected application responses and source hashes. Raw databases/checkpoints remain local.

The reporter's assurance is scoped to a closed isolated local operation and its receiver snapshot. The caller establishes execution context; this is not protection against concurrent remote actions or authenticated review. The controlled verification failure is a missing configured path, not every storage failure mode. The embedded graph report retains stale generic preflight wording about editable environments; this invocation reused the separately verified non-editable environment, without a new installation.
