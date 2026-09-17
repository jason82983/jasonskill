# HZP Amazon 6-0-3｜精准泛词提取 / Search Intent Market Map

`hzp-amz-6-0-3-precision-broad-extraction` 只消费 6-0-2 正式 C 资产：
`6-0-2_去重去对标后 筛选后的精准词表_YYYYMMDD_HHMMSS.csv`。解析当前产品的
`06_SKILL分析报告/6-0-2_AI精准关键词识别/data/`，按文件名时间戳取最大值（filename timestamp）并做最小
Schema 校验；不把 RunPackage、Manifest、sidecar 或文件修改时间作为上下游前置条件。

输入必须满足“一条 Canonical Keyword 一行”。A/B/D（包括“精准判断所有词表”和“筛选后的精准词表”）不参与603 Intent输入。重复 Canonical Keyword 返回
`INPUT_NOT_UNIQUE`，603 不静默再去重，也不重新判断精准度、查询 ERP、处理 Benchmark
重复或执行广告写操作。当前产品资料只用于理解 Purchase Driver 和搜索任务；优先复用
602 已形成的产品语义证据。

Intent Brain 分两阶段运行：Phase A 为每个关键词形成 Keyword Semantic Unit；Phase B
基于这些单位全局合并同义购买任务、分配唯一 Primary Intent，并构建最多一个直接 Parent。
大数据可分批，但必须 Global Reconciliation，不能把各批次树直接拼接。关系、场景、产品类型、
兼容性等维度按当前产品的 Primary Purchase Driver 判断；字符串包含、词长和公共词根不能单独
决定同Intent或父子关系。每个关键词保留 `IntentAssignmentReason`、`ChallengeResult` 和
`ChallengeReasonSummary`，但不暴露隐藏推理过程。

## 输出

正式输出写入 `06_SKILL分析报告/6-0-3_精准泛词提取/data/`，文件名带
`YYYYMMDD_HHMMSS`；历史批次保留在 `历史数据/`，HTML（如生成）遵循公共报告归档规则。

**B：`6-0-3_词对应的精准泛词_{timestamp}.csv`（Ground Truth）**

固定字段：

`Id｜词｜中文｜市场容量｜竞争产品数｜供需比｜自然排名｜精准泛词｜精准泛词中文｜PrimaryIntentId｜PrimaryIntentCode｜KeywordPurchaseMission｜Intent层级｜ParentIntentId｜父精准泛词｜IntentAssignmentReason｜ChallengeResult｜ChallengeReasonSummary`

每个输入 Id 只出现一行，且只归属一个 Primary Intent。

**A：`6-0-3_精准泛词汇总_{timestamp}.csv`（由 B 程序聚合）**

固定字段：

`精准泛词｜中文｜层级｜父精准泛词｜直接搜索量｜汇总搜索量｜平均竞品数｜意图机会比｜直接对应词数｜IntentId｜IntentCode｜IntentDefinition｜PrimaryPurchaseDriver｜ChallengeStatus｜ChallengeReasonSummary`

直接搜索量、父/子 Subtree 汇总、平均竞品数、意图机会比及市场容量对账全部由程序计算；
不求和竞品数、不平均子节点比值、不把父子汇总跨层相加。所有 Primary Intent 的直接搜索量
必须与输入市场容量对账，否则返回 `MARKET_VOLUME_RECONCILIATION_FAILED`。

稳定 Intent 身份优先复用既有 Registry；当前没有 Registry 时使用由 Canonical Intent
Identity 派生的稳定标识，禁止按本次运行顺序生成 `INTENT_001` 造成漂移。

606 通过 603 的 `data/` 读取统一 Intent Map 观察多对标自然占领；6-1 读取 A、B 及可用
606 Reality Evidence 制定广告作战计划。603 只提供 Search Intent 市场结构，不输出广告决策。
