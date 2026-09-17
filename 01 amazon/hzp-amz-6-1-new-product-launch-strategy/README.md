# HZP Amazon 6-1｜新品推广方案

**正式英文名称：** New Product Launch Strategy
**Skill ID：** `hzp-amz-6-1-new-product-launch-strategy`
**职责关系：** 6-0-5 = PLAN；6-1 = 初始架构 BUILD；6-4 = 日常优化 APPLY。

6-1 只把最新有效、同 RUN_ID、已批准的 6-0-5 作战计划转换为 Amazon Campaign / Ad Group / Advertised Product / Target Desired State。它实时读取 Amazon Ads 状态，按稳定 Logical ID 初始化架构并处理同一已批准计划下的必要差异，在用户批准精确写入差异后执行、Read-back 和审计。6-1 不重新决定意图、目标词、任务、阶段、投放方式、控制方式或预算战略，也不执行 6-3 日常优化决策；运行期获批修改由 6-4 执行。

## 输入与执行门

从当前产品 Product Root 读取 605 同 RUN_ID 的 A 意图市场作战表、B 关键词作战明细、C 关键词阶段规划表和正式报告。当前解析器只接受 605 Latest Valid Approved Bundle。仅 `APPROVED + 当前允许阶段（当前为 PHASE_1）+ 控制方式不是不投` 的 Battle Units 可以进入 Desired State；没有可执行批准单元则停止。

默认 Products Root 为 `E:\【所有产品目录专用】\`。执行前必须从中央映射表与共享身份解析规则核实 Product/Variant/Own ASIN/SKU/Store/Marketplace/Portfolio，并通过实时 SellerSpace 查询确认 Actual State。Own ASIN、Benchmark ASIN、Product Target ASIN 分开处理；Benchmark ASIN 不得作为 Advertised Product。

## 控制方式与架构

- **独立**：以 605 Intent Code 作为独立 Campaign 控制边界；该 Code 必须进入 Campaign Name。
- **共享**：Intent Code 不进入 Campaign Name；只合并技术角色、Target 类型、阶段、Budget、Placement 等参数兼容的执行单元。
- **不投**：不生成 Campaign、Ad Group 或 Target。

Campaign 命名：`{ProductCode}.{CampaignTag}.{AdType}-{Role}-{TargetType}-[IntentCode]-{Seq}`，例如 `B2.M.SP-EXP-PHR-01`。运行先读取 `04_产品推广思路.md` 中的 `ProductCode`、`CampaignTag`、`CampaignPrefix`，并核对 `B2.M.` 这类前缀。前缀只作广告识别范围和 BUILD/RECONCILE 判断，不代表 Variant；真实 Variant 继续经身份映射解析，和 CampaignTag 分开保存。仅统计、匹配和判断该前缀开头的 Campaign，其他广告完全排除。当前仅执行已验证支持的 AdType；序号通过产品级追加身份清单稳定预留；已有 Campaign 不自动改名。

共享设置不兼容时返回 605 修订，不静默改变控制方式或拆改计划。当前 605 B Schema 若未提供 Product Target/Category Target 的准确 Target Value，6-1 必须停止相关单元，不可猜测。

多个 Benchmark 不复制广告架构；同一 Keyword 的市场事实只贡献一次，任何 Target 仍须由 6-0-5 明确批准。

## 安全执行

每次实时查询后生成完整 Before/Desired/Diff。未经用户针对精确 CREATE/UPDATE 差异确认，不调用 SellerSpace `apply_change_plan`。通过 `prepare_change_plan` 预览并精确核对后才能 Apply；然后按 Amazon ID Read-back。相同批准 Run 与 Desired State 重跑应产生零写入。迁移、暂停、删除或归档候选只报告，不自动执行。日常流程为 `6-2 DATA → 6-3 DECIDE → 人工批准 → 6-4 APPLY`；6-1 不再 APPLY AGAIN。

详情见 [SKILL.md](SKILL.md)、[approved-battle-plan.md](references/approved-battle-plan.md) 与 [execution-reconciliation.md](references/execution-reconciliation.md)。本仓库测试只使用合成计划和 Mock Provider，不连接真实 Amazon/SellerSpace 数据。
