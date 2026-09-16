# 6-4 Execution Contract

## Campaign Scope gate

The runtime ProductCode and opaque CampaignTag define the exact prefix `ProductCode.CampaignTag.`. Resolve only the latest valid 6-3 package carrying the same ProductCode, CampaignTag and CampaignPrefix. For every write, query live identity before prepare and again before apply. A Campaign must match the exact prefix. A Target must resolve through Live Target → Ad Group → Campaign and that Campaign must match the prefix. If a new Campaign is part of an approved structural operation, its proposed name must also match the prefix. Any failure is `OUTSIDE_CAMPAIGN_SCOPE` or `RUNTIME_SCOPE_MISMATCH`; no out-of-scope prepare/apply is allowed.

## Campaign Scope gate

The runtime ProductCode and opaque CampaignTag define the exact prefix `ProductCode.CampaignTag.`. Resolve only the latest valid 6-3 package carrying the same ProductCode, CampaignTag and CampaignPrefix. For every write, query live identity before prepare and again before apply. A Campaign must match the exact prefix. A Target must resolve through Live Target → Ad Group → Campaign and that Campaign must match the prefix. If a new Campaign is part of an approved structural operation, its proposed name must also match the prefix. Any failure is `OUTSIDE_CAMPAIGN_SCOPE` or `RUNTIME_SCOPE_MISMATCH`; no out-of-scope prepare/apply is allowed.

## 6-3 source and approval

The only business-decision source is the latest complete 6-3 package for the current Product Root/Product_Code. Resolve all four `scripts/ad_decision_package.py::SCHEMAS` tables as one `RUN_ID`, through `scripts/stage6_artifact_contract.py::resolve_latest_valid_bundle`. Validate each CSV sidecar and the package `6-3_RunPackage_YYYYMMDD_HHMMSS.json`; require the expected skill ID, package identity, `FULL_SUCCESS`, product code, run ID/timestamp, record counts and output assets. Never parse 6-3 HTML.

Only `确认状态=已批准` and an actionable result enters execution preflight. Non-action and unapproved rows are zero-write. 6-3 packages are immutable; approval must be joined through an authorized persistent approval record and must never be written into a copied CSV or inferred from chat. Current repository gap: 6-3 candidates start `待确认` and no approval-overlay resolver exists, so the normal output is zero-write until that handoff is implemented. Prior successful execution results for the same `6-3 RUN_ID + 执行ID` are terminal `已执行过`; use the same stable API `idempotencyKey` on retries.

## Expected/Actual/Target checks

Resolve identity first, query Actual State in the one authorized Store/Marketplace, and match entities by stable Amazon IDs through the shared identity resolver and 6-1 identity manifest. Campaign names are labels, never master identity.

Compare each action's exact Expected Current fields from its approved 6-3 row with the fresh live values. Any unequal value is `64_STATE_CONFLICT`; absent values are `64_EXPECTED_VALUE_MISSING`; absent target values are `64_PROPOSED_VALUE_MISSING`. Submit only the intended field(s), never a whole object. Use `discover_capabilities`/`discover_fields` before each live action type if exact entity, field, scale, or payload semantics are not already confirmed for the current connection.

The SellerSpace MCP write sequence is `prepare_change_plan → show exact preview → explicit user confirmation → apply_change_plan(planId,idempotencyKey) → query/read-back`. Do not call Apply before explicit confirmation of the exact preview. Compare preview action, identities, field/value, scope, and matched count to the approved 6-3 action; differences stop with `64_TECHNICAL_EXECUTION_CONFLICT`.

## Decision-to-action mapping

