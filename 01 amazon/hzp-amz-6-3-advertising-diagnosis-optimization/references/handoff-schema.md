# 6-2 输入交接包

仅当 6-3 已有真实广告数据并形成可交接状态时生成，不提前完整做运营监控。

至少包含：

- Product Code、产品名称、Marketplace、Products Root、Product Root；沿用 Amazon 产品身份解析规则记录的 Store、ASIN、Mapped_SKUs[]、Advertised_SKUs[]、映射来源和 MCP 验证状态
- 6-1 来源报告版本、6-3 报告版本、广告诊断时间范围和产品阶段
- 当前广告状态、最大问题层级、最大烧钱点、最大流量机会
- 核心 Campaign、Keyword/Target、Search Term、Placement 的真实状态
- Impressions、Clicks、CTR、CPC、Spend、Orders、Sales、CVR、ACoS、ROAS（仅真实存在时）
- Budget 状态、页面承接状态、库存/Buy Box 相关风险（如有）
- 每个 Campaign 的原始目的和验证假设
- 已执行或建议执行的最小调整、证据充分性、风险和复查条件
- 继承的 Keyword Mother Pool、Semantic/Purchase Intent Clusters、Initial Released Keywords、Held Keywords、Cluster/Keyword Maturity、Expansion Rules、Expansion Budget Rules、Promotion Rules、Stop Rules
- 已触发的 Expansion Batch/Proposal：Validated Cluster、证据、AI选择词、自动 Match Type、Bid、Budget、Traffic Overlap Check、批准和执行状态
- 待继续观察项、数据不足项、下一周期 6-2 需要关注的广告指标

不得把搜索量、建议 Bid、BSR 或单日结果写成销量、真实 CPC 或稳定结论。6-2 作为下一周期经营诊断入口，继承本交接中的广告状态；完整运营监控仍由 6-2 负责。


## Evidence-Gated Keyword Expansion 交接字段

- 每个 Expansion Batch 独立记录：released_at、keywords、cluster、campaign、match_type、initial_bid、budget_change、approval、execution_result、1/3/7 天或动态验证结果。
- 状态包括 `[扩词有效]`、`[部分有效]`、`[数据不足]`、`[扩词过宽]`、`[流量增加但转化下降]`、`[发现新的成交子Cluster]`、`[建议继续扩词]`、`[建议停止扩词]`。
- Own Product 真实成交词与 H10/Benchmark 推荐词分开；新 Search Term 不在母池时可追加 `Source=OWN_SEARCH_TERM`。

## 阶段6闭环字段

交给下一周期 6-2 时补充：Search Term 生命周期阶段、核心成交词/排名词、当前推广目标、每日调整状态、操作卡、人工决策、执行方式、执行时间、调整前后数据窗口、1天/3天/7天验证结果、自然订单/排名变化和未解决风险。

人工决策与执行日志保存到 `06_SKILL分析报告/广告表现汇报优化日志/`；日志不是 6-3 正式版本，也不能成为最新版报告。
- Portfolio Name（映射表 `广告组合`）、Portfolio ID（SellerSpace 只读解析）、Portfolio Status、来源/读取时间和异常。
- 每个 Campaign/Expansion Batch 的 Portfolio 继承状态；若与当前产品身份不一致，写入状态必须为 `[禁止写入]`。
