# 6-0-2｜AI精准关键词识别

Machine Name：`hzp-amz-6-0-2-ai-precision-keyword-identification`

判断依据仍是当前产品识别文本与 Searcher Intent。正式读取 6-0-1 最新有效的 `BENCHMARK_KEYWORD_POOL`；`Id=KwId` 表示跨 ProId 稳定唯一的关键词实体，一行只判断一次。市场事实原样透传；覆盖数、最佳自然排名、中位排名只作 Reality Evidence，不自动抬高或降低精准度。

精准度直接裁决为四级：`高度精准`、`精准`、`弱精准`、`不精准`。CSV Coverage Check 记录 `INPUT_RECORD_COUNT` 与 `OUTPUT_RECORD_COUNT`，要求每个输入关键词恰好对应一条全量判断结果。

输出文件：

- `AI精准词`：`Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准度,精准原因`
- `AI高度精准词`：与全量文件同 Schema，只保留高度精准行，供 6-0-3 使用。

两份资产同一时间戳与 RUN_ID，UTF-8 with BOM，字段事实按 Id 与 6-0-1 母池逐值比对。`KwId` 不是 6-0-4 的 PickPwK 写入行主键。运行契约见 `SKILL.md` 和 `../references/stage6-artifact-contract.md`。
