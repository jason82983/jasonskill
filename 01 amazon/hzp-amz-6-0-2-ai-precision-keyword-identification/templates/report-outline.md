# 6-0-2 Report Outline

## 运行身份
- Product Code / Product Root / RUN_ID / RUN_TIMESTAMP
- 6-0-1 当前选中的有效Batch时间戳、全部Observation文件、表头和输入记录数
- 产品识别文本路径与版本指纹

## Current Product Evidence Context
- 完整读取 `05_分析源数据/01_产品数据/本产品/产品识别 - 文本文案.txt` 的路径和状态
- 输入身份：`CURRENT_PRODUCT_TEXT_EVIDENCE`
- 缺失状态：`CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND` / `CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY` / `CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED`
- 仅记录文本中实际存在的 Current Product 事实；不从关键词反推产品属性

## Precision Judgment
- Product Purchase Driver（同一 Run 一次）：Primary / Secondary / Reason
- Product–Search Intent Fit
- Query Specificity
- Intent Convergence
- Hard Conflict
- Driver-specific evidence：FUNCTIONAL、COMPATIBILITY、GIFT_EMOTIONAL、AESTHETIC_DECOR、OCCASION、HYBRID
- Gift Mission Evidence：GiftIntentPresent、GiftMissionFit/PurchaseMissionFit、RecipientFit、RelationshipFit、OccasionFit、EmotionalMessageFit
- Convergence：PhysicalProductConvergence、PurchaseMissionConvergence、CompatibilityConvergence
- Decision Challenge：检查物理形态误降级、错误 Driver 证据、Gift 任务过高/过低估计和 Hard Conflict
- 每条 Id 的具体意图、证据、精准度、精准原因
- Evidence Trace

## Precision Brain Regression
- Golden Case：PrimaryPurchaseDriver、PurchaseMissionFit、PhysicalProductConvergence、CaseType
- 指标：ExactPrecisionMatch、MismatchCount、HighPrecisionRecall、GiftHighMissionFitRecall、FalseHighPrecisionRate、BroadGiftFalseHighPrecisionRate
- Grade Compression 与 UNRESOLVED 项

## 完整性与输出
- OUTPUT A：`6-0-2_精准判断所有词表_{RUN_TIMESTAMP}.csv`，保留Benchmark observation和所属产品编号
- OUTPUT B：`6-0-2_筛选后的对标精准词_{RUN_TIMESTAMP}.csv`，从A按共享配置等级筛选
- OUTPUT C：`6-0-2_去重_筛选后的对标精准词_{RUN_TIMESTAMP}.csv`，按Benchmark+Canonical Keyword去重，保留Benchmark身份；另有D `6-0-2_去对标去重_筛选后的精准词_{RUN_TIMESTAMP}.csv`供603
- OUTPUT E：每个所属产品编号一张 `6-0-2_{所属产品编号}_筛选后的精准词_{RUN_TIMESTAMP}.csv`，从B按产品编号筛选
- 每Benchmark D表中的Canonical Keyword唯一；D表记录数之和等于B记录数
- A+B+C+D+N(E)文件名、Manifest时间戳、Schema、记录数、透传、A/B一致判断C去重、D唯一关键词、E拆分覆盖全部校验
- 缺少任意公共表或预期D表时Run不得标记VALID
- 历史Run文件保留；所有输出直接位于固定报告根目录，不创建时间戳子目录
- 不生成手动精准 CSV
- 精准度只能为：高度精准、精准、弱精准、不精准；AI直接裁决，不使用0–100分
- SearchVolume30 降序、缺失置底、稳定排序
- 6-0-3/6-0-4 兼容性与 UNRESOLVED


