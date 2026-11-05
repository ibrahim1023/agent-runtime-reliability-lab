# Agent Runtime Reliability Lab

**A tool can run twice even when a checkpoint remembers the conversation.** This independent, AI-assisted lab investigates what happens when an action commits, its process crashes before tool completion is saved, and the runtime resumes pending work.

The central comparison is small: both receivers see two tool attempts. The unprotected receiver commits twice; the protected SQLite receiver recognizes the same operation ID and returns its original receipt, leaving one effect. A separate application reporter checks receiver evidence rather than treating a successful graph or receipt as proof of task success.

## What this project contributes

Ibrahim Arshad developed the experiment harness, local receiver, outcome reporting, evaluators and reviewed evidence with AI assistance. **Deep Agents, LangChain and LangGraph supply the agent runtime.** Scripted models drive the fresh recovery fixtures; historical live-model results are retained separately. This is not an upstream SDK contribution or a production deployment.

## Selected findings

| Finding | Observed result | Inspect the evidence |
|---|---|---|
| Checkpoints can replay an already committed action | Two tool entries: two unprotected effects versus one protected effect | [Crash/replay comparison](docs/crash-resume-evidence.md), [saved phases and receipts](results/fresh/crash-resume-v1/execution.json), [corrected assessment](results/fresh/crash-resume-v1/reassessment-a1.json) |
| Approval and edited contents survive this restart boundary | Edited payload replayed unchanged; rejection made no effect | [Frozen expectations](results/next-experiment-plan-v1.json), [same-host package reproduction](results/fresh/clean-install-v1/execution.json) |
| Graph completion and a valid receipt do not prove one effect | Application disclosed a duplicate; unavailable verification produced unknown | [Integrated responses](docs/final-response-integration.md), [saved graph answers and application responses](results/fresh/final-response-v1/execution.json) |
| A spent request budget does not prevent pending tool replay | Both receivers replayed; a genuinely new request was blocked | [Budget/recovery explanation](docs/budget-recovery-evidence.md), [saved execution](results/fresh/budget-recovery-v1/execution.json) |
| Broader recovery guidance can make decisions worse | Rejected middleware chose one of two plausible sources and wrote output | [Historical comparison](docs/search-recovery-evidence.md), [actual rejected run](results/historical/search/candidate-ambiguous-1.json) |

These are bounded findings, including intentionally failed tasks. Passing the fixture means observing the expected behavior, including the unsafe control.

## Verify without dependencies or keys

From the repository root, with Python 3.10 or newer (checked on 3.14.6 and 3.12.11):

```sh
python3 -S -m reliability_lab verify-offline
```

Exit 0 means the stored-evidence stages passed their hash and consistency checks and the six receiver contracts passed against fresh temporary databases. The JSON separates those activities and prints a unique `work/attempts/<id>/report.json` path. It does **not** rerun historical agents, install packages or launch graph workers. Invalid evidence stops later stages and produces a nonzero exit. On Python before 3.13, the SQLite connection-warning contract is explicitly skipped and reported.

For the separate development suite:

```sh
python3 -S -m unittest discover -s tests -v
```

The suite ran 130 tests: all passed on Python 3.14.6; on 3.12.11, 129 passed and one was explicitly skipped. These include tampering checks and deterministic application tests, not 130 model evaluations. Python socket operations are blocked on the offline command's execution path; this is not an operating-system security sandbox. See [verification scope](docs/reproduction.md).

## Optional: deliberately reproduce crash/replay

Use saved evidence first. A fresh runtime attempt requires a virtual environment and the eight pinned seed versions in [requirements-runtime.txt](requirements-runtime.txt), including SQLite checkpoint support. The recorded published-package installation used Python 3.14.6; other Python/platform combinations are unverified. From the repository root, these are **setup and fresh-execution commands**, not offline validation:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-runtime.txt
.venv/bin/python -m reliability_lab crash-resume-check --prediction 'Write your prediction before running'
```

This launches up to **19 fresh worker phases across five cases**, with zero live model calls or provider tokens, no automatic case retries, a 30-second wait cap per worker, a 600-second case-sequence budget and graph recursion limit 10. Approved crash phases intentionally exit 86. Reports, databases and logs stay in ignored `work/crash-resume/`; only reviewable extracts belong in published evidence.

The eight seeds are not a full transitive artifact lock. The original clean installation used uv; this pip spelling has not separately been executed. Existing [same-host clean-package evidence](docs/clean-install-reproduction.md) reproduced the five cases once. Today's command uses the current assessor, not the original mistaken assessor. The historical report's generic editable-environment preflight wording is retained and corrected by its separate environment record. See [exact prerequisites, expected outcomes and verification limits](docs/reproduction.md) before running. No new runtime installation or graph experiment was performed for this presentation closeout.

## Reading order

1. [Five-minute demo](docs/demo.md): inspect saved evidence and run the offline check.
2. [REPORT.md](REPORT.md): the central story, failures, safeguards and corrections.
3. [Claim-to-evidence map](docs/claim-evidence.md): what each public claim supports and where it stops.
4. [Architecture](docs/architecture.md), [provenance](docs/provenance.md) and [remaining gaps](docs/provenance-gaps.md): deeper reference and historical milestone notes.

## Limits

The receiver is local SQLite, approval is simulated, and the crash is abrupt process exit rather than power loss. Fresh scripted runs test runtime mechanics, not general model reliability. Historical answer-quality labels remain earlier manual assistant review. The unresolved [120B result and separate 20B cohort](docs/optional-cohorts.md) remain separate. Selected source hashes and same-host reproduction do not establish every historical revision, cross-platform behavior or authenticity against coherent artifact fabrication. Saved filesystem graph exports are not yet covered by the default offline verifier.

No claim is made of general exactly-once delivery, authenticated human approval, production deployment or inference optimization. [InferenceBench](https://github.com/ibrahim1023/inference-bench) is separate supporting work. Original milestone documents and failed assessments are preserved; their dated status statements are historical, not the current entry point.
