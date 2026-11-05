# Agent Runtime Reliability Lab

**What happens when an agent's action succeeds—but the process crashes before it saves the tool result?**

On restart, the runtime can execute the pending tool again. This independent, AI-assisted lab makes that behavior visible and tests safeguards against duplicate effects and misleading success reports.

Built with **Python, SQLite, Deep Agents, LangChain and LangGraph**. Start with the [five-minute walkthrough](docs/demo.md) or read the [full report](REPORT.md).

## The core experiment

```text
Action commits → process crashes → pending tool replays
```

Both receivers get two attempts at the same operation:

| Receiver | Tool attempts | Committed effects | Result |
|---|---:|---:|---|
| Unprotected control | 2 | 2 | Duplicate action; the task failed |
| Protected SQLite receiver | 2 | 1 | Original receipt returned; no second effect |

The checkpoint restores pending work. The protected receiver recognizes the stable operation ID and prevents another effect. A separate application reporter checks receiver records before reporting the outcome.

**A successful graph or a valid receipt alone does not prove the action happened once.**

## What the evidence shows

| Finding | Evidence |
|---|---|
| Pending tools can replay after their actions commit | [Crash/replay observations and corrected assessment](docs/crash-resume-evidence.md) |
| Approval, edited contents and rejection survive the tested restart boundary | [Five-case published-package reproduction](docs/clean-install-reproduction.md) |
| The application can disclose duplicates and report unavailable evidence as unknown | [Graph answers versus application responses](docs/final-response-integration.md) |
| A spent request budget blocks a new request, but allows pending work to replay | [Budget and crash recovery](docs/budget-recovery-evidence.md) |
| Broader recovery guidance can introduce incorrect source selection | [Why one middleware candidate was rejected](docs/search-recovery-evidence.md) |

These are bounded findings. A passing experiment can include an intentionally unsafe control whose user task failed. Each walkthrough links the saved observations; [the claim map](docs/claim-evidence.md) connects public claims to results, code and limits.

## Verify locally—no dependencies or API keys

From the repository root, with Python 3.10 or newer:

```sh
python3 -S -m reliability_lab verify-offline
```

This validates saved evidence and runs **six fresh SQLite receiver contracts**. The JSON reports each stage separately and gives the path to a new local report under `work/attempts/`. Exit 0 means the checks passed; invalid evidence produces a nonzero exit.

It does **not** rerun historical agents, launch graph workers or call a model. Stored records include failures and excluded attempts; their count is not a count of successful evaluations.

Run the separate development suite with:

```sh
python3 -S -m unittest discover -s tests -v
```

Verified on Python 3.14.6: **130 passed**. On Python 3.12.11: **129 passed, one explicitly skipped** because the SQLite connection warning is unavailable before 3.13. These are development tests, not model evaluations. See the [verification record](results/presentation-closeout-check-20261105.json).

## Optional: run a new crash/replay experiment

Saved evidence is enough for the walkthrough. To deliberately reproduce the five-case experiment, use a virtual environment with the eight pinned seed versions in [requirements-runtime.txt](requirements-runtime.txt), including SQLite checkpoint support. Runtime execution was verified on Python 3.14.6 on the same host; other runtime platforms and Python versions remain unverified.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-runtime.txt
.venv/bin/python -m reliability_lab crash-resume-check --prediction 'Your prediction before running'
```

**Execution bound:** up to 19 fresh worker phases, five cases, zero provider calls/tokens, no automatic case retries, a 30-second wait cap per worker, a 600-second case-sequence budget and recursion limit 10 per invocation. Approved crash phases intentionally exit 86. New reports, databases and logs stay in ignored `work/crash-resume/`.

The seed requirements are not a full transitive artifact lock. The recorded clean installation used uv; the pip setup spelling above has not separately been executed. Read the [setup details, expected outcomes and known limitations](docs/reproduction.md) before starting. No new runtime experiment was run for this documentation closeout.

## Project contribution and attribution

Ibrahim Arshad developed the experiment harness, local receiver, outcome reporting, evaluators and reviewed evidence with AI assistance. **Deep Agents, LangChain and LangGraph supply the agent runtime.** This is an independent lab, not an upstream SDK contribution or production deployment.

Fresh recovery experiments use scripted model proposals and simulated reviewer decisions. Earlier live-model evaluations are retained as a separate evidence category. [InferenceBench](https://github.com/ibrahim1023/inference-bench) is a separate supporting project.

## Read next

1. [Five-minute demo](docs/demo.md) — follow the crash/replay comparison using saved evidence.
2. [Full report](REPORT.md) — understand the safeguards, failures and evaluator corrections.
3. [Architecture](docs/architecture.md) — see where the runtime, receiver and reporter fit.
4. [Claim map](docs/claim-evidence.md) and [provenance gaps](docs/provenance-gaps.md) — inspect support and uncertainty behind each claim.

## Scope and limitations

- **Local recovery mechanics:** SQLite receiver, simulated approval and abrupt process exit; no general exactly-once delivery or power-loss guarantee.
- **Bounded evaluation:** scripted runs test runtime behavior, not general model reliability. Historical answer-quality labels remain earlier manual assistant review. The [unresolved 120B result and separate 20B comparison](docs/optional-cohorts.md) remain visible.
- **Partial reproducibility:** same-host package reproduction and selected source hashes do not establish every historical revision or cross-platform behavior. Saved filesystem graph exports are not yet checked by the default offline verifier.
- **Evidence integrity:** hashes and consistency checks cannot authenticate a coherent replacement of artifacts and manifest. The offline Python socket guard is not an operating-system security sandbox.

Original milestone documents, failed assessments and interrupted attempts are preserved. Their dated status notes are historical; [the reproduction guide](docs/reproduction.md) describes current verification coverage.
