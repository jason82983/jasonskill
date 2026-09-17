# 6-0-2｜AI精准关键词识别

Machine Name：`hzp-amz-6-0-2-ai-precision-keyword-identification`

读取当前产品识别文本和 6-0-1 最新有效 Run Package 的 `BENCHMARK_KEYWORD_ALL_OBSERVATIONS`。按 Canonical Keyword 只判断一次，再将同一判断回填到各 Benchmark × Keyword observation。市场事实不进入判断；覆盖数、排名只作 Reality Evidence。

精准度直接裁决为四级：`高度精准`、`精准`、`弱精准`、`不精准`。数据列包括市场容量、竞争产品数、供需比、对标覆盖数和自然排名证据。

所有输出直接写入固定目录 `06_SKILL分析报告/6-0-2_AI精准关键词识别/`，不创建时间戳子文件夹；一次 Run 输出同一时间戳的三张公共表和 N 张对标表：

- A `6-0-2_精准判断所有词表_{RUN_TIMESTAMP}.csv`：全量观察行，保留所属产品编号、对标 ASIN、Keyword Id、中文、市场容量、竞争产品数、供需比、自然排名、精准度和精准原因。
- B `6-0-2_高度精准词表_{RUN_TIMESTAMP}.csv`：从 A 严格筛选 `精准度=高度精准`，仍为观察行。
- C `6-0-2_去对标去重 高度精准词_{RUN_TIMESTAMP}.csv`：从 B 按 Canonical Keyword 输出唯一行，市场事实只保留一次且不含所属产品编号，供 6-0-3 唯一读取；Report Identity 为 `去对标去重 高度精准词`。
- D 每个所属产品编号各生成 `6-0-2_{所属产品编号}_高度精准词_{RUN_TIMESTAMP}.csv`，严格从 B 分组筛选，用于 6-0-6。

所有 CSV 使用 UTF-8 with BOM 编码，`run_manifest_{RUN_TIMESTAMP}.json` 与三张公共表和 N 张 D 表组成完整 Package。3+N 文件、Schema、观察覆盖、统一判断、筛选、去重、对标拆分和时间戳校验通过后才标记 `VALID`；历史 Run 文件保留。`KwId` 不是 6-0-4 的 PickPwK 写入行主键。
