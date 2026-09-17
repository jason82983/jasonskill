# HZP Amazon 6-4｜广告经营决策

## 30 秒运行

```text
使用 6-4 Skill
产品：P001
Products Root：E:\【产品总目录】
广告数据窗口：近 30 天（如已确认）
```

6-4 用于广告已经产生真实数据后，诊断曝光、点击、转化、CPC、ACoS、放量、Campaign、关键词、Search Term、Placement 和预算问题，形成有证据的决策包和待执行动作，由6-5执行。6-4不调用Amazon Ads写操作。

运行前需要：

- `[Product Root]/01_产品档案.md`
- `[Product Root]/04_产品推广思路.md`
- Products Root 下的只读身份主表：`00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`；先按共享身份规则解析并验证 Store、Marketplace、ASIN、SKU
- 最新有效的 6-2 报告和6-3事实包及6-3广告运行事实包
- `[Product Root]/05_分析源数据/` 中的 Amazon Ads 导出
- 可用时提供 `[Product Root]/07_产品资料/` 的价格、促销、Review、库存和页面变更资料

6-4 会先确认广告数据的实际时间范围和产品阶段，再按曝光→点击→转化→经济性→规模找断点。它不会因为 ACoS 高、CTR 低、CVR 低或 0 订单就机械降 Bid、改主图或加 Negative；数据不足时会明确标记并允许“暂不调整”。

店铺身份遵循 Amazon 行业共享规则 `Amazon产品身份解析规则.md`；映射表只读，身份冲突或 SellerSpace 验证未完成时不把广告数据归到错误产品。

## 输出

正式报告写入：

`[Product Root]/06_SKILL分析报告/6-4_广告经营决策/YYYYMMDD_HHMMSS/6-4_[产品编号]_广告经营决策_YYYYMMDD_HHMMSS.html`

报告包括广告诊断结论、曝光/点击/转化/经济性/放量、Campaign、Keyword/Target、Search Term 生命周期、Keyword Mother Pool、Semantic/Purchase Intent Clusters、Expansion Batch、Placement、预算、页面路由、每日调整状态、操作卡、人工决策、1/3/7 天验证、证据充分性、优化动作和条件满足时的 6-5 交接包。运行日志写入 `06_SKILL分析报告/广告表现汇报优化日志/`，不进入正式报告索引。正式报告成功后自动调用 0-2 更新索引；6-4 不自行维护 `index.html`。

详细字段和边界见同目录的 `SKILL.md`、`references/diagnosis-framework.md`、`references/handoff-schema.md` 和 `templates/report-outline.md`。


## 证据驱动扩词

6-4 只在真实成交语义方向出现并通过证据验证后，回查 6-2 的 Keyword Mother Pool，分批生成 Expansion Proposal；每批联动 Match Type、Bid、预算和库存约束，须经用户批准后执行。
### Portfolio 范围

6-4 以已验证的 Portfolio Name/ID、Store、Marketplace、Own ASIN 和 `Mapped_SKUs[]` 作为广告诊断边界；同一 ASIN 多 SKU 只保留一个 Campaign 视图，具体变更记录 `Advertised_SKU`。错组合允许只读审计但禁止写入；扩词和扩展 Campaign 继承 6-2 Portfolio。

6-4 复用共享身份解析：Product_NewCode→正式 Product_Code→Portfolio→Var_Code→Campaign。变体 Child ASIN、Mapped_SKUs[]/Advertised_SKUs[] 映射缺失或冲突时只读诊断，不跨变体扩展；Benchmark 和 Product Target ASIN 不作为自有身份。

命名读取使用共享 `parse_campaign_name()`；新名称按当前标准解析，旧名称分为 `LEGACY_RECOGNIZABLE` 或 `LEGACY_UNKNOWN`。6-4 不因旧名称拒绝分析，也不会因 Bid、Budget 或扩词自动改名。

## 每日运行

可由外部调度器调用：`6-4，DAILY` 或 `6-4，B2，DAILY`。每次运行自动完成身份与数据新鲜度检查、广告诊断、历史变更验证、决策和日志；`Daily Run ≠ Daily Change`。当前决策为 `NO_CHANGE`、`OBSERVE`、`AUTO_EXECUTE`、`NEED_APPROVAL`、`INSUFFICIENT_DATA`、`WRITE_BLOCKED`。

有根因和证据时，AI 会生成包含当前值、建议值、幅度、证据、风险和验证窗口的操作卡；没有必要调整时记录 `NO_CHANGE` 及下次检查时间。页面、经营、库存和市场根因分别路由到 5-5、6-5、7-1/7-2 和 2-2。6-4 只生成待批准动作；满足策略和护栏的动作仍需进入6-5执行，6-4不直接写入。日志每日保存到 `广告表现汇报优化日志`，不参与正式报告索引。


