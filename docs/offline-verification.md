# What the offline command establishes

## Stored evidence validation

The command reads the four historical JSON extracts and the manifest. It checks file hashes and then cross-checks the content: two tool entries, two process identities, unchanged operation ID and payload, matching returned receipts, and one protected versus two unprotected committed rows. Expectations are fixed by the known cohort, not accepted blindly from an evidence field.

Tests deliberately alter evidence in disposable copies. Some also update the hash, so behavior consistency checks must catch the contradiction. Missing cases, missing files, changed receiver bytes, changed IDs, changed receipts, extra effects, and invalid paths are rejected. The original exports are never mutated by tests.

Hashes detect drift against a trusted manifest. They are not signatures and cannot establish authenticity if someone replaces both the records and manifest with a coherent fabrication. The public extracts also cannot independently prove checkpoint internals or the physical crash boundary; original checkpoint dumps remain private. Phase exits and journals are historical recorded observations, not new executions.

## Fresh receiver contracts

The second stage executes the actual extracted receiver against new temporary SQLite databases. It tests same-ID payload conflict, receipt reuse after reopening, distinct IDs, eight simultaneous duplicate requests, the expected unprotected duplication, and deterministic connection cleanup. A skipped test is reported, not counted as executed coverage.

A normal unprotected control result is two effects; the verifier must recognize that as the intended demonstration. Passing that control does not imply the unprotected receiver is safe.

## No live calls

The command uses only Python's standard library and the extracted receiver. It requires no keys, does not load .env files, disables tracing, and rejects Python socket operations through an audit hook. No subprocess or provider client is part of the command's execution path. This is an accidental-use guard, not a security boundary against malicious native code.

## Reproduction record

November 2, 2026: `python3 -S -m reliability_lab verify-offline` exited 0 with four historical cases validated and six receiver contracts passing. The full development command executed 19 tests, all passing on Python 3.14.6. The command integration tests also demonstrate nonzero failure for a corrupted export and fresh attempt directories across repeated invocations.

These checks do not rerun an LLM, LangGraph, approval, or crash/resume experiment. Those later milestones need their own frozen predictions and execution evidence.
