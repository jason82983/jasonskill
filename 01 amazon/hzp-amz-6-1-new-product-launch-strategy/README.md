# HZP Amazon 6-1｜新品推广方案

## 30 秒运行

```text
使用 6-1 Skill
产品：P001
Products Root：E:\【产品总目录】
```

6-1 用于已经具备页面基础的 Amazon 新品，设计首阶段流量、广告测试、预算、价格/促销协同和继续/停止规则。

运行前需要：

- `[Product Root]/01_产品档案.md`
- `[Product Root]/04_产品推广思路.md`（没有时会标记待确认）
- 通过状态的最新 5-4 页面审核报告
- 可用时提供 `[Product Root]/05_分析源数据/03_关键词数据/` 和 `07_产品资料/` 中的真实推广资料

5-4 页面未通过时，6-1 会停止正常大规模推广方案并要求返回 5-4；不会用烧广告替代页面修正。数据不足时可以形成证据有限的小规模验证方案，但不会编造预算、CPC、CVR、ACoS、销量或订单。

## 输出

正式报告写入：

`[Product Root]/06_SKILL分析报告/6-1_[产品编号]_新品推广方案_Vx_YYYYMMDD_HHMMSS.html`

报告包括推广核心战略、核心推广假设、关键词地图、流量—页面承接矩阵、Campaign 结构、预算逻辑、价格—推广关系、验证表、继续/停止规则、首阶段执行清单、观察指标和 6-2 交接包。正式报告成功后自动调用 0-2 更新索引；6-1 不自行维护 `index.html`。

详细字段和边界见同目录的 `SKILL.md`、`references/launch-framework.md`、`references/handoff-schema.md` 和 `templates/report-outline.md`。
