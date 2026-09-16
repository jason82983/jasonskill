# 6-0-5 Approved Battle Plan Input Contract

6-0-5 is the sole strategic source for 6-1. Resolve with `scripts/new_product_battle_plan_contract.py::resolve_latest_approved_battle_plan(product_root, product_code)`. Never select the newest file by timestamp alone; require the resolver’s CURRENT PRODUCT → VALID → LATEST APPROVED same-run bundle.

| Role | Formal filename stem | Required lineage |
|---|---|---|
| A | `新品意图市场作战表` | Intent Code, intent/control decisions, approval state |
| B | `新品关键词作战明细` | Battle Unit ID, Intent Code, task, control mode, targets and approval |
| C | `新品关键词阶段规划表` | Keyword lifecycle, phase, execution method and approval |

All three CSVs and the formal 6-0-5 HTML must match Product Code and `RUN_ID`. The resolver validates schema, lineage, coverage and approval contract. Current execution phase is `PHASE_1`; other phases are not executable until the upstream contract explicitly changes.

6-1 consumes only B rows whose `确认状态=APPROVED`, phase is currently allowed, and `控制方式` is not `不投`. A/C/B `PROPOSED` or `HOLD` rows are not execution permission. If there are no approved executable Battle Units, return `NO_APPROVED_BATTLE_PLAN`. Never convert or approve proposal rows.

605 `控制方式` is the physical Campaign boundary and is immutable to 6-1. Independent uses the approved Intent Code, Shared omits it, No-invest produces no Desired entity. Every Desired Target carries the exact 605 `Battle Unit ID`; no data source may add to the Approved Target Set.

### Current Target Value boundary

The current 6-0-5 battle-unit schemas are keyword-centric and do not define dedicated Product Target ASIN or Category Target value columns; its generator also rejects those inputs when it cannot trace a value. 6-1 must not reinterpret the keyword `词` as a Product Target or Category Target. If a future approved 605 bundle explicitly carries those target facts, 6-1 may map them through the documented role table; otherwise return `TECHNICAL_EXECUTION_CONFLICT` and ask for 605 contract completion.

The row-level 605 approval is not authorization to write to Amazon. 6-1 must query Actual State, produce a complete diff and obtain user approval for the exact CREATE/UPDATE fields before applying.
