---
name: hzp-amz-6-1-new-product-launch-strategy
description: 基于完整链路或现实中已存在的 Amazon 产品，设计首阶段流量获取、市场验证、广告测试、预算与价格促销协同，并建立可执行的继续/停止规则和 6-2 交接；缺少上游报告时先做最低必要检查，不把烧广告当作解决方案。
metadata:
  short-description: 设计 Amazon 新品首阶段推广与验证方案
---

# HZP Amazon 6-1｜新品推广方案

## 定位与边界

6-1 是新品推广架构师（New Product Launch Architect），负责新品上线前、上线初期或现有产品重新启动时的推广设计：明确流量从哪里来、要验证什么、预算如何分配、页面如何承接，以及何时继续、暂停或进入 6-2。广告在新品阶段既买订单，也买数据验证商业假设。运行开始先选择 `Pipeline Mode｜完整链路模式` 或 `Direct Launch Mode｜直接推广模式`。

- 5-4 负责页面审核；6-1 负责新品推广方案；6-3 负责广告诊断优化；6-2 负责产品经营监控与诊断。
- 不假装拥有未来广告数据，不重新做 5-1、5-2、5-3，不在批准前直接改广告；批准后仅按“批准后的初始广告创建”边界创建新广告，不把广告类型清单当战略，也不把 ACoS 作为唯一判断。
- 不修改 `04_产品推广思路.md`、原始数据、历史 HTML 或 `index.html`；正式报告完成后只调用 0-2 更新索引。
- 一次运行连续完成当前已定义步骤，不要求用户逐阶段确认；但在正式定案前，必须展示《6-1 新品广告初始化预案》，取得一次战略预案审批。该审批不等于写入授权；只有完整执行清单展示后针对该清单的明确批准，才授予本批新 Campaign 创建授权。

## V2 核心决策模型

6-1 V2 同时负责 `New Product Launch Strategy`、`Search Intent Investment Decision`、`Initial Traffic Breakthrough Plan`、`Initial Advertising Blueprint` 和 `Approved Initial Campaign Creation`。最高原则是 `Campaign Architecture should follow Search Intent Architecture`，固定顺序为：

`Search Intent → Opportunity → Advertising Role → Target → Match Type → Campaign Architecture → Bid → Placement → Budget → Validation Plan`。

先建立内部 `Launch Search Intent Map`（Intent_Name、Precision_Keywords[]、Precision_Broad_Seed、Known_Search_Demand、Product_Fit、Page_Fit、Benchmark_Evidence、Competition_Evidence、CPC_Evidence、Economic_Fit、Ranking_Opportunity、Evidence_Quality、Launch_Role），再决定哪些流量进入 COR-EXA、EXP-PHR、DIS-BRO、DIS-AUT、COM-ASI 或 CAT-CAT。该工具箱按任务动态选择，不是强制 4+1 套餐；同一 Intent 的多路径必须有不同 Business Purpose。

每个 Intent 使用 `PRIMARY_LAUNCH_INTENT`、`SECONDARY_GROWTH_INTENT`、`PRECISION_LONGTAIL_HARVEST`、`DISCOVERY_INTENT` 或 `DEFER` 表示投入机会。6-0-1 精准词不自动等于 COR/Exact/高 Bid，6-0-2 精准泛词不自动等于 Broad Target；Known Demand 与 Unknown Demand 必须双引擎评估。完整字段、COM 生命周期、Ranking Opportunity、经济和页面门槛、初始成熟度与 V2 测试契约见 `references/v2-launch-decision-model.md`。

## 必读输入与身份

1. 使用本次确认的 Products Root、Product Root，读取同一产品的 `01_产品档案.md` 和 `04_产品推广思路.md`。产品代码、中文名称和 Product Root 冲突时停止并输出 `[产品身份冲突]`；禁止根据 ASIN、文件名或经验猜产品名称。
2. 在读取 SellerSpace 真实数据前，按 Amazon 行业共享规则 `Amazon产品身份解析规则.md` 读取 Products Root 下的 `00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`。用当前运行已确定的 Product Code 精确匹配，形成唯一的 `SellerSpace_Store + Marketplace + own_asin`；变体层归并为 `Mapped_SKUs[]`，仅在单 SKU 接口明确要求时验证 `Primary_Advertised_SKU`，再用 SellerSpace MCP 只读二次验证。唯一 ACTIVE 且验证通过才输出 `【产品身份验证通过】` 并继续；映射缺失、多个 ACTIVE、INACTIVE/TEST、映射与 MCP 或 `01_产品档案.md` 冲突时按共享规则停止、标记或要求人工确认，不得猜测或自动修改映射表。SellerSpace 不可用时可降级使用本地证据并标记 `【SellerSpace实时身份验证未完成】`。
3. 运行上下文固定区分 `own_asin`（自有 ASIN）与 `benchmark_asin`（对标 ASIN）。`own_asin` 才能用于 SellerSpace 的商品、库存、广告、订单、Listing 和经营查询；`benchmark_asin` 只用于市场研究、Cerebro、Niche、页面对标、Keyword mining 和 Product Targeting 候选。禁止用对标 ASIN 查询当前产品 SellerSpace 数据，也禁止用泛化 `asin` 同时代表两者。
4. Product Code、Products Root、Product Root 一经本次运行确认，必须原样传递到后续报告和 0-2；不得根据 ASIN、SKU、文件名或报告重新推断。共享规则文件只维护一份；不要在 6-1 内复制另一套身份解析逻辑。
5. 检查 `[Product Root]/06_SKILL分析报告/` 是否有当前产品最新有效的 5-4 正式 HTML。存在时按当前 Product Code + Skill 编号、最大 V 和文件名时间选择，并优先读取《6-1输入交接包》；排除 index、失败、incomplete、invalid、deprecated、test、temp、preview、draft、非正式输出以及 `广告表现汇报优化日志/` 目录及其子目录。不存在时切换 `Direct Launch Mode`，不得仅因缺少 5-4 停止。具体规则见 `references/launch-framework.md`。
6. 主动扫描 `[Product Root]/05_分析源数据/03_关键词数据/`、`[Product Root]/05_分析源数据/06_广告数据下载/` 和 `[Product Root]/07_产品资料/`。文件名只是线索，必须读取实际字段、数据日期和产品身份；只有真实存在的 Search Volume、CPC、Organic Rank、Sponsored Rank、CTR、CVR、ACoS、订单、售价、毛利、库存、预算、Coupon、Promotion、Vine 等才能写数值。`06_广告数据下载/` 中的 Excel、CSV、JSON 是原始广告证据，不覆盖、不修改，也不把 AI 结论写回原文件。
7. Direct Launch Mode 先做最低必要推广前检查：Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Marketplace、Store、Listing/可售状态、主图、标题、价格、库存和已知经济边界。缺少非关键参数时标记待确认并继续形成小规模验证方案；只有错误身份、不可售、重大页面问题或无法安全启动时才停止。
8. 按需辅助回查最新有效的 5-1、5-2、5-3、2-1、2-2、3-1，只核对消费者、搜索意图、P0/P1、关键词、竞争环境、产品事实和页面承接，不重新完整运行上游 Skill。

