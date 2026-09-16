---
name: hzp-amz-6-3-advertising-diagnosis-optimization
description: Read the latest complete 6-2 advertising facts package together with the approved 6-0-5 plan and 6-0-3 intent assets, then make evidence-gated decisions for Intent, Campaign, Target, and Search Term objects. Produces a traceable decision package for human approval and 6-4 execution; never writes Amazon Ads.
metadata:
  short-description: 基于广告事实与作战计划形成可追溯经营决策
---

# HZP Amazon 6-3｜广告诊断优化

## Role

6-3 is the Stage 6 **DECIDE** layer. The operating chain is `6-0-5 PLAN → human approval → 6-1 initial BUILD → 6-2 DATA → 6-3 DECIDE → human approval → 6-4 APPLY → next 6-2`. Keep the existing Skill ID and directory. The repository currently has no separately declared formal English display name; do not invent or rename one.

6-3 reads a frozen advertising-facts Run Package and its original approved battle purpose, judges what should happen next, and creates decision artifacts for review and handoff. It does not refresh advertising facts, re-plan the market, or change Amazon Ads. Even when a decision is approved, only 6-4 applies daily operating actions through its own approved-state reconciliation and read-back contract.

## Resolve inputs

Require the runtime inputs `ProductCode` and opaque `CampaignTag`. Call `resolve_decision_inputs(product_root, product_code, campaign_tag)`; it derives the trailing-dot prefix and selects only the latest valid 6-2 Run Package matching ProductCode + CampaignTag + CampaignPrefix. 6-3 never rescans Amazon Campaigns. Campaign rows must have an in-scope CampaignName; Target/SearchTerm rows must join to an in-scope CampaignId; Intent rows are retained only if represented by scoped Targets. Contaminated rows are excluded and mark the run `SCOPE_CONTAMINATION` / `PARTIAL_SUCCESS`; scope mismatch blocks with `RUNTIME_SCOPE_MISMATCH`. Excluded Campaign metrics must never enter the AI context or outputs. Decision Run Metadata carries ProductCode, CampaignTag, CampaignPrefix and Source 6-2 Run ID. Decision history is resolved only within the same CampaignTag.

Use the current Product Root resolved under the 0-1 product-directory rules. Do not search other products or infer product identity from ASIN, Campaign Name, or file names.

1. **Required performance truth:** call `scripts/ad_facts_package.py:resolve_latest_valid_62_package(product_root, product_code, campaign_tag)` once. Require `LATEST_VALID_62_PACKAGE_RESOLVED`; consume all four CSV tables and metadata returned from that one ProductCode + CampaignTag package: Campaign, Intent, Target, and Search Term. Do not query SellerSpace/Amazon or assemble a package from separate latest files. The 6-2 package is the only performance fact source for this run.
2. **Required original purpose:** call `scripts/new_product_battle_plan_contract.py:resolve_latest_approved_battle_plan(...)`. Read the same-run `新品意图市场作战表.csv`, `新品关键词阶段规划表.csv`, and `新品关键词作战明细.csv` rows returned by the resolver. They ground task, phase, placement method, control mode, IntentCode, BattleUnitId, and purpose. HTML is never ground truth. An absent, invalid, unapproved, or mixed-run plan blocks decisions that depend on that purpose; return the applicable `605_*`/`63_INPUT_*` error instead of guessing.
3. **Supporting market context:** use `scripts/new_product_battle_plan_contract.py:resolve_603_bundle(...)` for the current product's same-run `精准泛词汇总.csv` and `词对应的精准泛词.csv`. If unavailable or invalid, continue only where the missing market context does not make the decision unreliable, disclose it as unavailable, and lower readiness as needed.
4. **Optional Benchmark reality:** use `hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis/scripts/benchmark_intent_occupancy.py:resolve_inputs(...)` when a valid 606 report exists. If absent, record `606_EVIDENCE_NOT_AVAILABLE`; never fabricate it.
5. Load prior 6-3 decision packages through the local Decision History helper when available. Missing history is `DECISION_HISTORY_UNAVAILABLE`, not a reason to invent earlier actions.

All inputs must resolve to the same current Product Root and Product_Code. Validate required CSV headers, package identity, status, lineage, and same-Run relationships before judgment. CSV/structured assets are ground truth; HTML is only a rendered view. A missing optional 606 is not a run failure. Insufficient evidence for an object normally yields `继续观察`, not a whole-run failure.

## Build decision context, then judge

The helper `scripts/ad_decision_package.py:build_decision_context(...)` prepares deduplicated objects, factual current values, and dated 3/7/14/30-day aggregates from the resolved 6-2 rows. It sums additive facts and recomputes ratios from their numerators and denominators. It does not fill missing dates, infer zeros, or treat `SOURCE_WINDOW` aggregates as dated daily facts. Placement, creation, modification, attribution, and economic-boundary values absent from the 6-2 package stay unavailable; do not infer them. Identify those source gaps in the run.

Evaluate the four business layers: **Intent, Campaign, Target, and Search Term**. Search Term grain is one SearchTerm × Source Target (TargetId) as supplied by 6-2. Ad Group is a technical container unless an existing source explicitly defines a business control at that level.

For every evaluated object, make an AI judgment for all five fields: `决策成熟度`, `决策结果`, `决策原因`, `下一观察条件`, `确认状态`. No evaluated object may be silently omitted, left blank, or described as “no handling.” Use the decision-readiness guidance in [references/decision-readiness-kernel.md](references/decision-readiness-kernel.md). Assess evidence per candidate action, not with a shared day/click threshold. State the actual evidence window(s) in `决策原因` because the fixed CSV contracts have no separate window column.

