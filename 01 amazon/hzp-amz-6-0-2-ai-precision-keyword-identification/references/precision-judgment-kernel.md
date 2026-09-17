# 6-0-2 Precision Judgment Kernel

这是 6-0-2 的唯一精准判断内核。它替换“产品类型词出现得越完整，精准度越高”的旧判断方式；输入、输出、Record ID、Coverage Check、文件路径和下游边界不变。

## Product Purchase Driver（同一 Run 只识别一次）

基于 Current Product Ground Truth 先识别一次 `PrimaryPurchaseDriver`：`FUNCTIONAL`、`COMPATIBILITY`、`GIFT_EMOTIONAL`、`AESTHETIC_DECOR`、`OCCASION` 或 `HYBRID`，并记录可验证的 `SecondaryPurchaseDrivers` 与 `PurchaseDriverReason`。每个 Keyword 不得重新判断 Product Driver。若 Ground Truth 不足，保持 `DATA_NOT_AVAILABLE`，不得从关键词反推产品驱动。

## 固定判断顺序

1. **先独立还原 Searcher Intent**：记录 purchase goal、显式商品类型、recipient/relationship、occasion、required attributes、quantity、material、feature、theme 和其他 hard modifiers。先回答消费者想买什么，再读取当前产品事实进行比较。
2. **确认 Product Purchase Driver**：按 Driver 选择主要 Evidence。`FUNCTIONAL` 看 Product Type、Core Function、Use Case、Target Object、Installation、Critical Feature；`COMPATIBILITY` 看 Compatible Object、Model、Size、Interface、Installation、Required Specification；`GIFT_EMOTIONAL` 看 Gift Mission、Recipient、Relationship、Occasion、Message/Emotion、Product Suitability；`AESTHETIC_DECOR` 看 Decor Object、Style、Theme、Placement/Scene、Visual Expectation 和明确 Material/Size；`OCCASION` 看 Occasion、Recipient、Use Context、Timing、Purchase Mission；`HYBRID` 先识别 Primary/Secondary，不做机械平均。
3. **识别 Search Mode**：PRODUCT-LED、GIFT-LED、BROAD-GIFT、RELATIONSHIP-ONLY、HARD-SPECIFIED。Gift-led 查询不要求出现 figurine/statue/decor 等产品类型词。
4. **区分 CORE FIT 与 CAN SERVE**：当前产品本身围绕该关系/礼物购买目的设计时是 CORE FIT；只是众多可送礼答案之一时是 CAN SERVE。
5. **检查所有 Hard Modifiers**：商品类型、材质、数量/人物表达、个性化、兼容性、尺寸、功能和主题要求逐项核对。任何明确冲突都否决“高度精准”，商品类型冲突通常为“不精准”。
6. **Benchmark 自然排名只作 Market Reality Evidence**：不得用排名升降精准等级。
7. **反事实检查**：把产品放到该词搜索结果第一页，买家是否会自然认为它就是本次要买的商品？若只是“也能当礼物”，属于 CAN SERVE。
8. **直接裁决四级**：高度精准、精准、弱精准、不精准；禁止数学评分、固定权重、词数阈值和硬编码词表。

## 关系型礼物边界

当前产品若已确认是 Sister/Friendship relationship keepsake gift，则 `sister birthday gifts`、`gift for sister`、`best friend gifts for women`、`friendship gifts for women` 可以是高度精准，即使没有写 figurine。SERP 中出现首饰、杯子、摆件、相框、蜡烛或毯子等不同物理商品，不能单独作为降级理由。`sister` 只有 Relationship 而 Gift Mission 不明确时不能自动判高度精准；`birthday gifts for women`、`gift for women` 通常是弱精准；`gift` 不精准。以上是 B2 校准样本，不得按完整字符串硬编码到程序。

`GIFT_EMOTIONAL` 的结构化 Evidence 至少记录 `GiftIntentPresent`、`GiftMissionFit`（Golden Case 中可别名为 `PurchaseMissionFit`）、`RecipientFit`、`RelationshipFit`、`OccasionFit`、`EmotionalMessageFit`，取 `HIGH/MEDIUM/LOW/NOT_SPECIFIED/CONFLICT`。这些是证据，不得机械加权求分。高度精准要求明确 Gift Purchase、核心 Recipient/Relationship/Occasion 与产品定位高度匹配、产品真实围绕该 Gift Mission 设计、无关键 Hard Conflict 且 Purchase Mission Convergence 足够高。

