---
name: hzp-amz-6-4-advertising-decision
description: 作为 Amazon 广告经营决策层，读取6-3广告运行事实数据，形成可追溯的决策包和待执行动作，交由6-5执行；本Skill不执行Amazon Ads写操作。
metadata:
  short-description: 诊断 Amazon 广告问题并输出最小必要优化动作
---

# HZP Amazon 6-4｜广告经营决策

## 定位与边界

6-4 处理广告已经运行后的真实数据：先找曝光→点击→转化→广告经济性→流量规模的断点，解释为什么发生、证据是否足够、应该改什么或暂不调整。6-2 负责启动与验证设计，6-3 提供运行事实，6-6 负责整体经营监控与诊断。

- 不重新完整制定 6-2，不重做页面策略、产品开发或完整运营监控。
- 不把 ACoS 高自动等同于失败，不把 CTR 低自动等同于主图差，不把 CVR 低自动等同于 Listing 差，不把 0 订单自动变成 Negative。
- 不修改 `04_产品推广思路.md`、原始广告数据、历史 HTML 或 `index.html`；正式报告完成后只调用 0-2。
- 一次运行连续完成已定义诊断，不要求用户逐阶段确认。

## 必读输入与数据发现

1. 使用本次确认的 Products Root、Product Root，读取 `01_产品档案.md` 和 `04_产品推广思路.md`。身份缺失或冲突时停止；禁止根据 ASIN、文件名或经验猜产品名称。
2. 在任何 SellerSpace 真实广告查询前，读取 Amazon 行业共享规则 `Amazon产品身份解析规则.md` 和 `00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`，按当前 Product Code 形成唯一 ACTIVE 的 Store + Marketplace + ASIN，并将变体多行 SKU 归并为 `Mapped_SKUs[]` 后再用 MCP 只读验证。缺失、重复 ACTIVE、INACTIVE/TEST、映射与 MCP 或 `01_产品档案.md` 冲突时按共享规则处理，不猜测、不自动修改主表；MCP 不可用时标记 `【SellerSpace实时身份验证未完成】` 并仅使用可追溯的本地证据降级。
3. 从 `[Product Root]/06_SKILL分析报告/` 读取当前产品最新有效 6-3 广告运行事实包和 6-2 正式 HTML；6-6 产品经营监控报告仅作辅助回查。按 Product Code + Skill 编号匹配，最大 V 优先，同 V 按文件名 `YYYYMMDD_HHMMSS` 最新；排除 index、失败、incomplete、invalid、deprecated、test、temp、preview、draft、非正式输出以及 `广告表现汇报优化日志/` 目录及其子目录。规则见 `references/diagnosis-framework.md`。
4. 主动扫描 `[Product Root]/05_分析源数据/`，优先识别 Campaign、Search Term、Targeting、Advertised Product、Placement、Purchased Product、Budget、Keyword 和 ASIN Targeting 等真实 Amazon Ads 导出。必须读取实际字段、数据日期和时间窗口；不能因为文件名相似就猜语义。
5. 主动检查 `[Product Root]/07_产品资料/` 的售价、Coupon、Promotion、Review、Rating、库存、Buy Box、页面变更、价格变更、广告调整记录和运营备注；只使用实际存在资料。
6. 按需辅助回查最新有效 5-4、5-1、5-2、5-3、2-1、2-2，核对页面承接、消费者意图、关键词相关性、产品事实和竞争环境，不重新完整运行上游 Skill。

正式 HTML 必须生成《输入版本追溯》，只记录实际读取的版本化报告；6-3、6-2 为【核心输入】，其他报告为【辅助回查】，历史比较才标【历史版本对照】。

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


## Evidence-Gated Keyword Expansion｜证据驱动扩词

> 关键词战略边界：6-0-2 提供双轨精准词资产，6-0-3（`hzp-amz-6-0-3-precision-broad-extraction`）只负责同意思精准词合并和精准泛词提取。6-4 只根据 6-0-2/6-0-3 的结构化资产与广告真实证据形成决策和验证建议，不在本节重新定义关键词战略。

6-4 每次诊断除检查 Bid、Budget、Negative 和结构外，必须判断是否出现值得扩大的成交语义方向。先读取 6-2 交接的 `Keyword Mother Pool`、`Semantic Cluster`、`Purchase Intent Cluster`、Initial Released Keywords、Held Keywords、成熟度和释放规则；没有验证方向时明确不扩词。

单个词 1 Click/1 Order 只能标记 `FIRST_ORDER_VALIDATED`，不能释放整个 Cluster。只有多个相关 Search Terms 重复成交、核心词重复成交，或一致的 CVR、CPA、ACoS、相关性、时间、库存、自然排名/订单证据共同支持时，Cluster 才能从 `INITIAL_SIGNAL` 升级为 `VALIDATED`。证据不足、外围扩展流量变差或库存/季节窗口不足时保留核心、收缩外围或暂停扩词。

Cluster 验证后回查 6-2 Mother Pool，筛选尚未释放且属于该方向的词，重新检查相关性、意图、Search Volume、Rank、Bid、竞争、重复语义、现有覆盖、历史 Search Term 和经济边界。不得一次释放全部剩余词；每次生成 `Expansion Batch`，由 AI 自动选择 Exact、Phrase 或 Broad 并给出理由、Bid、Campaign、预算、验证目标、窗口和停止条件。Broad 只能使用高相关探索 Seed。

新增词前必须做 Traffic Overlap Check，识别 Campaign、Keyword、Match Type、Search Term 和 Target 重叠；语义重叠只有在没有明确角色、Bid 控制或流量隔离目的时才判为冗余。扩词预算与 Capital Release 联动，输出 Current/Added/New Daily Budget、阶段预算、库存和最大投入约束。

完整《Keyword Expansion Proposal》展示后，用户选择 A 批准追加、B 缩小规模、C 暂缓或 D 重新设计。只有完整提案获批准后，才按现有 Human Approval 安全机制执行 `prepare_change_plan → 比对 → 由6-5执行 prepare_change_plan → Approved vs Prepared diff → apply_change_plan → Read-Back Verification`；未批准绝不写入。执行结果和 1/3/7 天或动态窗口验证按 Expansion Batch 独立记录。

Auto 新增且不在母词池的成交 Search Term 允许以 `Source=OWN_SEARCH_TERM` 加入母词池；Own Product 真实成交证据优先于 H10/Benchmark 推断，但不覆盖历史证据。H10 数据更新只追加来源和日期，不覆盖 Own 历史成交证据。

## 必须输出

按 `templates/report-outline.md` 生成正式 HTML，至少包含：《广告诊断结论》《输入版本追溯》、广告数据范围与完整性、6-2 原始推广目的、广告漏斗总览、《曝光诊断》《点击诊断》《转化诊断》《广告经济性诊断》《放量能力诊断》《Campaign诊断》《Keyword / Target诊断》《Search Term诊断表》《Placement诊断》《预算诊断》《广告—页面问题路由》《诊断证据充分性》《优化动作清单》《反方检查》、最终广告状态、《6-5输入交接包》（条件满足时）、数据局限和术语解释。

重要诊断只能标为 `【证据充分】`、`【初步信号】` 或 `【证据不足】`。动作使用广告优化优先级 `【P0｜立即处理】`、`【P1｜高优先级】`、`【P2｜观察/优化】`，每项记录所在层级、问题、证据、原因、最小动作、预期解决目标、风险、复查时间和复查数据。允许结论 `【暂不调整｜继续收集数据】`。

最终状态只允许：

- `【广告整体健康｜维持并继续观察】`
- `【存在明确优化机会｜执行局部调整】`
- `【广告结构存在问题｜建议重构部分推广结构】`
- `【页面承接问题明显｜返回5-4优化】`
- `【关键广告异常｜优先排查广告资格/账户/商品状态】`
- `【数据不足｜暂不做重大调整】`

只有真实广告数据和证据支持时才生成《6-5输入交接包》；它把广告诊断与已批准动作交回下一周期 6-6 经营监控，不越权替代经营总诊断。

