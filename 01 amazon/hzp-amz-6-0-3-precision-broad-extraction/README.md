# 6-0-3｜精准泛词提取

Machine Name：`hzp-amz-6-0-3-precision-broad-extraction`

只读取 6-0-2 最新有效 `HIGH_PRECISION_KEYWORDS` 十一列资产。每个唯一 KwId 在一棵当前产品 Search Intent Tree 中映射一次。市场容量只按唯一 Keyword Fact 聚合，不乘 Benchmark 数；对标覆盖和排名字段从输入完整透传到映射结果。

两个输出：

- `词对应的精准泛词`：`Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准泛词,精准泛词中文`
- `精准泛词汇总`：仍为九列 `精准泛词,中文,层级,父精准泛词,直接搜索量,汇总搜索量,平均竞品数,意图机会比,直接对应词数`

使用同一 RUN_ID/RUN_TIMESTAMP 和 latest-valid 输入合同；同一 6-0-2 配套输出不得跨 Run 拼接。完整定义见 `SKILL.md`。
