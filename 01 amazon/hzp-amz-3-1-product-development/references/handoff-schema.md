# 3-1 产品开发交接数据结构（JSON 兼容格式）

`3-1-[ProductCode]_product-handoff-vN-YYYYMMDD.json` 是 3-1 的可选机器可读兼容文件。标准 AI 接口是同目录的 `3-1-[ProductCode]_HANDOFF.md`，优先使用 [`../templates/handoff-template.md`](../templates/handoff-template.md)。两者只保存能够追溯到来源的事实、用户决定、开发假设和待验证项，不把推断写成事实。

## 必填字段

| 字段 | 含义 |
| --- | --- |
| `schema_version` | 交接结构版本，例如 `1.0` |
| `current_product_code` | 产品项目根目录 `PRODUCT.md` 中的当前 Product Code；它是跨员工、跨电脑、跨阶段的唯一产品身份和正式文件名识别信息；没有时停止生成正式交接文件 |
| `previous_product_code` | 可选的上一个 Product Code；产品编码迁移时保留，用于追溯旧文件和旧 HANDOFF |
| `product_code_history` | 可选的产品编码历史数组，按时间顺序记录曾用编码 |
| `current_stage` | 当前 Amazon 阶段，例如 `3-1` |
| `product_status` | `PRODUCT.md` 的生命周期状态：`ACTIVE`、`WAITING`、`HOLD`、`COMPLETED` 或 `CANCELLED`；不能用阶段 Decision 替代 |
| `handoff_version` | 当前 HANDOFF 的整数版本 |
| `handoff_status` | `CURRENT` 或 `SUPERSEDED`；当前文件必须为 `CURRENT` |
| `supersedes` | 被当前 HANDOFF 替代的旧版本或旧文件；没有时写 `null` |
| `exit_gate` | `READY FOR NEXT STAGE` 或 `NOT READY` |
| `product_id` | 旧版本兼容字段；可选，不再作为正式文件名或产品身份 |
| `product_code` | 旧版本可选字段；可保留内部子编码，但不覆盖 `current_product_code` |
| `asin` | 目标 ASIN；没有时写 `null` |
| `variation` | 颜色、尺寸或款式；未知时写 `null` |
| `marketplace` | 站点，例如 `Amazon US` |
| `source_report` | 上游市场研究报告的相对产品项目路径 |
| `source_handoff` | 上游 AI HANDOFF 的相对产品项目路径，例如 `2-1-market-research/2-1-[ProductCode]_HANDOFF.md`；没有时写 `null` |
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
  "current_product_code": "N24",
  "previous_product_code": null,
  "product_code_history": ["N24"],
  "current_stage": "3-1",
  "product_status": "ACTIVE",
  "handoff_version": 1,
  "handoff_status": "CURRENT",
  "supersedes": null,
  "exit_gate": "READY FOR NEXT STAGE",
  "product_id": null,
  "product_code": null,
  "asin": "B0FZRQDRYS",
  "variation": "Calacatta Viola / 13 x 6.3 x 13.2 in",
  "marketplace": "Amazon US",
  "source_report": "2-1-market-research/2-1-N24_产品市场分析报告.html",
  "source_handoff": "2-1-market-research/2-1-N24_HANDOFF.md",
  "decision": "CONDITIONAL GO",
  "customer_job": {
    "statement": "在台面上整理化妆品、香水或首饰，并获得稳定的展示与取用体验。",
      "evidence_label": "[FACT]"
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
      "evidence_label": "[FACT]",
      "acceptance_criteria": "待供应链/实验室确认",
      "validation_method": "开箱计时 + 跌落/振动测试",
      "status": "待验证"
    }
  ],
  "active_cross_stage_requirements": [
    {
      "id": "MR-001",
      "content": "外观不要做得太医疗化。",
      "author": "HZP",
      "date": "2026-09-08",
      "applies_to": ["3-1", "5-1"],
      "status": "ACTIVE",
      "evidence_label": "[MANUAL-REQ]"
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
      "label": "[TO-VERIFY]"
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
      "path": "2-1-market-research/2-1-N24_产品市场分析报告.html",
      "date": "YYYY-MM-DD",
      "use": "研究结论、评论和产品定义"
    }
  ]
}
```

## 使用规则

- `null` 或 `数据缺失` 表示缺失，不能用 0 替代。
- `current_product_code` 必须与 `PRODUCT.md` 的当前值一致，并用于所有 3-1 正式文件名；`previous_product_code` 和 `product_code_history` 用于编码迁移追溯。旧 `product_id` 只能作为兼容字段，不能替代当前 Product Code。
- `product_status` 必须使用 `PRODUCT.md` 的生命周期状态；`decision` 记录阶段结论，二者不能混用。
- `handoff_status` 为 `CURRENT` 的文件才是当前接口；`supersedes` 用于指向旧版本，不能根据 `final`、`最新` 等文件名猜测。
- `active_cross_stage_requirements` 只保留仍影响后续阶段的 `ACTIVE` / `TO-VERIFY` 人工要求，并使用 `[MANUAL-REQ]`；不得把整份 `MANUAL_REQUIREMENTS.md` 复制进来。
- `exit_gate` 必须明确为 `READY FOR NEXT STAGE` 或 `NOT READY`。
- `evidence_label` 使用 `[FACT]`、`[INFERENCE]`、`[TO-VERIFY]` 或 `[DECISION]`；不得把 `[INFERENCE]` 或 `[TO-VERIFY]` 自动升级为 `[FACT]`。
- `acceptance_criteria` 必须可观察；没有阈值时写明谁确认。
- `cost_inputs` 保留原币种和来源，不把投资试算图的模型利润写成实际利润。
- `sources` 至少包含上游报告和本次读取的关键文件。
- `source_report`、`source_handoff` 和 `sources.path` 只写相对于产品项目根目录的路径或裸文件名；禁止写入员工电脑的盘符、UNC、`/mnt/...` 或 `file:///...` 路径。
- 交接单只推动下一阶段工作，不授权下单、量产、联系供应商或修改线上账户。
