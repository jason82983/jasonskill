# 6-4 诊断框架

进入 SellerSpace 查询前，统一读取 Amazon 行业共享文件 `Amazon产品身份解析规则.md`，从 Products Root 的 `00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx` 解析唯一 ACTIVE 的 Store + Marketplace + ASIN，并将“产品对应变体”多行 SKU 归并为 `Mapped_SKUs[]` 后只读二次验证。身份异常按共享规则处理；本文件不复制身份解析逻辑。

## 版本与窗口

- 读取同一 Product Root 的 `01_产品档案.md`、`04_产品推广思路.md`、最新有效 6-2 新品推广报告和最新有效 6-5 产品经营监控与诊断报告。
- 版本化文件按 `Product Code + Skill 编号` 匹配，最大 V 优先；同 V 按文件名 `YYYYMMDD_HHMMSS` 最新。不得按 filesystem 时间、目录顺序或 first found 选取。
- 排除 `index.html`、失败、incomplete、invalid、deprecated、draft、preview、temp、test 和非正式报告。有效性不确定时标记 `[上游报告有效性无法确认]`，不静默回退旧版。
- 广告数据必须写明实际窗口和产品阶段；不同窗口不可无说明混比。

## 广告数据发现

主动扫描 `05_分析源数据` 中的 Campaign、Search Term、Targeting、Advertised Product、Placement、Purchased Product、Budget、Keyword、ASIN Targeting 等导出，并检查 `07_产品资料` 的价格、Offer、Review、Rating、库存、Buy Box、页面/价格/促销变化和运营记录。以真实字段为准，不因文件名猜测语义。

## 漏斗断点

先判主要断点：曝光 → 点击 → 转化 → 广告经济性 → 流量规模。

- 无曝光：资格、索引/相关性、状态、Target、Match Type、Budget、Bid、搜索量、库存、Buy Box 和竞争环境。
- 有曝光没点击：意图、主图、Title、价格、Rating、Review、Offer、Placement 和竞争页面。
- 有点击无订单：先区分流量错与页面接不住，再查产品、价格、Review、Offer 和竞争。
- 高 ACoS：按 Campaign 原始目的、流量质量、商业价值、数据量和可放大性解释；不机械降 Bid。
- 赚钱不等于能放量：检查流量规模、曝光份额、Bid/Budget、Organic Rank、页面承接和库存。

## 下钻字段

Campaign、Ad Group、Keyword/Target、Search Term 和 Placement 分层记录实际存在的 Campaign、Match Type、ASIN、Status、Budget、Bid、Impressions、Clicks、CTR、CPC、Spend、Orders、Sales、CVR、ACoS、ROAS。Campaign 平均只能作为入口，必要时必须下钻 Search Term。

## 动作与证据

诊断状态只用 `【证据充分】`、`【初步信号】`、`【证据不足】`。动作优先级是广告优化专用的 `【P0｜立即处理】`、`【P1｜高优先级】`、`【P2｜观察/优化】`；不是产品或页面阶段优先级。

允许动作：暂不调整/继续收集、继续观察、扩大验证、提高/降低 Bid、转 Exact、Negative 候选、暂停、进入页面诊断、进入结构调整、进入资格排查。任何 Bid 或 Budget 动作都要说明要解决的问题和依据。0 订单不自动 Negative；意图错误或证据充分长期无价值才提出 Negative 候选。

不得统一使用 10/20/30 点击停词阈值；结合售价、毛利、CPC、测试目的、关键词价值、样本量和风险承受能力。一次优先只改一个可解释变量；最小问题做最小修改。

## 时间波动与路由

单日波动检查曝光、点击、CPC、Spend、Budget、Search Term、Placement、CVR、Organic、价格、Coupon、Review、库存、Buy Box、页面和竞争变化。严重资格/商品状态异常先标记 `[广告资格待排查]`。多个核心高意图流量同时出现明确 CTR/CVR 承接问题，才标记 `【页面承接问题明显｜返回5-4优化】`；单个词失败不推倒整页。


## 阶段6闭环补充

6-4 必须把一次诊断闭环记录为：真实数据 → AI诊断 → 最小必要动作 → 人工批准/修改/否决 → MCP或人工执行 → 1天/3天/7天复盘。运行日志统一保存到 `06_SKILL分析报告/广告表现汇报优化日志/`，默认不进入 0-2 正式报告索引，也不参与最新版正式报告选择。

- 先输出每日调整状态：`【今天不建议调整】`、`【局部优化】`、`【需要明显调整】`、`【需要重构部分广告】`、`【优先排查广告资格/账户/商品状态】` 或 `【数据不足，继续观察】`。不机械套点击阈值。
- Search Term 生命周期可记录为：候选词 → 探索词 → 首单词 → 重复成交词 → 核心成交词 → 核心排名词 → 自然流量资产；淘汰路径为高曝光无点击、点击无转化、高成本低转化、低相关或错误意图 → 降级/否定/停止。1 点击 1 单不能自动升级为核心词。
- 每个动作使用操作卡：对象、当前数据、问题、建议动作、幅度、原因、预期结果、验证周期、成功/失败标准、风险、是否需要人工批准。动作可为保持、Bid/Budget 调整、Pause/Resume、转 Exact、Negative、Placement 调整或结构调整。
- 默认流程是 AI 读取 → AI 诊断 → AI 建议 → 按 Risk-Gated/Autonomous Policy 自动执行，或因策略/能力边界转人工确认、观察或阻断 → MCP或人工执行。没有写入能力时只能输出建议并明确未执行。
- 验证必须比较调整前与调整后，至少覆盖 CPC、CTR、CVR、Orders、Spend、ACoS、Search Term、Keyword、Organic order 和 Rank（有数据时），并标记【调整有效】、【基本有效】、【无明显效果】、【调整错误】或【证据不足】。
- 外部接口按读取/写入能力审计；缺少写入能力时只输出建议并明确未执行，禁止假装完成 Bid、Budget、Pause、Negative 或结构修改。


## Evidence-Gated Keyword Expansion

6-4 先读取 6-2 的 Mother Pool、Semantic/Purchase Intent Clusters、Initial Released Keywords、Held Keywords 与成熟度。没有值得放大的成交语义方向时不扩词。1 Click/1 Order 只能是 `FIRST_ORDER_VALIDATED`；Cluster 升级 `VALIDATED` 必须结合多个相关 Search Terms/重复成交、CVR、CPA、ACoS、相关性、时间、库存和自然证据动态判断，不使用固定死门槛。