## Risk-Gated Auto Execution

当前决策状态为 NO_CHANGE、AUTO_EXECUTE、NEED_APPROVAL、OBSERVE、WRITE_BLOCKED、INSUFFICIENT_DATA。只有身份无冲突、数据新鲜、根因明确、Confidence=HIGH、经济与库存安全、通过证据门槛、在集中 Auto-Execution Policy Allowlist 和预授权幅度内的低风险 Bid/Top/Budget 小幅调整，才可进入 AUTO_EXECUTE。Pause、Negative、结构、新 Campaign、大幅调整和跨身份动作默认进入 NEED_APPROVAL。策略默认关闭，AI 不能扩大自身权限。

6-5 执行必须走 `Internal Approved-by-Policy Plan → prepare_change_plan → Policy/Prepared diff → apply_change_plan → Read-Back`，差异或回读失败立即阻断并记录。全局或 Product 级 `AUTO_EXECUTION_ENABLED=false` 时只诊断不写入。日志每日保存到 `广告表现汇报优化日志`，不参与正式报告索引。

## 当前经营目标

每次运行都会重新读取当前产品的 `04_产品推广思路.md` 中《当前经营目标》，不会使用上次缓存。支持 A 验证优先、B 增长优先、C 增长利润平衡、D 利润优先、E 收缩/库存保护；模式只改变判断权重，不是固定 ACoS/Bid/Budget 参数。目标模式缺失或冲突时显示 `[经营目标无法确认]`，可继续只读诊断但不做高影响方向性写入。库存风险可临时覆盖为 E，并在日志中保留正式目标与临时状态。

6-4 按资深运营经理方式工作：先理解产品目标，再独立判断每个 Campaign、Keyword、Target、Search Term 和 Placement，最后做 Portfolio/Product reconciliation。机器层继续使用标准命名，老板层显示中文 Role/Target，例如“核心｜精准”“挖词｜自动”“竞品｜ASIN”。

## 自动广告授权

6-4 的精确自动广告授权唯一读取：

`[所有产品总根目录]/00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`

运行时从实际 Workbook 中寻找同时包含 `Product_Code`、`Second_Code`、`Status` 的 Sheet，不根据截图猜 Sheet 名。只有 `Product_Code + Second_Code + Status=ACTIVE` 才允许对应 Variant 命名空间（例如 `B2.M.*`）进入自动执行；`Second_Code` 是内部变体代码，不是 Amazon 真实 ASIN。重复 ACTIVE 行可去重，ACTIVE/非 ACTIVE 冲突、空值或关键列缺失均 Fail Closed。

Campaign 名称必须结构化解析并与授权 Product/Second_Code 精确匹配，不能用模糊前缀匹配；随后仍需通过 Identity Resolver 核验真实 Campaign ID、Store、Marketplace、Portfolio、Own ASIN 和 SKU。`B2.M` 不会误匹配 `B2.M2` 或 `B2.MM`，授权表也不会因 Product_Code 相同而授权其它 Variant。

`6-4，ALL` 只覆盖 Excel ACTIVE 授权 ∩ 当前可访问账户/店铺/站点 ∩ 身份验证通过 ∩ Active/Enabled Campaign。`6-4，B2，M` 继续受同一精确授权和既有经济、库存、Policy 护栏约束；`6-4，B2` 会返回 `[MISSING_SECOND_CODE]`，不会扫描 B2 的其它 Variant。授权表每次运行重新读取；原 `开自动的产品有.txt` 不删除、不修改，但不参与 6-4 最高授权判断，若被其它流程使用则保留兼容。

## Campaign 独立日志## Campaign 独立日志

广告运营日志按 Campaign 分开持续记录，目录仍是：

`[Product Root]/06_SKILL分析报告/广告表现汇报优化日志/`

每个 Campaign 一份历史文件对：同名 `[完整 Campaign Name].csv` 保存结构化快照，同名 `[完整 Campaign Name].md` 保存判断、变更、验证和 Learning；开头先写完整 Campaign Name，并记录 Campaign ID、产品/Second_Code、店铺、站点、Portfolio 和当前经营目标。Campaign ID 用于稳定找回历史；名称变化时不新建错误的对象历史。每次运行（包括 `NO_CHANGE` 和 `OBSERVE`）都向 CSV 追加快照并向 MD 追加判断记录。

Keyword、Target、Search Term、Placement 和 Ad Group 操作归入所属 Campaign。Campaign 之间通过 `Source Decision ID`/`Change ID` 追踪，不得混写历史。`6-4，ALL` 会逐 Campaign 处理，另生成老板汇总日报；日报不替代 Campaign 详细日志。日志不进入 0-2 正式索引。

