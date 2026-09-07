# JasonSkill

这是个人 Skill 仓库。每个 Skill 使用独立目录保存，目录内包含 `SKILL.md`、中文 README、引用资料、模板、代理元数据和资源文件。当前仓库登记了以下 Skill。

## Skill 清单

| Skill | 目录 | 用途 |
|---|---|---|
| `hzp-amazon-product-market-research` | [`01 amazon/hzp-amazon-product-market-research`](01%20amazon/hzp-amazon-product-market-research/) | 分析 Amazon US 单个 ASIN 的 Keepa、Helium 10 Cerebro、Amazon Reviews 和公开商品页数据，输出证据可追溯的中文 HTML 选品与产品开发决策报告。 |

后续新增 Skill 时，在本 README 的清单中补充名称、目录和用途，并在对应目录中提供完整的 `SKILL.md` 与说明文件。

## hzp-amazon-product-market-research

### 解决的问题

这个 Skill 用于判断一个 Amazon US 产品方向是否值得继续开发，并回答：

- 基准 ASIN 真正卖的是什么；
- 市场需求、关键词和 H10 建议竞价如何表现；
- Keepa 历史趋势、真实评论和当前商品页分别说明了什么；
- 消费者问题可以转化为什么产品改进方向；
- Product Definition V1 应该如何定义；
- 哪些问题仍需要 QMT 和供应链验证。

### 输入

完整分析需要同一 ASIN 的三份核心文件：

1. Keepa 导出：`.xlsx`；
2. Helium 10 Cerebro 导出：`.csv` 或 `.xlsx`；
3. Amazon Reviews 导出：`.xlsx` 或 `.csv`。

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
- ASIN 不一致、核心文件缺失或页面重定向到其他 ASIN 时，按 Skill 规则停止或降级处理。

### 目录结构

```text
01 amazon/
└── hzp-amazon-product-market-research/
    ├── SKILL.md
    ├── README.md
    ├── agents/openai.yaml
    ├── assets/icon.svg
    ├── references/
    │   ├── amazon-page-data.md
    │   ├── data-field-mapping.md
    │   └── product-terms-guidance.md
    └── templates/
        ├── html-style-guide.md
        └── report-outline.md
```

### 调用与维护

调用某个 Skill 时，使用其目录中的 `SKILL.md` 作为入口。更新 `hzp-amazon-product-market-research` 时，以本仓库目录为主版本：

`E:\codex\JasonSkill\01 amazon\hzp-amazon-product-market-research`

更新完成后同步到 Codex 安装目录：

`C:\Users\qmhzp\.codex\skills\hzp-amazon-product-market-research`

同步后运行：

```powershell
python C:\Users\qmhzp\.codex\skills\.system\skill-creator\scripts\quick_validate.py `
  E:\codex\JasonSkill\01 amazon\hzp-amazon-product-market-research
```

确认校验通过后，再执行 Git 提交和 push。提交前不要把临时文件、分析报告或其他无关文件加入仓库。

### 相关说明

- Skill 详细规则：[`01 amazon/hzp-amazon-product-market-research/SKILL.md`](01%20amazon/hzp-amazon-product-market-research/SKILL.md)
- 中文使用说明：[`01 amazon/hzp-amazon-product-market-research/README.md`](01%20amazon/hzp-amazon-product-market-research/README.md)
- Amazon 页面协议：[`references/amazon-page-data.md`](01%20amazon/hzp-amazon-product-market-research/references/amazon-page-data.md)
- HTML 报告大纲：[`templates/report-outline.md`](01%20amazon/hzp-amazon-product-market-research/templates/report-outline.md)
- HTML 样式指南：[`templates/html-style-guide.md`](01%20amazon/hzp-amazon-product-market-research/templates/html-style-guide.md)
