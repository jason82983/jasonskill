# 6-0-2 Report Outline

## 运行身份
- Product Code / Product Root
- 6-0-1 输入文件、Generated_At/文件名时间戳、表头和 Input Resolution Method
- INPUT_RECORD_COUNT

## Current Product Evidence Context
- 完整读取 `05_分析源数据/01_产品数据/本产品/产品识别 - 文本文案.txt` 的路径和状态
- 输入身份：`CURRENT_PRODUCT_TEXT_EVIDENCE`
- 缺失状态：`CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND` / `CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY` / `CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED`
- 仅记录文本中实际存在的 Current Product 事实；不从关键词反推产品属性

## Precision Judgment
- Product–Search Intent Fit
- Query Specificity
- Intent Convergence
- Hard Conflict
- 每条 Id 的具体意图、证据、精准度、精准原因
- Evidence Trace

## 完整性与输出
- OUTPUT_RECORD_COUNT
- Coverage Check、缺失/额外 Id
- 全量判断 CSV：Id｜词｜中文｜市场容量｜竞争产品数｜供需比｜对标覆盖数｜最佳自然排名｜自然排名中位数｜精准度｜精准原因
- 高度精准 CSV：同样十一列，仅保留“高度精准”
- 不生成手动精准 CSV
- 精准度只能为：高度精准、精准、弱精准、不精准；AI直接裁决，不使用0–100分
- SearchVolume30 降序、缺失置底、稳定排序
- 6-0-3/6-0-4 兼容性与 UNRESOLVED