Campaign 日志文件对固定为 `[完整 Campaign Name].csv` 与 `[完整 Campaign Name].md`，例如 `B2.M-SP-COR-EXA-01.csv` 与 `B2.M-SP-COR-EXA-01.md`；不追加 Campaign ID，不按日期新建。Campaign ID 写入 CSV 字段和 MD 正文。名称变化时先通过 Campaign ID 找回原历史；只有合法 Rename 后才同步迁移 CSV 与 MD 文件并保留旧名称记录。Windows 非法字符只替换本地文件名，正文保留真实 Amazon 名称。

每日产品汇总单独保存到：

`广告表现汇报优化日志/每天更新日志/YYYY-MM-DD_广告修改汇总.md`

Campaign 详细日志与每日汇总都不进入 0-2 正式索引。

### 老板每日主要入口

每天更新日志是老板查看单个产品广告经营情况的主要入口。文件顶部先用一句话说明当天整体状态，再展示本次正式巡检的全部 Campaign 总览；总览至少包含 Campaign、中文类型、7D ACoS、CPA、趋势、上次修改、AI 状态和“今天”动作列。`Scanned Campaigns` 统计所有完成正式诊断的 Campaign；`Modified Campaigns` 只统计 `apply_change_plan SUCCESS` 且 `read-back PASS` 的 Campaign；`Executed Changes` 统计这些 Campaign 中实际成功的 Change 数量。

未修改的 Campaign（包括正常、观察、等待验证、证据不足或已阻止）只保留极简摘要，不展开完整多窗口数据。只有真实修改成功的 Campaign 才在“今日真实修改”中展开 Before/After、原因、执行状态、Change ID 和验证窗口。验证历史可以单独列出，但不得重复计入当天新修改。同一产品同一自然日始终更新同一个 `YYYY-MM-DD_广告修改汇总.md`；即使当天没有修改也生成文件，并保留全部巡检 Campaign 总览。Campaign CSV/MD 继续作为 AI 后台长期记忆，不被日报替代。

## 修改节奏

每次诊断 Campaign 前，先读取它自己的 CSV 快照和 MD 判断日志，恢复上次修改、Change ID、Before/After、验证状态和 Learning，再结合本次新增证据决定：`CAN_CHANGE_NOW`、`WAIT_FOR_VALIDATION`、`EMERGENCY_OVERRIDE`、`NO_CHANGE` 或 `INSUFFICIENT_EVIDENCE`。不使用所有 Campaign 共用的固定“几天改一次”规则。

上次 Change 为 `PENDING` 且新证据不足时，默认继续观察；关联参数会触发 `CHANGE_INTERACTION_CHECK`，避免破坏归因。只有明确 Spend 失控、错误流量、库存/Offer/Listing 或身份等重大风险才允许 `EMERGENCY_OVERRIDE`，并在日志中说明原因及原验证影响。Learning 必须带置信度、证据窗口和适用场景。

每次运行的 `NO_CHANGE`/`OBSERVE` 都写入 Campaign 日志；每天更新日志的总览包含所有正式巡检 Campaign，但只有真实执行的新修改进入其中的“今日真实修改”详细区，紧急干预需标记 `⚠ 紧急提前干预`。

## 运行范围（Scope）

运行范围必须显式提供，遵循 **Fail Closed, Never Expand Scope**：

```text
6-4，ALL                 # 全部当前授权且 Active/Enabled 的广告
6-4，B2，M               # 仅 B2 的 M 变体
6-4，A3，S               # 仅 A3 的 S 变体
6-4，A6，BW              # 仅 A6 的 BW 变体
6-4，https://amazon...   # 解析 Own ASIN 后仅对应产品/Second_Code
```

只输入 `6-4` 或调度器传入空参数会返回 `[MISSING_SCOPE]`，不会自动变成 ALL。只输入 `6-4，B2` 这类 Product_Code-only 形式会返回 `[MISSING_SECOND_CODE]`，不会自动选择默认或唯一 Variant。手动运行必须使用 `6-4，Product_Code，Second_Code`；Second_Code 是 HZP 内部第二层广告管理代码（如 M、S、BW），不是 Amazon 真实 ASIN，也不是 SKU；一个 Second_Code 可以对应多个 SKU/ASIN。产品+Second_Code 或 URL/ASIN 解析失败返回 `[SCOPE_RESOLUTION_FAILED]`；`ALL` 与具体产品混用返回 `[SCOPE_CONFLICT]`。ALL 只覆盖有权限的账户/店铺/站点、已确认的自有身份和 Active/Enabled 广告，暂停或归档对象默认排除。每个产品/Second_Code 独立读取自己的经营目标；ALL 代表逐个判断，不代表全部都要修改。报告和日志会记录 Scope Resolution、授权边界以及 READ_ONLY/WRITE_BLOCKED 等状态。

## 运行快照与修改节奏

