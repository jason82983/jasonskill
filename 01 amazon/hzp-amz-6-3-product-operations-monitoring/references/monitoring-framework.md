# 6-3 监控框架

进入 SellerSpace 查询前，统一读取 Amazon 行业共享文件 `Amazon产品身份解析规则.md`，从 Products Root 的 `00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx` 解析唯一 ACTIVE 的 Store + Marketplace + ASIN + SKU，并只读二次验证。身份异常按共享规则处理；本文件不复制身份解析逻辑。

## 数据发现

在当前 Product Root 内主动检查 `05_分析源数据` 和 `07_产品资料`。优先识别 Business Reports、Sales Dashboard、Detail Page Sales and Traffic、Search Query/Catalog Performance、Advertising、Keyword/Organic/Sponsored Rank、Brand Analytics、Return/Refund、Review、Inventory/FBA、Pricing/Buy Box 和 Competitor Tracking。按实际字段识别数据类型，不凭文件名猜语义。

记录每个来源的：文件名、实际字段、最早日期、最晚日期、行数/样本量、是否可比较、是否存在缺失或冲突。窗口不一致时分别呈现，禁止把 7 天广告与 30 天销量当成同一窗口。

## 分析顺序

1. 产品运营总览：身份、Marketplace、阶段、窗口、各层状态、最大异常/机会/风险、今日动作、人工介入。
2. 流量：Sessions、Page Views、Impressions、Ad Traffic、Organic Traffic、关键词/Search Query；区分广告流量下降、自然流量下降、搜索需求、预算、资格、库存、Buy Box 和索引变化。
3. 转化：Sessions、Orders、Units、Unit Session Percentage/CVR、Ad CVR、可真实计算的 Organic CVR，并联看流量结构、价格、Coupon、Rating、Review、Offer 和页面变更。
4. 销量结构：只在真实字段支持时拆分总订单、Units、广告订单、自然订单、核心词、长尾、竞品流量和促销订单；不得伪算。
5. 广告整体影响：继承最新 6-2 结论，只判断支撑增长、拖累经济性、流量不足、异常波动或过度依赖；不重复做 6-2 诊断。
6. 自然排名：追踪核心关键词的 Organic Rank、Sponsored Rank、流量和订单贡献；排名不作为独立经营目标。
7. 价格与 Offer：Price、Coupon、Promotion、Deal、Prime、Buy Box、Delivery 和竞品价格；广告/流量未变而 Offer 变化时纳入根因。
8. Review：Rating、Review Count、新增差评和主题趋势；分类为【偶发问题】、【重复问题】、【新出现问题】、【已知问题恶化】、【核心产品风险】或【证据不足】。
9. 库存：Available、Reserved、Inbound、Total Inventory、Sales Velocity、Days of Cover、OOS、广告放量约束、Buy Box/排名影响；只识别风险，不做完整补货预测。
10. 竞争：只看会改变经营判断的降价、Coupon、强势新竞品、Review、页面升级、类似差异化和关键词竞争变化。
11. 异常清单：只使用【正常波动】、【值得观察】、【明确异常】、【高风险异常】、【证据不足】。
12. 根因：可标记【流量层】、【转化层】、【广告层】、【自然排名层】、【价格/Offer层】、【Review/产品质量层】、【库存层】、【竞争环境层】、【多因素共同作用】、【证据不足】。用“可能相关”表达未证实因果。
13. 路由：广告→6-2；页面承接→5-4；文案→5-2；视觉→5-3；样品→4-1；量产→4-2；产品方案→3-2；机会失效→3-1/2-2；库存/补货→7-1/7-2；正常波动→无需处理。遵守最小必要升级。

## 反方检查

在最终状态前回答：是否把单日波动当异常；是否只看销量、ACoS 或星级；是否把销量下降直接归因广告、CVR 下降直接归因页面、竞品变化直接写成因果；是否忽略价格、Buy Box、库存、自然能力、Review重复问题；是否越权重做 6-2、5-4 或 7-1；是否可以明确标记【无需动作】。

## 最终状态

只能使用：

- 【整体运营健康｜维持当前策略】
- 【整体基本健康｜存在局部优化项】
- 【出现明确异常｜需要专项处理】
- 【出现高风险异常｜优先处理核心问题】
- 【关键数据不足｜暂无法判断整体运营状态】

不得为了显示价值而强行给出动作；最佳结论可以是【无需动作】。


## 阶段6闭环补充

6-3 读取 6-1/6-2 正式报告和阶段6运行日志，但运行日志只作为【运行证据】或【历史验证】，不替代最新有效正式报告，也不进入 0-2 正式索引或最新版选择。