验证成功后只回查同方向的 Held Keywords，继续按相关性、意图、Search Volume、Rank、Bid、竞争、覆盖和经济边界筛选 Expansion Batch。每批必须做 Traffic Overlap Check、自动选择 Exact/Phrase/Broad、联动 Added Budget 和 Capital Release，并有批准、验证和停止条件。扩词失败时保留已验证核心、收缩外围，不静默判整个 Cluster 失败。

Auto 新成交 Search Term 可追加到 Mother Pool，标记 `OWN_SEARCH_TERM`；H10 更新追加来源和日期，不覆盖 Own 真实成交历史。扩词提案获用户批准前不得调用写接口，批准后沿用 prepare_change_plan → 比对 → apply_change_plan → Read-Back Verification。
## Portfolio 范围与写入边界

Campaign、Ad Group、Keyword/Target、Search Term 和 Placement 诊断表增加 `Portfolio Name`、`Portfolio ID`、`Portfolio Status`。先验证映射表 `广告组合` 与 SellerSpace 只读 Portfolio，再检查 Campaign 的 Own ASIN、Mapped_SKUs[]/Advertised_SKUs[] 关系。Portfolio 不匹配可以保留为只读证据，但不得生成可执行写入；扩词、竞品 Product Target 和预算扩展必须继承已验证 Portfolio。

诊断同时沿共享解析器的 `Product_NewCode → Product_Code → Portfolio → Var_Code → Campaign` 关系展开；变体 Child ASIN、Mapped_SKUs[]/Advertised_SKUs[] 无法唯一映射时只读并标记 `【变体广告身份映射不完整】`，不得跨变体合并或扩展。

## Daily Run 与决策状态

外部调度器可以调用 `6-4，DAILY` 或 `6-4，B2，DAILY`。每次运行顺序固定为：Identity Validation、Data Freshness Check、Advertising Performance Diagnosis、Previous Change Validation、AI Decision、Log。Daily Run 不等于 Daily Change；V1 不启用无人审批广告写入。决策状态仅允许：

| Decision | 规则 |
|---|---|
| `NO_CHANGE` | 证据显示无需改变，必须写原因与 Next Check |
| `OBSERVE` | 信号存在但尚未达到动作门槛，继续收集指定指标 |
| `CHANGE_RECOMMENDED` | 根因和证据足够，输出可批准的操作卡 |
| `URGENT_CHANGE_RECOMMENDED` | 严重超支、广告失控、身份/Offer/库存高风险，优先请求批准 |
| `INSUFFICIENT_DATA` | 关键数据不足，只做可支持的诊断，不猜数字 |
| `WRITE_BLOCKED` | 身份、权限、Portfolio 或对象冲突，禁止写入 |

根因优先路由：页面承接 → 5-5；经营总诊断 → 6-5；库存 → 7-1/7-2；市场 → 2-2。只有广告根因才生成广告动作。动作卡至少包含对象、Current Value、Proposed Value、Change %、Reason、Evidence、Expected Result、Risk、Validation Window 和是否需批准。允许 Hold、Bid/Budget、Bidding Strategy、Placement/Top、Exact 晋级、扩词批次、Pause/Negative、Product Target、预算迁移和局部结构调整；不为满足每日运行而强制产生动作。

## 变更冷却、验证和证据门槛

每个写操作生成 Change ID，并记录 Product_Code、Second_Code、Campaign ID、Target ID（如适用）、Changed At、参数、Before/After、证据、预期结果、Validation Metric、Minimum Observation Window、Validation Status。Bid、Top、Budget、Negative、Keyword Expansion 按点击、花费、订单、归因延迟、角色和经济边界动态确定窗口，可参考 1/3/7 天但不能按固定天数结案。窗口内默认不重复修改同一关键变量；严重超支、异常流量、库存风险、广告失控、身份或 Buy Box/Offer 异常可提前升级。

验证阶段比较 Before/After 的 Top Impressions、Clicks、CPC、Orders、CVR、CPA、ACoS、Total Orders（有数据时），结果只能为 `SUCCESS`、`PARTIAL_SUCCESS`、`NO_CLEAR_EFFECT`、`NEGATIVE_EFFECT` 或 `INSUFFICIENT_DATA`。少量点击 0 单不能直接暂停核心词，单个订单不能宣布成功，单日 ACoS 峰值不能单独大幅降 Bid；连续高 Spend+足够 Clicks+0 Order、重复成交 Search Term 才提高相应置信度。COR-EXA 的 Dynamic Bids - Up and Down 与 Top +50% 仅是 Launch Reference，真实 Placement/CVR/CPA/ACoS 优先。

## 执行批准、差异和日志

用户可用“批准”“全部执行”“只执行第1项”“第2项不要”或修改某个参数表达范围。执行链为 `prepare_change_plan → Approved/Prepared diff → apply_change_plan → Read-Back`；Material Difference 包括 Store、Portfolio、Product_Code、Var_Code、ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Campaign/Target、Bid、Budget、Placement、Bidding Strategy、Negative 和 Campaign Count 等。差异出现时必须 STOP 并重新确认；Read-Back 未确认不得报告成功，部分失败记为 `PARTIAL_FAILURE` 或 `FAILED`。本参考文档只定义流程，不代表本次调用写接口。

每个 Campaign 的详细 Run Record 写入其 `[完整 Campaign Name].md`；产品级每日汇总写入 `06_SKILL分析报告/广告表现汇报优化日志/每天更新日志/YYYY-MM-DD_广告修改汇总.md`。Campaign 记录字段至少为 Run Date、Product_Code、Second_Code、ASIN、Store、Portfolio、Data Window、Decision、Decision Summary、Actions Proposed、Actions Approved、Actions Rejected、Actions Applied、No Change Reason、Evidence、Root Cause、Risk、Change IDs、Validation Window、Next Check、Read-back Result。两类日志均不进入 0-2 索引或正式报告 latest selector。长期学习仅使用 Own Product Real Evidence，优先级为自有历史、变更结果、成交 Search Term、SellerSpace/Amazon 实时、官方建议、H10/Cerebro、通用经验。

## Scope 最终契约（最新覆盖）

6-4 的运行范围在身份验证、广告发现和任何写操作之前解析。Fail Closed, Never Expand Scope：ALL 必须显式指定，空 Scope 不能代表 ALL；越具体的输入只能得到相同或更窄的范围。

