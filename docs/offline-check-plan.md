# Offline verification step — November 2, 2026

This step implements the authorized sprint's two separate verification layers; it does not launch a new experiment.

- [x] Freeze expectations for the four historical cases and receiver contracts.
- [x] Add negative tests before implementing the evidence verifier and command.
- [x] Validate hashes and event/receipt/effect consistency without original paths.
- [x] Run receiver contracts in fresh disposable SQLite databases.
- [x] Add nonzero-failure, fresh-attempt-directory, and socket-blocking command tests.
- [x] Diagnose and reproduce SQLite connection warnings; fix the extracted copy and record provenance.
- [x] Run all development tests and the combined command; document outcomes and limits.

Remaining sprint work: export other cohorts with their own validators, scripted runtime mechanics, approval/crash intersection, provenance/settings completion, packaging and clean-environment reproduction. Nothing is committed or published by this step.
