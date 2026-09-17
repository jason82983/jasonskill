---
name: hzp-amz-6-2-product-operations-monitoring
description: Collect, reconcile, attribute, and package real Amazon advertising run facts at Campaign, Intent, Target, and Search Term levels. DATA ONLY; analysis and actions belong to 6-3.
metadata:
  short-description: 生成可追溯的广告运行事实数据包
---

# HZP Amazon 6-2｜产品经营监控与诊断

## Identity and role

Keep the existing Skill ID and formal Chinese name. The new responsibility is **advertising runtime facts only**: answer “what actually happened?” 605 plans, 6-1 applies approved plans, 6-2 collects facts, 6-3 decides what they mean and what to do, and 6-1 applies approved changes. Do not rename this Skill in this change; its current name may not describe the narrowed responsibility, so report that mismatch for the owner to decide.

6-2 may query the configured current advertising provider, map confirmed provider fields, validate and aggregate facts, save four CSVs, and render a static HTML snapshot. It must not assess performance, explain causes, rank opportunities, recommend actions, or execute any ad change. Never call a write capability.

## Data contract

The machine source of truth is one complete, same-run package of four UTF-8-with-BOM CSVs: Campaign, Intent, Target, and Search Term. HTML is a human-readable snapshot rendered from those exact CSVs, not a separate data source. Use the exact schemas and grain rules in [references/advertising-facts-contract.md](references/advertising-facts-contract.md).

Before a live read, resolve Current Product identity and provider access using the repository’s existing shared identity/provider boundaries. Discover actual entity capabilities and field semantics; do not guess field aliases, units, date columns, attribution fields, or metric availability. Query only read-only advertising endpoints. Historical CSVs may be lineage evidence but cannot impersonate a fresh source snapshot.

## Runtime Campaign Scope (required)

Every run must receive `ProductCode` and opaque `CampaignTag`; call `scripts.campaign_scope_contract.build_campaign_scope()` to derive `CampaignPrefix=ProductCode.CampaignTag.`. First query the live Campaign inventory, then call `scripts.ad_facts_package.select_runtime_campaign_scope()` and filter Campaigns by `CampaignName STARTS_WITH CampaignPrefix` (the final dot is mandatory). Only after selecting matched Campaign IDs may the provider query their Ad Groups, Targets, Search Terms, and performance. Never fetch whole-account child performance and filter only afterward. Excluded Campaign metrics must not appear in CSV/HTML. Record `ProductCode`, `CampaignTag`, `CampaignPrefix`, `AccountCampaignCount`, `PrefixMatchedCampaignCount`, `ExcludedCampaignCount`, and `MatchedCampaignIds` in metadata/HTML. No matches returns `NO_CAMPAIGN_MATCHED`. The existing four CSV schemas remain unchanged.

## Attribution

Resolve facts by verified Amazon IDs and the 6-1 identity manifest, then join Target identity to its exact `BattleUnitId`, and that ID to the same approved 6-0-5 Battle Plan row for `IntentCode`, Intent term, and control mode. Search Terms join through their actual Target ID. Never infer Intent from a shared Campaign name or distribute Campaign-level metrics across Intents. Preserve unresolved facts with `IntentCode=UNMAPPED` and `INTENT_ATTRIBUTION_UNRESOLVED`; do not discard records or guess attribution. Older identity events without the added Target-to-BattleUnit fields remain unresolved.

## Time, metrics, and integrity

Prefer one row per entity per date only when the provider actually supplies day-grain records and a confirmed date field. Otherwise preserve and label source-window grain; never manufacture days. Stable cutoff defaults to yesterday. Keep any returned current-day facts explicitly marked `TODAY_PARTIAL`, separate from complete days. HTML windows are derived only from CSV data; unavailable subwindows must disclose the actual range/grain.

Programmatically calculate `CTR=Clicks/Impressions`, `CPC=Spend/Clicks`, `CVR=Orders/Clicks`, `ACoS=Spend/Sales`, and `ROAS=Sales/Spend`; zero or missing denominators yield NULL. Compare provider raw ratios with calculated values only when the repository’s configured reconciliation tolerance is known. Do not invent one. Validate nonnegative source counts/amounts, supported Clicks≤Impressions, join coverage, duplicate facts, package completeness, and HTML-to-CSV lineage. A missing attribution refresh rule must be reported as `UNRESOLVED`; accept `ATTRIBUTION_REFRESH_DAYS` only as explicit configuration.

## Outputs and latest package

Write each run to `[Product Root]/06_SKILL分析报告/6-2_产品经营监控与诊断/[YYYYMMDD_HHMMSS]/`, using the shared Stage 6 artifact contract for Run ID, timestamp, metadata, and no-overwrite behavior. The run folder contains four timestamped CSVs, `6-2_广告运行数据报告_[YYYYMMDD_HHMMSS].html`, and one package `6-2_RunPackage_[YYYYMMDD_HHMMSS].json`; the HTML also has its shared metadata sidecar. Resolve latest-valid at **package** level, and require identity, status, all four exact schemas, the HTML, sidecar Run ID/timestamp, and all named output assets to validate together. Never combine separately selected latest CSVs.

Use [references/advertising-facts-contract.md](references/advertising-facts-contract.md) for field schemas, provider mapping and Run Package behavior. Use [templates/report-outline.md](templates/report-outline.md) for the neutral HTML sections. Legacy product-diagnosis, ERP keyword analysis, period-comparison, and handoff rules are not part of this DATA ONLY workflow.

## 全局正式报告目录与命名规则

本 Skill 面向确定 Product Root 生成正式报告或结构化分析报告时，统一保存到 `06_SKILL分析报告/{Skill编号}_{Skill中文正式名称}/`，文件名使用 `{Skill编号}_{报告名称}_{YYYYMMDD_HHMMSS}.{ext}`；同一运行的配套正式资产共用时间戳。6-0-1、6-0-2、6-0-3、6-0-5、6-0-6 的报告资产直接放固定 Skill 目录，不建时间戳子目录；6-2、6-3、6-4 可按每次运行建立 `YYYYMMDD_HHMMSS/` 子目录，子目录中的文件仍须带 Skill 编号前缀和时间戳。读取最新报告或运行包时按文件名/包内时间及有效性校验，不按文件修改时间选择。若 HTML 由同批 CSV 生成，必须从文件名时间戳相同的 CSV 读取并生成不可变快照；禁止运行时另找“最新 CSV”。未由 CSV 构成输入的 HTML 报告遵循对应 Skill 的原有报告内容逻辑。此规则优先于本文档中旧的目录和文件名示例。历史报告不自动迁移或删除。跨产品公共知识、提醒状态、决策登记簿和运行日志等持续业务数据按各自数据契约保存，不作为 Product Root 正式分析报告迁移。

## Shared AI Brain

本 Skill 遵守仓库共享 AI Brain：`../references/ai-brain/README.md`。运行时按 `context-manifest.md` 声明 GLOBAL、DOMAIN、UPSTREAM、HISTORY、FORBIDDEN；本 Skill 的业务 Contract、正式 Ground Truth 和职责边界优先于泛化推理。AI Judgment 必须区分 Evidence 类型，重要判断先执行 Decision Challenge，再由 Reason Trace 生成原因；程序确定的数学、Join、去重、筛选、聚合、Schema、Identity、Timestamp、Latest 和 Read-back 不交给 AI 计算。
