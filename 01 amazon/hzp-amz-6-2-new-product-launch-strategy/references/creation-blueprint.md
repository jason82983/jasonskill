# Desired Advertising State Blueprint｜广告状态执行蓝图

本文件中的旧“Launch/创建蓝图”字段仅作为执行参数的展示参考，不授权 6-2 重新规划产品战略、Launch Goal、Intent、Target 或预算策略。当前正式执行以最新有效且已批准的 6-1 作战表为准；6-2 生成 Desired State，与 Live Actual State 对账后展示精确差异。

## 两层视图

LEVEL 1 Execution Summary 让用户快速看到 6-1 RUN_ID、BUILD/RECONCILE、资格状态和 CREATE/UPDATE/NO_CHANGE/PAUSE_CANDIDATE 数量；LEVEL 2 Detailed Desired-vs-Actual Diff 保留可逐项审计、可映射到 Amazon Ads 的完整执行参数。批准仅针对已展示的具体 CREATE/UPDATE 差异。

## LEVEL 1 必备字段

执行摘要必须显示 Product Code、CampaignTag、CampaignPrefix、Product Name、Marketplace、Store、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、6-1 RUN_ID、Approved Battle Unit Count、BUILD/RECONCILE、执行资格状态、各差异动作数和错误数。CampaignTag是运行时筛选Tag；真实Variant从产品身份映射单独显示。Launch Goal、Intent、释放阶段及总预算从6-1透传，不由6-2重算。

Campaign Desired/Actual 对账至少显示 Campaign Name、Logical ID、Amazon Campaign ID、Role、Targeting、Daily Budget、Base Bid/Bid Range、Bidding Strategy、Placement、动作和逐字段差异。预算与目标集合以6-1批准范围为准。

对于 `COR-EXA` 且 `CORE_HIGH_CONFIDENCE_EXACT` 的新品核心精准 Campaign，Campaign 总览和明细额外显示 `Base Bid`、`Top Adjustment`（默认参考 +50%）、`Top Placement Adjusted Bid`、`Rest of Search`、`Product Pages`、`Bidding Strategy`、`Potential Maximum Effective Bid`、`Dynamic Upward Multiplier`（如平台确认）及 `Break-even / Economic Risk`。`Base Bid` 不得使用机械 `×1.20` 默认；潜在最大有效竞价在动态上限未确认时标记 `【动态上调上限未确认】`。

## LEVEL 2 必备字段

每个 Campaign 独立展示：名称、Role、Ad Type、Status、Start/End Date、Daily Budget、Portfolio、Bidding Strategy、Top of Search、Rest of Search、Product Pages。

`EXP-PHR`、`DIS-BRO`、`DIS-AUT`、`COM-ASI` 的 Bid、Placement 和 Bidding Strategy 独立展示，不得继承 COR-EXA 的 +50% 参考。

每个 Ad Group 展示名称、Default Bid、Status；Advertised Product 展示 Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]，并固定标记 `[Advertised Product｜Own Product]`。

每个 Keyword 逐词展示 Keyword、中文含义、Source、Cluster、Role、Match Type、Target-Level Bid、H10 Suggested Bid、H10 Bid Range、Amazon/SellerSpace Suggested Bid、Own Historical CPC、Evidence、Reason。缺失显示 `[数据缺失]`，不估算 H10 原始建议竞价。

Auto 展示 Close Match、Loose Match、Substitutes、Complements；只有 SellerSpace/Amazon 支持独立 Bid 时才分别展示 Bid，否则标记 `[当前执行接口不支持]`。Product Target 逐个展示 Target ASIN、产品名、品牌、价格、Rating、Review Count（如有）、Source、Reason 和 Initial Bid，并标记 `[Product Target ASIN]`。

Own ASIN = Advertised Product；Benchmark ASIN = Market/Research Reference；Product Target ASIN = Advertising Target。禁止使用不带身份前缀的通用 ASIN 字段。

## 审批和差异校验

执行检查覆盖 Identity、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Marketplace、Store、Campaign Names/Budgets、Ad Groups、Advertised Product、已批准 Targets、Target-Level Bids、Bidding Strategies、Placements 和 6-6 Handoff。Launch/Phase 策略由6-1提供，不由6-2重新设计。关键字段缺失时标记 `EXECUTION_NOT_READY`。

旧 A/B/C/D 战略预案审批流程已由 6-1 PLAN / 6-2 APPLY 取代。6-2 展示 Desired-vs-Actual 精确差异；用户批准后才调用 prepare，Prepared Change Plan 必须与已批准动作及字段完全一致，否则停止并重新审批。

创建后用同一字段结构 Read-Back，核对 Campaign ID、名称、预算、策略、广告位、Ad Group、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Keyword/Match/Bid、Product Target、Auto、Negative 和 Status。
## Portfolio 字段（新增必填）

每个 Campaign 的 Desired/Actual/Prepared/Read-back 都展示：`Portfolio Name`、`Portfolio ID`、`Portfolio Status`、来源与读取时间。Portfolio Name 只能来自映射表 `广告组合`，Portfolio ID 只能来自当前 SellerSpace 只读解析；未验证时标记 `EXECUTION_NOT_READY`。禁止把 Portfolio 留空或用硬编码 ID 替代。

身份字段还必须记录 `Product_NewCode`、正式 `Product_Code`、Store 前缀、`Var_Code`、Advertised Child ASIN、Mapped_SKUs[]、Advertised_SKUs[]。变体映射不完整时只生成不可执行方案，禁止猜测子 ASIN、Mapped_SKUs[]/Advertised_SKUs[]；Campaign 名称使用共享 `format_campaign_name()`。

同一 `Product_Code + Var_Code + Advertised ASIN` 可对应多个 SKU。蓝图必须展示 `Mapped_SKUs[]`、`Advertised_SKUs[]` 和 `SKU_Count`，并通过实际 Ads/SellerSpace eligibility 决定 `ADD BOTH`、`ADD ELIGIBLE SKU ONLY` 或按 ASIN 去重的 `ADD ONCE`；全部不合格时标记 `ADVERTISED_PRODUCT_NOT_ELIGIBLE`。不得取 Excel 第一行 SKU、按 SKU 数量复制 Campaign，或把多个 ASIN 静默合并。

先展示《Campaign Naming Preview》：沿用共享 `format_campaign_name(..., campaign_tag=..., control_mode=..., intent_code=...)` 规则并逐字透传 6-1 控制方式。正式骨架为 `{ProductCode}.{CampaignTag}.{AdType}-{Role}-{TargetType}-[IntentCode]-{Sequence}`；独立必须带单一 Intent Code（如 `B2.M.SP-COR-EXA-SG-01`），共享不得带 Intent Code（如 `B2.M.SP-EXP-PHR-01`），不投不创建 Campaign。CampaignTag 是广告范围标识，不代表真实 Variant；真实 Variant 单独记录。Ad Group 命名保持现有规则。命名不包含日期、Bid、Budget、Coupon、Price、Placement 或策略参数。Sequence Collision Check 必须在用户批准执行差异前完成，旧 Campaign 不重命名；历史格式只作兼容解析。
