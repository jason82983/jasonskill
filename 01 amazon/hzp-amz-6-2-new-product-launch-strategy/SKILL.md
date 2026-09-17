---
name: hzp-amz-6-2-new-product-launch-strategy
description: 将 6-1 最新有效且已批准的 Amazon 广告作战计划转为 Desired State，与实时广告状态对账，并在精确差异获批后安全应用、回读和审计；不重判投放战略或关键词。
metadata:
  short-description: 将已批准的 6-1 作战表安全应用到 Amazon Ads
---

# HZP Amazon 6-2｜新品推广方案

## 正式职责

**6-1 = PLAN；6-2 = BUILD；6-5 = 日常 APPLY。** 本 Skill 的正式身份保持：中文名 `6-2｜新品推广方案`，英文名 `New Product Launch Strategy`，Skill ID `hzp-amz-6-2-new-product-launch-strategy`。

6-2 只把 6-1 的最新有效批准计划翻译成 Amazon 技术实体，查询实时广告状态，生成确定性差异，首次创建（BUILD）已批准广告架构并回读。不得自行改变或重新决定 Intent、Keyword、作战任务/优先级、阶段、EXACT/PHRASE/BROAD/AUTO/ASIN/PT/PRODUCT/CATEGORY、控制方式或预算战略；不得新增不在已批准 Battle Unit 中的 Target。6-2 不消费 6-4 日常决策决策，也不执行运行期 Bid/Budget/Placement/Status/Negative/Harvest/结构迁移动作；这些获批日常动作统一交给 `hzp-amz-6-5-advertising-optimization-action-executor`。

## 6-1 输入与执行门

### Runtime Campaign Scope（必填）

每次运行先读取当前 Product Root 的 `01_产品档案.md`，其中必须明确配置 `ProductCode`、`CampaignTag` 和 `CampaignPrefix`。`01_产品档案.md` 是 6-2 Runtime Campaign Scope 的唯一技术配置来源。例如：

```text
ProductCode = B2
CampaignTag = M
CampaignPrefix = B2.M.
```

`04_产品推广思路.md` 仅作为人工推广思路、经营目标、预算/库存约束和待 AI 验证事项的决策参考；它不是 Runtime Campaign Scope 的技术配置来源。若其中出现同名字段，不参与 6-2 Scope 解析。

程序必须用 `scripts.campaign_scope_contract.build_campaign_scope()` 重建并核对 `CampaignPrefix=ProductCode.CampaignTag.`：缺失、格式不合法或文件值与运行参数不一致时停止，返回 `CAMPAIGN_SCOPE_NOT_CONFIGURED` 或 `RUNTIME_SCOPE_MISMATCH`。`CampaignTag` / `CampaignPrefix` 只表示本次广告体系的识别范围，不代表 Variant，不得推断颜色、尺码、SKU 或 ASIN。真实 Variant 仍独立来自共享产品身份解析，用于 Own ASIN/SKU/变体验证和 Logical Identity。Desired Campaign Name 必须以该前缀开头。

通过 `scripts/campaign_scope_contract.py::load_product_campaign_scope(product_root)` 从 `01_产品档案.md` 读取并核对 Scope，再通过 `scripts/new_product_battle_plan_contract.py::resolve_latest_approved_battle_plan(product_root, product_code)` 读取同一最新有效 `RUN_ID` 的 A/B/C/D：D `广告创建参数表` 是唯一的创建参数来源。

- A：`新品意图市场作战表.csv`
- B：`新品关键词作战明细.csv`
- C：`新品关键词阶段规划表.csv`
- D：`广告创建参数表.csv`（Campaign/Ad Group/Target 全部创建参数；唯一参数来源）
- 配套正式 HTML 报告

当前允许执行范围是 `确认状态=APPROVED`、当前允许阶段（当前合同为 `PHASE_1`）、且 `控制方式!=不投` 的 Battle Units。`PROPOSED`、`HOLD`、未批准、非当前阶段或不投记录不得创建。没有 Approved Battle Unit 时返回 `NO_APPROVED_BATTLE_PLAN`；不得由 6-2 自行批准。

读取并保留作战任务、阶段、投放方式、目标类型、目标值、控制方式、Intent Code、Battle Unit ID 及 Target 事实。6-1 行批准只是战略审批，不是 Amazon 写入授权。完整输入合同见 [approved-battle-plan.md](references/approved-battle-plan.md)。缺少或不一致的 ASIN/PT/Category 目标事实必须停止并返回技术冲突。

## 从批准计划构造 Desired State

