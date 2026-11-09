# Reproduction: validate saved evidence or start a new attempt

These are different activities. The default path validates reviewed records and executes small fresh SQLite contracts. The optional path installs runtime dependencies and launches a new scripted graph/process experiment.

## Dependency-free checks

From the repository root, use Python 3.10 or newer:

```sh
python3 -S -m reliability_lab verify-offline
python3 -S -m unittest discover -s tests -v
```

No API keys, dotenv loading, model provider or tracing account are needed. `-S` disables site-package loading. The presentation check used Python 3.14.6 in the working checkout and Python 3.12.11 in an isolated source copy. Other versions remain untested. The connection-warning receiver test explicitly skips on Python before 3.13.

The offline command reports these stored-evidence stages separately: `historical_evidence`, `search_recovery_review`, `historical_search_evidence`, `optional_cohort_inventory`, `crash_resume_evidence`, `clean_install_evidence`, `outcome_reporting_evidence`, `final_response_evidence`, `receiver_diagnostics_evidence`, `native_retry_evidence`, `run_budget_evidence`, `budget_lifetime_evidence`, `budget_recovery_evidence`, and `portable_reproduction_evidence`. These inspect saved exports, not original private databases or fresh graphs. The final `receiver_contracts` stage runs six fresh temporary-database tests. Errors stop later stages; success is exit 0, with no failed stages and no receiver failures/errors.

The first historical stage contains sixteen records, including invalid attempts. Search has twenty-five detailed records. Optional cohorts are inventories, not full per-run behavioral validation. Do not sum overlapping review/export stages into a model-trial count. The saved filesystem/root graph exports remain outside the default verifier's coverage.

Each invocation creates a new ignored `work/attempts/<id>/report.json`. The development suite includes temporary artifact tampering, failure-path and application tests. Neither command launches the optional graph workers. Python socket operations are rejected on the offline command's path; this is not an OS sandbox.

## Optional runtime setup

The verified seed requirements are:

| Package | Version |
|---|---|
| deepagents | 0.7.32 |
| langchain | 1.4.7 |
| langchain-core | 1.7.0 |
| langgraph | 1.2.17 |
| langgraph-prebuilt | 1.1.0 |
| langsmith | 0.14.12 |
| langgraph-checkpoint | 4.3.0 |
| langgraph-checkpoint-sqlite | 3.1.2 |

[requirements-runtime.txt](../requirements-runtime.txt) supplies these seeds. The recorded successful installation used uv in a new non-editable virtual environment on Python 3.14.6. [The installed inventory](../requirements-runtime-resolved-20261103.txt) records 59 versions; it is not a complete artifact/hash lock and installation from that inventory was not tested separately.

The same seed requirements were subsequently installed with pip on the [November 9 hosted Linux runner](portable-reproduction.md), using this setup from the repository root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install --retries 0 --timeout 30 -r requirements-runtime.txt
```

Installation needs access to a package index. Future transitive resolution can differ. Do not silently substitute newer seed versions if resolution fails; preserve the setup failure. Use the environment's executable directly, without resolving its symlink to the base interpreter. No keys are required for the scripted fixtures.

## Optional crash/replay execution — creates new work

```sh
.venv/bin/python -m reliability_lab crash-resume-check --prediction 'your prediction'
```

This invokes the current lab implementation against the frozen five-case plan. Maximum nineteen worker phases, no automatic case retries, 30-second process-wait cap per worker, 600-second case-sequence budget, recursion limit ten per invocation, zero live provider calls/tokens. The deadline is a fixture control, not a hard operating-system wall-clock guarantee. Each phase gets a fresh process; identities are stable within a case.

Expected approved/edit phase exits are 0, 0, 86, 0; rejection has three successful phases and no tool entry. Expected entries/effects are 2/1 for each protected approval and edit, 2/2 for the unprotected control, and 0/0 for rejection. The current assessor should accept those fixture contracts. The unprotected task must still be classified as failed, and rejection as no completed write. Exit 0 is fixture success, not universal task success.

Reports, raw logs and checkpoint/receiver databases remain local under ignored `work/crash-resume/<id>/`. Missing dependencies or incomplete sequences produce interrupted/failed output and a nonzero exit. Preserve failures rather than silently retrying. Inspect detailed logs locally before publishing sanitized fields. Generic inherited `preflight` text refers to an editable environment even in a non-editable installation; actual package locations/editability must be established separately, as in the saved clean-install environment record.

For integrated response selection, `reported-crash-check` deliberately launches another five-case/nineteen-worker attempt. It is unnecessary for the saved-evidence demo. Other opt-in commands and their individual bounds are listed in [runtime checks](../runtime_checks/README.md). The two ordinary runtime test methods exercise filesystem conditions, not all crash/retry/budget commands.

## What was actually checked for this closeout

[The November 5 check record](../results/presentation-closeout-check-20261105.json) records fresh dependency-free checks in the working checkout and an isolated source copy, plus documentation-link and publication-scope review. No new optional runtime installation, graph execution or live-model evaluation was needed: existing [same-host clean-package evidence](clean-install-reproduction.md) covers the central five-case reproduction.

The isolated copy passed 129 development tests with one explicit SQLite warning-test skip on Python 3.12.11; all 130 passed on Python 3.14.6. This checks the dependency-free path on two interpreters, not graph execution on both. At that November 5 closeout, pip setup and independent-host runtime execution remained unexecuted. The [November 9 Linux attempt](portable-reproduction.md) subsequently exercised both once. Runtime execution on other Python versions and the full corrected retry suite as one uninterrupted attempt remain unexecuted. Historical source/model identity gaps are unchanged. Dated milestone documents retain their original status notes; this document and the README describe current coverage.

## Hosted Linux follow-up, November 9

One manual job reproduced the five crash cases with nineteen worker phases and zero provider calls on Ubuntu 24.04/Python 3.14.6. Eight seeds and five selected module hashes matched the earlier package run; twelve transitive versions changed. The `portable_reproduction_evidence` offline stage validates the saved summary and comparison, without rerunning that job. See [actual observations and limits](portable-reproduction.md).
