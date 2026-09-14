# 6-1 运行框架与证据规则

## 1. 产品与报告选择

- 先由用户提供或当前会话确认 Products Root 和产品代码；在该根目录中定位唯一 Product Root。
- 读取 `01_产品档案.md`，确认产品代码、产品名称、站点和当前研究对象。身份冲突必须停止。运行上下文必须分开记录 `own_asin`（自有 ASIN）和 `benchmark_asin`（对标 ASIN）。
- `04_产品推广思路.md` 是人工输入，不是自动正确策略。空缺时标记 `[推广思路待确认]`。
- 版本化 HTML 只按 `Product Code + Skill 编号` 匹配；最大 V 优先，同 V 按文件名中的 `YYYYMMDD_HHMMSS` 最新。不得按 filesystem 时间、目录顺序或 first found 选择。
- 排除 `index.html`、Draft、Preview、Test、Temp、Demo、Debug、failure、incomplete、invalid、deprecated 等文件。最新有效性不确定时输出 `[上游报告有效性无法确认]`，不要静默回退旧版。

身份规则：从 Amazon 产品店铺映射表解析并验证 `own_asin`、Store、Marketplace、SKU；`benchmark_asin` 仅用于市场研究、Cerebro、Niche、页面对标、关键词挖掘和 Product Targeting 候选。禁止使用 `benchmark_asin` 查询 SellerSpace 商品、库存、广告、订单、Listing 或经营数据；禁止用一个泛化 `asin` 字段同时承载两种身份。

## 2. 运行模式与 5-4 状态门

先判断当前产品是否存在最新有效 5-4 正式报告：

- 有：使用 `Pipeline Mode｜完整链路模式`，按下表继承页面状态和 P0/Claim 边界。
- 没有：使用 `Direct Launch Mode｜直接推广模式`，不因缺少 5-4 停止，先做最低必要推广前检查，不复制完整 5-4。

Direct Launch Mode 最低必要检查：Own ASIN、SKU、Marketplace、Store；Listing/可售状态；主图、标题、当前价格；可售库存或明确的启动状态；已知成本、Coupon 和广告经济边界。缺少预算或经济数据时标记待确认并继续形成小规模验证方案。只有错误身份、不可售、重大页面问题、广告资格异常或无法安全执行时才阻止启动。检查结果只能写为：`【最低推广条件满足】`、`【最低推广条件基本满足｜存在待验证项】`、`【存在关键页面问题｜建议先修复】`、`【商品不可售或广告资格异常｜暂不启动】`、`【关键事实不足｜无法安全启动】`。

只有存在真实页面证据时，才可使用 `【上游页面状态不满足推广条件｜返回5-4】`。缺少 5-4 本身不是该状态的证据。

| 5-4 状态 | 6-1处理 |
|---|---|
| `【页面通过｜可上线/进入推广】` | 读取 6-1 输入交接包，继续检查产品、预算和关键词。 |
| `【有条件通过｜完成P0修改后上线】` | 必须核实 P0 已完成；无法确认则返回 5-4。 |
| `【需要优化｜修改后重新审核】` | 输出 `【上游页面状态不满足推广条件｜返回5-4】`，不做正常大规模推广。 |
| `【关键Claim或产品事实冲突｜暂不建议上线】` | 返回 5-4，保留阻断原因。 |
| `【页面成品不足｜暂无法完成正式审核】` | 返回 5-4；不能用广告弥补页面缺失。 |
| 缺少、失败或无法确认的 5-4 | 切换 Direct Launch Mode；记录未读取 5-4，并执行最低必要推广前检查。 |

## 3. 关键词地图字段

至少记录：Keyword、中文理解、搜索意图、关键词角色、数据来源、Search Volume（如有）、Organic Rank（如有）、Sponsored Rank（如有）、产品匹配度、页面承接位置、商业价值判断、当前推广角色、证据状态和风险。关键词角色按真实资料动态使用：核心定义词、核心需求词、属性差异词、使用场景词、长尾高意图词、竞品承接词、探索词、暂不投放。

明确区分：ABA/H10/Brand Analytics 的搜索词证据、Cerebro 词表、历史广告 Search Term 和第三方建议 Bid。第三方建议 Bid 不是 CPC；搜索量不是销量；BSR 不能推销量；没有字段就不填数值。

## 4. Campaign 与验证

每个 Campaign/Ad Group 记录目的、流量对象、对应假设、成功信号、失败信号、预算逻辑、Bid 来源、继续/暂停条件和何时交 6-2。至少逻辑分开核心验证流量、探索流量和竞品/商品流量；必要时再单列防御流量。不要自动把 Auto+Exact+Phrase+Broad 全部打开。

