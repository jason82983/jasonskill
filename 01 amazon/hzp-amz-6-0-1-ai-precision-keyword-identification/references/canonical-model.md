# 6-0-1 精准关键词 Canonical Model

6-0-1 只保留用于身份、双轨分类和证据追溯的最小模型。没有真实数据的字段写 `NULL` 或 `DATA_NOT_AVAILABLE`，不以推断填充。

| 字段 | 用途 |
|---|---|
| Product_Code / ERP_ProId | 产品身份与 SQL 范围 |
| Current_ERP_ProId / Benchmark_ERP_ProIds | 当前产品与明确配置的对标产品身份边界；对标值不得替代当前值 |
| Keyword / KeywordCn | ERP 关键词原文与中文 |
| Source / Manual_Is_Precision / AI_Is_Precision | 人工路径、AI 路径与分类结果 |
| AI_Confidence / AI_Reason / Search_Intent / Precision_Type | AI 分类解释；不形成完整关键词族 |
| Product_Intent_Fit / Current_Product_ERP_Evidence | 当前产品搜索意图匹配与当前 ERP 证据 |
| Benchmark_Count / Benchmark_Keyword_Coverage / Benchmark_Organic_Evidence | 对标关键词覆盖和可用的自然排名证据；仅作辅助证据 |
| Best_Benchmark_Organic_Rank / Median_Benchmark_Organic_Rank / Evidence_Summary | 对标自然排名摘要与证据追溯；语义不明时写不可用状态 |
| AI_Classification | `PRECISION`、`NOT_PRECISION`、`REVIEW_REQUIRED` |
| Manual_Precision_Label | AI 盲分类后合并的历史 `Tags` 标签 |
| Comparison_Status | `BOTH_PRECISION`、`MANUAL_ONLY`、`AI_ONLY`、`BOTH_NOT_PRECISION`、`REVIEW_REQUIRED` |
| 已确认的 PickPwKView 质量字段 | 只保留字段字典中已确认语义的证据 |
| Provider / Source_Grain / Metric_Semantics / Data_Through / Freshness | 可追溯元数据 |

Manual 精准路径只认当前产品 `ProId` 范围内完整 `Tags` 标签 `|1精准|`，`IsExact` 不参与。AI Blind 输入不得包含当前产品或 Benchmark 的 `Tags`、`IsExact` 或 `raw_fields`。Benchmark 关键词与对标 `|1精准|` 只能作为独立 Evidence；AI 若基于当前产品 Search Intent Fit 独立判定为 Precision，可以保留该 Benchmark 记录的真实 Record ID，不能继承其标签。自然排名只有在 Schema 明确语义时才可摘要，否则写 `[BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE]`。Search Intent 只用于解释 AI 判断，不在 6-0-1 生成 Cluster、Broad Seed、生命周期、Rankability 或广告动作；这些对象由 6-0-2/6-3 负责。

最终对外 CSV 由内部模型投影为六列：`自动编号`、`关键词`、`搜索量`（仅 `SearchVolume30`）、`中文名称`（优先 `KeywordCn`）、`精准理由`、`精准度`（0–100 内部判断分数）。自动编号必须是 Schema 确认的稳定 ERP 记录 ID；当前 `Id`/`KwId` 未确认时写 `[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]`。AI 最终 CSV 只包含 `PRECISION`，其余状态仅留在内部审计数据。

## Product–Search Intent Fit

AI 判断先建立由真实产品资料提供的 `Current Product Semantic Profile`，至少按适用性维护 `Core_Product_Type`、`Target_Customer`、`Recipient`、`Core_Functions`、`Core_Use_Cases`、`Purchase_Occasions`、`Relationship_Intent`、`Core_Attributes`、`Important_Differentiators`、`Compatibility`、`Compatible_Search_Intents`、`Incompatible_Search_Intents`、`Excluded_Product_Types` 和 `Hard_Intent_Conflicts`。画像缺失字段不从 Keyword 反推。

分类采用整体语义判断而非固定权重。明确的 Hard Intent Conflict（产品类型、功能、兼容性、安装方式、关系/对象或关键属性）直接返回 `NOT_PRECISION`；关键要求未知返回 `REVIEW_REQUIRED`。未指定类型与指定错误类型必须区分。Volume、广告表现、订单、Rank、Benchmark 计数和标签只能作为 Supporting Evidence；Benchmark `Tags`/`IsExact` 永不继承。`evaluate_product_search_intent_fit` 只提供保守冲突护栏，最终 CSV 仍仅保留 `PRECISION`。
