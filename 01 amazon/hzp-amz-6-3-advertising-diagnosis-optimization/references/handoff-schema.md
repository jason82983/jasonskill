# 6-3 → 6-4 Decision Handoff

6-3 is DECIDE only. It may create a candidate Desired State, but does not prepare or apply an Amazon Ads write plan. Every action candidate starts `确认状态=待确认`.

After the user changes a decision to `已批准` through the established human decision path, hand off the approved decision row(s), source Product_Code, 6-2 Run_ID, 6-0-5 Run_ID, 6-3 Run_ID, stable object IDs, current values, desired values, reason and next observation condition to 6-4. Keep approvals as a distinct decision record; do not overwrite immutable 6-3 Run Packages. `暂缓` is not handed off for execution.

6-4 applies an approved daily operating action only after current identity, scope, permission, capability and actual-state checks. It preserves the decision and proposed amount. It may stop for `TECHNICAL_EXECUTION_CONFLICT` (identity mismatch, missing capability, infeasible state, or material current-vs-approved difference), report the exact conflict, and return for a new decision. 6-4 must not silently re-judge the business merit or change the approved amount. 6-1 remains reserved for initial 6-0-5 advertising architecture BUILD.

Candidate semantics:

- Intent `放大/收缩/升级独立/降级共享/阶段升级/阶段降级/暂停候选` must state destination task, control mode and/or phase as applicable.
- Campaign budget/placement decisions carry both current and proposed values.
- Target bid decisions carry both current and proposed values.
- Search Term `收割候选` and `否定候选` are business proposals only; 6-4 requires a complete supported execution mapping and explicit approval before a concrete target is created or negated.

Handoff validation errors include `EXECUTION_HANDOFF_INVALID`, `PROPOSED_VALUE_MISSING`, `DECISION_CONFLICT`, missing source Run IDs, unresolved entity IDs, and non-approved confirmation state. 6-2 remains independent: it next collects facts and does not consume 6-3 business decisions as performance facts.