- 6-4，ALL 设置 RUN_SCOPE=ALL_ACTIVE_AUTHORIZED_ADS。实际候选是授权表中 Product_Code + Second_Code + Status=ACTIVE 的命名空间与当前可访问账户/Store/Marketplace 内 Active/Enabled Campaign 的交集；不先获取全部 ASIN 再决定范围。
- 6-4，B2，M、6-4，A3，S、6-4，A6，BW、6-4，A6，M2 设置 RUN_SCOPE=EXPLICIT_SECOND_CODE_ONLY，只处理 B2.M.*、A3.S.*、A6.BW.* 或 A6.M2.*。一个 Second_Code 下允许多个 SKU/ASIN，不要求 SKU 参数或唯一 Amazon ASIN。
- Amazon Product URL 或明确 Own ASIN 仍可作为兼容快捷入口，但最终必须唯一解析为 Product_Code + Second_Code；Benchmark、Competitor、Product Target 或未知 ASIN 不得成为 Own Scope。
- 仅输入 6-4，B2 或 6-4，B2，返回 [MISSING_SECOND_CODE]，不得自动选择第一行、唯一或 ACTIVE Second_Code，也不得扫描 B2 的全部 Variant。
- 仅输入 6-4 或调度器空参数返回 [MISSING_SCOPE]；参数数量错误返回 [INVALID_SCOPE_FORMAT]；Product_Code 为空返回 [MISSING_PRODUCT_CODE]；Second_Code 不存在或映射失败返回 [SCOPE_RESOLUTION_FAILED]；ALL 与具体参数混用返回 [SCOPE_CONFLICT]。
- 外部调度器只有在显式提供 6-4，ALL 或有效的 6-4，Product_Code，Second_Code 后才能运行；空 DAILY 不得转成 ALL。

Campaign Name 必须先通过结构化 Parser 按英文句点分段：Segment 1=Product_Code，Segment 2=Second_Code，剩余部分=Campaign_Structure。授权比较只对前两段做 Exact Match；禁止 startswith、contains、substring 或模糊前缀匹配。因此 A6.M2.SP-COR-EXA-01 不得匹配 A6.M20.*、A6.M21.* 或 A6.M2X.*。6-4，A6，M2 永远不扫描 A6.BW.*、A6.M.* 或其他产品。

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

## 广告自动化精确授权契约（Product_Code + Second_Code + ACTIVE）

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

## Campaign 独立日志契约（最新日志规则）

高频广告运营日志以 Campaign 为基本单位，目录固定为：

`[Product Root]\\06_SKILL分析报告\\广告表现汇报优化日志\\`

### 归属与文件

一个 Campaign 对应一份持续历史日志；不同 Campaign 不得写入同一份详细运营日志。日志正文第一项必须为完整 `Campaign Name`，随后至少记录老板显示的中文 Role/Target、Product_Code、Second_Code、Campaign ID、Store、Marketplace、Portfolio、Own Advertised ASIN、`Mapped_SKUs[]`、`Advertised_SKUs[]`、`SKU_Count` 和当前经营目标。Campaign Name 负责可读性，Campaign ID 是内部稳定身份；不能只依赖名称归属历史。

创建新日志前先检查已有命名机制并保持兼容；当前固定文件对为 `[完整 Campaign Name].csv` 与 `[完整 Campaign Name].md`，不追加 Campaign ID，也不追加日期。Windows 非法字符只对本地文件名做安全替换，正文仍保存 Amazon 返回的完整真实 Campaign Name；Campaign ID 写入 CSV 字段和 MD 正文并作为唯一归属键。Campaign Name 变化时先通过 Campaign ID 找回原日志；只有 6-4 合法执行 Campaign Rename 后，才同步迁移为 `[New Campaign Name].csv` 与 `[New Campaign Name].md`，并保留 Previous Campaign Name、Current Campaign Name、Campaign ID 及全部历史。每日产品汇总另存于 `广告表现汇报优化日志/每天更新日志/YYYY-MM-DD_广告修改汇总.md`，不与 Campaign 详细日志混写。默认不按日期拆散同一 Campaign 的历史。

### Run Record 与回写

同一 Campaign 每次 6-4 运行在其日志中追加一条 Run Record，至少包含：运行时间、当前经营目标、Decision（`NO_CHANGE`、`OBSERVE`、`AUTO_EXECUTE`、`INSUFFICIENT_DATA`、`WRITE_BLOCKED`）、发生了什么、AI 判断、根因、候选动作、最终选择、未选替代方案、Before/After、prepare_change_plan、diff、apply_change_plan、read-back、执行结果、Change ID、验证指标、最小观察窗口和 Validation Status。`NO_CHANGE` 与 `OBSERVE` 也必须写入，说明不动或继续观察的证据。

后续 `Change Validation` 必须回写产生该 Change 的同一 Campaign 历史，并保留原始动作、观察窗口、结果、Validation Status 和 Campaign-specific Learning。Learning 只代表当前 Campaign 的历史证据，不自动成为通用规则。存在 `PENDING` Change 时，下一次该 Campaign 默认优先 `OBSERVE`，除非出现明确重大风险。

Keyword、Target、Search Term、Placement、Ad Group 的动作都归属其所属 Campaign 日志。跨 Campaign 晋级或执行必须同时记录 `Source Decision ID`/`Change ID`；接收动作的 Campaign 也记录来源。Campaign A 的历史标记为 `OWN_CAMPAIGN_EVIDENCE`，只能以 `PRODUCT_PORTFOLIO_CONTEXT` 形式辅助产品级判断，不能作为 Campaign B 的自身历史证据。

### ALL 与日报

`6-4，ALL` 对白名单和授权范围内的每个 Campaign 分别读取自己的历史、经营目标和当前广告数据，独立诊断、执行/观察和追加日志。所有 Campaign 完成后另生成《6-4 AI广告运营日报》，只汇总检查数量、修改、保持、观察、异常、Spend 变化和重大风险；日报不得塞入或替代每个 Campaign 的底层详细历史。Campaign 日志仍不进入 0-2 formal report index。

### Campaign Log Mock Test Contract 1–20

以下为实现或静态回归检查契约，不代表本次对真实广告执行：

