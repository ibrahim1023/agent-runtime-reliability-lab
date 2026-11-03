# Boundaries in this lab

```text
Model proposes an action
    → Middleware permits, denies, or pauses for review
    → Tool body invokes the receiver
    → Receiver commits an action and receipt
    → Tool result becomes input to the next model call
```

Deep Agents assembles the capabilities and middleware. LangChain supplies the agent loop; LangGraph executes it and manages configured checkpoint persistence. This lab does not implement their runtime.

## Separate consistency domains

A graph checkpoint records execution state, including pending work. The receiver's SQLite database records externally committed actions. They are separate transactions: a receiver action can commit before tool completion is checkpointed. The runtime may replay the pending tool on recovery. A stable application-generated operation ID and atomic receiver-side deduplication can make that repeated attempt return the original local receipt.

Approval applies before tool execution. Existing historical records show pending review surviving restart, and simulated approve/reject/edit inputs changing what proceeds. The [fresh scripted crash fixture](crash-resume-evidence.md) now combines these at one post-commit boundary, with two protected approval repetitions, edit, reject and an unprotected control.

## Separate diagnostic evidence

LangSmith traces record observable operations for diagnosis. A trace is not a checkpoint and does not resume execution. The public lab includes reviewed local phase records, journals, and SQL receipt extracts so a private tracing dashboard is not required to inspect the packaged claims.

## Current executable boundary

The standard-library path executes SQLite receiver contracts and checks historical evidence. Separate opt-in commands launch the baseline/conservative root-alias pair and the remaining six original middleware fixtures, using a scripted model and real middleware/search tools. They record preserved proposals, actual execution arguments, raw tool callback results, model-facing ToolMessages and next model input. They make no provider calls. A third opt-in command, `crash-resume-check`, uses persistent approval and a separate receiver database across fresh workers. Optional runtime imports are lazy so the dependency-free path remains separate. See [the first scripted graph check](scripted-root-check.md) for environment/source provenance and the unverified clean-install boundary.


## Application outcome reporting

The [read-only outcome reporter](outcome-reporting-evidence.md) runs outside the agent graph. With isolated workers stopped, it checks committed receiver rows for the stable operation ID and approved payload. It distinguishes one effect, duplicates, rejection, missing effects, conflicting evidence and unknown evidence. It does not infer a total effect count from a single receipt or replace the original model answer. Integration into the runtime's final response is a separate pending step.
