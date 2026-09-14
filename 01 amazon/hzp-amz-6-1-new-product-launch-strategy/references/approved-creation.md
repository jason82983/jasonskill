# 批准后创建执行契约

## 支持边界

SellerSpace `prepare_change_plan` 当前契约列出：`campaign.create`、`keywords.create`、`targets.create`，并为 `change.campaign` 提供 `name`、`adGroupName`、`dailyBudget`、`defaultBid`、`productAds`、`keywords/targets`、`strategy`、`placementTop/Other/Product/Business`、状态和日期字段。`apply_change_plan` 以 `planId + idempotencyKey` 执行。

`discover_capabilities` 当前明确提供 Campaign 更新、预算、广告位和批量规则工作流；创建动作的嵌套对象字段在公开能力摘要中不完整，因此每次必须以实际 `prepare_change_plan` preview 为准。没有 preview 或字段不支持时不得假装创建成功，标记 `[SellerSpace能力缺口]`。

## 只创建新广告

批准清单是唯一授权范围。旧 Campaign 只查询和提示并行风险，不 Pause、Archive、Delete 或修改。Own ASIN/SKU 必须来自映射表、产品档案和 SellerSpace 三方一致验证；Benchmark/Product Target 只能作为研究或 Target 候选。

## 幂等与恢复

执行前检查 Campaign identity、名称 Sequence、Store、Marketplace、Own ASIN/SKU；生成唯一 `execution_id`。部分成功先 Read-Back，Recovery Plan 只覆盖失败对象，不能整批重跑。
## Portfolio 校验（每次批准创建都必须执行）

- 批准清单记录 `Portfolio Name`（来自映射表 `广告组合`）和 SellerSpace 解析的 `Portfolio ID`，并记录来源、读取时间、Store、Marketplace。
- Prepared Change Plan 必须逐字段比对 Portfolio Name/ID；任何差异都属于 Material Difference，停止 `apply_change_plan` 并重新确认。
- Read-Back 必须核对实际 Campaign Portfolio Name/ID；匹配才标记 `[创建成功｜Portfolio一致]`。缺失、冲突或无法验证不得自动修复旧广告。

- Approved、Prepared 与 Read-Back 还必须核对 Product_NewCode、正式 Product_Code、Store 前缀、Var_Code、Advertised Child ASIN 和 Child SKU；任何身份差异都是 Material Difference，禁止写入。