内部区分 `PhysicalProductConvergence`、`PurchaseMissionConvergence` 和适用时的 `CompatibilityConvergence`。`FUNCTIONAL` 通常更看物理产品与功能收敛，`GIFT_EMOTIONAL` 更看 Purchase Mission，`COMPATIBILITY` 更看 Compatibility；禁止固定数学权重。

## Modifier 反例

`3 sisters figurine` 在产品只有两个人物时存在 representation/quantity conflict；`wooden sisters figurine` 在产品为 resin 时存在 material conflict；`sister birthday card` 是 product-type conflict；不支持个性化的产品不能接受 `personalized gifts for women`。不得由 sister + figurine 自动通过，也不得由 gift 未写产品类型自动降级。

Decision Challenge 必须在 Final 前检查：是否把 SERP 物理商品形态多错误理解为 Gift Intent 不精准；是否针对当前 Driver 使用了错误主要维度；Gift 的 Recipient/Relationship/Occasion/Gift Mission 是否高度匹配；产品是否真实围绕该 Gift Mission 设计；是否让 Physical Product Convergence 凌驾于 Purchase Mission Convergence；是否仅因出现 gift/sister/women 就过度高估。Hard Conflict 仍然优先，Purchase Driver 不能覆盖个性化或安装方式冲突。结果只能为 `CONFIRMED`、`DOWNGRADED`、`UPGRADED`、`RECONSIDERED_NO_CHANGE`。

每条结果的理由必须用 1–2 句话说明搜索者主要想买什么，以及当前产品是 CORE FIT、CAN SERVE 还是发生冲突；Gift 高度精准理由必须说明 Gift Mission、Recipient/Relationship/Occasion 与产品核心定位的匹配，不得写成“包含 sister 和 gift，所以高度精准”。不得批量复制同一句理由。`REVIEW_REQUIRED` 只作为内部证据不足状态，正式 CSV 仍使用四级之一。

## Precision Brain 增量硬契约

精准度判断对象是“搜索者是否正在寻找 Current Product 这种具体产品/解决方案”，不是一般语义相关性。必须区分 `RELEVANCE`、`SEMANTIC SIMILARITY`、`BENCHMARK ORGANIC RANK`、`SEARCH VOLUME` 与 `PURCHASE INTENT PRECISION`。

每个 Canonical Keyword 只判断一次，按以下顺序形成可审计记录：Search Intent → Shopping Intent Strength → Intent Convergence → Product–Intent Fit → Hard Conflict → Initial Precision → Benchmark Reality Check → Decision Challenge → Final Precision。Keyword 未表达的字段保持 UNKNOWN/NOT_SPECIFIED，不得补造。

Initial Precision 不读取排名；Benchmark 只作为 SUPPORTS、WEAKLY_SUPPORTS、NEUTRAL、CONTRADICTS 或 INSUFFICIENT 的 Reality Evidence，不能覆盖 Hard Conflict、投票决定等级或因排名好而自动升高。Final Reason 必须说明搜索者主要想买什么、意图是否收敛、产品如何匹配、是否存在冲突以及 Benchmark 的实际作用。

Decision Challenge 必须检查：是否把相关误当精准、是否只是宽泛 Category/Occasion/Recipient 词、购物意图是否不明确、是否存在 Hard Conflict、是否被多个 Benchmark 或排名锚定、去掉 Benchmark 后方向是否仍成立。Challenge 结果只能为 CONFIRMED、DOWNGRADED、UPGRADED、RECONSIDERED_NO_CHANGE。

内部 Judgment Record 至少保留 PrimaryPurchaseDriver、SecondaryPurchaseDrivers、PurchaseDriverReason、SearcherPrimaryIntent、ShoppingIntentStrength、IntentConvergence、ExpectedProductType、ExpectedCoreFunction、ExpectedRecipient、ExpectedOccasion、ExpectedInstallationMethod、ExpectedCriticalAttributes、HardConflictType、InitialPrecision、BenchmarkRealityAssessment、ChallengeResult、FinalPrecisionReason，以及上述 Gift/Convergence Evidence；这些是业务证据，不是隐藏思维链。

Batch 必须按模型上下文、Profile 长度、字段数量、历史截断/校验失败自适应规划；每个词使用稳定 JudgmentItemId 按 ID Join，失败时缩小批次重试，禁止静默接受缺字段或位置错配。任何 Precision Brain 修改必须运行 Golden Regression，并报告 `ExactPrecisionMatch`、`MismatchCount`、`FalseHighPrecision`、`HighPrecisionRecall`、`GiftHighMissionFitRecall`、`FalseHighPrecisionRate`、`BroadGiftFalseHighPrecisionRate`，同时检查 Grade Compression。
