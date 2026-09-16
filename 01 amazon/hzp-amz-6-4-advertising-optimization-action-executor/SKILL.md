---
name: hzp-amz-6-4-advertising-optimization-action-executor
description: Execute human-approved Amazon Ads optimization decisions from the latest complete 6-3 package. Reconcile each approved action against live state, require confirmation of the exact SellerSpace preview, apply through the shared provider, verify by read-back, and write an immutable audit package. Never re-decides advertising strategy.
metadata:
  short-description: 安全执行已批准的广告优化动作
---

# HZP Amazon 6-4｜广告优化动作执行

## Role and identity

Formal name: `6-4｜广告优化动作执行` / `Advertising Optimization Action Executor`. Skill ID and directory: `hzp-amz-6-4-advertising-optimization-action-executor`.

Stage 6 responsibilities: `6-0-5 PLAN → human approval → 6-1 BUILD → 6-2 DATA → 6-3 DECIDE → human approval → 6-4 APPLY → next 6-2`. 6-4 is the execution hand. It must never reconsider whether, why, or by how much an ad should change. It executes only the exact business decision approved in 6-3 and validates that decision against live state.

## Resolve and validate the decision package

Require ProductCode + opaque CampaignTag at runtime. Resolve the latest valid 6-3 package using all three scope metadata fields (ProductCode, CampaignTag, CampaignPrefix); any mismatch returns `RUNTIME_SCOPE_MISMATCH`. Before each prepare and again immediately before each apply, re-query Live Identity. Campaign actions require exact trailing-dot prefix membership. Target actions require a verified Live Target → Ad Group → Campaign ancestry and the Campaign name must still start with CampaignPrefix; absent or ambiguous parent links fail closed as `OUTSIDE_CAMPAIGN_SCOPE` with zero writes. Every new Campaign destination must use the same prefix. 6-4 metadata records the inherited scope.

1. Resolve Product Root and Product/Variant/Store/Marketplace using the 0-1 directory contract and shared `scripts/resolve_amazon_ad_identity.py`. Never identify a product by Campaign Name, benchmark ASIN, or a filename alone.
2. Call `scripts/action_execution.py::resolve_latest_approved_decisions(product_root, product_code, campaign_tag)` once. It uses the shared `scripts/stage6_artifact_contract.py::resolve_latest_valid_bundle` for the four 6-3 CSVs. Require one valid current-product + CampaignTag `RUN_ID`, matching manifest and CSV sidecars, exact schemas, and a complete package. CSV is ground truth; never parse 6-3 HTML as machine input.
3. Eligible decisions require `确认状态=已批准` and an actionable decision value. `待确认`, `暂缓`, `保持`, `继续观察`, `保持观察`, missing approval, and non-action decisions cause zero writes. A run with no approved actionable row is a normal `64_NO_APPROVED_ACTION` result and still writes an audit package.
4. Check prior 6-4 result packages for the same 6-3 `RUN_ID` and stable `执行ID`; successful actions become `已执行过` and are never replayed. Use an API idempotency key derived from the 6-3 Run ID and immutable action identity.

6-3 decision Run Packages are immutable. Do not edit their CSVs to record a later human approval. Use only an approval record linked to the 6-3 `RUN_ID` and exact layer/object/action; if no validated approval handoff is available and the input row itself is not authoritatively marked `已批准`, keep it out of the execution set. Never infer approval from conversational context, a report display, or a copied/edited CSV. Repository integration gap: the current 6-3 writer emits candidates as `待确认` and no shared persistent approval-overlay resolver is implemented yet; until one is connected, normal 6-3 output will yield zero writes.

## Live-state compare and approval gates

Before preparing any write, discover current SellerSpace capabilities and field semantics, verify the authorized Store/Marketplace, then read only the required live Campaign/Ad Group/Target/negative-target hierarchy and Amazon IDs. Historical 6-2 values are not execution-time Actual State. Resolve Amazon IDs through the shared identity resolver / append-only 6-1 entity identity manifest. Unknown, duplicate, cross-product, cross-variant, or conflicting identities fail closed.

For each actionable row, compare 6-3 Expected Current with live Actual Current. A mismatch yields `状态冲突`; missing expected/proposed values yield the applicable stable error and no write. Do not overwrite a human or another system's intervening change. Prepare only exact whitelisted fields; never replace a whole entity.

Approval has two checks: the 6-3 row must already be `已批准`; and SellerSpace's exact `prepare_change_plan` preview must be shown to the user and explicitly confirmed before `apply_change_plan`, following the connected MCP's approval rule. A 6-3 approval alone does not waive the prepared-preview confirmation. Prepare failures, preview differences, unclear field semantics, or unsupported capabilities stop that action.

Use one Store/Marketplace at a time. Apply the exact `planId` with a stable `idempotencyKey`, then query live state again by Amazon ID. API success is not success until `read-back` verifies the intended values, status, parentage, target, and Amazon ID. Append verified identity links only after successful read-back using the existing 6-1 registry helper; do not create a competing identity registry.

## Action support and limits

