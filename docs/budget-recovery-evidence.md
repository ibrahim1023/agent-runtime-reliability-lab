# A spent budget can still allow pending work to replay

We combined the existing approval, checkpoint, budget and receiver patterns. The result was simple: the pending tool replayed after the crash even though its conversation allowance had already been counted. A genuinely new request was blocked afterward.

## What happened

Each condition allowed one logical tool request in the conversation. The first action paused for simulated approval, survived an undecided restart, then committed and exited with code 86 before returning its result. A fresh process resumed with `None`, without a new input or approval decision.

| Receiver | Entries of the pending tool | Effects of the first action | Entries of the new action |
|---|---:|---:|---:|
| Protected | 2 | 1 | 0 |
| Unprotected control | 2 | 2 | 0 |

The protected receiver returned its exact first receipt on replay. The control created a second receipt and a duplicate effect. Its record-once task failed. Both conditions correctly blocked the later new action.

The budget counter reached one before the first commit and stayed one through replay and the later request. The pending replay did not pass through a new model-request budget check. It resumed already accepted graph work. The new request used a different tool-call ID and a different application operation ID, so zero entries for it demonstrate budget blocking rather than receiver deduplication.

The protections have different jobs:

- The budget limits new accepted requests.
- The checkpoint restores pending work.
- The protected receiver prevents a repeated action from creating another effect.

A budget of one therefore does not guarantee one physical tool execution or one receiver effect.

## Approval order was visible too

In this installed configuration, approval runs before the budget check. The first approval pause had a counter of zero; approval was followed by budget acceptance and the counter becoming one.

The later new request also paused for approval. We supplied its own simulated approval once, then the spent budget blocked it before tool execution. Approval did not override the budget. This ordering means an approval prompt can appear for work the budget will subsequently deny; the experiment records that behavior without changing middleware order.

No new approval appeared during post-crash replay. The two recorded decisions were for the first request and the genuinely new request.

## Bound and evidence

[The frozen plan](../results/budget-recovery-plan-v1.json) defined two conditions and six fresh worker phases each: initial pause, undecided restore, approve/commit/crash, resume, new request, and approve/block. All twelve workers had their expected exits, including two deliberate exits with code 86. There were four actual tool-body entries and zero provider calls. The experiment ran once without case retries.

[The execution export](../results/fresh/budget-recovery-v1/execution.json) preserves phase exits, review requests, selected checkpoint counters, stable thread/operation identities, actual receipts, model-visible results and the blocked ToolMessage. Every worker checked frozen native module fingerprints before invoking the graph. Executed lab source bytes are preserved separately. Raw checkpoint databases and private logs stay local.

The learner's answer, “Yes—the spent budget blocks the replay,” arrived after execution. The original run retains `learner_prediction: not supplied`; [a separate learning note](../results/budget-recovery-learning-note.json) records the late answer. It is not presented as a prospective prediction score.

## Checks and limits

```sh
python3 -S -m reliability_lab verify-offline
python3 -S -m unittest discover -s tests -v
```

The `budget_recovery_evidence` stage validates the stored phase inputs, exact review decisions, native source identities, receipts, budget counters, model observations and new-request block. It starts no workers. Development verification passed 130 tests on Python 3.14.6; the existing six receiver contracts remain separately identified as fresh execution.

For a deliberate new twelve-worker attempt in a compatible optional environment:

```sh
python -m reliability_lab budget-recovery-check --prediction 'your prediction'
```

This is a scripted local synchronous fixture with a simulated reviewer. It is not authenticated review, machine power-loss recovery, concurrent budget enforcement or arbitrary remote exactly-once delivery. It changes no SDK default and does not establish a user/account-wide resource budget. The original unprotected duplicate remains visible as task failure.
