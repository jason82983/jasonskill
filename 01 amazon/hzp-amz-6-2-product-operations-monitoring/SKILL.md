---
name: hzp-amz-6-2-product-operations-monitoring
description: 持续监控单个 Amazon 产品的真实经营数据，区分正常波动与明确异常，并将问题路由到 6-3、页面、产品、供应链或 7 阶段 Skill；无可靠数据时明确证据不足，不编造指标。
metadata:
  short-description: 监控 Amazon 产品经营健康并路由异常
---

# HZP Amazon 6-2｜产品经营监控与诊断

## 定位与边界

6-2 是产品级经营总监控入口和异常路由器。它观察销量、流量、转化、广告、自然排名、价格与 Offer、Review、库存、竞争和页面承接，回答“发生了哪一层变化、是否值得处理、由谁处理”。

- 6-1 负责新品推广方案；6-3 负责广告专项诊断；7-1/7-2 负责补货与库存专项决策。
- 不重新完整执行 6-3、5-4、3-2 或 7-1，不把所有异常自己解决。
- 不修改 `01_产品档案.md`、`04_产品推广思路.md`、原始运营数据、历史 HTML 或 `index.html`。
- 一次运行连续完成已经定义的监控，不要求用户逐阶段确认。

## 输入与身份

使用本次确认的 Products Root、Product Root 和 Product Code。先读取：

1. `[Product Root]/01_产品档案.md`；身份缺失或冲突时停止，禁止根据 ASIN、文件名或产品名猜身份。
2. 在任何 SellerSpace 真实查询前，读取 Amazon 行业共享规则 `Amazon产品身份解析规则.md` 和 `00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`，按当前 Product Code 形成唯一 ACTIVE 的 Store + Marketplace + ASIN，并归并变体的 `Mapped_SKUs[]`，再用 MCP 只读验证。缺失、重复 ACTIVE、INACTIVE/TEST、映射与 MCP 或 `01_产品档案.md` 冲突时按共享规则处理，不猜测、不自动修改主表；MCP 不可用时标记 `【SellerSpace实时身份验证未完成】` 并降级到可追溯本地证据。
3. `[Product Root]/04_产品推广思路.md`（可为空，但必须记录为空）。
4. `[Product Root]/06_SKILL分析报告/` 中当前产品最新有效的 6-1 正式报告，并按需读取最新有效 6-3 广告报告及其《6-2输入交接包》。
5. `[Product Root]/05_分析源数据/` 中实际存在的 Business Reports、Sales Dashboard、Detail Page Sales and Traffic、Search Query/Catalog Performance、广告、排名、Brand Analytics、退货、Review、库存、定价和竞品数据。
6. `[Product Root]/07_产品资料/` 中售价、Coupon、Promotion、Review、Rating、页面变更、库存、Buy Box、竞品、运营和质量资料。

文件名只是线索，必须读取实际字段、内容、日期和时间窗口。不得扫描整个硬盘；优先限定当前 Product Root。

### ASIN-first 经营视图与 SKU 下钻

同一 `Product_Code + Var_Code + ASIN` 的多个 SKU 只形成一个 ASIN 经营视图，不生成重复 SKU 报告。广告、订单和销售额聚合前必须先标记 `[ASIN_AGGREGATION_SEMANTICS_CHECK]`，再记录 `Source Grain`、`Aggregation Method` 和 `Deduplication Check`；已经是 ASIN 汇总的数据不得再次按 SKU 求和，语义不明标记 `[ASIN_AGGREGATION_UNCERTAIN]`。库存显示 ASIN 总览并保留 SKU breakdown；SKU 缺货、Offer、Listing、履约或广告资格异常必须作为 SKU-level Exception 下钻展示，不能被 ASIN 总览掩盖。

## 最新版本与追溯