| 6-3 layer/result | Execution mapping | Required approved data |
|---|---|---|
| Campaign `增加预算` / `降低预算` | Campaign daily-budget update | `当前Budget`, `建议Budget`, Campaign ID |
| Campaign `调整位置` | Campaign placement update | `当前Placement`, `建议Placement`, AdType, Campaign ID |
| Target `提高竞价` / `降低竞价` | Target bid update | `当前Bid`, `建议Bid`, Target ID |
| Campaign/Target `暂停候选` | Pause status update | Exact approved object, expected status, matching live status |
| Search Term `否定候选` | Create a negative keyword/target | Source Campaign/AdGroup still exists, explicit negative level, explicit negative match type, duplicate check |
| Search Term `收割候选` | Create the destination keyword Target | Destination Intent/control mode, exact match type, target, Bid and Campaign/AdGroup identity |
| Intent `升级独立` / `降级共享`, Target `迁移候选` | Structural migration | Exact destination identity/settings and explicit approved handling for the old Target |
| `保持`, `继续观察`, `保持观察`, no-op | No write | None |

Unsupported or underspecified actions remain visible in the execution and, for structural work, migration result packages; they are never completed by inference. In the current 6-3 CSV contract, Pause lacks Expected Status; Negative does not carry negative scope/match type; Harvest lacks full destination configuration; structural migration does not explicitly choose old-Target handling. Return the relevant stable error and request a complete 6-3 handoff before execution. The resolver returns `LATEST_VALID_RUN_BUNDLE_RESOLVED`; any other result blocks the run. A run with unresolved action/migration rows cannot be written as `FULL_SUCCESS`.

## Migration and partial failure

Both directions and Harvest migration use:

1. Preflight the approved source and complete destination, all identities, capability, target values and exact naming via the shared naming formatter/parser.
2. Create the new Campaign/Ad Group/Product Ad/Target in dependency order.
3. Read back each new Amazon ID and exact parent, identity, status and parameters.
4. Only when all destination checks pass may the explicitly approved old-object handling be prepared.
5. Read back old state. Keep the old entity if create/verification fails.

Never invent a destination campaign or old-target disposition. Never delete/archive. An explicit old-object action must have its own approval and Expected Current check.

## Execution plan and idempotency

Stable `执行ID` is a SHA-256-derived key over current Product_Code, 6-3 RUN_ID, layer, stable object IDs, action, expected fields and target fields. Stable API keys use that action identity. Before each action, consult complete prior 6-4 result packages; prior success or no-op prevents duplicate writes. After an uncertain API response, query live state first; do not blindly retry.

Order dependencies: destination create → destination read-back → ordinary parameter changes → read-back → migration validation → old-target handling → final read-back. Execute per Store/Marketplace; do not cross-store batch.

## Output schemas

### `广告优化执行结果.csv`

Fixed columns:

`执行ID｜6-3决策RunID｜对象类型｜对象ID｜对象名称｜IntentCode｜BattleUnitId｜决策结果｜确认状态｜执行前预期值｜执行时实际值｜目标值｜执行动作｜执行结果｜AmazonId｜失败/冲突原因｜执行时间｜ReadBack结果`

`执行结果`: `执行成功｜无需执行｜状态冲突｜执行失败｜等待人工｜已执行过`.

### `广告结构迁移结果.csv`

Fixed columns:

`MigrationId｜6-3决策RunID｜IntentCode｜迁移类型｜旧CampaignId｜旧CampaignName｜新CampaignId｜新CampaignName｜新结构创建结果｜新Target创建结果｜新结构ReadBack｜旧Target处理动作｜旧Target处理结果｜迁移状态｜失败/冲突原因｜执行时间`

`迁移类型`: `共享转独立｜独立转共享｜收割迁移｜其他正式支持类型`.

## HTML and lineage

HTML is generated from same-run output CSVs, never re-evaluates business performance. It shows approved actions and outcomes, before/actual/target values, status conflicts, migration stages, read-back, failures, and no-approved-action/zero-write runs. Metadata lineage records Product identity, 6-3 RUN_ID and four input filenames, approved/actionable count, 6-4 RUN_ID, Actual query time, execution start/end, success/no-action/conflict/failure/migration/read-back-failure counts, and provider.

Run folder: `[Product Root]/06_SKILL分析报告/6-4_广告优化动作执行/YYYYMMDD_HHMMSS/`; all outputs share one RUN_ID/RUN_TIMESTAMP, are immutable, and are not 0-2 formal report index inputs.
