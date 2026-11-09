# Can the same crash behavior reproduce on a clean Linux runner?

The earlier clean-package reproduction used a new virtual environment on the same host. This experiment moves the existing five-case fixture to one fresh GitHub-hosted Ubuntu runner. It tests portability of the recorded mechanism, not an independent person's interpretation or general production reliability.

## Frozen target

[The plan](../results/portable-reproduction-plan-v1.json) records the learner's prospective prediction: **“Yes—the same recovery behavior will reproduce.”** One manual dispatch is allowed, with one installation and one runtime attempt. The target is Ubuntu 24.04 with Python 3.14.6 and the existing eight seed versions. The official Python-build manifest was checked for a Linux x64 Ubuntu 24.04 build before dispatch.

Expected entries/effects remain 2/1 for protected approval and edit, 2/2 for the unprotected control and 0/0 for rejection. The control must still fail its record-once task. Approved cases intentionally exit 86 after receiver commit, then resume in a fresh process. Reviewer inputs and model proposals are scripted.

## What executes

[The manual-only workflow](../.github/workflows/portable-reproduction.yml) installs into a fresh non-editable virtual environment, records origin/version facts, then runs the unchanged `crash-resume-check` once. The experiment retains its nineteen-worker maximum, thirty-second process-wait caps, six-hundred-second case-sequence budget and recursion limit ten. Installation has a five-minute cap with pip retries disabled; the whole job has a twenty-minute cap. There are zero provider calls or tokens.

[The public exporter](../reliability_lab/portable_summary.py) reuses the existing saved-run validator and assessor. It records phase exits, cumulative attempts/effects, exact receipt reuse, graph completion and task outcome separately. Failed process exits cannot be overridden by an apparently successful report. Only allowlisted summary JSON is uploaded; raw execution logs, receipts, tool journals and checkpoint databases are excluded.

No new agent loop, runtime behavior, receiver behavior or provider integration is introduced. The setup uses GitHub's existing repository workflow facility; there is no scheduled run or push-triggered experiment.

## Preparation before dispatch

The implementation passed 134 development tests and the dependency-free offline check on Python 3.14.6. Four new tests cover duplicate/task interpretation, nonzero exit, incomplete or contradictory observations and raw-data exclusion. Workflow configuration was parsed without launching a graph. Independent read-only review found no dispatch blocker. Tests target the export's observation logic, not every command-line/environment failure branch.

The preparation commit was `614d115ec2ab55956135c79735787fb6235c13e3`. The workflow was then dispatched once. There was no setup interruption and no retry.

## Actual Linux result — November 9, 2026

[Run 42596424861](https://github.com/ibrahim1023/agent-runtime-reliability-lab/actions/runs/42596424861) completed successfully on that exact commit. The [public observation summary](../results/fresh/portable-linux-v1/execution-summary.json), [allowlisted hosted metadata](../results/fresh/portable-linux-v1/hosted-run.json), [comparison](../results/fresh/portable-linux-v1/comparison.json) and executed source snapshots are preserved in the repository, so the evidence does not depend on the temporary Actions artifact remaining available.

| Case | Tool entries | Effects | Task outcome |
|---|---:|---:|---|
| Protected approve, first | 2 | 1 | Completed once |
| Protected approve, fresh repetition | 2 | 1 | Completed once |
| Unprotected approve control | 2 | 2 | Failed: duplicate |
| Protected edit | 2 | 1 | Completed with approved contents |
| Protected reject | 0 | 0 | Correct rejection; no write completed |

All nineteen worker phases had the expected exits. Approval stayed pending through the undecided restart; approved cases exited 86 after commit and replayed without another approval. Protected replay returned the exact first receipt. The unprotected graph completed but its receipt did not account for all effects. The learner's prediction held within this five-case scope. There were zero provider calls or tokens.

The environment was a non-editable Linux x86_64 virtual environment using Python 3.14.6, with no system site packages. All eight seed versions and five selected loaded-module hashes matched the earlier same-host package execution. **Twelve transitive versions differed**, including Pydantic and LangGraph SDK; pip was additionally inventoried. Matching outcomes is therefore not evidence of identical full environments. The comparison lists every inventory difference.

The hosted job took 51 seconds; the runtime step occupied 17 seconds according to GitHub's step timestamps. These include orchestration and are not directly comparable with earlier fixture timers or evidence of a speed improvement. One dispatch, one installation and one runtime attempt ran.

The downloaded artifact contained only `public-summary.json`; its ZIP SHA-256 matched GitHub's reported artifact digest. Only the reviewed JSON is committed, not raw tool logs or checkpoints. Artifact checks establish byte identity against the recorded service metadata, not independent authenticity against coherent replacement.

## Verify saved Linux evidence

```sh
python3 -S -m reliability_lab verify-offline
python3 -S -m unittest discover -s tests -v
```

`portable_reproduction_evidence` checks the saved run identity, phase exits, attempt/effect counts, separate task outcomes, seed versions, dependency comparison and source snapshot hashes. This stage starts no workers and performs no installation. It validates derived summary observations; raw receipts and checkpoint state are not available for independent reassessment. Fresh receiver contracts still execute separately.

To deliberately repeat the remote experiment, use GitHub's manual workflow entry point and supply a prediction. That starts a new installation and up to nineteen worker phases. It is not an ordinary offline check, and this published result does not authorize automatic repeats.

## Limits that remain

A hosted runner is another execution environment, not independent human verification. Seed versions can resolve different transitive packages; neither the runner image nor installed version inventory is a full artifact lock. Selected loaded module hashes and installed versions are recorded for comparison rather than assumed equal. The public export contains derived receipt-equality facts, not raw receipts for independent reassessment. Local SQLite, simulated review, abrupt process exit and Python audit-hook limitations remain unchanged.

The earlier [same-host comparison](clean-install-reproduction.md), [central crash explanation](crash-resume-evidence.md) and original failed assessment remain intact. No live-model score or historical result is replaced by this experiment.