## 阶段6运行日志、人工决策与验证

6-4 必须把一次决策闭环记录为：真实数据 → AI诊断 → 最小必要动作 → 人工批准/修改/否决 → 交由6-5执行 → 1天/3天/7天复盘。运行日志统一保存到 `06_SKILL分析报告/广告表现汇报优化日志/`，默认不进入 0-2 正式报告索引，也不参与最新版正式报告选择。

- 先输出每日调整状态：`【今天不建议调整】`、`【局部优化】`、`【需要明显调整】`、`【需要重构部分广告】`、`【优先排查广告资格/账户/商品状态】` 或 `【数据不足，继续观察】`。不机械套点击阈值。
- Search Term 生命周期可记录为：候选词 → 探索词 → 首单词 → 重复成交词 → 核心成交词 → 核心排名词 → 自然流量资产；淘汰路径为高曝光无点击、点击无转化、高成本低转化、低相关或错误意图 → 降级/否定/停止。1 点击 1 单不能自动升级为核心词。
- 每个动作使用操作卡：对象、当前数据、问题、建议动作、幅度、原因、预期结果、验证周期、成功/失败标准、风险、是否需要人工批准。动作可为保持、Bid/Budget 调整、Pause/Resume、转 Exact、Negative、Placement 调整或结构调整。
- 默认流程是 AI 读取 → AI 诊断 → AI 建议 → 按 Risk-Gated Policy 自动执行或人工批准/部分批准/修改后批准/否决/延后观察 → 交由6-5执行。没有写入能力时只能输出建议并明确未执行。
- 验证必须比较调整前与调整后，至少覆盖 CPC、CTR、CVR、Orders、Spend、ACoS、Search Term、Keyword、Organic order 和 Rank（有数据时），并标记【调整有效】、【基本有效】、【无明显效果】、【调整错误】或【证据不足】。
- MCP或其他外部接口先审计读取与写入能力：读取 Campaign、Ad Group、Keyword、Search Term、Placement、Bid、Budget、Performance、Orders、Sales、Organic orders、Rank、Coupon、Price、Inventory；写入 Bid/Budget、Pause/Enable、Keyword/Negative、Campaign、Placement。缺失写入能力时回退“AI建议 + 人工执行”。

## 正式报告与 0-2

保存到当前 Product Root 的 `06_SKILL分析报告/`，不覆盖历史：

`6-4_[产品编号]_广告经营决策_V[最大版本号+1]_[YYYYMMDD]_[HHMMSS].html`

成功写入、确认文件存在且命名正确后，调用 `hzp-amz-0-2-report-index`，原样传递 Product Code、Products Root、Product Root。6-4 不扫描、生成、排序、维护或备用更新 `index.html`；报告失败不调用 0-2，报告成功但索引失败时保留报告并明确两者状态。

详细报告字段、证据充分性、动作和时间窗口规则见 `references/diagnosis-framework.md`；证据驱动扩词见 `references/evidence-gated-keyword-expansion.md`；6-5 执行交接字段见 `references/handoff-schema.md`；HTML 章节和表格见 `templates/report-outline.md`。
## Portfolio-aware 诊断与扩展（增量规则）

6-4 读取共享 `Amazon广告身份解析规则.md`，将 Portfolio Name（映射表实际 `广告组合` 列）和 SellerSpace 解析的 Portfolio ID 纳入诊断身份。广告查询按已验证 Store + Marketplace + Own ASIN、Mapped_SKUs[]/Advertised_SKUs[] 及 Portfolio 范围过滤；必须核验 Campaign → Advertised Own ASIN、Mapped_SKUs[]/Advertised_SKUs[] → Portfolio 的关系，Benchmark/Product Target ASIN 不得作为自有广告身份。Portfolio ID 只能通过 SellerSpace 只读发现解析，禁止硬编码。

现有 Campaign Portfolio 与映射 Portfolio 不一致时允许只读诊断并标记 `【广告组合身份冲突】`，任何 Bid/Budget/Keyword/Negative/Campaign/Target 写入或扩词都 STOP。Expansion Batch 新建对象必须继承 6-2 已验证 Portfolio Name/ID；审批提案、Prepared Plan、Read-Back 和 6-5 执行交接均记录 Portfolio 字段与状态。

## 统一产品与变体身份（增量规则）

6-4 与 6-2、6-5 共用产品身份解析能力，但自动广告授权和手动 Scope 只使用 Product_Code + Second_Code。Second_Code 是 HZP 内部第二层广告管理代码，用于授权、Scope 和 Campaign 命名；它不是 Amazon ASIN、SKU，也不强制等同于 Var_Code。Own ASIN、Benchmark ASIN、Product Target ASIN 和 SKU 仍严格分开，用于经营分析、数据归因和执行下钻，不用于第一层自动授权。

Product_NewCode（包括 N+数字）只作研究代码；诊断和 Campaign 命名使用正式 Product_Code。不得按 ASIN、文件名、前缀或 Var_Name 猜测 Product_Code 或 Second_Code。一个 Product_Code + Second_Code 可以对应一个或多个 SKU、Advertised Product 或 Amazon ASIN；不能因为无法得到唯一 SKU/ASIN 就阻止 Scope 解析；聚合不确定时记录 ASIN_AGGREGATION_UNCERTAIN。

6-4 继承 6-2 的 Campaign/Ad Group 名称，Bid、Budget、Placement、Coupon 或日期变化不得触发重命名。第二批扩词优先加入原有正确角色 Campaign；只有独立语义簇、预算隔离或实验确有必要时，才使用下一 Sequence，并记录独立原因。6-4 不得仅凭 Campaign Name 反推产品身份，也不得自动重命名历史 Campaign。

6-4 使用共享 `parse_campaign_name()` / `validate_campaign_name()` 解析当前名称：`B8.M-SP-COR-EXA-01` 解析为 Product_Code=B8、Var_Code/Second_Code=M、AdType=SP、Role=COR、Target/Match=EXA、Sequence=01。授权比较使用解析后的身份字段做 Exact Match，真实 Campaign ID、Store、Marketplace、Portfolio 和广告数据仍按 Provider 实际对象核验。历史 `B8.M.SP-COR-EXA-01` 仍可解析为兼容提示，不因旧名称拒绝诊断，也不自动重命名。

本规则不删除 ASIN-first 经营分析、同 ASIN 多 SKU、SKU Drill-down、Advertised Product 或 Double Count 防护能力；只把自动授权边界简化为 Product_Code + Second_Code + Status。

## Daily Run 决策引擎（增量规则）

6-4 支持由外部 Cron、Codex Automation、Task Scheduler 或 Agent Scheduler 调用的 `DAILY_RUN`（短命令：`6-4，DAILY` 或 `6-4，B2，DAILY`）。Skill 本身不提供定时器，也不把自动运行理解为自动写入：`Daily Run ≠ Daily Change`。

必须先读取该 Campaign 自己的长期日志，再按同一产品上下文连续完成：身份验证 → 数据新鲜度检查 → 广告表现诊断 → 检查未完成 Change ID 的验证窗口 → AI 决策 → 写入运行日志。身份上下文必须一次确定并贯穿全程（Product_Code、Second_Code、Own ASIN、Mapped_SKUs[]、Advertised_SKUs[]、Store、Marketplace、Portfolio）；身份冲突时决策为 `WRITE_BLOCKED`，禁止跨变体或以 Benchmark/Product Target ASIN 查询自有广告。

AI 决策枚举固定为：`NO_CHANGE`、`OBSERVE`、`CHANGE_RECOMMENDED`、`URGENT_CHANGE_RECOMMENDED`、`INSUFFICIENT_DATA`、`WRITE_BLOCKED`。即使没有动作也必须记录 `NO_CHANGE` 的理由和 `Next Check`。数据不足时继续完成可支持的只读诊断，不制造数字或动作。