验证表按以下字段展开：假设、来源、重要性、验证方法、流量来源、目标 Keyword/ASIN/Category、观察指标、所需数据、成功信号、失败信号、下一步动作。用样本量和经济边界解释信号，禁止统一点击阈值。

## 5. 预算、投资决策、价格和促销

`$100/day` 是 `Fallback Planning Budget｜缺乏充分预算证据时的系统默认规划值`，不是固定新品预算。6-1 必须先判断产品值得投入多少，再决定阶段和 Campaign 预算。预算决策顺序为：`Business Opportunity → Launch Goal → Market Potential → Benchmark Sales → Own Product Economics → Inventory / Season Window → Expected Traffic Economics → Launch Total Investment Budget → Phase Budget → Daily Budget Envelope → Campaign Budget → Bid / Placement`。

### 5.1 Launch Investment Decision

当数据存在时，综合 Niche 容量、Benchmark/主要竞品销量与销售额、目标市场份额、售价、Coupon、Amazon/FBA 费用、产品/物流成本、Contribution Margin、库存、季节窗口、预计销售周期、Own CVR/CPC/CPA、市场 CPC、关键词竞争、Launch Goal 及广告/自然订单目标，输出 `AI Recommended Launch Investment｜AI推荐新品投入`。Benchmark 只能作为市场机会和推算证据，不能写成自有产品事实。

正式报告新增《Launch Investment Decision｜新品投资决策》，至少包含：Market Opportunity、Benchmark Sales Evidence、Target Opportunity、Launch Goal、Launch Window、Product Economics、Expected Traffic Economics、Recommended Total Launch Budget、Initial Daily Budget、Maximum Daily Budget、Phase Budgets、Budget Release Gates、Expected Validation Output、Capital Efficiency Assessment、Largest Downside Risk、Stop-Loss Logic。总预算是 `Maximum Planned Investment Envelope`，不是必须花完的金额。

总预算窗口和金额按 Season Window、Launch Mode、Evidence Maturity、经济边界和库存动态决定；不得机械采用 28 天。报告记录 Evidence、Reason、Expected Purpose、Confidence（High/Medium/Low）和 `[AI推荐预算]`。若证据不足，采用 Fallback 并标记 `[证据不足｜采用Fallback预算]`，不能把 `$100/day` 写成产品固定规则。

### 5.2 推算与回报

可靠 Benchmark 销量存在时，可用 `Benchmark 日销 × 目标争取比例 → Potential Daily Orders`，再结合 Expected Ad Order Share、Expected CVR、Expected CPC 推算 Required Clicks、Expected Ad Spend、Expected CPA、Expected Ad Orders；每项标记 `[推算指标]`，并与真实订单/销售额分开。不得把推算销量写成事实。

至少分开查看：

- Ad-Level Return：Spend、Ad Sales、Ad Orders、CPA、ACoS、ROAS；
- Product-Level Economics：Selling Price、Coupon、Amazon Fees、Product Cost、Freight、Contribution Margin、Break-even ACoS、Acceptable CPA；
- Launch Asset Return：Converting Search Terms、Repeated Converting Terms、Keyword Rank、Organic Orders、Organic Share、Total Order Growth。

只有售价、Coupon、费用、成本和测试边界充分时才计算 Break-even ACoS；缺失时标记 `[经济边界数据不足]`。

### 5.3 阶段预算与释放

总预算按 Validation、Focus、Scale、Steady State 动态配置。先释放验证预算，只有成交证据、重复成交、经济性或排名/自然流量证据达到晋级条件，才释放下一阶段；负向证据充分时停止释放，不因总预算余额继续投入。输出 `Initial Daily Budget`、`Maximum Daily Budget After Validation`，需要时再输出 Scale Stage 上限。低于 `$100/day` 表示小规模验证，约 `$100/day` 表示标准 Launch，高于 `$100/day` 表示 Accelerated Launch；也可以建议暂不 Launch。Campaign 预算必须在 Daily Budget Envelope 之后决定，不能先凑 Campaign 再反推总额。

Budget、Bid、Bidding Strategy、Placement 必须联合设计，禁止同时无条件拉高。新品若因验证或排名暂时接受高 ACoS，必须写明最大投入、验证问题、期限、继续证据和停止证据；“新品前期亏钱正常”不是继续投入理由。

### 5.4 资金效率与人工约束

