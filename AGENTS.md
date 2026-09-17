# HZP-AMZ 项目协作规则

本仓库下所有对话和任务默认采用 `01 amazon/references/ai-brain/` 中的共享 AI Brain 规则。

## 对话方式

- 先给结论，再给核心逻辑；复杂比较使用表格。
- 明确区分 `FACT`、`DERIVED_FACT`、`AI_JUDGMENT`、`AI_REASON`、`UNKNOWN` 和 `ASSUMPTION`。
- 主动检查数据重复、职责重叠、上游重判、Scope 泄漏、版本混淆、重复创建/执行和更简单的替代方案。
- 不把不确定内容写成事实；缺失证据明确标记，不用 0、999 或猜测掩盖缺失。

## 实施方式

- 共享 Brain 只定义跨 Skill 稳定的思考方式；业务事实和业务逻辑仍由各 Skill Contract 与正式数据决定。
- AI 负责语义判断、经营判断、原因和反证；程序负责数学、Join、去重、筛选、聚合、Coverage、Schema、身份、时间、Latest 和 Read-back。
- 遵守 `UPSTREAM DECIDES → DOWNSTREAM CONSUMES → DO NOT RE-JUDGE`。
- 重要判断完成前执行 Decision Challenge，并保留 Reason Trace；连续经营 Skill 按 Contract 读取 Decision History。
- 优先增量修改现有实现，不建立平行基础设施，不改变已有 Ground Truth 或业务边界。

## 优先级

用户当前明确指令 > Skill Hard Contract > 当前 Ground Truth / Schema > 本仓库 Operating System > Domain Brain > Case Library > 通用模型知识。

共享 Brain 入口：`01 amazon/references/ai-brain/README.md`。
