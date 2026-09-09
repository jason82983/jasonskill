# HZP Amazon 2-2｜细分市场分析

这个 Skill 判断目标 Amazon 产品真正属于哪些细分市场，分析市场需求、竞争结构、消费者痛点、新品进入机会和价格空间，最终输出 GO、CONDITIONAL GO、NO-GO 或因 P0 缺失而 HOLD / STOP 的结论，并为 3-1 产品机会定义提供结构化输入。

## 适用范围

适用于：

- 验证用户指定的 Niche 是否真实匹配；
- 比较多个候选 Niche，选择主切入口和次级机会；
- 分析市场需求、趋势、集中度、价格带、新品表现和消费者需求；
- 对比对标新品、Niche 榜1和整个市场；
- 输出市场进入决策、机会定义和下游 HANDOFF。

不适用于单个 ASIN 的完整产品诊断、Listing 文案、广告优化或供应商执行。

## 使用方式

在目标 Product Root 上调用：

Use $hzp-amz-2-2-market-analysis to validate this product's Amazon market scope and entry opportunity.

Skill 会优先读取：

- 01_产品档案.md
- 05_分析源数据/02_细分市场数据/
- 05_分析源数据/01_产品数据/
- 05_分析源数据/03_关键词数据/
- 05_分析源数据/04_用户反馈/
- Products Root 的 00_产品公用数据/01_Amazon平台资料/

人工思路只能作为人工假设，不能替代市场证据。

## 核心规则

- 不盲信用户指定的 Niche 名称，先做 Market Scope Validation。
- Definition ≠ Evidence；公共定义与产品/市场实际数值分开。
- Amazon 行为数据优先；无法精确匹配的第三方数据标记为 [证据不足]。
- 不从 BSR、评论数、价格或单个关键词搜索量推算未经支持的市场规模、销量或利润。
- 结论区分 [数据支持]、[分析推断]、[待验证]、[证据不足] 和 [样本有限]。
- ASIN 是稳定研究对象，角色是动态上下文；同一 ASIN 只读取和保存一套原始数据。
- 榜1必须绑定具体 Niche，并尽量带数据日期；2-2 仍需按当期数据重新验证。
- 不修改、覆盖、删除或复制原始证据。

## 新的核心决策问题

2-2 默认不是单纯回答“这个 Niche 好不好”，而是回答：

> 如果以这个对标产品为开发起点，在它背后的真实 Amazon 市场中进行改良开发，这个项目是否值得进入 3-1？

因此，2-2 是“以对标产品为开发起点的细分市场进入决策”。对标产品是分析锚点和机会线索，不等于市场本身。

## 两种分析模式

- Benchmark-Driven Analysis：当产品档案中有对标产品或对标新品时默认启用，比较对标产品、成熟榜1和整体 Niche。
- Market-Driven Analysis：没有明确对标时启用，从市场边界和消费者需求出发寻找机会，不虚构对标产品。

对标驱动分析必须回答：哪些优势应该保留、哪些问题值得改良、哪些设计不应复制，以及消费者为什么可能从对标或榜1转向 HZP 产品。

## 改良机会验证

对标产品的每个潜在问题都必须经过：

1. Benchmark Problem：问题是什么；
2. Evidence：证据来自 Reviews、Niche 负面评价、退货、榜1、搜索词或市场数据；
3. Market Validation：问题是单个产品问题，还是市场普遍问题；
4. Consumer Importance：是否影响购买、评分或退货；
5. Existing Solution Check：榜1或其他成熟产品是否已解决；
6. Commercial Opportunity：是否可能带来转化、评价、退货、差异化、场景、人群或价格价值；
7. Development Handoff：只把有证据的机会交给 3-1。

报告必须包含改良机会矩阵，并把特征分为 SHOULD KEEP、SHOULD IMPROVE、OPTIONAL DIFFERENTIATION、SHOULD NOT COPY。改良价值使用 P0、P1、P2；不得为了显得有差异化而强行创造改良点。

## 2-1、2-2、3-1 分工

- 2-1：解释一个对标产品为什么成功或失败。
- 2-2：判断基于该对标进行改良开发的市场是否值得进入，并验证问题是否具有市场普遍性。
- 3-1：将机会转成详细产品定义、结构、尺寸、材料、BOM、样品和质量标准。

## P0 / P1 / P2

- P0：目标 ASIN 的 Niche 出现记录、候选 Niche 核心 Amazon 数据、头部商品、主要搜索词、市场核心指标、点击或品牌集中度。P0 无法确定市场边界时停止结论。
- P1：Niche 正负面评价、退货洞察、对标 Keepa/Cerebro/Reviews/Listing、榜1数据。缺失时可继续，但要降低可信度并说明影响。
- P2：更多代表 ASIN、精确匹配的第三方数据、社媒、Google Trends、行业资料。可选，不能编造。

## 输出

~~~
06_SKILL分析报告/
└─ 2-2_细分市场分析/
   ├─ 2-2-[产品编号]_[分析对象可选]_细分市场分析报告_[YYYY-MM-DD].html
   └─ 2-2-[产品编号]_HANDOFF.md
~~~

HTML 首屏显示产品、对标 ASIN、主要市场、分析模式、结论、最大改良机会、最大风险和进入 3-1 的关键条件，并显示 HZP Amazon 2-2｜细分市场分析。报告正文增加 Benchmark Definition、Improvement Opportunity Matrix、Benchmark-Based Entry Thesis 和 Risks & Failure Conditions。HANDOFF 是给 3-1 的浓缩接口，不复制整份 HTML。

详细流程见 SKILL.md；市场边界见 references/market-scope-validation.md；改良机会验证见 references/improvement-opportunity-validation.md；对标与榜1比较见 references/benchmark-vs-leader.md；报告结构见 templates/report-outline.md；HTML 展示要求见 templates/html-report-style.md；下游接口见 templates/handoff-template.md。
