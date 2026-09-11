# 6-2 诊断框架

## 版本与窗口

- 读取同一 Product Root 的 `01_产品档案.md`、`04_产品推广思路.md` 和最新有效 6-1 正式报告。
- 版本化文件按 `Product Code + Skill 编号` 匹配，最大 V 优先；同 V 按文件名 `YYYYMMDD_HHMMSS` 最新。不得按 filesystem 时间、目录顺序或 first found 选取。
- 排除 `index.html`、失败、incomplete、invalid、deprecated、draft、preview、temp、test 和非正式报告。有效性不确定时标记 `[上游报告有效性无法确认]`，不静默回退旧版。
- 广告数据必须写明实际窗口和产品阶段；不同窗口不可无说明混比。

## 广告数据发现

主动扫描 `05_分析源数据` 中的 Campaign、Search Term、Targeting、Advertised Product、Placement、Purchased Product、Budget、Keyword、ASIN Targeting 等导出，并检查 `07_产品资料` 的价格、Offer、Review、Rating、库存、Buy Box、页面/价格/促销变化和运营记录。以真实字段为准，不因文件名猜测语义。

## 漏斗断点

先判主要断点：曝光 → 点击 → 转化 → 广告经济性 → 流量规模。

- 无曝光：资格、索引/相关性、状态、Target、Match Type、Budget、Bid、搜索量、库存、Buy Box 和竞争环境。
- 有曝光没点击：意图、主图、Title、价格、Rating、Review、Offer、Placement 和竞争页面。
- 有点击无订单：先区分流量错与页面接不住，再查产品、价格、Review、Offer 和竞争。
- 高 ACoS：按 Campaign 原始目的、流量质量、商业价值、数据量和可放大性解释；不机械降 Bid。
- 赚钱不等于能放量：检查流量规模、曝光份额、Bid/Budget、Organic Rank、页面承接和库存。

## 下钻字段

Campaign、Ad Group、Keyword/Target、Search Term 和 Placement 分层记录实际存在的 Campaign、Match Type、ASIN、Status、Budget、Bid、Impressions、Clicks、CTR、CPC、Spend、Orders、Sales、CVR、ACoS、ROAS。Campaign 平均只能作为入口，必要时必须下钻 Search Term。

## 动作与证据

诊断状态只用 `【证据充分】`、`【初步信号】`、`【证据不足】`。动作优先级是广告优化专用的 `【P0｜立即处理】`、`【P1｜高优先级】`、`【P2｜观察/优化】`；不是产品或页面阶段优先级。

允许动作：暂不调整/继续收集、继续观察、扩大验证、提高/降低 Bid、转 Exact、Negative 候选、暂停、进入页面诊断、进入结构调整、进入资格排查。任何 Bid 或 Budget 动作都要说明要解决的问题和依据。0 订单不自动 Negative；意图错误或证据充分长期无价值才提出 Negative 候选。

不得统一使用 10/20/30 点击停词阈值；结合售价、毛利、CPC、测试目的、关键词价值、样本量和风险承受能力。一次优先只改一个可解释变量；最小问题做最小修改。

## 时间波动与路由

单日波动检查曝光、点击、CPC、Spend、Budget、Search Term、Placement、CVR、Organic、价格、Coupon、Review、库存、Buy Box、页面和竞争变化。严重资格/商品状态异常先标记 `[广告资格待排查]`。多个核心高意图流量同时出现明确 CTR/CVR 承接问题，才标记 `【页面承接问题明显｜返回5-4优化】`；单个词失败不推倒整页。
