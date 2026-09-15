# Initial Advertising Creation Blueprint｜新品广告创建蓝图

## 两层视图

LEVEL 1 Executive Approval View 让老板在 2–5 分钟内看到经营结论、Campaign 总览、预算分配和关键词释放情况；LEVEL 2 Detailed Creation Blueprint 保留可逐项审计、可映射 SellerSpace 的完整执行参数。

## LEVEL 1 必备字段

《6-1 新品广告创建决策》必须显示 Product Code、Product Name、Marketplace、Store、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Launch Goal、Launch Mode、Launch Window、Recommended Total Launch Budget、Phase 1 Released Budget、Initial Daily Budget、Maximum Daily Budget After Validation、Planned Campaign Count、Initial Keyword Count、Product Target ASIN Count 和 AI Recommendation。

Campaign 总览至少显示 Campaign Name、Role、Targeting、Daily Budget、Base Bid/Bid Range、Bidding Strategy、Top of Search、Rest of Search（支持时）、Product Pages、Keyword/Target Count 和 Purpose。另列 Initial Budget Allocation 与 Initial Keyword Allocation，明确 Campaign Budget Sum、Initial Released Keywords 和 Held in Mother Pool。

对于 `COR-EXA` 且 `CORE_HIGH_CONFIDENCE_EXACT` 的新品核心精准 Campaign，Campaign 总览和明细额外显示 `Base Bid`、`Top Adjustment`（默认参考 +50%）、`Top Placement Adjusted Bid`、`Rest of Search`、`Product Pages`、`Bidding Strategy`、`Potential Maximum Effective Bid`、`Dynamic Upward Multiplier`（如平台确认）及 `Break-even / Economic Risk`。`Base Bid` 不得使用机械 `×1.20` 默认；潜在最大有效竞价在动态上限未确认时标记 `【动态上调上限未确认】`。

## LEVEL 2 必备字段

每个 Campaign 独立展示：名称、Role、Ad Type、Status、Start/End Date、Daily Budget、Portfolio、Bidding Strategy、Top of Search、Rest of Search、Product Pages。

`EXP-PHR`、`DIS-BRO`、`DIS-AUT`、`COM-ASI` 的 Bid、Placement 和 Bidding Strategy 独立展示，不得继承 COR-EXA 的 +50% 参考。

每个 Ad Group 展示名称、Default Bid、Status；Advertised Product 展示 Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]，并固定标记 `[Advertised Product｜Own Product]`。

每个 Keyword 逐词展示 Keyword、中文含义、Source、Cluster、Role、Match Type、Target-Level Bid、H10 Suggested Bid、H10 Bid Range、Amazon/SellerSpace Suggested Bid、Own Historical CPC、Evidence、Reason。缺失显示 `[数据缺失]`，不估算 H10 原始建议竞价。

Auto 展示 Close Match、Loose Match、Substitutes、Complements；只有 SellerSpace/Amazon 支持独立 Bid 时才分别展示 Bid，否则标记 `[当前执行接口不支持]`。Product Target 逐个展示 Target ASIN、产品名、品牌、价格、Rating、Review Count（如有）、Source、Reason 和 Initial Bid，并标记 `[Product Target ASIN]`。

Own ASIN = Advertised Product；Benchmark ASIN = Market/Research Reference；Product Target ASIN = Advertising Target。禁止使用不带身份前缀的通用 ASIN 字段。

## 审批和差异校验

Creation Checklist 必须覆盖 Identity、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Marketplace、Store、Campaign Names/Budgets、Ad Groups、Advertised Product、Keywords、Match Types、Product Targets、Target-Level Bids、Bidding Strategies、Placements、Auto Targeting、Negatives、Launch/Phase Budget、Validation Rules 和 6-2 Handoff。关键字段缺失时只能标记 `[Ready with Known Limitations]` 或 `[Not Ready to Create]`。

A = 全部批准并创建；B = 选择部分修改后重算；C = 重新设计；D = 查看完整明细且不构成批准。用户批准后保存 Approved Creation Blueprint；prepare 返回 Prepared Creation Plan，执行 Field-Level Diff。Campaign、Ad Group、ASIN、Keyword、Bid、Budget、Match、Strategy、Placement、Negative 任一重大差异都必须停止并重新确认。

创建后用同一字段结构 Read-Back，核对 Campaign ID、名称、预算、策略、广告位、Ad Group、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Keyword/Match/Bid、Product Target、Auto、Negative 和 Status。
## Portfolio 字段（新增必填）

Campaign 总览与每个 Campaign 明细都必须展示：`Portfolio Name`、`Portfolio ID`、`Portfolio Status`、来源与读取时间。Portfolio Name 只能来自映射表 `广告组合`，Portfolio ID 只能来自当前 SellerSpace 只读解析；未验证时只能 `[Not Ready to Create]`。Initial Budget Allocation、Creation Checklist、Approved Creation Blueprint、Prepared Plan 和 Read-Back 使用同一字段名，禁止把 Portfolio 留空或用硬编码 ID 替代。

身份字段还必须记录 `Product_NewCode`、正式 `Product_Code`、Store 前缀、`Var_Code`、Advertised Child ASIN、Mapped_SKUs[]、Advertised_SKUs[]。变体映射不完整时只生成不可执行方案，禁止猜测子 ASIN、Mapped_SKUs[]/Advertised_SKUs[]；Campaign 名称使用共享 `format_campaign_name()`。

同一 `Product_Code + Var_Code + Advertised ASIN` 可对应多个 SKU。蓝图必须展示 `Mapped_SKUs[]`、`Advertised_SKUs[]` 和 `SKU_Count`，并通过实际 Ads/SellerSpace eligibility 决定 `ADD BOTH`、`ADD ELIGIBLE SKU ONLY` 或按 ASIN 去重的 `ADD ONCE`；全部不合格时标记 `ADVERTISED_PRODUCT_NOT_ELIGIBLE`。不得取 Excel 第一行 SKU、按 SKU 数量复制 Campaign，或把多个 ASIN 静默合并。

先展示《Campaign Naming Preview》：Campaign 使用正式 Product_Code、可选 Var_Code、AdType、Role、Target/Match 和两位 Sequence；Ad Group 使用 `[Product_Code].[Var_Code].[Role]-[Sequence]` 或 `[Product_Code].[Role]-[Sequence]`。命名不包含日期、Bid、Budget、Coupon、Price、Placement 或策略参数。Sequence Collision Check 必须在审批前完成，旧 Campaign 不重命名。
