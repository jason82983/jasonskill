# JasonSkill

这是个人 Skill 仓库。每个 Skill 使用独立目录保存，目录内包含 `SKILL.md`、中文 README、引用资料、模板、代理元数据和资源文件。当前仓库登记了以下 Skill。

## Skill 清单

| Skill | 目录 | 用途 |
|---|---|---|
| `hzp-amz-0-1-product-file-structure` | [`01 amazon/hzp-amz-0-1-product-file-structure`](01%20amazon/hzp-amz-0-1-product-file-structure/) | 创建、检查和安全整理 Amazon 产品文件结构，保护原始证据并区分人工思路与 Skill 分析成果。 |
| `hzp-amz-2-1-market-research` | [`01 amazon/hzp-amz-2-1-market-research`](01%20amazon/hzp-amz-2-1-market-research/) | 分析 Amazon US 单个 ASIN 的 Keepa、Helium 10 Cerebro、Amazon Reviews、销量记录/预估表、投资回报试算图和公开商品页数据，输出证据可追溯的中文 HTML 选品与产品开发决策报告。 |
| `hzp-amz-3-1-product-development` | [`01 amazon/hzp-amz-3-1-product-development`](01%20amazon/hzp-amz-3-1-product-development/) | 优先读取 2-1 HANDOFF，把市场结论转成 Product Definition V2、产品需求规格书、打样与测试计划、质量验收标准和 3-1 HANDOFF。 |

后续新增 Skill 时，在本 README 的清单中补充名称、目录和用途，并在对应目录中提供完整的 `SKILL.md` 与说明文件。

## hzp-amz-0-1-product-file-structure

这个基础 Skill 负责 Products Root 和单个产品项目的目录结构管理。它支持 `CREATE`、`CHECK`、`ORGANIZE`、`MIGRATE` 四种模式：先识别 `00_产品公用数据` 和 Product Root，再以 `01_产品档案.md` 中的产品编号确认身份；公共定义只保存一份，产品证据按产品保存，真正生成的 Skill 成果放入 `06_SKILL分析报告`。迁移前必须先扫描和输出计划；发现重名、覆盖或数据丢失风险时停止。

详细规则：[`01 amazon/hzp-amz-0-1-product-file-structure/SKILL.md`](01%20amazon/hzp-amz-0-1-product-file-structure/SKILL.md)

中文说明：[`01 amazon/hzp-amz-0-1-product-file-structure/README.md`](01%20amazon/hzp-amz-0-1-product-file-structure/README.md)

## Amazon 产品目录共用规则

当前活动的 Amazon Skill 共用便携式产品项目协议：产品项目根目录由 `PRODUCT.md` 标识，Skill 从当前工作目录向上搜索该文件，不依赖员工电脑的盘符、固定根目录或上一次任务路径。找不到 `PRODUCT.md` 时必须停止并请用户选择或创建项目目录。

每个产品项目使用以下结构：

```text
<ProductRoot>/
├── PRODUCT.md
├── MANUAL_REQUIREMENTS.md       # 可选；跨阶段人工要求
├── DECISIONS.md                 # 可选；重要正式决策
├── 0-source/                    # 原始导出、图片、供应商资料、样品记录
├── 2-1-market-research/         # 2-1 正式报告与 HANDOFF
└── 3-1-product-development/     # 3-1 开发资料与 HANDOFF
```