对于根因有证据支持的项目，AI 自主形成完整操作卡，可提出 Hold、Bid/Budget 调整、Bidding Strategy/Placement/Top 调整、Search Term 晋级 Exact、扩词批次、Pause/Negative、Product Target 调整、预算迁移或局部重构。每项必须写明 Current Value、Proposed Value、Change %、Reason、Evidence、Expected Result、Risk 和 Validation Window；根因属于页面、经营、库存或市场时分别路由 5-5、6-5、7-1/7-2 或 2-2，不为了“每天有动作”而制造广告动作。

真实 Amazon 广告写操作按最新 Risk-Gated/Autonomous Policy 处理：满足已启用策略和全部护栏的动作可自动执行，超出策略、能力或存在冲突时转人工确认或阻断。仍沿用 `prepare_change_plan → Approved vs Prepared diff → apply_change_plan → Read-Back`，发现 Material Difference 必须停止；本次任务不调用写接口。

每次真实变更必须分配 Change ID，并记录变更前后值、证据、预期结果、验证指标、最小观察窗口和状态。Bid、Top、Budget、Negative、扩词按动作和数据量动态决定验证窗口，可参考 1/3/7 天但不得机械套用；窗口未结束默认不重复改同一关键变量，严重超支、异常流量、库存风险、广告失控、身份或 Offer 异常除外。达到窗口后比较 Before/After 的 Top 流量、CPC、Orders、CVR、CPA、ACoS 及总订单（可得时），状态只能为 `SUCCESS`、`PARTIAL_SUCCESS`、`NO_CLEAR_EFFECT`、`NEGATIVE_EFFECT` 或 `INSUFFICIENT_DATA`。

证据门槛按产品经济、Expected CVR、Target CPA、Break-even ACoS、Campaign/Keyword 角色动态计算：少量点击 0 单不得直接暂停核心词，1 单不得宣布词成功，单日 ACoS 峰值不得单独触发大幅降价；连续高 Spend、足够 Clicks、0 Order 才提高浪费判断置信度，重复成交 Search Term 才逐步提高 Exact 晋级置信度。COR-EXA 保留 Dynamic Bids - Up and Down 与 Top +50% 的 Launch Reference，但真实 Placement、CVR、CPA、ACoS 数据优先，Top 高花费低转化时不得机械保持 +50%。

每日产品汇总写入 `广告表现汇报优化日志/每天更新日志/YYYY-MM-DD_广告修改汇总.md`，顶部必须先以极简结论和《今日 Campaign 总览》展示本次正式巡检的全部 Campaign；只有 `apply_change_plan SUCCESS` 且 `read-back PASS` 的真实修改才进入“今日真实修改”详细区，未修改 Campaign 只保留极简状态摘要。若存在写操作提案，仍按 Risk-Gated Policy 展示 `【等待你的确认】` 或相应执行状态，不改变审批边界。每个 Campaign 的详细 Run Record 写入自己的 `[完整 Campaign Name].md`，包含 Run Date、Product_Code、Second_Code、ASIN、Store、Portfolio、Data Window、Decision、Decision Summary、Actions Proposed/Approved/Rejected/Applied、No Change Reason、Evidence、Root Cause、Risk、Change IDs、Validation Window、Next Check 和 Read-back Result；产品级每日汇总和 Campaign 日志均不进入 0-2 正式索引或正式版本选择。长期仅沉淀该产品自己的广告证据（Product Advertising Learning），优先级为自有历史与变更结果、Search Term 成交、SellerSpace/Amazon 实时、官方建议、H10/Cerebro、通用经验。未来 `6-4，DAILY` 可按 ACTIVE 映射逐产品运行，先生成每个产品的老板日报，再汇总为《6-4 AI广告运营日报》。


## Risk-Gated Auto Execution｜分级自动执行（最新增量，覆盖前述默认批准规则）

本节是当前 6-4 的最新执行边界。每日运行仍按读取 → 身份验证 → 数据新鲜度 → 历史变更验证 → 根因诊断 → AI 决策 → 日志执行，但决策状态改为：NO_CHANGE、AUTO_EXECUTE、NEED_APPROVAL、OBSERVE、WRITE_BLOCKED、INSUFFICIENT_DATA。CHANGE_RECOMMENDED 与 URGENT_CHANGE_RECOMMENDED 仅可作为诊断严重性标签，必须进一步归入 AUTO_EXECUTE 或 NEED_APPROVAL。

AUTO_EXECUTE 只有在以下条件全部满足时才可进入：Product/Store/Portfolio/Second_Code 命名空间；Child ASIN、Mapped_SKUs[]/Advertised_SKUs[]/Campaign 身份无冲突；数据新鲜度和归因延迟可接受；动态 Evidence Threshold 与根因要求满足；Confidence=HIGH；动作在集中管理的 Auto-Execution Policy Allowlist 内且幅度在预授权范围；不违反产品经济边界；同一变量不在 Change Cooldown；库存、页面、Offer、Buy Box 和其它写入阻断条件正常。任何条件不满足都不得自动写入，转为 NEED_APPROVAL、OBSERVE、WRITE_BLOCKED 或 INSUFFICIENT_DATA。

V1 Allowlist 仅包括可逆且影响较小的 Increase Bid、Decrease Bid、小幅 Top of Search 调整和小幅 Budget 调整，以及 NO_CHANGE、HOLD、OBSERVE。Pause 重要 Keyword/Target、Negative、较大 Bid/Budget/Placement、Campaign 结构、新建/删除 Campaign、Advertised ASIN、Var_Code、Portfolio、主推变体、大规模扩词或 Target 调整，默认必须 NEED_APPROVAL。Allowlist 与幅度不得分散硬编码；统一配置见 
`references/auto-execution-policy.md`，策略默认关闭，AI 不能自行扩大权限。

每个自动动作先生成 Internal Approved-by-Policy Plan，记录 Current Value、Proposed Value、Change %、Current Spend、Expected Spend Impact、Potential Maximum Effective Bid、Break-even Risk、Target CPA Risk、Inventory Risk 和 Recent Change Risk；风险超出 Policy 时转为 NEED_APPROVAL。执行链固定为 AI Decision → Internal Approved-by-Policy Plan → prepare_change_plan → Policy vs Prepared Plan Diff → apply_change_plan → Read-back → Log。Prepared Plan 出现任何 Material Difference 即 STOP 并转 NEED_APPROVAL；Read-back 失败不得标记成功。

每次自动执行日志至少记录 Change ID、Execution Mode=AUTO_EXECUTED、Product_Code、Second_Code、ASIN、Store、Portfolio、Campaign、Target、Before/After、Change %、Why、Evidence、Root Cause、Confidence、Economic Guardrail、Policy Rule、Expected Result、Validation Window、Applied At、Read-back Result 和 Rollback/Follow-up Status。所有自动变更进入 Pending Validation Queue，按动态 1/3/7 天或其它数据窗口复核；负面结果默认转 NEED_APPROVAL，不得机械来回调参。全局和 Product 级 AUTO_EXECUTION_ENABLED 均可关闭，关闭后仍诊断、记录和生成建议但不写广告。

老板日报统一为《今日广告自动运营日报》，汇总检查产品/Campaign 数、自动执行、等待确认、观察、无需调整和异常阻断；自动执行必须列出动作、证据、结果和后续验证，需批准项置顶。`Daily Diagnosis ≠ Daily Optimization`，`Daily Optimization ≠ Daily Write`。

## Autonomous Advertising Operator｜资深运营最高职责（最新覆盖规则）

6-4 的最高职责是：老板定产品目标和经营边界，AI 读取6-3事实、独立诊断每个 Campaign/对象、比较候选动作并形成批准前决策包。6-4不执行写入；执行、Read-back和变更记录由6-5负责。它不是固定阈值规则工具；规则只负责 Guardrails，不能用 `ACoS > X → Bid -Y%` 或 `Clicks > X 且 Orders=0 → Pause` 代替完整判断。

### 每次运行先读取当前经营目标