### SellerSpace MCP 只读接入

如果 `sellerspace-mcp` 可用，先调用 `discover_capabilities` 和 `discover_fields` 确认当前真实能力、实体、字段、站点和时间范围，再调用只读工具。优先使用 `get_stores` 固定本次 sellerId 与 marketplace；按任务使用 `query_ads`、`query_products`、`query_store_performance`、`listing`、`query_inventory`、`query_shipments`、`query_orders`、`get_metric_history`、`get_sp_campaign_recommendations` 和 `export_data`。工具名称不能代替字段证据；不支持的字段标记 `【SellerSpace当前无法提供】`。

6-1 在用户批准完整初始广告创建清单前为 READ ONLY：禁止调用 `prepare_change_plan` 或 `apply_change_plan`。批准后仅可对批准清单执行 `prepare_change_plan → 逐项比对 → apply_change_plan → Read-Back Verification`，只创建新 Campaign/Ad Group/Advertised Product/Keyword/Target；不得修改旧广告、Listing、Price 或 Coupon。`export_data` 只有在确实生成原始文件时才保存到 `[Product Root]/05_分析源数据/06_广告数据下载/`。

正式 HTML 必须生成《输入版本追溯》，只记录本次实际读取的版本化报告；读取 5-4 时标为【核心输入】，其他回查为【辅助回查】，历史对照才标【历史版本对照】。Direct Launch Mode 没有读取的 5-4 不得虚构列入。

## 运行模式与页面前置检查

- `Pipeline Mode｜完整链路模式`：存在当前产品最新有效的 5-4 正式报告时，继承其页面审核状态、P0、页面承接能力和 Claim 边界。只有真实证据显示页面不满足推广条件时，才输出 `【上游页面状态不满足推广条件｜返回5-4】`。
- `Direct Launch Mode｜直接推广模式`：没有 5-4 或上游链路不完整，但现实产品可能已上线、可售、有库存或已有广告数据时使用。缺少 5-4 本身不是推广失败证据，也不要求复制完整 5-4 审核。
- Direct Launch Mode 只做最低必要检查：身份（`own_asin`、SKU、Marketplace、Store）、Listing/可售状态、主图、标题、价格、库存和已知经济边界。结果只允许为 `【最低推广条件满足】`、`【最低推广条件基本满足｜存在待验证项】`、`【存在关键页面问题｜建议先修复】`、`【商品不可售或广告资格异常｜暂不启动】` 或 `【关键事实不足｜无法安全启动】`。
- 缺少预算上限、毛利、CVR、Coupon 或广告历史时继续完成能被证据支持的结构；相应金额或指标标记 `【预算待确认】`、`【经济边界不足】` 或 `【待验证】`。只有错误身份、不可售、重大页面问题或无法安全执行时才阻止真实启动。
- 标准顺序为：接收 Product Code → 读取身份映射并以 SellerSpace 只读验证 → 选择运行模式 → 读取产品/Listing、关键词、对标证据、广告历史（如有）、推荐、经济边界和库存 → 建立关键词母池与动态广告架构 → 形成首轮验证计划和 6-2 输入交接包 → 生成正式报告并调用 0-2。全程不要求用户逐阶段确认。

## 老板输入层、默认目标与 Launch Window

- 先自动读取能从产品档案、页面、SellerSpace、H10/Cerebro、Niche、历史广告、库存和已有推广思路可靠获得的信息；只询问真正影响商业取舍且无法可靠推断的内容。提问优先用选择题：推广目标（稳健验证/标准增长/快速强攻/自定义）、时间压力（正常/加速/紧急/自定义）、季节性（非季节/窗口充足/窗口偏短/不确定）、阶段性亏损接受度（保守/适中/积极/自定义）、预算约束（AI反推/日上限/周期上限/双重限制）、库存目标（正常销售/指定时间消化/窗口结束前降库存/AI建议）。
- 不得机械询问已被可靠资料确认的项目；只有季节性或窗口确实影响策略且旺季结束时间无法确认时，才追问有效销售窗口。
- 没有人工目标时，生成并明确标记 [系统默认目标]：在可控投入下尽快验证真实成交路径、沉淀可重复成交关键词并判断是否值得放量。默认采用 Standard Growth Launch｜标准增长型 Launch，再根据时间窗口、季节性、库存和经济边界修正；优先级为人工目标 > 已知商业约束 > 客观产品事实 > 系统默认目标。提供接受默认、改为稳健验证、改为加速/强攻或自定义的快速选择。
- 结合当前日期、旺季窗口、到仓时间、库存/在途、消化目标、预算、最大损失、页面状态和人工时间要求判断 Standard Launch、Accelerated Launch 或 Seasonal Sprint。窗口长短只作综合判断，不写死 60/21/10 天等阈值；窗口越短越强调快速证伪与资源集中，但不得同时无条件拉满 Bid、Placement、Bidding Strategy 和 Budget。
- 如果目标、库存、窗口、流量、CPC、CVR、Budget、Listing 或经济边界明显冲突，输出 [目标与当前资源/时间窗口存在冲突]，列出冲突证据和调整选项，不为满足目标伪造可行数字。

## 阶段路线、证据成熟度与目标反推

- 用“时间负责节奏，证据负责晋级”。可按 Stage 1 验证 → Stage 2 聚焦 → Stage 3 放量 → Stage 4 稳态/扩量组织 Launch；允许提前晋级，也允许因数据不足延长，不因到达某天数机械宣布成功或失败。每阶段都写目标、需证明的问题、证据、晋级/提前晋级、延长、加速、止损/回退条件，以及适用的时间和投入上限。
- 证据状态至少支持 [数据不足｜继续收集]、[初步信号｜暂不放量]、[首单验证｜继续观察重复性]、[重复成交验证｜可考虑增加资源]、[验证通过｜进入下一阶段]、[负向证据充分｜建议调整/停止]、[时间窗口不足｜降低证据门槛快速决策]、[目标与现实冲突｜需要重新制定Launch目标]。参考点击/订单区间只能辅助判断，不能作为统一硬阈值；1 click + 1 order 只能是首单验证。
- 有可靠基准 CVR 时可展示 Expected Orders ≈ Clicks × Expected CVR，标记 [推算指标]，并与实际订单分开；没有可靠 CVR 不得生成 Expected Orders。综合 Clicks、Orders、CVR、CPC、CPA、ACoS、Revenue、相关性、Match Type、Placement、重复性、经济边界和剩余窗口判断。
- Search Term/Target 生命周期可为：发现 → 候选 → 首单验证 → 重复成交验证 → 核心成交候选 → 核心成交 → 核心排名 → 自然流量资产；负向证据逐步增强时交给 6-3 处理降 Bid、降预算、暂停、否定、页面检查或流量重构。