| # | 情形 | 预期 |
|---:|---|---|
| 1 | 每个 Campaign 创建/定位日志 | 每个 Campaign 有独立日志 |
| 2 | 日志第一项 | 包含完整 Campaign Name |
| 3 | 稳定归属 | 包含 Campaign ID |
| 4 | 两个 Campaign | 不得写入同一详细日志 |
| 5 | 同一 Campaign 多次运行 | 追加到同一历史日志 |
| 6 | `NO_CHANGE` | 产生 Run Record |
| 7 | `OBSERVE` | 产生 Run Record |
| 8 | `AUTO_EXECUTE` | 记录 Before/After |
| 9 | Change ID | 正确归属 Campaign |
| 10 | 后续 Validation | 回写对应 Campaign 历史 |
| 11 | Pending Change | 影响下一次该 Campaign 判断 |
| 12 | Campaign A 历史 | 不得成为 Campaign B 的 Own Campaign Evidence |
| 13 | Keyword/Target/Search Term/Placement | 归入所属 Campaign |
| 14 | 跨 Campaign 动作 | 通过 Source Decision ID/Change ID 追踪 |
| 15 | ALL 多 Campaign | 分别写自己的日志 |
| 16 | Boss Daily Digest | 与 Campaign Detailed Log 分离 |
| 17 | Campaign Name 变化 | 仍可通过 Campaign ID 找回原历史 |
| 18 | 历史正式分析报告 | 不修改 |
| 19 | 高频 Campaign 日志 | 不进入 0-2 formal report index |
| 20 | Windows 非法字符 | 文件名安全处理 |

报告和日志应能区分 `OWN_CAMPAIGN_EVIDENCE`、`PRODUCT_PORTFOLIO_CONTEXT`、建议但未执行和实际执行；不得因日期、名称变化或日报汇总造成历史断裂。

## Campaign 修改节奏与历史日志驱动决策（最新规则）

准备诊断某 Campaign 前，先读取该 Campaign 自己的 `[完整 Campaign Name].md`，恢复：Last Run At、Last Decision、Last Real Change At、Last Change ID、Last Changed Object、Last Changed Parameter、Before、After、Why Changed、Expected Result、Validation Metrics、Minimum Observation Window、Current Validation Status、Outcome 和 Previous Learning。该私有日志与当前 Amazon/SellerSpace 数据共同构成决策证据。

### Change Readiness

不得使用所有 Bid、Budget 或 Placement 共用的固定修改天数。每个候选动作按对象、修改幅度、Campaign Role、当前经营目标、流量/Clicks/Orders/Spend、归因成熟度、数据新鲜度、产品生命周期、上次修改原因、修改后新证据量和当前风险，形成：

```text
《Change Readiness》
Last Real Change:
Last Change:
Validation Status: PENDING / SUCCESS / PARTIAL_SUCCESS / NO_CLEAR_EFFECT /
                   NEGATIVE_EFFECT / INSUFFICIENT_DATA /
                   INTERRUPTED_BY_NEW_CHANGE
New Evidence Since Change: Impressions / Clicks / Spend / Orders / Sales /
                            CPC / CVR / CPA / ACoS / Placement / Search Term
Interaction Risk: LOW / MEDIUM / HIGH
Current Urgency: LOW / MEDIUM / HIGH / CRITICAL
AI Judgment: READY_TO_CHANGE / WAIT_FOR_MORE_EVIDENCE /
             EMERGENCY_OVERRIDE / NO_NEED_TO_CHANGE
```

时间只是验证条件之一；7 天只有少量新证据不能机械修改，短时间有足够成熟证据则可以重新判断。存在同一对象或关联对象的 `PENDING` Change 时，先做 `CHANGE_INTERACTION_CHECK`，判断是否会干扰流量、CPC、Placement mix、订单或归因；不值得叠加时选择 `WAIT_FOR_VALIDATION`/`OBSERVE`。多个参数只有在同一明确策略下才可组合，并以 `CHANGE_SET_ID` 作为一个共同验证单元。

### 紧急覆盖与历史 Learning

Spend 快速失控、错误流量大量消耗、库存/Offer/Listing 重大异常、异常放量、经济损失扩大、身份或配置错误等可靠高风险证据，可以触发 `EMERGENCY_OVERRIDE`。必须在 Campaign 日志记录原 Change 仍在验证期、不能继续等待的原因、新风险、提前干预理由及其对原验证的影响；原 Change 必要时标记 `INTERRUPTED_BY_NEW_CHANGE`。

历史 `SUCCESS`、`NEGATIVE_EFFECT` 和其它结果可参与当前候选动作排序，但不能变成永久死规则，必须结合当前产品目标、Campaign 阶段、环境、样本和经济边界。Learning 至少带 `Confidence`、`Evidence Window` 和 `Applicable Context`。不得无官方证据硬编码“改广告必然伤权重”等机制。

`NO_CHANGE`/`OBSERVE` 必须追加到 Campaign 私有日志。只有真实执行的新修改才进入 `广告表现汇报优化日志/每天更新日志/YYYY-MM-DD_广告修改汇总.md`；单纯 `WAIT_FOR_MORE_EVIDENCE` 不进入“已修改”清单。Emergency Override 的真实修改进入每日汇总并标记 `⚠ 紧急提前干预`。

### Campaign 修改节奏 Mock Test Contract 1–20

以下为实现或静态回归检查契约，不代表本次对真实广告执行：

| # | 情形 | 预期 |
|---:|---|---|
| 1 | 诊断前读取 Campaign 私有日志 | 先恢复历史上下文 |
| 2 | Last Real Change | 正确恢复 |
| 3 | Pending Change | 正确恢复 |
| 4 | Pending + 新证据不足 | `WAIT_FOR_MORE_EVIDENCE` |
| 5 | 多天但样本不足 | 不机械修改 |
| 6 | 时间较短但证据充分 | 允许重新判断 |
| 7 | 同参数连续修改 | 触发 Change Readiness |
| 8 | 关联参数修改 | 触发 `CHANGE_INTERACTION_CHECK` |
| 9 | Top 后立即改 Base Bid | 识别归因干扰 |
| 10 | 明确高风险事件 | 允许 `EMERGENCY_OVERRIDE` |
| 11 | Emergency Override | 原 Change 标记 `INTERRUPTED_BY_NEW_CHANGE` |
| 12 | 历史 SUCCESS | 参与候选动作排序 |
| 13 | 历史 NEGATIVE_EFFECT | 参与候选动作排序 |
| 14 | 历史 Learning | 不当作永久规则 |
| 15 | Learning | 保存 Confidence/Evidence Window/Applicable Context |
| 16 | NO_CHANGE/OBSERVE | 写入 Campaign 私有日志 |
| 17 | WAIT_FOR_MORE_EVIDENCE 且无修改 | 不进入每日已修改清单 |
| 18 | Emergency Override 真实修改 | 进入每日汇总并标记紧急提前干预 |
| 19 | 权重理论 | 不存在无证据的必然伤害硬编码 |
| 20 | 任一候选动作 | 能解释现在可改或不可改 |

