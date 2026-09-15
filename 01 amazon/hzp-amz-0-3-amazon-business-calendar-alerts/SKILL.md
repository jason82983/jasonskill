---
name: hzp-amz-0-3-amazon-business-calendar-alerts
description: Provide Amazon US business-calendar reminders, product seasonal and launch reverse scheduling, daily operational forecasts, risk alerts, and routing to the appropriate HZP Amazon Skill without changing Amazon data or performing specialist analysis.
---

# HZP Amazon 0-3｜Amazon经营日历与预警

这是基础层的【Amazon经营日历 + 产品时间倒排 + 经营预警 + Skill路由中枢】。它回答“什么事情如果今天不提醒，之后可能来不及”，负责发现、提醒、倒排和路由；不替代 2-1/2-2/3-1/6-2/7-1 等专业 Skill 的深入分析或决策。

## V1范围

支持 Amazon US 日历、节日/销售节点、季节产品倒排、新品 Launch 倒排、产品级时间提醒、每日经营预报和 Skill 路由。不要构建 SaaS、消息服务器、数据库平台、复杂预测模型，也不要自动修改 Amazon、广告、Listing、库存、Coupon 或 Promotion。

支持入口：`0-3`（全局）、`0-3，P001`（产品）、`0-3，Christmas`（节点）、`0-3，未来90天`（窗口）。运行时先确认 Products Root、Product Root 和产品身份，优先读取 `01_产品档案.md`、必要的 `06_SKILL分析报告` 正式报告和产品资料，不修改产品档案。每日执行由外部 Scheduler/Automation 负责；Skill 本身不假装持续运行。支持 MANUAL MODE、PRODUCT MODE 和未来 Scheduler Mode。产品编号只从已确认身份继承，不根据 ASIN、文件名或中文名猜测。

## 日历与证据

至少维护 New Year's Day、Valentine's Day、Easter、Mother's Day、Father's Day、Memorial Day、Independence Day、Back to School、Labor Day、Halloween、Thanksgiving、Black Friday、Cyber Monday、Christmas、Prime Day、Prime Big Deal Days 和其他 Amazon 活动。

固定日期使用可靠日历规则；可变日期按年份计算或读取可靠来源。Amazon 尚未公布的活动必须写 `[日期待Amazon公布]`，禁止猜具体日期。日期记录使用 `[官方日期]`、`[官方已确认]`、`[历史规律参考]` 等证据标签，历史规律不得写成官方事实。每个节点至少保留名称、日期/销售窗口、Seasonality Type、Product Relevance、Season Start、Peak Window、Season End、开发/打样、生产、国际运输、FBA缓冲、Cold Start、促销准备、Latest Recommended Start Date、Current Stage、Risk Status。严格区分 Holiday Date、Season Start、Peak Selling Window、Launch Start、Shipping Date 和 Development Start。

`Season Start` 是一等字段；没有可靠证据时只能标 `[历史规律参考]` 或 `[AI规划假设]`。产品相关性需结合产品档案和证据判断，不能因节日名称自动判定。

## 产品倒排

根据目标销售开始日倒排：`Target Selling Start → Cold Start → FBA Receiving Buffer → International Shipping → Production → Sample/Development → Latest Development Start`。

公式：`Latest Development Start = Target Selling Start - Cold Start Days - FBA Receiving Buffer Days - Shipping Days - Production Days - Development/Sample Days`。

所有参数可配置。默认国际运输 30 天、新品 Cold Start 30 天，均须标 `[系统默认规划参数]`；生产、开发、FBA 缓冲无证据时也只能用可配置默认值并标注。真实产品参数优先于公司默认值。若产品档案缺少季节性字段，标 `[季节性规划数据缺失]`，不自动改写 `01_产品档案.md`。新品 Launch 还要倒排 Listing Ready、Inventory Ready、FBA Available、Advertising Start、Review/Conversion Observation、6-1 Initial Plan、6-2 Operating Diagnosis 和 6-3 Advertising Optimization。

