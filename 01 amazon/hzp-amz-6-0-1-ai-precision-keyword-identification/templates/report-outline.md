# 6-0-1 精准关键词识别报告结构

如当前运行链生成正式 HTML，内容限于：

1. 产品身份、ERP ProId、查询时间和数据状态
2. 输入版本追溯与 PickPwKView 字段语义
3. 手动分类精准词 CSV 摘要与源字段
4. AI 精准词 CSV 摘要（最终仅六列，AI 只保留 PRECISION；自动编号遵循 Schema 记录身份规则）
5. 内部 AI 三态与人工对照（不写入最终 CSV）
6. 失败状态、数据缺口和后续路由 6-0-2
7. 关键词来源运行摘要（不进入最终六列 CSV）：`Keyword Source Mode`、Own/Benchmark 候选数、去重数，以及 Benchmark-only 词缺少当前 ERP 记录的数量；无自有词且无明确 Benchmark 时显示 `CURRENT_KEYWORDS_UNAVAILABLE_NO_BENCHMARK`
8. Benchmark 证据与当前产品证据分层说明：Benchmark 只能扩展候选和提供辅助证据，最终 Precision 仍由当前产品 Search Intent Fit 决定；当前产品与 Benchmark 可分别保留真实 Record ID，来源 ProId 不作为写回阻断条件

9. 当前产品语义画像与判断边界：说明产品类型、对象/关系、核心功能、场景、关键属性/兼容性和已确认的 Hard Intent Conflict；分别列出 `PRECISION`、`NOT_PRECISION`、`REVIEW_REQUIRED` 的语义理由。搜索量、广告表现、订单、排名与 Benchmark 仅作为 Supporting Evidence，不得写成精准核心理由；未确认字段写 `DATA_NOT_AVAILABLE`。

不得在 6-0-1 报告内生成精准泛词、关键词族、Broad Seed、Rankability 或广告执行建议。双轨 CSV 保存于 `06_SKILL分析报告/6-0-1_精准关键词识别/`，不进入 0-2 正式索引。