## Daily 多产品摘要

无产品参数的 `DAILY` 读取 ACTIVE 映射，逐产品/Second_Code复用同一身份解析，最后生成一份《今日广告决策清单》：🔴 需要确认、🟡 继续观察、🟢 不需要处理、⚪ 数据/身份异常；先展示需要批准的动作，不合并不同变体证据。

## Risk-Gated Auto Execution（最新覆盖规则）

本节覆盖此前“所有真实写操作均需批准”的默认表述。当前决策状态为 `NO_CHANGE`、`AUTO_EXECUTE`、`NEED_APPROVAL`、`OBSERVE`、`WRITE_BLOCKED`、`INSUFFICIENT_DATA`；旧的 `CHANGE_RECOMMENDED`/`URGENT_CHANGE_RECOMMENDED` 仅描述严重性，随后必须归类到上述执行状态。

Allowlist、幅度、经济护栏和开关集中定义在 `references/auto-execution-policy.md`，默认 `AUTO_EXECUTION_ENABLED=false`，AI 不得自行扩大策略。Policy 至少包含 `max_bid_change_pct`、`max_top_change_pp`、`max_budget_change_pct`、`max_daily_incremental_spend`、`minimum_confidence`、动态证据与冷却规则、经济/库存护栏和 `allowlist`。

进入 `AUTO_EXECUTE` 必须同时满足：产品、店铺、Portfolio、Second_Code 命名空间；Child ASIN 与 Mapped_SKUs[]/Advertised_SKUs[] 仅作可用时的身份对账 和 Campaign 身份无冲突；数据新鲜且考虑归因延迟；根因明确、证据门槛和 Confidence=HIGH 满足；动作在 Allowlist 与预授权幅度内；经济、库存、页面/Offer/Buy Box 正常；不在同一变量 Cooldown 且无其它 WRITE BLOCK。任一条件不满足，转 `NEED_APPROVAL`、`OBSERVE`、`WRITE_BLOCKED` 或 `INSUFFICIENT_DATA`。

V1 只允许自动执行小幅 Bid、Top of Search、Budget 调整及 Hold/Observe/No Change。Pause、Negative、大幅调整、Campaign 结构、新建/删除 Campaign、ASIN、Mapped_SKUs[]/Advertised_SKUs[]/Second_Code/Portfolio 变化、大规模扩词或 Target 调整默认 `NEED_APPROVAL`。

自动动作必须经过 `Internal Approved-by-Policy Plan → prepare_change_plan → Policy Plan vs Prepared Plan Diff → apply_change_plan → Read-back → Log`。执行前计算 Current/Proposed、Change %、Expected Spend Impact、Potential Maximum Effective Bid、Break-even/Target CPA/Inventory/Recent Change Risk；任何 Material Difference 或回读失败都不得标记成功。自动变更进入 Pending Validation Queue，按动态 1/3/7 天或其它窗口评估，负面结果默认转 `NEED_APPROVAL`。

全局或 Product 级 `AUTO_EXECUTION_ENABLED=false` 时仍可读取、诊断、记录和生成建议，但不写广告。每日《今日广告自动运营日报》列出自动执行、需确认、观察、无需调整和异常阻断，并显示 Policy Rule、Confidence、护栏、回读结果和验证窗口。

## Mock Test Contract A-T

实现或静态回归检查至少覆盖以下情形；这些是决策契约，不代表已对真实产品执行：

| Case | 输入/情形 | 预期 |
|---|---|---|
| A | 正常表现 | `NO_CHANGE` 并写日志 |
| B | 昨日刚改 Bid | Cooldown，不重复修改 |
| C | COR-EXA 曝光不足 | 建议 Up/Down 与 Top +50% |
| D | COR-EXA Top 高花费低转化 | 不机械保持 +50% |
| E | Search Term 重复成交 | 建议 Exact 晋级 |
| F | 少量点击 0 单 | 不提前暂停核心词 |
| G | 高 Spend、足够 Clicks、0 Order | 提出明确动作 |
| H | 高效 Campaign 频繁预算耗尽 | 提出预算动作 |
| I | ACoS 高但自然/核心趋势改善 | 不机械砍广告 |
| J | 页面 CVR 异常 | 路由 5-5 |
| K | 库存风险 | 路由 7，不盲目放量 |
| L | 批准全部动作 | prepare → diff → apply → Read-back |
| M | 仅批准 Action 1 | 只执行 Action 1 |
| N | Prepared Plan 有 Material Difference | STOP，重新确认 |
| O | apply 部分失败 | 记录 `PARTIAL_FAILURE` |
| P | 达到验证窗口 | 自动 Before/After 评价 |
| Q | 连续 5 天 No Change | 每天保留 Decision Log |
| R | 身份冲突 | `WRITE_BLOCKED` |
| S | 关键数据不足 | `INSUFFICIENT_DATA` |
| T | 多产品 Daily | 汇总《今日广告决策清单》，优先确认项 |

### Risk-Gated Auto Execution A-R

风险门控的 Mock Test 还需覆盖：A 高置信度+低风险Bid小幅调整→`AUTO_EXECUTE`；B Bid变化超过Policy→`NEED_APPROVAL`；C 小幅Top调整+证据充分→`AUTO_EXECUTE`；D 大幅Top调整→`NEED_APPROVAL`；E 小幅Budget调整且经济安全→`AUTO_EXECUTE`；F Pause核心Exact→`NEED_APPROVAL`；G Negative核心Search Term→`NEED_APPROVAL`；H 身份冲突→`WRITE_BLOCKED`；I 库存风险→禁止自动Scale；J 页面/Offer异常→禁止自动提高投入；K 处于Cooldown→`OBSERVE`；L Policy Plan不一致→STOP + `NEED_APPROVAL`；M Read-back失败→不标记成功；N 连续5天无需修改→正常 `NO_CHANGE` 日志；O 自动修改后表现恶化→不机械反复调参；P 全局 `AUTO_EXECUTION_ENABLED=false`→只诊断不写广告；Q Product级 Kill Switch 关闭→该产品不执行；R AI试图超出Policy→阻断。

## Campaign 运行快照、证据时钟与日报契约（最新覆盖）

