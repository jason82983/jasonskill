# 6-0-2｜AI精准关键词识别

Machine Name：`hzp-amz-6-0-2-ai-precision-keyword-identification`

按 Canonical Keyword 对 6-0-1 的全部 Benchmark Observation 只判断一次，直接输出四级精准度：`高度精准`、`精准`、`弱精准`、`不精准`。`JudgmentStatus` 独立为 `SUCCESS`、`REVIEW_REQUIRED`、`FAILED`，不是第五级精准度。

共享筛选配置固定读取：
`E:\【所有产品目录专用】\01_公共资料\03_系统配置\生成精准词库的要求.txt`

配置中的 `已精准` 规范化为 `精准`。缺失、为空或包含未知级别时，真实运行分别失败为 `PRECISION_LIBRARY_CONFIG_NOT_FOUND`、`PRECISION_LIBRARY_CONFIG_EMPTY`、`CONFIG_PRECISION_LEVEL_INVALID`；不得静默使用默认等级。配置只决定筛选，不改变 AI 判断。

正式观察列：`所属产品编号`｜`对标ASIN`｜`Id`｜`词`｜`中文`｜`市场容量`｜`竞争产品数`｜`供需比`｜`自然排名`｜`精准度`｜`精准原因`。

一次 Run 生成同一时间戳的五类 UTF-8 with BOM 资产：

- A `6-0-2_精准判断所有词表_{timestamp}.csv`：全部 Benchmark×Keyword Observation，保留四级精准度。
- B `6-0-2_筛选后的对标精准词_{timestamp}.csv`：A 按配置等级筛选，保留对标维度。
- C `6-0-2_去重_筛选后的对标精准词_{timestamp}.csv`：B 按“所属产品编号 + Canonical Keyword”去重，仍保留对标维度。
- D `6-0-2_去对标去重_筛选后的精准词_{timestamp}.csv`：B 按 Canonical Keyword 去重并移除对标字段，唯一供 6-0-3 使用。
- E `6-0-2_{所属产品编号}_筛选后的精准词_{timestamp}.csv`：B 按对标产品编号拆分，供 6-0-6 使用；不假设只有“高度精准”。

B/C/D/E 均为程序派生，不重新调用 AI。Run Manifest 保存配置原文、规范化等级、路径和指纹，以及输入、输出、覆盖和回读校验。旧批次保留，失败批次不得发布为有效数据。602 不查询 ERP、不执行广告或 ERP 写操作。

