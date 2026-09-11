# 6-3 监控框架

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
