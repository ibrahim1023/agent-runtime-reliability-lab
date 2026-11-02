"""Check optional cohort identities and exclusions, not model capability anew."""

import json
from pathlib import Path

from reliability_lab.evidence import checked_bytes, require

COHORTS = ('explicit-alternative-120b', 'original-present-followup-120b', 'comparison-20b')
PILOT = ('explicit', 'ambiguous_original', 'ambiguous_alternative', 'missing_alternative', 'original_present', 'confirmation_required')


def expected_labels(cohort: str) -> set[str]:
    """Keep the known retrospective inventories separate and complete."""
    if cohort == COHORTS[0]:
        labels = {f'{v}-{case}-1' for v in ('previous', 'scoped') for case in PILOT}
        labels.update(f'{v}-explicit-{r}' for v in ('previous', 'scoped') for r in (2, 3))
        return labels
    if cohort == COHORTS[1]:
        return {'scoped-original_present-2'}
    return {f'{v}-{case}-{r}' for v in ('previous', 'scoped')
            for case, r in (('original_present', 1), ('original_present', 2), ('explicit', 1), ('ambiguous_alternative', 1))}


def verify_cohort(data: dict, cohort: str) -> None:
    """Verify roster/classification, without reissuing retained behavior verdicts."""
    model = 'groq:openai/gpt-oss-20b' if cohort == COHORTS[2] else 'groq:openai/gpt-oss-120b'
    require(data['cohort'] == cohort and data['historical'] is True and data['model'] == model, 'Optional model cohort identity changed')
    rows = data['records']; expected = expected_labels(cohort)
    require(len(rows) == len(expected) and {r['label'] for r in rows} == expected, 'Optional cohort roster incomplete')
    require(data['resolves_120b_original_present_failure'] is False, 'Different model cannot resolve the 120B failure')
    valid = 0
    for row in rows:
        require(row['label'] == f"{row['variant']}-{row['case']}-{row['repetition']}", 'Wrong inventory row identity')
        if row['valid_behavior_trial']:
            valid += 1
            require(row['status'] == 'completed' and row['error'] is None and
                    type(row['historical_behavior_correct']) is bool and type(row['task_completed']) is bool, 'Invalid completed inventory entry')
        else:
            require(row['status'] == 'provider_interrupted' and row['error'] == {'type': 'RateLimitError', 'http_status': 429, 'category': 'provider_quota'} and
                    row['historical_behavior_correct'] is None and row['task_completed'] is None, 'Provider interruption cannot receive behavior/task verdicts')
    require(data['attempts'] == len(rows) and data['valid_behavior_trials'] == valid and data['invalid_provider_attempts'] == len(rows)-valid,
            'Optional inventory counts disagree')
    require(valid == {COHORTS[0]: 13, COHORTS[1]: 0, COHORTS[2]: 8}[cohort], 'Changed retrospective validity counts')


def verify_optional_inventory(root: Path) -> dict:
    """Preserve the unresolved case and report three inventories as inventories."""
    manifest = json.loads((root/'results/manifest.json').read_text())
    entries = manifest['optional_cohorts']
    require([e['cohort'] for e in entries] == list(COHORTS), 'Changed optional cohort inventory')
    cohorts = []
    for entry in entries:
        require(entry['export'] == f"results/optional/{entry['cohort']}.json", 'Wrong optional export path')
        data = json.loads(checked_bytes(root, entry['export'], entry['sha256']))
        verify_cohort(data, entry['cohort']); cohorts.append(data)
    entry = manifest['unresolved_120b_result']
    require(entry['export'] == 'results/optional/unresolved-original-present-120b.json', 'Missing unresolved result')
    unresolved = json.loads(checked_bytes(root, entry['export'], entry['sha256']))
    require(unresolved['resolution'] == 'unresolved' and unresolved['model'] == 'groq:openai/gpt-oss-120b' and
            unresolved['label'] == 'scoped-original_present-1' and unresolved['selection_events'] == [] and
            unresolved['historical_behavior_correct'] is False and unresolved['task_completed'] is False,
            'Unresolved 120B failure was altered or claimed resolved')
    require('/notes/data.txt' in unresolved['final_files'] and '/out.txt' not in unresolved['final_files'] and
            all(call['name'] == 'ls' for call in unresolved['tool_calls']), 'Unresolved source observations changed')
    row = next(r for r in cohorts[0]['records'] if r['label'] == unresolved['label'])
    require(row['historical_behavior_correct'] is False and row['task_completed'] is False, 'Inventory dropped the unresolved failure verdict')
    require(cohorts[1]['planned_trials'] == 4 and cohorts[1]['unstarted_trials'] == 3, 'Blocked follow-up attempts were invented')
    return {'status': 'passed', 'kind': 'historical inventory/classification checks; not full per-run behavioral validation',
            'cohort_attempt_counts': [c['attempts'] for c in cohorts], 'valid_trial_counts': [c['valid_behavior_trials'] for c in cohorts],
            'unresolved_120b': 'preserved', 'new_model_calls': 0}
