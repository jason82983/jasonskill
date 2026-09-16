# 6-0-4 受限 Writer 契约

唯一系统配置：`E:/【所有产品目录专用】/00_公共资料/03_系统配置/erp-pickpwk-write-access.json`。

从当前 Product Root 的 6-0-2 输出目录，通过共享 `scripts/stage6_artifact_contract.py` 按 `AI_PRECISION_KEYWORDS` 解析最新有效输入；校验 Product_Code、报告身份、6-0-4 既有输入 Schema 和有效状态，不按 mtime 选择。执行日志文件名带本次 `YYYYMMDD_HHMMSS`，并用 `.meta.json` 保存来源血缘；日志不是正式报告。具体公共字段见 `../references/stage6-artifact-contract.md`。

配置固定 `dbo.PickPwK`、`Id`、`Tags` 和 `PickPwKView.Id → PickPwK.Id`。`allowed_update_columns` 必须只有 `Tags`，完整 Token 必须是 `|1精准|`。`enabled`、凭据、目标表/列、权限或字段身份任一失败都阻断整批运行。

业务适配器只暴露 `select_record(record_id)`、`add_precision_tag(record_id, expected_keyword)`、`verify_record(record_id, expected_keyword, before_tags)` 等固定动作；不暴露 `execute_sql`、`run_sql` 或接受任意 SQL 文本的接口。所有参数值均参数化，标识符只来自已验证配置。

每个记录先用 ID 查询一条记录并核验 Keyword，再重新读取最新 Tags，使用条件 UPDATE 防止并发覆盖。追加算法保留原 Tags，NULL/空值变成单一完整标签，已有标签不重复。事务范围只包含一条记录的读取、条件更新和更新后回读。

输入与结果字段：`自动编号`、`关键词` 是执行身份；搜索量、中文名称、精准理由和精准度不参与 UPDATE。结果状态包括 `SUCCESS`、`NO_CHANGE`、`SKIPPED`、`FAILED`、`WRITE_BLOCKED`。日志只记录运行身份、结果、错误码和非敏感证据。

## Benchmark Record ID 边界

6-0-2 的 AI 判断对象是 `Current Product + Normalized Keyword`，但最终资产按真实 PickPwK Record ID 展开。Record ID 可来自当前产品或当前产品资料中明确绑定的 Benchmark；6-0-4 以该 ID 为唯一写入定位，不要求记录 `ProId` 等于本次 `Product_Code` 的当前 ERP ProId。

放宽来源不等于放宽安全校验：每条 CSV 记录都必须先确认 ID 唯一，并确认数据库当前 `Keyword` 与 CSV `关键词` 一致；不一致返回 `[ERP_KEYWORD_IDENTITY_MISMATCH]`，禁止 UPDATE。CSV 内同一 ID 对应不同 Keyword 返回 `[ERP_KEYWORD_RECORD_IDENTITY_CONFLICT]`，该 ID 不进入执行。已有完整 `|1精准|` 只返回 `NO_CHANGE`、不发送 UPDATE；没有完整标签时只追加该 Token，继续 ADD ONLY，不修改其他字段，不 REMOVE。

## 多对标统一关键词池安全边界

新版 6-0-2 的十一列 `AI_PRECISION_KEYWORDS` / `HIGH_PRECISION_KEYWORDS` 使用 `Id=KwId`，表示跨 ProId 稳定的 Keyword Entity。它不能映射成配置指定的 `PickPwK.Id` 写入行身份。6-0-4 发现该 Schema 时返回 `[ERP_KEYWORD_ENTITY_ID_NOT_WRITABLE_AS_PICKPWK_ID]` 并停止；不得查询/写入一个猜测行、把 KwId 当 PickPwK.Id，或在多个 Benchmark 记录中任意挑一行。未来若批准行扩展规则，须明确唯一/多行写入范围后另行更新契约与测试。