本节补足 Campaign CSV + MD 日志的可执行记录格式；与前文冲突时以 CSV 负责数据、MD 负责判断的规则为准。每次运行先读取同名 Campaign CSV 与 MD，恢复 Last Real Change、Last Change ID/Set、Before/After、Validation Status、Outcome 和带上下文的 Learning，再读取当前证据。

### Run Record 最小结构

结构化数字写入同名 Campaign CSV；MD 仅引用 Run_ID 并保存判断与变更：

```markdown
## [Run ID] [运行时间]
数据：[Campaign Name].csv；Run_ID：[... ]
当前目标：[...]

### AI数据判断
流量/CTR/CPC/CVR/ACoS状态：[...]
主要问题与根因：[...]
当前优先检查：[...]

### 四个必答问题
今天发生了什么：[...]
主要原因是什么：[...]
今天要不要动：[...]
为什么现在可以/不能动：[...]
```

CSV 行保存数据窗口、7D 主指标、3D/14D/30D 辅助指标、Since Last Change 与状态字段；缺失为 `[数据未获取]`，不可比为 `[不可可靠比较]`。

`Placement`（Top/Rest/Product Pages）和 Budget 只在相关问题出现时记录可获得的证据；Keyword、Target、Search Term 只保留重要决策对象。缺失值写 `[数据未获取]`，不可比趋势写 `[不可可靠比较]`，绝不虚构。

### 动态节奏、Change Readiness 与日报

3–7 天及其它天数只是 `REFERENCE WINDOW`。PENDING Change + 新证据不足必须 `WAIT_FOR_MORE_EVIDENCE`；七天但样本不足仍不改；两天但高流量且证据充分可重新判断；成熟且符合目标可 `NO_NEED_TO_CHANGE`。每个候选动作记录 `Interaction Risk`、`Current Urgency`、`CHANGE_INTERACTION_CHECK` 和 AI Judgment；同一策略的多参数动作生成 `CHANGE_SET_ID`。重大支出、错误流量、库存/Offer/Listing/身份或经济风险允许 `EMERGENCY_OVERRIDE`，标记原 Change 的 `INTERRUPTED_BY_NEW_CHANGE`（如适用）。Negative/Pause/结构变更的证据门槛高于小幅 Bid。历史 SUCCESS/NEGATIVE_EFFECT 参与排序但不变成永久规则；Learning 必须含 Confidence、Evidence Window、Applicable Context，禁止无证据权重理论。

每日汇总固定为 `广告表现汇报优化日志/每天更新日志/YYYY-MM-DD_广告修改汇总.md`，一产品一自然日一份，重复运行追加。只有 apply 成功且 read-back 确认的真实修改才计入今日修改；验证、NO_CHANGE、OBSERVE、WAIT、prepare 未 apply、apply 失败和 WRITE_BLOCKED 均不计入。日报必须区分 `Modified Campaigns` 与 `Executed Changes`，按 Campaign 分组列 Campaign Name、中文 Role/Target、对象、Before、After、原因、状态，并允许 0 修改极简记录；紧急真实修改标注 `⚠ 紧急提前干预`。Campaign 私有日志与日报均不进入 0-2 formal report index/latest selector。

### 产品老板每日汇总层（新增前台展示契约）

每天更新日志是单个产品老板查看广告经营情况的唯一主要入口。它必须先给出当天整体一句话结论，再展示本次正式巡检的全部 Campaign；老板不需要打开每个 Campaign 的 CSV/MD 才能回答“今天检查了什么、动了什么、有什么风险”。Campaign CSV/MD 仍是 AI 后台长期记忆，原始广告导出仍是完整证据。

顶部固定包含：当前经营目标、`Scanned Campaigns`、`Modified Campaigns`、`Executed Changes`、继续观察数、无需调整数、证据不足数和重大风险数。`Scanned Campaigns` 是本次完成正式诊断的 Campaign 总数；`Modified Campaigns` 只统计 `apply_change_plan SUCCESS` 且 `read-back PASS` 的 Campaign；`Executed Changes` 是这些 Campaign 中实际成功 Change 的总数。同一 Campaign 多个 Change 仍只计 1 个 Modified Campaigns，但按实际 Change 数计 Executed Changes。

紧接顶部生成《今日 Campaign 总览》，默认字段为：Campaign、中文老板类型、7D ACoS、CPA、趋势、上次修改、AI状态、今天。可按当前经营目标补充 Orders、Spend 或 CVR，但不得复制完整 CSV 字段。机器 Campaign Name 和 Machine State 保留在追溯层；老板类型必须按 Role/Target 中文映射，`COM-ASI` 必须显示“竞品｜ASIN”，不得显示“竞品｜自动”。AI 状态在老板层映射为：READY_TO_CHANGE→可以调整、WAIT_FOR_MORE_EVIDENCE→等待验证、EMERGENCY_OVERRIDE→紧急干预、NO_NEED_TO_CHANGE→正常/无需调整、INSUFFICIENT_DATA→证据不足、WRITE_BLOCKED→已阻止执行。趋势必须综合 3D、7D、14D/30D、Since Last Change 和 Data Maturity；窗口不可比、样本不足或归因未成熟时显示 `? 证据不足`，不得使用单日 ACoS 生成趋势。

未修改 Campaign（NO_CHANGE、OBSERVE、WAIT_FOR_MORE_EVIDENCE、INSUFFICIENT_DATA、WRITE_BLOCKED）必须出现在总览，但默认只写极简状态摘要，不展开完整 3D/7D/14D/30D 表格、Placement、Keyword 或 Search Term 明细。只有 `apply_change_plan SUCCESS` 且 `read-back PASS` 的真实修改 Campaign 才进入“今日真实修改”详情，并展开对象、Before/After、Change ID、原因、未选替代方案、执行状态和验证窗口。prepare-only、apply 失败、read-back 失败或 WRITE_BLOCKED 不得写成“修改成功”；若 apply 成功但 read-back 未通过，记录“执行状态异常/待确认”。历史 Change Validation 单独列出，不增加当天 Modified Campaigns 或 Executed Changes。

同一产品同一自然日只维护 `每天更新日志/YYYY-MM-DD_广告修改汇总.md` 一份；重复运行更新顶部最新状态并追加历史真实 Change，不生成 `_01`/`_02`。即使当天 0 修改，也必须生成文件并展示全部巡检 Campaign 总览。Campaign 日志、日报和 Learning 均不进入 0-2 formal report index/latest selector。

