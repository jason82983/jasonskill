# 《7-1输入交接包》

仅交接真实运营事实和趋势，不交接伪造的补货数量或完整预测。至少包含：

- Product Code、产品名称、Marketplace、Products Root、Product Root；沿用 Amazon 产品身份解析规则记录的 Store、ASIN、`Mapped_SKUs[]`、`Advertised_SKUs[]`、SKU_Count、映射来源和 MCP 验证状态。多个 SKU 对应同一 ASIN 时只交接一个 ASIN 视图，并保留 SKU 异常下钻。
- 6-6 报告版本、监控窗口、产品阶段
- 当前运营状态、销量状态、真实可算的 Sales Velocity
- Available、Reserved、Inbound、Total Inventory、OOS 状态和库存风险
- 广告是否计划放量、广告/自然结构、销量趋势、价格/Coupon/Promotion 变化
- Review、Buy Box、竞品和异常因素
- 数据来源、字段、日期窗口和缺口
- 7-1 需重点验证的问题

每个字段标注 `[原始运营数据]`、`[已确认事实]`、`[分析推断]`、`[推算指标]` 或 `[证据不足]`。库存数据不足时仍可生成交接包，但必须明确 `[库存数据不足]` 或 `[销售速度数据不足]`。

## 版本追溯

正式 HTML 的《输入版本追溯》至少记录：

| Skill编号 | 中文名称 | 文件名 | 版本 | 文件名时间戳 | 输入类型 | 用途 |
|---|---|---|---|---|---|---|
| 6-2 | HZP Amazon 6-2｜新品推广方案 | 实际文件 | Vx | YYYYMMDD_HHMMSS | 【核心输入】 | 推广目标与假设 |
| 6-4 | HZP Amazon 6-4｜广告诊断优化 | 实际文件 | Vx | YYYYMMDD_HHMMSS | 【辅助回查】 | 广告状态与已知问题 |

只列实际读取的文件；没有文件时写 `[缺失]`，不能补写版本。


## 阶段6闭环字段

交给 7-1/7-2 或其他责任 Skill 时补充：今日产品运营结论、当前增长阶段、放量资格、广告依赖、Coupon 依赖、核心关键词资产、自然增长状态、增长飞轮证据、最重要动作、责任 Skill、人工介入和验证窗口。

运行日志字段至少包含 Product Code、ASIN、日期、Skill、目标、数据窗口、来源、Campaign/Ad Group、Keyword/Search Term、指标、AI诊断、建议、人工决策、最终动作、执行方式、1天/3天/7天结果、最终验证结论和后续动作；保存到 `06_SKILL分析报告/广告表现汇报优化日志/`。
- Portfolio Name、Portfolio ID、Portfolio Status、Store/Marketplace、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[] 和读取来源/时间。
- 分开交接 Portfolio Ad Sales、Portfolio Ad Orders 与 Product Total Sales、Product Total Orders；Portfolio Identity Anomaly 的证据、影响和路由。

## 经营周期与对比字段（新增）

交接时必须记录本次实际参数，避免下游误把不同窗口相加：

- Report Mode：`RECENT_3D`、`RECENT_7D`、`RECENT_14D`、`RECENT_30D`、`WEEKLY` 或 `DATE_RANGE_CUSTOM`
- Current Start、Current End、Report Days、Today Included
- Comparison Mode：`PERIOD_OVER_PERIOD`（环比）、`PERIOD_REFERENCE_COMPARE`（同比/同期）、`BOTH` 或 `NONE`
- Comparison Start、Comparison End、Reference Compare Start/End（如有）
- 每项指标的 Current、Previous/Reference、Change、Change % 或百分点变化，以及来源窗口

3 天、7 天、14 天同比按上个月对应日期；30 天同比按去年同一日期区间。自定义日期必须保留用户原始范围。缺失日期写 `[数据缺失]`，不得当作 0。
