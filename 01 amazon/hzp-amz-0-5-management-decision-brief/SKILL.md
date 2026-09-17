---
name: hzp-amz-0-5-management-decision-brief
description: 发现 Amazon 经营链路中真正需要上级方向、资本、资源、风险或继续/停止决策的问题，生成增量式中文决策周报、A/B/C/D问询、Decision Register 和执行路由；不替代专业 Skill 作日常操作或最终老板决策。
---
# HZP Amazon 0-5｜上级决策与经营问询

0-5 是 Management Decision Radar + Boss Question Generator + Decision Register：从上次成功周报之后发生的事实中，筛选真正需要上级决断的事项，先给 AI 推荐，再记录老板原始回答、执行路由和后续结果。默认手动运行或由外部 Scheduler 每周触发；Skill 不假装拥有后台定时能力。

## 运行入口
`0-5`、`0-5，B2`、`0-5，待决策`、`0-5，已决策`。先提供 `Products Root`，再定位 `[Products Root]/00_公共资料/02_公司标准/上级决策【0-5】/`；公司级资料不放入产品报告，也不进入 0-2。

## 核心流程
1. 读取 `checkpoint.json` 的 `last_successful_brief_at`；扫描窗口为 `(Previous Successful Brief Timestamp, Current Brief Timestamp]`。首次运行明确标记 `[首次运行]`，只读取近期重大变化和当前未决事项。
2. 按 references/evidence-and-filtering.md 读取 0-3、0-4、1–7 阶段当前产品的最新版有效正式报告、产品档案、人工思路、运行日志和异常证据。文件/接口数字必须带来源、窗口和口径。
3. 用 `[FACT]`、`[INFERENCE]`、`[TO-VERIFY]`、`[DECISION]` 区分事实、推断、待核验和已确认决定；AI推算标记 `[AI推算]`。
4. 只升级战略方向、资本分配、重大风险接受、资源/优先级、重大产品决定、时间临界、跨系统冲突、继续/停止事项。普通 Bid、Keyword、图片文案、否词和已有 SOP 可解决事项不问老板。
5. 先按 Decision Topic 和已有 `decision_id` 去重。未回答事项更新证据与紧迫度；已回答事项只有 Material New Evidence 才 `REOPENED` 并说明原因。
6. 每个问题生成 Question、Why Now、Facts、What Changed Since Last Brief、A/B/C/D 选项、AI Recommendation、Reason、Expected Upside、Main Downside、Cost/Capital Impact、Deadline、If No Decision、Affected Product/Project、Affected Skills、Evidence Confidence。主周报默认 ≤5 项，所有 P0 必须显示，其余进入 Secondary Queue。
7. 生成中文《HZP Amazon 上级决策周报》HTML。成功写入后才推进 checkpoint；失败不得推进。老板回答原意写入 Decision Register，并路由给 6-2/6-3、3-2/3-3、5 阶段或 7-1/7-2，0-5 不越权执行。

## Decision Inbox｜日常决策候选收件箱

日常对话中的问题、担忧、想法、抱怨、机会和风险，先作为 `Decision Candidate` 进入公司级 `decision_inbox.json`，不自动升级为正式老板问题。支持 `0-5，记一下：原话`，也允许上层 Chat/Agent 在用户明确表达经营问题时写入。

Candidate 至少保存：`candidate_id`、`created_at`、`source_type`、`source_context`、`original_user_statement`、`ai_interpretation`、`potential_decision_topic`、`decision_level`、`related_product_codes`、`related_projects`、`related_skills`、`why_it_may_matter`、`current_evidence`、`missing_evidence`、`suggested_review_time`、`status`。`original_user_statement` 必须保留原话；AI 解释必须单独标记 `[AI推测的决策候选]`。

候选分类包括 `PRODUCT`、`PROJECT`、`COMPANY`、`POLICY`、`CAPITAL`、`RESOURCE`、`RISK`、`STRATEGY`。状态为 `DRAFT`、`WATCHING`、`READY_FOR_DECISION`、`DISMISSED`、`MERGED`。每周周报除增量扫描系统证据外，还要复查新增候选和重要 `WATCHING` 候选：证据成熟、时间临近、资本/风险增加、团队被卡住或方向已影响执行时升级为正式 Decision；否则继续观察。重复 Candidate 与已有 Candidate/Decision/Policy 合并并保留新证据和时间戳。

周报增加《本周观察中的管理问题》，只展示少量重要 `WATCHING` 候选，不要求老板回答。多个产品出现同类问题时，优先提炼为公司级或制度级候选；老板明确形成的制度决定，保留原话后才可标记 `[可沉淀为公司经营规则]` 并生成 Policy Candidate。普通知识问答、一次性小问题、普通操作、纯技术问题和无后续价值的抱怨不进入 Inbox。

## 与 0-3 / 0-4 边界
0-3 回答“什么时候注意什么”，发现时间风险可提供 0-5 候选；0-4 回答规则和合规边界，涉及禁止事项时先读取 0-4，只呈现合法选项；0-5 只回答“现在有哪些事情必须让老板给方向”。

## 输出
`[Products Root]/00_公共资料/02_公司标准/上级决策【0-5】/` 下保存 `index.html`、`decision_register.json`、`checkpoint.json` 和 `weekly/Weekly_Decision_Brief_YYYYMMDD.html`。没有重大事项必须输出 `[本周暂无需要上级决断的重大事项]`。

## 安全边界
默认只读并写入公司级 0-5 管理资料。禁止修改 Amazon、SellerSpace、产品原始资料、历史正式报告或映射表；不调用广告写操作或 `apply_change_plan`；不 commit/push。

详见 references/decision-schema.md、references/integration-routing.md、references/test-cases.md、references/candidate-inbox.md 和 templates/weekly-brief-outline.md。

