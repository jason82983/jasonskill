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
- 最新有效的 6-1 报告及《6-2输入交接包》
- `[Product Root]/05_分析源数据/` 中的 Amazon Ads 导出
- 可用时提供 `[Product Root]/07_产品资料/` 的价格、促销、Review、库存和页面变更资料

6-2 会先确认广告数据的实际时间范围和产品阶段，再按曝光→点击→转化→经济性→规模找断点。它不会因为 ACoS 高、CTR 低、CVR 低或 0 订单就机械降 Bid、改主图或加 Negative；数据不足时会明确标记并允许“暂不调整”。

## 输出

正式报告写入：

`[Product Root]/06_SKILL分析报告/6-2_[产品编号]_广告诊断优化_Vx_YYYYMMDD_HHMMSS.html`

报告包括广告诊断结论、曝光/点击/转化/经济性/放量、Campaign、Keyword/Target、Search Term、Placement、预算、页面路由、证据充分性、优化动作和条件满足时的 6-3 交接包。正式报告成功后自动调用 0-2 更新索引；6-2 不自行维护 `index.html`。

详细字段和边界见同目录的 `SKILL.md`、`references/diagnosis-framework.md`、`references/handoff-schema.md` 和 `templates/report-outline.md`。
