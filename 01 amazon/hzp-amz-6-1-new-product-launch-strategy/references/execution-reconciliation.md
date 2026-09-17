# 6-1 BUILD / RECONCILE Contract

## Authority and exact input

6-1 is the apply executor, not a second planning model. Resolve the latest valid approved 6-0-5 bundle using `resolve_latest_approved_battle_plan`. It contains A `新品意图市场作战表.csv`, B `新品关键词作战明细.csv`, C `新品关键词阶段规划表.csv`, and formal HTML, all for the same Product and `RUN_ID`. The resolver checks bundle lineage, schema, approval, and target coverage. Consume only APPROVED Battle Units in the currently allowed execution phase (`PHASE_1`) with control mode `独立` or `共享`. No-invest, HOLD, proposal, later-phase or unapproved rows produce no Target. Do not bypass missing approval.

## Business-to-technical translation

Map only the approved pair. Do not alter the business task or add targets:

| 605 task / method | Technical Role / Target Type |
|---|---|
| 首攻/核心 + EXACT | COR / EXA |
| 扩展 + PHRASE | EXP / PHR |
| 探索 + BROAD | DIS / BRO |
| 探索 + AUTO | DIS / AUT |
| approved competitor ASIN target | COM / ASI |
| approved Product Target (PT) | DIS / PT |
| approved Category Target | CAT / CAT |

No unique translation is `ROLE_TRANSLATION_AMBIGUOUS`. 6-0-5’s current B contract is keyword-centric and does not carry dedicated Product Target/Category Target values. Unless an approved 605 input explicitly supplies exact Target Value, fail `TECHNICAL_EXECUTION_CONFLICT`; never use a Benchmark ASIN, Own ASIN or keyword text as a substitute target. Current 6-1 execution remains SP-only unless the exact create/update workflow has been validated for another AdType. The naming parser accepts SP/SB/SD, which does not authorize SB/SD execution.

## Desired Advertising State

`scripts/advertising_state_reconciler.py::build_desired_state_from_605` is pure: it accepts a resolved 605 bundle, verified current Product/Variant identity, current evidence-derived execution parameters, and current Actual entities. It returns serializable Campaign, Ad Group, Advertised Product and Target rows. It performs no SellerSpace/Amazon I/O and does not invent Bid, Budget, Placement, Bidding Strategy, target values or statuses.

Required entity fields:

| Entity | Required Desired fields |
|---|---|
| Campaign | Logical ID, Product/Variant, AdType, ControlMode, Intent Code when independent, Role, Target Type, Name, Budget, Placement, Bidding Strategy, Status, Own ASIN/SKU identity |
| Ad Group | Logical ID, parent Campaign Logical ID, Name, Default Bid and Status |
| Advertised Product | Logical ID, parent Ad Group Logical ID, Own advertised Child ASIN, eligible SKU, Status |
| Target | Logical ID, parent Ad Group Logical ID, 605 Battle Unit ID, Target Value/Type, Match Type, Bid and Status |

Execution settings must be evidence-backed and cover every approved Battle Unit. Campaign-level budget, placement and strategy, and Ad Group-level default bid/status must agree across every unit assigned to one physical Campaign/Ad Group. Any incompatible shared assignment is `SHARED_GROUP_INCOMPATIBLE`; 6-1 returns it upstream instead of silently regrouping. Target-level bids may vary.

Only a verified current Own Product identity can populate Advertised Product. Resolve Product Code + Variant Code + exact Own ASIN + eligible advertised SKU(s); exclude Benchmark ASINs. Store and Marketplace must be present. Own/Benchmark/Product Target ASIN are separate typed values.

## Control-aware grouping and Campaign Name

Runtime Campaign Scope is mandatory and is configured in the current Product Root's `04_产品推广思路.md`: `ProductCode=B2`, `CampaignTag=M`, `CampaignPrefix=B2.M.`. Rebuild and validate the prefix with `build_campaign_scope`; missing or conflicting values fail closed. The prefix is the only scope boundary for 6-1: retain only Campaign names that strictly `STARTS_WITH CampaignPrefix`; exclude all other ads from counts, matching, BUILD/RECONCILE, Desired State and writes. No in-scope Campaign means `BUILD`; one or more in-scope Campaigns means `RECONCILE`, regardless of other account ads. CampaignTag is an opaque identifier, not a Variant; verified real Variant remains a separate identity field. The Campaign naming contract is `{ProductCode}.{CampaignTag}.{AdType}-{Role}-{TargetType}-[IntentCode]-{Seq}`. Independent requires exactly its 605 Intent Code; Shared has no Intent Code; No-invest creates no Campaign. Campaign Name and run metadata must carry the exact scope.