按 `Product Code + Skill 编号` 选择版本化正式报告：最大 `V` 优先，同 `V` 按文件名 `YYYYMMDD_HHMMSS` 最新。排除 `index`、失败、invalid、incomplete、deprecated、draft、preview、temp、test、非正式输出以及 `广告表现汇报优化日志/` 目录及其子目录；不得使用 filesystem 顺序、modified time 或跨产品文件。无法确认有效性时标记 `【上游报告有效性无法确认】`，不得静默回退。

正式 HTML 必须有《输入版本追溯》，记录每个实际读取的报告的 Skill 编号、中文名、文件名、版本、时间戳、输入类型和用途。6-1 为【核心输入】；6-3 为【辅助回查】；其他 Skill 按需为【辅助回查】；历史版本仅为【历史版本对照】。不得重新完整运行上游 Skill。

## 监控方法

先确认每个数据源的实际窗口和产品阶段（【新品期】、【成长期】、【稳定期】、【衰退/异常期】或【阶段无法确认】），再按系统链路观察：

`销量 → 流量 → 转化 → 广告 → 自然流量/排名 → 价格/Offer → Review/质量 → 库存/Buy Box → 竞争`

优先比较当前窗口与前一可比窗口；只有数据覆盖时才做 7/14/30 天趋势。不同窗口必须分开说明，不能用 3 天数据强做 30 天结论。

必须覆盖以下正式章节（数据不足仍保留章节并说明缺口）：

1. 《产品运营总览》
2. 《输入版本追溯》
3. 数据范围与完整性、当前产品阶段
4. 《流量健康检查》
5. 《转化健康检查》
6. 《销量结构》
7. 《广告整体影响》（继承 6-3，不重做完整广告诊断）
8. 《自然排名健康》
9. 《价格与Offer状态》
10. 《Review风险趋势》
11. 《库存健康检查》
12. 《竞争变化》
13. 《运营异常清单》
14. 《运营变化根因判断》
15. 《异常—责任Skill路由》
16. 《运营优先事项》
17. 《运营动作清单》
18. 《反方检查》
19. 最终运营状态
20. 《7-1输入交接包》、数据局限和术语解释

### 关键判断约束

- 不看单点：销量下降不能直接等于广告问题；CVR 下降不能直接等于页面问题；排名上升不能直接等于经营改善。
- 分离广告与自然：真实数据支持时报告广告/自然订单、流量占比和自然排名变化；广告占比上升且自然订单下降时标记【广告依赖风险上升】；广告占比下降、总销量增长且自然能力改善时才可标记【自然增长能力增强】。
- Review 不只看星级；重复结构、材料、功能或批次问题应路由 4-1/4-2/3-2。
- 库存不足或 Buy Box 风险时不能无条件建议放量；6-2 只识别风险，7-1 才做正式补货预测。
- 竞品变化只有在真实证据显示会改变点击、转化、价格或差异化时才升级为经营异常。
- 不制作“健康分”“运营得分”或“AI 信心分”。只给真实状态、原因和证据充分性。

### 状态、优先级与证据标签

异常状态只允许：`【正常波动】`、`【值得观察】`、`【明确异常】`、`【高风险异常】`、`【证据不足】`。

运营优先事项只允许：`【P0｜今天必须处理】`、`【P1｜近期重点处理】`、`【P2｜继续观察】`、`【无需动作】`。这里的 P0/P1/P2 是运营优先级，不等同于产品开发或广告优化优先级。

事实判断使用：`[原始运营数据]`、`[已确认事实]`、`[人工运营记录]`、`[分析推断]`、`[推算指标]`、`[初步信号]`、`[证据充分]`、`[证据不足]`、`[可能相关]`、`[异常待确认]`、`[需要专项诊断]`、`[无需动作]`。不得把相关性写成因果，不得用经验阈值替代真实窗口和业务阶段。

最终运营状态只能使用：

- `【整体运营健康｜维持当前策略】`
- `【整体基本健康｜存在局部优化项】`
- `【出现明确异常｜需要专项处理】`
- `【出现高风险异常｜优先处理核心问题】`
- `【关键数据不足｜暂无法判断整体运营状态】`
## 阶段6增长闭环与运行日志

