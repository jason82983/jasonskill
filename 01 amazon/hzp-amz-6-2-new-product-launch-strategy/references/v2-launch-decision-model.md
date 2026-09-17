> **Legacy strategic reference:** 6-1 is the sole PLAN authority and 6-2 only applies its latest approved plan. This file may retain historical planning examples; those examples do not authorize 6-2 to choose or expand Intent, Target, lifecycle, Launch Goal, or budget strategy. Follow `approved-battle-plan.md` and `execution-reconciliation.md` for current behavior.

# 6-2 V2 Launch Decision Model｜新品启动决策模型

本参考文件把 6-2 的新品首阶段决策收敛为一套可审计模型。它只补充 6-2 的决策顺序，不替换身份解析、Provider Boundary、预算安全、批准写入或 0-2 索引规则。

## 定位与最高决策链

6-2 V2 同时承担 `New Product Launch Strategy`、`Search Intent Investment Decision`、`Initial Traffic Breakthrough Plan`、`Initial Advertising Blueprint` 和 `Approved Initial Campaign Creation`。目标是在可控投入内尽快验证有效 Search Intent、Traffic、Search Term、Conversion 与可放大的需求入口，不承诺必然爆款。

固定决策链：

```text
Search Intent → Opportunity → Advertising Role → Target → Match Type
→ Campaign Architecture → Bid → Placement → Budget → Validation Plan
```

`Campaign Architecture should follow Search Intent Architecture`。不能先固定建若干 Campaign 再把词机械塞入；Campaign 数量由任务差异、预算、库存和证据决定。

## 输入资产与降级

- 优先读取当前产品最新有效的 6-0-2 `AI_PRECISION_KEYWORDS` 资产与 6-0-3 `PRECISION_BROAD_SUMMARY` 资产；需要逐词追溯时，使用共享 bundle resolver 选择同一 RUN_ID/RUN_TIMESTAMP 的 `PRECISION_BROAD_MAPPING`。必须校验 Product_Code、Report Identity、Schema、状态和完整性，不能把不同运行的两个文件拼接，也不按 mtime 选择。
- 6-0-2 的精准分类由 6-0-2 完成。6-2 不重新判断 `PRECISION/NOT_PRECISION`；`Precision` 不等于 Launch Priority、COR、Exact 或高 Bid。
- 6-0-3 的精准泛词是 Search Intent 资产，不等于 Amazon Broad Match Target；不能机械把精准泛词投为 Broad。 其汇总表中的“直接搜索量”仅统计Primary直接归属词，“汇总搜索量”包含全部子Intent；父子汇总量不得跨层相加。
- Stage 6-0 编号固定为：6-0-1 Benchmark Organic Keyword Raw Evidence、6-0-2 AI 精准关键词、6-0-3 精准泛词/Search Intent/Broad Seed、6-0-4 AI 精准词同步 ERP 结果状态。
- 缺失时分别标记 `[6-0-2_AI_PRECISION_KEYWORD_INPUT_MISSING]`、`[6-0-3_PRECISION_BROAD_INPUT_MISSING]`，允许用可靠产品、页面、Benchmark、Amazon 或人工证据形成降级方案，但不得复制 6-0-2/6-0-3 的完整算法。

## Launch Search Intent Map

在决定广告前，为每个 Search Intent 建立内部 `Launch Search Intent Map`，至少保留：

`Intent_Name`、`Precision_Keywords[]`、`Precision_Broad_Seed`、`Known_Search_Demand`、`Product_Fit`、`Page_Fit`、`Benchmark_Evidence`、`Competition_Evidence`、`CPC_Evidence`、`Economic_Fit`、`Ranking_Opportunity`、`Evidence_Quality`、`Launch_Role`。

先按共同购买意图聚类，再决定同一 Intent 下是否需要 Exact、Phrase、Broad、Auto、Product Target 或 Category Target。场景（如生日、圣诞、毕业）在证据支持时保持边界，不因搜索量大而合并。

### Launch Opportunity 分类

每个 Intent 只能在证据基础上归入以下经营角色之一，不能用固定百分比加权公式机械计算优先级：

