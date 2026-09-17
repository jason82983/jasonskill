# HZP-AMZ AI Brain

这是 HZP-AMZ 的共享智能决策层，不是新的业务 Skill。它定义跨产品、跨 Skill 稳定的判断方式；当前产品事实、输入输出 Schema 和职责边界仍以对应 Skill Contract 与正式数据为准。

## 统一流水线

```text
REAL DATA
→ Evidence Builder
→ Hard Constraints
→ Domain Brain
→ Reasoning Procedure
→ Initial Judgment
→ Decision Challenge
→ Final Judgment
→ Reason Trace
→ Validation
→ Final Output
```

## 模块

| 模块 | 文件 | 用途 |
|---|---|---|
| Operating System | `operating-system.md` | 跨 Skill 长期经营原则 |
| Evidence Contract | `evidence-contract.md` | Evidence 类型、缺失和追溯 |
| Domain Brains | `domain-brains.md` | Precision、Intent、Market、Benchmark、Launch、Ads |
| Decision Challenge | `decision-challenge.md` | Final Judgment 前反证检查 |
| Reason Trace | `reason-trace.md` | 判断、证据、反证和下一条件 |
| Decision History | `decision-history.md` | 连续运行的历史决策链 |
| Context Manifest | `context-manifest.md` | 每个 Skill 的允许读取边界 |
| Manifest Index | `context-manifest-index.md` | 全部 hzp-amz Skill 的最小读取边界 |
| Case Library | `case-library.md` | 可复用反例和正确推理方向 |
| Version | `VERSION` | Brain 版本和变更入口 |

## 边界

Brain 不保存当前产品、ASIN、搜索量、Bid、Campaign ID 或其它运行事实；这些必须来自当前 Product Root、正式报告、API 或 Skill 输入包。Brain 版本变化不自动重写业务 Skill。
