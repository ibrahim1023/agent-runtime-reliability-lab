# Can the same crash behavior reproduce on a clean Linux runner?

The earlier clean-package reproduction used a new virtual environment on the same host. This experiment moves the existing five-case fixture to one fresh GitHub-hosted Ubuntu runner. It tests portability of the recorded mechanism, not an independent person's interpretation or general production reliability.

## Frozen target

[The plan](../results/portable-reproduction-plan-v1.json) records the learner's prospective prediction: **“Yes—the same recovery behavior will reproduce.”** One manual dispatch is allowed, with one installation and one runtime attempt. The target is Ubuntu 24.04 with Python 3.14.6 and the existing eight seed versions. The official Python-build manifest was checked for a Linux x64 Ubuntu 24.04 build before dispatch.

Expected entries/effects remain 2/1 for protected approval and edit, 2/2 for the unprotected control and 0/0 for rejection. The control must still fail its record-once task. Approved cases intentionally exit 86 after receiver commit, then resume in a fresh process. Reviewer inputs and model proposals are scripted.

## What executes

[The manual-only workflow](../.github/workflows/portable-reproduction.yml) installs into a fresh non-editable virtual environment, records origin/version facts, then runs the unchanged `crash-resume-check` once. The experiment retains its nineteen-worker maximum, thirty-second process-wait caps, six-hundred-second case-sequence budget and recursion limit ten. Installation has a five-minute cap with pip retries disabled; the whole job has a twenty-minute cap. There are zero provider calls or tokens.

[The public exporter](../reliability_lab/portable_summary.py) reuses the existing saved-run validator and assessor. It records phase exits, cumulative attempts/effects, exact receipt reuse, graph completion and task outcome separately. Failed process exits cannot be overridden by an apparently successful report. Only allowlisted summary JSON is uploaded; raw execution logs, receipts, tool journals and checkpoint databases are excluded.

No new agent loop, runtime behavior, receiver behavior or provider integration is introduced. The setup uses GitHub's existing repository workflow facility; there is no scheduled run or push-triggered experiment.

## Status before dispatch

The implementation passed 134 development tests and the dependency-free offline check on Python 3.14.6. Four new tests cover duplicate/task interpretation, nonzero exit, incomplete or contradictory observations and raw-data exclusion. Workflow configuration was parsed without launching a graph. Independent read-only review found no dispatch blocker. Tests target the export's observation logic, not every command-line/environment failure branch.

This document initially records preparation, not a completed reproduction. Actual run identity and reviewed results will be added after the single dispatch. A setup interruption will remain an infrastructure result; it will not be called a runtime failure or silently retried.

## Limits that remain

A hosted runner is another execution environment, not independent human verification. Seed versions can resolve different transitive packages; neither the runner image nor installed version inventory is a full artifact lock. Selected loaded module hashes and installed versions are recorded for comparison rather than assumed equal. The public export contains derived receipt-equality facts, not raw receipts for independent reassessment. Local SQLite, simulated review, abrupt process exit and Python audit-hook limitations remain unchanged.

The earlier [same-host comparison](clean-install-reproduction.md), [central crash explanation](crash-resume-evidence.md) and original failed assessment remain intact. No live-model score or historical result is replaced by this experiment.