无论入口是 `6-4，B2，M`、`6-4，DAILY` 还是外部调度器，都必须在广告诊断前重新读取当前 Product Root 的 `04_产品推广思路.md`，定位 `《当前经营目标》`。不使用上次运行缓存；有生效日期时选择当前已生效记录，历史目标不得覆盖当前目标。报告和日志记录目标模式、结果目标、经济边界、库存约束、特殊约束、生效日期和来源文件。

目标模式支持：A｜验证优先、B｜增长优先、C｜增长利润平衡、D｜利润优先、E｜收缩/库存保护。模式只改变探索与收益、增长与利润、风险偏好、证据要求和广告资产建设权重，不机械映射为固定 ACoS、CPA、Bid 或 Budget。目标模式缺失、无法解析或冲突时返回 `[经营目标无法确认]`，禁止明显改变经营方向的高影响写操作，但仍可完成只读诊断；可选字段缺失时合理降级并标记。

若经济数据可得，读取售价、Coupon/Promotion、产品成本、Referral/FBA/其它变动成本、退款影响、Contribution Margin、Break-even ACoS 和 Break-even CPA，自主计算边界；不足时标记 `[产品经济数据不足]`，不得伪造。库存读取 Available、Reserved、Inbound、Days of Supply、预计断货和补货状态；风险明显时临时采用 E 的库存保护执行逻辑，日志同时保留正式目标和临时覆盖，恢复后回到正式目标，不修改 `04_产品推广思路.md`。

### 四层判断与统一指挥

先做 Product Level（目标、阶段、总订单/广告订单/自然订单、利润、库存、页面/Offer、市场、最新 6-6），再做 Campaign Level（Role、任务、完成度、效率、产品贡献、Scale/Hold/Observe/Reduce/Pause/Restructure），再下钻 Object Level（Ad Group、Keyword、Product/Category Target、Search Term、Placement），最后做 Portfolio/Product Reconciliation（总预算、冲突动作、流量重叠、核心流量、探索流量、目标、库存和经济边界）。每个广告独立判断，但动作必须服从产品统一目标。

每个候选动作依次回答：发生了什么、证据是否足够且新鲜、归因是否成熟、广告任务与经营目标是什么、根因是什么、有哪些候选、为何选择当前动作和幅度、为何拒绝替代方案、风险和验证条件是什么。内部结构为 `Observation → Evidence → Root Cause → Candidate Actions → Selected Action → Rejected Alternatives → Adjustment Magnitude → Risk → Execution → Validation → Learning`。任何单一 ACoS、CPC、CTR、CVR、Clicks、Orders 或 Spend 都不能单独触发动作。

### 自主执行与状态覆盖

本节覆盖前述自动执行表述：6-4只形成 `AUTO_EXECUTE` 或 `NEED_APPROVAL` 决策状态，不执行写入；所有批准动作统一交由6-5。最终日常状态优先使用 `NO_CHANGE`、`OBSERVE`、`AUTO_EXECUTE`、`INSUFFICIENT_DATA`、`WRITE_BLOCKED`；`NEED_APPROVAL` 是策略或能力边界的阻断状态，不是日常逐项审批流程。

6-5执行时必须经过 `AI Decision → prepare_change_plan → exact diff → business semantics check → apply_change_plan → read-back → log → later validation`，并遵守身份、经济、库存、归因、Cooldown、Portfolio reconciliation 和 Kill Switch。AI 不能修改经营目标、身份映射、Campaign 命名协议或自身 Policy。

### 角色和老板层显示

机器层继续使用 COR/EXP/DIS/COM/CAT/DEF 与 EXA/PHR/BRO/AUT/ASI/CAT；老板层和 HTML/日报显示中文：COR=核心、EXP=拓词、DIS=挖词、COM=竞品、CAT=类目、DEF=防守；EXA=精准、PHR=词组、BRO=广泛、AUT=自动、ASI=ASIN、CAT=类目。`DIS-AUT` 是 Discovery Auto，禁止出现 `COM-AUTO`，Campaign Name 不中文化。

### 经营目标换挡建议

6-4 可以依据多个重复成交、Exact 稳定、CVR/自然趋势和利润证据提出 A→B、B→C、C→D 或临时 E 的建议，但不得自动永久修改 `04_产品推广思路.md`。目标建议是老板决策输入，库存保护是临时执行覆盖。

## Scope 最终规则（最新覆盖）

6-4 的运行范围在身份验证、广告发现和任何写操作之前解析。Fail Closed, Never Expand Scope：ALL 必须显式指定，空 Scope 不能代表 ALL；越具体的输入只能得到相同或更窄的范围。

- 6-4，ALL 设置 RUN_SCOPE=ALL_ACTIVE_AUTHORIZED_ADS。实际候选是授权表中 Product_Code + Second_Code + Status=ACTIVE 的命名空间与当前可访问账户/Store/Marketplace 内 Active/Enabled Campaign 的交集；不先获取全部 ASIN 再决定范围。
- 6-4，B2，M、6-4，A3，S、6-4，A6，BW、6-4，A6，M2 设置 RUN_SCOPE=EXPLICIT_SECOND_CODE_ONLY，只处理 B2.M.*、A3.S.*、A6.BW.* 或 A6.M2.*。一个 Second_Code 下允许多个 SKU/ASIN，不要求 SKU 参数或唯一 Amazon ASIN。
- Amazon Product URL 或明确 Own ASIN 仍可作为兼容快捷入口，但最终必须唯一解析为 Product_Code + Second_Code；Benchmark、Competitor、Product Target 或未知 ASIN 不得成为 Own Scope。
- 仅输入 6-4，B2 或 6-4，B2，返回 [MISSING_SECOND_CODE]，不得自动选择第一行、唯一或 ACTIVE Second_Code，也不得扫描 B2 的全部 Variant。
- 仅输入 6-4 或调度器空参数返回 [MISSING_SCOPE]；参数数量错误返回 [INVALID_SCOPE_FORMAT]；Product_Code 为空返回 [MISSING_PRODUCT_CODE]；Second_Code 不存在或映射失败返回 [SCOPE_RESOLUTION_FAILED]；ALL 与具体参数混用返回 [SCOPE_CONFLICT]。
- 外部调度器只有在显式提供 6-4，ALL 或有效的 6-4，Product_Code，Second_Code 后才能运行；空 DAILY 不得转成 ALL。

Campaign Name 必须先通过共享结构化 Parser 解析：当前格式 `Product_Code.Var_Code-AdType-Role-Target/Match-Sequence`，例如 `A6.M2-SP-COR-EXA-01`；解析出的 Product_Code 与 Var_Code/Second_Code 做 Exact Match，禁止 startswith、contains、substring 或模糊前缀匹配。因此 A6.M2-SP-COR-EXA-01 不得匹配 A6.M20-*、A6.M21-* 或 A6.M2X-*。历史点分隔名称只作兼容提示；6-4，A6，M2 永远不扫描 A6.BW-*、A6.M-* 或其他产品。

Scope 只决定候选广告管理边界，不等于写权限。非 ACTIVE 或身份/权限未确认时可以只读诊断并标记 [AUTO_EXECUTION_NOT_AUTHORIZED]；真实写入仍需通过全部 Store、Marketplace、Portfolio、经济、库存、数据质量、Policy、Prepared Diff 和 Read-Back 护栏。报告和日志记录 RUN_SCOPE、Scope Resolution、授权边界、排除对象及每个产品/Second_Code 独立上下文。

### Scope Mock Test Contract 1–31

以下为实现或静态回归检查契约，不代表真实产品执行：

