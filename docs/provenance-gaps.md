# Provenance review: what is established and what remains unknown

## Evidence levels

| Area | Established evidence | Remaining gap |
|---|---|---|
| Historical search roster | 25 original observed/journal hashes, seven fixtures, detailed allowlisted extracts | Retrospective roster; initial six-case baseline gained an existing-file control later |
| Historical action/approval/missing-source | Earlier reviewed records, journals and SQL receipts with source hashes | No new replay of those agents; checkpoint internals remain private |
| Historical runtime source | Current source identities and packaging checkout observation | Exact code revision for each October execution not established; older recorder schemas differ |
| Historical models | Recorded aliases; allowlisted diagnostic model metadata when present | Immutable provider model snapshot/revision and backend behavior unknown |
| Historical settings | Saved trace model alias, token cap and reported temperature where present | Exact wire request and all timeout/retry/pacing settings not recovered; current runner is not per-run execution proof |
| Historical dependencies | Trace-reported Python, LangChain/core and diagnostic SDK versions when present | Complete dependency lock and Deep Agents/LangGraph execution source identity not recovered |
| Historical scores | Original scorer source hash, fixed synthetic fixtures, retained scores, artifact checks | Answer-quality assessments remain earlier assistant review, not a new semantic judge |
| Fresh scripted runtime | Versions, selected loaded-module hashes, observed tracked-clean editable checkout, extraction identities, actual callbacks | Selected pins/hashes are not a complete lock; clean installation equivalence unverified |
| Extracted receiver | Original/destination hashes and explicit connection-cleanup change, fresh contracts | Local SQLite property only; not exactly-once effects for arbitrary remote services |
| Approval | Historical simulated approve/reject/edit behavior | Fresh scripted approval plus post-commit crash/resume now executed together; no authenticated human reviewer test or power-loss test |
| Optional cohorts | 16 original 120B attempts, one blocked follow-up and eight 20B runs inventoried separately | Full optional per-run behavioral export not performed; original-present 120B failure unresolved |

## Recovered diagnostic metadata

`results/runtime-provenance-20261102.json` contains allowlisted samples from fifty stored trace files across the search and optional cohorts, plus hashes of those source files. It does not publish the traces, tracing IDs, tool prompts, account metadata or credentials. Multiple differing samples would be retained rather than silently collapsed to one setting.

The current search/optional runner requests temperature 0. Saved diagnostic metadata reports `ls_temperature: 1e-08` and `ls_max_tokens: 512`. These are different evidence levels: do not rewrite reported metadata as exact zero or infer the exact wire payload. Small sampling settings do not prove deterministic provider behavior or explain the unresolved failure's cause.

Missing fields remain missing. Earlier baseline journals can lack result execution IDs and final conversation snapshots; the full export labels sequential pairing and unavailable observations. The graph-limit run's unavailable final state is not an empty mapping. Hashes/consistency checks detect drift against trusted records, not a coherent fabrication of records and manifest.

## What “finished provenance” means here

The review is complete enough to state the lab's bounded claims and expose its gaps. It does not turn unknown historical revisions into known values or certify a fully reproducible clean release. New experiments must capture their own package/source identities, settings, criteria and exclusions before interpretation. The next experiment is frozen separately; its criteria are not results.

[InferenceBench](https://github.com/ibrahim1023/inference-bench) remains supporting work only. No inference server, UI, new tracing platform or agent loop is part of this sprint.