执行 `scripts/advertising_state_reconciler.py::build_desired_state_from_6_1`，仅消费已解析的 6-1 Approved Bundle。D 中的 Campaign/Ad Group/Target 参数必须逐字段透传；`DATA_NOT_AVAILABLE`、`待人工确认` 或 `Parameter Status!=READY_FOR_6_1` 时返回 `CREATION_BLUEPRINT_NOT_READY` / `EXECUTION_NOT_READY`。6-2 不得再根据经济模型、实时历史或默认值补猜 Bid、Budget、Placement、Bidding Strategy、Portfolio、Own ASIN/SKU、Status 或否定项。

Desired State 需包含 Campaign、Ad Group、Advertised Product、Target 实体、父子 Logical ID、6-1 `RUN_ID`、Battle Unit ID、Own ASIN/SKU、Campaign 参数和 Target 参数。结构、身份算法、共享兼容与迁移合同见 [execution-reconciliation.md](references/execution-reconciliation.md)。

Role/Target 翻译只按 6-1 已批准的语义执行；6-2 不再选择角色或重判关键词：

| 6-1 作战任务 + 投放方式 | Technical Role / Target Type |
|---|---|
| 首攻/核心 + EXACT | COR-EXA |
| 扩展 + PHRASE | EXP-PHR |
| 探索 + BROAD / AUTO | DIS-BRO / DIS-AUT |
| 竞品 ASIN + ASIN | COM-ASI |
| Product Target + PT | DIS-PT |
| Category + CATEGORY | CAT-CAT |

不唯一映射返回 `ROLE_TRANSLATION_AMBIGUOUS`。6-1 B 的 `目标类型`/`目标值` 是 ASIN、PT/Category 的唯一目标事实来源；不能从对标 ASIN、Own ASIN、关键词文本或 AI 猜测替代。字段缺失或类型不符时返回技术冲突并交回 6-1 完善输入。

`控制方式` 是 Campaign 物理控制边界：

- **独立**：Campaign Logical Identity/Name 必须带唯一、原样复用的 6-1 Intent Code。同一 Intent 下可将多个兼容 Target 放入同一 Campaign/Ad Group，不可一词一 Campaign。
- **共享**：Intent Code 不进入 Campaign Name；按 Product、Variant、AdType、Role、Target/Traffic Type、执行阶段和明确逻辑组聚合。只有 Campaign Budget、Placement、Bidding Strategy、Ad Group Default Bid 等物理级设置兼容时才可合并；不兼容时 `SHARED_GROUP_INCOMPATIBLE`，退回 6-1/人工，不静默拆改战略。
- **不投**：不生成 Campaign、Ad Group 或 Target。

多 Benchmark 仅作 6-1 Reality Evidence，不得产生多套 Current Product 广告架构。
多个 Benchmark 不复制广告架构；同一 Keyword 的市场事实在上游只贡献一次，Benchmark observation 不得放大搜索量或机会值。任何 Target 仍须由 6-1 明确批准。

## COR-EXA Initial Bid 兼容规则

仅当 6-1 已批准的目标属于 `CORE_HIGH_CONFIDENCE_EXACT` 且角色为 `COR-EXA` 时，保留新品核心精准默认参考：合理决定的 Base Bid 不额外机械加价；`Top of Search +50%`、`Rest of Search 0%`、`Product Pages 0%`、`Dynamic Bids - Up and Down`。+50% 可按真实证据调整，不适用于 EXP-PHR、DIS-BRO、DIS-AUT 或 COM-ASI。

必须同时展示 Base Bid、Top Adjustment、Top Placement Adjusted Bid、Dynamic Upward Multiplier（平台上限未确认时标为 `【动态上调上限未确认】`）、Potential Maximum Effective Bid 与 Break-even / Economic Risk。不得把 `Base Bid × 1.20` 作为默认，也不得机械 `×1.20` 默认；基础竞价保持证据支持的合理值。后续监控方须基于真实 Top of Search 展示、点击、订单、CVR、CPA、ACoS 判断继续、调整或取消 Top +50%，不能机械加 Bid。

## Naming、Logical Identity 与序号

Campaign 格式固定为 `{ProductCode}.{CampaignTag}.{AdType}-{Role}-{TargetType}-[IntentCode]-{Seq}`。ProductCode、CampaignTag、AdType 以点分隔；CampaignTag 为本轮不透明 Tag，独立包含 Intent Code，共享不包含，不投不命名。真实 Variant 另存于实体身份，不从 CampaignTag 推断。当前 6-2 只实际执行已验证支持的 SP；不得伪造不支持的广告类型。Ad Group 与实体身份由共享身份解析器维护。

