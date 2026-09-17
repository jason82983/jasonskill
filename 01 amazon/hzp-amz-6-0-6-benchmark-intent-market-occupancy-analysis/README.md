# 6-0-6｜对标意图市场占领分析

Skill ID：`hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis`

606 从 602 `data/` 目录读取全部 `6-0-2_{所属产品编号}_高度精准词_{YYYYMMDD_HHMMSS}.csv` D 资产，并从 603 `data/` 目录读取同一文件名时间戳的两张表；按最大文件名时间戳选最新输入并做最小 Schema 校验，不依赖 RunPackage、manifest、sidecar 或文件修改时间。606 计算 Individual Organic Occupancy 与 Benchmark Consensus，不代表销量/GMV份额，不决定 6-1 怎么打，也不写广告或 ERP。

先检查输入：

```powershell
python scripts/benchmark_intent_occupancy.py inspect --product-root "<Product Root>" --product-code B2
```

完成数据核对与 AI 定性判断后，按 [data-contract.md](references/data-contract.md) 编制 decisions JSON，再生成本次报告：

```powershell
python scripts/benchmark_intent_occupancy.py build --product-root "<Product Root>" --product-code B2 --decisions "<decisions.json>"
```

输出目录：`[Product Root]/06_SKILL分析报告/6-0-6_对标意图市场占领分析/`。两个 CSV 和 HTML 共用同一 RUN_ID、时间戳；旧文件保留。README、流程路由与 Skill 入口见仓库根目录 README。

`简化取数规则（增量 Patch）`：分析型上游输入固定从指定 Skill 的 `data/` 目录读取，按完整 Report Identity 文件名中的 `YYYYMMDD_HHMMSS` 选择最大时间戳，进行最小 Schema 校验；不依赖 RunPackage、manifest、sidecar 或文件修改时间。
