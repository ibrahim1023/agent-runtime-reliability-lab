# Sprint checkpoint and frozen next experiment

## Day 1 closeout

No separate Day 1 calendar was found in the repository. This checklist follows the three pending items supplied in the learning conversation.

- [x] Complete the 25-run historical search export and offline consistency checks, including rejected results and unavailable observations.
- [x] Inventory optional cohorts, preserving the unresolved 120B result and separate 20B comparison.
- [x] Finish the provenance review with explicit unknowns and freeze the next experiment's criteria.

These packaging/validation tasks made no new live-model calls and did not rerun historical experiments. Existing fresh scripted filesystem results remain separate. This checklist does not mark the next runtime experiment or clean-environment reproduction complete.

## Next: approval → receiver commit → process crash → fresh-process resume

Status: **v1 executed once on 2026-11-03; original failed assessment and A1 reassessment retained**. [Read the evidence](crash-resume-evidence.md). The frozen JSON keeps its original pre-execution status as a historical snapshot. The machine-readable criteria are [next-experiment-plan-v1.json](../results/next-experiment-plan-v1.json), hash-linked in the manifest. Changes after observing results require a new version/amendment, not overwriting v1.

Reuse the existing SQLite receiver, historical approval/edit patterns, idempotency crash boundary and the Deep Agents/LangChain/LangGraph execution stack. Use deterministic scripted model responses and a simulated reviewer. Do not build an agent loop, authenticate a human, select a live model or add infrastructure.

| Planned case | Tool-body entries | Committed effects | Receipt behavior |
|---|---:|---:|---|
| Protected approve, first repetition | 2 | 1 | Exact first receipt reused |
| Protected approve, fresh second repetition | 2 | 1 | Exact first receipt reused within that case |
| Unprotected approve control | 2 | 2 | New receipt on replay; task has duplicated effect |
| Protected reviewer edit | 2 | 1 | Only approved replacement recorded, then same receipt reused |
| Protected reject | 0 | 0 | No committed receipt |

The unprotected control should pass its expected-duplication check while failing the intended single-effect task. Rejection is correct policy handling with no completed record action. Completion under an edit is judged against the approved replacement, while the original proposal remains visible. Do not combine these dimensions into a misleading overall success count.

## Phase boundary and observations

For each case, initial invocation must pause before tool execution. A fresh worker invokes None without a decision: the review remains pending and effects stay zero. A third worker supplies the simulated decision. Approve/edit cases commit to the separate receiver database, fsync the receipt journal and exit 86 before the tool returns. A fourth worker invokes None to resume pending graph work. Rejection ends in phase three without a tool-body entry or crash.

The application persists the thread/operation identity once. Every replay must use the same identity and approved payload. Checkpoint and receiver databases remain separate transactions. Use synchronous graph durability. A new approval interrupt after the post-commit restart is a contract failure to record, not a prompt to approve again until the run looks successful.

The final scripted response must derive from the actual ToolMessage and agree with committed SQL receipts. The fixture must not manufacture an expected success response. Record actual tool attempts, effects, review decisions, process identities, returned receipts and outcome reporting. Keep raw checkpoints and unreviewed traces private.

## Bound, gates and exclusions

Five cases, at most nineteen fresh worker processes, thirty seconds per worker, six hundred seconds total and ten graph steps per invocation. Zero live-model calls, zero estimated provider tokens, no automatic retries or provider substitutions. The current SQLite checkpoint package metadata is recorded as a preflight observation, not proof of a clean installation.

Before implementation/execution, verify component hashes and dependency compatibility, disable tracing, strip key-bearing worker variables and block Python socket operations before runtime imports. That is not an OS sandbox. Invite a learner prediction before execution; if the learner asks to proceed without one, record it as not supplied. Do not block routine packaging on quiz answers.

Preserve every failed or interrupted attempt. A missing dependency is setup interruption; a graph-limit stop is a behavior/fixture failure, not silently excluded as infrastructure. Worker timeouts leave an unknown outcome to inspect; do not turn them into successful runs, increase budgets after the fact or retry under the same label. No claim is made about machine/power failure, arbitrary remote exactly-once delivery or authenticated review.

Implementation, one bounded execution and reviewed result publication are complete. Clean-environment reproduction remains pending. The first assessment failed on the edit-message format; amendment A1 documents a saved-evidence reassessment without rerunning workers. Any later live evaluation needs a separate bounded run/token budget; old Groq allowances are not assumed.

Frozen v1 SHA-256: `2cd7c3d68afb6331d93e27312fe51fe9edfcd5354d0410949b8c68a46e9e04ff`.
