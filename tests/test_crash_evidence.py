"""Reject misleading crash/resume conclusions using hand-checked observations."""

import copy
import unittest

from reliability_lab.crash_evidence import assess_case


def observation() -> dict:
    return {
        "protected": True, "decision": "approve", "operation_id": "op",
        "approved_message": "note", "phases": [
            {"phase": "initial", "pid": 1, "exit_code": 0, "pending_review": True, "effects": 0, "tool_entries": 0},
            {"phase": "restore", "pid": 2, "exit_code": 0, "pending_review": True, "effects": 0, "tool_entries": 0},
            {"phase": "decision", "pid": 3, "exit_code": 86, "effects": 1, "tool_entries": 1},
            {"phase": "resume", "pid": 4, "exit_code": 0, "pending_review": False, "effects": 1, "tool_entries": 2}],
        "same_pending_review": True, "graph_completed": True,
        "entries": [{"operation_id": "op", "message": "note", "receipt_id": "r1", "status": "recorded"}],
        "tool_entries": [{"operation_id": "op", "message": "note"}] * 2,
        "receiver_results": [
            {"receipt": {"operation_id": "op", "message": "note", "receipt_id": "r1", "status": "recorded"}, "reused": False},
            {"receipt": {"operation_id": "op", "message": "note", "receipt_id": "r1", "status": "recorded"}, "reused": True}],
        "final_tool_status": "success", "final_tool_content": '{"operation_id":"op","message":"note","receipt_id":"r1","status":"recorded"}',
        "answer": '{"operation_id":"op","message":"note","receipt_id":"r1","status":"recorded"}',
    }


class CrashEvidenceContracts(unittest.TestCase):
    def test_protected_replay_has_two_entries_and_one_effect(self) -> None:
        result = assess_case(observation())
        self.assertTrue(result["contract_met"])
        self.assertTrue(result["approved_task_completed"])
        self.assertTrue(result["report_matches_observed_tool_result"])

    def test_unprotected_expected_duplication_is_not_task_success(self) -> None:
        record = observation()
        record["protected"] = False
        duplicate = {**record["entries"][0], "receipt_id": "r2"}
        record["entries"].append(duplicate)
        record["receiver_results"][1] = {"receipt": duplicate, "reused": False}
        record["phases"][-1]["effects"] = 2
        import json
        record["answer"] = record["final_tool_content"] = json.dumps(duplicate)
        result = assess_case(record)
        self.assertTrue(result["contract_met"])
        self.assertFalse(result["approved_task_completed"])
        self.assertTrue(result["report_matches_observed_tool_result"])
        self.assertFalse(result["report_accounts_for_all_effects"])

    def test_changed_identity_or_payload_fails_contract(self) -> None:
        for field in ("operation_id", "message"):
            record = copy.deepcopy(observation())
            record["tool_entries"][1][field] = "changed"
            self.assertFalse(assess_case(record)["contract_met"])

    def test_protected_duplicate_or_reapproval_fails_contract(self) -> None:
        record = observation()
        record["entries"].append(dict(record["entries"][0]))
        self.assertFalse(assess_case(record)["contract_met"])
        record = observation()
        record["phases"][-1]["pending_review"] = True
        self.assertFalse(assess_case(record)["contract_met"])

    def test_fabricated_answer_and_missing_crash_are_rejected(self) -> None:
        record = observation()
        record["answer"] = "success"
        self.assertFalse(assess_case(record)["contract_met"])
        record = observation()
        record["phases"][2]["exit_code"] = 0
        self.assertFalse(assess_case(record)["contract_met"])

    def test_rejection_is_correct_handling_without_task_completion(self) -> None:
        record = observation()
        record.update(decision="reject", entries=[], tool_entries=[], receiver_results=[],
                      final_tool_status="error", final_tool_content="rejected", answer="rejected")
        record["phases"] = record["phases"][:3]
        record["phases"][-1].update(exit_code=0, pending_review=False, effects=0, tool_entries=0)
        result = assess_case(record)
        self.assertTrue(result["contract_met"])
        self.assertTrue(result["review_policy_handled"])
        self.assertFalse(result["approved_task_completed"])

    def test_new_receipt_on_protected_replay_fails_contract(self) -> None:
        record = copy.deepcopy(observation())
        record["receiver_results"][1]["receipt"] = {**record["entries"][0], "receipt_id": "other"}
        self.assertFalse(assess_case(record)["contract_met"])

    def test_edit_envelope_matches_approved_action_and_sql_receipt(self) -> None:
        import json
        record = copy.deepcopy(observation())
        record["decision"] = "edit"
        prefix = ('Note: a human reviewer replaced this tool call before it ran. '
                  'The call recorded in your message is the one you produced, not the one that executed. '
                  'This was intentional and authorized. Do not re-issue your original call. '
                  'Executed instead: record_action with arguments {"message": "note"}.\n\nTool response:\n')
        record["answer"] = record["final_tool_content"] = prefix + json.dumps(record["entries"][0])
        self.assertTrue(assess_case(record)["contract_met"])
        for replacement in ('{"message": "wrong"}', '{"receipt_id": "invented"}'):
            bad = copy.deepcopy(record)
            if 'message' in replacement:
                bad["answer"] = bad["final_tool_content"] = record["answer"].replace('{"message": "note"}', replacement)
            else:
                bad["answer"] = bad["final_tool_content"] = prefix + replacement
            self.assertFalse(assess_case(bad)["contract_met"])
        record["decision"] = "approve"
        self.assertFalse(assess_case(record)["contract_met"])
