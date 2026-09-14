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
2. 在任何 SellerSpace 真实广告查询前，读取 Amazon 行业共享规则 `Amazon产品身份解析规则.md` 和 `00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`，按当前 Product Code 形成唯一 ACTIVE 的 Store + Marketplace + ASIN + SKU，再用 MCP 只读验证。缺失、重复 ACTIVE、INACTIVE/TEST、映射与 MCP 或 `01_产品档案.md` 冲突时按共享规则处理，不猜测、不自动修改主表；MCP 不可用时标记 `【SellerSpace实时身份验证未完成】` 并仅使用可追溯的本地证据降级。
3. 从 `[Product Root]/06_SKILL分析报告/` 选择当前产品最新有效 6-1 正式 HTML，优先读取《6-2输入交接包》。按 Product Code + Skill 编号匹配，最大 V 优先，同 V 按文件名 `YYYYMMDD_HHMMSS` 最新；排除 index、失败、incomplete、invalid、deprecated、test、temp、preview、draft、非正式输出以及 `广告表现汇报优化日志/` 目录及其子目录。规则见 `references/diagnosis-framework.md`。
4. 主动扫描 `[Product Root]/05_分析源数据/`，优先识别 Campaign、Search Term、Targeting、Advertised Product、Placement、Purchased Product、Budget、Keyword 和 ASIN Targeting 等真实 Amazon Ads 导出。必须读取实际字段、数据日期和时间窗口；不能因为文件名相似就猜语义。
5. 主动检查 `[Product Root]/07_产品资料/` 的售价、Coupon、Promotion、Review、Rating、库存、Buy Box、页面变更、价格变更、广告调整记录和运营备注；只使用实际存在资料。
6. 按需辅助回查最新有效 5-4、5-1、5-2、5-3、2-1、2-2，核对页面承接、消费者意图、关键词相关性、产品事实和竞争环境，不重新完整运行上游 Skill。

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


## Evidence-Gated Keyword Expansion｜证据驱动扩词

6-2 每次诊断除检查 Bid、Budget、Negative 和结构外，必须判断是否出现值得扩大的成交语义方向。先读取 6-1 交接的 `Keyword Mother Pool`、`Semantic Cluster`、`Purchase Intent Cluster`、Initial Released Keywords、Held Keywords、成熟度和释放规则；没有验证方向时明确不扩词。

单个词 1 Click/1 Order 只能标记 `FIRST_ORDER_VALIDATED`，不能释放整个 Cluster。只有多个相关 Search Terms 重复成交、核心词重复成交，或一致的 CVR、CPA、ACoS、相关性、时间、库存、自然排名/订单证据共同支持时，Cluster 才能从 `INITIAL_SIGNAL` 升级为 `VALIDATED`。证据不足、外围扩展流量变差或库存/季节窗口不足时保留核心、收缩外围或暂停扩词。

Cluster 验证后回查 6-1 Mother Pool，筛选尚未释放且属于该方向的词，重新检查相关性、意图、Search Volume、Rank、Bid、竞争、重复语义、现有覆盖、历史 Search Term 和经济边界。不得一次释放全部剩余词；每次生成 `Expansion Batch`，由 AI 自动选择 Exact、Phrase 或 Broad 并给出理由、Bid、Campaign、预算、验证目标、窗口和停止条件。Broad 只能使用高相关探索 Seed。

新增词前必须做 Traffic Overlap Check，识别 Campaign、Keyword、Match Type、Search Term 和 Target 重叠；语义重叠只有在没有明确角色、Bid 控制或流量隔离目的时才判为冗余。扩词预算与 Capital Release 联动，输出 Current/Added/New Daily Budget、阶段预算、库存和最大投入约束。

完整《Keyword Expansion Proposal》展示后，用户选择 A 批准追加、B 缩小规模、C 暂缓或 D 重新设计。只有完整提案获批准后，才按现有 Human Approval 安全机制执行 `prepare_change_plan → 比对 → apply_change_plan → Read-Back Verification`；未批准绝不写入。执行结果和 1/3/7 天或动态窗口验证按 Expansion Batch 独立记录。

Auto 新增且不在母词池的成交 Search Term 允许以 `Source=OWN_SEARCH_TERM` 加入母词池；Own Product 真实成交证据优先于 H10/Benchmark 推断，但不覆盖历史证据。H10 数据更新只追加来源和日期，不覆盖 Own 历史成交证据。

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

## 阶段6运行日志、人工决策与验证

6-2 必须把一次诊断闭环记录为：真实数据 → AI诊断 → 最小必要动作 → 人工批准/修改/否决 → MCP或人工执行 → 1天/3天/7天复盘。运行日志统一保存到 `06_SKILL分析报告/广告表现汇报优化日志/`，默认不进入 0-2 正式报告索引，也不参与最新版正式报告选择。