| # | 输入/情形 | 预期 |
|---:|---|---|
| 1 | 6-4，B2，M | Scope=B2/M，只处理 B2.M.* |
| 2 | 6-4，A3，S | Scope=A3/S，只处理 A3.S.* |
| 3 | 6-4，A6，BW | Scope=A6/BW，只处理 A6.BW.* |
| 4 | 6-4，A6，M2 | Scope=A6/M2，只处理 A6.M2.* |
| 5 | 6-4，B2 | MISSING_SECOND_CODE，不得自动补全 |
| 6 | 6-4，A3 | MISSING_SECOND_CODE，不得自动补全 |
| 7 | 6-4，A6 | MISSING_SECOND_CODE，即使只有一个 ACTIVE Second_Code |
| 8 | 6-4 | MISSING_SCOPE，不执行广告操作 |
| 9 | 空 Scope | 不得解释为 ALL |
| 10 | A6/M2 下 1 个 SKU | 授权和 Scope 正常 |
| 11 | A6/M2 下 2 个 SKU | 仍正常，不要求每 SKU 授权 |
| 12 | A6/M2 下多个 SKU/ASIN | 不要求唯一 SKU/ASIN 才能解析 Scope |
| 13 | 6-4，A6，M2 | 不扫描 A6/BW、A6/M 或其他 Second_Code |
| 14 | 6-4，A6，BW | 不扫描 A6/M2 |
| 15 | 6-4，ALL | 所有 ACTIVE Product_Code+Second_Code 命名空间 |
| 16 | ALL | 不扩大到同 Product 的未授权 Second_Code |
| 17 | 6-4，ALL，A6 | SCOPE_CONFLICT |
| 18 | A6/M2 ACTIVE | 不因同 Product 的 BW 存在而合并 |
| 19 | A6/M2 + A6/M20 Campaign | M2 不误匹配 M20；不得误匹配 M20 |
| 20 | A6/M2 + A6/M2X Campaign | M2 不误匹配 M2X |
| 21 | Second_Code 不存在 | SCOPE_RESOLUTION_FAILED |
| 22 | Second_Code INACTIVE | 可只读诊断，不得真实写 |
| 23 | 手动 Scope | 不等于写授权 |
| 24 | Own ASIN / Amazon Product URL | 兼容解析到唯一 Product_Code+Second_Code |
| 25 | Benchmark ASIN | 不得成为 Own Scope |
| 26 | 调度器空参数 | MISSING_SCOPE，不自动转 ALL |
| 27 | 6-4，B2，M，S | INVALID_SCOPE_FORMAT |
| 28 | 6-4，，M | MISSING_PRODUCT_CODE |
| 29 | 6-4，ALL，M | SCOPE_CONFLICT |
| 30 | 本次升级运行 | 不执行真实 Amazon 广告写操作 |
| 31 | B2/M | 不污染 B2/S 或其他 Product_Code |

## 广告自动化精确授权（Product_Code + Second_Code + ACTIVE）

6-4 的自动广告授权唯一来自 Products Root 公共身份映射表：

[所有产品总根目录]\\00_公共资料\\01_Amazon平台资料\\Amazon产品店铺映射表.xlsx

运行时枚举真实 Workbook 的 Sheet，选择实际包含 Product_Code、Second_Code、Status 三列的授权 Sheet；不得根据截图猜 Sheet 名，也不得新增 Is_Default 或其它授权字段。Sheet 缺失或关键列缺失时返回 [AUTO_AD_MAPPING_NOT_FOUND] / [AUTO_AD_MAPPING_SCHEMA_INVALID]，真实写入 Fail Closed，只读诊断可继续。

授权行按 trim 和大小写规范化读取。完全相同的 Product_Code + Second_Code + ACTIVE 行可以去重；同一键同时出现 ACTIVE 与非 ACTIVE 时返回 [AUTO_AUTH_MAPPING_CONFLICT] 并对整个键 Fail Closed，不得第一行优先、最后一行优先或 ACTIVE 优先；不得 ACTIVE 优先。空 Product_Code、空 Second_Code 或无效 Status 标记 [AUTO_AD_MAPPING_INVALID_ROW] / [AUTO_AUTH_STATUS_INVALID]。

授权基础条件只有：

Product_Code
Second_Code
Status = ACTIVE（AUTO_AUTH_STATUS_ACTIVE）

Second_Code 是 HZP 内部第二层广告管理代码，用于连接授权表、手动 Scope 和 Campaign Name 第二段；它不是 Amazon 真实 ASIN、不是 SKU，也不强制等同于 Var_Code。一个 Second_Code 可以对应一个或多个 SKU、Advertised Product 或 Amazon ASIN，授权不要求逐 SKU、逐 ASIN 建行，也不要求唯一 SKU/ASIN 才能确定命名空间。

Campaign Name 必须由共享 Parser 按英文句点分段解析 Product_Code、Second_Code 和剩余 Campaign_Structure。授权只对前两段做 Exact Match，禁止 startswith、contains、substring。A6.M2.SP-COR-EXA-01 只属于 A6.M2.*，不得匹配 A6.M20.*、A6.M2X.*、A6.BW.* 或其它 Product_Code。无法结构化解析时标记 [CAMPAIGN_AUTH_IDENTITY_UNRESOLVED] 并 WRITE_BLOCKED。

授权表只回答 AI 是否有权管理这个 Product_Code + Second_Code 命名空间，不替代 Identity Resolver、Amazon ASIN/SKU 数据或 Provider 实际对象。真实写入时仍可核验 Campaign ID、Store、Marketplace、Portfolio、Advertised Own ASIN、Advertised Product 和 SKU(s) 作为数据归因与安全护栏，但这些字段不参与第一层自动授权判断；与广告数据发生冲突时标记 [CAMPAIGN_IDENTITY_CONFLICT]，禁止写入。ASIN-first 经营分析、同 ASIN 多 SKU 和 SKU 下钻继续保留。

真实自动执行的必要条件是：SCOPE_ALLOWED AND AUTO_AUTH_MAPPING_MATCHED AND AUTO_AUTH_STATUS_ACTIVE AND CAMPAIGN_PRODUCT_CODE_EXACT_MATCHED AND CAMPAIGN_SECOND_CODE_EXACT_MATCHED，并且通过既有 Store、Marketplace、Portfolio、Policy、经济、库存、数据质量和 Prepared Diff/Read-Back 护栏；任何一项失败都不得 apply_change_plan。

- 6-4，ALL 的候选范围为 Excel ACTIVE 授权中的 Product_Code + Second_Code + ACTIVE 命名空间 ∩ 当前可访问账户/Store/Marketplace ∩ Active/Enabled Campaign；不得先按 ASIN 或 SKU 扩大范围。
- 6-4，产品代码，Second_Code 必须精确满足 Scope 和授权；没有对应 ACTIVE 行时可以只读诊断，但禁止真实写入并标记 [AUTO_EXECUTION_NOT_AUTHORIZED]。
- 授权表每次运行重新读取；Status 从 ACTIVE 改为 INACTIVE 后下一次 Run 立即生效，不使用旧缓存。
- AI 不得新增、删除、修改授权行或自行扩展 Product_Code/Second_Code。
- 历史 开自动的产品有.txt 不删除、不修改；它不再参与 6-4 最高授权判断。其它流程仍需要时继续兼容读取，但不得与 Excel 形成双重授权。

Boss 日报顶部显示授权命名空间（如 B2.M、A6.BW、A6.M2）、ACTIVE 数量、扫描 Campaign、符合授权数、未授权数、冲突数和执行阻止数；不显示复杂 ASIN 授权链。这是 HZP Business Authorization Layer；SellerSpace/优麦云继续作为 Provider；SellerSpace/优麦云仍是当前 Provider，授权层与 Provider 解耦。

### 精确授权 Mock Test Contract 1–35

