# Receiver extraction plan — November 2, 2026

Scope: extract the existing local SQLite receiver unchanged. Reuse local_checks from the historical idempotency runner as behavioral contracts, expressed as independent standard-library unittest cases. No runtime integration, model calls, network, dependency installs, or new live metrics.

Files: reliability_lab/receiver.py owns the receiver; tests/test_receiver.py owns contracts; docs/provenance.md and results/manifest.json record reuse. Preserve upstream MIT notice in THIRD_PARTY_NOTICES.md before extracting code. The local experimental receiver is not upstream SDK implementation.

Steps:
1. Write five observable contracts: conflicting payload rejected without state change; reopened receiver reuses exact receipt; fresh ID permits another action; eight concurrent duplicates commit once; unprotected control duplicates as expected.
2. Confirm discovery fails because the receiver has not been extracted.
3. Copy the existing receiver byte-for-byte, preserving source hash.
4. Run all offline tests without site packages or credentials; record actual outcome and distinguish these receiver checks from crash/resume or LLM evaluations.

Review limits: tests use fresh temporary SQLite databases. They do not establish arbitrary remote delivery, graph concurrency, crash recovery, or production readiness. Historical evidence verification and the unified CLI remain separate tasks.
