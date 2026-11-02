# Opt-in scripted runtime contract

Use an environment containing the versions in `requirements-runtime.txt`. The recorded run reused an existing environment; a clean package installation has not been verified. Deep Agents was editable, so the selected loaded-module hashes and observed checkout revision in the result matter alongside package versions. The requirements file is an environment reference, not a complete transitive dependency lock.

From the lab root, with that environment's Python:

```sh
python -m reliability_lab scripted-root-check
python -m unittest discover -s runtime_checks -v
```

Each invocation executes one fixture under baseline and conservative conditions, making two fresh graphs with scripted responses, not provider calls. Tests execute the public command in a new process without key-bearing environment variables. The command disables tracing and installs the Python socket audit guard before runtime imports. Reports and raw callback journals go to unique ignored `work/scripted-root/` directories. The committed result is an explicitly reviewed, sanitized report, not an automatic upload of raw journals.

Keep these opt-in checks separate from `python3 -S -m unittest discover -s tests -v`. The latter remains a standard-library development path and does not import Deep Agents. `verify-offline` does not yet validate the saved scripted-runtime result or extraction metadata; the runtime command checks extraction hashes itself before loading them. The other six historical middleware contracts and approval/crash/resume remain future work.
