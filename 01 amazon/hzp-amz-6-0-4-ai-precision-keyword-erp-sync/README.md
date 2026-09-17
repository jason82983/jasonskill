# HZP Amazon 6-0-4｜AI精准词同步ERP

Machine Name：`hzp-amz-6-0-4-ai-precision-keyword-erp-sync`

6-0-4 只消费 6-0-2 的 AI 精准词六列 CSV，并通过 `erp-pickpwk-write-access.json` 声明的受限能力追加 `PickPwK.Tags` 的完整 `|1精准|`。自动编号是 PickPwK 真实记录 ID，可来自当前产品或明确绑定的 Benchmark；6-0-4 按 ID + Keyword 双校验执行，不因 Record ProId 与当前分析产品不同而阻止。它不重新判断精准词，不读取 6-0-3，不直接连接任意 SQL。

正式命令：`6-0-4，Product_Code`；预检命令：`6-0-4，Product_Code，预检`。缺少输入、配置、凭据、目标身份或回读条件时必须 fail closed。日志位于 `06_SKILL分析报告/6-0-4_AI精准词同步ERP/执行日志/`，不进入 0-2 正式报告索引。

当前配置确认的身份映射为：`PickPwKView.Id → PickPwK.Id`，目标字段为 `Tags`。该映射来自系统配置和人工确认；本 Skill 不修改配置、不修改 `IsExact`，不删除精准标签。
