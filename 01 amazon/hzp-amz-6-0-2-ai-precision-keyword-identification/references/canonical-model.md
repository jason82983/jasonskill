# 6-0-2 Canonical Model

## 来源

唯一正式输入是两个资产：当前 Product Root 下完整读取的 `05_分析源数据/01_产品数据/本产品/产品识别 - 文本文案.txt`（`CURRENT_PRODUCT_TEXT_EVIDENCE`），以及最新有效 6-0-1 Run Package 的 `BENCHMARK_KEYWORD_ALL_OBSERVATIONS` asset（Observation 含 `Id,词,中文,市场容量,竞争产品数,供需比,对标编号,对标ASIN,自然排名,ASIN,产品编号`）。产品文本缺失、为空或不可读时分别返回 `CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND`、`CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY`、`CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED`；6-0-1 缺失返回 `6-0-1_KEYWORD_INPUT_NOT_FOUND`。运行时不查询 ERP、Amazon，也不按关键词文本反查。

## 证据上下文

Runtime 完整读取并记录产品识别文本路径和内容；它不从关键词反推产品事实。6-0-1 all-observation CSV 是唯一 Keyword Candidate 输入。按 Canonical Keyword 聚合成一次 AI 判断单位；市场容量与排名仅供 Reality Evidence/输出，竞争产品数和供需比仅作直通数据，不参与精准裁决。A/B 回填每条观察，C 输出唯一高精准关键词。

## 每条记录

`Id` 是 6-0-1 的原始记录身份，必须原样保留。AI 先独立解释 Searcher Intent，再用一次性的 Current Product Understanding 判断 Product–Search Intent Fit、Query Specificity 与 Hard Conflict；这些维度不是固定评分表。每条记录提供四级精准度标签（高度精准、精准、弱精准、不精准）及简短逐词理由；AI直接裁决标签，不计算或映射0–100分。Benchmark rank 只属于辅助现实校验。

Search Mode 先区分 PRODUCT-LED、GIFT-LED、BROAD-GIFT、RELATIONSHIP-ONLY、HARD-SPECIFIED。Gift-led 关系礼物不因缺少 figurine/statue 词而自动降级；必须判断当前产品是否是 CORE FIT，还是只能 CAN SERVE。商品类型、材质、数量/人物表达、个性化、兼容性、尺寸、功能和主题等明确 modifier 具有否决/降级权。

Gift、关系、人群、节日和场景词必须先检查商品类型是否收敛；“可以送给某人”不等于“正在寻找该商品”。Hard Requirement Conflict 优先于局部语义相关。

## 完整性

输入每条有效记录均须输出。Coverage Check 比较 Id 多重集合；INPUT_RECORD_COUNT 必须等于 OUTPUT_RECORD_COUNT。不得因证据不足跳过记录。内部可记录 REVIEW_REQUIRED，但正式 CSV 的“精准度”必须是四级标签之一。

## 输出

6-0-2 将三张公共表和每个所属产品编号一张 D 表写入 `06_SKILL分析报告/6-0-2_AI精准关键词识别/`，不创建时间戳子文件夹。所有表与清单使用同一 `RUN_TIMESTAMP`：

1. `6-0-2_精准判断所有词表_{RUN_TIMESTAMP}.csv`：每条 Benchmark × Keyword observation 一行，Schema 为 `所属产品编号,对标ASIN,Id,词,中文,市场容量,竞争产品数,供需比,自然排名,精准度,精准原因`。
2. `6-0-2_高度精准词表_{RUN_TIMESTAMP}.csv`：A 中 `精准度 == 高度精准` 的严格筛选结果，保留 observation 粒度。
3. `6-0-2_去对标去重 高度精准词_{RUN_TIMESTAMP}.csv`：从 B 按 Canonical Keyword 汇总唯一行，Schema 为 `Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准度,精准原因`，不含 Benchmark 身份字段，供 603 使用。
4. 每个 source `所属产品编号` 一张 `6-0-2_{所属产品编号}_高度精准词_{RUN_TIMESTAMP}.csv`：从 B 按所属产品编号筛选，保留 A/B Schema，供 606 使用；每张表内部 Canonical Keyword 唯一。

一次 Run 的 3+N 表与 `run_manifest_{RUN_TIMESTAMP}.json` 位于同一固定报告根目录；Manifest 与所有文件通过相同 `RUN_TIMESTAMP` 绑定。A/B 每个 observation 的判断相同；C 仅保留一次市场事实，排名与覆盖值只用于 Reality Evidence。校验预期 Benchmark 文件数、D表身份和覆盖数完整通过后才将 Run Manifest 标记为 `VALID`。6-0-2 不生成手动精准 CSV；历史手动文件不由本 Skill 改写。
