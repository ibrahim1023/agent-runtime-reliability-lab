# Optional cohorts are comparisons, not a repair to the main result

| Historical cohort | Recorded attempts | Usable completed observations | Provider interruptions |
|---|---:|---:|---:|
| Explicit-alternative 120B, original pilot/repeats | 16 | 13 | 3 |
| Original-present 120B follow-up | 1 of 4 planned | 0 | 1; three trials unstarted |
| Separate GPT-OSS 20B comparison | 8 | 8 | 0 |

These are retrospective inventories, not new executions. Files in `results/optional/` preserve per-attempt labels, variants, retained verdicts or null exclusions, counts, source hashes and cohort identities. They are **not full per-run behavioral exports**. The offline command checks inventory completeness and classification separately from the full search evidence. It does not rejudge optional model outputs.

## The 120B failure stays unresolved

Open `results/optional/unresolved-original-present-120b.json`. The original `/notes/data.txt` existed alongside `/notes/dataset.txt`. The agent listed the files and asked which to use; it never read or wrote. The source-selection rule did not activate. Both transformation completion and the retained correct-handling verdict are false.

The original pilot remained 5/6 for each runtime variant. Equal semantic messages and observations through the divergent decision make model variation plausible, but causality was not established. The later 120B follow-up was quota-blocked before a completed response; it supplies no behavioral reproduction. The provider message/account identifiers are excluded from public artifacts.

The separate 20B comparison had 3/4 correct handling for the previous runtime and 4/4 for the scoped runtime, over three distinct cases with an original-present repeat. Its original-present successes are not 120B repetitions and do not close that unresolved result. Its one successful alternative pair is not a general reliability guarantee.

## Scope and gaps

Immutable provider model revisions and historical runtime revisions remain unknown. Recorded aliases, runner hashes and current checkouts cannot fill those gaps. Source hashes point to originals; they are not signatures of execution. The inventory does not export full optional tool journals or private traces. No old quota is assumed to remain available. A future live evaluation needs an explicit run/token budget and must not silently change model or provider in a paired comparison.

The rejected broad search middleware remains rejected. Optional scoped-alternative guidance is a separate prototype and is not made the default by this inventory. InferenceBench remains [a separate supporting project](https://github.com/ibrahim1023/inference-bench); this lab does not rebuild it.
