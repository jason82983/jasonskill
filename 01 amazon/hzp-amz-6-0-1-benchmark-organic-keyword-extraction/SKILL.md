---
name: hzp-amz-6-0-1-benchmark-organic-keyword-extraction
description: 对当前产品档案中配置的 1..N 个 Benchmark 分别读取 PickPwKView 自然排名数据，输出多对标明细、唯一关键词母池、逐 ASIN 原始表和 Observation 汇总表；不做语义判断或写操作。
metadata:
  short-description: 多对标自然排名关键词资产提取
---

# HZP Amazon 6-0-1｜对标自然排名关键词提取

Formal identity: 6-0-1 | Benchmark Organic Keyword Extraction | `hzp-amz-6-0-1-benchmark-organic-keyword-extraction`.

## 运行和身份

支持 `6-0-1，Product_Code`，也支持显式单个 `Benchmark_ASIN`。Product_Code 模式从当前产品唯一 `01_产品档案.md` 的“对标产品”配置读取 1..N 对标 ASIN 与 ERP ProId，并逐个查询；不从对标名称或历史报告猜身份。每个 Benchmark Code 稳定复用档案编码；缺少显式编码时由显式 ASIN 构造固定的 `ASIN_<ASIN>` 编码。对标身份缺失、重复或冲突时 fail closed。

601 只接受 ERP 导出的对标词 CSV（通过必填 `--input-csv` 传入），不再连接 ERP、SQL 或 `erp_keyword_adapter.py`，也不接受历史报告代替本次输入。CSV 必须包含 PickPwKView 字段；`PickPwKView.Id` 是源行身份，`KwId` 跨 ProId 稳定唯一。`KeywordCn` 直接读取源 CSV；为空时保留为空，不翻译、不回写，也不因此终止。

## 事实和过滤

Keyword Market Fact 一词一份：`Keyword`、`KeywordCn`、`SearchVolume30`、`AsinQuantity`；供需比由代码计算 `SearchVolume30 / AsinQuantity`，四位小数。Benchmark Observation 按一个 Keyword Entity × 一个 Benchmark Code 记录真实 `RankOra`。字段语义及冲突策略见 [field contract](references/field-contract.md)。

`中文`字段直接使用 ERP `KeywordCn`；为空时保留为空。该字段只用于展示，不参与筛选、排序、Keyword Entity、市场事实、排名或语义判断。

继续使用既有合法筛选：`RankOra >= 1` 且 `SearchVolume30 > 100`。保留所有合格 Keyword；不做 AI 精准度判断、关键词语义去重、聚类、推广或写操作。相同 `KwId` 的市场容量/竞争产品数冲突时报告 `KEYWORD_MARKET_FACT_CONFLICT`，不得任选或静默覆盖。

## 正式输出

生成同一运行的 A/B 两份既有资产、每个有效 ASIN 一份原始 CSV，以及一份 Observation 汇总 CSV；所有正式文件使用 UTF-8 with BOM 并写各自 `.meta.json`：

1. `01_6-0-1_多对标关键词排名明细_YYYYMMDD_HHMMSS.csv`，固定九列：`Id,词,中文,市场容量,竞争产品数,供需比,对标编号,对标ASIN,自然排名`。一行一个 Keyword × Benchmark rank observation；`对标编号`是当前产品档案中该 Benchmark 的 ERP 数字编号（`benchmark_erp_pro_id`）。
2. `02_6-0-1_对标关键词母池_YYYYMMDD_HHMMSS.csv`，固定九列：`Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数`。一行一个唯一 Keyword Entity，是 6-0-2 唯一正式关键词输入。
3. 每个有效对标 ASIN 单独生成 `NN_6-0-1_{ASIN}_关键词自然排名_YYYYMMDD_HHMMSS.csv`，固定沿用 A 表九列 schema。`对标编号`与该 ASIN 对应的 ERP 编号一致。
4. `NN_6-0-1_所有对标自然排名关键词_YYYYMMDD_HHMMSS.csv`，不包含`对标编码`列，保留`对标编号`，并追加 `ASIN,产品编号`。内容是 N 张 ASIN 原始表的 UNION ALL；不按词或 Id 去重。`产品编号`为该 ASIN 在 `01_产品档案.md` 对应 Benchmark 配置中的 ERP 数字编号（`benchmark_erp_pro_id`）；缺失时返回 `BENCHMARK_PRODUCT_CODE_MISSING`。

本 Skill 的全部带时间戳 CSV（多对标明细、关键词母池、每个 ASIN 原始表、所有对标自然排名关键词）及其 `.meta.json` 必须先写入 `_system/staging/{RUN_TIMESTAMP}_build`，通过完整性、身份、Schema、覆盖数和时间戳校验后，由公共发布器原子发布到 `data/`。`data/` 只保留当前 LATEST VALID Batch；旧 VALID Batch 整包移动到 `历史数据/{旧RUN_TIMESTAMP}/`，不再向 Skill 根目录复制业务 CSV，也不覆盖同名历史文件。

覆盖数、最佳排名 MIN 和排名中位数 MEDIAN 均由程序计算。一个词在 N 个 Benchmark 出现，市场容量与竞争产品数仍各保留一份，不乘 N。明细中的全部唯一 `Id` 必须在母池恰好出现一次；冲突或覆盖校验失败不得标记 `FULL_SUCCESS`。

正式文件名、RUN_ID 和 Sidecar 共用同一 `RUN_TIMESTAMP`；`data/` 不创建时间戳子文件夹，历史归档按 Batch 使用 `历史数据/{RUN_TIMESTAMP}/`。Sidecar 复用现有 Stage 6 metadata，并记录 `BenchmarkRawOrganicFiles`、`BenchmarkRawOrganicFileCount`、`BenchmarkOrganicSummaryFile`、`BenchmarkOrganicSummaryRecordCount`、`PerBenchmarkObservationCounts`、`BenchmarkASINs`、`BenchmarkProductCodes`（ASIN→ERP数字编号）。每 ASIN 原始行数、汇总中该 ASIN 行数都必须等于 A 明细中该 ASIN 有效 Observation 数；汇总总数必须等于 A 明细总数。A、B、N 张原始表、汇总表及所有 sidecar 任一缺失、身份不符或覆盖不符时，该 Run Package 不得成为 latest-valid。文件名包含时间戳，禁止覆盖既有文件。6-0-2 消费 A 全部Observation；6-0-6 通过 6-0-2 的每Benchmark高度精准 D 表消费已判断的词，不再直接读取本 Skill 的 A 明细。后续输入必须按 Product Root、Skill ID、Report Identity、Schema、状态、完整包和覆盖校验筛选，再按最新有效 `Generated_At`/文件名时间选择；不得按 mtime、首个文件或跨产品选择。通用版本规则见 `../references/stage6-artifact-contract.md`。

实现和验证见 `scripts/benchmark_organic_extract.py`、`references/field-contract.md` 与 `tests/`。


## Global report layout

All formal 6-0-1 CSVs and metadata sidecars are published to the `data/` directory of `06_SKILL分析报告/6-0-1_对标自然排名关键词提取/` only after a VALID batch check. The four CSV name patterns above begin with `6-0-1_` and share one `YYYYMMDD_HHMMSS` timestamp. Historical batches are stored under `历史数据/{RUN_TIMESTAMP}/`; manifests, metadata, registry, staging and logs stay under `_system/`.

## 导出 CSV 输入模式

提供 ERP 导出的对标词 CSV 时，使用 --input-csv，601 跳过 ERP 连接，按 PickPwKView 字段映射读取该文件；其它输入、过滤、翻译、校验和输出血缘保持不变。


