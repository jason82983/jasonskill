---
name: hzp-amz-6-0-4-ai-precision-keyword-erp-sync
description: 将 6-0-2 AI 精准词 CSV 通过系统级受限 PickPwK Writer 能力安全追加到 ERP Tags；支持预检、幂等、事务、并发保护和回读，不重新判断精准词。
metadata:
  short-description: 6-0-2 AI精准词受限同步ERP
---

# HZP Amazon 6-0-4｜AI精准词同步ERP

6-0-4 只执行同步：读取当前产品的 `6-0-2_[Product_Code]_AI精准词.csv`，按 `自动编号` 定位 `PickPwK` 记录，以 `关键词` 做二次身份核验，仅在缺少完整 `|1精准|` 时追加该标签。精准词判断归 6-0-2，精准泛词归 6-0-3。

## 唯一输入与配置

- 输入从 `[Product Root]/06_SKILL分析报告/6-0-2_精准关键词识别/` 通过共享 Latest Valid Resolver 选择当前产品最新有效的 6-0-2 `AI_PRECISION_KEYWORDS` 资产，文件名可带 `YYYYMMDD_HHMMSS`。历史六列兼容输入规则保持不变；旧七列全量判断资产因缺少经批准的同步选择/阈值仍返回 `[PRECISION_THRESHOLD_UNRESOLVED]`。新多对标十一列资产的 `Id` 是跨 ProId 稳定的 `KwId`，不是 PickPwK 主表写入行 `PickPwK.Id`；在没有经批准且唯一的 `KwId → PickPwK.Id` 行扩展规则前，必须返回 `[ERP_KEYWORD_ENTITY_ID_NOT_WRITABLE_AS_PICKPWK_ID]` 并阻止写入。不得把统一关键词实体 ID 当成行主键。不读取 6-0-3 CSV，不重新运行 6-0-2。
- Writer 唯一配置入口是 `E:/【所有产品目录专用】/00_公共资料/03_系统配置/erp-pickpwk-write-access.json`。不得硬编码连接、表、字段或凭据，也不得使用 Reader Credential。
- 自动编号必须对应配置声明的 `PickPwK.Id`；ID 与数据库 `Keyword` 必须精确（仅 Trim/合理大小写标准化）一致。Record ID 可以来自当前产品或明确绑定的 Benchmark；6-0-4 不以本次 `Product_Code` 或 Record `ProId` 做所有权阻断。

## 安全执行契约

配置缺失、无效、disabled、凭据不可用、数据库或目标字段检查失败时，整批 `WRITE_BLOCKED`，返回 `[ERP_PICKPWK_WRITE_CAPABILITY_NOT_AVAILABLE]`，不得绕过 JSON 或部分写入。6-0-4 没有任意 SQL 接口，只能调用固定的读取、追加标签和回读业务动作。

正式运行顺序固定为：CSV Schema 检查 → 全批 Preflight → 每条记录重新读取最新 `Id/Keyword/Tags` → 精确身份核验 → 检查完整 `|1精准|` → 在最小事务中只更新 `Tags` → Read-Back → 写无 Secret 日志。Preflight 命令 `6-0-4，Product_Code，预检` 绝不 UPDATE；正式命令也必须先完成 Preflight。

同步是 ADD ONLY 且幂等：已有完整标签为 `NO_CHANGE`；NULL/空 Tags 生成合法标签；已有其他标签全部保留；不删除、覆盖或重排其他标签，不修改 `Keyword`、`ProId`、`IsExact`、搜索量或任何其他列。重复 ID 在单次运行只处理一次；同 ID 不同 Keyword 返回 `[ERP_KEYWORD_RECORD_IDENTITY_CONFLICT]` 并阻止该 ID；ID 0 条/多条分别为 `[ERP_PICKPWK_ID_NOT_FOUND]` / `[ERP_PICKPWK_ID_NOT_UNIQUE]`，身份不一致为 `[ERP_KEYWORD_IDENTITY_MISMATCH]`。Benchmark ID 与当前产品 ProId 不同不构成错误。

并发时使用最新 Tags 和条件更新保护，不能用旧快照覆盖别人新增的标签。只有回读确认 ID、Keyword、完整精准标签和原有其他标签均保持后才记为 `SUCCESS`；否则记为 `FAILED` / `[ERP_PRECISION_TAG_READBACK_FAILED]`。日志保存到 `[Product Root]/06_SKILL分析报告/6-0-4_AI精准词同步ERP/执行日志/`，每次文件名追加 `YYYYMMDD_HHMMSS` 并写 `.meta.json` 输入血缘；不是正式报告，不进入 0-2 索引，也不写入密码、连接字符串或 Secret。

实现细节见 [references/restricted-writer-contract.md](references/restricted-writer-contract.md)，固定业务适配器见 `scripts/restricted_writer.py`。本开发阶段仅做 Mock/静态验证，不运行真实 6-0-4，不执行真实 ERP UPDATE。

输入选择、RUN_ID/RUN_TIMESTAMP 和日志元数据统一遵守 `../references/stage6-artifact-contract.md`；实时 PickPwK 写入前的身份重读、事务和 Read-Back 规则保持原样。

## 全局正式报告目录与命名规则

本 Skill 面向确定 Product Root 生成正式报告或结构化分析报告时，统一保存到 `06_SKILL分析报告/{Skill编号}_{Skill中文正式名称}/`，文件名使用 `{Skill编号}_{报告名称}_{YYYYMMDD_HHMMSS}.{ext}`；同一运行的配套正式资产共用时间戳。6-0-1、6-0-2、6-0-3、6-0-5、6-0-6 的报告资产直接放固定 Skill 目录，不建时间戳子目录；6-2、6-3、6-4 可按每次运行建立 `YYYYMMDD_HHMMSS/` 子目录，子目录中的文件仍须带 Skill 编号前缀和时间戳。读取最新报告或运行包时按文件名/包内时间及有效性校验，不按文件修改时间选择。若 HTML 由同批 CSV 生成，必须从文件名时间戳相同的 CSV 读取并生成不可变快照；禁止运行时另找“最新 CSV”。未由 CSV 构成输入的 HTML 报告遵循对应 Skill 的原有报告内容逻辑。此规则优先于本文档中旧的目录和文件名示例。历史报告不自动迁移或删除。跨产品公共知识、提醒状态、决策登记簿和运行日志等持续业务数据按各自数据契约保存，不作为 Product Root 正式分析报告迁移。

## Shared AI Brain

本 Skill 遵守仓库共享 AI Brain：`../references/ai-brain/README.md`。运行时按 `context-manifest.md` 声明 GLOBAL、DOMAIN、UPSTREAM、HISTORY、FORBIDDEN；本 Skill 的业务 Contract、正式 Ground Truth 和职责边界优先于泛化推理。AI Judgment 必须区分 Evidence 类型，重要判断先执行 Decision Challenge，再由 Reason Trace 生成原因；程序确定的数学、Join、去重、筛选、聚合、Schema、Identity、Timestamp、Latest 和 Read-back 不交给 AI 计算。
