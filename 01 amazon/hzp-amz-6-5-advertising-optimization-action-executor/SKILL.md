---
name: hzp-amz-6-5-advertising-optimization-action-executor
description: 消费已批准的6-4广告经营决策包，校验身份、权限、能力和精确差异后执行并回读获批Amazon Ads动作；不重新决策。
metadata:
  short-description: 广告优化动作执行层
---

# HZP Amazon 6-5｜广告优化动作执行

## 职责边界

6-5 是 APPLY ONLY 层。它只消费最新有效、明确批准的 `hzp-amz-6-4-advertising-decision` 决策包和其中的精确动作，不重判经营策略、不新增目标、不自行扩词、不把建议当批准。新品初始广告创建仍由 6-2 BUILD 负责。

执行顺序固定为：解析批准包 → 再验证 Product/Var/ASIN/SKU/Store/Marketplace/Portfolio 与 Campaign ID → 检查 Provider capability → `prepare_change_plan` → Approved vs Prepared diff → 仅在授权条件满足时 `apply_change_plan` → read-back → 写入 Campaign 私有日志和每日汇总。任何身份冲突、Material Difference、权限不足或能力语义不明都必须阻断。

## 输出与审计

每个动作记录 Change ID、批准状态、变更前后值、Provider返回、read-back结果、失败原因和验证窗口；不修改历史报告。执行日志写入 `06_SKILL分析报告/广告表现汇报优化日志/`，不进入 0-2 正式报告索引。没有写能力时只报告“未执行”，不得假装成功。

## 路由

`6-3 DATA → 6-4 DECIDE → 6-5 APPLY → 6-6 MONITOR`。6-5 不替代 6-4 的经营判断，也不替代 6-6 的产品级监控。

## Human Report Publishing

本 Skill 生成正式 HTML 报告时，遵循统一的人类可见报告规则：Skill 报告根目录只保留一个当前最新 HTML；旧 HTML（以及同名 `.meta.json`）全部移动到同级 `历史HTML/`，不删除、不覆盖。一次性 Skill 的正式机器 CSV/JSON 只进入当前 Skill 报告目录的 `data/`，且只保留完整 `LATEST VALID` Batch；RunPackage/Manifest、metadata sidecar、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。HTML 仅按人类报告规则发布到根目录或 `历史HTML/`。完成写入、回读和校验后才发布当前报告；失败或不完整 Run 不得发布。公共实现与索引规则见 [`skills/references/human-report-publishing.md`](../references/human-report-publishing.md)。

## 全局报告文件治理（适用本 Skill）

本 Skill 遵循公共 `scripts/hzp_amz_report_contract.py`、[human-report-publishing.md](../references/human-report-publishing.md) 与 [report-governance.md](../references/report-governance.md)：正式机器业务数据只进入当前 Skill 报告目录的 `data/`，`data/` 只保留完整 `LATEST VALID` Batch；旧 VALID Batch 整包进入 `历史数据/<RUN_TIMESTAMP>/`。RunPackage/Manifest、metadata、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。新 Batch 必须先 Staging、验证完整性后再原子发布；失败不得替换旧 data。根目录只保留最新人类 HTML（如有）及正式子目录，机器数据不得写根目录。下游通过正式 Registry/Resolver 读取 `data/`，不得按 HTML 或根目录 mtime 选数。已有成熟时间戳 Run Package 的持续 Skill 可保留其内部运行包，但仍遵守根目录清洁和系统资产分层。