## 广告初始化预案审批与创建蓝图

- 在生成正式 6-1 方案前，先生成《6-1 新品广告初始化预案》，至少展示：产品身份（Own ASIN、Benchmark ASIN、Product Target ASIN 分开）、Launch Goal/来源、Launch Mode、窗口/季节性、库存目标、Budget/最大投入/最大损失、经济边界、阶段路线、每阶段晋级逻辑、Campaign 架构、COR/EXP/DIS/COM 角色、Manual Keyword、Product Target、Auto、Bid、Budget、Bidding Strategy、Placement、Negative 初始原则、证据、假设、最大风险和选择理由。Campaign 数量动态决定，不能固定为 5 个。
- 预案展示后只等待一次快速审批：A 批准；B 基本批准并修改局部参数；C 不批准、重新制定；D 暂缓启动。B 只重算受影响部分，不重复询问全部目标。
- 预案审批与执行授权分开：在完整执行清单展示前，预案审批仅代表战略/初始化蓝图获批；清单展示后，用户对该清单回复“批准/A/批准创建/按这个执行”，即授予本批新 Campaign 创建授权。随后遵循 prepare_change_plan → 逐项比对 → apply_change_plan；Material Difference 必须重新确认。批准前不得调用 prepare_change_plan 或 apply_change_plan。
- 自动发现 Manual Keyword 和 Product Target ASIN：从 Own Listing、H10/Cerebro、Niche、Amazon/SellerSpace 推荐、Own 历史 Search Term/转化词、Benchmark 和竞品资料中去重、清洗并按相关性、购买意图、价格带、可替代性、Review/Rating 空间和切换理由筛选。无证据不得编造；Benchmark/Product Target 不得用于 Own Product SellerSpace 身份查询。
- 正式报告必须包含管理层摘要：当前打法、理由、Launch 模式、剩余窗口、第一阶段证明问题、投入/预算边界、晋级/加速/停止条件和前三大风险。

## 批准后的初始广告创建

6-1 在展示完整、具体的《初始广告创建清单》并得到针对该清单的明确批准后，才可以创建本次批准范围内的新 Campaign。完整清单至少列出 Store、Marketplace、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Campaign Name、Ad Type、Role、Start Date、Daily Budget、Ad Group、Advertised Product、Targeting Type、Keyword/Match Type/Bid、Product Target ASIN/Bid、Auto Targeting、Bidding Strategy、Placement、Initial Negatives、Campaign Initial Status、Recommended Total Launch Budget、Initial Daily Budget、Phase Budget 和 Budget Release Gate。

批准语义固定为一次知情批准：用户对已展示清单回复“批准”“A”“批准创建”或“按这个执行”，同时表示策略批准和本批新 Campaign 创建授权，不再机械询问第二次。未展示完整清单、回复含糊、或只批准战略方向时，不得写入。B/C/D 分别表示修改、重做、暂缓，需重新形成清单。

批准后按以下顺序执行：

1. 生成 `execution_id`，重新读取映射表、`01_产品档案.md` 和 SellerSpace，确认 Product Code → Store → Marketplace → Own ASIN 一致；变体层的 `Mapped_SKUs[]`、`Advertised_SKUs[]` 再按实际资格确认；Benchmark ASIN 和 Product Target ASIN 永远不能作为 Advertised Product。身份无法唯一确认时输出 `[产品身份无法唯一确认｜禁止创建广告]` 并停止。
2. 查询 Existing Campaigns，检查名称、关键词、Target 和结构重叠。若名称已存在，预案阶段就使用下一个 Sequence；不得批准后偷偷改名。重叠只生成 `[新旧广告并行风险]` 和建议人工关闭清单，不 Pause、Archive、Delete 或修改旧广告。
3. 只对已批准清单调用 `prepare_change_plan`，使用 SellerSpace 实际支持的 `campaign.create`、`keywords.create`、`targets.create` 或对应契约；prepare 只预览，不写入。将返回的 Campaign 数量、名称、预算、Bid、ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Target、策略和广告位与已批准清单逐项比对。
4. 任何 Material Difference（Campaign 数量、名称、预算、Bid、Keyword、Target、Placement、Bidding Strategy、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[] 改变）都停止并输出 `[执行计划与已批准预案存在重大差异｜需要重新确认]`；一致时用稳定 `idempotencyKey=execution_id` 调用 `apply_change_plan`，不得绕过 SellerSpace 安全流程。
5. apply 成功不等于结束。重新 Read-Back 验证 Campaign、Ad Group、Advertised Product、Keyword/Match Type、Product Target、Bid、Budget、Bidding Strategy、Placement 和 Status，生成《广告创建结果验证》。状态只能为 `[创建成功｜参数一致]`、`[创建成功｜存在非关键差异]`、`[部分创建成功]`、`[创建失败]`、`[创建结果无法验证]` 或 `[实际参数与批准方案不一致]`。
6. 部分失败时先读取实际状态，识别已成功对象，只对失败对象形成 Recovery Plan，不重跑完整 Change Plan。重复“批准”、刷新或超时不得造成第二套广告；执行记录保存 `execution_id`、`approved_at`、`prepared_at`、`applied_at`、`verification_at`、planId、结果和已创建对象。

授权严格限定为“本次展示并批准的新广告创建清单”。旧 Campaign、Listing、Price、Coupon、Bid、Budget、Placement、Keyword 和 Target 均不在授权内。旧广告固定记录：`[旧广告未修改｜由用户人工处理]`。创建成功后，6-2 只接收实际 Campaign ID/名称、Ad Group、Keyword、Target、Bid、Budget、Placement、Bidding Strategy、Launch Goal、Phase Budget、验证和止损条件。


## Evidence-Gated Keyword Expansion｜证据驱动扩词

6-1 负责建立完整的 `Keyword Mother Pool`，但母词池不是广告创建清单。来源可包括 H10/Cerebro、Niche、Amazon/SellerSpace 推荐、Own/Benchmark Listing 语义、Own 历史 Search Terms/成交词和其他可靠来源；每个词必须保留来源、来源 ASIN、日期、Search Volume、Rank、Bid/Range、相关性、购买意图、语义主题、证据状态和推广角色。Benchmark 表现不得写成 Own Product 成交事实。