Use the exact Chinese enums in [references/decision-data-contract.md](references/decision-data-contract.md). A reason must name the evidence that drove the decision. “不动” still requires a reason. Every decision needs a concrete next observation condition; do not default to “wait 7 days.” Current and proposed values are both required when changing a numeric setting. 6-3 does not approve its own execution decisions: all candidate execution changes start `待确认`.

The AI chooses decisions and explains them; code validates schemas, coverage, completeness, cross-layer consistency, values, timestamps, and lineage. Do not use a fixed score or a mechanical ACoS/click/day rule as a substitute for judgment. Do not let market capacity, 603 opportunity ratio, or 606 occupancy replace advertising performance evidence; they are strategy context. Never present organic occupancy as sales share.

## Decision results and safeguards

Allowed maturity values are `可决策`, `继续观察`, `紧急处理`. Allowed result values are layer-specific and fixed in the data contract. `可决策 + 保持` means evidence is sufficient and no change is chosen; `继续观察 + 继续观察/保持观察` means the evidence is not mature enough. These states are not interchangeable.

For Intent/Campaign/Target structural recommendations, check the desired state across layers. An Intent `升级独立` or `降级共享` must agree with its associated Campaign/Target destination. Conflicting outcomes for the same object or inconsistent destinations return `DECISION_CONFLICT`; they must not be marked approved. Candidate Search Term collection/harvesting is not an automatic Exact creation, and `否定候选` is not an automatic negative.

6-3 performs no Amazon Ads writes, no SellerSpace write calls, and never calls `apply_change_plan`. It does not approve a candidate, prepare an Amazon write plan, mutate listings, or claim an action was applied. Human-approved daily operating decisions are handed to 6-4 for compare-and-apply execution. 6-1 is reserved for initial 6-0-5 architecture BUILD and does not consume these daily decisions. 6-4 may stop for identity, permission, feasibility, missing action detail, or `TECHNICAL_EXECUTION_CONFLICT`; it must not re-decide the business merits or amount.

## Outputs

Call `scripts/ad_decision_package.py:write_decision_package(...)` only after all four decision tables pass validation and coverage. The helper writes one immutable package under:

`[Product Root]/06_SKILL分析报告/6-3_广告诊断优化/YYYYMMDD_HHMMSS/`

One run contains the four exact-schema CSVs and `6-3_广告优化决策报告_[YYYYMMDD_HHMMSS].html`, plus one shared `6-3_RunPackage_[YYYYMMDD_HHMMSS].json` and artifact sidecars. All use one `RUN_ID` / `RUN_TIMESTAMP`; CSVs use UTF-8 with BOM. Existing runs are never overwritten and this operational package is not a versioned formal report or 0-2 index target.

The HTML is rendered only from the four CSV decision tables and same-run lineage. It must show: summary; Intent, Campaign, Target, Search Term decisions; observation queue and why no action is taken; urgent handling; evidence windows, 605 purpose, 603 context and optional 606 evidence; pending decisions for 6-4; data gaps and limitations. Do not introduce a second set of decisions in HTML.

Decision history is append-only across Run Packages. Show prior decisions for a stable object identity when history exists, preserving the chain from observe/no-change to later adjustment and why. If history is missing, say so. The handoff to 6-4 contains only validated decision rows and lineage, never an executed-state claim.

## Validation and errors

Run synthetic tests in `tests/` and `skill-creator` quick validation. Hard input/lineage/schema errors block the package. Applicable stable errors include `63_INPUT_NOT_FOUND`, `63_INPUT_RUN_MISMATCH`, `63_INPUT_SCHEMA_INVALID`, `63_DATA_INSUFFICIENT`, `DECISION_REASON_MISSING`, `OBSERVATION_CONDITION_MISSING`, `DECISION_MATURITY_MISSING`, `DECISION_CONFLICT`, `PROPOSED_VALUE_MISSING`, `ECONOMIC_BOUNDARY_UNAVAILABLE`, `606_EVIDENCE_NOT_AVAILABLE`, `DECISION_HISTORY_UNAVAILABLE`, and `EXECUTION_HANDOFF_INVALID`.

See [decision-data-contract.md](references/decision-data-contract.md) for exact schemas, [decision-readiness-kernel.md](references/decision-readiness-kernel.md) for action-specific evidence judgment, [handoff-schema.md](references/handoff-schema.md) for 6-4 handoff, and [report-outline.md](templates/report-outline.md) for the rendered dashboard.


## 全局正式报告目录与命名规则

本 Skill 面向确定 Product Root 生成正式报告或结构化分析报告时，统一保存到 `06_SKILL分析报告/{Skill编号}_{Skill中文正式名称}/`，文件名使用 `{Skill编号}_{报告名称}_{YYYYMMDD_HHMMSS}.{ext}`；同一运行的配套正式资产共用时间戳。6-0-1、6-0-2、6-0-3、6-0-5、6-0-6 的报告资产直接放固定 Skill 目录，不建时间戳子目录；6-2、6-3、6-4 可按每次运行建立 `YYYYMMDD_HHMMSS/` 子目录，子目录中的文件仍须带 Skill 编号前缀和时间戳。读取最新报告或运行包时按文件名/包内时间及有效性校验，不按文件修改时间选择。HTML 必须使用同批 CSV 回读快照渲染。历史报告不自动迁移或删除。跨产品公共知识、提醒状态、决策登记簿和运行日志等持续业务数据按各自数据契约保存，不作为 Product Root 正式分析报告迁移。
