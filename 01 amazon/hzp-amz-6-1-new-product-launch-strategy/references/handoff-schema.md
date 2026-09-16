# 6-1 Execution Handoff Schema

6-1 只把批准作战计划及其实际应用状态交给 6-2/6-3，不生成第二套 Launch Strategy。

## Required lineage

- Product Code、Product Root、Store、Marketplace、Own ASIN、Var_Code、Mapped_SKUs[]/Advertised_SKUs[]
- 605 Intent A / Keyword Lifecycle C / Battle Units B 文件、RUN_ID、批准 Battle Unit IDs
- 6-1 RUN_ID、execution_id、BUILD/RECONCILE、实际状态查询时间、Provider
- 完整 Logical ID ↔ Amazon ID、父子 ID、Actual/Desired 名称与历史名关联

## Per-entity applied state

- Entity type、Battle Unit ID、Intent Code、605 原始作战任务/阶段/投放方式/控制方式（独立/共享/不投）
- Campaign、Ad Group、Advertised Product、Target 类型和值
- Bid、Daily Budget、Placement、Bidding Strategy、Status 及其事实来源
- Action（CREATE/UPDATE/NO_CHANGE/PAUSE_CANDIDATE）、批准字段、Prepared/Apply/Read-back 结果
- 错误、未解决事项、部分成功恢复范围

6-2/6-3 可读取这些实际对象与批准边界进行监控/诊断。它们不得把 6-1 的执行摘要解释成新的批准，且必须继续遵守自身写入授权合同。
