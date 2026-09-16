# 6-0-6｜对标意图市场占领分析

Skill ID：`hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis`

606 将 601 的 Benchmark×Keyword 自然排名观察映射到 603 当前产品 Intent Tree，计算 Individual Organic Occupancy 与 Benchmark Consensus。它不代表销量/GMV份额，不决定 6-0-5 怎么打，也不写广告或 ERP。

先检查输入：

```powershell
python scripts/benchmark_intent_occupancy.py inspect --product-root "<Product Root>" --product-code B2
```

完成数据核对与 AI 定性判断后，按 [data-contract.md](references/data-contract.md) 编制 decisions JSON，再生成本次报告：

```powershell
python scripts/benchmark_intent_occupancy.py build --product-root "<Product Root>" --product-code B2 --decisions "<decisions.json>"
```

输出目录：`[Product Root]/06_SKILL分析报告/6-0-6_对标意图市场占领分析/`。两个 CSV 和 HTML 共用同一 RUN_ID、时间戳；旧文件保留。README、流程路由与 Skill 入口见仓库根目录 README。