- `PRIMARY_LAUNCH_INTENT`：高 Product–Search Intent Fit、页面可承接、经济边界允许且值得首阶段重点验证。
- `SECONDARY_GROWTH_INTENT`：高度相关但资源优先级低于 Primary。
- `PRECISION_LONGTAIL_HARVEST`：精准且可低成本验证，但 Known Demand 有限，不强攻自然排名。
- `DISCOVERY_INTENT`：有合理机会但证据不足，需要 Amazon 真实数据验证。
- `DEFER`：当前 Demand、CPC、Page Fit、竞争、经济、库存、季节或经营目标不支持投入。

Launch Priority 综合判断 Precision、Intent Demand、Product Fit、Page Fit、Differentiation、Benchmark、Competition、Expected CPC/CVR、Economic Model、Target/Risk CPA、Ranking Opportunity、Inventory、Seasonality、Business Goal 与 Evidence Quality；缺少证据就降低置信度，不制造数字。

## 双引擎

`Known Demand Engine` 使用 6-0-2 精准词与 6-0-3 Search Intent 资产，验证曝光、点击、转化、Search Term 和核心 Intent。精准词可以进入 Exact、Phrase 或其他角色，但不自动等于 Exact。

`Unknown Demand Engine` 使用 SP Auto、Intent-Constrained Broad Discovery、Competitor ASIN Discovery、Category Discovery、Amazon 系统推荐等，寻找既有资产未覆盖的 Amazon 需求。Auto 是 Discovery Engine，不是 AI 不会投广告的替代品；预算或风险不适配时可以暂缓。

两套引擎必须同时评估：Known Demand 提高启动效率，Unknown Demand 防止历史 ERP、Benchmark 或 AI 认知锁死。Current Product 的真实 Amazon 数据积累后优先级逐步高于 Benchmark、H10/Cerebro 和初始推断。

## 默认工具箱与角色约束

`COR-EXA`、`EXP-PHR`、`DIS-BRO`、`DIS-AUT`、`COM-ASI` 是可选工具箱，不是强制 4+1 套餐：

- `COR-EXA` 只控制高战略价值、页面和经济均可承接的核心词/Intent。6-0-2 精准词不会自动进入 COR。
- `EXP-PHR` 围绕已确认 Intent 寻找更多有效 Search Terms，不为消耗词池而全量加入。
- `DIS-BRO` 只使用 `Intent-Constrained Discovery` Seed（优先 6-0-3 精准泛词或已验证不扩散错误意图的 Seed）。
- `DIS-AUT` 独立发现未知需求，是否建立取决于阶段、预算、库存、目标和证据。
- `COM-ASI` 验证具体竞争商品详情页流量；Benchmark ASIN 是候选证据，不是必须投放对象。
- `CAT-CAT` 与 `COM-ASI` 分离：Category Targeting 发现类目/属性范围，不能全部塞入竞品 ASIN Campaign。

同一 Intent 允许多路径并存，但每条路径必须有不同的 Discovery、Control、Budget 或 Ranking Purpose；没有可解释任务差异时合并或不创建，避免自我竞争。

## COM Product Target 生命周期

COM 仍使用单一正式命名 `COM-ASI`，内部记录 `Product Target Lifecycle State`：

`DISCOVERY → VALIDATION → CORE`。

新 Target 从 `DISCOVERY/TESTING` 开始；一次订单不能自动升级为 CORE。只有重复有效信号、合理 CPA、稳定相关性和独立控制价值同时支持时，才进入 VALIDATION/CORE。生命周期变化不自动改 Campaign 名称；只有值得独立预算、Bid、Placement 和风险控制时，才考虑物理拆分。

Keyword 生命周期继续使用 `DIS → EXP → COR` 表示经营成熟度和任务，不表示 Broad → Phrase → Exact 的机械升级。新 Exact 词仍可处于 `EXP/TESTING`。

## 经济、页面与排名门槛

Search Volume 或 6-0-3 合并量只是 Known Demand Signal，不能按占比直接分配预算。预算顺序仍是 Business Opportunity → Launch Goal → Market Potential → Economics → Inventory/Season → Expected Traffic Economics → Total/Phase/Daily Budget → Campaign Budget → Bid/Placement。

