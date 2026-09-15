---
name: hzp-amz-6-0-1-ai-precision-keyword-identification
description: 从当前产品 ERP PickPwKView 数据中识别人工与 AI 精准关键词，生成六列双轨 CSV 资产；不负责精准泛词、关键词族或广告写操作。
metadata:
  short-description: 精准关键词识别与双轨数据资产生成
---

# HZP Amazon 6-0-1｜精准关键词识别

## 定位

6-0-1 只负责“精准词识别与数据资产生成”。它从当前产品的 ERP `PickPwKView` 结果中分别提取人工标记精准词和 AI 独立判断精准词，保留当前产品证据，并可用明确配置的 Benchmark ERP Evidence 辅助 AI 判断。

精准泛词提取由 `hzp-amz-6-0-2-precision-broad-extraction` 负责；关键词族、排名经营和广告执行不属于 6-0-1。

## 职责边界

- 6-1 可读取 6-0-1 的精准词 CSV 作为 Launch 关键词证据。
- 6-2 只识别 ASIN 经营异常或机会，需要精准词识别时路由 6-0-1，需要泛词/关键词族时路由 6-0-2。
- 6-3 负责广告 Campaign、Keyword、Target、Bid、Budget、Placement 的执行和验证，并读取 6-0-1/6-0-2 资产。
- 6-0-1 负责 ERP 身份确认、一次取数、Manual/AI 双轨分类、证据字段保留和差异比较。
- 6-0-2 负责从 6-0-1 CSV 生成精准泛词；如需把 AI 精准词的真实记录编号受限追加到 ERP `Tags`，由独立的 `hzp-amz-6-0-3-ai-precision-keyword-erp-sync` 接管，6-0-1 本身不写 ERP。

6-0-1 只读 ERP、当前产品资料和必要的字段字典；禁止 `apply_change_plan`、广告写操作、ERP 写入、修改历史报告、跨产品取词、commit 或 push。

## 运行身份与数据源

支持短命令：`6-0-1，Product_Code`，例如 `6-0-1，B2`。先固定当前 Product Root，读取 `01_产品档案.md` 的真实 `ERP编号` 作为 `ERP_ProId`。`Product_Code` 不得替代 `ProId`，缺失或冲突分别标记 `[ERP_PROID_MISSING]`、`[ERP_PROID_CONFLICT]`。

### 关键词候选池与 Benchmark 回退

6-0-1 采用 `Own Product Keywords First`：先查询当前产品 `Current_ERP_ProId` 的 `PickPwKView` 关键词，再读取产品档案中明确绑定的 `Benchmark ERP Product ID` 作为候选补充。当前产品关键词为零且存在明确 Benchmark 时进入 `BENCHMARK_FALLBACK`；当前产品已有词但覆盖或核心 Search Intent 明显不足时进入 `OWN_PLUS_BENCHMARK`；证据足够时保持 `OWN_ONLY`。是否“不足”由当前覆盖、产品核心意图覆盖、数据完整度和产品成熟度综合判断，不使用固定词数阈值；无 Benchmark 时明确保留数据不足状态。

Benchmark 只能提供 Candidate，必须经过当前产品的 `Product–Search Intent Fit` 重新分类。Benchmark 的 `Tags`、`|1精准|`、`IsExact` 和自然排名不能直接成为当前产品 Precision Label；AI Blind View 必须屏蔽这些标签。相同 Keyword 的多个 Benchmark 证据先归一化去重，但保留多来源覆盖和已确认的自然排名 Evidence，不采用投票规则。AI 判断按 `Current Product + Normalized Keyword` 去重；最终 CSV 按真实 ERP PickPwK Record ID 展开。因此当前产品与明确绑定的 Benchmark 记录都可以保留各自真实 ID；记录身份必须与 Keyword 一一对应，同一 ID 不得重复，同一 ID 对应不同 Keyword 时标记 `[ERP_KEYWORD_RECORD_IDENTITY_CONFLICT]` 并阻止正常输出。无法取得真实稳定 ID 的候选标记 `[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]`，不进入正常六列 CSV，也不在 6-0-1 中 INSERT/UPDATE/DELETE PickPwK。
当前产品关键词为空且没有明确 Benchmark 时，运行摘要标记 `CURRENT_KEYWORDS_UNAVAILABLE_NO_BENCHMARK`，不生成合成候选。

运行摘要可报告 `Keyword Source Mode`、Own/Benchmark/去重候选数、AI Precision 数量及“Benchmark 精准候选但当前 ERP 无记录”数量；这些来源字段不进入六列最终 CSV。

