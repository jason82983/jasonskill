---
name: hzp-amz-5-5-live-asin-page-audit
description: 审计真实上线的 Amazon ASIN 页面，核对 5-1 至 5-4 的策略、文案和视觉是否被正确执行，诊断页面、Offer、流量、产品等根因并输出有证据的优化优先级和 Skill 路由；不直接修改 Listing、价格、Coupon 或广告。
metadata:
  short-description: 审计真实线上ASIN页面与策略执行，诊断转化问题并路由优化
---

# HZP Amazon 5-5｜线上ASIN页面审计与优化

## 角色与边界

5-5 是 Live Page Auditor、Strategy Alignment Auditor、Conversion Diagnosis 和 Optimization Decision Router。它回答“消费者现在在 Amazon 前台看到什么、是否执行了页面策略、当前问题是否值得改以及应该交给谁”。

- 5-1 负责页面战略，5-2 负责 Listing 文案，5-3 负责图片/视频/A+策划，5-4 负责上线前或页面成品 QA；5-5 负责上线后的真实页面审计。
- 不重新做 2-1/2-2，不重做页面战略，不代写完整 Listing，不制作图片/视频，不直接修改 Amazon 页面、Offer、价格、Coupon、变体或广告。
- 同一产品可重复人工触发运行；V1 不建设自动爬虫、历史数据库、自动 A/B 测试或后台监控系统。

## 何时使用

当用户要检查一个已经上线的真实 Amazon ASIN、核对页面是否按 5-1～5-4 执行、解释点击/转化问题，或判断页面是否应保持不动时使用。短命令示例：使用 5-5 Skill，产品：P001，Products Root：E:\【产品总目录】。支持 Variant-aware 短命令：`5-5，B2，M`（产品代码 + 变体代码）和 `5-5，B2`（未指定变体时先按默认 ASIN 规则核验）。

不要把 Benchmark ASIN、Product Target ASIN 或竞品 ASIN 当作自有线上页面审计对象。

## 产品身份与输入

1. 使用本次确认的 Products Root / Product Root，读取 01_产品档案.md 和公司级 Amazon产品店铺映射表.xlsx。通过公共产品身份解析逻辑确认 Product Code、产品中文名称、Store、Marketplace、Parent ASIN、Own Child ASIN、Mapped_SKUs[]、Var_Code 和 Variation Family；优先用映射表与真实页面/SellerSpace 对照。
2. 严格区分 Own ASIN ≠ Parent ASIN ≠ Child ASIN ≠ Benchmark ASIN ≠ Product Target ASIN。身份冲突输出 [线上ASIN身份无法确认] 或 [产品身份冲突]，不得猜测或继续把错误 ASIN 当自有产品。
3. 只从同一 Product Root 的 06_SKILL分析报告/ 选择 5-1、5-2、5-3、5-4 最新有效正式报告：按 Product Code + Skill 编号匹配，最高 V 优先，同 V 按文件名中的 YYYYMMDD_HHMMSS 取最新。排除 index、失败、Incomplete、Deprecated、Invalid、Test、Temp、Preview、Draft、Demo、Debug 等文件；无法确认时标记 [上游报告有效性无法确认]。
4. 只记录实际读取的上游版本。5-1～5-4 是核心输入；其他阶段仅在判断产品、市场或流量根因时辅助回查，不机械读取全部历史报告。
5. 按需读取 07_产品资料/ 的 Listing 成品、截图、主图/副图/A+、视频和版本记录；真实消费者页面优先于设计稿。没有成品时标记 【策划阶段页面审核】，不能声称已完成 Live Page 审计。

5-5 始终以 ASIN 页面为唯一审计主轴。同一 ASIN 对应多个 SKU 时不生成重复页面报告；只有可靠获取的 Offer、价格、可售、履约或资格差异才作为 SKU-level Backend Evidence/Exception 补充，并保留 `Mapped_SKUs[]`，不得把 SKU 当成新的页面身份。

### Variant-aware 短命令与身份解析

