# 6-1 Approved Battle Plan Input Contract

6-1 is the sole strategic source for 6-2. Resolve with `scripts/new_product_battle_plan_contract.py::resolve_latest_approved_battle_plan(product_root, product_code)`. Never select the newest file by timestamp alone; require the resolver’s CURRENT PRODUCT → VALID → LATEST APPROVED same-run bundle.

| Role | Formal filename stem | Required lineage |
|---|---|---|
| A | `新品意图市场作战表` | Intent Code, intent/control decisions, approval state |
| B | `新品关键词作战明细` | Battle Unit ID, Intent Code, task, control mode, targets and approval |
| C | `新品关键词阶段规划表` | Keyword lifecycle, phase, execution method and approval |
| D | `广告创建参数表` | Complete Campaign/Ad Group/Target creation parameters, one row per approved target |

All three CSVs and the formal 6-1 HTML must match Product Code and `RUN_ID`. The resolver validates schema, lineage, coverage and approval contract. Current execution phase is `PHASE_1`; other phases are not executable until the upstream contract explicitly changes.

6-2 consumes only B rows whose `确认状态=APPROVED`, phase is currently allowed, and `控制方式` is not `不投`, together with matching D rows. A/C/B/D `PROPOSED` or `HOLD` rows are not execution permission. If there are no approved executable Battle Units, return `NO_APPROVED_BATTLE_PLAN`. Missing or mismatched non-keyword target facts stop execution. Never convert or approve proposal rows.

6-1 `控制方式` is the physical Campaign boundary and is immutable to 6-2. Independent uses the approved Intent Code, Shared omits it, No-invest produces no Desired entity. Every Desired Target carries the exact 6-1 `Battle Unit ID`; no data source may add to the Approved Target Set. D is mandatory: 6-2 must consume its Campaign, Ad Group, bid, budget, placement, strategy, Portfolio, Own ASIN/SKU, Marketplace, Store, status and negative-target fields verbatim. `DATA_NOT_AVAILABLE` or `EXECUTION_NOT_READY` is a hard stop; 6-2 may not calculate or fill a missing value.

### Current Target Value contract

The 6-1 B Battle Unit schema carries `目标类型` and `目标值` immediately after `投放方式`. Keyword methods carry `KEYWORD` plus the exact keyword; `ASIN` carries the approved competitor ASIN; `PT`/`PRODUCT` carries the approved Product Target value; and `CATEGORY` carries the approved category value. 6-2 maps these exact approved facts and never substitutes a Benchmark ASIN, Own ASIN, or keyword text for a non-keyword target. Missing or mismatched target facts return `TECHNICAL_EXECUTION_CONFLICT`.

The row-level 6-1 approval is not authorization to write to Amazon. 6-2 must query Actual State, produce a complete diff and obtain user approval for the exact CREATE/UPDATE fields before applying.