输出 `Capital Efficiency Assessment｜资金效率判断`，只使用状态，不做虚假 0–100 评分：`[值得积极投入]`、`[值得标准投入]`、`[只值得小规模验证]`、`[当前不值得继续增加投入]`、`[市场机会大但当前页面/产品承接不足]`、`[证据不足｜采用Fallback预算]`。

用户明确的日预算或总投入标记 `[人工明确约束]`，优先级高于 AI 建议，6-1 不得突破；若与 Launch Goal 冲突，输出 `[目标与预算约束冲突]`，说明按该约束无法合理支持的目标部分。预算、成本、CVR 或销量不足时继续完成有证据的结构，但不编造精确金额。

Coupon、Promotion、Vine、Deal 只有在说明要解决的阻力、实验窗口、经济影响、回撤条件和验证指标时才建议，不机械默认。

## 6. 指标与动作

观察层次：曝光、点击、转化、商业、搜索词、关键词、商品投放、页面反馈。ACoS/ROAS/CTR/CVR 不能单独决定成败：

- 无曝光：进入广告资格、索引、相关性、竞价、预算和状态诊断，属于 6-2；不无限加价。
- 有点击无订单：联合搜索意图、产品、页面、价格、Review 和竞争判断；不自动加价或直接判页面失败。
- 少量订单：只是积极信号，还需稳定性、可复制性、流量规模、商业价值和库存承受能力。

## 7. 证据标签

使用 `[已确认事实]`、`[原始数据]`、`[人工事实]`、`[人工推广思路]`、`[专家判断]`、`[推广假设]`、`[分析推断]`、`[推算指标]`、`[预算待确认]`、`[CPC待验证]`、`[关键词待验证]`、`[消费者价值待验证]`、`[页面承接待验证]`、`[证据不足]`。下游 6-2 必须知道每个 Campaign 原始目的和假设。


## 阶段6闭环补充（运行与交接）

6-1 的输出必须能进入“推广目标 → 广告架构 → 实际运行 → 6-2诊断”的闭环：

- 建立动态关键词池：核心精准候选词、高意图长尾词、场景词、探索 Seed 词、泛词、竞品 ASIN、低优先级词、暂不投放词、证据不足词。每项记录英文词、中文含义、来源、相关性、购买意图、竞争/成本信号、新品期适配、Match Type、风险和下一步验证方式；不能只因搜索量、H10排名或竞品出单高就定为核心词。
- Campaign 数量和组合按产品、目标、库存与证据动态决定。每个 Campaign/Ad Group 记录目的、阶段、对象、Match Type、Bid 来源、Budget 逻辑、Placement、验证内容、成功/失败信号和交给 6-2 的触发条件。
- 对用户目标做反推：目标订单/自然订单结构 → 点击需求 → CVR 假设 → CPC 边界 → Budget → 关键词与 Campaign 结构 → 验证周期。缺少成本、CVR、预算或库存参数时标记【待确认】或【数据不足】，不伪造边界。
- Coupon/Price 只能作为明确的流量验证变量，写清目的、实验窗口、经济性影响、回撤条件和验证指标；Coupon 不是广告优化的万能补偿工具。
- 正式报告可形成后续执行计划；批准前不写广告，批准后仅按已批准创建清单执行。每次实际运行、人工决定、执行方式和 1/3/7 天验证，统一记录到 `06_SKILL分析报告/广告表现汇报优化日志/`；该目录不属于正式报告索引。

### 6-2 输入接口

报告中的《6-2输入交接包》至少交接：产品阶段、当前推广目标、Campaign/Ad Group 结构、关键词分组、Seed 词、核心候选词、竞品 ASIN、初始 Bid/Budget/Placement 逻辑、Coupon/Price、验证周期、成功/失败信号、6-2 可建议动作、必须人工确认的动作和关键待验证项。

广告平台接入按实际【读取能力】/【写入能力】审计；写入能力不存在时只能交接建议，不得宣称已执行。

## 8. SellerSpace MCP 只读数据入口

在进入本节查询前，先读取 Amazon 行业共享文件 `Amazon产品身份解析规则.md`，从 Products Root 的 `00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx` 解析当前 Product Code 的唯一 ACTIVE 身份，并以 Store + Marketplace + ASIN + SKU 做 MCP 二次验证。身份缺失、重复或冲突时遵循共享规则停止或降级，不复制另一套解析逻辑。

