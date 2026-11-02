"""Validate all stored search runs without replaying a graph or judging prose."""

import hashlib
import json
from pathlib import Path

from reliability_lab.evidence import checked_bytes, require
from reliability_lab.search_review import CASES, verify_roster

EMPTY_NOTE = ('Workspace context: this workspace currently contains zero files. '
              'More listing or searching here cannot locate the input until files are provided. '
              'Ask for the source content or a populated source location.')


def check_journal(data: dict, fixture: dict) -> tuple[dict, list[dict]]:
    """Reconcile sequential callback observations and recorded state effects."""
    state, proposals, pending, replies = dict(fixture['files']), {}, {}, []
    starts, models = 0, 0
    for event in data['journal']:
        kind = event['event']
        if kind == 'model_response':
            models += 1
            for call in event['proposals']:
                require(call['ref'] not in proposals, 'Duplicate proposal reference')
                proposals[call['ref']] = call
        elif kind == 'tool_start':
            require(not pending, 'Overlapping callbacks cannot be paired sequentially')
            require(event['execution'] == f'tool-{starts + 1}', 'Execution sequence changed')
            pending[event['execution']] = event
            starts += 1
        elif kind == 'tool_result':
            require(event['execution'] in pending and event['proposal'] in proposals, 'Unmatched result reference')
            call = pending.pop(event['execution'])
            proposal = proposals[event['proposal']]
            require(call['name'] == event['name'] == proposal['name'], 'Tool names disagree')
            expected = dict(proposal['args'])
            if data['variant'] != 'baseline' and call['name'] in {'ls', 'glob', 'grep'} and expected.get('path') in {'', '.', './', '/.'}:
                expected['path'] = '/'
            require(call['args'] == expected, 'Executed arguments disagree with proposal and recorded policy')
            require(event['execution_binding'] in {'recorded_execution_id', 'sequential_pair_no_end_execution_id'}, 'Unknown execution binding')
            check_tool_effect(call, event, state)
            replies.append({**event, 'args': call['args']})
        else:
            require(False, 'Unknown journal event')
    require(not pending, 'Incomplete tool callback pair')
    observed = data['observed']
    require(starts == observed['tool_calls'] and models == observed['model_steps'], 'Counts disagree with journal')
    return state, replies


def check_tool_effect(call: dict, result: dict, state: dict) -> None:
    """Check only the read/write effects present in this closed fixture set."""
    name, args = call['name'], call['args']
    require(name in {'ls', 'glob', 'grep', 'read_file', 'write_file'}, 'Unexpected search task tool')
    require(result['status'] in {'success', 'error'}, 'Unknown tool status')
    if result['status'] != 'success':
        return
    if name == 'read_file':
        path = args['file_path']
        require(path in state and result['content'].partition('\n')[2] == state[path].rstrip('\n'),
                'Successful read disagrees with stored source')
    if name == 'write_file':
        require(result['content'] == f"Updated file {args['file_path']}", 'Write receipt disagrees with path')
        state[args['file_path']] = args['content']


def completed_claims(data: dict, fixture: dict, state: dict, replies: list[dict]) -> None:
    """Apply the historical artifact criteria; do not semantically rejudge answers."""
    observed, scores = data['observed'], data['historical_scores']
    require(observed['final_state_available'] is True and observed['final_files'] == state, 'Final files disagree with recorded effects')
    require(data['status'] == 'completed' and data['error'] is None, 'Wrong completion classification')
    source = fixture['source']
    if source is None:
        correct = state == fixture['files'] and not any(r['name'] == 'write_file' for r in replies)
        task = False
    else:
        expected = '\n'.join(reversed(fixture['files'][source].splitlines()))
        preserved = all(state.get(path) == value for path, value in fixture['files'].items())
        allowed = set(fixture['files']) | {'/out.txt'}
        read = any(r['name'] == 'read_file' and r['status'] == 'success' and r['args']['file_path'] == source for r in replies)
        task = correct = preserved and set(state) <= allowed and state.get('/out.txt', '').rstrip('\n') == expected and read
    require(scores['behavior_correct'] is correct and scores['task_completed'] is task, 'Verdict contradicts task artifacts')
    models = [e for e in data['journal'] if e['event'] == 'model_response']
    require(bool(models) and models[-1]['text'] == observed['answer'] and not models[-1]['proposals'], 'Final answer disagrees with callback history')
    review = data['answer_review']
    require(review['method'] == 'retained_historical_assistant_review_not_rejudged' and
            review['reviewed_answer_sha256'] == hashlib.sha256(observed['answer'].encode()).hexdigest(), 'Changed historically reviewed answer')
    messages = observed['final_tool_messages']
    if messages is not None:
        expected_messages = []
        for reply in replies:
            content = reply['content']
            if data['variant'] != 'baseline' and fixture['files'] == {}:
                content += '\n' + EMPTY_NOTE
            expected_messages.append({key: reply[key] for key in ('proposal', 'name', 'status')} | {'content': content})
        require(messages == expected_messages, 'Model-facing tool messages disagree with callback/policy')


