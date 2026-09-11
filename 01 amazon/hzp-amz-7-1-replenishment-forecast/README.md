# HZP Amazon 7-1｜补货预测

## 30 秒运行

```text
使用 7-1 Skill
产品：P001
Products Root：E:\【产品总目录】
```

7-1 根据真实库存、销售速度、在途状态、完整 Lead Time、推广/促销计划和安全库存，判断何时下单、补多少、到货前是否会断货，以及积压和现金风险。

运行前准备：

- `[Product Root]/01_产品档案.md`
- 最新有效的 6-3 报告，优先《7-1输入交接包》
- `[Product Root]/05_分析源数据/` 的库存、销售、采购、物流和供应商数据
- `[Product Root]/07_产品资料/` 的补货、生产、运输、促销和季节资料

Skill 会区分 Available、Reserved、Inbound、在途和计划补货，按真实时间判断“及时可售”，并输出需求情景、Lead Time、Safety Stock、Reorder Point、补货量和断货/积压风险。缺少关键数据时会标记【关键数据不足｜暂无法形成可靠补货预测】，不会编造库存、销量、MOQ、物流时效或未来订单。

正式报告写入：

`[Product Root]/06_SKILL分析报告/7-1_[产品编号]_补货预测_Vx_YYYYMMDD_HHMMSS.html`

报告成功后自动调用 0-2 更新当前产品索引；7-1 不自行维护 `index.html`。7-2 负责后续库存风险管理。