SellerSpace 可用时先用 `discover_capabilities` 和 `discover_fields` 核对真实实体、字段、单位、日期参数和站点，再固定 `get_stores` 返回的 sellerId 与 marketplace。6-1 允许读取：

- `query_ads`：Campaign、Ad Group、Product Ads、Keywords、Targets、Search Query、Search Term Frequency、Negative Keywords、Negative Targets，以及 impressions、clicks、ctr、cpc、cost、orders、sales、cvr、acos、roas、bid、budget、placement 等实际存在字段；
- `get_metric_history`：Campaign、Product、Keyword、Target、Search Term 的日/周/月或支持的Placement趋势；
- `query_products`、`query_store_performance`、`query_orders`：商品、店铺和订单表现；
- `listing`、`query_inventory`、`query_shipments`：Listing、售价、SKU、库存、在途、销售速度、可售天数和运输状态（仅使用实际返回字段）；
- `get_sp_campaign_recommendations`：建议关键词、建议竞价/区间、推荐ASIN或Product Target；
- `export_data`：在确实需要保存原始快照时导出。

工具名称不能证明字段存在。不支持的字段写 `【SellerSpace当前无法提供】`。`query_orders` 不天然区分广告订单与自然订单；`query_products` 中名称像订单数但单位异常的字段，未经核实不得使用。批准前 6-1 不调用 `prepare_change_plan` 或 `apply_change_plan`；批准完整创建清单后，仅按 `approved-creation.md` 的新广告创建流程调用。

## 9. 数据性质与冲突

报告中分别标记：

- `[真实运行事实]`：SellerSpace 或本地广告原始文件在明确站点、日期和窗口内返回的指标；
- `[平台/工具推荐]`：SellerSpace/Amazon 推荐词、推荐ASIN、建议 Bid 或建议范围；
- `[第三方原始推荐数据]`：H10/Cerebro 原始建议 Bid 或范围；
- `[人工目标]`：预算、目标订单、最大亏损、毛利底线、库存限制等用户确认项；
- `[AI策略建议]`：模型基于上述证据形成的启动结构、Bid、Budget 或验证动作；
- `[待验证]`：尚未运行、来源不明或需要人工/供应商确认的内容。

SellerSpace 推荐 Bid 不是实际 CPC，H10 推荐 Bid 也不是实际 CPC、ACoS 或盈利结论。若 SellerSpace 与 `05_分析源数据/06_广告数据下载/` 覆盖同一窗口但明显冲突，必须输出 `【广告数据源冲突】`，同时记录两个来源、时间范围、指标和口径、差异、归因延迟或时区可能性及核查方法。

## 10. 新品冷启动与关键词母池

没有历史广告数据时，不因缺少历史而停止 6-1。用产品事实、可用的 5-4 页面依据或 Direct Launch 最低必要检查、5 阶段页面输入（如有）、H10/Cerebro、Niche/Search Term、SellerSpace推荐（如有）、Price/Coupon、库存和人工目标形成 Cold Start Advertising Architecture；CPC、CVR、ACoS、订单和利润未知时只写假设与验证方式。

先形成《新品关键词母池》，再选择启动池。每个词至少保留：Keyword、中文理解、来源、来源ASIN、Search Volume、Organic/Sponsored Rank、H10建议Bid/Range、SellerSpace建议Bid/Range及来源状态、相关性、购买意图、竞争信号、Match Type、优先级、风险和验证方式。分类可包含核心精准候选词、高意图长尾词、场景词、问题词、探索 Seed 词、泛词、竞品品牌/ASIN、低优先级词、暂不投放词和证据不足词。禁止用没有依据的综合评分。

H10/Cerebro 词与 SellerSpace 推荐词合并时去重但不丢来源。两者交集可以提高新品验证优先级，不能直接定义为核心成交词；核心成交词只能由真实运行数据交给 6-2 判定。



## 10.1 Evidence-Gated Keyword Expansion

母词池只保存候选与证据，不等同于广告创建清单。先按来源、日期、相关性和意图去重清理，再生成 Semantic/Purchase Intent Cluster。首批释放由 6-1 按证据和经济边界主动筛选；未释放词保留状态 `HELD_FOR_EXPANSION`、`WAITING_CLUSTER_VALIDATION`、`LOW_PRIORITY`、`INSUFFICIENT_EVIDENCE` 或 `DO_NOT_LAUNCH`。

单个词 1 Click/1 Order 只能是 `FIRST_ORDER_VALIDATED`，不能释放整个 Cluster。只有多个相关 Search Terms 重复成交、CVR/CPA/ACoS、相关性、时间窗口、库存和自然排名/订单证据共同支持时，Cluster 才可从 `INITIAL_SIGNAL` 升级 `VALIDATED`。具体门槛按样本和商业边界动态判断，不使用死板固定数字。

