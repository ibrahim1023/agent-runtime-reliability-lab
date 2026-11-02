# First evidence walkthrough: attempts versus effects

## Prediction recorded in the learning conversation

The learner predicted that an interrupted action could be attempted again without idempotency protection. The refinement was that the runtime can replay a pending tool call without a fresh model decision. The receiver must enforce a stable operation ID; saving the ID alone is insufficient.

## Inspect the evidence

Open `results/historical/idempotency/unprotected-1.json` and `protected-1.json`.

1. Find two `tool_enter` events with different process IDs: execution entered the tool twice across processes.
2. Compare the operation IDs: both attempts use the same ID in each case.
3. Inspect `committed_receipts`: unprotected has two rows; protected has one.
4. Compare `ledger_result` receipts: protected resume returns the first receipt with `reused: true`.

These exported events and SQL row values were read from the original saved journals and databases in read-only mode. They corroborate historical results; they are not new executions. Original checkpoints remain untouched and are not exported: this milestone cannot independently reconstruct checkpoint internals from its public evidence alone.

## Mechanism in the existing receiver

Within one SQLite transaction, the protected receiver checks for an existing operation ID, rejects different contents under that ID, and returns an existing receipt or inserts the action and receipt together. A unique constraint and write transaction serialize duplicate submissions.

The receiver is a separate consistency domain from the graph checkpoint. An action may commit before tool completion is saved. Recovery can repeat the attempt; receiver deduplication prevents another local effect.

## Next learning checkpoint

The learner initially proposed a new action for changed contents. We clarified that an operation ID identifies one intended action: changed contents under that ID must be rejected; a new intended action needs a new ID. The extracted contract now verifies rejection, unchanged ledger contents, and continued receipt reuse for the original payload. No new model metrics were generated.
