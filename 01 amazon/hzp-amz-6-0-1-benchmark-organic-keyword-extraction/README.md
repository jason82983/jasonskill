# HZP Amazon 6-0-1｜对标自然排名关键词提取

Machine Name：`hzp-amz-6-0-1-benchmark-organic-keyword-extraction`

从当前产品档案获取 1..N 个 Benchmark 身份，对每个明确 ProId 实时只读查询 PickPwKView，并分开保存唯一 Keyword Market Fact 与每个 Benchmark 的真实 Organic Rank Observation。

正式输出包含 A/B 两份既有资产，以及按实际有效对标数量生成的 N 张 ASIN 原始表和一张观察汇总表。所有 CSV 放在 `6-0-1_对标自然排名关键词提取/{YYYYMMDD_HHMMSS}/` Run Folder 内，共用同一时间戳、RUN_ID，并各自带 `.meta.json`：

- `多对标关键词排名明细`：`Id,词,中文,市场容量,竞争产品数,供需比,对标编号,对标ASIN,自然排名`，一行一个 Keyword × Benchmark；`对标编号`为产品档案中该对标的 ERP 数字编号。
- `对标关键词母池`：`Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数`，一行一个唯一 Keyword Entity，供 6-0-2 消费。
- 每个有效对标 ASIN 各一张 `{ASIN}+关键词自然排名_{timestamp}.csv`，沿用 A 表的九列 Observation schema，只含该 ASIN 合格记录。
- `所有对标自然排名关键词汇总_{timestamp}.csv`：不含`对标编码`，保留`对标编号`，并追加 `ASIN,产品编号` 两列。按 UNION ALL 合并各 ASIN 原始表；ASIN 取 Observation 身份，产品编号取产品档案中该对标对应的 ERP 数字编号。

用户已确认 `PickPwKView.KwId` 是跨 ProId 稳定唯一的 Keyword Entity ID；资产 `Id` 使用 KwId，源行 `PickPwKView.Id` 不等同于 6-0-4 可写 PickPwK.Id。逐 ASIN 原始表及汇总表由本轮过滤后的 Observation 直接生成，不另查 ERP。逐 ASIN原始数、汇总 ASIN 数及总数必须与本轮 A 明细覆盖一致。汇总表的产品编号按 ASIN 从产品档案对应 Benchmark 项读取其 ERP 数字编号。Metadata 记录 ASIN 原始文件列表、文件数、汇总文件/记录数、ASIN→ERP编号映射和逐 ASIN Observation 数。6-0-2 继续只消费 B 母池；6-0-6 继续只消费 A 明细。所有输出时间戳、输入血缘、latest-valid 规则见 `../references/stage6-artifact-contract.md`。实现见 `scripts/benchmark_organic_extract.py`。
