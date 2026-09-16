# 6-0-1 多对标字段与资产契约

## 身份解析

Product_Code 模式定位当前产品唯一 `01_产品档案.md`，从明确的“对标产品”段落读取 1..N 对标 ASIN 与 ERP ProId；不得按名称、文件名或相似产品补齐。每个 Benchmark 有稳定 `Benchmark_Code` 和 ASIN。档案里有显式对标编码时沿用；没有时以显式 ASIN 构造确定性 `ASIN_<ASIN>` 编码，不随机生成。每个已确认 ProId 独立调用共享 ERP Adapter 的参数化只读 SELECT。

PickPwKView 不提供 ASIN 字段。ASIN 和 Benchmark Code 只作为配置身份及输出证据，不假装来自 View。缺少 ASIN / ProId、身份重复或冲突时 fail closed。

## Keyword Entity Identity

`PickPwKView.Id` 是源 View 行身份，只用于识别同一 ProId 查询中的重复/冲突行；不得作为跨 ProId Keyword Entity ID。

用户明确确认 `PickPwKView.KwId` 跨 ProId 对同一个关键词稳定且唯一。故多对标资产统一使用 `KwId` 作为 `Id`（Keyword Entity ID）。此确认仅用于跨产品关键词实体归并，不代表 `KwId` 是可写 `PickPwK.Id`，也不代表它能代替 6-0-4 的写入主键。写入操作仍必须提供并核验真实 `PickPwK.Id`。

## 市场事实与排名观察

关键词市场事实为 `KwId` 唯一的一份：`Id,词,中文,市场容量,竞争产品数,供需比`。固定来源为 `Keyword`, `KeywordCn`, `SearchVolume30`, `AsinQuantity`；供需比只由程序计算 `SearchVolume30 / AsinQuantity`，保留四位小数。竞争产品数 NULL 不补 0，分母小于等于 0 时比例留空。

Benchmark Observation 是一对 `(KwId, Benchmark_Code)` 的真实 `RankOra`。自然排名字段语义已确认。只保留自然排名可解析且 >=1、市场容量可解析且 >100 的行。

## 正式输出

FILE A：多对标关键词排名明细，一行一个 `KwId × Benchmark Observation`，固定九列：

`Id,词,中文,市场容量,竞争产品数,供需比,对标编号,对标ASIN,自然排名`

`对标编号`填写对应 Benchmark 在当前产品档案中的 `benchmark_erp_pro_id` ERP 数字编号；内部 `Benchmark_Code` 仅保留在输入血缘和元数据中用于稳定识别，不写入该表列。

FILE B：对标关键词母池，一行一个唯一 `KwId`，固定九列：

`Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数`

每个有效 ASIN 的原始表：一 ASIN 一文件，字段沿用 FILE A 的九列；`对标编号`填写档案中该 ASIN 的 ERP `benchmark_erp_pro_id`，文件名为 `{ASIN}+关键词自然排名_{RUN_TIMESTAMP}.csv`。只含该 ASIN 自身的合格 Observation。

汇总表：`所有对标自然排名关键词汇总_{RUN_TIMESTAMP}.csv`。不包含`对标编码`列，保留`对标编号`，并追加 `ASIN,产品编号` 两列。ASIN 来自对应 Benchmark Observation 的已解析 Benchmark ASIN；`产品编号`按该 ASIN 从当前产品档案对应 Benchmark 项读取 `benchmark_erp_pro_id` 数字编号。

汇总表是各单 ASIN 原始表的 UNION ALL。相同 Keyword 出现在不同 ASIN 时保留多行；不得按 Keyword 或 KwId 去重。市场事实仍仅在 FILE B 中按唯一 KwId 保留一次。

覆盖数是该 KwId 下有有效排名的 Benchmark 数；最佳排名为 MIN，中位数为 MEDIAN。一个词在多个 Benchmark 出现时，市场容量、竞争产品数、供需比只保留一份，绝不按 Benchmark 数累加。FILE A 中所有不同 `KwId` 必须在 FILE B 恰好出现一次。

同一 `KwId` 的关键词文本、SearchVolume30 或 AsinQuantity 冲突时返回 `KEYWORD_MARKET_FACT_CONFLICT` / `KEYWORD_ENTITY_ID_CONFLICT`，不能静默挑一边；同一 `KwId × Benchmark_Code` 出现冲突观察时返回 `BENCHMARK_OBSERVATION_CONFLICT`。冲突时两个资产均不得标记 `FULL_SUCCESS`。

所有 CSV 使用 UTF-8 with BOM、同一 `RUN_ID/RUN_TIMESTAMP` 和各自 `.meta.json`，放在 `6-0-1_对标自然排名关键词提取/{RUN_TIMESTAMP}/`。除 FILE A/B 外，本次有效对标有 N 个时，必须有 N 张单 ASIN 原始表和 1 张汇总表。Sidecar 复用共享 Stage 6 metadata，并增加 `BenchmarkRawOrganicFiles`、`BenchmarkRawOrganicFileCount`、`BenchmarkOrganicSummaryFile`、`BenchmarkOrganicSummaryRecordCount`、`PerBenchmarkObservationCounts`、`BenchmarkASINs`、`BenchmarkProductCodes`（ASIN 到该 Benchmark ERP 数字编号的映射）。latest-valid 校验要求 A/B、N 张原始表、汇总表及所有同 RUN_ID 成功 sidecar 齐全，并核验 ERP 编号映射、ASIN 隔离、逐 ASIN 数量和汇总总数。6-0-2 仍只读取 FILE B；6-0-6 仍只读取 FILE A。601 每次从 ERP 重新读取；历史 601 CSV 不能代替当前 live query。