正式关键词数据唯一来自 SQL Server `Amazon.dbo.PickPwKView`，使用参数化只读查询：

```sql
SELECT ... FROM PickPwKView WHERE ProId = @ERP_ProId
```

字段语义必须读取公共配置 `erp-amazon-pickpwkview-schema.md`；未确认语义的字段只能保留为证据，不能用于重要判断。`IsExact` 当前定义为“暂无用”，严禁用于 ERP 精准词判定。

### Benchmark Evidence

先从同一份 `01_产品档案.md` 读取当前 `ERP编号`，再读取档案中实际存在且明确标注的“对标 ERP 产品编号”字段（当前样例字段为 `对标ERP产品编号`）。当前值只能进入 `Current_ERP_ProId`；每一个明确的对标值单独进入 `Benchmark_ERP_ProIds[]`，不得根据 ASIN、名称、角色或相似产品猜测。

对每个 `Benchmark_ERP_ProId`，通过共享 ERP Adapter 的 Benchmark Evidence 入口分别参数化查询 `PickPwKView WHERE ProId = ?`。这些行只作为 `Benchmark Evidence`，不得混入当前产品关键词集合，也不得把对标 `Tags` 的 `|1精准|` 直接复制为当前产品 AI 精准结论。对标关键词覆盖度、多对标一致性和对标自然排名只能辅助 `Product–Search Intent Fit`；自然排名不是 Precision Label。

`RankOra`、`abarank` 等字段只有在 `03_系统配置/erp-amazon-pickpwkview-schema.md` 明确标记为自然排名语义时才能进入 `Benchmark_Organic_Evidence`。字段缺失或语义未确认时必须写 `[BENCHMARK_ORGANIC_RANK_NOT_AVAILABLE]`，不得按排名区间机械判定。

对标 ERP 编号缺失不阻止当前产品 6-0-1，AI CSV 的对标字段写 `[BENCHMARK_ERP_PROID_NOT_AVAILABLE]` 或 `DATA_NOT_AVAILABLE`。当前产品自身 ERP/Search Term/转化证据逐步优先于 Benchmark Evidence。

AI 判断输入优先使用当前产品语义画像、当前产品全部 ERP 关键词及已确认指标，再综合多个 Benchmark 的关键词覆盖、相似度、自然排名证据和当前 Amazon Search Term/转化证据（如有）；多 Benchmark 不是简单投票，不能使用“排名 1–10 即精准”等机械规则。

## 双轨精准词 CSV

默认 `6-0-1，Product_Code` 对当前 `ProId` 的全部有效行只查询一次，再在内存中分两条路径：

- **手动分类精准词**：`Tags` 完整包含 `|1精准|` 且 `Keyword` 非空；`IsExact` 不参与。
- **AI 精准词**：对全部有效 `Keyword` 独立进行产品语义判断。AI 输入必须移除 `Tags`、`IsExact` 和 `raw_fields`，只能使用产品语义画像、Keyword 语义、已确认质量字段、Benchmark Evidence 及可靠的当前 Amazon 证据。历史 `|1精准|` 只是人工对照证据，不是 AI 前置条件。内部仍可保留三态判断，但最终文件只保留 `PRECISION`。

默认直接生成两份 UTF-8 with BOM CSV：

```text
[Product Root]/06_SKILL分析报告/6-0-1_精准关键词识别/6-0-1_[Product_Code]_手动分类精准词.csv
[Product Root]/06_SKILL分析报告/6-0-1_精准关键词识别/6-0-1_[Product_Code]_AI精准词.csv
```

最终两份 CSV 严格只含六列：`自动编号`、`关键词`、`搜索量`、`中文名称`、`精准理由`、`精准度`。`搜索量`只取经 Schema 确认的 `SearchVolume30`，缺失写 `DATA_NOT_AVAILABLE`；中文名称优先 `KeywordCn`，缺失时可用明确翻译，否则写 `DATA_NOT_AVAILABLE`。`精准度`为 0–100 的内部判断分数，不是转化率或成交概率。`自动编号`只能来自 Schema 明确定义的稳定 ERP 记录 ID，可来自当前产品或明确绑定的 Benchmark；不得使用行号、Keyword 文本或伪造值。AI 文件只保存 `PRECISION` 行，`NOT_PRECISION` 与 `REVIEW_REQUIRED` 不写入最终 CSV、不生成 Review Queue。内部证据模型仍可保留完整追溯字段，但不得混入最终 CSV。