未来 `4-production/`、`5-listing/`、`6-growth/`、`7-inventory/` 目录只在对应阶段实际使用时创建，不提前创建空目录。`PRODUCT.md` 中的 `Current Product Code` 是跨员工、跨电脑、跨阶段的规范产品身份和正式文件名标识，优先级高于 Product Name、别名和 ASIN；`Previous Product Code` 与 `Product Code History` 用于编码迁移追溯。已知 `N24` 表示新品项目阶段、`A7` 表示已确认的 A 店正式产品，未来编码格式保持开放。产品从 N24 转为 A7 时，旧 N24 文件保留，新输出统一使用 A7，并在 PRODUCT.md 和 HANDOFF 中保留历史。`Current Stage` 与生命周期 `Status` 分开；Status 只使用 `ACTIVE`、`WAITING`、`HOLD`、`COMPLETED`、`CANCELLED`，其中 `ACTIVE` 才是默认可推进状态，`WAITING` / `HOLD` 需要用户明确要求恢复。阶段决策 `GO / CONDITIONAL GO / NO-GO` 不替代生命周期 Status，Skill 不能擅自决定 `COMPLETED` 或 `CANCELLED`。可选的 `MANUAL_REQUIREMENTS.md` 只读取适用范围内的 `ACTIVE`、`TO-VERIFY` 要求，并使用 `[MANUAL-REQ]` 标记，不得当作 `[FACT]`。可选的 `DECISIONS.md` 只记录已确认的重要正式决策，不是日志或普通建议。2-1 从 `0-source/` 读取并写入 `2-1-market-research/`，3-1 优先读取 `2-1-market-research/2-1-[ProductCode]_HANDOFF.md`，再从 `0-source/` 核实，并写入 `3-1-product-development/`。报告、HANDOFF、JSON 和来源清单只能使用相对于产品项目根目录的路径或裸文件名。完整目录发现、路径安全和跨员工规则见两个活动 Skill 内的 `references/product-directory-contract.md`。
两个活动 Skill 都必须执行 Entry Gate 和 Exit Gate：2-1 的 Entry Gate 为 `READY TO ANALYZE` / `BLOCKED`，3-1 的 Entry Gate 为 `READY TO DEVELOP` / `BLOCKED`；阶段完成时统一写 `READY FOR NEXT STAGE` 或 `NOT READY`。HANDOFF 通过 `Version`、`Status: CURRENT`、`Supersedes` 和 `PRODUCT.md` 的 `Latest Handoff` 确认当前版本，不依赖 `final`、`最新` 等文件名。

## hzp-amz-2-1-market-research

### 解决的问题

这个 Skill 用于判断一个 Amazon US 产品方向是否值得继续开发，并回答：

- 基准 ASIN 真正卖的是什么；
- 市场需求、关键词和 H10 建议竞价如何表现；
- Keepa 历史趋势、真实评论和当前商品页分别说明了什么；
- 消费者问题可以转化为什么产品改进方向；
- Product Definition V1 应该如何定义；
- 哪些问题仍需要 QMT 和供应链验证。

### 输入

完整分析需要同一 ASIN 的五份产品文件：

1. Keepa 导出：`.xlsx`；
2. Helium 10 Cerebro 导出：`.csv` 或 `.xlsx`；
3. Amazon Reviews 导出：`.xlsx` 或 `.csv`。
4. 销量记录/销量预估表：`.xls`、`.xlsx`、`.csv`，或内容等价的制表数据；
5. 投资回报试算图：`.png`、`.jpg`、`.jpeg` 或 `.webp`。

五份文件校验通过后，Skill 会尝试读取对应的公开商品页：

`https://www.amazon.com/dp/{ASIN}`

销量表可以是按日期记录的销量或来源方估算；投资试算图是场景模型。二者会分别标记 `文件范围内计算` 和 `试算模型`，不等于实际利润或已实现回报。

核心文件 ASIN 校验通过后，Skill 会尝试读取公开商品页：

`https://www.amazon.com/dp/{ASIN}`

商品页用于补充当前标题、品牌、展示价格、评分区、卖点、规格、变体和可见履约信息。页面被拦截、无法确认身份或字段未显示时，报告标记 `Amazon 页面补充缺失`，不编造数据。

### 输出

默认生成自包含的中文 HTML 决策报告，内容包括：

- `GO / CONDITIONAL GO / NO-GO` 决策；
- Keepa 价格、BSR、评分和季节性趋势；
- Cerebro 需求簇与代表关键词；
- H10 原始建议竞价、最低竞价和最高竞价；
- Amazon 当前商品页快照与 page/file 冲突；
- 销量记录日期范围、7/14/30 天文件范围内汇总、零/非零销量天数和同期价格/BSR/评分；
- 投资试算图的手动输入、场景假设和自动计算结果，并保留币种、单位和图片定位；
- 真实评价英文短摘录、中文翻译和开发启示；
- 消费者问题到产品改进的开发矩阵；
- Product Definition V1；
- 风险、未知项和 QMT 会议问题；
- 来源文件、日期、页面状态和数据限制。

### 证据规则