Independent grouping uses Product + Variant + AdType + ControlMode + Intent Code + Role + Target Type/Match + approved logical group + compatible phase. One Intent is a control boundary, not necessarily one keyword/one Campaign: compatible approved Targets under the same Intent are grouped.

Shared grouping uses Product + Variant + AdType + ControlMode + Role + Target Type/Match + compatible phase + explicit logical group, with no Intent Code in Campaign identity/name. Merge only if campaign/Ad Group execution settings are compatible. Do not merge incompatible role, AdType, Variant, Target Type, phase or placement/budget strategy.

Use `scripts/resolve_amazon_ad_identity.py` for formatting/parsing. Preserve a verified live Campaign name for an existing Logical ID; never rename an existing Campaign because a naming rule or run timestamp changed. New Campaign sequence is two digits (`01`, `02`, …) and is independent of input file timestamp.

## Stable Logical IDs and sequence manifest

Logical IDs exclude mutable bid, budget, placement and status values:

- Campaign: Product + Variant + approved ControlMode + independent Intent Code if applicable + AdType + Role + Target Type/Match + approved logical group.
- Ad Group: Campaign Logical ID + approved grouping key.
- Target: Battle Unit ID + physical Campaign control-boundary Logical ID. This lets a moved Target be CREATEd in its new boundary while the old Target remains a migration candidate.
- Advertised Product: Ad Group Logical ID + verified Own Child ASIN + eligible SKU.

Use `[Product Root]/06_SKILL分析报告/广告表现汇报优化日志/6-1_广告实体身份清单.jsonl` as the append-only registry/audit. `execution_manifest_path` returns this path. Before a provider write, load sequence reservations and append any new `CAMPAIGN_SEQUENCE_RESERVED` records with `reserve_campaign_sequences`. Once read-back succeeds, append `ENTITY_IDENTITY_VERIFIED` records with `append_verified_entities`. Target identity events preserve approved BattleUnitId/IntentCode/ControlMode/TargetType and target facts; Campaign events also preserve real Product/Variant identity plus opaque CampaignTag/CampaignPrefix, Ad Type, role, target type and control mode. These fields support exact downstream attribution without treating CampaignTag as Variant. Resolve Actual Amazon IDs using `resolve_actual_logical_identities`; Campaign Name is descriptive only. Unknown, duplicate or conflicting IDs fail closed. Do not overwrite manifest history.

For a repeated Logical Campaign ID, retain the recorded sequence. A second physical Campaign receives the next unused sequence only when a distinct approved logical group actually requires it. Run timestamp, filename and report generation order never change sequence. Do not use fuzzy name matching to avoid an identity conflict.

## Live Actual State and API capability

Before every BUILD or RECONCILE, require ProductCode/CampaignTag and derive the trailing-dot prefix. Discover current SellerSpace capability/field meanings and query actual one Store/Marketplace at a time. Query Campaigns, Ad Groups, Advertised Products, Keywords/Targets, Status, Bid, Budget, Placement, Bidding Strategy and Amazon IDs using supported filters/select fields; retain only Campaign names beginning with the exact prefix before reconciliation. Never infer the Tag's business meaning. A local export or historical report is not current Actual State. If no Campaign matches, stop with `NO_CAMPAIGN_MATCHED` for reconciliation (an approved initial BUILD may have no prior match); any proposed CREATE outside the prefix is rejected as `OUTSIDE_CAMPAIGN_SCOPE`.

SellerSpace capability discovery lists `campaign.create`, `keywords.create`, `targets.create` and update workflows. The nested fields supported by a specific write are not assumed from tool names: inspect the current capability, prepare preview and exact diff. Create Campaign → Ad Group → Product Ad/Target with the supported provider payload; do not claim an object exists until Read-back returns its stable Amazon ID.

## Diff and migration safety

`build_diff` compares canonical desired/live entities by resolved Logical ID, parent and immutable identity fields:

