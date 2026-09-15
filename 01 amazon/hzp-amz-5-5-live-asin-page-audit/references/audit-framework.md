# 5-5 审计字段与判定表

## Live Page Snapshot

每次运行先建立快照：审计时间、Marketplace、Product Code、产品中文名称、Var_Code、Var_Name、最终审计 ASIN、Parent ASIN、Own Child ASIN、`Mapped_SKUs[]`、SKU-level Exception、Title、Item Highlights、Bullets、Description、Main Image、Secondary Images、Image Count、Video、A+、Brand、Price、List Price、Coupon/Promotion、Rating、Review Count、Variation、Availability、Buy Box/Offer、Delivery、Seller/Fulfillment。无法获取写【未获取】。同一 ASIN 多 SKU 仍只生成一份页面审计；SKU 仅用于可靠的 Offer/履约等后端异常下钻。

## Variant-aware 解析结果

报告开始处记录短命令原文、`Product_Code`、`Var_Code`（如有）、`Var_Name`、映射 ASIN 和解析状态。指定变体时只接受中央“产品对应变体”表中唯一的 `Product_Code + Var_Code → ASIN`；Var_Name 只作显示。未指定变体时从“产品店铺映射”表按 `Product_Code` 读取默认 ASIN；ASIN 为空标记 `[默认ASIN缺失]`。不得新增 `Is_Default` 字段、使用 Excel 第一行或回退到其他变体。未找到变体标记 `[未找到对应变体ASIN]`；同一组合对应多个不同 ASIN 标记 `[变体ASIN映射冲突]`。身份失败时不得读取或混合其他变体页面。

## 策略到线上执行矩阵

| 策略项 | 原策略 | 线上实际 | 状态 | 影响 | 证据 | 建议 | 路由 |
|---|---|---|---|---|---|---|---|

状态：PASS、PARTIAL、GAP、CONFLICT、NOT_VERIFIED。Presence 不等于 Effective Execution：还要检查信息是否在正确位置、是否满足首屏和消费者阅读顺序。

## 文案与视觉检查

逐项比较 Title、Item Highlights/Bullets、Description、A+、主图、副图、视频与 5-1～5-3。核对材料、数字、尺寸、配件、安装、使用场景、Claim 和关键词语义。图片必须实际查看，只有 URL 或文件名时写【图片内容未验证】。

## 首屏与购买路径

只看主图、Title 前半段和前两张副图，检查消费者是否知道：这是什么、给谁、解决什么、为何不同、为何值得买、主要顾虑是什么。路径为：识别 → 相关性 → 价值 → 差异化 → 信任 → 顾虑解除 → Offer → 购买信心。

## Claim 与 Offer

Claim 状态：保留、弱化、补证据后使用、删除、无法确认。不得把未测试性能、认证、专利、医疗/安全保证或竞品比较写成事实。

Offer 单独判断：CONTENT ISSUE、OFFER ISSUE、BOTH、NOT ENOUGH EVIDENCE。Price、Coupon、Promotion、Variation、Rating、Review、Delivery、Availability、Buy Box 和 Fulfillment 不属于页面文案本身。

## 根因、优先级和路由

根因：PAGE_CONTENT、VISUAL、OFFER、REVIEW、TRAFFIC_QUALITY、AD_TARGETING、PRODUCT、MARKET、INVENTORY、SEASONALITY、UNKNOWN。

每项问题记录：Observed Problem、Evidence、Most Likely Root Cause、Alternative Explanation、Confidence、Business Impact、Recommended Action、Route。

优先级：
- P0：事实/结构/变体/价格错误、核心 Claim 无证据、严重真实性或合规风险。
- P1：首屏、核心价值、信任、顾虑或顺序问题，预计影响点击/转化。
- P2：合理但需要测试的表达、场景、A+或品牌优化。
- P3：收益小或证据弱，暂不处理。

允许 No Change：若页面策略、内容、视觉和 Offer 已健康且没有高价值证据，输出【建议保持当前页面】。

## 老板版表达规则

详细证据仍按本文件前述字段记录；生成 HTML 时先输出 LEVEL 1 老板首页，再输出 LEVEL 2 专业证据。LEVEL 1 不展示机器状态码作为主结论，必须转成经营语言：

| 内部状态/术语 | LEVEL 1 中文表达 |
|---|---|
| LIVE_PAGE_ANOMALY | 线上页面存在异常，需要检查 |
| STRATEGY_MISALIGNMENT | 页面和原来的打法有明显偏差 |
| OFFER_NOT_VERIFIED / NOT_VERIFIED | 购买状态这次没有完全确认 |
| INSUFFICIENT_EVIDENCE | 目前证据不够，先别急着改 |
| PASS / PARTIAL / GAP / CONFLICT | 做到 / 部分做到 / 没做到 / 与原策略有冲突 |
| ROOT_CAUSE | 问题更可能出在哪里 |

LEVEL 1 固定回答五个问题：页面有没有大问题、要不要改、最应该改哪几项、哪些地方不要动、下一步交给哪个 Skill。首页最多列 3～5 个动作，每项包含问题、原因、建议和责任 Skill；同时列出有证据支持的保持项。

### 图片逐张点评

图片区标题为《7张图片，一张一张看》（实际图片数量不足时按真实数量显示）。每张图片固定写：

1. 这张图片应该完成的购买任务；
2. 当前表现（🟢 保持、🟡 建议优化、🔴 需要处理、⚪ 暂时无法判断）；
3. 具体问题和业务影响；
4. 建议动作及责任 Skill。

只有实际查看到图片时才能评价内容；否则保留【图片内容未验证】。

### Offer、Listing、竞争的中文标题

老板版标题分别使用《客户现在能不能顺利买？》《文案有没有把产品说清楚？》《跟现在的竞品比，还够不够强？》。无法确认 Offer 时说明“这次没有可靠确认购买环境，所以价格/Buy Box/配送部分暂不下结论”，不得仅凭缺失字段制造红色严重警报。