重点攻击 Intent 前必须检查最新有效 5-4 的 Page Fit；页面无法承接时标记 `[PAGE_INTENT_MISMATCH]`，降低优先级或路由 5-x，6-2 不改 Listing、图片、A+ 或视频。

Ranking Opportunity 只作内部经营判断，可区分 `STRATEGIC_RANKING_INTENT`、`PROFITABLE_HARVEST_INTENT`、`DISCOVERY_INTENT`、`LOW_OPPORTUNITY_INTENT`。它不是 Amazon 官方指标，也不能用固定排名区间直接贴标签。

经济数据充分时才计算 Selling Price、Effective Price、Coupon、Amazon/FBA Fees、Product Cost、Freight、Other Variable Cost、Contribution Margin、Break-even CPA/ACoS、Target CPA、Maximum/Risk CPA；不足时标记 `[产品经济数据不足]`。

## 广告架构生成顺序与初始成熟度

1. 确认 Product/Variant/ASIN/SKU、Store、Marketplace、Portfolio 和经营目标。
2. 读取最新有效页面/产品资料、6-0-2、6-0-3、Benchmark/H10/Cerebro、Amazon 与本地广告证据。
3. 建立 Launch Search Intent Map，分类 Opportunity，拆分 Known/Unknown Demand。
4. 选择必要的 Role、Target、Match Type 和 Campaign，并解释每个 Campaign 的独立 Business Purpose。
5. 联合决定 Bid、Placement、Bidding Strategy、Budget、经济边界和验证计划。
6. 输出 Blueprint、Creation Checklist、6-3/6-4/6-6 交接；只有用户对完整清单明确批准后才进入 Prepare → Diff → Apply → Read-back。

新建 Target/Campaign 的初始成熟度原则上是 `UNTESTED` 或 `TESTING`，不能因 6-0-2 精准度高就写成 `VALIDATED`。可继续兼容 `INITIAL_SIGNAL`、`VALIDATED`、`SCALING`、`MATURE`、`FAILED`、`PAUSED` 等既有状态。

## 多 SKU、命名与交接边界

同一 `Product_Code + Var_Code + ASIN` 的多行 SKU 归并为 `Mapped_SKUs[]`，按实际 Ads/SellerSpace eligibility 形成 `Advertised_SKUs[]`；不得按 Excel 第一行推断或按 SKU 数量复制 Campaign。Own ASIN、Benchmark ASIN、Product Target ASIN 始终分离。

历史 V2 方案中的 Campaign 命名描述已由现行 6-1 控制方式合同取代。当前名称使用 `{ProductCode}.{CampaignTag}.{AdType}-{Role}-{TargetType}-[IntentCode]-{Sequence}`：独立含 Intent Code，共享不含 Intent Code，不投不创建；CampaignTag 不代表真实 Variant，真实 Variant 单独记录；历史 V2 命名只作迁移前参考，不自动改名。报告必须逐 Campaign 说明 Campaign Name、ProductCode、CampaignTag、真实 Variant、AdType、Role、Tool、Intent/Purpose、Targets、Match、Bid、Placement、Bidding Strategy、Budget、Evidence、Validation Goal、Promotion/Exit Condition。

交给后续运行 Skill 的交接包至少保存：Launch Intent、Campaign/Target Role、证据来源、Initial Maturity、Bid/Budget/Placement 逻辑、Validation Goal、Expected Evidence、Economic Boundary、Held Keywords 和关键未知项。6-2 不复制 6-3 的长期自主运营逻辑。

## 报告与验证

正式 HTML 首屏应回答：是否值得启动、先打哪些 Intent、为什么、哪些暂缓、Known/Unknown 如何分工、初始总预算与理由、Target/Risk CPA、最大下行风险、什么结果代表有效、何时交给后续运行 Skill。

测试至少覆盖：6-0-2/6-0-3 正常输入与缺失降级；精准词不全量进入 COR；大容量不自动成为 Primary；精准泛词不机械等于 Broad；同 Intent 多路径仅在任务不同才并存；Benchmark 不自动变 COM；COM 一单不升级 CORE；Category 与 COM 分离；Page/Economic 数据不足时不编造；多 SKU 不复制 Campaign；初始状态不误写 VALIDATED；完整清单批准前不调用写入；旧广告不自动修改。正式报告成功后仍只调用 0-2 更新索引。