#### Daily Owner Summary Mock Test Contract 1–38

| # | 情形 | 预期 |
|---:|---|---|
| 1 | 顶部列出全部正式巡检 Campaign | Scanned Campaigns 与总览数量一致 |
| 2 | 未修改 Campaign 出现在总览 | 不遗漏 |
| 3 | 未修改 Campaign 不计入 Modified Campaigns | 计数保持 0 |
| 4 | 真实修改 Campaign 展开详情 | 进入今日真实修改 |
| 5 | apply SUCCESS + read-back PASS | 才计真实修改 |
| 6 | apply 成功但 read-back 失败 | 不写修改成功，标执行状态异常 |
| 7 | 一个 Campaign 多个 Change | Modified=1，Executed=N |
| 8 | NO_NEED_TO_CHANGE | 显示正常/无需调整 |
| 9 | WAIT_FOR_MORE_EVIDENCE | 显示等待验证 |
| 10 | INSUFFICIENT_DATA | 显示证据不足 |
| 11 | WRITE_BLOCKED | 显示已阻止执行 |
| 12 | EMERGENCY_OVERRIDE | 显示紧急干预 |
| 13 | 中文老板类型 | Role/Target 映射正确 |
| 14 | COM-ASI | 显示竞品｜ASIN，不显示自动 |
| 15 | 趋势证据不足 | 显示 ? 证据不足 |
| 16 | 单日 ACoS | 不直接生成趋势 |
| 17 | 未修改摘要 | 仅极简摘要 |
| 18 | 完整多窗口数据 | 不重复写入日报 |
| 19 | 真实修改详情 | 包含 Before/After |
| 20 | 修改原因 | 详情包含核心原因 |
| 21 | Rejected Alternatives | 详情包含精简说明 |
| 22 | 执行状态 | 包含 prepare/apply/read-back |
| 23 | 历史 Validation | 不计入今日新 Change |
| 24 | 0 修改日 | 仍生成日报 |
| 25 | 0 修改日总览 | 仍展示全部 Campaign |
| 26 | 同日多次 Run | 更新同一文件 |
| 27 | 文件命名 | 不生成 `_01`/`_02` |
| 28 | 后续 Run 顶部 | 反映截至当前最新状态 |
| 29 | 历史真实 Change | 不被覆盖删除 |
| 30 | Campaign CSV | 继续追加，不被日报替代 |
| 31 | Campaign MD | 继续追加，不被日报替代 |
| 32 | 日报索引边界 | 不进入 0-2 |
| 33 | Campaign CSV/MD 索引边界 | 不进入 0-2 |
| 34 | ALL 多产品 | 每个产品各自生成日报 |
| 35 | ALL 全局日报 | 与产品日报职责分离 |
| 36 | 未修改长表 | 不复制 3D/7D/14D/30D |
| 37 | 真实修改计数 | 只按 apply+read-back |
| 38 | B2/A3 Mock | 不执行真实广告修改 |

### Campaign Runtime Evidence Mock Test Contract 1–60

以下为静态/Mock 契约，覆盖本节要求，不代表真实产品执行：

| Case | 必须验证 | 预期 |
|---:|---|---|
| 1 | 文件名 | 同名 `.csv` + `.md` |
| 2 | Campaign ID | 写正文，不进文件名 |
| 3 | 隔离 | 不同 Campaign 分开 |
| 4 | 追加 | 同一 Campaign 持续追加 |
| 5 | 历史读取 | 诊断前先读私有日志 |
| 6 | Last Real Change | 正确恢复 |
| 7 | Last Change ID | 正确恢复 |
| 8 | Pending Validation | 正确恢复 |
| 9 | 快照核心指标 | Impressions/Clicks/CTR/Spend/CPC/Orders/Sales/CVR/ACoS/CPA |
| 10 | ROAS | 仅可靠时记录 |
| 11 | 缺失值 | `[数据未获取]` |
| 12 | 不可比周期 | `[不可可靠比较]` |
| 13 | Placement | 相关时读取证据 |
| 14 | Budget | 相关时读取证据 |
| 15 | 对象筛选 | 只记重要对象 |
| 16 | 四问 | 每次 Run 均回答 |
| 17 | Pending+不足 | WAIT_FOR_MORE_EVIDENCE |
| 18 | 7 天+不足 | 不机械修改 |
| 19 | 2 天+充分 | 允许重新判断 |
| 20 | 稳定 Campaign | NO_NEED_TO_CHANGE |
| 21 | 不制造动作 | 稳定不改 |
| 22 | 同参数连续改 | 触发 Readiness |
| 23 | 关联参数 | 触发 Interaction Check |
| 24 | Top→Base | 识别归因干扰 |
| 25 | 组合动作 | 生成 CHANGE_SET_ID |
| 26 | 高风险 | 允许 Emergency |
| 27 | Emergency记录 | 写原因和证据 |
| 28 | 原 Change | 可标 INTERRUPTED_BY_NEW_CHANGE |
| 29 | 高影响动作 | 更高证据门槛 |
| 30 | 固定 3 天 | 不存在硬触发 |
| 31 | 固定 7 天 | 不存在硬触发 |
| 32 | 权重理论 | 不无证据硬编码 |
| 33 | 历史 SUCCESS | 参与排序 |
| 34 | 历史 NEGATIVE_EFFECT | 参与排序 |
| 35 | Learning字段 | Confidence/Window/Context |
| 36 | Learning边界 | 不成为永久规则 |
| 37 | NO_CHANGE | 写私有日志 |
| 38 | OBSERVE | 写私有日志 |
| 39 | WAIT | 写私有日志 |
| 40 | NO_NEED | 写私有日志 |
| 41 | 日报目录 | 固定每天更新日志 |
| 42 | 一日一文件 | 同产品同自然日一份 |
| 43 | apply+read-back | 才算真实修改 |
| 44 | NO_CHANGE日报 | 不计修改 |
| 45 | OBSERVE日报 | 不计修改 |
| 46 | WAIT日报 | 不计修改 |
| 47 | WRITE_BLOCKED | 不冒充成功 |
| 48 | prepare未apply | 不计修改 |
| 49 | apply失败 | 不计成功 |
| 50 | 3参数改单广告 | Modified=1/Executed=3 |
| 51 | 日报快速表 | 显示七项关键列 |
| 52 | 日报详情 | 按 Campaign 分组 |
| 53 | 可追踪性 | Campaign/Change/Run ID |
| 54 | Validation | 不重复计今日修改 |
| 55 | 0 修改 | 允许极简记录 |
| 56 | Emergency成功 | 进入日报并标记 |
| 57 | 跨 Campaign | Source Decision/Change 追踪 |
| 58 | 历史隔离 | A 不冒充 B |
| 59 | Rename | ID 保持连续 |
| 60 | 索引隔离 | 私有日志/日报不进 0-2 |

