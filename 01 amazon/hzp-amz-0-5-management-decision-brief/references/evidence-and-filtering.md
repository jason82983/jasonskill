# 证据与筛选规则

- 时间窗口严格为 `(last_successful_brief_at, current_brief_at]`；首次运行标记 `[首次运行]`，失败不推进 checkpoint。
- `[FACT]` 是文件、接口或人工确认直接支持；`[INFERENCE]` 是分析推断；`[TO-VERIFY]` 需新证据；`[DECISION]` 是老板确认。AI 推算必须标记 `[AI推算]`。
- 只有战略方向、资本、重大风险、资源/优先级、重大产品、时间临界、跨系统冲突、继续/停止才进入雷达。P0 立即决策，P1 本周，P2 近期，P3 观察，INFO 仅知悉。
