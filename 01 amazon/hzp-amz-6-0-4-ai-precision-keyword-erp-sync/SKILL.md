---
name: hzp-amz-6-0-4-ai-precision-keyword-erp-sync
description: 将 6-0-2 AI 精准词 CSV 通过系统级受限 PickPwK Writer 能力安全追加到 ERP Tags；支持预检、幂等、事务、并发保护和回读，不重新判断精准词。
metadata:
  short-description: 6-0-2 AI精准词受限同步ERP
---

# HZP Amazon 6-0-4｜AI精准词同步ERP

6-0-4 只执行同步：读取当前产品的 `6-0-2_[Product_Code]_AI精准词.csv`，按 `自动编号` 定位 `PickPwK` 记录，以 `关键词` 做二次身份核验，仅在缺少完整 `|1精准|` 时追加该标签。精准词判断归 6-0-2，精准泛词归 6-0-3。

## 唯一输入与配置

- 输入固定为 `[Product Root]/06_SKILL分析报告/6-0-2_精准关键词识别/6-0-2_[Product_Code]_AI精准词.csv`，当前七列契约为：`Id`、`词`、`中文`、`市场容量`、`自然排名`、`精准度`、`精准原因`；实现可识别历史六列作为兼容输入。七列覆盖所有判断记录而没有经批准的 ERP 同步选择/阈值，因此读取七列时必须返回 `[PRECISION_THRESHOLD_UNRESOLVED]` 并阻止任何写入，不得把全量结果直接同步。不读取手动 CSV 或 6-0-3 CSV，不重新运行 6-0-2。
- Writer 唯一配置入口是 `E:/【所有产品目录专用】/00_公共资料/03_系统配置/erp-pickpwk-write-access.json`。不得硬编码连接、表、字段或凭据，也不得使用 Reader Credential。
- 自动编号必须对应配置声明的 `PickPwK.Id`；ID 与数据库 `Keyword` 必须精确（仅 Trim/合理大小写标准化）一致。Record ID 可以来自当前产品或明确绑定的 Benchmark；6-0-4 不以本次 `Product_Code` 或 Record `ProId` 做所有权阻断。

## 安全执行契约

配置缺失、无效、disabled、凭据不可用、数据库或目标字段检查失败时，整批 `WRITE_BLOCKED`，返回 `[ERP_PICKPWK_WRITE_CAPABILITY_NOT_AVAILABLE]`，不得绕过 JSON 或部分写入。6-0-4 没有任意 SQL 接口，只能调用固定的读取、追加标签和回读业务动作。

正式运行顺序固定为：CSV Schema 检查 → 全批 Preflight → 每条记录重新读取最新 `Id/Keyword/Tags` → 精确身份核验 → 检查完整 `|1精准|` → 在最小事务中只更新 `Tags` → Read-Back → 写无 Secret 日志。Preflight 命令 `6-0-4，Product_Code，预检` 绝不 UPDATE；正式命令也必须先完成 Preflight。

同步是 ADD ONLY 且幂等：已有完整标签为 `NO_CHANGE`；NULL/空 Tags 生成合法标签；已有其他标签全部保留；不删除、覆盖或重排其他标签，不修改 `Keyword`、`ProId`、`IsExact`、搜索量或任何其他列。重复 ID 在单次运行只处理一次；同 ID 不同 Keyword 返回 `[ERP_KEYWORD_RECORD_IDENTITY_CONFLICT]` 并阻止该 ID；ID 0 条/多条分别为 `[ERP_PICKPWK_ID_NOT_FOUND]` / `[ERP_PICKPWK_ID_NOT_UNIQUE]`，身份不一致为 `[ERP_KEYWORD_IDENTITY_MISMATCH]`。Benchmark ID 与当前产品 ProId 不同不构成错误。

并发时使用最新 Tags 和条件更新保护，不能用旧快照覆盖别人新增的标签。只有回读确认 ID、Keyword、完整精准标签和原有其他标签均保持后才记为 `SUCCESS`；否则记为 `FAILED` / `[ERP_PRECISION_TAG_READBACK_FAILED]`。日志保存到 `[Product Root]/06_SKILL分析报告/6-0-4_AI精准词同步ERP/执行日志/`，不是正式报告，不进入 0-2 索引，也不写入密码、连接字符串或 Secret。

实现细节见 [references/restricted-writer-contract.md](references/restricted-writer-contract.md)，固定业务适配器见 `scripts/restricted_writer.py`。本开发阶段仅做 Mock/静态验证，不运行真实 6-0-4，不执行真实 ERP UPDATE。

## Human Report Publishing

本 Skill 生成正式 HTML 报告时，遵循统一的人类可见报告规则：Skill 报告根目录只保留一个当前最新 HTML；旧 HTML（以及同名 `.meta.json`）全部移动到同级 `历史HTML/`，不删除、不覆盖。一次性 Skill 的正式机器 CSV/JSON 只进入当前 Skill 报告目录的 `data/`，且只保留完整 `LATEST VALID` Batch；RunPackage/Manifest、metadata sidecar、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。HTML 仅按人类报告规则发布到根目录或 `历史HTML/`。完成写入、回读和校验后才发布当前报告；失败或不完整 Run 不得发布。公共实现与索引规则见 [`skills/references/human-report-publishing.md`](../references/human-report-publishing.md)。

## 全局报告文件治理（适用本 Skill）

本 Skill 遵循公共 `scripts/hzp_amz_report_contract.py`、[human-report-publishing.md](../references/human-report-publishing.md) 与 [report-governance.md](../references/report-governance.md)：正式机器业务数据只进入当前 Skill 报告目录的 `data/`，`data/` 只保留完整 `LATEST VALID` Batch；旧 VALID Batch 整包进入 `历史数据/<RUN_TIMESTAMP>/`。RunPackage/Manifest、metadata、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。新 Batch 必须先 Staging、验证完整性后再原子发布；失败不得替换旧 data。根目录只保留最新人类 HTML（如有）及正式子目录，机器数据不得写根目录。下游通过正式 Registry/Resolver 读取 `data/`，不得按 HTML 或根目录 mtime 选数。已有成熟时间戳 Run Package 的持续 Skill 可保留其内部运行包，但仍遵守根目录清洁和系统资产分层。