1. 解析命令中的 `Product_Code` 和可选 `Var_Code`。输入 `5-5，[Product_Code]，[Var_Code]` 时，必须在中央映射表的“产品对应变体”表中用 `Product_Code + Var_Code` 精确匹配 `ASIN`；`Var_Name` 只用于人类可读显示，不得用于反查 ASIN。匹配结果必须唯一。
2. 明确 `Var_Code` 没有对应行时输出 `[未找到对应变体ASIN]`；同一 `Product_Code + Var_Code` 对应多个不同 ASIN 时输出 `[变体ASIN映射冲突]`。这两种情况都在 Live Page 读取前停止，不猜测、不回退到其他变体。
3. 用户未输入 `Var_Code` 时，从中央映射表“产品店铺映射”表按 `Product_Code` 读取该产品的默认 `ASIN`；不新增 `Is_Default` 字段，也不把 Excel 第一行或任意变体当成默认值。该 ASIN 为空时输出 `[默认ASIN缺失]`。用户明确输入 `Var_Code` 时，优先且仅使用“产品对应变体”表中唯一的 `Product_Code + Var_Code → ASIN`，不得回退到产品店铺映射 ASIN。
4. 解析成功后，在整个运行上下文和正式报告中同时保留 `Product_Code`、`Var_Code`、`Var_Name`、最终 `ASIN`；Live Page、5-1～5-4 对照、Offer、Review 和图片审计都只能针对该最终 ASIN，不能把不同变体页面混合。
5. 变体解析失败属于身份阻断：不访问 Amazon 页面，不调用 SellerSpace Listing，不生成正式审计结论；应明确显示失败状态和需要补充/修正的映射字段。

## Live Page 获取与证据

先检查现有 Amazon 页面访问、浏览器、Listing 读取能力和 SellerSpace MCP 的 discover_capabilities / discover_fields，再选择可用接口。优先级：

1. Amazon 消费者前台或当前浏览器可验证内容（LEVEL A）；
2. SellerSpace / Amazon API / Listing 后台数据（LEVEL B，必须标记 【后台Listing数据】）；
3. 本地截图、导出和素材（LEVEL C）；
4. 5-1～5-4 策略或 AI 推断（LEVEL D）。

只有直接查看到图片才可评价图片内容；只有 URL、文件名或 alt 文本时标记 [图片内容未验证]。无法访问前台时可做部分审计，但要降低结论强度。每次运行先建立《Live Page Snapshot》，记录审计时间、Marketplace、产品身份、Title、Item Highlights/Bullets、Description、图片数量与顺序、Video、A+、Brand、Price、List Price、Coupon/Promotion、Rating、Review Count、Variation、Availability、Buy Box/Offer、Delivery、Seller/Fulfillment 等；缺失字段写 [未获取]。

证据标签至少使用：【事实】、【实测证据】、【上游策略】、【数据事实】、【AI判断】、【推算指标】、【待验证】、【数据不足】。不得把推断写成事实。

## 连续执行流程

身份确认 → 选择最新 5-1～5-4 → 获取 Live Page Snapshot → 判断真实前台/后台/策划审核 → 页面完整性 → 策略到线上执行矩阵 → Listing 文案一致性 → 视觉执行与主图 → 首屏与购买路径 → Claim/真实性/合规 → Offer → Review/VOC → 竞争现实 → 根因诊断 → P0/P1/P2/P3 优先级 → 跨 Skill 路由 → 反方检查 → 形成 6-1 输入交接包（仅条件满足）→ 生成正式 HTML → 确认落盘 → 调用 0-2。

正式 HTML 必须包含《输入版本追溯》，只列本次实际读取的报告和资料，并标明核心输入、辅助回查或历史版本对照。

## 审计维度与判断

### 1. 完整性与有效执行

检查 Title、Item Highlights/Bullets、Description、主图/副图顺序、Video、A+、Variation、Price、Coupon、Brand、Offer，以及 Amazon 是否截断、替换、漏展示或展示异常。状态使用 PASS、GAP、ANOMALY、NOT_VERIFIED。图片/视觉不仅检查“存在”，还检查是否完成原定任务、信息顺序和购买决策位置。

### 2. 策略、文案与视觉一致性

建立《策略 → 线上执行追踪矩阵》，字段为：策略项、原策略、线上实际、状态、影响、证据、建议、路由；状态为 PASS、PARTIAL、GAP、CONFLICT、NOT_VERIFIED。重点比较 5-1 P0/P1/P2、5-2 文案、5-3 视觉、真实页面和消费者实际接收；小卖点抢占核心信息时标记 [页面核心战略偏离]。

