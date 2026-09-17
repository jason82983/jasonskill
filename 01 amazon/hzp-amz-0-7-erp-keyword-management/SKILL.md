---
name: hzp-amz-0-7-erp-keyword-management
description: "Read the PickKw source table, translate missing KeywordCn values by a requested limit, safely update only blank KeywordCn, and emit a report for every run."
---

# HZP Amazon 0-7 | ERP Keyword Management

This skill operates on the ERP source table PickKw. It never reads PickPwKView.
The stable identity is the auto-number field PickKw.Id. The only writable
column is PickKw.KeywordCn, and only when the current value is NULL, empty, or
whitespace. Existing Chinese values are never overwritten.

## Invocation

The caller must provide a positive integer N. "0-7, 1" or "07, 1" means
select at most one next eligible PickKw row and process it. The run scope must
record Limit=N, the missing-KeywordCn filter, and a Run ID. Missing N stops.

## Execution

Use the approved ERP provider with stable keyset pagination. Do not load the
whole table. Choose a bounded page size from the estimated row count. Preserve
Id and Keyword through translation. Cache equal normalized Keywords once per
run. Validate one concise Simplified Chinese translation with no explanation,
JSON fragment, list marker, or merged alternatives.

Before applying, compare Id, original Keyword, and blank KeywordCn. The update
payload must contain KeywordCn only. Read back immediately and report concurrent
fill, source changes, write errors, or mismatches. Every run, including Dry Run,
writes a timestamped CSV, latest HTML, history HTML, and metadata.

Global PickKw reports are stored at:
E:\【所有产品目录专用】\01_公共资料\0-7_ERP关键词管理\

Do not create or use E:\【所有产品目录专用】\00_公共资料\.

The repository currently has no separately verified PickKw.KeywordCn writer
contract. Without that contract, real writes fail closed as WRITE_BLOCKED.

## 批量更新规则

输入数量 N 大于 1 时，默认采用批量流程：按有限批次读取 `PickKw`，在同一批次内复用翻译缓存，批量生成待更新 payload，再通过 6-0-4 的受限 ERP Writer 一次提交。批量大小根据上下文长度、字段数量、历史截断/校验失败自适应，不固定写死。

批量提交不取消单条安全校验：每条记录提交前仍必须核对 `Id`、原始 `Keyword` 和 `KeywordCn` 为空；payload 只能包含允许更新的 `KeywordCn`。提交后必须按 ID 批量回读并逐条确认，失败项单独记录，不用旧快照覆盖并发更新。批量处理主要减少 AI 翻译调用和网络往返，不能跳过数据完整性、权限和回读验证。

N=1 仍按单条流程执行。真实批量写入只有在 6-0-4 Writer 能力已验证、配置有效且调用明确允许时执行；否则保持 `WRITE_BLOCKED` 或 Dry Run。

## Human Report Publishing

本 Skill 生成正式 HTML 报告时，遵循统一的人类可见报告规则：Skill 报告根目录只保留一个当前最新 HTML；旧 HTML（以及同名 `.meta.json`）全部移动到同级 `历史HTML/`，不删除、不覆盖。一次性 Skill 的正式机器 CSV/JSON 只进入当前 Skill 报告目录的 `data/`，且只保留完整 `LATEST VALID` Batch；RunPackage/Manifest、metadata sidecar、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。HTML 仅按人类报告规则发布到根目录或 `历史HTML/`。完成写入、回读和校验后才发布当前报告；失败或不完整 Run 不得发布。公共实现与索引规则见 [`skills/references/human-report-publishing.md`](../references/human-report-publishing.md)。

## 全局报告文件治理（适用本 Skill）

本 Skill 遵循公共 `scripts/hzp_amz_report_contract.py`、[human-report-publishing.md](../references/human-report-publishing.md) 与 [report-governance.md](../references/report-governance.md)：正式机器业务数据只进入当前 Skill 报告目录的 `data/`，`data/` 只保留完整 `LATEST VALID` Batch；旧 VALID Batch 整包进入 `历史数据/<RUN_TIMESTAMP>/`。RunPackage/Manifest、metadata、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。新 Batch 必须先 Staging、验证完整性后再原子发布；失败不得替换旧 data。根目录只保留最新人类 HTML（如有）及正式子目录，机器数据不得写根目录。下游通过正式 Registry/Resolver 读取 `data/`，不得按 HTML 或根目录 mtime 选数。已有成熟时间戳 Run Package 的持续 Skill 可保留其内部运行包，但仍遵守根目录清洁和系统资产分层。