## Campaign CSV + MD 简化契约（最新覆盖此前快照写入方式）

本节替换此前把 3D/7D/14D/30D 完整数字反复写入 MD 的方式。 CSV负责结构化数据，MD负责判断、Change、Validation、Learning。**CSV 负责数据，MD 负责判断，原始广告数据负责完整证据。** 每个 Campaign 固定为同名文件对：`[完整 Campaign Name].csv` + `[完整 Campaign Name].md`，目录仍为 `06_SKILL分析报告/广告表现汇报优化日志/`。CSV 一行 = 一次有效 Run Snapshot；同一 Campaign 追加同一 CSV/MD，不按日期拆分；Campaign ID 写字段和正文，不进标准文件名。

CSV 采用稳定字段：

```text
Run_ID,Run_Time,Product_Code,Var_Code,Store,Marketplace,Portfolio,Campaign_Name,Campaign_ID,Advertised_ASIN,Mapped_SKUs,Advertised_SKUs,SKU_Count,Data_Through,Primary_Window_Start,Primary_Window_End,Impressions_7D,Clicks_7D,CTR_7D,Spend_7D,CPC_7D,Orders_7D,Sales_7D,CVR_7D,ACoS_7D,CPA_7D,ROAS_7D,ACoS_3D,CPA_3D,CVR_3D,ACoS_14D,CPA_14D,CVR_14D,ACoS_30D,CPA_30D,CVR_30D,Last_Real_Change_At,Last_Change_ID,Last_Change_Set_ID,Last_Changed_Object,Last_Changed_Parameter,Last_Change_Before,Last_Change_After,PostChange_Start,PostChange_End,PostChange_Impressions,PostChange_Clicks,PostChange_Spend,PostChange_Orders,PostChange_Sales,PostChange_CPC,PostChange_CVR,PostChange_ACoS,PostChange_CPA,Validation_Status,Interaction_Risk,Urgency,Change_Readiness,Decision
```

最近 7 个完整自然日是默认主判断窗口：Today/Intraday 只做异常/风险，Last Complete Day 看最新发生，3D 看短期方向，14D/30D 看背景，Since Last Change 判断疗效。完整窗口优先不混入未结束的今天；转化或归因未成熟时写 `CONVERSION_DATA_NOT_MATURE`，不能机械大幅调参。MD 每次只保存当前目标、CSV Run_ID/引用、上次 Change/Validation、AI 数据判断、Change Readiness、四个必答问题、Candidate/Selected/Rejected、执行/read-back、下一步和带 Confidence/Evidence Window/Applicable Context 的 Learning。Placement/Keyword/Target/Search Term 默认不进主 CSV，仅在影响决策时写入 MD 必要数字。

只有 apply_change_plan 成功且 read-back PASS 才计入真实修改；不修改历史正式 HTML 报告。CSV 写入前校验 Campaign ID、Campaign Name、Product_Code、Second_Code、Store、Marketplace；历史缺列、Schema 不一致、行损坏、编码异常或身份冲突时标记 `WRITE_BLOCKED_FOR_LOG_INTEGRITY`，保护原文件，不静默覆盖。Run_ID 幂等，重复重试不重复追加。每日汇总继续使用 `每天更新日志/YYYY-MM-DD_广告修改汇总.md`，不生成每日 CSV；真实修改必须 apply 成功且 read-back PASS；只有 apply_change_plan 成功且 read-back 确认的修改才计入日报；验证、NO_CHANGE、OBSERVE、WAIT、prepare-only、apply 失败和 WRITE_BLOCKED 不计入今日修改。CSV、MD 和每日汇总均不进入 0-2 formal report index/latest selector。

### Campaign CSV Simplification Mock Test Contract 1–40

| # | 情形 | 预期 |
|---:|---|---|
| 1 | Campaign 建立文件对 | 同名 `.csv` + `.md` |
| 2 | CSV 粒度 | 一行一个有效 Run Snapshot |
| 3 | 后续运行 | 追加同一 CSV |
| 4 | MD 历史 | 追加同一 MD |
| 5 | 不按日期拆 CSV | 单文件持续追加 |
| 6 | Campaign ID | 不进文件名 |
| 7 | Campaign ID | 写入 CSV/MD |
| 8 | 默认窗口 | 最近 7 个完整自然日 |
| 9 | 未结束今天 | 不混入普通 7D |
| 10 | Intraday | 只做风险检查 |
| 11 | 3D | 短期趋势 |
| 12 | 14D/30D | 历史背景 |
| 13 | Since Last Change | 独立疗效窗口 |
| 14 | PostChange | 关联 Last Change |
| 15 | Data Maturity | 不机械修改 |
| 16 | 7D 字段 | 正确写入 CSV |
| 17 | 缺失数据 | 不虚构 |
| 18 | 类型稳定 | 数字/百分比/金额分离 |
| 19 | Run_ID | 幂等不重复 |
| 20 | 身份冲突 | 不写错 CSV |
| 21 | MD 负担 | 不重复完整多窗口表 |
| 22 | Run_ID 引用 | MD 可追溯 CSV |
| 23 | Placement | 默认不进主 CSV |
| 24 | Keyword | 默认不进主 CSV |
| 25 | Search Term | 默认不进主 CSV |
| 26 | 重要对象 | 必要证据进入 MD |
| 27 | Change Readiness | 保持工作 |
| 28 | WAIT | 保持工作 |
| 29 | NO_NEED | 保持工作 |
| 30 | Emergency | 保持工作 |
| 31 | Interaction | 保持工作 |
| 32 | 固定 3/7 天 | 不存在自动触发 |
| 33 | 2 天高证据 | 可重新判断 |
| 34 | 7 天低证据 | 继续等待 |
| 35 | 每日汇总 | 继续使用 MD |
| 36 | 每日 CSV | 不生成 |
| 37 | apply+read-back | 才计真实修改 |
| 38 | 索引隔离 | CSV/MD 不进 0-2 |
| 39 | 损坏/冲突 | 保护原文件并阻断写入 |
| 40 | 多 Campaign | 独立运行不互相污染 |