- Budget, placement, and bid updates map only from their 6-3 current and proposed fields to a single-object SellerSpace change plan. Capability discovery and the exact prepared preview determine whether the provider supports that exact change.
- Pause requires an approved pause decision plus an explicit expected live status and a live status match. The current 6-3 CSV schema does not contain expected status; until a decision handoff supplies it, return `64_EXPECTED_VALUE_MISSING` and do not pause.
- Negative creation requires an explicit approved negative scope and negative match type, source Campaign/Ad Group still present, and a live duplicate check. `否定候选` alone does not state exact-vs-phrase or Campaign-vs-AdGroup; do not infer these from ordinary target MatchType. Missing details return `64_TECHNICAL_EXECUTION_CONFLICT`.
- Harvest requires approved exact destination Intent, control mode, match type, bid, and destination identity. SearchTerm text alone is insufficient. Return `64_HARVEST_EXECUTION_INCOMPLETE` if the approved handoff lacks any required field.
- Shared↔independent and harvest migrations use `CREATE NEW → VERIFY NEW → HANDLE OLD → VERIFY OLD`. Never disable the source before the destination exists and passes read-back. Preserve prior Campaigns. Each stage requires exact approved source/destination identities and old-object handling; if the 6-3 package does not specify them, return `64_MIGRATION_FAILED` without partial teardown.
- Reuse the shared Campaign naming parser/formatter, identity resolver, Provider boundary, SellerSpace MCP, `scripts/advertising_state_reconciler.py` Provider/read-back conventions, Stage 6 artifact contract, and 6-1 append-only identity registry. Do not add another API client, naming system, identity system, or approval system.

## Execution ordering and partial failure

Build a deterministic dependency plan before writes: create destination resources; verify new resources; update ordinary settings; verify; migrate targets; verify; only then handle explicitly approved old-object state; verify. Group API plans only when the action type, store, and exact change are compatible. Never blindly execute CSV row order.

Record one result per approved/actionable candidate. Distinguish `执行成功`, `无需执行`, `状态冲突`, `执行失败`, `等待人工`, and `已执行过`. A failure is local to its action unless a shared prerequisite (identity, store, capability, or source Run ID) invalidates the remaining plan. Never report all-success after a partial failure. Do not retry an uncertain apply; query Actual State first and return a recovery diff for review.

## Output

Write one immutable package under `[Product Root]/06_SKILL分析报告/6-4_广告优化动作执行/YYYYMMDD_HHMMSS/`:

- `6-4_广告优化执行结果_[YYYYMMDD_HHMMSS].csv`
- `6-4_广告结构迁移结果_[YYYYMMDD_HHMMSS].csv`
- `6-4_广告优化执行报告_[YYYYMMDD_HHMMSS].html`
- shared `6-4_RunPackage_[YYYYMMDD_HHMMSS].json` and artifact sidecars

Use the exact CSV schemas in [references/execution-contract.md](references/execution-contract.md), UTF-8 with BOM, and one shared 6-4 `RUN_ID` / `RUN_TIMESTAMP`. HTML is an execution dashboard generated from the same-run result CSVs; it must not analyze ad performance. Include input lineage, approval counts, zero-write result when applicable, exact Before/Actual/Target, state conflicts, API results, Read-back results, migrations, failures, and unresolved gaps. Operational packages are not formal 0-2 report-index inputs.

## Stable error codes

Use at least: `64_INPUT_NOT_FOUND`, `64_INPUT_RUN_MISMATCH`, `64_INPUT_SCHEMA_INVALID`, `64_NO_APPROVED_ACTION`, `64_ACTION_MAPPING_UNSUPPORTED`, `64_ACTUAL_STATE_QUERY_FAILED`, `64_STATE_CONFLICT`, `64_EXPECTED_VALUE_MISSING`, `64_PROPOSED_VALUE_MISSING`, `64_IDENTITY_CONFLICT`, `64_CREATE_FAILED`, `64_UPDATE_FAILED`, `64_PAUSE_FAILED`, `64_NEGATIVE_FAILED`, `64_HARVEST_EXECUTION_INCOMPLETE`, `64_MIGRATION_FAILED`, `64_READBACK_FAILED`, `64_TECHNICAL_EXECUTION_CONFLICT`.

Read [execution-contract.md](references/execution-contract.md) for action mapping and Run Package schemas. Run the synthetic regression tests in `tests/`; never connect those tests to Amazon or SellerSpace.

## 全局正式报告目录与命名规则

本 Skill 面向确定 Product Root 生成正式报告或结构化分析报告时，统一保存到 `06_SKILL分析报告/{Skill编号}_{Skill中文正式名称}/`，文件名使用 `{Skill编号}_{报告名称}_{YYYYMMDD_HHMMSS}.{ext}`；同一运行的配套正式资产共用时间戳。6-0-1、6-0-2、6-0-3、6-0-5、6-0-6 的报告资产直接放固定 Skill 目录，不建时间戳子目录；6-2、6-3、6-4 可按每次运行建立 `YYYYMMDD_HHMMSS/` 子目录，子目录中的文件仍须带 Skill 编号前缀和时间戳。读取最新报告或运行包时按文件名/包内时间及有效性校验，不按文件修改时间选择。HTML 必须使用同批 CSV 回读快照渲染。历史报告不自动迁移或删除。跨产品公共知识、提醒状态、决策登记簿和运行日志等持续业务数据按各自数据契约保存，不作为 Product Root 正式分析报告迁移。