- 先输出每日调整状态：`【今天不建议调整】`、`【局部优化】`、`【需要明显调整】`、`【需要重构部分广告】`、`【优先排查广告资格/账户/商品状态】` 或 `【数据不足，继续观察】`。不机械套点击阈值。
- Search Term 生命周期可记录为：候选词 → 探索词 → 首单词 → 重复成交词 → 核心成交词 → 核心排名词 → 自然流量资产；淘汰路径为高曝光无点击、点击无转化、高成本低转化、低相关或错误意图 → 降级/否定/停止。1 点击 1 单不能自动升级为核心词。
- 每个动作使用操作卡：对象、当前数据、问题、建议动作、幅度、原因、预期结果、验证周期、成功/失败标准、风险、是否需要人工批准。动作可为保持、Bid/Budget 调整、Pause/Resume、转 Exact、Negative、Placement 调整或结构调整。
- 默认流程是 AI 读取 → AI 诊断 → AI 建议 → 人工批准/部分批准/修改后批准/否决/延后观察 → MCP或人工执行。没有写入能力时只能输出建议并明确未执行。
- 验证必须比较调整前与调整后，至少覆盖 CPC、CTR、CVR、Orders、Spend、ACoS、Search Term、Keyword、Organic order 和 Rank（有数据时），并标记【调整有效】、【基本有效】、【无明显效果】、【调整错误】或【证据不足】。
- MCP或其他外部接口先审计读取与写入能力：读取 Campaign、Ad Group、Keyword、Search Term、Placement、Bid、Budget、Performance、Orders、Sales、Organic orders、Rank、Coupon、Price、Inventory；写入 Bid/Budget、Pause/Enable、Keyword/Negative、Campaign、Placement。缺失写入能力时回退“AI建议 + 人工执行”。

## 正式报告与 0-2

保存到当前 Product Root 的 `06_SKILL分析报告/`，不覆盖历史：

`6-2_[产品编号]_广告诊断优化_V[最大版本号+1]_[YYYYMMDD]_[HHMMSS].html`

成功写入、确认文件存在且命名正确后，调用 `hzp-amz-0-2-report-index`，原样传递 Product Code、Products Root、Product Root。6-2 不扫描、生成、排序、维护或备用更新 `index.html`；报告失败不调用 0-2，报告成功但索引失败时保留报告并明确两者状态。

详细报告字段、证据充分性、动作和时间窗口规则见 `references/diagnosis-framework.md`；证据驱动扩词见 `references/evidence-gated-keyword-expansion.md`；6-3 交接字段见 `references/handoff-schema.md`；HTML 章节和表格见 `templates/report-outline.md`。
## Portfolio-aware 诊断与扩展（增量规则）

6-2 读取共享 `Amazon广告身份解析规则.md`，将 Portfolio Name（映射表实际 `广告组合` 列）和 SellerSpace 解析的 Portfolio ID 纳入诊断身份。广告查询按已验证 Store + Marketplace + Own ASIN/SKU 及 Portfolio 范围过滤；必须核验 Campaign → Advertised Own ASIN/SKU → Portfolio 的关系，Benchmark/Product Target ASIN 不得作为自有广告身份。Portfolio ID 只能通过 SellerSpace 只读发现解析，禁止硬编码。

现有 Campaign Portfolio 与映射 Portfolio 不一致时允许只读诊断并标记 `【广告组合身份冲突】`，任何 Bid/Budget/Keyword/Negative/Campaign/Target 写入或扩词都 STOP。Expansion Batch 新建对象必须继承 6-1 已验证 Portfolio Name/ID；审批提案、Prepared Plan、Read-Back 和 6-3 交接均记录 Portfolio 字段与状态。

## 统一产品与变体身份（增量规则）

6-2 与 6-1、6-3 共用 `resolve_advertising_identity()`，按 `Product_NewCode → Product_Code → Store → Product_Code_Prefix → Marketplace → Own ASIN/SKU → Portfolio → Var_Code → Campaign` 继承上下文。`Product_NewCode`（包括 N+数字）只作研究代码，诊断和扩展 Campaign 使用正式 `Product_Code`；不得按 ASIN、文件名或前缀猜代码。Own ASIN、Benchmark ASIN、Product Target ASIN 严格分开。

若“产品对应变体”无法唯一提供 `Var_Code → Child ASIN → SKU`，标记 `【变体广告身份映射不完整】`，可保留只读诊断但不得扩词或写入。扩展批次按已验证 Var_Code 和 Portfolio 绑定，不能跨变体静默汇总；冲突状态使用共享规则定义的 `[正式Product_Code缺失]`、`[店铺产品代码前缀冲突]`、`[Portfolio ID验证失败]`、`[Var_Code无法唯一解析]` 等。

6-2 继承 6-1 的 Campaign/Ad Group 名称，Bid、Budget、Placement、Coupon 或日期变化不得触发重命名。第二批扩词优先加入原有正确角色 Campaign；只有独立语义簇、预算隔离或实验确有必要时，才使用下一 Sequence，并记录独立原因。6-2 不得仅凭 Campaign Name 反推产品身份，也不得自动重命名历史 Campaign。

6-2 使用同一共享 `parse_campaign_name()` / `validate_campaign_name()` 解析新名称：`B8.M.SP-COR-EXA-01` 解析为 Product_Code=B8、Var_Code=M、AdType=SP、Role=COR、Target/Match=EXA、Sequence=01；`B8.SP-DIS-AUT-01` 的 Var_Code 为空，表示未限定或 MULTI_VARIANT。解析结果仅是辅助标签，仍须用 Shared Advertising Identity Resolver 和 SellerSpace 真实对象核验。旧名称分类为 `LEGACY_RECOGNIZABLE`（真实身份可确认）或 `LEGACY_UNKNOWN`（无法确认），不因不符合新标准而拒绝诊断。只有变体混淆、角色无法区分、身份冲突、严重影响运营或用户明确要求时，才提出 `[建议广告命名标准化]`；Rename 属于真实写操作，须经过用户批准、prepare/diff/apply/Read-Back，接口不支持时明确 `[当前MCP不支持广告活动重命名｜需要人工处理]`。

本次同步只增加独立 Var_Code 的 `.[Var_Code]` 段；SP、Role、Target/Match 和 Sequence 的原有含义、代码和顺序全部保持不变。历史名称继续兼容读取。
