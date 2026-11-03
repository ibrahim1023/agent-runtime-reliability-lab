"""Read-only application reports for this lab's closed local receiver operations."""

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Literal, TypedDict

Decision = Literal['approve', 'edit', 'reject']
Outcome = Literal['completed_once', 'duplicate_detected', 'rejected', 'not_recorded',
                  'payload_conflict', 'policy_violation', 'outcome_unknown']


class OutcomeReport(TypedDict):
    """Evidence-scoped result; unknown task completion is explicitly null."""

    outcome: Outcome
    operation_id: str
    observed_effects: int | None
    task_completed: bool | None
    evidence_available: bool
    graph_finished: bool
    report: str


def read_snapshot(path: Path, operation_id: str) -> list[tuple[str, str, str]]:
    """Read matching columns in one snapshot without creating a missing database."""
    with closing(sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=1)) as conn:
        conn.execute('PRAGMA query_only=ON')
        conn.execute('BEGIN')
        return conn.execute('SELECT operation_id, message, receipt FROM entries WHERE operation_id = ? ORDER BY id',
                            (operation_id,)).fetchall()


def matching_receipts(rows: list[tuple[str, str, str]], approved_message: str) -> bool:
    """Require receipt identity and payload to agree with their receiver columns."""
    receipts = set()
    for operation, message, encoded in rows:
        try:
            receipt = json.loads(encoded)
            valid = (isinstance(receipt, dict) and receipt.get('operation_id') == operation and
                     receipt.get('message') == message == approved_message and
                     receipt.get('status') == 'recorded' and isinstance(receipt.get('receipt_id'), str) and
                     bool(receipt['receipt_id']))
            if not valid or receipt['receipt_id'] in receipts:
                return False
            receipts.add(receipt['receipt_id'])
        except (ValueError, TypeError):
            return False
    return True


def outcome_report(outcome: Outcome, operation_id: str, count: int | None, finished: bool) -> OutcomeReport:
    """Render a fixed report from classified evidence, never from an expected verdict."""
    reports = {
        'completed_once': 'The local receiver contains exactly one committed record for this approved operation.',
        'duplicate_detected': f'Duplicate detected: the local receiver contains {count} committed records for this operation. The record-once task was not completed correctly.',
        'rejected': 'The action was rejected. No committed record was found for this operation in the local receiver.',
        'not_recorded': 'No committed record was found for this operation in the local receiver. The task was not completed.',
        'payload_conflict': 'The receiver contents or receipt conflict with the approved operation. The requested outcome is not verified.',
        'policy_violation': 'The receiver contains a committed action despite rejection. Review policy was violated.',
        'outcome_unknown': 'The outcome is unknown: receiver evidence is unavailable or execution is unfinished. I cannot verify that the action completed exactly once.',
    }
    return {'outcome': outcome, 'operation_id': operation_id, 'observed_effects': count,
            'task_completed': None if outcome == 'outcome_unknown' else outcome == 'completed_once',
            'evidence_available': count is not None, 'graph_finished': finished, 'report': reports[outcome]}


def reconcile_action(path: Path, *, operation_id: str, approved_message: str,
                     decision: Decision, graph_finished: bool) -> OutcomeReport:
    """Report one operation after its isolated graph workers have stopped.

    Args:
        path: Existing local receiver database, opened in read-only mode.
        operation_id: Application identity preserved across attempts.
        approved_message: Persisted approved contents, including reviewer edits.
        decision: Review outcome supplied by the application.
        graph_finished: Whether the caller established terminal graph execution.

    Returns:
        A report scoped to the local receiver snapshot, with null completion when unknown.

    Raises:
        ValueError: If review or execution context is invalid.
    """
    if decision not in ('approve', 'edit', 'reject') or not operation_id or not isinstance(graph_finished, bool):
        raise ValueError('Valid review decision, operation identity and execution state required')
    if not graph_finished:
        return outcome_report('outcome_unknown', operation_id, None, False)
    try:
        rows = read_snapshot(path, operation_id)
    except (sqlite3.Error, OSError):
        return outcome_report('outcome_unknown', operation_id, None, True)
    count = len(rows)
    if decision == 'reject':
        outcome: Outcome = 'policy_violation' if count else 'rejected'
    elif not matching_receipts(rows, approved_message):
        outcome = 'payload_conflict'
    else:
        outcome = 'not_recorded' if not count else ('completed_once' if count == 1 else 'duplicate_detected')
    return outcome_report(outcome, operation_id, count, True)