6-2 读取 6-1 正式报告、按需读取 6-3 广告报告和阶段6运行日志，但运行日志只作为【运行证据】或【历史验证】，不替代最新有效正式报告，也不进入 0-2 正式索引或最新版选择。

- 增加增长飞轮观察：广告订单 → 核心 Search Term 重复成交 → Keyword 自然排名 → Organic order → Organic share → Total order → 经济性 → 是否具备放量条件。只能根据真实变化描述，不能声称存在公开统一的 Amazon“整体权重”公式。
- 增加《放量资格判断》：综合 CTR、CVR、广告/自然订单、Organic share、核心词重复成交、核心词排名、CPC、边际 ACoS、Review、Coupon 依赖、Price 稳定性、库存覆盖、竞争和页面状态；不使用固定 3/10/30/100 单机械门槛。
- 增加《Coupon依赖判断》：比较 Coupon 调整前后 CVR、总订单、自然订单、关键词排名、利润和广告经济性，输出可回撤、继续维持、强折扣依赖、测试较低 Coupon 或证据不足。
- 今日运营结论必须能路由到加速、维持、优化、减速或停止，并明确最重要动作、责任 Skill、人工介入和验证窗口。
- 日常监控、人工批准/否决、实际执行和验证记录写入 `06_SKILL分析报告/广告表现汇报优化日志/`；正式 6-2 HTML 仍写入 `06_SKILL分析报告/` 根目录。
- MCP接入继续区分读取与写入能力；6-2默认只做产品级判断和路由，无法写入时不假装替广告 Skill 执行动作。

## 报告与索引

正式 HTML 保存到当前 Product Root 的 `06_SKILL分析报告/`，不覆盖历史：

`6-2_[产品编号]_产品经营监控与诊断_[周期标识]_V[最大版本号+1]_[YYYYMMDD]_[HHMMSS].html`

周期标识使用稳定短值（如 `3D`、`7D`、`14D`、`30D`、`WEEKLY` 或 `CUSTOM_YYYYMMDD-YYYYMMDD`）。历史未带周期标识的正式文件继续兼容；版本选择仍只看 `V` 和文件名时间戳，不能另造第二套版本系统。

首页第一屏显示产品代码+中文名、Marketplace、监控窗口、产品阶段、整体状态、销量/流量/转化/广告/自然排名/Review/库存状态、最大异常/机会/风险、今天最重要动作和是否需要人工介入。只有真实数据支持时生成趋势图；否则明确显示 `[数据不足，未生成该图表]`。

报告写入并确认文件存在、命名正确后，调用 `hzp-amz-0-2-report-index`，原样传递 Product Code、Products Root、Product Root。6-2 不扫描、生成、排序、维护或备用更新 `index.html`。报告失败不调用 0-2；报告成功但索引失败时保留报告并分别报告两种状态。

详细监控规则见 [references/monitoring-framework.md](references/monitoring-framework.md)，7-1 交接字段见 [references/handoff-schema.md](references/handoff-schema.md)，HTML 章节模板见 [templates/report-outline.md](templates/report-outline.md)。
## Portfolio 级运营监控（增量规则）

6-2 沿用共享 `Amazon广告身份解析规则.md`，读取映射表 `广告组合` 作为 Portfolio Name，并通过 SellerSpace 只读解析 Portfolio ID。监控范围记录 Store、Marketplace、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Portfolio Name/ID/Status；Portfolio ID 不得硬编码。

可按 Portfolio 聚合广告 Impressions、Clicks、Spend、Orders、Ad Sales 等，但必须明确区分 `Portfolio Ad Sales` 与 `Product Total Sales`，不能把 Portfolio 销售额直接当作当前产品总销售额。若 Campaign/广告数据落在错误 Portfolio、同名多 ID、Portfolio 缺失或无法验证，输出 `【Portfolio Identity Anomaly｜广告组合身份异常】`，保留只读监控并路由 6-3/6-1；不得替换身份或执行广告写操作。

