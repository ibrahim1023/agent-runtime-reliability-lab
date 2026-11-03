# Assessment amendment A1: reviewer-edit message envelope

Recorded after the first and only v1 execution, 2026-11-03. The frozen v1 criteria are unchanged. No worker rerun or extra provider call is authorized by this amendment.

The original assessment returned `failed`: four case contracts met, while `protected-edit` failed `report_matches_observed_tool_result`. Inspection shows the scripted final answer exactly equals its actual ToolMessage. Deep Agents prefixes the receipt with an authorized-edit explanation and `Tool response:`. The assessor incorrectly required the whole message to be JSON. SQL rows and both receiver journal receipts agree on `reviewer-approved`; replay reused the same receipt.

Preserve the original report and its assessor hash. Add a regression using the actual retained ToolMessage, then allow an edit-only envelope whose executed tool and arguments exactly match the approved action. Parse its receipt suffix and compare it with SQL. Reject altered prefixes, altered arguments, forged receipt suffixes, or an envelope outside the edit condition. Require answer equality to the entire actual ToolMessage. Record reassessment separately, identifying the corrected assessor hash. This is offline reassessment of saved observations, not a second runtime experiment and not a new semantic model judge.

The note says “human reviewer” because that is upstream middleware wording; this experiment supplied a simulated reviewer decision. It does not establish authenticated human review.
