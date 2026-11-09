# Budget-aware approval implementation plan

**Goal:** Avoid an approval prompt for an exhausted request while retaining approval for eligible work and preserving allowance on rejection.

**Spec/design:** `results/budget-aware-approval-plan-v1.json` freezes the serial one-tool policy, six conditions, 23-worker ceiling and prospective prediction. Use the installed public `when` callback to read eligibility; keep the native tool limiter in place to enforce/count it. A narrow application builder pairs both with the same limit. No SDK source or original fixtures change.

**Approach:** A read-only predicate is smaller than moving the counting middleware, which could spend allowance before review. It does not reserve a slot or grant execution by itself. Unsupported batch shapes or invalid counter values raise before execution.

## Implementation and verification

- [x] Write predicate tests for eligible/exhausted counts, no mutation, invalid counters and unsupported batches; observe missing implementation failure, then implement.
- [x] Add a narrow builder pairing native approval and native limiter; imports remain optional.
- [x] Write assessor tests against hand-checked expected observations, then implement a separate six-condition worker/driver; preserve original experiments.
- [x] Run stdlib checks and source review before the one new bounded experiment.
- [ ] Execute six conditions once in the existing verified package environment, at most 23 workers, seven body entries and zero provider calls/tokens. No automatic retries or new install.
- [ ] Inspect actual interrupts, counters, arguments, receipts and blocked ToolMessages; compare against the learner's prediction and the baseline.
- [ ] Preserve executed source bytes and reviewed synthetic observations; validate saved evidence without rerunning graphs.
- [ ] Commit and push verified milestones to the lab only.

**Review focus:** Skipping review is safe here only because the paired native limiter blocks exhausted requests; rejected calls must disappear before counting; pending tools-node replay must retain receiver deduplication; edits must use approved args. This is a serial local policy, not a concurrent reservation mechanism.

Pre-execution review: no serial-policy blocker. Added an explicit worker cap, pre-execution source fingerprints and malformed-observation preservation. Tool-entry bound is from scripted proposals, not a separate atomic cap; provider totals are design declarations supported by socket blocking and scrubbed environment.

A1: Original attempt stopped after12workers on real native rejection accounting, not an evaluator false negative. V1 frozen criteria, failed report and executed bytes retained. V2 changes the candidate counter adapter; four candidate conditions15workers, no baseline rerun. Original source-review interpretation of rejection was wrong.