母词池先去重、清理无关词，再识别 `Semantic Cluster` 与 `Purchase Intent Cluster`。每个 Cluster 至少记录 `cluster_id`、名称、意图、词数、代表词、数据源、搜索量/排名/Bid证据、Own/Benchmark证据、相关性、当前成熟度和 `release_status`。关键词成熟度使用 `DISCOVERED → CANDIDATE → FIRST_ORDER_VALIDATED → REPEATED_CONVERSION_VALIDATED → CORE_CANDIDATE → CORE_CONVERTING → CORE_RANKING → ORGANIC_ASSET`；Cluster 成熟度使用 `UNTESTED → TESTING → INITIAL_SIGNAL → VALIDATED → SCALING → MATURE`，异常状态可为 `FAILED/PAUSED`。

6-1 根据相关性、购买意图、搜索量、排名、Bid、竞争、Own 历史、Launch Goal、预算和经济边界，主动选择 `Initial Validation Batch`，分配到 COR-EXA、EXP-PHR、DIS-BRO、DIS-AUT、COM-ASI 等角色。Broad 只使用高度相关且有明确探索价值的 Seed，不能把剩余词全部丢进 Broad。未进入首批的高价值词必须保留为 `HELD_FOR_EXPANSION`、`WAITING_CLUSTER_VALIDATION`、`LOW_PRIORITY`、`INSUFFICIENT_EVIDENCE` 或 `DO_NOT_LAUNCH`，不得丢失。

6-1 的《6-2输入交接包》必须同时交接 Keyword Mother Pool、Semantic/Purchase Intent Clusters、Initial Released Keywords、Held Keywords、Cluster/Keyword Maturity、Expansion Rules、Expansion Budget Rules、Promotion Rules 和 Stop Rules。6-1 定义首批验证与释放边界，不承担长期日常扩词。


## Initial Advertising Creation Blueprint｜新品广告创建蓝图

正式创建前必须生成两层审批视图。`LEVEL 1｜Executive Approval View` 供 2–5 分钟决策，`LEVEL 2｜Detailed Creation Blueprint` 用于逐项审计和 SellerSpace 映射；后台参数完整保留，审批界面只做清晰分层，不隐藏执行字段。

### LEVEL 1｜Executive Approval View

顶部固定显示《6-1 新品广告创建决策》：Product Code、Product Name、Marketplace、Store、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Launch Goal、Launch Mode、Launch Window、Recommended Total Launch Budget、Phase 1 Released Budget、Initial Daily Budget、Maximum Daily Budget After Validation、Planned Campaign Count、Initial Keyword Count、Product Target ASIN Count 和 AI Recommendation（`【建议创建】`、`【有条件建议创建】` 或 `【暂不创建】`）。

随后以 Campaign 总览表说明钱主要投向哪里，至少包括 Campaign Name、Role、Targeting、Daily Budget、Base Bid/Bid Range、Bidding Strategy、Top of Search、Rest of Search（平台支持时）、Product Pages、Keyword/Target Count 和 Purpose。首页另列《Initial Budget Allocation｜初始预算分配》和《Initial Keyword Allocation｜初始关键词分配》，明确 Released 与 Held 数量，并解释“母词池总量 ≠ 本批创建量”。

### LEVEL 2｜Detailed Creation Blueprint

每个 Campaign 独立展开 Campaign、Ad Group、Advertised Product、Targeting、Bid、Budget、Bidding Strategy、Placement、Negative 和 Status。Campaign 至少显示名称、Role、Ad Type、起止日期、状态、Daily Budget、Portfolio（如适用）、策略和各广告位；Ad Group 显示名称、Default Bid、Status；Advertised Product 显示 Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]，并固定标记 `[Advertised Product｜Own Product]`。

每个 Keyword 必须逐词列出 Keyword、中文含义、Source、Cluster、Role、Match Type、Initial Bid、H10 Suggested Bid、H10 Bid Range、Amazon/SellerSpace Suggested Bid、Own Historical CPC、Evidence 和 Reason。缺失字段写 `[数据缺失]`，不得估算 H10 原始建议竞价。Phrase、Broad 的每个词/Seed 也必须完整列出；Auto 必须显示 Close Match、Loose Match、Substitutes、Complements 及独立 Bid（仅在接口支持时）。Product Targeting 必须逐个显示 Target ASIN、产品名/品牌/价格/Rating/Review Count（如有）、Source、Reason 和 Initial Bid，并标记 `[Product Target ASIN]`。

Own ASIN、Benchmark ASIN、Product Target ASIN 必须视觉隔离：Own ASIN 只作为 Advertised Product；Benchmark ASIN 只作市场/研究参考；Product Target ASIN 只作广告 Target。禁止使用不带身份前缀的通用 `ASIN` 字段。

### ASIN-first / SKU-aware 身份规则

共享身份解析器按 `Product_Code + Var_Code + ASIN` 归并“产品对应变体”中的多行 SKU，输出 `Mapped_SKUs[]`、`Advertised_SKUs[]`、`SKU_Count` 和仅在单 SKU 接口确实需要时使用的 `Primary_Advertised_SKU`。同一 ASIN 对应多个 SKU 是合法的 `MULTI_SKU_SAME_ASIN`，不得生成重复 Campaign 或取 Excel 第一行 SKU；Campaign 命名仍以 Product_Code + Var_Code + ASIN 语义为主。

创建前必须用 Amazon Ads/SellerSpace 实际能力核验每个 Mapped SKU 的 Advertised Product/ASIN eligibility，并记录 `SKU_ELIGIBILITY_VERIFIED` 或 `SKU_ELIGIBILITY_PARTIAL` 状态：全部合格且接口允许独立对象时 `ADD BOTH`；只有部分合格时 `ADD ELIGIBLE SKU ONLY`；平台按 ASIN 去重时 `ADD ONCE`；全部不合格时标记 `ADVERTISED_PRODUCT_NOT_ELIGIBLE` 并停止该变体写入。Product_Code + Var_Code 对应多个不同 ASIN 时标记 `[VARIANT_ASIN_MAPPING_CONFLICT]`，Fail Closed，不按行序、库存或 SKU 名猜测。

每个 Campaign 必须逐项显示 Bidding Strategy（Dynamic Bids - Down Only、Dynamic Bids - Up and Down 或 Fixed Bids）和 Placement（Top of Search、Rest of Search、Product Pages；不支持时标记 `[当前执行接口不支持]`）。若 Keyword/Target/Auto 支持独立 Bid，必须显示 Target-Level Bid，并与 Ad Group Default Bid 分开。

预算必须同时显示 Launch Total Budget、Phase Budget、Daily Budget Envelope、Campaign Daily Budget，并核对 Campaign Budget Sum 与 Initial Daily Budget；不一致时解释保留预算、上限或未释放部分的原因。初始 Negative 如存在，完整列出对象、类型、Match Type、Campaign/Ad Group 和 Reason；没有足够证据时明确 `[暂不预设大规模否词]`。

### Creation Checklist 与审批

