# 6-3 正式报告结构

正式 HTML 文件名：

`6-3_[产品编号]_广告诊断优化_V[版本号]_[YYYYMMDD]_[HHMMSS].html`

建议章节：

1. 产品身份与《广告诊断结论》
2. 《输入版本追溯》
3. 广告数据范围与完整性
4. 6-1 原始推广目的回顾
5. 广告漏斗总览
6. 《曝光诊断》
7. 《点击诊断》
8. 《转化诊断》
9. 《广告经济性诊断》
10. 《放量能力诊断》
11. 《Campaign诊断》
12. 《Keyword / Target诊断》
13. 《Keyword Mother Pool 与语义簇状态》
14. 《Keyword Expansion Proposal｜扩词提案》（触发时）
15. 《Search Term诊断表》
16. 《Placement诊断》
17. 《预算诊断》
18. 《广告—页面问题路由》
19. 《诊断证据充分性》
20. 《优化动作清单》
21. 《反方检查》
22. 最终广告状态
23. 《6-2输入交接包》（条件满足时）
24. 数据与证据局限
25. 《名词术语解释》

首页优先显示产品代码+中文名称、诊断窗口、6-1 来源版本、当前广告状态、最大问题层级、最大赚钱点、最大烧钱点、最大流量机会、数据不足、最优先动作、是否建议大改和是否建议保持不动。

核心表字段：

- Campaign：名称、原始目的、类型、窗口、Budget、Spend、Impressions、Clicks、Orders、Sales、CTR、CPC、CVR、ACoS、证据和动作。
- Keyword/Target：对象、Match Type、原始角色/假设、真实指标、意图匹配、页面承接、充分性和动作。
- Mother Pool/Cluster：cluster_id、Purchase Intent、成熟度、已释放词、Held Keywords、证据和 release_status。
- Expansion Batch：批次、Cluster、AI选择词、Exact/Phrase/Broad、Bid、Current/Added/New Budget、验证目标、窗口、停止条件、批准和执行结果。
- Search Term：词、来源 Campaign/Keyword、意图、匹配、真实指标、商业价值、充分性和动作。
- Placement：Top of Search、Rest of Search、Product Pages（数据存在时）及真实表现。
- 优化动作：编号、优先级、层级、问题、证据、原因、最小动作、预期目标、风险、复查时间和数据。

只有真实数据适合时才使用漏斗、Spend/Sales、Campaign、Search Term 或 Placement 图表；不伪造趋势线、评分、雷达图、AI 信心分或 3D 图。


## 增量输出要求

正式报告增加：

- 《今日调整状态》
- 《Search Term生命周期》
- 《广告优化操作卡》
- 《人工决策记录》
- 《调整前后验证结果（1天/3天/7天）》
- 《运行日志证据》（仅列实际读取的运行日志）

每个动作必须保留“建议但未执行”与“实际执行”的区别。


《Keyword Expansion Proposal》至少包含：Validated Cluster、Evidence、Current Released Keywords、Mother Pool Remaining、AI Selected New Keywords、自动 Match Type、Bid、Current/Added/New Daily Budget、Expected Purpose、风险、验证窗口、Stop Condition、用户 A/B/C/D 决策。
### Portfolio 诊断字段（新增）

产品身份、Campaign 诊断、优化动作、Expansion Proposal 和 6-2 交接必须显示 `Portfolio Name`、`Portfolio ID`、验证状态、来源和读取时间。Portfolio 与映射不一致时的动作只能是只读诊断、人工核查或路由，不得写入。

### 每日轻量运行附录（Daily Run）

正式报告或单独运行日志可在首页增加《今天广告要不要动？》摘要：Decision、Decision Summary、建议动作数量、预计预算影响、最大风险、Next Check，以及 `【等待你的确认】`（仅存在真实写操作提案时）。

每个操作卡固定显示：Action ID、对象、Current Value、Proposed Value、Change %、Reason、Evidence、Expected Result、Risk、Validation Window、Approval Scope、Applied/Not Applied。无动作也显示 `Decision=NO_CHANGE`、No Change Reason 和 Next Check。

