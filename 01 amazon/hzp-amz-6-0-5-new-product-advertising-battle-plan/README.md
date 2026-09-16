# HZP Amazon 6-0-5｜新品广告作战规划

6-0-5 从 6-0-3 最新有效的同次 Intent Summary 与 Keyword Mapping 中形成新品作战规划。AI决定首攻、任务、阶段、投放方式及控制方式（独立/共享/不投）；程序确保全量词覆盖、字段血缘、控制方式透传、稳定 Intent Code、稳定 Battle Unit ID，并生成三张待审批 CSV 和 Dashboard。

## 运行

```powershell
python scripts/battle_plan.py inspect --product-root "<Product Root>" --product-code B2
python scripts/battle_plan.py build --product-root "<Product Root>" --product-code B2 --variant-code M --decisions "<decisions.json>"
```

`inspect` 返回 Resolver 实际选中的 6-0-3 文件与数据。Codex 依据输入进行经营判断，将每个 Intent 和每个 Keyword 的决定按 [plan contract](references/plan-contract.md) 写入一次性 decisions JSON，再调用 `build`。没有真实 6-0-3 的同 RUN_ID 两份输入、缺失决策、覆盖或Schema不一致时停止。示例命令不代表已运行任何真实产品。

输出位于 `[Product Root]/06_SKILL分析报告/6-0-5_新品广告作战规划/`，每次有独立 `YYYYMMDD_HHMMSS`，不覆盖历史。所有状态初始 `PROPOSED`。本 Skill 无 Amazon Ads / ERP 写入功能。

Stage 6 顺序：`6-0-3 → 6-0-5 PLAN → 人工审批 → 6-1 APPLY`。6-1 使用共享 `scripts/new_product_battle_plan_contract.py` 解析已批准同Run资产，并逐字透传控制方式：独立含 Intent Code、共享不含 Intent Code、不投不创建；6-1不得重判或改写该经营决策，并仍遵守自身的广告创建审批、身份和读回机制。