检查 Title、Bullet、Description、A+、图片文字、视频与真实产品的材料、数字、尺寸、配件、安装、Claim 和关键词语义。Claim 最终状态只用【保留】、【弱化】、【补证据后使用】、【删除】、【无法确认】；不得编造认证、测试、专利、评论或政策结论。

### 3. 首屏、转化与 Offer

用主图 + Title 前半段 + 前两张副图模拟 5～10 秒理解，回答“这是什么、给谁、解决什么、为什么不同、为什么值得买、主要顾虑是什么”。购买路径检查：识别 → 相关性 → 价值 → 差异化 → 信任 → 顾虑解除 → Offer → 购买信心。

将 Price、Coupon、Promotion、Variation Offer、Rating、Review、Delivery、Availability、Buy Box 和 Fulfillment 单独判断为 CONTENT ISSUE、OFFER ISSUE、BOTH 或 NOT ENOUGH EVIDENCE。不要因 CVR 低、销量低或 ACoS 高就直接判页面差。

### 4. Review、竞争与根因

新 Review/VOC 中的尺寸、质量、安装、误解、预期差异和真实卖点，分别判断是页面沟通问题还是产品本身问题。按需比较当前头部/竞品页面，检查原差异化是否被复制；若市场变化导致策略过时，标记 [原页面策略可能已过时] 并路由 5-1/2-2，不重做完整市场分析。

每个重要问题输出：Observed Problem、Evidence、Most Likely Root Cause、Alternative Explanation、Confidence、Business Impact、Recommended Action、Route。根因枚举：PAGE_CONTENT、VISUAL、OFFER、REVIEW、TRAFFIC_QUALITY、AD_TARGETING、PRODUCT、MARKET、INVENTORY、SEASONALITY、UNKNOWN。

## 优先级、路由与最终状态

- 【P0｜必须改】：事实/结构/变体/价格错误、阻断性缺失、无证据核心 Claim、严重真实性或合规风险。
- 【P1｜强烈建议改】：首屏、核心价值、信任、购买顾虑、顺序或重复问题，预计明显影响点击/转化。
- 【P2｜可优化】：有合理依据但需要测试的表达、场景、A+或品牌优化。
- 【P3｜暂不处理】：收益小、证据弱、当前不值得动。

每项清单必须有编号、模块、当前问题、证据、业务影响、修改方向、责任 Skill 和验证方法。允许结论为【建议保持当前页面】；不要为了证明价值强行制造问题。

路由：策略 → 5-1；文案 → 5-2；图片/视频/A+ → 5-3；页面成品 QA → 5-4；产品差异化 → 3-2；产品方案 → 3-3；样品/量产 → 4-1/4-2；广告流量/Target → 6-3；经营异常 → 6-2；市场结构变化 → 2-2。5-5 不直接改页面或广告。

主状态只能使用：HEALTHY、MINOR_OPTIMIZATION、MAJOR_OPTIMIZATION、STRATEGY_MISALIGNMENT、LIVE_PAGE_ANOMALY、INSUFFICIENT_EVIDENCE，并附 HIGH、MEDIUM 或 LOW 证据置信度。

只有页面策略、核心文案/视觉、关键 Claim 与真实产品事实没有阻断性问题，且结论允许上线时，才生成《6-1输入交接包》；不得越权设计广告方案。

## 正式输出与安全边界

报告保存到当前 Product Root 的 06_SKILL分析报告/，不覆盖历史，复用现有版本 Helper 和命名规则；默认命名为 5-5_[产品编号]_线上ASIN页面审计与优化_V[版本]_[YYYYMMDD]_[HHMMSS].html。固定章节见 templates/report-outline.md。

正式报告成功落盘且文件名确认后，才调用 hzp-amz-0-2-report-index，原样传递本次 Product Code、Products Root、Product Root。5-5 不扫描、生成、排序、维护或备用更新 index.html；报告失败不调用 0-2，索引失败时保留报告并报告原因。