## 统一产品与变体身份（增量规则）

6-2 与 6-1、6-3 共用 `resolve_advertising_identity()`，监控层级固定为 `Product_NewCode → Product_Code → Portfolio → Var_Code → Campaign`，并保留 Store、Marketplace、Own ASIN、Child ASIN、Mapped_SKUs[]/Advertised_SKUs[]。`Product_NewCode`（包括 N+数字）只是研究代码，不能替代正式 Product_Code；不得按 ASIN、文件名、前缀或中文名猜身份。Own ASIN、Benchmark ASIN、Product Target ASIN 严格分开。

只有可靠的 `Var_Code → Child ASIN → Mapped_SKUs[]` 才能做变体级趋势；缺失或冲突时标记 `【变体广告身份映射不完整】`，报告可继续只读但不得把其他变体数据归入当前变体。Portfolio 聚合仍与 Product Total 分开，身份冲突沿共享规则路由回 6-3/6-1。

6-2 使用共享 `parse_campaign_name()` 识别 Product_Code、Var_Code、AdType、Role、Target/Match、Sequence；名称只是 Parsing Hint。必须先用 Shared Advertising Identity Resolver、映射表和 SellerSpace 实际 Advertised Product/Child ASIN、Mapped_SKUs[]/Advertised_SKUs[] 确认归属。解析出的 Var_Code 与真实变体不一致时标记 `【广告命名与真实变体身份冲突】` 并路由 6-3；不得按名称前缀聚合，也不执行 Rename。旧名称若身份已验证仅记为 `【历史广告命名】`，不产生经营异常；无法确认则标记 `【广告身份无法可靠确认】`。

本次同步只识别 Product_Code 后新增的独立 Var_Code 段；其余 AdType、Role、Target/Match、Sequence 规则不变。名称仍不是 Master Identity Source。

## ASIN经营周期报告与日期对比（增量规则）

本节只增加报告周期、对比和图表展示能力，不改变产品身份、Portfolio、SellerSpace、Root Cause、异常检测、Scaling 或路由逻辑。每次运行先解析 `Skill → Product_Code → optional Var_Code → Report Period → Comparison Mode`，在同一次运行中固定 Product Code、Var Code、ASIN、Mapped_SKUs[]、Advertised_SKUs[]、Store 和 Marketplace。

### 周期解析

- **站点日期边界（强制）**：所有“最近 N 个完整自然日”、本周、上周及环比窗口，必须先按目标 Amazon `Marketplace` 的业务日期边界计算，再生成 SellerSpace/其他数据源查询窗口。不得直接使用运行机器的本地日期、北京时间或 UTC 日期替代站点日期。对于 Amazon US，只有在美国站点的该日期已经完整结束后，才能纳入窗口；北京时间 17 日查询时，美国站点 16 日若尚未确认完整，最近 7 个完整自然日仍应取美国站点 9 日至 15 日。若数据源未明确返回或支持站点日期边界，标记 `[MARKETPLACE_TIMEZONE_UNCERTAIN]`，不得把可能未完整的一天计入，并在报告中降级证据。
- 报告必须同时记录 `Marketplace`、采用的站点日期边界/时区来源、`Current Start/End`、`Comparison Start/End`、`Today Included` 和是否存在未完整日；环比窗口也必须沿用同一站点日期边界。
- 支持最近 `3天`、`7天`、`14天`、`30天`，均截至**站点业务日的昨天**，默认只取完整自然日。
- 未指定周期时默认 `最近7个完整自然日`；今天不计入。日期必须由程序化日历计算，不能硬编码示例日期。
- 支持 `本周` 和 `上周`。自然周按周一至周日；本周只取已经完成的自然日，上周优先使用已结束的完整周，并在报告写出实际日期。
- 支持明确日期（如 `2026-09-01到2026-09-07`、`9月1日到9月7日`）和任意合理自定义范围，模式标记为 `DATE_RANGE_CUSTOM`。用户明确包含今天时允许执行，但必须显示 `【包含未完整自然日】`。

