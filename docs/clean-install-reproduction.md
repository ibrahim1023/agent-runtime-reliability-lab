# Does the experiment depend on the editable checkout?

The learner predicted **“The published packages reproduce the same behavior.”** On November 3, 2026, a fresh package installation reproduced the five crash/resume case outcomes on the same machine and Python 3.14.6. This is a new deterministic execution, not historical artifact validation or a live-model evaluation.

Before this milestone, the evidence showed the fixture working in an existing editable Deep Agents environment. That left a practical question: could its behavior depend on local SDK changes or undeclared installed packages?

## What we did

The [pre-execution plan](../results/clean-install-plan-v1.json) allowed one installation attempt from public PyPI, then one runtime attempt if setup succeeded. The setup used a fresh virtual environment without system site packages, an allowlisted environment, no editable SDK and no provider keys. It installed the six recorded runtime versions plus the two recorded checkpoint packages. The runtime requirements file now includes those checkpoint packages explicitly.

An unsupported installer flag was rejected before package resolution. We retained that command-validation failure locally, corrected the option using an environment setting, and performed one actual resolution/install attempt with retries disabled. The installation resolved 59 packages successfully. No existing environment was modified.

Preflight confirmed Deep Agents loaded from the new environment and was not editable. The selected runtime module hashes matched the earlier execution's selected hashes. This does not establish every dependency byte was identical.

## What repeated

| Case | Tool-body entries | Receiver effects | Result compared with earlier evidence |
|---|---:|---:|---|
| Protected approve 1 | 2 | 1 | Same contract outcome |
| Protected approve 2 | 2 | 1 | Same contract outcome |
| Unprotected control | 2 | 2 | Same duplication; task incomplete |
| Protected reviewer edit | 2 | 1 | Same approved replacement and receipt reuse |
| Protected reject | 0 | 0 | Same correct rejection handling |

Nineteen fresh workers ran. No new review was required after the post-commit restart. Every saved verdict was recomputed with the corrected assessor and compared with the earlier observations. Random operation IDs, receipt IDs and process IDs were expected to differ.

Your prediction held within this tested scope. The graph still replayed unfinished work, and only the protected receiver prevented the second effect. We improved reproducibility and the setup recipe; we did not change SDK runtime behavior.

This invocation took 8.462 seconds versus 15.028 seconds for the earlier one. These are local wall times with process startup, warm-cache and environment differences, not a controlled speed comparison.

## Evidence and setup

- [Fresh execution](../results/fresh/clean-install-v1/execution.json)
- [Environment and installed packages](../results/fresh/clean-install-v1/environment.json)
- [Reviewed comparison and limitations](../results/fresh/clean-install-v1/comparison.json)
- [Installed version inventory](../requirements-runtime-resolved-20261103.txt)

A minimal setup recipe, from the lab root:

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-runtime.txt
.venv/bin/python -m reliability_lab crash-resume-check --prediction 'your prediction'
```

This recipe uses the same eight seed versions. The recorded installation used uv; the pip spelling above has not separately been executed. Future resolution of unpinned transitive packages can differ. The 59-package inventory records what was installed, but installing that inventory as a separate input has not been tested. It is not a hash lock or cross-platform lock.

The fresh execution's `preflight` string contains inherited fixture wording referring to an existing editable environment. That wording is stale in this invocation; the separate environment observations establish a non-editable installation. We retained the raw result and explicitly corrected its interpretation in the comparison, rather than rewriting execution evidence.

## What remains unproved

This was a new environment on the same host and Python version, not a second machine or operating system. The seven filesystem middleware fixtures were not rerun here. Historical execution revisions remain unknown. Provider/model decision quality was not tested: the model and reviewer were scripted, with zero live calls and zero provider tokens.

The manifest hash-links this new result. The default offline command still validates the earlier crash export; it does not yet validate this clean-install result automatically. The comparison was checked separately during publication without launching more workers. A full transitive artifact lock and independent-host reproduction remain future work.
