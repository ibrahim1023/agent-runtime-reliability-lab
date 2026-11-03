"""Select the final application response while preserving the model's answer."""

import json
from pathlib import Path
from typing import TypedDict

from reliability_lab.outcome_reporting import Decision, OutcomeReport, reconcile_action


class FinalResponse(TypedDict):
    """Separate diagnostic model output from evidence-backed delivery."""

    model_answer: str | None
    reconciliation: OutcomeReport
    user_response: str
    delivery_source: str


def final_response(path: Path, *, operation_id: str, approved_message: str,
                   decision: Decision, graph_finished: bool, model_answer: str | None) -> FinalResponse:
    """Reconcile a terminal isolated operation before choosing its application response."""
    result = reconcile_action(path, operation_id=operation_id, approved_message=approved_message,
                              decision=decision, graph_finished=graph_finished)
    response = result['report']
    if result['outcome'] == 'completed_once':
        response += f' Recorded contents: {json.dumps(approved_message)}.'
    return {'model_answer': model_answer, 'reconciliation': result,
            'user_response': response, 'delivery_source': 'receiver_reconciliation'}