### 对比规则

- 默认开启 `环比`：当前窗口之前紧邻的、连续、等长且不重叠完整窗口。
- 可选 `同比`（前台显示“同比（同期对比）”）、`环比+同比` 或 `不对比`。3/7/14 天的同比按上个月对应日历日期；无法完整对齐时必须披露实际参考范围。30 天同比优先按去年同一日期区间；完整自然月才按去年同月。
- 自然周环比为上一自然周；自然周同比为去年对应自然周。每个变化必须同时显示对比周期，不能只写百分比。
- 比率指标优先显示百分点变化：CVR、ACoS 等同时可给相对变化，但不能用分子/分母简单相减替代比率重算。缺少分母时不计算变化。

正式报告的《报告参数》必须记录：Product_Code、Var_Code、ASIN、Marketplace、Report Mode、Current Start/End、Days、Comparison Mode、Comparison Start/End、Reference Compare Start/End（如有）、站点日期边界/时区来源、Generated At、Today Included、未完整日状态。

### 图表选择

只有真实时间序列才画趋势图；缺失日期标记 `[数据缺失]`，不得当作 0、插值或制造趋势。按数据形态动态选择：时间序列用折线图，当前/环比/同比用普通 2D 柱状图，Part-to-Whole 用圆环图，Top 贡献用横向柱状图，少量关键指标用 KPI Cards；数据不足则显示 `[数据不足，未生成该图表]`。LEVEL 1 首页保留 3～6 张最重要图表，LEVEL 2 可放详细图表，不引入新的大型前端框架或第二套图表库。

每张图必须有中文标题、说明句、单位、日期范围、必要图例和 Tooltip。图表负责理解，表格负责查数，文字负责解释结论。颜色只表达正常/关注/明确问题/无法判断的经营语义；不能把所有下降机械标红（ACoS 下降通常属于改善）。

### 首页与专业版

LEVEL 1 首页固定展示《今天/这段时间怎么样？》《要不要处理？》《关键数据》KPI Cards（Orders、Sales、Ad Orders、Organic Orders、Ad Spend、ACoS、CVR、Inventory）、《走势》《订单从哪里来？》《跟上一周期比怎么样？》《现在最值得做的3件事》《这次不要动什么》《下一步怎么做》。每张 KPI Card 显示当前值、环比、同比（启用时）和一句经营解释。

LEVEL 2 保留 Daily Metrics、Campaign、Keyword、Search Term、Placement、Variant、Portfolio、Organic/Ad、CTR、CPC、CVR、CPA、ACoS、ROAS、Root Cause、Scaling Evidence、Inventory、Input Version Trace、Data Source、Evidence Gaps、Confidence 和完整数字表。周期越短，结论置信度越谨慎：3 天只适合发现异常，7 天常规判断，14 天阶段趋势，30 天经营复盘。

详细日期算法、对比边界、图表选择和 Mock A-T 用例见 [references/periods-and-charts.md](references/periods-and-charts.md)。

## ERP Keyword Provider（阶段6统一规则）

阶段 6 的 ERP 历史关键词只通过共享 `scripts/erp_keyword_adapter.py` 读取；本 Skill 不得自行编写 PickPwKView SQL 或解释 Provider 列名。运行时先读取 `03_系统配置/erp-amazon-data-mapping.json` 和 `erp-amazon-pickpwkview-schema.md`，再从本次已确认的 `[Product Root]/01_产品档案.md` 读取档案中明确记录的 ERP 产品编号（返回实际字段名；没有编号为 `[ERP_PROID_MISSING]`，冲突为 `[ERP_PROID_CONFLICT]`）。只以该编号作为参数查询 `Amazon.dbo.PickPwKView.ProId`，不得用 Product_Code、ASIN、文件名、首条记录或相似产品替代，也不得跨产品。

