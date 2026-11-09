# Avoid approval prompts for work the budget will block

Previously, a new request with a spent conversation allowance could pause for approval, then be denied by the native limiter after approval. The lab's candidate uses the installed approval middleware's public `when` callback to check eligibility before asking.

The callback is read-only. With allowance available, review remains required. With allowance spent, it skips the prompt and the paired native limiter blocks execution. Both use the same thread limit. We keep the original middleware order: rejected calls are removed by approval handling before the native limiter counts accepted calls.

This is a narrow application configuration change, not an upstream SDK patch. [The builder and predicate](../reliability_lab/approval_budget.py) support the serial `record_action` fixture only. Invalid counters and unsupported batches raise instead of being auto-approved. Skipping approval is safe in this fixture only with the paired native limiter still enforcing the same allowance; this predicate is not a standalone permission system or concurrent reservation mechanism.

## Frozen comparison

[The plan](../results/budget-aware-approval-plan-v1.json) records the prospective prediction: **“Yes—rejection leaves the allowance available.”** Six conditions compare baseline and candidate exhaustion/rejection behavior, plus candidate protected crash/replay and edited contents. Maximum 23 fresh worker phases, seven expected tool-body entries, twenty-second worker waits, 480-second sequence budget, no automatic retries, no new installation and zero provider calls/tokens.

The worker cap is checked by the driver. Tool-entry expectations follow the fixed scripted proposals and phases and are checked against actual journals; this is not a global atomic tool-execution budget. Provider totals are declared from the scripted/no-provider design, scrubbed worker environment and socket guard, not billing instrumentation.

Preparation passed the dependency-free development suite and offline verification. The inspected native source confirms that approval runs before counting, rejection removes calls before counting, and a false `when` result reaches the native limiter. Before execution, implementation hashes are captured; every worker checks those hashes and the inspected runtime fingerprints. Original experiments, receiver and dependencies are unchanged.

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

This launches the six conditions above into a unique ignored `work/approval-budget/` directory. Raw checkpoint databases and worker logs remain local. A setup/runtime failure or contradictory result is preserved; do not silently retry. Installed-source identities and reviewed observations will be published separately after the first execution.

The policy does not establish async/multi-tool/concurrent approval, run-level budgets, global account limits, authenticated human review or general remote exactly-once delivery. Receiver deduplication remains necessary for post-commit pending-tool replay.
