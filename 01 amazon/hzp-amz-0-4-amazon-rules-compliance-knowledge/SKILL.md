---
name: hzp-amz-0-4-amazon-rules-compliance-knowledge
description: 查询、核验并沉淀 Amazon US 平台规则、FBA要求、产品合规与官方帮助知识；按来源和时效区分平台规则、美国法规、物流要求与公司经验。
---

# HZP Amazon 0-4｜Amazon规则、合规与官方知识

0-4 是 HZP Amazon 的公共规则与知识入口。用户输入“0-4，问题”即可查询 Amazon 平台规则、FBA/包装、产品合规、类目准入、广告规则、账户店铺、官方帮助或跨境合规边界；也可以复用已沉淀的专项知识。它不替代 2-1/2-2 的市场判断、3 阶段的产品开发或其他专业 Skill 的业务决策。

## 知识根目录

固定根目录：`[Products Root]/00_公共资料/01_Amazon平台资料/日常知识【0-4】/`。该目录是公司公共知识，不放入具体 Product Root、`06_SKILL分析报告` 或 0-2 产品报告索引。首次使用时若不存在，可创建 `index.html` 和十个分类目录：`01_Amazon平台规则`、`02_Listing与页面`、`03_FBA物流与包装`、`04_产品合规与认证`、`05_类目准入与限制`、`06_广告规则`、`07_账户与店铺`、`08_官方帮助与操作`、`09_出口税务与跨境`、`10_其他`。

Products Root 必须由当前会话提供或由可靠配置确定，不依赖固定盘符。

## 运行规则

1. 解析问题类型和适用 Marketplace；优先读取知识根目录已有条目和 `index.html`，按 `knowledge_id`、主题和关键词去重。
2. 根据 `last_verified_at`、`change_risk` 和规则易变程度，决定只读本地知识还是重新核验官方资料。
3. 需要联网时优先 Amazon Seller Central Help、Amazon Ads Documentation、Seller University、Amazon公告；涉及美国法律/监管时查询对应政府机构，并保留具体可点击 URL。
4. 统一证据状态：`[官方已确认]`、`[法规已确认]`、`[多官方来源确认]`、`[部分确认]`、`[历史规律参考]`、`[公司经验]`、`[AI推断]`、`[待确认]`、`[可能已过期]`、`[官方资料存在冲突]`、`[无法可靠确认]`。不得把 AI 推断写成官方要求。
5. 严格分开【Amazon平台要求】、【美国法律/监管要求】、【物流/FBA要求】和【HZP公司经验/内部标准】。来源冲突时并列展示来源、日期、差异和核验建议。

## 即时问题与专项知识

简单的一次性操作问题直接回答，不强制生成 HTML。具有长期复用价值、影响多个产品/Skill、规则复杂或风险较高的问题，生成专项知识报告，并在元数据中写入 `knowledge_id`、`title`、`marketplace`、`category`、`keywords`、`status`、`change_risk`、`last_verified_at`、`version`、`source_types`、`affected_skills`、`affected_product_types`、`report_path` 和 `superseded_by`。

专项报告保存到知识根目录的分类子目录，建议命名：`Amazon_US_[主题]_V[版本]_[YYYYMMDD].html`。顶部和底部提供相对路径“← 返回日常知识首页”，首页不添加返回自身按钮；官方来源必须可点击，需登录的页面标记 `[需要 Seller Central 登录]`。

同一主题再次查询时，先判断是否只是重新核验。无实质变化则更新核验日期和索引元数据，避免重复报告；规则实质变化或原报告错误时保留历史，生成新版本并用 `superseded_by` 标记旧条目 `[已被新版替代]`。`change_risk` 使用 `HIGH/MEDIUM/LOW`，易变的 Title、FBA箱规、广告后台和活动规则通常为 HIGH，但必须结合实际来源判断。

## 产品专项合规

收到“0-4，产品代码，这个产品有什么合规要求？”时，只读当前 Product Root 的 `01_产品档案.md`、`07_产品资料` 和必要的最新有效报告，识别材质、电池、儿童/电气属性、使用环境、Claim 和包装。事实不足时输出 `[产品事实不足，无法完整判断合规要求]` 并列出缺失项；不修改产品档案或产品资料，不承诺“绝对合规”。风险等级使用 `LOW/MEDIUM/HIGH/CRITICAL` 并说明理由。

## 边界与衔接

其他 Skill 需要规则时，优先查询 0-4，不能复制易变规则。0-4 可向 2-1、2-2、3-1、4-2、5-1/5-2/5-4、6-1、7 阶段提供规则查询结果，但不替它们做产品、市场、广告或补货决策。0-3 可读取 0-4 元数据形成经营日历提醒；V1 不建立自动监控平台。

默认只读：不修改 Amazon、SellerSpace、产品原始资料或历史产品报告，不调用广告写操作。0-4 知识报告不进入 0-2。

按需读取：
- [references/workflow.md](references/workflow.md)：问题分类、来源核验、状态和去重流程；
- [references/knowledge-schema.md](references/knowledge-schema.md)：知识元数据与索引接口；
- [templates/knowledge-report-outline.md](templates/knowledge-report-outline.md)：专项 HTML 章节模板；
- [templates/knowledge-entry.json](templates/knowledge-entry.json)：知识条目元数据模板；
- `scripts/build_index.py`：重建 0-4 知识首页；
- [references/test-cases.md](references/test-cases.md)：V1行为核对。

## 全局正式报告目录与命名规则

只要本次任务针对一个确定的 Product Root 并生成正式分析报告/结构化分析结果，就保存到 `06_SKILL分析报告/{Skill编号}_{Skill中文正式名称}/`，文件名为 `{Skill编号}_{报表名称}_{YYYYMMDD_HHMMSS}.{ext}`；同一运行的配套文件共用时间戳。跨产品通用的知识库、提醒状态和决策登记簿属于持续维护的业务数据，不作为产品分析报告迁入报告目录。历史报告不自动搬迁或删除。

## Shared AI Brain

本 Skill 遵守仓库共享 AI Brain：`../references/ai-brain/README.md`。运行时按 `context-manifest.md` 声明 GLOBAL、DOMAIN、UPSTREAM、HISTORY、FORBIDDEN；本 Skill 的业务 Contract、正式 Ground Truth 和职责边界优先于泛化推理。AI Judgment 必须区分 Evidence 类型，重要判断先执行 Decision Challenge，再由 Reason Trace 生成原因；程序确定的数学、Join、去重、筛选、聚合、Schema、Identity、Timestamp、Latest 和 Read-back 不交给 AI 计算。
