# 产品开发交接数据结构

`product-handoff-vN-YYYYMMDD.json` 是市场研究与产品开发之间的机器可读交接单。它只保存能够追溯到来源的事实、用户决定、开发假设和待验证项，不把推断写成事实。

## 必填字段

| 字段 | 含义 |
| --- | --- |
| `schema_version` | 交接结构版本，例如 `1.0` |
| `product_code` | 产品编码；没有时写 `null` |
| `asin` | 目标 ASIN；没有时写 `null` |
| `variation` | 颜色、尺寸或款式；未知时写 `null` |
| `marketplace` | 站点，例如 `Amazon US` |
| `source_report` | 上游市场研究报告路径 |
| `decision` | `GO`、`CONDITIONAL GO`、`NO-GO` 或 `未决定` |
| `customer_job` | 用户要完成的核心任务 |
| `non_goals` | 本次开发明确不做的范围 |
| `requirements` | 带优先级、标签和验收方式的需求数组 |
| `prototype_hypotheses` | 每个样品版本要验证的假设 |
| `tests` | 测试方法、样本量、阈值和结果 |
| `cost_inputs` | 已知成本、币种、来源和缺失字段 |
| `open_decisions` | 需要用户、QMT、供应链或实验室确认的事项 |
| `sources` | 文件名、路径、日期和用途 |

## 推荐结构

```json
{
  "schema_version": "1.0",
  "product_code": "N24",
  "asin": "B0FZRQDRYS",
  "variation": "Calacatta Viola / 13 x 6.3 x 13.2 in",
  "marketplace": "Amazon US",
  "source_report": "<absolute-or-relative-report-path>",
  "decision": "CONDITIONAL GO",
  "customer_job": {
    "statement": "在台面上整理化妆品、香水或首饰，并获得稳定的展示与取用体验。",
    "evidence_label": "资料事实"
  },
  "non_goals": [
    "不在本版本承诺自动化收纳或其他未验证功能"
  ],
  "requirements": [
    {
      "id": "REQ-P0-001",
      "priority": "P0",
      "category": "packaging",
      "statement": "开箱时可无工具取出保护材料，且结构关键部位不因运输破损。",
      "evidence_label": "资料事实",
      "acceptance_criteria": "待供应链/实验室确认",
      "validation_method": "开箱计时 + 跌落/振动测试",
      "status": "待验证"
    }
  ],
  "prototype_hypotheses": [
    {
      "version": "V1-A",
      "hypothesis": "改用可拆解缓冲结构可以降低破损和退货风险。",
      "variables": ["缓冲材料", "边角保护", "拆包路径"],
      "decision_gate": "改版后再测"
    }
  ],
  "tests": [
    {
      "test_id": "TEST-001",
      "requirement_ids": ["REQ-P0-001"],
      "method": "待确认",
      "sample_size": null,
      "pass_threshold": "待确认",
      "owner": "待确认",
      "result": "未测试",
      "retest_rule": "不通过时修正包装并重新测试"
    }
  ],
  "cost_inputs": [
    {
      "name": "产品成本",
      "value": null,
      "currency": "CNY",
      "source": "待供应商报价",
      "label": "待验证"
    }
  ],
  "open_decisions": [
    {
      "question": "实重、包装尺寸、FBA费用和破损上限是多少？",
      "owner": "QMT/供应链",
      "gate": "继续打样前"
    }
  ],
  "sources": [
    {
      "name": "产品市场研究报告",
      "path": "<report-path>",
      "date": "YYYY-MM-DD",
      "use": "研究结论、评论和产品定义"
    }
  ]
}
```

## 使用规则

- `null` 或 `数据缺失` 表示缺失，不能用 0 替代。
- `acceptance_criteria` 必须可观察；没有阈值时写明谁确认。
- `cost_inputs` 保留原币种和来源，不把投资试算图的模型利润写成实际利润。
- `sources` 至少包含上游报告和本次读取的关键文件。
- 交接单只推动下一阶段工作，不授权下单、量产、联系供应商或修改线上账户。
