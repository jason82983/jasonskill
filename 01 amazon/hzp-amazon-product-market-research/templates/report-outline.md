# Chinese HTML Report Outline — HZP Enhanced

The report is designed for QMT meeting decisions. The top of the page must answer the decision before the reader scrolls.

## 0. Header / source validation strip
- Report title + ASIN + benchmark product
- data date
- file check: Keepa / Cerebro / Reviews / ASIN match / Amazon 页面状态
- Amazon request URL, final URL, fetch time, displayed ASIN, and page limitation when attempted
- if mismatch: STOP and show mismatch notice; do not render the following sections

## 1. Executive decision hero — first screen
- 一句话结论
- GO / CONDITIONAL GO / NO-GO badge
- Benchmark is really selling: demand formula
- Key KPI cards (only source-supported metrics), e.g. current price, current/best BSR, rating/count, key category rank, seasonality status
- Four decision cards:
  - 为什么成功
  - 最大机会
  - 最大风险
  - 我们应该开发什么

## 1A. Amazon 当前商品页快照
- 页面身份：标题、品牌、类目、页面 ASIN、父/子体和当前选中变体
- 当前 offer：展示价格、划线价、优惠券、可售/配送、卖家和可见履约标识
- 页面评分区：星级与评论/评分数量
- 可见卖点与规格：短事实、原单位、页面定位
- page/file 对照表：字段、页面值、文件值、来源时间、冲突解释、后续验证
- 页面无法访问或身份无法确认时显示 `Amazon 页面补充缺失`，并列出限制

## 2. Market / Keepa trend
- launch/growth/decline interpretation
- milestone table
- price/promotion observations
- rating-count/rating trend
- seasonality
- explicit fact vs inference labels

## 3. Representative keywords + H10 raw bid
Mandatory columns:
- 需求簇
- 代表关键词
- 搜索量
- 竞品数
- 自然排名
- 广告排名
- H10建议竞价
- H10竞价范围
- 解读

Rules:
- bid data comes from H10 raw file only
- missing displays `数据缺失`
- never estimate

Then summarize demand clusters and explain how the product wins.

## 4. Review insights
- review sample count
- star distribution
- sample average
- Vine count only if reliable
- positive themes
- negative themes
- claim-vs-experience contradictions
- polarized themes

## 5. 典型真实评价
Use review cards, not a dense table.
Each card:
- type + stars
- short English original quote
- Chinese translation
- 开发启示
- source locator when useful

Recommended amount:
- 2–4 positive
- 2–4 negative
- 1–2 polarized only when useful

## 6. 核心：我们的产品开发方向
Mandatory matrix:

| 消费者问题/需求 | 竞品表现或证据 | 我们的产品改进方向 | 优先级 | 验证方法 | 证据属性 |
|---|---|---|---|---|---|

Priority tags:
- P0 必须解决
- P1 重要差异化
- P2 加分项

Evidence tags:
- 数据支持
- 分析推断
- 待供应链验证

## 7. Product Definition V1
Show as an executive product brief card with:
- 产品概念
- 目标用户
- 使用场景
- 核心母需求 / JTBD
- 3–5 核心承诺
- P0 requirements
- P1 differentiators
- do-not-overpromise / avoid list
- target price band or 待商业验证
- target keyword clusters
- pre-production validation tests
- 待QMT/供应链确认

## 8. Risk / unknowns
Separate cards:
- 已观察风险
- 分析推断风险
- 待验证未知项

## 9. QMT meeting questions
6–10 questions tied to development matrix and feasibility.

## 10. Decision scorecard
Use 0–10 only as decision aid:
- market validation
- new-product entry validation
- price space
- differentiation space
- year-round stability/seasonality
- inventory friendliness
- product maturity

Keep the main GO/Conditional GO/NO-GO decision consistent with the top hero.

## 11. Data-source footer
- exact source filenames
- source/export dates where visible
- data limitations
- note that H10 bids are raw H10 suggestions, not actual CPC
- note that real-review quotes were selected from the provided Reviews export
- note that Amazon page values are a time-stamped public snapshot; include request/final URL, status, fetch time, and displayed ASIN when attempted
- note that page/file conflicts are shown rather than silently averaged, and blocked pages fall back to valid core-file evidence
