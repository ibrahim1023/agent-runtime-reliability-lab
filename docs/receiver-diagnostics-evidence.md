# The reporting path must survive its own diagnostic failures

The learner predicted **“Return outcome unknown and preserve the graph answer”** if the ordinary receiver disappears before final response selection. Inspection showed an earlier step: the application read the entire receiver file to calculate a diagnostic hash before calling reconciliation.

That ordering meant a diagnostic exception could prevent the user from receiving an outcome report at all. The previous unavailable-receiver response check called the reporter directly and missed this ordinary-path dependency.

## Reproduce before changing code

The [frozen plan](../results/receiver-diagnostics-plan-v1.json) allowed three baseline and three corrected application replays, zero new graph workers and zero provider calls. The graph generation boundary was replaced with already published output from the November 3 integration. Synthetic receiver databases were reconstructed from its published receipts. No original private receiver was modified and no tool, review or commit was repeated.

These are deterministic application orchestration replays, not fresh agent recovery or model evaluations. The reused graph record contains nineteen historical worker phases; those are source context, not new workers in this experiment. Development regression executions are separate from the six recorded experiment conditions.

| Condition | Before correction | After correction |
|---|---|---|
| Receiver available | Report saved; completed once | Same result |
| Ordinary receiver missing | `FileNotFoundError`; no application report saved | Report saved; outcome unknown |
| Diagnostic hash read fails; SQL readable | `PermissionError`; no application report saved | Report saved; completed once from SQL |

The learner's prediction did not hold for the baseline ordinary path. It holds for the corrected missing-receiver path: the response is unknown and the successful graph answer is preserved separately.

The third condition uses method-level fault injection only on the diagnostic byte reader. SQLite still reads an actual reconstructed database. This does not claim SQLite can bypass an operating-system permission denial; it demonstrates that a failed optional measurement should not automatically invalidate independent readable SQL evidence.

## What changed

Receiver fingerprinting now catches its own `OSError`, records the error type and returns a null hash. Reconciliation still runs. The application distinguishes three facts:

- The outcome supported by the receiver's SQL snapshot.
- Whether byte-identity diagnostics were available.
- Whether the original experiment's full criteria were met.

A missing receiver provides no SQL evidence, so task completion stays unknown. A failed hash read with readable matching SQL supports a single-effect report, while byte identity remains unknown. Two unavailable hashes are not proof of unchanged bytes: `receiver_bytes_unchanged` is null, never true.

Both faulted conditions retain `fixture_contracts_met: false` and command exit code 1. For the missing receiver, the original once-completion criterion cannot be established. For the hash-only fault, the frozen unchanged-bytes criterion cannot be established. We improved response delivery without rewriting those experiment failures as success.

The correction is in the lab's application wrapper, not the Deep Agents SDK. It handles diagnostic `OSError`; report-directory write failures and every other storage failure mode are outside this bounded evidence.

## Evidence and source identity

- [Original exceptions and available control](../results/fresh/receiver-diagnostics-v1/baseline.json)
- [Corrected responses and diagnostic availability](../results/fresh/receiver-diagnostics-v1/corrected.json)

The original November 3 graph experiment remains unchanged. Its executed lab source files are now preserved as manifest-linked byte-identical snapshots from commit `8354841`. The verifier checks its recorded implementation hashes against those snapshots, allowing today's fixture to evolve without pretending today's code produced the historical result. A tampering regression rejects a changed snapshot even if its manifest hash is refreshed.

The corrected source snapshot is separate. The saved evidence preserves before/after implementation hashes and the frozen criteria. Hashes and consistency checks cannot authenticate a coherently fabricated replacement of all evidence.

## Verification and reproduction

```sh
python3 -S -m unittest discover -s tests -v
python3 -S -m reliability_lab verify-offline
```

The development suite passed 102 tests on Python 3.14.6. `test_delivery_diagnostics.py` reconstructs the published synthetic receivers, replaces graph generation with saved output, and runs the real application orchestration. It covers the same delivery boundaries without model/runtime dependencies. No new graph process is started by these tests.

The default offline command checks the six saved conditions in `receiver_diagnostics_evidence`; it does not rerun their orchestration. The existing six fresh receiver contracts remain separately identified. The prior graph experiments retain their own worker counts and limitations.

Independent review found no important correctness issues in the correction, replay evidence or historical source snapshots.