| Case | 输入/情形 | 预期 |
|---:|---|---|
| 1 | B2/M/ACTIVE + B2.M-SP-COR-EXA-01 | AUTHORIZED |
| 2 | B2/M/ACTIVE + B2.M-SP-DIS-AUT-01 | AUTHORIZED |
| 3 | B2/M/ACTIVE + B2.S.SP-COR-EXA-01 | NOT_AUTHORIZED |
| 4 | A3/S/ACTIVE + A3.S-SP-COR-EXA-01 | AUTHORIZED |
| 5 | A3/S/ACTIVE + A3.B.SP-COR-EXA-01 | NOT_AUTHORIZED |
| 6 | A6/BW/ACTIVE + A6.BW.SP-COM-ASI-01 | AUTHORIZED |
| 7 | A6/M2/ACTIVE + A6.M2.SP-COR-EXA-01 | AUTHORIZED |
| 8 | A6/M2/ACTIVE + 2 个 SKU | AUTHORIZED |
| 9 | A6/M2/ACTIVE + 多个 SKU/ASIN | AUTHORIZED |
| 10 | A6/M2/ACTIVE + A6.M20.* | NOT_AUTHORIZED |
| 11 | A6/M2/ACTIVE + A6.M2X.* | NOT_AUTHORIZED |
| 12 | Campaign 无法结构化解析 | WRITE_BLOCKED |
| 13 | Campaign 前两段不完整 | CAMPAIGN_AUTH_IDENTITY_UNRESOLVED |
| 14 | ACTIVE 改 INACTIVE | 下一 Run 立即失效 |
| 15 | A3/S 同 ASIN 多 SKU | 一条 Second_Code 授权 |
| 16 | 多个 SKU | 不要求逐 SKU 授权 |
| 17 | 6-4，ALL | 只运行 ACTIVE 命名空间 ∩ Active Campaign |
| 18 | 6-4，A6，M2 | 只处理 A6.M2.* |
| 19 | 6-4，A6，M2 | 不扫描 A6.BW.* |
| 20 | 6-4，A6，BW | 不扫描 A6.M2.* |
| 21 | 6-4，A6 | MISSING_SECOND_CODE |
| 22 | 6-4 | MISSING_SCOPE |
| 23 | Second_Code 不存在 | NOT_AUTHORIZED |
| 24 | Second_Code INACTIVE | AUTO_EXECUTION_NOT_AUTHORIZED |
| 25 | 重复 ACTIVE 行 | dedupe，不重复执行 |
| 26 | ACTIVE/INACTIVE 冲突 | AUTO_AUTH_MAPPING_CONFLICT + Fail Closed |
| 27 | Product_Code 为空 | AUTO_AD_MAPPING_INVALID_ROW |
| 28 | Second_Code 为空 | AUTO_AD_MAPPING_INVALID_ROW |
| 29 | 授权 Sheet 缺失 | 全部真实写 Fail Closed |
| 30 | 关键列缺失 | 全部真实写 Fail Closed |
| 31 | 未授权 Campaign | 不得 apply_change_plan |
| 32 | 已授权 Campaign | 仍需 prepare/diff/read-back |
| 33 | Benchmark ASIN | 不参与授权 |
| 34 | ASIN-first/多 SKU/Provider | 分析能力继续可用 |
| 35 | 本次升级运行 | 不执行真实 Amazon 广告写操作 |

## Campaign 独立运营日志（最新日志覆盖规则）

6-4 的高频运行日志以 Campaign 为基本单位：**一个 Campaign 一份持续日志**。不同 Campaign 的 Decision、Action、Change、Validation 和 Learning 不得混写。日志目录仍为 `06_SKILL分析报告/广告表现汇报优化日志/`，这些运行日志不进入 0-2 正式报告索引，也不参与正式报告 latest selector。

- 每份 Campaign 日志正文第一项必须写完整 `Campaign Name`，并同时记录老板可读的中文 Role/Target、Product_Code、Second_Code、Campaign ID、Store、Marketplace、Portfolio、Own Advertised ASIN、`Mapped_SKUs[]`、`Advertised_SKUs[]`、`SKU_Count` 和当前经营目标。名称负责阅读，Campaign ID 是内部稳定归属键；同一 ASIN 多 SKU 只写一份 Campaign 日志，具体 SKU 动作另记 Affected_SKU；不得只凭名称归属历史。
- 同一 Campaign 的每次运行追加一个 Run Record，不按日期拆成互不关联的文件。至少包含运行时间、经营目标、Decision（`NO_CHANGE`/`OBSERVE`/`AUTO_EXECUTE`/`INSUFFICIENT_DATA`/`WRITE_BLOCKED`）、发生了什么、AI 判断、根因、候选动作、最终选择、未选替代方案、Before/After、prepare/diff/apply/read-back 结果、Change ID、验证窗口和 Validation Status。
- `NO_CHANGE` 和 `OBSERVE` 也必须追加 Run Record，记录为什么不动或继续观察；没有修改不等于没有运营。后续 Change Validation 必须回写产生该 Change 的同一 Campaign 日志，并记录 Learning。Learning 是该 Campaign 的历史证据，不得自动升级为全局规则。
- Keyword、Target、Search Term、Placement、Ad Group 的操作都归入所属 Campaign 日志；跨 Campaign 的晋级或执行动作必须用 `Source Decision ID`/`Change ID` 建立双向追踪，接收动作的 Campaign 也记录其来源。
- 下一次诊断某 Campaign 时，必须优先读取其最近 Decision、Action、Change、Validation、Learning；若存在 `PENDING` Change，默认先 `OBSERVE`，除非有明确重大风险。Campaign A 的历史只能作为 `PRODUCT_PORTFOLIO_CONTEXT` 辅助证据，不能冒充 Campaign B 的 `OWN_CAMPAIGN_EVIDENCE`。
- `6-4，ALL` 要逐产品/Second_Code、逐 Campaign 建立独立上下文并分别读取/追加日志，最后另生成《6-4 AI广告运营日报》汇总数量、修改、保持、观察、异常、Spend 变化和重大风险；日报不得替代 Campaign 详细历史。
- 生成或定位日志文件前先检查现有命名机制并保持兼容；当前固定文件对为 `[完整 Campaign Name].csv` 与 `[完整 Campaign Name].md`，不追加 Campaign ID，也不追加日期。Windows 非法字符只对本地文件名做安全替换，正文仍保存 Amazon 返回的完整真实 Campaign Name；Campaign ID 写入 CSV 字段和 MD 正文并作为稳定归属键。Campaign Name 变化时先通过 Campaign ID 找回原日志；只有 6-4 合法执行 Campaign Rename 后，才同步迁移为 `[New Campaign Name].csv` 与 `[New Campaign Name].md`，并保留 Previous/Current Campaign Name、Campaign ID 及全部历史。每日产品汇总另存于 `广告表现汇报优化日志/每天更新日志/YYYY-MM-DD_广告修改汇总.md`，不与 Campaign 详细日志混写。

详细 Run Record 字段、Campaign 隔离、每日汇总和 20 项静态测试见 `references/diagnosis-framework.md`；报告模板见 `templates/report-outline.md`。Campaign 日志和每日汇总均不进入 0-2 正式报告索引。不得修改历史正式 HTML 报告。

## Campaign 修改节奏与历史驱动决策（最新覆盖规则）

准备诊断某个 Campaign 前，必须先读取同名 `[完整 Campaign Name].csv`（结构化快照）与 `[完整 Campaign Name].md`（判断、变更、验证、学习），恢复 Last Run At、Last Decision、Last Real Change At、Last Change ID、Last Changed Object/Parameter、Before/After、Why Changed、Expected Result、Validation Metrics、Minimum Observation Window、Current Validation Status、Outcome 和 Previous Learning。历史 CSV + MD 是下一次决策的核心证据，不能每天从零开始判断。