每次检查某个 Campaign，6-4 会先读它自己的 `[完整 Campaign Name].md`，再追加一条运行记录和《Campaign 经营快照》。快照保存数据窗口、Impressions、Clicks、CTR、Spend、CPC、Orders、Sales、CVR、ACoS、CPA；ROAS 仅在来源可靠时记录，缺失值写 `[数据未获取]`。不可比周期写 `[不可可靠比较]`，不强行造趋势。

快照后会写《AI数据判断》，只记录与下一次决策有关的 Placement、Budget、Keyword、Target、Search Term 证据，并回答“发生了什么、主要原因、要不要动、为什么现在能/不能动”。3–7 天只是参考窗口；PENDING 且证据不足时等待，证据充分时可提前判断。关联参数使用 `CHANGE_INTERACTION_CHECK`，组合动作使用 `CHANGE_SET_ID`，重大风险才用 `EMERGENCY_OVERRIDE`。

`NO_CHANGE`、`OBSERVE`、`WAIT_FOR_MORE_EVIDENCE` 和 `NO_NEED_TO_CHANGE` 仍写 Campaign 私有日志。只有 apply 成功并 read-back 确认的真实修改进入同一产品同一自然日的 `每天更新日志/YYYY-MM-DD_广告修改汇总.md`；验证不重复计为今日修改，0 修改也可生成极简记录。两类日志都不进入 0-2 正式索引。

## Campaign CSV + MD 日志

每个 Campaign 使用同名长期文件对：`[完整 Campaign Name].csv`（结构化 Run Snapshot）和 `[完整 Campaign Name].md`（AI 判断、Change、Validation、Learning）。CSV 一行代表一次有效巡检；同一 Campaign 持续追加，Campaign ID 写入字段/正文而不进文件名。原始广告导出仍是完整证据。

默认 7D 为最近 7 个完整自然日主窗口；3D 看变化、14D/30D 看背景、Since Last Change 看疗效、Today 只查风险。CSV 保持稳定字段和类型；缺失不虚构，转化未成熟时降低结论置信度。MD 不再重复完整多窗口数字，只引用 Run_ID 并记录必要判断和对象证据。

每日修改汇总仍为 Markdown，只有 apply 成功并 read-back 确认的真实修改才计入；验证不重复算今日修改，0 修改可生成极简记录。Campaign CSV/MD 与每日汇总不进入 0-2 索引。


### ERP 关键词数据源

阶段 6 可通过共享 `scripts/erp_keyword_adapter.py` 读取当前产品档案中的 ERP 编号，再以参数化 `PickPwKView.ProId` 查询历史关键词。字段定义以 `00_公共资料/03_系统配置` 为准，语义不明的列不会被猜测；缺失编号、无匹配数据或 Provider 不可用时保留状态并继续其他证据来源。
阶段 6 共用精准词定义：`PickPwKView.Tags` 包含完整标签 `|1精准|` 且 `Keyword` 有效；`IsExact` 当前定义为“暂无用”，不得用于精准词判定。6-4 只消费共享适配器输出，不复制筛选逻辑。
### Provider Boundary

核心判断使用 HZP Canonical 业务语义；SellerSpace/优麦云等 Provider 的原始字段先由 Adapter 映射。能力缺失显示 `[CAPABILITY_NOT_AVAILABLE]`，语义不明不猜；未来接入其他 Provider 只新增真实适配器，不改本 Skill 核心流程。


日报中的未授权对象显示 Authorization State，不作为广告表现问题。


授权层说明：这是 HZP Business Authorization Layer；SellerSpace/优麦云仍是当前 Provider。授权表不与 Excel 形成双重授权，开自动的产品有.txt 不参与 6-4 最高授权判断。产品日报显示 Authorization State。
## 关键词战略边界（6-0-2）

6-4 只负责广告经营决策和批准前动作设计；6-5负责执行。6-0-2 提供双轨精准词资产，6-0-3（`hzp-amz-6-0-3-precision-broad-extraction`）提供精准泛词；6-4 读取该资产，再根据真实广告证据决定 Bid、Budget、Match、Placement、Negative 和验证动作，不在本 Skill 内复制关键词识别或聚类算法。


## 6-4 DECIDE 最终覆盖

6-4 是广告经营决策系统，不是写入执行器。它读取最新有效 6-3 DATA、6-1 PLAN、6-0-3 Intent、6-0-6 Reality Evidence、6-4 历史决策和 6-5 成功执行历史，经过 Evidence Gate、四层决策、Decision Challenge 和 Cross-Level Consistency 后输出待批准 Decision Package。批准后交给 6-5；6-4 不调用 Amazon Ads 写接口。

正式输出目录：`[Product Root]/06_SKILL分析报告/6-4_广告经营决策/YYYYMMDD_HHMMSS/`。