- `CREATE`: desired ID has no Actual counterpart.
- `UPDATE`: same logical identity but an explicitly whitelisted field differs.
- `NO_CHANGE`: all requested allowed fields match; issue no write.
- `PAUSE_CANDIDATE`: Actual entity is not in Desired; report only.
- `MIGRATION_CANDIDATE`: same 605 Battle Unit exists under an old Campaign boundary and a new Desired target is created elsewhere; report both IDs and preserve old target pending the approved migration flow.

Shared↔Independent and Independent→Shared/No-invest changes never delete/replace history in place. A transition creates the newly approved target under its new boundary; any old Target becomes MIGRATION_CANDIDATE or PAUSE_CANDIDATE. Campaign/Ad Group not in the new Desired State remain pause candidates. No automatic Pause, Archive, Delete or Rename.

UPDATE allowlist: Campaign `name/daily_budget/placement/bidding_strategy/status`; Ad Group `name/default_bid/status`; Advertised Product `status`; Target `bid/status`. Send PATCH-only fields present in Desired. Omitted Desired fields keep Actual values. Immutable identity/parent changes are conflicts, not updates.

## BUILD / RECONCILE, idempotency, approval

1. **Preflight:** resolve approved 605; verify Product/Variant/Own ASIN/SKU/Store/Marketplace/Portfolio; check page/economics/inventory/eligibility gates, role translation, target facts, parameters, sequence reservations, Logical ID uniqueness and provider write/read-back capability.
2. **Build:** use only approved units to serialize Desired State. No Actual Campaigns means `BUILD`; otherwise `RECONCILE`.
3. **Diff:** query fresh Actual and produce a complete entity-level Desired-vs-Actual diff. `NO_CHANGE` results are never written. Show independent/shared counts and migration/pause candidates.
4. **Exact approval:** user approval applies only to the displayed CREATE/UPDATE fields. Any identity, Campaign/Ad Group/Target, Portfolio, bid, budget, placement, strategy, status or action change requires renewed approval.
5. **Prepare / Apply:** `prepare_change_plan` previews the exact approved batch. Compare action, object, parent, target, field, before/desired and scope. Difference is `TECHNICAL_EXECUTION_CONFLICT`; do not Apply. After exact match, call `apply_change_plan` with stable idempotency key.
6. **Idempotency:** derive key from Product Code + 605 RUN_ID + canonical Desired State digest (not wall clock or filename). Same 605 run and same Actual state must yield zero CREATE and UPDATE on re-run.
7. **Read-back:** query each created/updated Amazon ID. Verify ID, name, parent Campaign/Ad Group, Own ASIN/SKU, Target value/type/match, status, Bid, Budget, Placement and strategy as applicable. Any missing/mismatch is `READBACK_FAILED`, not success.
8. **Recovery:** on timeout/partial result, do not replay. Re-query Actual and compute a recovery diff only for unmet entities. Report recovery scope for user review.

## Output and error statuses

Keep formal 6-1 HTML and 0-2 indexing unchanged. HTML/Diff CSV carry Product identity, exact A/B/C input names and 605 RUN_ID, approved Battle Unit IDs, 6-1 RUN_ID/time, BUILD/RECONCILE, Actual query time, entity/action counts, prepare/apply/read-back outcome, provider and unresolved issues. Run logs and append-only identity manifest stay out of formal 0-2 indexing.

Do not report `FULL_SUCCESS` after core 605 lineage, identity, actual query, apply or read-back failure. Return at least: `61_INPUT_NOT_FOUND`, `61_INPUT_RUN_MISMATCH`, `61_INPUT_SCHEMA_INVALID`, `NO_APPROVED_BATTLE_PLAN`, `INVALID_APPROVAL_STATE`, `CONTROL_MODE_MISSING`, `INTENT_CODE_MISSING`, `BATTLE_UNIT_ID_MISSING`, `ROLE_TRANSLATION_AMBIGUOUS`, `SHARED_GROUP_INCOMPATIBLE`, `CAMPAIGN_IDENTITY_CONFLICT`, `ADGROUP_IDENTITY_CONFLICT`, `TARGET_IDENTITY_CONFLICT`, `DESIRED_STATE_INVALID`, `ACTUAL_STATE_QUERY_FAILED`, `CREATE_FAILED`, `UPDATE_FAILED`, `READBACK_FAILED`, `TECHNICAL_EXECUTION_CONFLICT`, `EXECUTION_NOT_READY`, `MIGRATION_REQUIRES_APPROVAL`.

All tests use synthetic approved plans and Mock Providers only. Never connect regression tests to a real SellerSpace/Amazon account or write capability.
