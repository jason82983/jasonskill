---
name: hzp-amz-6-2-advertising-diagnosis-optimization
description: 基于真实 Amazon 广告数据诊断曝光、点击、转化、广告经济性、放量、Campaign、关键词、Search Term、Placement 和预算问题，给出有证据的最小必要调整并交接 6-3；没有可靠广告数据时不编造结论。
metadata:
  short-description: 诊断 Amazon 广告问题并输出最小必要优化动作
---

# HZP Amazon 6-2｜广告诊断优化

## 定位与边界

6-2 处理广告已经运行后的真实数据：先找曝光→点击→转化→广告经济性→流量规模的断点，解释为什么发生、证据是否足够、应该改什么或暂不调整。6-1 负责启动与验证设计，6-3 负责整体运营监控。

- 不重新完整制定 6-1，不重做页面策略、产品开发或完整运营监控。
- 不把 ACoS 高自动等同于失败，不把 CTR 低自动等同于主图差，不把 CVR 低自动等同于 Listing 差，不把 0 订单自动变成 Negative。
- 不修改 `04_产品推广思路.md`、原始广告数据、历史 HTML 或 `index.html`；正式报告完成后只调用 0-2。
- 一次运行连续完成已定义诊断，不要求用户逐阶段确认。

## 必读输入与数据发现

1. 使用本次确认的 Products Root、Product Root，读取 `01_产品档案.md` 和 `04_产品推广思路.md`。身份缺失或冲突时停止；禁止根据 ASIN、文件名或经验猜产品名称。
2. 从 `[Product Root]/06_SKILL分析报告/` 选择当前产品最新有效 6-1 正式 HTML，优先读取《6-2输入交接包》。按 Product Code + Skill 编号匹配，最大 V 优先，同 V 按文件名 `YYYYMMDD_HHMMSS` 最新；排除 index、失败、incomplete、invalid、deprecated、test、temp、preview、draft 和非正式输出。规则见 `references/diagnosis-framework.md`。
3. 主动扫描 `[Product Root]/05_分析源数据/`，优先识别 Campaign、Search Term、Targeting、Advertised Product、Placement、Purchased Product、Budget、Keyword 和 ASIN Targeting 等真实 Amazon Ads 导出。必须读取实际字段、数据日期和时间窗口；不能因为文件名相似就猜语义。
4. 主动检查 `[Product Root]/07_产品资料/` 的售价、Coupon、Promotion、Review、Rating、库存、Buy Box、页面变更、价格变更、广告调整记录和运营备注；只使用实际存在资料。
5. 按需辅助回查最新有效 5-4、5-1、5-2、5-3、2-1、2-2，核对页面承接、消费者意图、关键词相关性、产品事实和竞争环境，不重新完整运行上游 Skill。

正式 HTML 必须生成《输入版本追溯》，只记录实际读取的版本化报告；6-1 为【核心输入】，其他报告为【辅助回查】，历史比较才标【历史版本对照】。

## 核心诊断规则

- 任何结论先明确广告数据实际时间范围（近 1/7/14/30 天或自定义）和产品阶段（新品期/成长期/稳定期），禁止无说明混合窗口。
- 广告整体健康不等于能放量；Campaign 平均不能掩盖 Keyword、Target、Search Term 或 Placement 内部问题。
- 无曝光先排查广告资格、索引/相关性、状态、Target、Match Type、Budget、Bid、搜索量、库存、Buy Box 和竞争环境；高 Bid 无曝光不得无限加价。
- 有曝光没点击联合 Search Intent、主图、Title、价格、Rating、Review、Offer、Placement 和竞争页面判断；CTR 低不自动怪主图。
- 有点击无订单先区分流量错还是页面接不住，再检查产品、价格、Review、Offer 和竞争；CVR 低不自动怪 Listing。
- ACoS/ROAS/CPC/CVR 结合 Campaign 原始目的（探索型、验证型、核心增长型、收割型、竞品型、防御型）、流量质量、商业价值、数据量和可放大性解释。只有真实成本资料充分时才计算 Break-even ACoS。
- 0 订单先看点击量、Spend、意图、匹配、核心假设和样本量；明确意图错误或证据充分长期无价值时才提出 Negative 候选。Bid、Budget、Match Type、价格、Coupon、页面一次不要同时大改。
- Placement 必须区分 Top of Search、Rest of Search、Product Pages（数据存在时）；没有证据不得凭经验建议百分比调整。
- Budget 诊断区分 `Budget-limited`、`Demand-limited`、`Bid-limited`、`Conversion-limited` 和 `【证据不足】`，预算花不出去不自动等于应加预算。
- 单日波动要对比曝光、点击、CPC、Spend、Budget、Search Term、Placement、CVR、Organic、价格、Coupon、Review、库存、Buy Box、页面和竞争变化，不因一天变差就大改。

## 必须输出

按 `templates/report-outline.md` 生成正式 HTML，至少包含：《广告诊断结论》《输入版本追溯》、广告数据范围与完整性、6-1 原始推广目的、广告漏斗总览、《曝光诊断》《点击诊断》《转化诊断》《广告经济性诊断》《放量能力诊断》《Campaign诊断》《Keyword / Target诊断》《Search Term诊断表》《Placement诊断》《预算诊断》《广告—页面问题路由》《诊断证据充分性》《优化动作清单》《反方检查》、最终广告状态、《6-3输入交接包》（条件满足时）、数据局限和术语解释。

重要诊断只能标为 `【证据充分】`、`【初步信号】` 或 `【证据不足】`。动作使用广告优化优先级 `【P0｜立即处理】`、`【P1｜高优先级】`、`【P2｜观察/优化】`，每项记录所在层级、问题、证据、原因、最小动作、预期解决目标、风险、复查时间和复查数据。允许结论 `【暂不调整｜继续收集数据】`。

最终状态只允许：

- `【广告整体健康｜维持并继续观察】`
- `【存在明确优化机会｜执行局部调整】`
- `【广告结构存在问题｜建议重构部分推广结构】`
- `【页面承接问题明显｜返回5-4优化】`
- `【关键广告异常｜优先排查广告资格/账户/商品状态】`
- `【数据不足｜暂不做重大调整】`

只有真实广告数据和证据支持时才生成 6-3 输入交接包；它只交接广告状态、原始假设、Campaign/Keyword/Search Term/Placement、动作和待观察项，不越权完成 6-3。

## 正式报告与 0-2

保存到当前 Product Root 的 `06_SKILL分析报告/`，不覆盖历史：

`6-2_[产品编号]_广告诊断优化_V[最大版本号+1]_[YYYYMMDD]_[HHMMSS].html`

成功写入、确认文件存在且命名正确后，调用 `hzp-amz-0-2-report-index`，原样传递 Product Code、Products Root、Product Root。6-2 不扫描、生成、排序、维护或备用更新 `index.html`；报告失败不调用 0-2，报告成功但索引失败时保留报告并明确两者状态。

详细报告字段、证据充分性、动作和时间窗口规则见 `references/diagnosis-framework.md`；6-3 交接字段见 `references/handoff-schema.md`；HTML 章节和表格见 `templates/report-outline.md`。