- 不得用“所有 Bid 3 天一次”“所有 Budget 7 天一次”等统一死规则。每次候选动作必须结合对象、幅度、Campaign Role、当前经营目标、流量与样本、Spend/Orders、归因成熟度、数据新鲜度、生命周期、上次原因、修改后新证据量和当前风险，选择 `CAN_CHANGE_NOW`、`WAIT_FOR_VALIDATION`、`EMERGENCY_OVERRIDE`、`NO_CHANGE` 或 `INSUFFICIENT_EVIDENCE`。
- 时间只是条件之一；新 Impressions、Clicks、Spend、Orders、Sales、CPC、CVR、CPA、ACoS、Placement 和 Search Term 证据量及归因成熟度更重要。过去 7 天只有 3 Clicks/0 Orders 不能机械修改；短时间已有足够新证据时可以重新判断。
- 每次动作前必须形成《Change Readiness》：Last Real Change、Last Change、Validation Status（含 `PENDING`、`SUCCESS`、`PARTIAL_SUCCESS`、`NO_CLEAR_EFFECT`、`NEGATIVE_EFFECT`、`INSUFFICIENT_DATA`、`INTERRUPTED_BY_NEW_CHANGE`）、New Evidence Since Change、Interaction Risk（LOW/MEDIUM/HIGH）、Current Urgency（LOW/MEDIUM/HIGH/CRITICAL）和 AI Judgment（`READY_TO_CHANGE`、`WAIT_FOR_MORE_EVIDENCE`、`EMERGENCY_OVERRIDE`、`NO_NEED_TO_CHANGE`）。未通过 Readiness 不得进入真实动作。
- 必须检查同一对象和关联对象的 `PENDING` Change。Top、Base Bid、Budget、Placement 等共同影响流量、CPC、Placement mix 和订单时，要做 `CHANGE_INTERACTION_CHECK`；若叠加会破坏归因，优先 `WAIT_FOR_VALIDATION`/`OBSERVE`。同一明确策略必须组合修改时，生成 `CHANGE_SET_ID` 并作为一个 Change Set 共同验证，不事后拆分归因。
- 只有 Spend 失控、错误流量大量消耗、库存/Offer/Listing 重大异常、异常放量、经济损失快速扩大、身份/配置错误或其他可靠高风险证据，才允许 `EMERGENCY_OVERRIDE`。日志必须说明原 Change 仍在验证期、不能等待的原因、新风险、提前干预理由和对原验证的影响；原 Change 必要时标记 `INTERRUPTED_BY_NEW_CHANGE`。
- 历史成功或失败结果参与当前候选动作排序，但不是永久规则。Learning 必须带 `Confidence`、`Evidence Window` 和 `Applicable Context`，并结合当前目标、阶段、环境、样本和经济边界重新判断；不得硬编码“修改广告必然伤权重”等未经官方证据支持的机制。
- 每次运行都把 NO_CHANGE/OBSERVE 及其理由写回 Campaign 私有日志。只有真正执行的新修改进入 `广告表现汇报优化日志\\每天更新日志\\YYYY-MM-DD_广告修改汇总.md`；`WAIT_FOR_MORE_EVIDENCE` 且没有真实修改时不进入每日“已修改”清单。Emergency Override 的真实修改必须进入每日汇总并标记 `⚠ 紧急提前干预`。

核心顺序固定为：**先读历史，再看现在，再决定要不要动**。详细 Change Readiness 字段和 20 项测试见 `references/diagnosis-framework.md`。

## Campaign 运行快照与历史驱动闭环（最新增量规则）

Campaign经营快照是每次正式巡检的结构化身份与指标记录。

本节覆盖前述日志和修改节奏的细节，作为 6-4 当前执行契约。每次诊断先读取同一 Campaign 的长期私有日志，再读取当前真实数据；日志不是普通存档，而是下一次决策的核心输入。

每次运行向同名 `[完整 Campaign Name].csv` 追加一行 Snapshot，并向 `[完整 Campaign Name].md` 追加一条 `Campaign Run Record`（只写判断与变更）：

- 数据窗口（明确自然日/时段和时区）
- Impressions、Clicks、CTR
- Spend、CPC
- Orders、Sales、CVR
- ACoS、CPA
- ROAS（只有来源可靠且口径明确时）

无法可靠获取的指标写 `[数据未获取]`，不得补猜。只有时间窗口、指标定义和归因口径可比时，才记录“当前周期 vs 上一可比周期”；否则写 `[不可可靠比较]`。快照只保留会影响下一次决策的数据，不倾倒全部明细。

快照后必须写《AI数据判断》，解释流量、CTR、CPC、CVR、ACoS 的状态、主要问题、可能根因和当前优先检查项。Placement（Top of Search、Rest of Search、Product Pages）或 Budget 只有在与当前判断相关时才读取并记录其可用指标；不得以 Spend 接近 Daily Budget 单独推出必须加预算。Keyword、Target、Search Term 只记录主要花费、主要出单、高花费低产出、重要新增/成交、正在验证、AI实际动作或会影响下一次判断的对象。

每次 Run Record 必须回答：今天发生了什么；AI 认为主要原因是什么；今天要不要动；为什么现在可以动或不能动。正式决策可为 `NO_CHANGE`、`OBSERVE`、`AUTO_EXECUTE`、`INSUFFICIENT_DATA`、`WRITE_BLOCKED`，并与 Change Readiness 的 `READY_TO_CHANGE`、`WAIT_FOR_MORE_EVIDENCE`、`EMERGENCY_OVERRIDE`、`NO_NEED_TO_CHANGE` 对应。

3–7 天及其它时长只能是 `REFERENCE WINDOW`，不是触发器。判断优先看修改后新增的有效 Impressions、Clicks、Spend、Orders、归因成熟度和风险。PENDING Change 且新证据不足时记录 `WAIT_FOR_MORE_EVIDENCE` 并继续观察；即使过去 7 天也不机械修改；时间较短但证据充分可以重新判断。关联参数必须做 `CHANGE_INTERACTION_CHECK`；同一明确策略的组合修改使用 `CHANGE_SET_ID`，按整个 Change Set 验证。

Spend 快速失控、错误流量、库存/Offer/Listing/身份或经济风险等可靠重大风险，可用 `EMERGENCY_OVERRIDE` 提前干预，说明新证据、不能等待的原因和对原验证的影响，并在必要时把原 Change 标为 `INTERRUPTED_BY_NEW_CHANGE`。Negative、Pause、Campaign 结构动作的证据门槛高于普通小幅 Bid。历史 `SUCCESS` 与 `NEGATIVE_EFFECT` 只参与候选动作排序；Learning 必须带 `Confidence`、`Evidence Window`、`Applicable Context`，不得成为永久死规则，也不得无官方证据硬编码“修改必然伤 Amazon 权重”。稳定且符合目标时可以连续 `NO_NEED_TO_CHANGE`。

每次 `NO_CHANGE`、`OBSERVE`、`WAIT_FOR_MORE_EVIDENCE`、`NO_NEED_TO_CHANGE` 都写 Campaign 私有日志。每日产品汇总固定为 `广告表现汇报优化日志/每天更新日志/YYYY-MM-DD_广告修改汇总.md`，同一产品同一自然日只有一份，重复运行持续追加。只有 `apply_change_plan` 成功且 read-back 确认实际状态符合预期的真实修改，才进入“今日实际修改”；prepare 未 apply、apply 失败、验证回写或 NO_CHANGE/OBSERVE/WAIT 均不计入。日报允许 0 修改极简记录，快速表按 Campaign 分组，并分别统计 `Modified Campaigns` 与 `Executed Changes`；验证结果单独列出，不重复算作今日修改。EMERGENCY_OVERRIDE 的真实修改进入日报并标注 `⚠ 紧急提前干预`。Campaign 私有日志、日报、Validation 和 Learning 均不进入 0-2 formal report index 或 latest-valid selector。

不得修改历史正式 HTML、原始广告数据或 0-2 索引职责；本规则只约束 6-4 的记录与决策输入。

## Campaign CSV + MD 日志简化（最新覆盖规则）

本节替换此前“所有经营快照和窗口数字写入 Markdown”的做法：**CSV 负责结构化数据，MD 负责判断、Change、Validation、Learning，原始广告文件负责完整证据。** 每个 Campaign 固定建立同名长期文件对：

- `[Product Root]\06_SKILL分析报告\广告表现汇报优化日志\[完整 Campaign Name].csv`
- `[Product Root]\06_SKILL分析报告\广告表现汇报优化日志\[完整 Campaign Name].md`