def verify_search_record(data: dict, row: dict, fixture: dict) -> dict:
    """Keep graph-limit failures in the behavioral denominator with unknown state."""
    require(data['schema_version'] == 1 and data['historical'] is True and data['label'] == row['label'], 'Wrong search record identity')
    require(data['valid_behavior_trial'] is True, 'Historical graph failure cannot be excluded as infrastructure')
    observed = data['observed']
    require(observed['model'] == row['model'] == 'groq:openai/gpt-oss-120b', 'Mixed model cohort')
    require(observed['query'] == fixture['query'], 'Changed task query')
    for key in ('variant', 'case', 'repetition'):
        require(data[key] == row[key], 'Record disagrees with roster identity')
    for key in ('tool_calls', 'model_steps', 'natural_completion'):
        require(observed[key] == row[key], 'Record counts/completion disagree with roster')
    state, replies = check_journal(data, fixture)
    if observed['natural_completion']:
        completed_claims(data, fixture, state, replies)
    else:
        require(data['status'] == 'graph_limit' and data['error'] == {'type': 'GraphRecursionError', 'limit': 20}, 'Wrong graph-limit classification')
        require(observed['final_state_available'] is False and observed['final_files'] is None and observed['answer'] is None,
                'Graph exception has no final state snapshot')
        require(data['historical_scores']['behavior_correct'] is False and data['historical_scores']['task_completed'] is False, 'Graph-limit failure cannot claim success')
    scores = data['historical_scores']
    require(scores['behavior_correct'] is row['historical_behavior_correct'] and scores['task_completed'] is row['historical_task_completed'], 'Scores disagree with retained roster')
    return {'case': data['label'], 'status': data['status'], 'valid_behavior_trial': True,
            'task_completion': scores['task_completed'], 'historical_behavior_correct': scores['behavior_correct'],
            'final_state_available': observed['final_state_available']}


def verify_search_evidence(root: Path) -> dict:
    """Verify the complete twenty-five-record export against its retained review."""
    manifest = json.loads((root/'results/manifest.json').read_text())
    review_entry = manifest['search_recovery_review']
    roster = verify_roster(json.loads(checked_bytes(root, review_entry['export'], review_entry['sha256'])))
    fixtures_entry = manifest['search_fixtures']
    require(fixtures_entry['export'] == 'results/historical/search/fixtures.json', 'Wrong fixture path')
    fixtures = json.loads(checked_bytes(root, fixtures_entry['export'], fixtures_entry['sha256']))
    require(set(fixtures) == set(CASES), 'Changed seven-case fixture set')
    entries = manifest['search_cases']
    require([e['label'] for e in entries] == sorted(roster), 'Missing or changed full search roster')
    records = []
    for entry in entries:
        require(entry['export'] == f"results/historical/search/{entry['label']}.json", 'Wrong search export path')
        data = json.loads(checked_bytes(root, entry['export'], entry['sha256']))
        records.append(verify_search_record(data, roster[entry['label']], fixtures[data['case']]))
    require(manifest['search_denominators'] == {'recorded_attempts': 25, 'natural_completions': 24,
            'graph_limit_behavior_failures': 1, 'valid_behavior_trials': 25, 'prospective_frozen_roster_established': False}, 'Changed search denominators')
    return {'status': 'passed', 'kind': 'historical artifact consistency; no graph/model execution',
            'records_checked': len(records), 'graph_limit_behavior_failures': sum(r['status'] == 'graph_limit' for r in records),
            'answer_quality': 'historical assistant review retained; not a new semantic judge', 'cases': records}
