# Test lesson: matching bytes can still contain a contradictory claim

## Prediction and bounded experiment

The learner's prediction was **unsure**: “I'm not sure if I have the answer.” We retain that uncertainty rather than replace it with the explanation supplied afterward.

This experiment changes disposable copies of historical evidence. It makes no model calls and executes no Deep Agents graph. The actual historical search review remains unchanged.

The question: if we relabel the rejected ambiguous write as correct, and recompute its manifest hash, will the public verifier still reject the contradiction?

## Before adding the check

At base commit `0ec0200`, the search review was documented as not yet integrated. We first ran nine command-level tests: one unaltered control and eight altered copies. The control passed; all eight rejection tests failed because the command returned success. That demonstrated a coverage gap, not yet a comparison of hashes versus meaning: the old command ignored the search review altogether.

## The decisive control after integration

The focused test changes the label in the detailed extract, roster and summary matrix, then recomputes the review hash. The byte-identity helper successfully reads that altered review. Therefore the later rejection cannot be explained by a stale hash or a mismatched summary alone.

The new review check rejects it because:

- The fixed task contains two plausible sources and requires a user choice.
- The recorded tool sequence includes a successful write.
- The saved final filesystem contains its output.
- A positive ambiguity-handling label contradicts those recorded effects.

The failed review stops the command before fresh receiver contracts. The intact review still passes. Other tests catch a dropped rejected run, a changed read result, a false no-output artifact, a changed selected prototype, a changed matrix, a missing review entry, and byte drift without rehashing.

## What these checks establish

We improved the **evidence validator**. We did not improve or re-evaluate the model or middleware. The fixed ambiguous fixture lets us check the no-write constraint mechanically; this is not a general natural-language permission parser or answer-quality judge. The original final answers retain their historical assistant-review status.

The public command reports separate units: sixteen historical records, a 25-entry retrospective search roster with three detailed ambiguity extracts, and six fresh receiver contracts. The seven stored graph-contract results are historical inventory, not fresh execution. Tests also demonstrate failures under recomputed manifest hashes, but coherent fabrication of all evidence and its manifest remains outside the checker’s guarantees.

The next runtime lesson remains separate: exercise the existing seven middleware contracts through real graph/tool execution using scripted model responses. Before that new experiment, get a new prediction and establish the dependency/extraction boundary. No live-call budget is needed for these validator tests; any later live evaluation needs its own agreed run and token budget.