CSV 一行只代表一次有效 Run Snapshot；同一 Campaign 后续运行追加同一个 CSV 和同一个 MD，不按日期拆分，不把 Campaign ID 放进文件名。Campaign ID 必须同时写入 CSV 字段和 MD 正文。CSV/MD 仅使用已确认的 Campaign 身份，身份不一致或 CSV 损坏时保护原文件并标记 `WRITE_BLOCKED_FOR_LOG_INTEGRITY`，不得静默覆盖；同一 Run_ID 重试不得重复追加。

### Campaign CSV 稳定 Schema

CSV 至少保持以下稳定字段，数字、百分比、金额和时间格式不得与解释性长文本混列：

`Run_ID, Run_Time, Product_Code, Var_Code, Store, Marketplace, Portfolio, Campaign_Name, Campaign_ID, Advertised_ASIN, Mapped_SKUs, Advertised_SKUs, SKU_Count, Data_Through, Primary_Window_Start, Primary_Window_End, Impressions_7D, Clicks_7D, CTR_7D, Spend_7D, CPC_7D, Orders_7D, Sales_7D, CVR_7D, ACoS_7D, CPA_7D, ROAS_7D, ACoS_3D, CPA_3D, CVR_3D, ACoS_14D, CPA_14D, CVR_14D, ACoS_30D, CPA_30D, CVR_30D, Last_Real_Change_At, Last_Change_ID, Last_Change_Set_ID, Last_Changed_Object, Last_Changed_Parameter, Last_Change_Before, Last_Change_After, PostChange_Start, PostChange_End, PostChange_Impressions, PostChange_Clicks, PostChange_Spend, PostChange_Orders, PostChange_Sales, PostChange_CPC, PostChange_CVR, PostChange_ACoS, PostChange_CPA, Validation_Status, Interaction_Risk, Urgency, Change_Readiness, Decision`

`Mapped_SKUs` 与 `Advertised_SKUs` 使用共享解析器的稳定去重序列化（固定排序、`|` 分隔，如 `A3-S-2|A3-S-3`）；一行仍表示一次运行中的一个 Campaign，不因 SKU 数量拆行。`SKU_Count` 为关联 Mapped SKU 数量，Campaign 命名不加入 SKU。

默认主判断窗口为最近 7 个完整自然日：Today/Intraday 只做风险检查，Last Complete Day 看最新发生，3D 看短期变化，14D/30D 看背景，Since Last Change 判断上次修改疗效。转化归因未成熟时标记 `CONVERSION_DATA_NOT_MATURE`，不把短期 ACoS 当成最终失败。

### MD 只保留经营判断

MD 每次 Run 只追加：当前目标、CSV 的 Run_ID/数据引用、上次修改及验证、AI 数据判断、Change Readiness、今天决定、为什么动/不动、Candidate/Selected/Rejected、实际执行与 Read-back、下一步观察和带上下文 Learning。3D/7D/14D/30D 的完整数字只在 CSV 保存；Placement、Keyword、Target、Search Term 明细默认不进主 CSV，只有影响本次决策、发生 Change、处于 Validation 或产生 Learning 时，才在 MD 保存必要证据。

### 每日汇总与索引边界

每日汇总仍是 Markdown：`广告表现汇报优化日志\每天更新日志\YYYY-MM-DD_广告修改汇总.md`，不增加每日汇总 CSV。只有 apply 成功且 read-back PASS 的真实修改进入“今日实际修改”；Validation、NO_CHANGE、OBSERVE、WAIT、prepare-only、apply 失败和 WRITE_BLOCKED 不计入。Campaign CSV、Campaign MD、每日汇总和 Learning 均不进入 0-2 formal report index/latest-valid selector。

## ERP Keyword Provider（阶段6统一规则）

阶段 6 的 ERP 历史关键词只通过共享 `scripts/erp_keyword_adapter.py` 读取；本 Skill 不得自行编写 PickPwKView SQL 或解释 Provider 列名。运行时先读取 `03_系统配置/erp-amazon-data-mapping.json` 和 `erp-amazon-pickpwkview-schema.md`，再从本次已确认的 `[Product Root]/01_产品档案.md` 读取档案中明确记录的 ERP 产品编号（返回实际字段名；没有编号为 `[ERP_PROID_MISSING]`，冲突为 `[ERP_PROID_CONFLICT]`）。只以该编号作为参数查询 `Amazon.dbo.PickPwKView.ProId`，不得用 Product_Code、ASIN、文件名、首条记录或相似产品替代，也不得跨产品。

适配器返回每行 `Keyword`/`KeywordCn`、完整 `raw_fields`、字段定义状态和追溯信息（`Provider`、`Source_View`、`ERP_ProId`、`Field_Definition_Source`、`Retrieved_At`、`Source_Grain`、`Metric_Semantics`、`Data_Through`、`Freshness`、`Aggregation_Method`）。字段语义只以 `03_系统配置` 文档为准；未明确的列必须标记 `SEMANTICS_UNCERTAIN`，不得把它们猜作搜索量、点击、订单、销售、CVR、排名或竞价。连接复用既有只读配置/密钥，SQL 只允许参数化 SELECT；密码、服务器和连接字符串不得进入 Skill、报告、日志或 Git。

阶段 6 共用的 ERP 精准词语义固定为：当前产品 `ProId` 范围内，`PickPwKView.Tags` 包含完整标签 `|1精准|` 且 `Keyword` 有效的记录。`IsExact` 当前定义为“暂无用”，不得用于精准词判定；6-4 只消费共享适配器返回的精准词证据，不自行另造筛选逻辑。

- 6-2：ERP 关键词仅作为 COR 候选、EXP 候选和少量 DIS Broad Seed 的辅助证据，不能由 ERP 历史标记直接升级为核心成交词。
- 6-5：ERP 关键词仅作为当前产品历史背景或监控解释；当前 Amazon 自有经营数据优先，语义不明不计算经营指标。
- 6-4：ERP 关键词仅作为历史 Search Term/生命周期参考；当前 Amazon 自有广告数据足够后由自有数据接管，不自动跨产品扩展。

连接/驱动/密钥不可用返回 `[ERP_KEYWORD_PROVIDER_UNAVAILABLE]`，无匹配行返回 `[ERP_KEYWORD_DATA_NOT_FOUND]`；这些状态只降级 ERP 证据，不阻断本 Skill 其他数据源。
## MCP Provider Boundary / Canonical Business Model

6-4 的广告诊断只消费 HZP Canonical 业务语义，不直接依赖 SellerSpace/优麦云的原始 Tool Name、Field Name、JSON 结构、枚举、分页或指标名称。Provider Adapter 负责映射 Campaign、AdGroup、Advertised Product、Keyword、Target、Search Term、Placement、ASIN/SKU[] 及广告指标，并保留来源粒度、归因语义和去重状态。

Provider 能力必须显式标记 `SUPPORTED`、`NOT_SUPPORTED` 或 `SEMANTICS_UNCERTAIN`；缺失能力只返回 `[CAPABILITY_NOT_AVAILABLE]`，不得猜测。真实写入仍固定为 Decision → Prepare → Exact Diff → Apply → Read-back → Log → Validation；Provider 缺少可靠等价能力时标记 `[SAFE_WRITE_CAPABILITY_NOT_AVAILABLE]` 并阻断写入。未来新增 Provider 只需新增真实 Adapter，不改变本 Skill 的诊断、allowlist、Change Readiness 或安全写入边界。
## 关键词战略边界（6-0-2）

6-4 只负责广告经营决策和批准前动作设计；6-5负责执行。6-0-2 提供双轨精准词资产，6-0-3 提供精准泛词；6-4 读取这些结构化资产，再根据真实广告证据决定 Bid、Budget、Match、Placement、Negative 和验证动作，不在本 Skill 内复制关键词识别或聚类算法。

## 6-4 DECIDE 最终覆盖

最终职责、输入、Evidence Gate、Change Clock、四层 Decision、Decision Challenge、Cross-Level Consistency、Reason Trace、批准门和异常契约，以 [references/decision-engine-contract.md](references/decision-engine-contract.md) 为准。6-4 只输出批准前决策包，绝不直接写 Amazon；批准后由 6-5 执行。
