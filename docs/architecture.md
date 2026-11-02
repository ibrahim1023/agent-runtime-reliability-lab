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

Approval applies before tool execution. Existing historical records show pending review surviving restart, and simulated approve/reject/edit inputs changing what proceeds. They do not yet demonstrate approval and post-commit replay at the same boundary.

## Separate diagnostic evidence

LangSmith traces record observable operations for diagnosis. A trace is not a checkpoint and does not resume execution. The public lab includes reviewed local phase records, journals, and SQL receipt extracts so a private tracing dashboard is not required to inspect the packaged claims.

## Current executable boundary

The portable code currently executes only SQLite receiver contracts. It validates historical agent records but does not yet launch a new graph, call a model, or reproduce approval/crash mechanics. Scripted real-runtime fixtures and their dependency provenance remain future milestones.
