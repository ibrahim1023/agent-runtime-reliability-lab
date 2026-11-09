# Avoid approval prompts for work the budget will block

Previously, a new request with a spent conversation allowance could pause for approval, then be denied by the native limiter after approval. The lab's candidate uses the installed approval middleware's public `when` callback to check eligibility before asking.

The callback is read-only. With allowance available, review remains required. With allowance spent, it skips the prompt and the paired native limiter blocks execution. Both use the same thread limit. We keep the original middleware order. Initial inspection incorrectly suggested rejection would remove a proposal before counting. The first execution disproved that assumption: the native stack keeps the proposal and its synthetic rejection reply, then counts the proposal.

This is a narrow application configuration change, not an upstream SDK patch. [The builder and predicate](../reliability_lab/approval_budget.py) support the serial `record_action` fixture only. Invalid counters and unsupported batches raise instead of being auto-approved. Skipping approval is safe in this fixture only with the paired native limiter still enforcing the same allowance; this predicate is not a standalone permission system or concurrent reservation mechanism.

## Frozen comparison

[The plan](../results/budget-aware-approval-plan-v1.json) records the prospective prediction: **“Yes—rejection leaves the allowance available.”** Six conditions compare baseline and candidate exhaustion/rejection behavior, plus candidate protected crash/replay and edited contents. Maximum 23 fresh worker phases, seven expected tool-body entries, twenty-second worker waits, 480-second sequence budget, no automatic retries, no new installation and zero provider calls/tokens.

The worker cap is checked by the driver. Tool-entry expectations follow the fixed scripted proposals and phases and are checked against actual journals; this is not a global atomic tool-execution budget. Provider totals are declared from the scripted/no-provider design, scrubbed worker environment and socket guard, not billing instrumentation.

Preparation passed the dependency-free development suite and offline verification. The inspected native source confirms that approval runs before counting and a false `when` result reaches the native limiter. Following the rejection branch fully shows that it retains the proposal plus its reply; the original preflight interpretation of that branch was wrong. Before execution, implementation hashes are captured; every worker checks those hashes and the inspected runtime fingerprints. Original experiments, receiver and dependencies are unchanged.

## Inspect or execute

Ordinary verification does not start the experiment:

```sh
python3 -S -m reliability_lab verify-offline
python3 -S -m unittest discover -s tests -v
```

A deliberate new attempt requires the existing compatible optional runtime environment:

```sh
python -m reliability_lab approval-budget-check --prediction 'your prediction'
```

This launches the six conditions above into a unique ignored `work/approval-budget/` directory. Raw checkpoint databases and worker logs remain local. A setup/runtime failure or contradictory result is preserved; do not silently retry. The current command uses the corrected v2 plan. The original v1 plan and its execution-time implementation remain preserved separately.

The policy does not establish async/multi-tool/concurrent approval, run-level budgets, global account limits, authenticated human review or general remote exactly-once delivery. Receiver deduplication remains necessary for post-commit pending-tool replay.

## First attempt exposed a policy mistake

[The original v1 execution](../results/fresh/budget-aware-approval-v1/execution.json) stopped after twelve worker phases, with its failed criterion preserved. The exhausted-budget comparison worked: baseline asked for approval; candidate v1 returned the native budget block without asking. Both made only the first effect.

The next baseline condition contradicted the frozen expectation. Rejection made no tool entry or receiver effect, but the thread counter rose from zero to one. Its next action could be approved but was then budget-blocked. This is a real difference between native proposal counting and the execution-allowance policy we wanted, not a checker false negative.

Native rejection returns the original `tool_call` alongside an error ToolMessage. Keeping that pair preserves conversation history, and native routing recognizes the reply so the body does not run. The limiter nevertheless sees the proposal and counts it. Read-only checkpoint-history inspection confirmed the proposal/reply pair before the counter increment; it launched no graph invocation.

## Explicit corrective follow-up

[Amendment A1](../results/budget-aware-approval-amendment-a1.json) preserves that failure and authorizes one additional candidate attempt. [The v2 plan](../results/budget-aware-approval-plan-v2.json) contains four candidate conditions and fifteen worker phases. The already executed baselines are reused, not rerun. Exhaustion is checked again because the candidate counting component changes. Across both attempts the ceiling is 27 worker phases and seven expected body entries, with zero provider calls or new installations.

The correction is a narrow subclass of the native limiter. If the latest proposal already has its matching tool reply, it skips counting it; otherwise it delegates to native enforcement. It leaves proposal/reply history intact. In this serial stack, that keeps rejected work from spending execution allowance while accepted work is still counted before the body runs. Reply matching is not an authenticated rejection detector for arbitrary histories.

Your original prospective prediction remains in v1. No separate follow-up answer arrived before the v2 freeze, so v2 explicitly records not supplied. No successful follow-up result is claimed at this preparation milestone.
