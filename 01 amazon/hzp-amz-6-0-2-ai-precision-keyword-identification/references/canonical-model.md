# 6-0-2 Canonical Model

## 来源

唯一正式输入是两个资产：当前 Product Root 下完整读取的 `05_分析源数据/01_产品数据/本产品/产品识别 - 文本文案.txt`（`CURRENT_PRODUCT_TEXT_EVIDENCE`），以及最新有效的 6-0-1 正式 CSV（契约为 `Id,词,中文,市场容量,竞争产品数,供需比,自然排名`）。产品文本缺失、为空或不可读时分别返回 `CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND`、`CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY`、`CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED`；6-0-1 缺失返回 `6-0-1_KEYWORD_INPUT_NOT_FOUND`。运行时不查询 ERP、Amazon，也不按关键词文本反查。

## 证据上下文

Runtime 完整读取并记录产品识别文本路径和内容；它不从关键词反推产品事实。6-0-1 CSV 是唯一 Keyword Candidate 输入；市场容量与自然排名按既有规则作为辅助证据/排序来源，竞争产品数和供需比仅作直通数据，不参与精准裁决。

## 每条记录

`Id` 是 6-0-1 的原始记录身份，必须原样保留。AI 先独立解释 Searcher Intent，再用一次性的 Current Product Understanding 判断 Product–Search Intent Fit、Query Specificity 与 Hard Conflict；这些维度不是固定评分表。每条记录提供四级精准度标签（高度精准、精准、弱精准、不精准）及简短逐词理由；AI直接裁决标签，不计算或映射0–100分。Benchmark rank 只属于辅助现实校验。

Search Mode 先区分 PRODUCT-LED、GIFT-LED、BROAD-GIFT、RELATIONSHIP-ONLY、HARD-SPECIFIED。Gift-led 关系礼物不因缺少 figurine/statue 词而自动降级；必须判断当前产品是否是 CORE FIT，还是只能 CAN SERVE。商品类型、材质、数量/人物表达、个性化、兼容性、尺寸、功能和主题等明确 modifier 具有否决/降级权。

Gift、关系、人群、节日和场景词必须先检查商品类型是否收敛；“可以送给某人”不等于“正在寻找该商品”。Hard Requirement Conflict 优先于局部语义相关。

## 完整性

输入每条有效记录均须输出。Coverage Check 比较 Id 多重集合；INPUT_RECORD_COUNT 必须等于 OUTPUT_RECORD_COUNT。不得因证据不足跳过记录。内部可记录 REVIEW_REQUIRED，但正式 CSV 的“精准度”必须是四级标签之一。

## 输出

6-0-2 输出两份相同十一列契约的 UTF-8 BOM CSV：

1. `6-0-2_[Product_Code]_AI精准词_YYYYMMDD_HHMMSS.csv`：保留每条有效 6-0-1 记录及其四级精准度。
2. `6-0-2_[Product_Code]_AI高度精准词_YYYYMMDD_HHMMSS.csv`：从第一份结果按 `精准度 == 高度精准` 直接筛选，不重新判断。两份文件使用同一 RunContext，并各自伴随 `.meta.json`。

列固定为：`Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准度,精准原因`。前九列继承 6-0-1 唯一关键词母池，其中市场事实、对标覆盖数和排名聚合值必须原值透传，不得用于精准判断或重新计算；按继承的 SearchVolume30 / 市场容量降序且缺失置底、排序稳定。排序只影响输出顺序，不参与精准判断。6-0-2 不再生成手动精准 CSV；历史手动文件不由本 Skill 改写。