《调整前后验证结果》按 Change ID 列出 Before/After 的 Top Impressions、Clicks、CPC、Orders、CVR、CPA、ACoS、Total Orders（有数据时）、Validation Status（SUCCESS/PARTIAL_SUCCESS/NO_CLEAR_EFFECT/NEGATIVE_EFFECT/INSUFFICIENT_DATA）和解释。附《人工决策记录》及《运行日志证据》，明确建议、批准、拒绝、执行和 Read-back 的区别；广告运行日志目录不进入正式报告索引。

### 《本次经营目标》

报告首页必须显示从当前 `04_产品推广思路.md` 实际读取的：目标模式（A 验证优先 / B 增长优先 / C 增长利润平衡 / D 利润优先 / E 收缩/库存保护）、结果目标、经济边界、库存约束、特殊约束、生效日期和来源文件。模式只改变决策权重，不映射为固定 ACoS、CPA、Bid 或 Budget；无法确认模式时显示 `[经营目标无法确认]`。

### 《今日广告自动运营日报》

每日摘要显示：检查产品数、Campaign 数、自动执行数、No Change 数、Observe 数、Write Blocked 数、Spend/Orders 变化、重大风险、历史变更验证和是否建议经营目标换挡。每个自动动作显示中文 Role/Target（如“核心｜精准”），机器 Campaign Name 及 Campaign/Target ID 放在追溯层。自动执行、回读和验证必须可与 Change ID 对应。

### 《运行范围与权限边界》（必填）

正式报告首页和诊断摘要必须显示：

- `RUN_SCOPE` 与 Scope Resolution（例如 `ALL_ACTIVE_AUTHORIZED_ADS`、`EXPLICIT_SECOND_CODE_ONLY`、`MISSING_SECOND_CODE`、`MISSING_SCOPE`）
- 本次授权账户、Store、Marketplace 和已确认 Own Product Identity 范围
- Active/Enabled 主动优化对象数量，以及排除的 Paused/Archived/Disabled 对象
- 每个产品/Second_Code 的 Product_Code、Second_Code、Own ASIN、Mapped_SKUs[]、Advertised_SKUs[]、Portfolio 和独立经营目标上下文
- 对象权限状态：`READ_ALLOWED`、`WRITE_ALLOWED`、`READ_ONLY`、`IDENTITY_UNRESOLVED`、`WRITE_BLOCKED`
- 空范围、解析失败或范围冲突时的 `[缺少运行范围]`、`[SCOPE_RESOLUTION_FAILED]` 或 `[SCOPE_CONFLICT]`，并明确未执行广告操作

`ALL` 只表示所有符合授权、身份、状态和自动执行边界的广告都经过判断，不表示所有广告都会被修改。报告不得把 Benchmark、Competitor 或 Product Target ASIN 显示为 Own Advertised Product；不同产品/Second_Code的目标、经济、库存和历史证据必须分开呈现。

### 《广告自动化精确授权》（ALL 时必填）

- 授权来源：`[所有产品总根目录]/00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`
- 实际授权 Sheet 名、读取时间和实际字段：`Product_Code`、`Second_Code`、`Status`
- 规范化、去重后的授权对象：`Product_Code + Second_Code + Status=ACTIVE`
- `Second_Code` → `Second_Code` 的适配结果；它不是 Amazon 真实 ASIN
- 每个对象的授权状态：`AUTHORIZATION_MATCHED`、`AUTO_EXECUTION_NOT_AUTHORIZED`、`AUTO_AUTH_MAPPING_CONFLICT`、`CAMPAIGN_AUTH_IDENTITY_UNRESOLVED` 或 `CAMPAIGN_IDENTITY_CONFLICT`
- 最终交集：Excel ACTIVE 授权、授权账户/店铺/站点、Identity Resolver 核验通过、Active/Enabled Campaign 和既有 Policy/经济/库存护栏

`ALL` 只表示所有符合精确授权和既有安全边界的广告都经过判断，不表示全部广告都会被修改。原 `开自动的产品有.txt` 只保留其它流程兼容用途，不得作为 6-3 最高授权源或扩大 Variant 权限。报告必须区分授权状态与广告表现问题。