适配器返回每行 `Keyword`/`KeywordCn`、完整 `raw_fields`、字段定义状态和追溯信息（`Provider`、`Source_View`、`ERP_ProId`、`Field_Definition_Source`、`Retrieved_At`、`Source_Grain`、`Metric_Semantics`、`Data_Through`、`Freshness`、`Aggregation_Method`）。字段语义只以 `03_系统配置` 文档为准；未明确的列必须标记 `SEMANTICS_UNCERTAIN`，不得把它们猜作搜索量、点击、订单、销售、CVR、排名或竞价。连接复用既有只读配置/密钥，SQL 只允许参数化 SELECT；密码、服务器和连接字符串不得进入 Skill、报告、日志或 Git。

- 6-1：ERP 关键词仅作为 COR 候选、EXP 候选和少量 DIS Broad Seed 的辅助证据，不能由 ERP 历史标记直接升级为核心成交词。
- 6-2：只识别 ASIN 经营层面的关键词异常或机会，并路由 6-0-2；不复制 ERP 精准词筛选、聚类、精准泛词或 Rankability 算法。
- 6-3：ERP 关键词仅作为历史 Search Term/生命周期参考；当前 Amazon 自有广告数据足够后由自有数据接管，不自动跨产品扩展。

连接/驱动/密钥不可用返回 `[ERP_KEYWORD_PROVIDER_UNAVAILABLE]`，无匹配行返回 `[ERP_KEYWORD_DATA_NOT_FOUND]`；这些状态只降级 ERP 证据，不阻断本 Skill 其他数据源。

### 6-2 关键词专项路由（6-0-2）

6-2 可以读取共享 ERP Adapter 返回的关键词证据，识别 Search Term 覆盖、核心词排名信号、广告/自然转化差异等 ASIN 经营异常或机会。需要 ERP 精准词识别时输出 `Route → 6-0-2`；需要精准泛词或后续关键词经营时输出 `Route → 6-0-3`，并读取对应最新有效资产。

6-2 不在自身报告中重复生成关键词战略结论；字段语义、ProId、Tags `|1精准|` 和 `IsExact` 的统一定义仍由共享 Adapter/6-0-2 维护。连接失败、无匹配、ProId 缺失或语义不确定时，只记录证据缺口，不跨产品回退。

## MCP Provider Boundary / Canonical Business Model

6-2 的经营监控只消费 HZP Canonical 业务语义，不直接依赖 SellerSpace/优麦云的原始 Tool Name、Field Name、JSON 结构、枚举、分页或指标名称。Provider Adapter 负责映射 ASIN、Mapped_SKUs[]、Store、Marketplace、Portfolio 及订单、销售、流量、转化、库存和广告指标，并保留 Source_Grain、Metric_Semantics、Attribution_Semantics、Data_Through、Freshness、Aggregation_Method、Deduplication_Status。广告归因订单与产品总订单不得静默合并；语义不明时标记 `[ASIN_AGGREGATION_UNCERTAIN]`。

Provider 能力必须显式标记 `SUPPORTED`、`NOT_SUPPORTED` 或 `SEMANTICS_UNCERTAIN`；缺失能力只返回 `[CAPABILITY_NOT_AVAILABLE]`，不得猜测或静默替代。未来新增 Provider 只需新增真实 Schema/Capability/语义映射 Adapter，不改变本 Skill 的 ASIN-first 核心判断。
## 关键词专项路由（6-0-2）

6-2 只识别 ASIN 经营层面的关键词异常或机会（例如 Search Term 覆盖变化、核心词自然排名信号、广告/自然词转化差异），不再复制 ERP 精准词筛选、精准泛词生成、Search Intent 聚类或 Rankability 算法。精准词问题输出 `Route → 6-0-2`；精准泛词问题输出 `Route → 6-0-3`，并读取对应最新有效资产。
