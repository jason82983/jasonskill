# 6-0-6｜对标意图市场占领分析

Skill ID：`hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis`

606 从 LATEST VALID 602 Batch 读取全部 `6-0-2_{所属产品编号}_高度精准词_{RUN_TIMESTAMP}.csv` D 资产，并从最新完整有效的 `6-0-3_RunPackage_{RUN_TIMESTAMP}.json` 读取同一 Run 的两张 603 表。602 Batch 必须包含 3 张公共表和每个预期对标一张 D 表；失败或不完整的新批次会跳过并回退最近完整 VALID Batch。603 通过共享 RunPackage 校验，失败或不完整的新包也会回退。606 不再直接读取 601 报表。它计算 Individual Organic Occupancy 与 Benchmark Consensus，不代表销量/GMV份额，不决定 6-1 怎么打，也不写广告或 ERP。

先检查输入：

```powershell
python scripts/benchmark_intent_occupancy.py inspect --product-root "<Product Root>" --product-code B2
```

完成数据核对与 AI 定性判断后，按 [data-contract.md](references/data-contract.md) 编制 decisions JSON，再生成本次报告：

```powershell
python scripts/benchmark_intent_occupancy.py build --product-root "<Product Root>" --product-code B2 --decisions "<decisions.json>"
```

输出目录：`[Product Root]/06_SKILL分析报告/6-0-6_对标意图市场占领分析/`。两个 CSV 和 HTML 共用同一 RUN_ID、时间戳；旧文件保留。README、流程路由与 Skill 入口见仓库根目录 README。
