# Five-minute walkthrough: did the action happen once?

Use saved evidence by default. No provider account, tracing dashboard or optional runtime is required. Open the repository root in an editor before starting.

## 0:00–0:45 — State the problem

Open [README.md](../README.md) and say:

> The receiver can commit an action before the runtime saves that its tool finished. If the process crashes in that gap, restart can run the tool again. We count tool entries and committed effects separately.

Deep Agents/LangChain/LangGraph supply the runtime. This lab supplies the harness, receiver, reporting and evaluators.

## 0:45–2:00 — Compare the saved cases

Open [the frozen plan](../results/next-experiment-plan-v1.json), then [the original execution](../results/fresh/crash-resume-v1/execution.json). In its `cases` array compare `protected-approve-1` and `unprotected-approve-control`.

Follow `phases`: `initial` → `restore` → `decision` → `resume`. The first two phases have no effect. The decision phase commits and exits 86 intentionally; resume enters the body again. Compare `tool_entries`, `receiver_results`, `entries`, and the phase cumulative effect counts.

- Both cases have two body entries with a stable operation ID.
- Protected storage has one row and reuses its exact receipt.
- The control has two rows and two receipts: its once-only task failed.

Open [the corrected assessment](../results/fresh/crash-resume-v1/reassessment-a1.json). Explain why the original report says failed: the edited ToolMessage included an explanation before its JSON receipt. The checker was corrected against saved data, without rerunning workers. Do not present the original execution as an uninterrupted passing assessment.

## 2:00–3:00 — Show why the answer needs reconciliation

Open [integrated execution](../results/fresh/final-response-v1/execution.json). In `deliveries`, compare the control's `response.model_answer` with `response.user_response`, and find the unavailable-evidence response. [Readable response examples](final-response-integration.md) are available beside the JSON.

Say:

> A receipt proves an observed commit, not the absence of another commit. The graph finished even in the duplicate control. The application checks receiver rows, discloses the duplicate, and reports unknown if receiver verification is unavailable. It preserves the graph answer separately.

These are deterministic application responses; the experiment does not show that a model learned to detect duplicates.

## 3:00–4:00 — Validate the package

Run from the repository root:

```sh
python3 -S -m reliability_lab verify-offline
```

The JSON's stored-evidence sections should report `status: passed`. `receiver_contracts` should report six tests and no failures/errors (one explicit skip on Python before 3.13). `exit_code: 0` means those checks passed. The command prints its new local report path.

Say:

> This checks saved observations and runs fresh receiver contracts. It does not recreate the saved graph crashes, call a model or count all stored records as successful tasks. An expected duplicate control can pass its fixture while the user's task fails.

## 4:00–5:00 — Explain the safeguards and limits

Open [budget recovery](budget-recovery-evidence.md): the pending tool replayed with a spent conversation allowance, but a new request was blocked. Checkpoint, budget and receiver have different jobs.

Close with the limits in [REPORT.md](../REPORT.md): local SQLite, simulated reviewer, abrupt process exit, scripted proposals, same-host package reproduction and incomplete historical source identity. The rejected middleware and unresolved 120B result remain visible.

## Optional after the demo — launches new workers

Only after reading [runtime setup and bounds](reproduction.md), deliberately run:

```sh
.venv/bin/python -m reliability_lab crash-resume-check --prediction 'your prediction'
```

This creates a new five-case attempt with up to nineteen worker phases. It is **not** part of the saved-evidence demo or a command run for this documentation closeout. Never describe ordinary offline validation as another successful crash reproduction.