批准前自动检查 Identity、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Marketplace、Store、Campaign Names、Campaign Budgets、Ad Groups、Advertised Product、Keywords、Match Types、Product Targets、Target-Level Bids、Bidding Strategies、Placements、Auto Targeting、Negatives、Launch Budget、Phase Budget、Validation Rules 和 6-2 Handoff。关键字段缺失时不得标记 `[Ready to Create]`，只能标记 `[Ready with Known Limitations]` 或 `[Not Ready to Create]` 并说明原因。

LEVEL 1 底部固定提供 A 全部批准并创建、B 部分修改、C 重新设计、D 查看完整广告明细。D 仅查看，不等于批准；B 先让用户选择总预算、Campaign 结构、Keyword、Product Target ASIN、Bid、策略、Placement、Match Type、Negative 或其他，再只重算受影响部分。A 对完整蓝图的明确回复沿用一次知情批准规则。

用户批准后形成 `Approved Creation Blueprint`，SellerSpace `prepare_change_plan` 返回 `Prepared Creation Plan`。必须做 Field-Level Diff，逐项比较 Campaign、Ad Group、Advertised Product、Keyword、ASIN Target、Bid、Budget、Match、Strategy、Placement 和 Negative；存在 Material Difference 时停止并输出 `[执行计划与已批准预案存在重大差异｜需要重新确认]`。创建后按同一蓝图字段 Read-Back，核对 Campaign ID、实际参数、状态和对象，输出既定创建结果状态。

## 核心决策方法

围绕“假设 → 流量 → 消费者行为 → 数据 → 判断 → 动作”设计方案。每个关键词、ASIN 或 Category 都要回答消费者意图、产品/页面/价格是否能承接、要验证的假设、需要观察的数据和继续/暂停条件。

- 关键词按搜索意图、产品匹配、页面承接和商业角色分类，可使用【核心定义词】【核心需求词】【属性差异词】【使用场景词】【长尾高意图词】【竞品承接词】【探索词】【暂不投放】；不要求机械覆盖全部类别。
- Exact、Phrase、Broad、Auto、Product Targeting、Category Targeting 只是流量机制。核心验证、探索、竞品流量应逻辑分开；没有明确目的不建立 Campaign。
- Campaign/Ad Group 必须按实际目标动态设计。每个计划项至少写明名称、目的、阶段、Keyword/ASIN/Category、Match Type、初始 Bid、Bid 来源、Budget、Budget 依据、Placement、验证问题、观察周期、成功信号、失败信号和交给 6-2 的触发条件；没有必要的结构不要创建。
- 搜索量最大不自动等于优先级最高；SEO 词不自动等于广告优先词；不满足产品意图的流量标记 `【意图不匹配｜暂不投放】`。
- `$100/day` 只作为 `Fallback Planning Budget｜缺乏充分预算证据时的系统默认规划值`，不是新品固定预算。预算证据充分时，必须先判断产品值得投入的总额和节奏，再给出低于、约等于或高于 `$100/day` 的 AI 建议；证据不足时可采用该 Fallback，但仍须说明依据、置信度和待补数据。建议 Bid 只能按来源写参考，不能改称真实 CPC；成本不足时不计算 Break-even ACoS。
- 不用统一“10/20/30 点击停词”阈值；判断要结合样本量、验证目的、商业边界、库存和现金流。无曝光、有点击无订单、少量订单分别进入资格/相关性/页面/价格/竞争等诊断，不自动加价或判失败。

### COR-EXA 新品 Initial Bid 策略（覆盖旧规则）

仅当 AI 将关键词标记为 `CORE_HIGH_CONFIDENCE_EXACT` 且 Campaign 角色为 `COR-EXA` 时，才使用本节的新品默认参考。`Base Bid` 必须由 Suggested Bid、Own Historical CPC（如有）、H10/Benchmark CPC、产品价格与毛利、Break-even ACoS、Target CPA、预计/实际 CVR、关键词相关性、搜索量、竞争、Listing Readiness、Price/Coupon、库存和 Launch Goal 综合计算为合理基础竞价；不得把 `Base Bid × 1.20`（或“基础竞价机械增加20%”）作为默认启动逻辑，也不得同时保留该旧默认。

- 默认 Launch Reference：`Top of Search +50%`、`Rest of Search 0%`、`Product Pages 0%`、`Dynamic Bids - Up and Down`。
- `+50%` 是高置信度 COR-EXA 的参考值，不是死规则。证据允许选择 `0%`、`20%`、`30%`、`50%`、`80%` 或其他合理值，并在报告写明调整值、证据和原因；当证据明显反对时应降低或取消 Top 调整。
- 蓝图和报告必须同时显示：`Base Bid`、`Top Adjustment`、`Top Placement Adjusted Bid`、`Rest of Search`、`Product Pages`、`Bidding Strategy`、`Potential Maximum Effective Bid` 和 `Break-even / Economic Risk`。计算 `Top Placement Adjusted Bid = Base Bid × (1 + Top Adjustment)`。
- `Potential Maximum Effective Bid` 必须使用平台/接口确认的 Dynamic Upward Cap：`Top Placement Adjusted Bid × Dynamic Upward Multiplier`。若当前平台没有返回可靠的动态上调上限，仍展示 `Top Placement Adjusted Bid`，并将潜在最大值标为 `【动态上调上限未确认】`，不得凭经验填入倍数；经济边界不足时标记 `【经济边界数据不足】`。
- 本默认只适用于 `COR-EXA`。`EXP-PHR`、`DIS-BRO`、`DIS-AUT`、`COM-ASI` 必须独立决定 Bid、Placement 和 Bidding Strategy，不继承本节默认。
- 6-3 接管时必须读取真实的 Top of Search Impressions、Impression Share（如有）、Clicks、CPC、Orders、CVR、CPA、ACoS；根据转化、经济边界、相关性、预算和库存决定继续、提高、降低或取消 Top 调整，不因“新品需要数据”机械加 Bid。

## 预算决策与资金释放

6-1 不只是把预算分给 Campaign，也要先判断产品是否值得投入、最多值得投入多少。固定顺序为：`Business Opportunity → Launch Goal → Market Potential → Benchmark Sales → Own Product Economics → Inventory / Season Window → Expected Traffic Economics → Launch Total Investment Budget → Phase Budget → Daily Budget Envelope → Campaign Budget → Bid / Placement`。不得从“每个 Campaign 分多少钱”倒推总预算。

