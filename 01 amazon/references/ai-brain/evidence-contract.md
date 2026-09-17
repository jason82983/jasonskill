# Evidence Contract

| 类型 | 含义 |
|---|---|
| `FACT` | ERP、API、正式 CSV、产品档案或平台真实数据原值 |
| `DERIVED_FACT` | 程序确定计算的供需比、机会比、Coverage、Weighted Rank、ACoS、CVR 等 |
| `AI_JUDGMENT` | 高度精准、首攻、占领等级、保持/调整等判断 |
| `AI_REASON` | 支撑判断的解释和因果边界 |
| `UNKNOWN` | 正式数据源无法提供或无法确认 |
| `ASSUMPTION` | Contract 明确允许的假设，必须显式标注 |

禁止 AI Judgment 伪装 Fact。缺失值保持 `UNKNOWN`，不得用 0、999 或估算掩盖缺失。重要判断应记录 Evidence Source、Timestamp、Source Skill、Run/Batch/File/API 和 Record Identity。
