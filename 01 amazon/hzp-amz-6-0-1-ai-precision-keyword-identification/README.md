# HZP Amazon 6-0-1｜精准关键词识别

6-0-1（`hzp-amz-6-0-1-ai-precision-keyword-identification`）只负责从当前产品 ERP `PickPwKView` 识别人工精准词和 AI 独立精准词，并生成六列双轨 CSV；当 Own 关键词不足时，可从档案明确绑定的 Benchmark ERP 关键词建立候选池，但必须针对当前产品重新判断。精准泛词由 6-0-2 负责，广告执行由 6-3 负责。

运行 `6-0-1，Product_Code` 时，先从 `01_产品档案.md` 取得当前产品 ERP `ProId`，再读取档案中实际标注的对标 ERP 编号并分别参数化查询 `PickPwKView`。当前 ProId 与对标 ProId 始终分离；对标行只作为 Benchmark Evidence，不能把对标 `Tags` 或自然排名直接变成当前产品精准标签。人工路径只认当前产品完整 `Tags` 标签 `|1精准|`；AI 路径对当前产品全部有效 Keyword 盲分类，并可在规则允许的扩展模式中加入明确绑定的 Benchmark Keyword，统一按当前产品 Search Intent Fit 重新判断，不读取任何来源的 `Tags`、`IsExact` 或 `raw_fields`。AI 结果必须是 `PRECISION`、`NOT_PRECISION` 或 `REVIEW_REQUIRED` 三态；历史人工标签仅在盲分类完成后并入最终审计字段。

默认输出：

- `06_SKILL分析报告/6-0-1_精准关键词识别/6-0-1_[Product_Code]_手动分类精准词.csv`
- `06_SKILL分析报告/6-0-1_精准关键词识别/6-0-1_[Product_Code]_AI精准词.csv`

文件使用 UTF-8 with BOM，最终 CSV 严格包含 `自动编号`、`关键词`、`搜索量`、`中文名称`、`精准理由`、`精准度` 六列。`自动编号`必须来自 Schema 确认的稳定 ERP 记录 ID，可来自当前产品或明确绑定的 Benchmark；同一 Keyword 允许多条真实记录，同一 ID 只能出现一次。同一 ID 对应不同 Keyword 时标记 `[ERP_KEYWORD_RECORD_IDENTITY_CONFLICT]` 并阻止正常输出；无法确认真实 ID 的行不进入正常六列资产。AI 文件只保存 `PRECISION` 行，NOT_PRECISION 与 REVIEW_REQUIRED 不写入最终资产；不修改 ERP，不进入 0-2 正式报告索引。明确指定某一分类时才只生成对应 CSV；空结果保留表头且不写合成状态行。

内部模型仍保留产品画像匹配/冲突属性、Benchmark 与当前 Amazon 证据等追溯字段；最终 CSV 仅投影六列。`搜索量`只取 `SearchVolume30`，`中文名称`优先 `KeywordCn`；缺失写 `DATA_NOT_AVAILABLE`。`精准度`为 0–100 内部判断分数。对标编号缺失标记 `[BENCHMARK_ERP_PROID_NOT_AVAILABLE]`，自然排名字段缺失或 Schema 语义未确认标记 `[BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE]`。Benchmark 只提供候选和 Supporting Evidence，`Tags`/`|1精准|`/`IsExact` 不得泄漏到 AI 分类。6-0-2 默认读取 `6-0-1_[Product_Code]_AI精准词.csv`，先按 Keyword 去重，忽略`自动编号`参与聚类和搜索量计算。

AI 产品语义画像至少记录 `Core_Product_Type`、`Target_Customer`、`Core_Functions`、`Core_Use_Cases`、`Core_Attributes`、`Important_Differentiators`、`Compatible_Search_Intents`、`Incompatible_Search_Intents` 和 `Excluded_Product_Types`。证据不足或语义冲突进入 `REVIEW_REQUIRED`，不以历史人工标签替代 AI 判断。

精准判断固定为 `Product–Search Intent Fit`：先从真实产品资料建立语义画像，再理解买家意图并整体核对类型、对象、功能、场景、关系、属性/兼容性和排除条件。明确无法满足的 `Hard_Intent_Conflicts` 直接阻止 `PRECISION`；产品资料无法确认 Keyword 的关键要求时进入 `REVIEW_REQUIRED`。未指定产品类型可在核心购买意图匹配时保持精准，明确错误类型则拒绝。搜索量、广告指标、订单、自然排名、Benchmark 出现次数或标签都只是辅助证据，不能替代语义判断或固定加权。
