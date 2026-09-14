# HZP Amazon 6-2｜广告诊断优化

## 30 秒运行

```text
使用 6-2 Skill
产品：P001
Products Root：E:\【产品总目录】
广告数据窗口：近 30 天（如已确认）
```

6-2 用于广告已经产生真实数据后，诊断曝光、点击、转化、CPC、ACoS、放量、Campaign、关键词、Search Term、Placement 和预算问题，给出有证据的最小必要调整。

运行前需要：

- `[Product Root]/01_产品档案.md`
- `[Product Root]/04_产品推广思路.md`
- Products Root 下的只读身份主表：`00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`；先按共享身份规则解析并验证 Store、Marketplace、ASIN、SKU
- 最新有效的 6-1 报告及《6-2输入交接包》
- `[Product Root]/05_分析源数据/` 中的 Amazon Ads 导出
- 可用时提供 `[Product Root]/07_产品资料/` 的价格、促销、Review、库存和页面变更资料

6-2 会先确认广告数据的实际时间范围和产品阶段，再按曝光→点击→转化→经济性→规模找断点。它不会因为 ACoS 高、CTR 低、CVR 低或 0 订单就机械降 Bid、改主图或加 Negative；数据不足时会明确标记并允许“暂不调整”。

店铺身份遵循 Amazon 行业共享规则 `Amazon产品身份解析规则.md`；映射表只读，身份冲突或 SellerSpace 验证未完成时不把广告数据归到错误产品。

## 输出

正式报告写入：

`[Product Root]/06_SKILL分析报告/6-2_[产品编号]_广告诊断优化_Vx_YYYYMMDD_HHMMSS.html`

报告包括广告诊断结论、曝光/点击/转化/经济性/放量、Campaign、Keyword/Target、Search Term 生命周期、Keyword Mother Pool、Semantic/Purchase Intent Clusters、Expansion Batch、Placement、预算、页面路由、每日调整状态、操作卡、人工决策、1/3/7 天验证、证据充分性、优化动作和条件满足时的 6-3 交接包。运行日志写入 `06_SKILL分析报告/广告表现汇报优化日志/`，不进入正式报告索引。正式报告成功后自动调用 0-2 更新索引；6-2 不自行维护 `index.html`。

详细字段和边界见同目录的 `SKILL.md`、`references/diagnosis-framework.md`、`references/handoff-schema.md` 和 `templates/report-outline.md`。


## 证据驱动扩词

6-2 只在真实成交语义方向出现并通过证据验证后，回查 6-1 的 Keyword Mother Pool，分批生成 Expansion Proposal；每批联动 Match Type、Bid、预算和库存约束，须经用户批准后执行。
### Portfolio 范围

6-2 以已验证的 Portfolio Name/ID、Store、Marketplace、Own ASIN/SKU 作为广告诊断边界。错组合允许只读审计但禁止写入；扩词和扩展 Campaign 继承 6-1 Portfolio。

6-2 复用共享身份解析：Product_NewCode→正式 Product_Code→Portfolio→Var_Code→Campaign。变体 Child ASIN/SKU 映射缺失或冲突时只读诊断，不跨变体扩展；Benchmark 和 Product Target ASIN 不作为自有身份。

命名读取使用共享 `parse_campaign_name()`；新名称按当前标准解析，旧名称分为 `LEGACY_RECOGNIZABLE` 或 `LEGACY_UNKNOWN`。6-2 不因旧名称拒绝分析，也不会因 Bid、Budget 或扩词自动改名。
