# Opt-in scripted runtime contract

Use an environment containing the versions in `requirements-runtime.txt`. Earlier runs reused an existing environment. A [fresh non-editable package installation](../docs/clean-install-reproduction.md) now reproduced the five crash/resume cases on the same host; filesystem checks were not rerun in that environment. Deep Agents was editable, so the selected loaded-module hashes and observed checkout revision in the result matter alongside package versions. The requirements file now includes the two required checkpoint packages. It is a verified seed-version reference, not a complete transitive dependency lock.

From the lab root, with that environment's Python:

```sh
python -m reliability_lab scripted-root-check
python -m reliability_lab scripted-filesystem-check
python -m unittest discover -s runtime_checks -v
```

The root command executes one fixture under baseline and conservative conditions (two graphs). The filesystem command executes the six remaining original fixtures. The full opt-in unittest suite contains two test methods and executes eight scripted graph conditions, not provider calls. Tests execute the public command in a new process without key-bearing environment variables. The command disables tracing and installs the Python socket audit guard before runtime imports. Reports and raw callback journals go to unique ignored `work/scripted-root/` or `work/scripted-filesystem/` directories. The committed result is an explicitly reviewed, sanitized report, not an automatic upload of raw journals.

Keep these opt-in checks separate from `python3 -S -m unittest discover -s tests -v`. The latter remains a standard-library development path and does not import Deep Agents. `verify-offline` does not yet validate the saved scripted-runtime result or extraction metadata; the runtime command checks extraction hashes itself before loading them. All seven original middleware contracts now have fresh scripted execution evidence across the two commands. Approval/crash/resume now has a separate manual `python -m reliability_lab crash-resume-check` command: nineteen fresh worker phases, zero provider calls. It is intentionally not part of these two runtime tests. Its saved observations are checked by `verify-offline`; see [the evidence and assessment amendment](../docs/crash-resume-evidence.md).


The separate `reported-crash-check` command integrates receiver reconciliation into the application's final response. It deliberately launches a new nineteen-worker attempt when invoked; it is not included in the two runtime tests. The default `verify-offline` checks its saved evidence, along with clean-install and reporting exports, without starting workers. See [integration evidence and limits](../docs/final-response-integration.md).


`native-retry-check` deliberately executes six native retry/timeout graph cases in a compatible runtime environment. It is not part of the two existing runtime test methods or the default offline command. Recorded coverage is a preserved five-case partial attempt plus a timeout-only continuation, with explicit setup amendments; the corrected whole command was not rerun as one suite. See [native evidence and limits](../docs/retry-timeout-evidence.md).


`run-budget-check` deliberately starts four new graphs comparing native retry, tool-call and model-call limits. It is separate from the ordinary runtime tests. The default offline command validates its saved evidence without rerunning those graphs. See [budget semantics and scope](../docs/run-budget-evidence.md).