### 《Campaign 独立日志追踪》（必填）

每个本次检查的 Campaign 单独列出：

- 完整 Campaign Name（正文首项）和稳定 Campaign ID
- Product_Code、Second_Code、Store、Marketplace、Portfolio、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、当前经营目标
- 对应 Campaign 日志文件/记录键，以及本次 Run Record 时间
- Decision、发生了什么、AI 判断、根因、候选动作、最终选择、Before/After、Change ID、执行结果、验证窗口和 Validation Status
- `NO_CHANGE`/`OBSERVE` 的不动或继续观察理由
- Keyword/Target/Search Term/Placement/Ad Group 操作及其所属 Campaign
- 跨 Campaign 动作的 `Source Decision ID`/`Change ID`，并区分 `OWN_CAMPAIGN_EVIDENCE` 与 `PRODUCT_PORTFOLIO_CONTEXT`

同一 Campaign 的后续 Validation 必须回写同一 Campaign 的 MD 判断日志，并通过 Run_ID 回写同名 CSV 快照。Campaign 详细日志与《6-3 AI广告运营日报》分离；日志目录不进入 0-2 正式报告索引。Campaign Name 变化时必须通过 Campaign ID 找回原历史，不得错误创建新对象历史。

### 《Change Readiness》（每个候选动作前必填）

- Last Real Change、Last Change ID、Last Changed Object/Parameter、Before/After
- Current Validation Status、Minimum Observation Window、Outcome
- New Evidence Since Change：Impressions、Clicks、Spend、Orders、Sales、CPC、CVR、CPA、ACoS、Placement、Search Term
- Interaction Risk：LOW / MEDIUM / HIGH
- Current Urgency：LOW / MEDIUM / HIGH / CRITICAL
- AI Judgment：`READY_TO_CHANGE`、`WAIT_FOR_MORE_EVIDENCE`、`EMERGENCY_OVERRIDE` 或 `NO_NEED_TO_CHANGE`
- `CHANGE_INTERACTION_CHECK` 结果；组合策略使用 `CHANGE_SET_ID`
- 历史 Learning 的 Confidence、Evidence Window、Applicable Context

存在 PENDING Change 且新证据不足时，报告应显示等待验证，而不是按固定天数制造动作。每天更新日志总览包含本次全部正式巡检 Campaign，但只有真实执行的新修改进入 `每天更新日志/YYYY-MM-DD_广告修改汇总.md` 的“今日真实修改”详细区；NO_CHANGE、OBSERVE 和 WAIT_FOR_MORE_EVIDENCE 只写 Campaign 私有日志并在总览保留极简状态。Emergency Override 真实修改需显示 `⚠ 紧急提前干预`，并说明其对原验证的影响。

### 《Campaign 经营快照与每日修改边界》（必填）

每个 Campaign 的 Run Record 先回写历史，再向同名 CSV 追加数据快照，并在同名 MD 追加判断：数据窗口、Impressions、Clicks、CTR、Spend、CPC、Orders、Sales、CVR、ACoS、CPA，以及可靠时的 ROAS 进入 CSV；MD 只引用 Run_ID 并记录《AI数据判断》和四个结论：今天发生了什么、主要原因、今天要不要动、为什么现在能/不能动。Placement 与 Budget 仅在相关时记录，Keyword/Target/Search Term 只列重要对象。

Change Readiness 使用证据时钟而非固定 3/7 天：PENDING 且证据不足为 `WAIT_FOR_MORE_EVIDENCE`；证据充分可提前判断；稳定且符合目标为 `NO_NEED_TO_CHANGE`。记录 Interaction Risk、Urgency、`CHANGE_INTERACTION_CHECK`，组合策略用 `CHANGE_SET_ID`；重大风险可 `EMERGENCY_OVERRIDE`，并记录 `INTERRUPTED_BY_NEW_CHANGE`（如适用）。Learning 含 Confidence、Evidence Window、Applicable Context。