Campaign/Ad Group/Target 不以名称模糊匹配。Logical ID 应基于 6-1 稳定身份、控制边界和批准分组；Target Logical ID 同时绑定 Battle Unit 与所属 Campaign 边界，使共享↔独立转换产生新 Desired Target 和旧 Target 的迁移候选。不能解析 Amazon ID↔Logical ID 时停止，不能靠相似名称避免重复。

Campaign Seq 从产品目录的追加式 `06_SKILL分析报告/广告表现汇报优化日志/6-2_广告实体身份清单.jsonl` 读取/预留。同 Logical ID 永久沿用序号；同一命名干只在确需第二个物理 Campaign 时分配 `02` 等。预留须在 Provider 写入前追加；已有 Campaign Name 不因新运行自动改名，Existing Actual Name 优先保留。时间戳和 CSV 文件名不参与序号身份。

身份通过共享 Canonical Identity Resolver（`resolve_advertising_identity`）确认；平台字段和写入能力必须通过 Provider Boundary 适配，不在 6-2 内复制身份模型或直连平台私有实现。

## Initial BUILD / Architecture Reconcile 执行闭环

1. 核实 Product Root、`01_产品档案.md` 的 Runtime Campaign Scope、`04_产品推广思路.md` 的人工决策参考、映射表的 Own ASIN / Variant / SKU / Store / Marketplace / Portfolio；严格区分 Own ASIN、Benchmark ASIN 与 Product Target ASIN。只有已验证自有身份可作为 Advertised Product。
2. 发现当前 SellerSpace 能力/字段后，逐站点实时查询当前 Campaign、Ad Group、Advertised Product、Keyword/Target、Bid、Budget、Placement、Status 和 Amazon IDs。历史 CSV 不代表 Actual State。
3. 先在当前 Store / Marketplace 的实时 Campaign 清单中严格保留 `CampaignName STARTS_WITH CampaignPrefix` 的对象；非此前缀广告不统计、不匹配、不进入 Desired State，也不修改。仅当该前缀下没有任何有效 Campaign 时判定 `BUILD`；该前缀下已有 Campaign 时判定 `RECONCILE`。店铺中存在其它前缀或手工广告，不影响这一判断。再由 Approved 6-1 生成序列化 Desired State；Desired 中的缺失参数不能用旧报告默认值补造。
4. 程序按 Logical ID 对首次架构生成 `CREATE / NO_CHANGE`；仅对同一已批准 6-1 架构中、已有实体的必要参数差异生成受限 `UPDATE`。不再把 6-3 运行期决策映射为 6-2 动作。迁移/暂停候选仅报告，不直接 Delete/Archive/Pause。
5. 展示完整实体级差异和 Before/Desired/Action/Reason，取得用户对该精确 CREATE/UPDATE 清单的批准。6-1 批准本身不授权写入。
6. 使用 SellerSpace `prepare_change_plan` 预览，逐字段核对命中对象与批准 diff；完全一致后才 `apply_change_plan`。任何变更为 `TECHNICAL_EXECUTION_CONFLICT`，需重新审批。
7. 按 Campaign → Ad Group → Advertised Product/Target 顺序处理依赖。Apply 后按 Amazon ID Read-back 每个实体，核对父子关系、身份、Name、状态、Bid/Budget/Placement/策略和 Target 值。只有回读一致才可 `FULL_SUCCESS`。
8. 超时/部分成功先重查实时 Actual State，只生成恢复差异，不盲目重放。相同 6-1 RUN_ID + Desired State + Actual State 的第二次运行须 0 CREATE / 0 UPDATE。

广告写操作只有在用户批准精确差异后才能进行。`PAUSE_CANDIDATE`、`MIGRATION_CANDIDATE` 仅报告并交现有批准机制；不自动删除、归档、暂停或重命名。

## 输出与 Skill 边界

保留既有正式 6-2 HTML 版本命名和 0-2 索引。HTML 和必要的执行差异 CSV 应展示 6-1 Lineage、批准 Battle Units、BUILD/RECONCILE、控制方式、独立/共享数量、实体差异、失败、Read-back 与未解决项。追加式 ID/序号清单及广告运行日志存入 `广告表现汇报优化日志`，不进入 0-2 正式报告索引。字段见 [handoff-schema.md](references/handoff-schema.md)；报告结构见 [report-outline.md](templates/report-outline.md)。

不修改产品档案、原始数据或 Listing/价格/Coupon；不把 6-2 执行摘要当成 6-3/6-4 批准。6-3/6-4 只能消费已读回的真实对象与执行记录。Stage 6 日常链路固定为 `6-3 DATA → 6-4 DECIDE → 人工批准 → 6-5 APPLY → 下一轮 6-3/6-6`；新品初始广告链路固定为 `6-1 PLAN → 人工批准 → 6-2 BUILD`。

