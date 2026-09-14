# Decision Inbox 规则

## 入口

支持 `0-5，记一下：原始表达`。Chat/Agent 也可在用户明确表达经营问题、担忧、方向或风险时写入，但宁可少记录，不把所有聊天变成管理问题。

## ID 与字段

Candidate ID 使用 `CAN-YYYY-0001`，按年度递增。保留 `original_user_statement` 原话；`ai_interpretation` 必须标记 `[AI推测的决策候选]`。分类：PRODUCT、PROJECT、COMPANY、POLICY、CAPITAL、RESOURCE、RISK、STRATEGY。

## 状态

`DRAFT`：信息不完整；`WATCHING`：继续观察；`READY_FOR_DECISION`：证据成熟，可建立正式 Decision；`DISMISSED`：已解决或不再重要；`MERGED`：与现有 Candidate/Decision/Policy 合并。

## 每周复查

复查上次成功周报后新增/变化的候选，以及重要历史 WATCHING。只有证据成熟、时间临近、资本或风险增加、团队被卡住或方向已影响执行时升级。重复项保留新证据和时间戳，不新建 ID。

多个产品反复出现同类问题时，优先升级为 COMPANY/POLICY 候选。老板明确决定后，原话进入 Decision Register；AI 只能另写执行解释，确认后才生成 Policy Candidate。