每日汇总固定为 `广告表现汇报优化日志/每天更新日志/YYYY-MM-DD_广告修改汇总.md`，同一产品同一自然日一份。只有 apply 成功且 read-back 确认的真实修改进入“今日实际修改”；验证、NO_CHANGE、OBSERVE、WAIT、prepare 未 apply、apply 失败和 WRITE_BLOCKED 不计入。快速表按 Campaign 分组并区分 `Modified Campaigns` 与 `Executed Changes`，0 修改仍可生成极简记录。Campaign 日志和日报均不进入 0-2 正式索引/latest selector。

### 产品老板每日汇总模板（每天更新日志）

同一产品同一自然日只维护一份文件；重复运行更新顶部最新状态并追加历史真实 Change。顶部顺序固定为：

```markdown
# [Product Code]｜[YYYY-MM-DD] AI广告运营

当前经营目标：[目标模式/结果目标]

## 今日结论

已巡检：[Scanned Campaigns] 个 Campaign
真实修改：[Modified Campaigns] 个 Campaign / [Executed Changes] 项 Change
继续观察：[数量]
无需调整：[数量]
证据不足：[数量]
重大风险：[数量]

老板一句话：[基于今日全部巡检结果的极简结论]

## 今日 Campaign 总览

| Campaign | 老板类型 | 7D ACoS | CPA | 趋势 | 上次修改 | AI状态 | 今天 |
|---|---|---:|---:|---|---|---|---|
| [完整 Campaign Name] | [中文 Role｜Target] | [真实值] | [真实值] | [↑改善/↓恶化/→稳定/?证据不足] | [日期/摘要或—] | [可以调整/等待验证/正常/证据不足/已阻止执行/紧急干预] | [不动/观察/Bid↓/…] |

## 今日真实修改

<!-- 仅列 apply SUCCESS + read-back PASS 的 Campaign；每个 Campaign 展开 Before/After、Change ID、原因、未选替代方案、执行和验证。无真实修改时写“今日没有广告修改”。 -->

## 重点观察

<!-- 未修改 Campaign 只写极简摘要；完整 3D/7D/14D/30D 数字保留在 Campaign CSV。 -->

## 历史修改验证

<!-- 列出本次确认的旧 Change 及 Validation，不计入 Modified Campaigns 或 Executed Changes。 -->

## 风险

[重大风险或“当前没有需要老板处理的重大广告风险”]
```

“老板类型”必须把机器 Role/Target 映射为中文（例如 `COR-EXA` → `核心｜精准`、`COM-ASI` → `竞品｜ASIN`）。“趋势”必须综合 3D、7D、14D/30D、Since Last Change 和 Data Maturity；窗口不可比或证据未成熟时显示 `? 证据不足`，不得使用单日 ACoS 制造趋势。底层 Machine State 保留，日报显示中文老板状态。日报只展示老板所需摘要，不复制 Campaign CSV、Campaign MD 或原始广告文件的完整数据。

### 《Campaign CSV + MD 运行记录》（必填）

每个 Campaign 维护同名 `[完整 Campaign Name].csv` 与 `[完整 Campaign Name].md`。CSV 一行代表一次有效 Run Snapshot，保存稳定身份、数据窗口、7D 主指标、3D/14D/30D 趋势辅助、Since Last Change、Validation/Readiness/Decision 字段；MD 只保存当前目标、CSV Run_ID 引用、AI 判断、Change、Validation、Learning 与必要对象证据。原始广告导出不被覆盖。

默认 7D 使用最近 7 个完整自然日；Today/Intraday 只查风险，3D 看变化，14D/30D 看背景，Since Last Change 看疗效。CSV 缺失值不虚构，MD 不重复完整多窗口表。CSV 写入须校验 Campaign 身份并按 Run_ID 幂等；异常标记 `WRITE_BLOCKED_FOR_LOG_INTEGRITY`。



授权层说明：这是 HZP Business Authorization Layer；SellerSpace/优麦云仍是当前 Provider。授权表不与 Excel 形成双重授权，开自动的产品有.txt 不参与 6-3 最高授权判断。产品日报显示 Authorization State。