扩词由 6-2 生成分批 Expansion Batch；每批必须有原因、Cluster、关键词、Match Type、Bid、预算、目标、验证窗口和停止条件，并执行 Traffic Overlap Check。扩词与 Capital Release 联动，检查剩余预算、库存、季节窗口和经济性；验证成功也不能在库存不足时机械扩词。

## 11. 动态广告架构与Bid/Budget

Campaign/Ad Group按产品目标、库存和证据动态设计，可使用 Exact、Phrase、Broad、Auto、Competitor ASIN、Category 或 Scenario 等机制，但没有明确任务就不创建。每个计划项必须写：名称、目的、阶段、对象、Match Type、初始 Bid、Bid 依据、Budget、Budget 依据、Placement、待验证问题、观察周期、成功信号、失败信号和交给6-2的触发条件。Broad 是匹配机制，不等于泛关键词。

分别保存 H10建议Bid、H10建议范围、SellerSpace/Amazon建议Bid/范围、历史实际CPC、当前实际Bid和AI建议启动Bid。冲突时核对日期、站点、币种、Match Type和字段口径，不直接平均；以人工预算上限设计可逆的小规模测试。没有预算、CPC、CVR或成本边界时不生成精确盈利数字，只给比例、顺序和待确认项。

### 11.1 COR-EXA 新品核心 Exact Initial Bid

当且仅当关键词证据状态为 `CORE_HIGH_CONFIDENCE_EXACT`、广告角色为 `COR-EXA` 且产品处于新品启动阶段时，采用以下默认参考，并覆盖任何旧的 `Base Bid × 1.20` 规则：

1. `Base Bid` 由 Suggested Bid、Own Historical CPC（如有）、H10/Benchmark CPC、售价/毛利、Break-even ACoS、Target CPA、CVR、相关性、搜索量、竞争、Listing、Price/Coupon、库存和 Launch Goal 综合决定；不机械增加20%。
2. 默认 `Top of Search = +50%`、`Rest of Search = 0%`、`Product Pages = 0%`，`Bidding Strategy = Dynamic Bids - Up and Down`。+50% 仅是 Launch Reference，可依据证据改为 0/20/30/50/80% 或其他合理值。
3. 报告必须列出 `Base Bid`、`Top Adjustment`、`Top Placement Adjusted Bid = Base Bid × (1 + Top Adjustment)`、`Bidding Strategy`、`Potential Maximum Effective Bid` 和 `Break-even / Economic Risk`。潜在最大有效竞价使用已确认的 `Dynamic Upward Multiplier` 计算；未获得平台上限时显示 `【动态上调上限未确认】`，不填经验倍数。
4. `EXP-PHR`、`DIS-BRO`、`DIS-AUT`、`COM-ASI` 不继承 COR-EXA 默认，必须按各自验证任务独立设计 Bid、Placement 和策略。

降低或取消 Top +50% 的触发包括：Top 已有充分点击但无订单/重复转化不足、Top CPC/CPA/ACoS 超出经济边界、CVR 明显低于可靠基准、Listing/Offer/Price/Coupon 尚未准备、库存或预算无法承受、关键词相关性/竞争判断被新证据否定，或动态上调上限无法确认且风险不可接受。6-2 必须基于真实 Top 展示、点击、CPC、订单、CVR、CPA、ACoS 及份额（如有）接管继续/提高/降低/取消判断，不能机械加 Bid。

## 12. 目标反推、经济边界与价格实验

从人工目标反推：目标订单/自然订单结构 → 有效点击 → CVR假设 → CPC边界 → Budget → 关键词/Campaign结构 → 验证周期。只有真实售价、Coupon、Amazon/FBA费用、产品和物流成本等充分时才计算Break-even ACoS或最大可承受CAC；否则标记 `【经济边界数据不足】`。

Price/Coupon 只能作为明确实验变量，说明目的、窗口、经济影响、回撤条件、广告订单、自然订单、CVR、排名、利润和Coupon依赖度观察项。折扣带来的订单不能单独证明产品已验证成功。

## 13. 首轮验证与6-2边界

7天是常见观察窗口，不是固定阈值。可按数据量缩短或延长：Day 1–2看广告资格和曝光，Day 3–4看Search Term质量、CTR和初步CVR，Day 5–7看重复成交词、无效流量、Campaign/Match Type差异和自然增长信号。不因单日波动频繁改广告。

