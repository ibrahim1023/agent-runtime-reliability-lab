# Full historical search export

All 25 recorded search runs now have detailed allowlisted public extracts in `results/historical/search/`. The original seven synthetic fixtures and recorded user queries are in `fixtures.json`. The manifest binds each export to its hash and the original observed-record/journal hashes. This completes artifact packaging, not a new graph or model experiment.

The offline command reports `historical_search_evidence` separately from the earlier sixteen records and the initial three-record review. Its 25-record inventory includes the rejected broad candidate and all four empty-workspace repetitions. The first-seven-case result remains 4/7 baseline, 4/7 rejected candidate, 6/7 conservative. No failed run is removed or relabeled.

## What a reader can inspect

Each record includes its fixed task and model alias, natural completion, journal/model/tool counts, normalized model proposals, actual tool arguments, tool results, available model-facing ToolMessages, final answer, available final filesystem, and retained historical scores. Exact answer hashes bind the earlier assistant review to the unchanged answer; this is not a new semantic judge.

The validator cross-checks sequential journal references and counts, proposal/execution differences allowed by the recorded root-alias middleware, successful reads/writes and available final state. It applies the original artifact criteria to reject contradictory task/verdict labels. No StateBackend or agent is executed by these checks. Negative tests recompute export hashes in disposable copies, demonstrating that content checks catch contradictions even after byte identity is updated.

## Missing observations stay missing

The baseline nested run reached the twenty-step graph limit. It remains a valid behavioral failure. Its final state is **unavailable**, not an empty workspace: the original exception path returned an empty mapping without a snapshot. The export uses null and an explicit availability flag rather than inventing a final state.

Some earlier baseline records lack final conversation snapshots and recovery-event fields. They remain null. Some result journal entries lack execution IDs. They are paired only with their single pending sequential start, and that binding method is labeled. Normalized local references replace original callback/tracing IDs; they do not authenticate execution. The current runner hash is a provenance pointer, not proof that every earlier run used that exact instrumentation.

The original roster is retrospective. The existing-file control was added after the initial baseline six-case sweep. Historical runtime revision and immutable model revision remain unknown. Coherent fabrication of records plus manifest cannot be excluded by hashes and consistency checks.

## Verification

```sh
python3 -S -m reliability_lab verify-offline
python3 -S -m unittest discover -s tests -v
```

The original sixteen records remain separate; the new historical stage checks twenty-five search records. Neither count denotes new or successful model trials. Receiver contracts still execute six fresh local checks. Source files, rejected results, earlier exported evidence, and fresh scripted-runtime results remain unchanged. The optional 120B and 20B cohorts are inventoried separately and are not included in these twenty-five records.
