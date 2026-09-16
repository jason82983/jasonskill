# 6-1 广告状态执行报告模板

> 本模板用于执行 6-0-5 已批准作战表。6-1 不作战略重选；报告中的批准必须绑定完整差异与字段。

## 1. Execution Summary

- Product Code / Product Root：
- Store / Marketplace / Own ASIN / Variant / Advertised SKU(s)：
- 605 RUN_ID 与最新有效输入文件：Intent A / Keyword Lifecycle C / Battle Units B / HTML
- 已批准 Battle Unit 数：
- 6-1 RUN_ID / execution_id / 运行时间：
- 模式：BUILD / RECONCILE
- 执行状态：
- 动作计数：CREATE / UPDATE / NO_CHANGE / PAUSE_CANDIDATE / Failed

## 2. Preflight 与技术映射

- 605 同 RUN_ID、身份、批准、Coverage：
- Own ASIN / Benchmark ASIN / Product Target ASIN 分离核验：
- 页面、库存、经济上限、Portfolio、命名与 Provider 字段能力：
- 作战任务 + 投放方式 → Technical Role / Tool：
- 未解决问题 / 阻断项：

## 3. Approved Desired State

逐项保留 Battle Unit ID、Intent Code、批准阶段、作战任务、投放方式、关键词/目标原值及 605 提供的约束；标明 6-1 补齐的技术执行字段及其来源。

## 4. Live Actual State 与身份映射

记录查询时间、Provider、Store、Marketplace、各实体 Amazon ID、Logical ID、父子关系、实际名称和字段。旧对象无可靠 Logical ID 时不得按名称模糊匹配。

## 5. Desired-vs-Actual Diff

| Entity | Logical ID | Amazon ID | Parent | Battle Unit ID | Action | Before | Desired | Reason |
|---|---|---|---|---|---|---|---|---|

PAUSE_CANDIDATE 只报告，不自动 Pause/Delete/Archive。

## 6. Exact Approval

- 用户批准的确切 CREATE/UPDATE 行及字段：
- 批准时间与确认内容：
- 批准后差异是否变化：

未批准时不调用写接口。若执行参数或动作与批准内容变化，重新展示并请求新批准。

## 7. Prepare / Apply / Read-back

- Prepared Change Plan ID 与精确差异校验：
- Apply 时间、幂等键、逐实体结果：
- Read-back Amazon IDs、字段核验及差异：
- 部分失败恢复范围：

## 8. Execution Audit 与后续交接

记录 605 输入血缘、6-1 RUN_ID、BUILD/RECONCILE、实际调用、动作数、结果、错误、Amazon IDs 和日志路径。交接 6-2/6-3 时透传批准目标、实际实体 ID、名称、Bid/Budget/Placement/策略、执行与 Read-back 状态；不附加自创生命周期或战略建议。