- 增加增长飞轮观察：广告订单 → 核心 Search Term 重复成交 → Keyword 自然排名 → Organic order → Organic share → Total order → 经济性 → 是否具备放量条件。只能根据真实变化描述，不能声称存在公开统一的 Amazon“整体权重”公式。
- 增加《放量资格判断》：综合 CTR、CVR、广告/自然订单、Organic share、核心词重复成交、核心词排名、CPC、边际 ACoS、Review、Coupon 依赖、Price 稳定性、库存覆盖、竞争和页面状态；不使用固定 3/10/30/100 单机械门槛。
- 增加《Coupon依赖判断》：比较 Coupon 调整前后 CVR、总订单、自然订单、关键词排名、利润和广告经济性，输出可回撤、继续维持、强折扣依赖、测试较低 Coupon 或证据不足。
- 今日运营结论必须能路由到加速、维持、优化、减速或停止，并明确最重要动作、责任 Skill、人工介入和验证窗口。
- 日常监控、人工批准/否决、实际执行和验证记录写入 `06_SKILL分析报告/广告表现汇报优化日志/`；正式 6-3 HTML 仍写入 `06_SKILL分析报告/` 根目录。
- MCP或其他外部平台能力不足时，保持“AI判断/路由 + 人工执行”边界，不把建议写成已执行。
## Portfolio 聚合与异常

监控表增加 Portfolio Name、Portfolio ID、验证状态和来源。Portfolio 层指标与 Product 层指标分开：Portfolio Ad Sales/Orders 只表示组合聚合，Product Total Sales/Orders 只表示当前 Own ASIN/SKU。发现 Campaign Portfolio 不匹配、ID无法解析、同名多 ID 或跨店铺/站点命中时，标记 `Portfolio Identity Anomaly`，只读记录并路由，不把异常数据静默归入产品。

监控上下文沿 `Product_NewCode → Product_Code → Portfolio → Var_Code → Campaign` 继承；没有可靠 Child ASIN/SKU 关系时不做变体归因。

## ASIN经营周期、对比与图表（新增）

### 日期窗口

解析顺序固定为：`Skill → Product_Code → optional Var_Code → Report Period → Comparison Mode`。默认窗口是截至昨天的最近 7 个完整自然日；今天的数据即使存在，也默认排除。最近 N 天的起止日按日历程序计算：`end = today - 1 day`，`start = end - (N-1) days`。自然周按 Monday-Sunday：上周使用最近已结束的周一至周日，本周只纳入截至昨天已完成的日期，并披露不完整状态。自定义范围原样使用并计算真实天数；若包含今天，标记【包含未完整自然日】。

### 对比窗口

默认环比取当前窗口之前紧邻的、连续、等长、不重叠完整窗口。同比/同期对比使用内部模式 `PERIOD_REFERENCE_COMPARE`：3/7/14 天按上个月对应日历日期，30 天按去年同一日期区间；完整自然月才按去年同月。日期不存在或无法完整对齐时，报告披露实际参考范围，不静默改变窗口。每个变化必须展示“对比周期”。CVR、ACoS 等比率重新用可靠分子/分母计算，优先展示百分点变化；分母缺失时显示【证据不足】。

### 图表选择契约

| 数据形态 | 图表 | 必须显示 |
|---|---|---|
| 真实每日/周期时间序列 | 折线图或柱线图 | 中文标题、单位、时间范围、Tooltip |
| 当前 vs 环比/同比 | 普通 2D 分组柱状图 | 图例含各周期和对比日期 |
| Part-to-Whole 结构 | Donut/Ring | 组成总和、各部分数值和比例 |
| Top 贡献项 | 横向柱状图 | 排名、单位、样本范围 |
| 少量关键指标 | KPI Cards | 当前值、环比、同比（启用时）、一句解释 |

只有真实数据覆盖时才画图；缺失日期标 `[数据缺失]`，不得当作 0、插值或制造趋势。没有足够数据时显示 `[数据不足，未生成该图表]`。LEVEL 1 首页保留 3～6 张最重要图表，LEVEL 2 才放细分图表；沿用现有图表库，不引入大型前端框架或第二套库。颜色只表达正常、关注、明确问题和无法判断，不能把所有下降机械标红。

### 周期谨慎程度

3 天主要用于发现异常，不宣布趋势形成或大幅放量；7 天用于常规运营判断；14 天用于阶段趋势；30 天用于经营复盘。结论强度和置信度必须随周期长度与数据完整性调整。

### Mock 用例

周期与图表实现至少覆盖 SKILL.md 中 CASE A-T：默认 7 天、3/14/30 天、自然周、自定义日期、环比/同比/双对比、排除或标记今天、缺失日、组成/时间序列/周期对比图表、ACoS 下降语义、CVR 百分点、短周期谨慎结论和不足数据不造假。