6-1只交接初始假设、结构、目标、数据需求、成功/失败信号和人工批准边界；Search Term生命周期、实际Bid调整、Negative、预算变更和运行后诊断交给6-2。6-1不能把未经真实运行证明的词写成核心成交词。

## 14. 广告原始数据归档与降级

SellerSpace实时查询不要求强制生成文件；调用 `export_data` 产生的原始文件默认保存到 `[Product Root]/05_分析源数据/06_广告数据下载/`，AI分析、人工决策和验证记录保存到 `06_SKILL分析报告/广告表现汇报优化日志/`。SellerSpace不可用时，6-1仍可用本地广告原始文件、H10/Cerebro、Niche/Search Term、产品资料和人工目标运行；缺少的SellerSpace字段标记 `【SellerSpace当前无法提供】`，不编造替代值。

## 15. Launch Goal Intake 与默认目标

优先读取产品事实和已有目标，只对无法可靠取得且会改变商业取舍的问题提问，优先使用 A/B/C/D 选择题。人工目标优先于商业约束，商业约束优先于客观事实，客观事实优先于系统默认目标。

没有人工目标时使用 [系统默认目标]：在可控投入下尽快验证真实成交路径、沉淀可重复成交关键词并判断是否值得放量；默认 Standard Growth Launch｜标准增长型 Launch，并根据窗口、季节性、库存和经济边界修正。对默认目标提供接受、稳健验证、加速/强攻、自定义四种快速确认。

## 16. Launch Window、阶段与成熟度

Standard Launch、Accelerated Launch、Seasonal Sprint 由日期、旺季/有效窗口、到仓、库存/在途、消化目标、预算、损失、页面状态和人工时间综合决定，不使用固定天数阈值。阶段按验证、聚焦、放量、稳态/扩量组织；时间负责节奏，证据负责晋级，允许提前晋级或延长。

每阶段记录目标、证据、晋级/提前晋级、延长、加速、止损/回退条件以及时间/投入限制。点击和订单区间只是辅助参考；Expected Orders 只有在存在可靠 CVR 时才计算并标记 [推算指标]。

## 17. Keyword 与 Product Target 自动发现

Manual Keyword 和 Product Target ASIN 可从 Own Listing、H10/Cerebro、Niche、Amazon/SellerSpace 推荐、Own 历史 Search Term/转化词、Benchmark 和竞品资料自动发现；去重、清洗并核验相关性、意图、价格带、可替代性、Review/Rating 空间和切换理由。没有证据不得编造。Own ASIN、Benchmark ASIN、Product Target ASIN 三者必须独立，后两者不得用于 Own Product SellerSpace 身份查询。

## 18. 初始化预案与审批边界

正式方案前先展示《6-1 新品广告初始化预案》，包括目标、窗口、阶段路线、Campaign/Ad Group、COR/EXP/DIS/COM 角色、Keyword、Product Target、Auto、Bid/Budget/Bidding Strategy/Placement、Negative 原则、证据、假设和风险。Campaign 数量动态决定，不固定为五个。

审批只采用一次 A 批准、B 局部修改、C 重新制定、D 暂缓启动。战略预案审批与创建授权分开：完整创建清单展示前仅代表战略获批；用户针对完整清单回复“批准/A/批准创建/按这个执行”即授予本批新 Campaign 创建授权。批准后按 prepare_change_plan → 比对 → apply_change_plan 执行，Material Difference 必须重新确认；旧广告、Listing、Price、Coupon 不在授权内。

## 19. 目标反推与冲突

当用户给出库存、窗口、预算或损失目标时，按窗口 → 库存目标 → 日销量 → 可靠自然订单贡献 → 广告订单 → CVR/点击 → CPC/建议 Bid → 投入的顺序反推。缺失变量标记 [数据不足] 或 [待验证]；目标与资源、时间、流量、CPC、CVR、预算、页面或经济边界冲突时明确输出 [目标与当前资源/时间窗口存在冲突]，不伪造可行性。
## Portfolio 继承

所有新 Campaign/Ad Group/Advertised Product/Keyword/Target 默认继承当前已验证的 Portfolio。6-1 不创建 Portfolio、不迁移旧 Campaign；只在已有 Portfolio 通过 `PORTFOLIO_VERIFIED` 时提出新建广告。Portfolio ID 由共享身份规则的 SellerSpace 只读解析提供，缺失能力时安全降级为建议，不宣称可执行。
