# Decision Register 字段与生命周期

字段至少包括：`decision_id, created_at, product_code, project, question, priority, options, ai_recommendation, boss_answer, boss_comment, answered_at, decision_status, deadline, affected_skills, execution_owner, follow_up_date, result, reopened_reason`。

状态：`NEW → WAITING_DECISION → ANSWERED → EXECUTION_PENDING → IN_EXECUTION → RESOLVED`；也可 `DEFERRED`、`CANCELLED`、`REOPENED`。老板回答原意保存，AI执行理解单独记录。

同一 Decision Topic 沿用原 decision_id；已回答问题只有 Material New Evidence 才 REOPENED，并填写 reopened_reason。