- 综合可获得的 Niche 容量、主要竞品/Benchmark 销量和销售额、目标市场份额、售价、Coupon、Amazon/FBA费用、产品成本、物流成本、Contribution Margin、库存、季节窗口、预计周期、Own CVR/CPC/CPA、市场 CPC、关键词竞争、Launch Goal、广告/自然订单目标，形成 `AI Recommended Launch Investment｜AI推荐新品投入`。Benchmark 销量只用于机会规模和推算，不得写成 Own Product 事实。
- 所有 `Benchmark 日销 × 目标争取比例`、`Expected Orders ≈ Clicks × Expected CVR`、Required Clicks、Expected Ad Spend、Expected CPA、Expected Ad Orders 等必须标记 `[推算指标]`，并与真实订单/销售额分开。
- 正式报告必须有《Launch Investment Decision｜新品投资决策》，至少列出 Market Opportunity、Benchmark Sales Evidence、Target Opportunity、Launch Goal、Launch Window、Product Economics、Expected Traffic Economics、Recommended Total Launch Budget、Initial Daily Budget、Maximum Daily Budget、Phase Budgets、Budget Release Gates、Expected Validation Output、Capital Efficiency Assessment、Largest Downside Risk 和 Stop-Loss Logic。总预算是 `Maximum Planned Investment Envelope`，不是必须一次花完的金额。
- Launch Total Investment Budget 的窗口和金额按 Season Window、Launch Mode、Evidence Maturity、经济边界和库存动态决定；每一项写 Evidence、Reason、Expected Purpose、Confidence（High/Medium/Low）和 `[AI推荐预算]`。不得机械采用 28 天或其他固定周期。
- 预算按 Validation、Focus、Scale、Steady State 阶段配置。先释放验证预算，只有成交证据、重复成交、经济性或排名/自然流量证据达到晋级条件，才释放下一阶段；负向证据充分时停止释放，不因总预算尚有余额而继续烧钱。
- 输出 `Initial Daily Budget`、`Maximum Daily Budget After Validation`，必要时再输出 Scale Stage 上限。低于 `$100/day` 表示小规模验证，约 `$100/day` 表示标准 Launch，高于 `$100/day` 表示 Accelerated Launch；还可以建议暂不 Launch。金额必须由当前证据推导，不得用默认值伪装成事实。
- Campaign 预算是最后一层，按 COR、EXP、DIS、AUTO、COM 等实际角色分配；Budget、Bid、Bidding Strategy 和 Placement 联合判断，不能同时无条件拉高。
- 投资回报至少同时查看 Ad-Level Return（Spend、Ad Sales、Ad Orders、CPA、ACoS、ROAS）、Product-Level Economics（售价、Coupon、费用、成本、Contribution Margin、Break-even ACoS、Acceptable CPA）和 Launch Asset Return（成交词、重复成交词、关键词排名、自然订单/占比、总订单增长）。数据缺失时标记 `[经济边界数据不足]`，不编造数值。
- `Capital Efficiency Assessment｜资金效率判断` 只使用状态判断，不使用虚假 0–100 分：`[值得积极投入]`、`[值得标准投入]`、`[只值得小规模验证]`、`[当前不值得继续增加投入]`、`[市场机会大但当前页面/产品承接不足]`、`[证据不足｜采用Fallback预算]`。
- 新品可以为验证或排名承受短期高 ACoS，但必须写明最大允许投入、验证问题、期限、继续证据和停止证据；“新品前期亏钱正常”不能单独构成继续投入理由。
- 用户明确的日预算或总投入是 `[人工明确约束]`，优先级高于 AI 建议，AI 不得突破；若与 Launch Goal 冲突，输出 `[目标与预算约束冲突]` 并解释预期无法支持的部分。

## 固定输出

正式报告按 `templates/report-outline.md` 生成，至少包含：新品推广核心战略、输入版本追溯、页面推广资格、人工推广思路同步、核心推广假设、推广关键词地图、流量—页面承接矩阵、新品推广结构、预算分配逻辑、价格—推广关系、新品推广验证表、测试继续/停止规则、首阶段执行清单、推广观察指标与数据需求、风险、反方检查、最终推广状态和 6-2 输入交接包（仅状态允许时）。

关键词表和验证表必须保留证据状态。缺失数据写 `[证据不足]`、`[预算待确认]`、`[CPC待验证]`、`[关键词待验证]` 或 `[页面承接待验证]`，不得用经验数字补齐。

数据性质必须分开标记：SellerSpace 已返回的 Spend/Orders/CPC 等是 `[真实运行事实]`；SellerSpace/Amazon 建议词或建议 Bid 是 `[平台/工具推荐]`；H10 建议 Bid 是 `[第三方原始推荐数据]`；用户给出的目标和限制是 `[人工目标]`；模型选择启动 Bid、Budget 或结构是 `[AI策略建议]`；尚未运行或来源不明的结果是 `[待验证]`。建议 Bid 不得改写成实际 CPC，搜索量不得改写成销量。

最终状态只允许：

- `【新品推广方案已形成｜可进入执行】`
- `【新品推广方案基本形成｜部分预算/关键词待确认】`
- `【关键页面或产品条件不足｜暂不建议启动推广】`
- `【关键推广数据不足｜可先执行小规模验证】`
- `【上游页面状态不满足推广条件｜返回5-4】`

只有页面、产品、流量承接、预算边界和验证逻辑都满足时，才可用第一种状态；Direct Launch Mode 在最低条件基本满足但证据不完整时可用受控小规模验证状态。没有足够历史广告数据也不应因此停止。真实页面问题才可触发返回 5-4，缺少 5-4 本身不能触发该状态。

## 阶段6闭环与运行日志

6-1 的输出必须能进入“推广目标 → 广告架构 → 实际运行 → 6-2诊断”的闭环：

