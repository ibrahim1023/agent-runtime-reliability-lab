# A checkpoint can replay a tool after its action committed

On November 3, 2026, we executed the frozen approval → commit → crash → resume plan once: five cases, nineteen fresh worker processes, zero live model calls. The learner predicted: **“Checkpoint prevents the tool from repeating.”** The observed tool journals contradict that prediction at this boundary.

Deep Agents supplied the tools and approval setup. LangChain supplied the agent and approval middleware. LangGraph restored execution from a persistent SQLite checkpoint. The lab reused its SQLite receiver and supplied a scripted model, a simulated reviewer, observation journals and a deliberate process exit. No SDK source or agent loop was changed.

## What survived each restart

1. The first worker proposed `record_action` and paused for review. No tool body ran and no receiver row existed.
2. A fresh worker resumed without a decision. The same review request remained pending. Still no tool entry or effect.
3. Another worker supplied the simulated decision. For approve/edit, the receiver committed, its receipt was journaled and flushed, then the process exited with code 86 before the tool returned.
4. A final fresh worker resumed with `None`: no new user message or review decision. It entered the pending tool again. Protected receivers returned their first receipt; the unprotected receiver committed again.

The checkpoint and receiver are separate transactions. The checkpoint cannot tell that an external action committed when it never received the tool's completed result. The application-generated operation ID survives in a separate identity file and graph configuration. It lets the protected receiver recognize the second attempt as the same operation. A new ID would look like a new action.

The edit survived too: both tool entries used `reviewer-approved`, and the receiver never recorded `original-proposal`. Rejection stopped in phase three, with no tool entry or receiver effect. No new approval request appeared after the post-commit restart.

## Actual results

| Case | Tool-body entries | Committed effects | Receipt on replay | Approved task completed |
|---|---:|---:|---|---|
| Protected approve 1 | 2 | 1 | Exact first receipt | Yes |
| Protected approve 2, fresh repetition | 2 | 1 | Exact first receipt within this case | Yes |
| Unprotected approve control | 2 | 2 | New receipt | No: duplicated action |
| Protected edit | 2 | 1 | Exact approved receipt | Yes, against the replacement |
| Protected reject | 0 | 0 | None | No action; correct rejection handling |

All five graphs finished. That does not mean five user tasks succeeded: three approved single-effect tasks completed; rejection correctly prevented an action; the control duplicated it. The scripted model echoed the actual ToolMessage. In the control that receipt accurately described the latest action, but did not disclose the earlier duplicate. Accordingly, `report_matches_observed_tool_result` is true while `report_accounts_for_all_effects` is false. Neither metric is a general natural-language honesty judge.

Worker wall times totaled about 3.075s and 3.027s for the protected approval repetitions, 2.978s for the control, 2.966s for edit and 2.401s for reject. The whole invocation took 15.028s. These include local process startup and graph/database work; this tiny scripted sample is not an inference or performance benchmark.

## A checker failure is preserved

The [original execution](../results/fresh/crash-resume-v1/execution.json) has `status: failed`. Four contracts met its first assessment; the edit case failed because my checker required the entire ToolMessage to be a JSON receipt.

The actual edit ToolMessage included an upstream explanation of the authorized replacement, followed by `Tool response:` and the receipt. The final scripted answer exactly echoed that message, and its receipt matched the SQL rows. This was a checker false negative, not an edited-payload recovery failure.

[Amendment A1](crash-resume-assessment-amendment-a1.md) documents that assumption and the constrained parser correction. A failing regression demonstrated the issue before the correction. The [separate reassessment](../results/fresh/crash-resume-v1/reassessment-a1.json) checks the same saved observations and supports all five expected fixture contracts. No workers were rerun. The frozen criteria and original failed assessment remain unchanged; the first implementation is preserved in commit `7bc4863`.

An independent review found that initial tampering tests could stop at a stale input hash instead of the intended semantic contradiction. The corrected tests update the linked hashes and assert the actual contradiction reason. The review found no evidence-invalidating flaw in the inspected execution.

## Reproduce or validate

Validate the saved evidence without runtime dependencies or new graph execution:

```sh
python3 -S -m reliability_lab verify-offline
python3 -S -m unittest discover -s tests -v
```

`crash_resume_evidence` checks five saved cases separately from historical exports and the six fresh receiver contracts. Each ordinary verification does not add nineteen new workers or five new trials. Development verification passed 75 tests on Python 3.14.6.

To deliberately create a **new** five-case attempt in a compatible optional runtime environment:

```sh
python -m reliability_lab crash-resume-check --prediction 'your prediction here'
```

Without the option, a new attempt records `not supplied`; it does not reuse this learner's prediction. New attempts use fresh directories under ignored `work/crash-resume/`. Logs, raw checkpoints and databases stay local. A new attempt has the same maximum nineteen workers, 30 seconds per worker, 600 seconds total and graph recursion limit ten; failures are retained without retries. The crash check is not automatically invoked by either existing runtime test method.

## Boundaries of the evidence

This reused an existing editable Deep Agents environment, not a verified clean installation. Runtime versions, selected loaded module hashes and execution-time lab source hashes are in the execution report. The first executed source matches commit `7bc4863`; later assessment and prediction-attribution corrections are separate changes. The historical SDK revision is still unknown.

The application receiver, checkpoint and journal are local files, and identities/payloads are synthetic. This is abrupt process exit, not machine/power failure or arbitrary remote exactly-once delivery. Python socket operations were blocked before runtime imports, tracing disabled and worker environment variables allowlisted. This is not an OS security sandbox. The reviewer was simulated even where upstream explanatory text says “human reviewer.”

In the original crash phase, `pending_review: false` means no interrupt result returned before process exit; it is not an inspection of checkpoint state at that instant. Initial/undecided/final phase observations establish the review behavior. Future fixture reports use null when the worker returned no observation.

Hashes detect mismatches, and consistency checks reject the covered contradictions. They cannot authenticate a coherently fabricated replacement of all artifacts and metadata.
