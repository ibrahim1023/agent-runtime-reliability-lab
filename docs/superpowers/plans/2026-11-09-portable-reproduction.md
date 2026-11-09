# Portable crash reproduction plan

**Goal:** Execute the existing five-case crash/replay fixture once on a fresh hosted Linux runner and compare effects, attempts and receipt reuse with saved same-host evidence.

**Spec:** `results/portable-reproduction-plan-v1.json` is the frozen budget, expectations and publication policy. User authorized independent reproduction and supplied a prospective prediction. Use GitHub's existing public-repository Actions facility, not a new service or agent loop.

**Design:** One manual-only workflow installs eight seed versions into a non-editable virtual environment. It runs the existing CLI once. A small standard-library export reuses the existing assessor and emits only reviewed fields, never raw checkpoint/tool logs. Existing runtime behavior and historical artifacts remain unchanged.

**Approach:** Hosted Ubuntu is the implementation choice; a second physical machine is unavailable to this session. Do not call this independent human verification. No provider credentials, live calls, inference infrastructure or automatic schedules.

## Task 1 — Result export

- [x] Write tests proving duplicates remain task failures, completed output cannot override a failed process, mismatched case/phase observations fail, and raw fields are excluded.
- [x] Watch them fail on the missing exporter, implement `summarize_execution(report, exit_code)`, then run development tests.
- [x] Capture environment identity separately without publishing filesystem paths.

## Task 2 — Manual workflow

- [x] Pin official checkout/setup-python/upload-artifact to resolved commit SHAs; read-only repository token and no persisted checkout credentials.
- [x] Install once with pip retries disabled and a five-minute step cap; retain setup failure without another dispatch.
- [x] Run existing CLI once; capture output locally on runner, no raw trace/checkpoint upload.
- [x] Always export the bounded summary; preserve process exit and failed steps rather than treating artifact upload as success.
- [x] Verify offline/tests and review before committing/pushing.

## Task 3 — Run and review

- [ ] Dispatch exactly once with the learner prediction; check actual workflow SHA and job outcome.
- [ ] Review downloaded summary, compare selected module identities and attempt/effect outcomes, preserve any interruption.
- [ ] Commit/push the reviewed result and explain the prediction versus evidence in simple language.

**Review focus:** No masked nonzero exit, no green empty/incomplete roster, no skipped dependency/version check, no raw logs in artifacts, no double dispatch/retry. Installation failure is not runtime failure. Same outcomes do not imply identical dependency bytes or a speed improvement.

Review note: no dispatch blocker. Minor coverage gap retained: exporter CLI/environment failure branches are not all tested; observation-logic contracts are covered.
