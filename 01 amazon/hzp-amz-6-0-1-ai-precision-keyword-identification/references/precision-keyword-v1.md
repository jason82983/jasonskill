# 6-0-1 V1 精准关键词识别规则

## 身份与查询

- `01_产品档案.md` 的 `ERP编号` 是唯一 `ERP_ProId` 来源；`Product_Code` 不能代替它。
- 复用共享 ERP Adapter，只执行参数化只读 `SELECT ... FROM PickPwKView WHERE ProId = ?`。
- ProId 缺失、冲突、Provider 不可用、字段语义未确认时，不伪造 CSV，保留对应状态。
- 产品档案中的当前 `ERP编号` 与明确标注的对标 ERP 编号分开维护；对标编号缺失时使用 `[BENCHMARK_ERP_PROID_NOT_AVAILABLE]`，不猜测或寻找类似产品。
- `Keyword` 是关键词文本；空值或清洗后为空的行丢弃。
- `IsExact` 当前定义为“暂无用”，始终不参与精准词判断。

## 两条分类路径

Manual Path 只筛当前产品 `ProId` 范围内 `Tags` 完整包含 `|1精准|` 的有效 Keyword。AI Blind Path 接收当前产品全部有效 Keyword、产品上下文、已经确认语义的质量字段和独立的 Benchmark Evidence，必须移除当前产品输入中的 `Tags`、`IsExact`、`raw_fields`，独立判断 Search Intent Fit。对标关键词、对标自然排名和对标标签只能提供证据，不能直接变成当前产品 Precision Label。AI 不使用词长或“长尾=精准”的替代规则。

默认一次查询同时生成：

- `6-0-1_[Product_Code]_手动分类精准词.csv`
- `6-0-1_[Product_Code]_AI精准词.csv`

保存到 `06_SKILL分析报告/6-0-1_精准关键词识别/`，UTF-8 with BOM。最终两份 CSV 严格只有 `自动编号`、`关键词`、`搜索量`、`中文名称`、`精准理由`、`精准度` 六列；AI 文件只保留 PRECISION 行，NOT_PRECISION/REVIEW_REQUIRED 不落盘。自动编号仅可使用 Schema 明确定义的稳定记录 ID；当前 `Id`/`KwId` 未确认，输出 `[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]`，不猜测。

AI CSV 同时记录 `Current_ERP_ProId`、`Product_Intent_Fit`、`Current_Product_ERP_Evidence`、`Benchmark_Count`、`Benchmark_Keyword_Coverage`、`Benchmark_Organic_Evidence`、`Best_Benchmark_Organic_Rank`、`Median_Benchmark_Organic_Rank`、`Evidence_Summary`。这些字段无可靠证据时写 `DATA_NOT_AVAILABLE`；RankOra/abarank 等字段未在 Schema 中明确为自然排名时写 `[BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE]`。

## Own First 与 Benchmark 候选池

- 默认先使用当前产品 `Current_ERP_ProId` 的完整可用关键词池。只有运行时基于覆盖度、核心 Search Intent 覆盖、字段完整度和产品成熟度判断当前池不足时，才启用明确绑定的 Benchmark ERP 关键词作为候选扩展；不使用固定条数阈值。
- 运行摘要必须标记 `OWN_ONLY`、`OWN_PLUS_BENCHMARK` 或 `BENCHMARK_FALLBACK`。当前产品无可用关键词且没有明确 Benchmark 时，状态为 `CURRENT_KEYWORDS_UNAVAILABLE_NO_BENCHMARK`，不得编造候选。
- Benchmark ERP ProId 只能来自 `01_产品档案.md` 或其他显式身份配置。不得按名称、ASIN、文件名或“相似产品”猜测；每个 Benchmark 通过参数化 `WHERE ProId = @Benchmark_ERP_ProId` 查询。
- Benchmark 词只属于候选/证据。`Tags`、`|1精准|`、`IsExact` 以及 Benchmark 的人工精准标签在 AI 盲视图中隐藏，不能直接成为当前产品 Precision Label；自然排名只有在 Schema 明确语义时作为辅助证据。
- 多个 Benchmark 的同义词按规范化 Keyword 去重用于一次 AI 语义判断，同时保留所有来源、覆盖度和自然排名证据。判断粒度是 `Current Product + Normalized Keyword`；最终 CSV 按真实 ERP Record ID 展开，同一 Keyword 可以有多条真实记录。
- 当前产品和明确绑定的 Benchmark 记录都可以保留各自真实 Record ID。Record ID 必须唯一对应 Keyword；同一 ID 对应不同 Keyword 时标记 `[ERP_KEYWORD_RECORD_IDENTITY_CONFLICT]`，不得进入正常输出。无法确认真实稳定 ID 的行标记 `[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]`，不得进入正常六列 CSV。
- 6-0-1 仅执行只读查询和 AI 分类，不执行 `INSERT`、`UPDATE`、`DELETE`。下游 6-0-3 以 Record ID + Keyword 双校验后按 ID 执行，不因该记录的 ProId 不同于当前分析产品而静默阻断。

## Product–Search Intent Fit 与 Hard Conflict

AI 先基于 `01_产品档案.md`、产品规格及必要的已批准资料建立画像，再理解 Keyword 的买家意图。画像字段按适用性包括：`Core_Product_Type`、`Target_Customer`、`Recipient`、`Core_Functions`、`Core_Use_Cases`、`Purchase_Occasions`、`Relationship_Intent`、`Core_Attributes`、`Important_Differentiators`、`Compatibility`、`Compatible_Search_Intents`、`Incompatible_Search_Intents`、`Excluded_Product_Types`、`Hard_Intent_Conflicts`。不允许用 Keyword 文本反向创造产品属性。

判断维度用于整体理解，不是固定加权模型。若资料明确产品不能满足 Keyword 的关键购买要求，形成 Hard Intent Conflict，直接 `NOT_PRECISION`；典型冲突包括错误产品类型、核心功能、兼容型号、安装方式、礼赠对象/关系以及关键材质、尺寸、颜色或防护属性。Keyword 未指定类型时不构成冲突；明确指定错误类型才阻止精准。产品资料无法确认关键要求时为 `REVIEW_REQUIRED`，当前 V1 不输出。

`SearchVolume30`、CPC、ACoS、CVR、订单、自然排名和 Benchmark 覆盖只保留为辅助证据。它们不改变 Precision，也不等同于 Advertising/Commercial Value；精准理由必须写明 Search Intent 与当前产品如何匹配。Benchmark `Tags`/`IsExact` 和多 Benchmark 数量不能投票决定精准。结构化调用方可用 `evaluate_product_search_intent_fit` 做硬冲突/未知护栏，但不执行 SQL 写入。

## 比较与边界

AI 对每个有效词输出 `PRECISION`、`NOT_PRECISION` 或 `REVIEW_REQUIRED`。盲分类完成后，才通过 `Product_Code + ERP_ProId + Keyword` 与人工标签形成内部对照状态；最终 AI CSV 只保留 PRECISION。差异只进入 Canonical Model/报告，不修改 ERP Tags。6-0-1 不生成精准泛词；精准泛词由 `hzp-amz-6-0-2-precision-broad-extraction` 接管。

真实精准结果为 0 时，CSV 保留 BOM 表头且不写合成状态行；失败状态不得伪装成 0 结果。