AI 先建立真实产品语义画像（`Core_Product_Type`、`Target_Customer`、`Core_Functions`、`Core_Use_Cases`、`Core_Attributes`、`Important_Differentiators`、`Compatible_Search_Intents`、`Incompatible_Search_Intents`、`Excluded_Product_Types`，以及真实适用的礼赠对象、关系、风格、材质、尺寸、颜色、室内/室外、年龄、性别、宠物、安装和兼容性），再结合当前产品、多个 Benchmark 和可靠 Amazon 证据判断。证据不足、语义冲突或无法确认字段时进入 `REVIEW_REQUIRED`，不编造结论；只有人工复核后明确改为 `PRECISION` 的行才可进入下游策略。

### Product–Search Intent Fit 判断引擎

AI 必须先从已核验的产品资料建立 `Current Product Semantic Profile`，再解析 Keyword 的实际 Search Intent，整体比较 Product Type、Target Customer/Recipient、Function、Use Case/Occasion、Relationship、Core Attribute/Compatibility 和 Exclusion。`build_product_semantic_profile` 只复制调用方提供的真实字段，不从 Keyword 反推产品属性；字段缺失保持 `DATA_NOT_AVAILABLE`。

`Hard_Intent_Conflicts` 是否决护栏：当产品资料明确证明 Keyword 的重要要求无法满足时（产品类型、核心功能、兼容性、安装方式、关系/礼赠对象或关键材质/尺寸/颜色等），直接判 `NOT_PRECISION`。若 Keyword 明确要求某属性而产品资料无法确认，判 `REVIEW_REQUIRED`；未指定具体产品类型不构成冲突，明确指定错误类型才构成冲突。该判断是整体语义理解，不使用固定维度加权或词长规则。

搜索量、CPC、ACoS、CVR、订单、排名、Benchmark 出现次数及标签只能作为 Supporting Evidence，不能改变 Semantic Fit；Semantic Fit 与 Performance/Commercial Fit 分开。`evaluate_product_search_intent_fit` 只在调用方提供结构化 Search Intent 时对明确硬冲突或未知关键属性进行保守拦截，不会因广告表现自动升级或降级语义结论。精准理由必须说明核心购买意图如何匹配，不能只写“相关”或引用搜索量/排名。

明确指定 `手动分类精准词` 或 `AI精准词` 时只运行对应路径；未指定时默认两套都生成。真实精准结果为 0 时保留六列表头且不写合成状态行；Provider、身份或字段语义失败时不得伪造结果，一条路径失败可保留另一条成功结果并报告失败状态。

人工与 AI 通过 `Product_Code + ERP_ProId + Keyword` 比较，状态可为 `BOTH_PRECISION`、`MANUAL_ONLY`、`AI_ONLY`、`BOTH_NOT_PRECISION`、`REVIEW_REQUIRED`。人工只看当前产品 `Tags` 完整包含 `|1精准|` 的行；AI 盲分类后才合并历史标签用于审计，不生成第三个强制 CSV，也不修改 ERP `Tags`。6-0-2 默认只读取 AI CSV 且只接收 `AI_Classification=PRECISION`，`REVIEW_REQUIRED` 不进入关键词族或精准泛词。

AI CSV 的 Benchmark 证据字段至少包括 `Benchmark_Count` 与 `Benchmark_Organic_Evidence`。

手动 CSV 同样只输出上述六列；人工来源仍严格限定为当前产品 `Tags` 完整包含 `|1精准|` 的行，内部审计信息不写入最终文件。若稳定记录 ID 未由 Schema 确认，`自动编号`写 `[ERP_KEYWORD_RECORD_ID_UNCONFIRMED]`。

## 输出边界

6-0-1 的结构化资产只包括上述双轨 CSV、身份/字段/源行数/失败状态和人工 vs AI 差异。6-0-1 不生成或维护精准泛词、Broad Seed、Search Intent Cluster、关键词族、关键词生命周期、Rankability 或广告扩展策略；这些交给 6-0-2 或 6-3。

如现有运行链仍生成正式 HTML，HTML 只能记录本次输入版本、ProId、双轨结果和差异，不得继续承担 6-0-2 的策略分析。正式 HTML（如生成）仍保存于 `06_SKILL分析报告/` 根目录并按现有规则调用 0-2，双轨 CSV 不进入 0-2 索引。

详细字段契约见 [references/precision-keyword-v1.md](references/precision-keyword-v1.md)，CSV 代码见 `scripts/dual_precision_csv.py`。
