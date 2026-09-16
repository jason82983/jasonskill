# 批准后广告状态同步契约

## 支持边界

SellerSpace `prepare_change_plan` 当前契约列出：`campaign.create`、`keywords.create`、`targets.create`，并为 `change.campaign` 提供 `name`、`adGroupName`、`dailyBudget`、`defaultBid`、`productAds`、`keywords/targets`、`strategy`、`placementTop/Other/Product/Business`、状态和日期字段。`apply_change_plan` 以 `planId + idempotencyKey` 执行。

`discover_capabilities` 当前明确提供 Campaign 更新、预算、广告位和批量规则工作流；创建动作的嵌套对象字段在公开能力摘要中不完整，因此每次必须以实际 `prepare_change_plan` preview 为准。没有 preview 或字段不支持时不得假装创建成功，标记 `[SellerSpace能力缺口]`。

## 允许的差异动作

6-0-5 最新有效且同 RUN_ID 的已批准作战表是唯一战略目标来源。6-1 先建立 Desired State，再以实时 Amazon Actual State 计算 CREATE、UPDATE、NO_CHANGE、PAUSE_CANDIDATE。CREATE/UPDATE 只可针对展示并经用户明确批准的精确差异与字段；NO_CHANGE 不写入；PAUSE_CANDIDATE 只报告，不 Pause、Archive 或 Delete。旧广告只有在与批准 Desired State 的同一 Logical ID 对应且字段属于更新白名单时才可 UPDATE；不得因名称相似或缺少旧对象而盲目修改。

Own ASIN、Mapped_SKUs[]/Advertised_SKUs[] 必须来自映射表、产品档案和 SellerSpace 三方一致验证；Benchmark/Product Target 只能作为批准 Target 的身份或研究证据，不能作为 Advertised Product。

UPDATE 仅限共享执行模块中的字段白名单，并且只能修改 Desired State 明确给出的字段；身份变更、未知字段、整对象替换或空值清除一律停止。当前 Amazon Ads Provider 未明确支持的字段不能因本地白名单而假设可写，仍须先通过 capability discovery 与 prepare preview 验证。

## 幂等与恢复

执行前检查 Campaign identity、名称 Sequence、Store、Marketplace、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]；使用同一产品、605 RUN_ID、规范化 Desired State 得出稳定 `execution_id`。同一 Actual State 再运行必须 0 CREATE/0 UPDATE。部分成功先 Query Actual State 并 Read-Back，Recovery Plan 只覆盖尚未满足的对象，不能整批重跑。Campaign Name 不是主身份；按 Logical ID 与 Amazon ID 追溯。
## Portfolio 校验（每个 CREATE/UPDATE 都必须执行）

- Desired State 记录 `Portfolio Name`（来自映射表 `广告组合`）和 SellerSpace 解析的 `Portfolio ID`，并记录来源、读取时间、Store、Marketplace。
- Prepared Change Plan 必须逐字段比对 Portfolio Name/ID；任何差异都属于 Material Difference，停止 `apply_change_plan` 并重新确认。
- Read-Back 必须核对实际 Campaign Portfolio Name/ID；匹配才标记 `[创建成功｜Portfolio一致]`。缺失、冲突或无法验证不得自动修复旧广告。

- Approved、Prepared 与 Read-Back 还必须核对 Product_NewCode、正式 Product_Code、Store 前缀、Var_Code、Advertised Child ASIN、Mapped_SKUs[]、Advertised_SKUs[]；任何身份差异都是 Material Difference，禁止写入。
