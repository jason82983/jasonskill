# HZP Amazon 0-3｜Amazon经营日历与预警

0-3 用来回答：未来哪些 Amazon 经营节点、产品季节窗口或 Launch 时间，如果现在不提醒，之后可能来不及。

## 快速使用

- 全局经营预报：`0-3`
- 某个产品：`0-3，P001`
- 某个节点：`0-3，Christmas`
- 未来窗口：`0-3，未来90天`

提供 Products Root；产品模式再提供产品编号。Skill 会自动定位 Product Root，读取产品档案和已有资料，计算季节/Launch 倒排，输出 P0/P1/P2/P3/INFO 预警，并建议下一步调用的专业 Skill。

## 它负责什么

Amazon US 节日和销售节点日历、Season Start/Peak Window、开发→生产→运输→FBA→Cold Start 倒排、新品 Launch 时间提醒、每日预报、提醒去重和 Skill 路由。

它不做专业市场、广告、页面、库存或产品设计分析，也不修改 Amazon、广告、Listing、库存、Coupon 或 Promotion。SellerSpace（如接入）只读，禁止 `apply_change_plan`。

## 资料与输出

季节和产品参数优先使用真实产品资料；没有可靠参数时使用可配置默认值并标注 `[系统默认规划参数]`，未知信息标 `[数据不足]`。高频预报默认写入：

`[Product Root]\06_SKILL分析报告\Amazon经营预报\`

该目录只保存 Markdown/JSON 等高频预报和状态，不是正式报告目录，因此不进入 0-2 索引。用户明确要求正式 HTML 时才写入 `06_SKILL分析报告\` 根目录并按报告型 Skill 约定调用 0-2。0-2 仍是唯一的 `06_SKILL分析报告\index.html` 维护者，0-3 不生成索引。详细字段和模板见 `SKILL.md`、`references/` 和 `templates/`。