至少识别：`CAMPAIGN_SCOPE_NOT_CONFIGURED`、`CAMPAIGN_TAG_MISSING`、`CAMPAIGN_TAG_INVALID`、`CAMPAIGN_PREFIX_INVALID`、`NO_CAMPAIGN_MATCHED`、`RUNTIME_SCOPE_MISMATCH`、`SCOPE_CONTAMINATION`、`OUTSIDE_CAMPAIGN_SCOPE`，以及 `61_INPUT_NOT_FOUND`、`61_INPUT_RUN_MISMATCH`、`NO_APPROVED_BATTLE_PLAN`、`INVALID_APPROVAL_STATE`、`CONTROL_MODE_MISSING`、`INTENT_CODE_MISSING`、`BATTLE_UNIT_ID_MISSING`、`ROLE_TRANSLATION_AMBIGUOUS`、`SHARED_GROUP_INCOMPATIBLE`、`CAMPAIGN_IDENTITY_CONFLICT`、`ADGROUP_IDENTITY_CONFLICT`、`TARGET_IDENTITY_CONFLICT`、`DESIRED_STATE_INVALID`、`ACTUAL_STATE_QUERY_FAILED`、`CREATE_FAILED`、`UPDATE_FAILED`、`READBACK_FAILED`、`TECHNICAL_EXECUTION_CONFLICT`、`EXECUTION_NOT_READY`、`MIGRATION_REQUIRES_APPROVAL`。6-1 B 目标类型或目标值缺失/错配时，解析阶段返回 `6-1_TARGET_VALUE_INVALID`。

## 全局正式报告目录与命名规则

本 Skill 面向确定 Product Root 生成正式报告或结构化分析报告时，统一保存到 `06_SKILL分析报告/{Skill编号}_{Skill中文正式名称}/`，文件名使用 `{Skill编号}_{报告名称}_{YYYYMMDD_HHMMSS}.{ext}`；同一运行的配套正式资产共用时间戳。各 Skill 的机器运行包按自身契约保存；人类可见 HTML 统一在 Skill 根目录只保留一个最新文件，旧 HTML 归档到同级 `历史HTML/`。读取最新报告或运行包时按文件名/包内时间及有效性校验，不按文件修改时间选择。若 HTML 由同批 CSV 生成，必须从文件名时间戳相同的 CSV 读取并生成不可变快照；禁止运行时另找“最新 CSV”。未由 CSV 构成输入的 HTML 报告遵循对应 Skill 的原有报告内容逻辑。此规则优先于本文档中旧的目录和文件名示例。跨产品公共知识、提醒状态、决策登记簿和运行日志等持续业务数据按各自数据契约保存，不作为 Product Root 正式分析报告迁移。

## Human Report Publishing

本 Skill 生成正式 HTML 报告时，遵循统一的人类可见报告规则：Skill 报告根目录只保留一个当前最新 HTML；旧 HTML（以及同名 `.meta.json`）全部移动到同级 `历史HTML/`，不删除、不覆盖。一次性 Skill 的正式机器 CSV/JSON 只进入当前 Skill 报告目录的 `data/`，且只保留完整 `LATEST VALID` Batch；RunPackage/Manifest、metadata sidecar、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。HTML 仅按人类报告规则发布到根目录或 `历史HTML/`。完成写入、回读和校验后才发布当前报告；失败或不完整 Run 不得发布。公共实现与索引规则见 [`skills/references/human-report-publishing.md`](../references/human-report-publishing.md)。

## 全局报告文件治理（适用本 Skill）

本 Skill 遵循公共 `scripts/hzp_amz_report_contract.py`、[human-report-publishing.md](../references/human-report-publishing.md) 与 [report-governance.md](../references/report-governance.md)：正式机器业务数据只进入当前 Skill 报告目录的 `data/`，`data/` 只保留完整 `LATEST VALID` Batch；旧 VALID Batch 整包进入 `历史数据/<RUN_TIMESTAMP>/`。RunPackage/Manifest、metadata、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。新 Batch 必须先 Staging、验证完整性后再原子发布；失败不得替换旧 data。根目录只保留最新人类 HTML（如有）及正式子目录，机器数据不得写根目录。下游通过正式 Registry/Resolver 读取 `data/`，不得按 HTML 或根目录 mtime 选数。已有成熟时间戳 Run Package 的持续 Skill 可保留其内部运行包，但仍遵守根目录清洁和系统资产分层。
