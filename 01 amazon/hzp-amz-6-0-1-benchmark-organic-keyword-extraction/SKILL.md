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

使用共享 `scripts/erp_keyword_adapter.py`，只读参数化 `PickPwKView.ProId`。不得把 Product_Code 或 ASIN 当作 ProId，不得以历史导出代替当前查询。`PickPwKView.Id` 是源行身份；用户已确认 `KwId` 跨 ProId 稳定唯一，因此正式多对标资产的 `Id` 是 Keyword Entity ID (`KwId`)。`KwId` 不是 PickPwK 写入行主键；6-0-4 需要真实 `PickPwK.Id`。

## 事实和过滤

Keyword Market Fact 一词一份：`Keyword`、`KeywordCn`、`SearchVolume30`、`AsinQuantity`；供需比由代码计算 `SearchVolume30 / AsinQuantity`，四位小数。Benchmark Observation 按一个 Keyword Entity × 一个 Benchmark Code 记录真实 `RankOra`。字段语义及冲突策略见 [field contract](references/field-contract.md)。

`中文`字段优先使用 ERP `KeywordCn`。对符合筛选条件但 `KeywordCn` 为空的关键词，运行时必须调用已配置的英文→简体中文翻译提供方补齐，并在写出前复核每条合格记录均有非空中文；已有 `KeywordCn` 不得覆盖。翻译只补充展示字段，不参与筛选、排序、Keyword Entity、市场事实、排名或任何语义判断。翻译提供方不可用、翻译失败或仍有空值时返回 `KEYWORD_CN_TRANSLATION_INCOMPLETE`，该 Run 不得标记 `FULL_SUCCESS`，不得用英文原词、关键词字面拆解或臆测中文替代翻译。

继续使用既有合法筛选：`RankOra >= 1` 且 `SearchVolume30 > 100`。保留所有合格 Keyword；不做 AI 精准度判断、关键词语义去重、聚类、推广或写操作。相同 `KwId` 的市场容量/竞争产品数冲突时报告 `KEYWORD_MARKET_FACT_CONFLICT`，不得任选或静默覆盖。

## 正式输出

生成同一运行的 A/B 两份既有资产、每个有效 ASIN 一份原始 CSV，以及一份 Observation 汇总 CSV；所有正式文件使用 UTF-8 with BOM 并写各自 `.meta.json`：

1. `6-0-1_多对标关键词排名明细_YYYYMMDD_HHMMSS.csv`，固定九列：`Id,词,中文,市场容量,竞争产品数,供需比,对标编号,对标ASIN,自然排名`。一行一个 Keyword × Benchmark rank observation；`对标编号`是当前产品档案中该 Benchmark 的 ERP 数字编号（`benchmark_erp_pro_id`）。
2. `6-0-1_对标关键词母池_YYYYMMDD_HHMMSS.csv`，固定九列：`Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数`。一行一个唯一 Keyword Entity，是 6-0-2 唯一正式关键词输入。
3. 每个有效对标 ASIN 单独生成 `6-0-1_{ASIN}_关键词自然排名_YYYYMMDD_HHMMSS.csv`，固定沿用 A 表九列 schema。`对标编号`与该 ASIN 对应的 ERP 编号一致。
4. `6-0-1_所有对标自然排名关键词_YYYYMMDD_HHMMSS.csv`，不包含`对标编码`列，保留`对标编号`，并追加 `ASIN,产品编号`。内容是 N 张 ASIN 原始表的 UNION ALL；不按词或 Id 去重。`产品编号`为该 ASIN 在 `01_产品档案.md` 对应 Benchmark 配置中的 ERP 数字编号（`benchmark_erp_pro_id`）；缺失时返回 `BENCHMARK_PRODUCT_CODE_MISSING`。

本 Skill 的全部带时间戳 CSV（多对标明细、关键词母池、每个 ASIN 原始表、所有对标自然排名关键词）除保留在本次 Run 的规范资产目录外，还必须以同一文件名复制到 `06_SKILL分析报告/6-0-1_对标自然排名关键词提取/` 外层，作为人工查看的历史与最新可见文件；每个副本同时复制对应 `.meta.json`。外层副本不改变规范 Run Package 的身份、覆盖校验或历史保留规则，禁止覆盖同名历史文件。

覆盖数、最佳排名 MIN 和排名中位数 MEDIAN 均由程序计算。一个词在 N 个 Benchmark 出现，市场容量与竞争产品数仍各保留一份，不乘 N。明细中的全部唯一 `Id` 必须在母池恰好出现一次；冲突或覆盖校验失败不得标记 `FULL_SUCCESS`。

所有 CSV 直接写入 `06_SKILL分析报告/6-0-1_对标自然排名关键词提取/`，不创建时间戳子文件夹。文件名、RUN_ID 和 Sidecar 共用同一 `RUN_TIMESTAMP`。Sidecar 复用现有 Stage 6 metadata，并记录 `BenchmarkRawOrganicFiles`、`BenchmarkRawOrganicFileCount`、`BenchmarkOrganicSummaryFile`、`BenchmarkOrganicSummaryRecordCount`、`PerBenchmarkObservationCounts`、`BenchmarkASINs`、`BenchmarkProductCodes`（ASIN→ERP数字编号）。每 ASIN 原始行数、汇总中该 ASIN 行数都必须等于 A 明细中该 ASIN 有效 Observation 数；汇总总数必须等于 A 明细总数。A、B、N 张原始表、汇总表及所有 sidecar 任一缺失、身份不符或覆盖不符时，该 Run Package 不得成为 latest-valid。文件名包含时间戳，禁止覆盖既有文件。6-0-2 消费 A 全部Observation；6-0-6 通过 6-0-2 的每Benchmark高度精准 D 表消费已判断的词，不再直接读取本 Skill 的 A 明细。后续输入必须按 Product Root、Skill ID、Report Identity、Schema、状态、完整包和覆盖校验筛选，再按最新有效 `Generated_At`/文件名时间选择；不得按 mtime、首个文件或跨产品选择。通用版本规则见 `../references/stage6-artifact-contract.md`。

实现和验证见 `scripts/benchmark_organic_extract.py`、`references/field-contract.md` 与 `tests/`。


## Global report layout

All formal 6-0-1 CSVs and metadata sidecars are stored directly in `06_SKILL分析报告/6-0-1_对标自然排名关键词提取/`. The four CSV name patterns above begin with `6-0-1_` and share one `YYYYMMDD_HHMMSS` timestamp. No timestamp subfolder is created.