- 建立动态关键词池：核心精准候选词、高意图长尾词、场景词、探索 Seed 词、泛词、竞品 ASIN、低优先级词、暂不投放词、证据不足词。每项记录英文词、中文含义、来源、相关性、购买意图、竞争/成本信号、新品期适配、Match Type、风险和下一步验证方式；不能只因搜索量、H10排名或竞品出单高就定为核心词。
- Campaign 数量和组合按产品、目标、库存与证据动态决定。每个 Campaign/Ad Group 记录目的、阶段、对象、Match Type、Bid 来源、Budget 逻辑、Placement、验证内容、成功/失败信号和交给 6-2 的触发条件。
- 对用户目标做反推：目标订单/自然订单结构 → 点击需求 → CVR 假设 → CPC 边界 → Budget → 关键词与 Campaign 结构 → 验证周期。缺少成本、CVR、预算或库存参数时标记【待确认】或【数据不足】，不伪造边界。
- Coupon/Price 只能作为明确的流量验证变量，写清目的、实验窗口、经济性影响、回撤条件和验证指标；Coupon 不是广告优化的万能补偿工具。
- 新品没有广告历史时仍应形成 Cold Start Advertising Architecture：使用产品事实、可用的 5-4 或 Direct Launch 最低检查、5 阶段页面输入（如有）、H10/Cerebro、Niche/Search Term、SellerSpace 推荐（如有）、价格/Coupon、库存和人工目标设计受控小规模验证；CPC、CVR、ACoS、订单等未知值标记待验证，不用经验数字补齐。
- 建立《关键词来源交叉验证》：H10/Cerebro 是竞品反查和市场证据，SellerSpace 推荐是投放候选，两者分别保留来源、日期和字段；H10 有词而 SellerSpace 无推荐不能淘汰，SellerSpace 推荐而 H10 无词不能直接定义为核心成交词。
- Bid 必须分别记录 H10 建议 Bid、H10 建议范围、SellerSpace/Amazon 建议 Bid/范围、历史实际 CPC、当前实际 Bid 和 AI 建议启动 Bid。建议 Bid 不是实际 CPC；冲突时核对日期、站点、Match Type 和口径，以人工预算边界设计小规模测试，不直接平均。
- 从人工推广目标反推目标订单、广告/自然订单结构、点击需求、CVR 假设、CPC 边界、Budget、关键词和 Campaign 结构；缺少 CVR、成本、预算或库存时标记数据不足。
- 首轮验证采用动态窗口，通常可观察 1–2 天资格与曝光、3–4 天 Search Term/CTR/初步 CVR、5–7 天重复成交词、无效流量、Campaign/Match Type差异和自然增长信号；不因单日波动频繁改广告。Search Term 生命周期由 6-3 依据真实运行数据判定。
- SellerSpace MCP 与本地广告原始文件覆盖同一窗口时必须交叉核对；冲突标记 `【广告数据源冲突】`，写明来源、时间范围、指标、口径、差异、归因延迟/时区可能性和核查方式，不静默选择。
- 正式报告可形成后续执行计划；批准前不写广告，批准后仅按已批准创建清单执行。每次实际运行、人工决定、执行方式和 1/3/7 天验证，统一记录到 `06_SKILL分析报告/广告表现汇报优化日志/`；该目录不属于正式报告索引。

### 6-2 输入接口

报告中的《6-2输入交接包》至少交接：Product Code、own_asin、Mapped_SKUs[]、Advertised_SKUs[]、Marketplace、产品阶段、上线时间/Review/库存状态（如有）、当前推广目标、验证周期、允许风险、Price/Coupon、真实成本与 Break-even ACoS（如可计算）、Campaign/Ad Group/Target 结构、Keyword/Seed/benchmark_asin 分组、Match Type、初始 Bid/Budget/Placement 依据、初始假设及证据、成功/失败信号、6-2 可建议动作、必须人工批准的动作和关键未知项。

广告平台接入只按实际能力区分【读取能力】和【写入能力】；没有写入能力时回退为“AI建议 + 人工执行”，不假装已执行。

## 正式报告与 0-2

保存到当前 Product Root 的 `06_SKILL分析报告/`，不覆盖历史：

`6-1_[产品编号]_新品推广方案_V[最大版本号+1]_[YYYYMMDD]_[HHMMSS].html`

成功写入、确认文件存在且命名正确后，调用 `hzp-amz-0-2-report-index`，原样传递本次 Product Code、Products Root、Product Root。6-1 不扫描、生成、排序、维护或备用更新 `index.html`。报告失败不调用 0-2；报告成功但 0-2 失败时保留报告，并明确“正式报告：生成成功；报告索引：更新失败；原因：[实际原因]”。

详细字段、状态门、关键词与预算规则见 `references/launch-framework.md`；创建蓝图与审批视图见 `references/creation-blueprint.md`；证据驱动扩词见 `references/evidence-gated-keyword-expansion.md`；预算决策 CASE K-R 见 `references/budget-decision-cases.md`；6-2 交接字段见 `references/handoff-schema.md`；HTML 章节与表格见 `templates/report-outline.md`。
## Portfolio-aware Advertising Identity（增量规则）

阶段 6 统一使用 `Amazon广告身份解析规则.md`，身份链为 `Product_NewCode → Product_Code → SellerSpace Store → Product_Code_Prefix → Marketplace → Own ASIN → Mapped_SKUs[] → Advertised_SKUs[] → Portfolio Name → Portfolio ID → Var_Code`。映射表实际列名 `广告组合` 是 Portfolio Name；先按唯一 ACTIVE 行读取，再在已验证 Store + Marketplace 范围内通过 SellerSpace `discover_capabilities`、`discover_fields` 和只读 Portfolio 查询解析 Portfolio ID。不得根据 ASIN、文件名或历史报告猜测，也不得在 Skill、模板、测试或报告中写死真实 Portfolio ID。

每个新 Campaign 的审批视图、Detailed Creation Blueprint、Prepared Change Plan 和 Read-Back Verification 都必须显示 Portfolio Name、Portfolio ID、解析状态，并与 Store、Marketplace、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[] 做字段级比对。只有 `PORTFOLIO_VERIFIED` 才能继续新建；Portfolio 缺失、未解析、同名多 ID、跨店铺/站点或 Prepared/Read-Back 不一致时输出 `【广告组合身份未验证/冲突｜禁止写入】`。旧 Campaign 不自动迁移或改组合；Legacy overlap 只记录风险。

## 统一 Product / Variant Advertising Identity（增量规则）

6-1 必须调用共享 `scripts/resolve_amazon_ad_identity.py` 的 `resolve_advertising_identity()`，先解析 `Product_NewCode → Product_Code → SellerSpace Store → Product_Code_Prefix → Marketplace → Own ASIN → Mapped_SKUs[] → Advertised_SKUs[] → Portfolio → Var_Code`，再设计广告。`Product_NewCode`（如 N+数字）是研究/新品代码，永远保留且不代表“未创建”；正式 Campaign 只能使用正式 `Product_Code`。前缀只从“店铺产品代码前缀”表运行时读取并校验，禁止硬编码或反推正式代码。

产品身份必须严格区分 Own ASIN、Benchmark ASIN 和 Product Target ASIN。变体来自“产品对应变体”表；只有可靠的 `Var_Code → Child ASIN → Mapped_SKUs[]` 关系才可作为 Advertised Product，否则输出 `【变体广告身份映射不完整】`，允许形成只读方案但禁止写入。Campaign 命名由共享 `format_campaign_name()` 生成：无变体为 `[Product_Code].[AdType]-[Role]-[Target/Match]-[Sequence]`，有变体为 `[Product_Code].[Var_Code].[AdType]-[Role]-[Target/Match]-[Sequence]`。

批准清单、Prepared Plan 和 Read-Back 必须逐字段记录并比对 `Product_NewCode`、正式 `Product_Code`、Store、Marketplace、Product_Code_Prefix、Portfolio Name/ID、Var_Code、Advertised Child ASIN、Mapped_SKUs[]、Advertised_SKUs[]、Campaign Name。使用 `diff_identity_fields()` 检测 Material Difference，使用 `verify_advertised_product()` 检查回读；任一身份冲突、Var_Code 不唯一或子 ASIN、Mapped_SKUs[]/Advertised_SKUs[] 不一致都停止真实写入。6-1、6-2、6-3 共享同一解析结果，不得重新猜身份。