不运行真实产品、不修改 Amazon 页面或原始资料、不修改映射表、不执行广告写操作、不调用 apply_change_plan、不修改历史 HTML、不 commit、不 push。详细字段见 references/audit-framework.md 和 references/handoff-schema.md。

## HTML 报告表达与阅读体验（固定规则）

本节只约束报告的表达层和阅读顺序，不改变审计逻辑、证据等级、根因判断、身份解析、最新版读取或最终状态规则。

### 两层阅读结构

- **LEVEL 1｜老板版**放在首页，使用简单中文、经营语言和直接动作，30 秒内回答：页面有没有大问题、要不要改、最应该改什么、哪些地方不要动、下一步交给哪个 Skill。
- **LEVEL 2｜专业版**放在后续章节或可折叠详细区，保留 Live Page Snapshot、输入版本追溯、策略矩阵、根因、证据、置信度和机器状态码，供复核追溯。机器状态码不得作为老板首页主标题或主结论。

### 首页固定顺序

首页标题固定为 `5-5｜线上页面体检`；副标题显示 `Product Code + 产品中文名称`、`Var_Code/Var_Name`（如有）和 `ASIN`。随后依次展示：

1. **《一句话结论》**：最多 2～3 句，说明页面整体问题和当前优先级。
2. **经营结论**：只用【不用改】、【小改】、【建议重点优化】、【建议重做部分页面】、【暂时无法判断】，并紧跟一句原因。
3. **《页面体检结果》**：主图、标题、前 3 张副图、五点描述、A+、价格/优惠、评论承接、整体策略；状态只用 🟢 没问题、🟡 值得优化、🔴 需要处理、⚪ 暂时无法判断，每项最多一句解释。
4. **《现在最值得做的3件事》**：最多 3～5 项，每项写清“哪里有问题 → 为什么 → 怎么办 → 交给谁”。
5. **《这次不建议动的地方》**：说明保持原因，避免团队无证据地全面改版。
6. **《如果销量不好，问题更可能在哪里？》**：用页面内容、图片表达、价格/Offer、广告流量、产品本身等经营语言描述风险，不展示复杂根因代码。
7. **《接下来怎么做》**：按执行顺序给出下一步和责任 Skill。

### 统一中文表达

首页和一级标题优先使用中文。`Offer Audit` 写作《客户现在能不能顺利买？》，`Strategy → Live Execution Matrix` 写作《原来想怎么卖，现在页面有没有做到？》，`Final Decision` 写作《接下来怎么做》。机器状态码（如 `LIVE_PAGE_ANOMALY`、`STRATEGY_MISALIGNMENT`、`OFFER_NOT_VERIFIED`、`ROOT_CAUSE`、`PASS/PARTIAL/GAP`）只允许出现在 LEVEL 2 的详细证据或术语解释中；首页翻译为“页面存在异常”“页面和原来的打法有偏差”“购买状态这次没有完全确认”“根因分析”“做到/部分做到/没做到/暂时看不出来”。

### 图片、Listing、Offer 与竞争的老板版标题

- 图片章节使用《7张图片，一张一张看》，逐张说明“这张图应该完成什么任务、现在怎么样、建议保持或优化、交给谁”。
- Listing 章节使用《文案有没有把产品说清楚？》，按标题、Item Highlights、Bullet、Description、A+说明现在怎么样、问题、影响和是否要改。
- Offer 章节使用《客户现在能不能顺利买？》。价格、Coupon、库存、Buy Box、配送、购买按钮无法确认时，直接写“这次没有可靠确认购买环境，暂不下结论”，只有有直接证据才标红。
- 竞争章节使用《跟现在的竞品比，还够不够强？》，回答主图、价格、Review、核心卖点和差异化是否吃亏，并给出保持/有所减弱/明显落后/数据不足。

## MCP Provider Boundary / Canonical Business Model

5-5 仍以 ASIN 为页面审计主轴。Provider 的 Offer、可售、履约和价格字段必须先由 Adapter 归一为 Canonical 语义，再作为 Backend Evidence/SKU Exception 使用；原始 Tool Name、Field Name、JSON 结构不进入页面审计判断。能力缺失标记 `[CAPABILITY_NOT_AVAILABLE]`，不猜测页面事实；未来新增 Provider 只需新增真实适配器，不改变 ASIN-first 审计逻辑。