若剩余时间不足，标 `[计划时间不足]`，列出可验证的压缩或放弃本季方案：现货/已有产品、空运、缩短开发、减少变体、沿用包装、缩短 Cold Start、降低库存目标、放弃本季；这些标 `[经营方案建议]`，不可把不可控时效当成可压缩事实。

## 每日预报、优先级与去重

输出标题 `AMAZON DAILY BUSINESS FORECAST`，至少包含今日日期、P0 今天必须处理、P1 未来7天、P2 未来30天、未来60–180天机会窗口、季节产品倒计时、Amazon重要节点、异常预警和建议调用Skill。没有重大异常时明确输出 `[今日无重大经营预警]`。

优先级：P0 已经晚了/今天必须处理；P1 近期必须处理；P2 应该开始准备；P3 提前关注；INFO 信息提醒。风险标签：`[正常]`、`[进入准备窗口]`、`[进入执行窗口]`、`[时间偏紧]`、`[明显滞后]`、`[高风险错过窗口]`、`[数据不足]`。每日重新计算倒计时，但仅在阶段、风险、阈值、待执行动作、官方信息或有意义的经营异常变化时提高优先级；用轻量状态记录去重，避免每天重复同一倒计时。

## 路由与安全边界

只输出 `[建议调用Skill]` 和理由：产品分析→2-1/2-2；开发→3-1/3-2；样品→4-1；量产前→4-2；页面→5-1/5-2/5-3/5-4；Launch→6-1；广告异常→6-3；经营异常→6-2；补货→7-1；库存风险→7-2。0-3 不复制这些 Skill 的算法和完整结论。

未来可接 SellerSpace MCP、Amazon、库存、订单、广告、Listing、Review、Coupon、Promotion 和 FBA Shipment，但 V1 默认 READ ONLY。禁止 `apply_change_plan`，禁止修改 Campaign、Bid、Budget、Listing、Inventory、Promotion。需要留存的广告原始快照应保存到 `05_分析源数据\06_广告数据下载\`，而不是预报或日志目录。

## 输出与 0-2 边界

高频结果默认保存到 `[Product Root]\06_SKILL分析报告\Amazon经营预报\`，以 Markdown/JSON 等非正式报告文件保存每日预报和轻量提醒状态；它们是 Operational Forecast，不是正式版本化 Skill 报告，因此不会进入 0-2 索引。若用户明确要求正式 HTML，才按统一版本命名保存到 `06_SKILL分析报告\` 根目录，并在成功落盘后按报告型 Skill 约定调用 0-2；不应每天制造 V1/V2。0-2 继续唯一负责 `06_SKILL分析报告\index.html`；0-3 不生成、维护或更新 `index.html`，也不修改 0-2。

## 证据与停止条件

使用 `[官方日期]`、`[产品事实]`、`[人工计划]`、`[系统默认规划参数]`、`[历史规律参考]`、`[AI推断]`、`[待确认]`、`[数据不足]`。不得把默认值、历史规律或推断升级为事实。缺少非关键数据时继续完成可支持的提醒并标 `[数据不足]`；只有产品身份冲突、无法确定 Product Root，或核心时间链无法安全计算时才停止并要求补充。

按需读取：

- [references/calendar-events.md](references/calendar-events.md)：节点、日期和证据维护；
- [references/reverse-schedule.md](references/reverse-schedule.md)：倒排参数、时间不足和 Launch 链；
- [references/routing-and-reminder-state.md](references/routing-and-reminder-state.md)：路由、去重状态和 0-2 边界；
- [templates/daily-business-forecast.md](templates/daily-business-forecast.md)：每日预报模板；
- [templates/event-config.json](templates/event-config.json)：事件结构模板；
- [templates/product-reminder.json](templates/product-reminder.json)：产品提醒结构模板。
- [references/test-cases.md](references/test-cases.md)：V1运行前后的 CASE A-N 行为核对。

0-3 不修改真实产品档案、原始数据、Amazon 账户或历史报告。