## Campaign / Ad Group Naming（增量规则）

Campaign 是稳定身份与战略角色的组合，不包含日期、Bid、Budget、Coupon、Price、ACoS、ROAS、CVR、Placement 百分比、Bidding Strategy 或阶段天数。本次命名增量唯一新增的是已识别独立 Var_Code 的 `.[Var_Code]` 段；共享 `format_campaign_name()` 继续使用固定词典：AdType=`SP|SB|SD`；Role=`COR|EXP|DIS|COM|CAT|DEF`；Target/Match=`EXA|PHR|BRO|AUT|ASI|CAT`；Sequence 为 `01、02、03…`。有独立变体时格式为 `[Product_Code].[Var_Code].[AdType]-[Role]-[Target/Match]-[Sequence]`；无独立变体的原格式保持兼容。

`Product_NewCode` 永远不进入正式 Campaign Name。只有真实 Campaign 专属于一个 Var_Code 时才加入该 Var_Code；真实支持多个 Advertised Products 且 Blueprint 明确 `Variant Scope=MULTI_VARIANT` 时才省略 Var_Code。Portfolio、Store、Marketplace、ASIN、SKU 不进入默认名称，而是在 Blueprint、执行对象和 Read-Back 中记录。

Ad Group 使用 `format_ad_group_name()`：独立变体为 `[Product_Code].[Var_Code].[Role]-[Sequence]`，无变体为 `[Product_Code].[Role]-[Sequence]`；多个组仅在确有隔离目的时使用 `AG01/AG02`，不得重复 Campaign 全部信息。`next_campaign_sequence()` 必须在审批前读取 Existing Campaigns 并确定下一个 Sequence；发现 `-01` 后需要独立新 Campaign 才用 `-02`，并写明原因。旧 Campaign 不自动重命名、暂停或删除。

审批页必须先展示《Campaign Naming Preview》，再展示完整广告对象。Approved→Prepared 用 `diff_identity_fields()` 比较 Campaign Name、Ad Group Name、Campaign Count 等命名字段；批准后名称变化是 Material Difference，停止并重新确认。Read-Back 必须核对实际 Campaign/Ad Group 名称与批准值；不一致时标记 `【实际广告命名与批准方案不一致】`。第二批扩词优先加入已有正确角色 Campaign，只有新语义簇、独立预算或独立实验等明确原因才创建下一个 Sequence。

## ERP Keyword Provider（阶段6统一规则）

阶段 6 的 ERP 历史关键词只通过共享 `scripts/erp_keyword_adapter.py` 读取；本 Skill 不得自行编写 PickPwKView SQL 或解释 Provider 列名。运行时先读取 `03_系统配置/erp-amazon-data-mapping.json` 和 `erp-amazon-pickpwkview-schema.md`，再从本次已确认的 `[Product Root]/01_产品档案.md` 读取档案中明确记录的 ERP 产品编号（返回实际字段名；没有编号为 `[ERP_PROID_MISSING]`，冲突为 `[ERP_PROID_CONFLICT]`）。只以该编号作为参数查询 `Amazon.dbo.PickPwKView.ProId`，不得用 Product_Code、ASIN、文件名、首条记录或相似产品替代，也不得跨产品。

适配器返回每行 `Keyword`/`KeywordCn`、完整 `raw_fields`、字段定义状态和追溯信息（`Provider`、`Source_View`、`ERP_ProId`、`Field_Definition_Source`、`Retrieved_At`、`Source_Grain`、`Metric_Semantics`、`Data_Through`、`Freshness`、`Aggregation_Method`）。字段语义只以 `03_系统配置` 文档为准；未明确的列必须标记 `SEMANTICS_UNCERTAIN`，不得把它们猜作搜索量、点击、订单、销售、CVR、排名或竞价。连接复用既有只读配置/密钥，SQL 只允许参数化 SELECT；密码、服务器和连接字符串不得进入 Skill、报告、日志或 Git。

阶段 6 共用的 ERP 精准词语义固定为：当前产品 `ProId` 范围内，`PickPwKView.Tags` 包含完整标签 `|1精准|` 且 `Keyword` 有效的记录。`IsExact` 当前定义为“暂无用”，不得用于精准词判定；6-1 只能把共享适配器返回的精准词作为候选证据，不能自行另造筛选逻辑。

- 6-1：ERP 关键词仅作为 COR 候选、EXP 候选和少量 DIS Broad Seed 的辅助证据，不能由 ERP 历史标记直接升级为核心成交词。
- 6-2：ERP 关键词仅作为当前产品历史背景或监控解释；当前 Amazon 自有经营数据优先，语义不明不计算经营指标。
- 6-3：ERP 关键词仅作为历史 Search Term/生命周期参考；当前 Amazon 自有广告数据足够后由自有数据接管，不自动跨产品扩展。

连接/驱动/密钥不可用返回 `[ERP_KEYWORD_PROVIDER_UNAVAILABLE]`，无匹配行返回 `[ERP_KEYWORD_DATA_NOT_FOUND]`；这些状态只降级 ERP 证据，不阻断本 Skill 其他数据源。
## MCP Provider Boundary / Canonical Business Model

6-1 的推广判断只消费 HZP Canonical Business Model，不直接依赖 SellerSpace/优麦云的原始 Tool Name、Field Name、JSON 结构、枚举、分页或指标名称。Provider Adapter 负责把实际 Provider 返回映射为统一业务语义：`Product_Code`、`Var_Code`、`ASIN`、`Mapped_SKUs[]`、`Advertised_SKUs[]`、`Primary_Advertised_SKU`、Store、Marketplace、Portfolio，以及 Orders/Sales/Traffic/Inventory 和广告指标。

Provider 能力必须显式标记 `SUPPORTED`、`NOT_SUPPORTED` 或 `SEMANTICS_UNCERTAIN`；缺失能力只返回 `[CAPABILITY_NOT_AVAILABLE]`，不得猜测或用另一字段静默替代。真实写入仍固定为 Decision → Prepare → Exact Diff → Apply → Read-back → Log → Validation；Provider 缺少可靠等价能力时标记 `[SAFE_WRITE_CAPABILITY_NOT_AVAILABLE]` 并阻断写入。未来新增 Provider 只需新增 Adapter 与真实 Schema/Capability/语义映射，不改变本 Skill 的核心业务判断。

## 6-0-1 关键词专业输出

如果当前产品已有 6-0-1/6-0-2 latest-valid 关键词资产，6-1 可读取 6-0-1 双轨精准词 CSV 以及 6-0-2 精准泛词结果，作为初始广告蓝图输入；6-1 仍负责整体 Launch、预算、阶段与经济边界，不复制 6-0-1 的精准词识别或 6-0-2 的聚类、泛词算法。
