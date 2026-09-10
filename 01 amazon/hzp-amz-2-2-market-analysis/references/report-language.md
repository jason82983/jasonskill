# 2-2 报告中文显示规则

本规则只约束 2-2 生成的 **HTML 人类报告** 的显示语言，不改变数据读取、分析逻辑、判断标准、目录结构或章节顺序。AI Handoff 继续使用既定接口字段，避免下游 Skill 解析中断。

## 默认语言

- HTML 报告以中文阅读为第一优先。一级标题、二级标题、卡片标题、表格表头、指标名称、结论标签、风险标签、图表标题、注释、页首摘要和页尾说明，凡能自然中文表达的，全部使用中文。
- 首次出现的必要缩写可写成“中文说明（英文缩写）”，例如“转化率（CVR）”“广告销售成本比（ACoS）”“畅销排名（BSR）”。
- `GO`、`CONDITIONAL GO`、`NO-GO`、`P0/P1/P2`、ASIN、Amazon、Keepa、Cerebro、FBA、Prime 等可保留；结论旁必须有中文解释。`Niche` 优先写“细分市场”，只有在数据字段或专有名词需要时保留英文。
- 品牌名、产品名、ASIN、Amazon 原始字段和原始文件名不翻译，不为了中文化改写原始数据。

## 固定标题与界面用语

| 英文原称 | HTML 中文显示 |
|---|---|
| Executive Decision | 执行决策 |
| Benchmark Definition | 对标产品定义 |
| Market Scope Validation | 市场范围验证 |
| Market Relationship Map | 市场关系图 |
| Candidate Niche Decision Table | 候选细分市场决策表 |
| Candidate Market Comparison | 候选市场对比 |
| Market Quality | 市场质量 |
| Competition Structure | 竞争结构 |
| Search Demand | 搜索需求 |
| Consumer Need Map | 消费者需求地图 |
| Benchmark Performance | 对标产品表现 |
| Leader Reference | 头部产品参考 |
| Benchmark vs Leader vs Market | 对标产品 vs 头部产品 vs 市场 |
| Improvement Opportunity Matrix | 改良机会矩阵 |
| Benchmark-Based Entry Thesis | 基于对标产品的市场进入逻辑 |
| Risks & Failure Conditions | 风险与失败条件 |
| Evidence & Limitations | 证据与局限 |
| Primary Market | 主要细分市场 |
| Secondary Market | 次要细分市场 |
| Benchmark | 对标产品 |
| Leader | 头部产品 / 榜1 |
| Decision | 最终决策 |
| Biggest Opportunity | 最大机会 |
| Biggest Risk | 最大风险 |
| Evidence | 证据 |
| Market Gap | 市场缺口 |
| Priority | 优先级 |
| Consumer Importance | 消费者重要度 |
| Development Recommendation | 开发建议 |
| Organic Rank | 自然排名 |
| Search Volume | 搜索量 |
| Competing Products | 竞品数量 |
| Average Competing Products | 平均竞品数量 |
| Keyword Count | 自然词数 |
| Search Volume Sum | 搜索量总和 |
| Demand Competition Ratio | 需求竞争比 |
| H10 Data Date | H10数据日期 |
| Market Demand Competition Ratio | 市场需求竞争比 |
| Market Search Conversion Efficiency | 市场搜索转化效率 |
| Keyword Click Conversion | 关键词点击转化 |
| Niche Clicks 360D | 细分市场点击量（过去360天） |
| Click Share 360D | 点击份额（过去360天） |
| Estimated Clicks | 推算点击数 |
| Estimated Orders | 推算订单量 |
| Click Conversion Rate | 点击转化率 |
| Overall Click Conversion Rate | 综合点击转化率 |
| Keyword Click Coverage | 主要词点击覆盖率 |
| Market Search Click Rate | 市场搜索点击率 |
| Glossary / Terminology | 名词术语解释 |

## 关键词显示

- Amazon 搜索词必须保留英文原词，中文翻译紧跟其后，使用全角括号：`marble shelf（大理石置物架）`。
- 翻译表达消费者真实搜索意图；同一关键词在同一报告中保持一致。
- 语义有歧义时使用“关键词（中文暂译，语义待验证）”，不修改原始关键词、搜索量、点击份额或转化率。
- 表格、卡片、图表和正文均遵守该格式；不能只显示中文而删除英文原词。

## 证据状态

HTML 统一使用中文标签：`[数据支持]`、`[分析推断]`、`[待验证]`、`[证据不足]`、`[数据冲突]`、`[持续性待验证]`、`[样本有限]`。不得用 `Data Supported`、`Inference` 或 `Pending Validation` 作为主要展示标签。

## 生成前检查

逐项检查页首摘要、所有标题、卡片、表头、指标、结论、风险、图表标题、注释和页尾；发现可自然中文表达的英文就替换。检查关键词仍保留英文原词且紧跟中文翻译，必要英文缩写首次出现有中文说明。