- 区分 `数据支持`、`分析推断` 和 `待供应链验证`；
- 页面快照、Keepa 历史值、Cerebro 估计和 Reviews 样本分开记录；
- 不从 BSR 推算销量，不从售价推算利润；
- 不估算缺失 H10 竞价，不把 H10 建议竞价写成实际 CPC、ACOS 或利润；
- 评价必须来自单条真实评论，不合并、编造或伪造引文；
- 页面和文件冲突并列展示来源与时间，不静默覆盖或平均；
- 页面只做公开、只读访问，不登录、不绕过验证码、不读取私有数据；
- 销量记录、试算模型和历史/页面数据不互相覆盖，冲突时显示来源、日期和口径；
- ASIN 不一致、必需产品文件缺失或页面重定向到其他 ASIN 时，按 Skill 规则停止或降级处理。

### 目录结构

```text
01 amazon/
├── hzp-amz-2-1-market-research/
└── hzp-amz-3-1-product-development/
    ├── SKILL.md
    ├── README.md
    ├── agents/openai.yaml
    ├── references/handoff-schema.md
    └── templates/handoff-template.md
```

研究 Skill 的目录结构：

```text
hzp-amz-2-1-market-research/
    ├── SKILL.md
    ├── README.md
    ├── agents/openai.yaml
    ├── assets/icon.svg
    ├── references/
    │   ├── amazon-page-data.md
    │   ├── secondary-inputs.md
    │   ├── data-field-mapping.md
    │   └── product-terms-guidance.md
    └── templates/
        ├── html-style-guide.md
        └── report-outline.md
```

### 调用与维护

调用某个 Skill 时，使用其目录中的 `SKILL.md` 作为入口。更新 `hzp-amz-2-1-market-research` 或 `hzp-amz-3-1-product-development` 时，以当前 Git 仓库的 `<repo-root>/01 amazon/<skill-name>` 为主版本，按需同步到本机 Codex 安装目录 `<CODEX_HOME>/skills/<skill-name>`（未设置 `CODEX_HOME` 时使用用户的 `.codex/skills`）。产品项目目录不参与这条安装路径规则。

同步后，在当前环境中运行：

```powershell
$skillCreator = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME 'skills\.system\skill-creator\scripts\quick_validate.py' } else { Join-Path $HOME '.codex\skills\.system\skill-creator\scripts\quick_validate.py' }
python $skillCreator '<repo-root>\01 amazon\hzp-amz-2-1-market-research'
```

确认校验通过后，再执行 Git 提交和 push。提交前不要把临时文件、分析报告或其他无关文件加入仓库。

### 相关说明

- Skill 详细规则：[`01 amazon/hzp-amz-2-1-market-research/SKILL.md`](01%20amazon/hzp-amz-2-1-market-research/SKILL.md)
- 中文使用说明：[`01 amazon/hzp-amz-2-1-market-research/README.md`](01%20amazon/hzp-amz-2-1-market-research/README.md)
- Amazon 页面协议：[`references/amazon-page-data.md`](01%20amazon/hzp-amz-2-1-market-research/references/amazon-page-data.md)
- 销量与投资回报协议：[`references/secondary-inputs.md`](01%20amazon/hzp-amz-2-1-market-research/references/secondary-inputs.md)
- HTML 报告大纲：[`templates/report-outline.md`](01%20amazon/hzp-amz-2-1-market-research/templates/report-outline.md)
- HTML 样式指南：[`templates/html-style-guide.md`](01%20amazon/hzp-amz-2-1-market-research/templates/html-style-guide.md)

### hzp-amz-3-1-product-development

这个 Skill 优先接收同一产品项目 `2-1-market-research/2-1-[ProductCode]_HANDOFF.md`，再结合产品市场研究报告、Product Definition V1、评论痛点、样品和供应链资料，输出到 `3-1-product-development/`：Product Definition V2、需求规格书、样品与测试计划、质量验收标准、开发变更记录和 3-1 HANDOFF。

- Skill 详细规则：[`01 amazon/hzp-amz-3-1-product-development/SKILL.md`](01%20amazon/hzp-amz-3-1-product-development/SKILL.md)
- 中文使用说明：[`01 amazon/hzp-amz-3-1-product-development/README.md`](01%20amazon/hzp-amz-3-1-product-development/README.md)
- 交接字段结构：[`references/handoff-schema.md`](01%20amazon/hzp-amz-3-1-product-development/references/handoff-schema.md)
- HANDOFF 模板：[`templates/handoff-template.md`](01%20amazon/hzp-amz-3-1-product-development/templates/handoff-template.md)
