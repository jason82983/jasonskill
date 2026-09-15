# Evidence-Gated Keyword Expansion｜证据驱动扩词

> 责任边界：6-0-1 提供双轨精准词资产，6-0-2 负责 Search Intent 和精准泛词；本参考只描述 6-3 如何把已交接的结构化建议转为需审批的广告扩词提案。

## 共同原则

Keyword Mother Pool 是去重、清洗和证据标注后的候选全集，不是广告创建清单。每个关键词保留来源、来源 ASIN、日期、Search Volume、Organic/Sponsored Rank、H10 或 SellerSpace Bid/Range、相关性、购买意图、Semantic/Purchase Intent Cluster、成熟度和 release_status。

Cluster 由真实关键词语义和购买意图动态生成，不使用固定示例。Cluster 字段至少包括 `cluster_id`、名称、意图、词数、代表词、data_sources、search_volume_evidence、ranking_evidence、bid_evidence、own_conversion_evidence、benchmark_evidence、relevance、current_maturity、release_status。

## 6-1 首批释放

6-1 从母词池选择 Initial Validation Batch，按 COR-EXA、EXP-PHR、DIS-BRO、DIS-AUT、COM-ASI 等实际角色建立初始架构。Broad 只接收高相关探索 Seed。未释放词保留 `HELD_FOR_EXPANSION`、`WAITING_CLUSTER_VALIDATION`、`LOW_PRIORITY`、`INSUFFICIENT_EVIDENCE` 或 `DO_NOT_LAUNCH`，并交接给 6-3。

## 6-3 后续扩词

6-3 只有在多个相关 Search Terms 重复成交或其他综合证据支持 Cluster 从 `INITIAL_SIGNAL` 升级 `VALIDATED` 时，才回查该 Cluster 的 Held Keywords。每次生成独立 Expansion Batch，自动选择 Exact/Phrase/Broad，进行 Traffic Overlap Check，联动 Bid、Campaign、Added Budget、库存、Season Window 和 Capital Release。不得一次释放全部剩余词。

扩词提案至少包含：Validated Cluster、Evidence、Current Released Keywords、Mother Pool Remaining、AI Selected New Keywords、Match Type、Bid、Current/Added/New Daily Budget、Expected Purpose、Main Risk、Validation Window、Stop Condition、A/B/C/D 决策。用户批准后才可执行写入。

## 证据与状态

关键词成熟度：`DISCOVERED`、`CANDIDATE`、`FIRST_ORDER_VALIDATED`、`REPEATED_CONVERSION_VALIDATED`、`CORE_CANDIDATE`、`CORE_CONVERTING`、`CORE_RANKING`、`ORGANIC_ASSET`。

Cluster 成熟度：`UNTESTED`、`TESTING`、`INITIAL_SIGNAL`、`VALIDATED`、`SCALING`、`MATURE`、`FAILED`、`PAUSED`。1 Click/1 Order 只能是首单验证，不能释放整个 Cluster。Own Product 真实成交证据优先于 H10/Benchmark 推断，但不同来源必须保留。


## CASE A-L 静态模拟契约

- CASE A：Cerebro 有 500 词 → 建立 Mother Pool，不创建 500 Targets。
- CASE B：首批只有少量高置信词 → 允许小批验证。
- CASE C：1 Click/1 Order → 仅 `FIRST_ORDER_VALIDATED`，不释放整个 Cluster。
- CASE D：同 Cluster 多个相关词重复成交 → 可升级 `VALIDATED`。
- CASE E：Validated Cluster 剩余词 → AI 筛选 Expansion Batch，不全量释放。
- CASE F：新增词需要流量 → 同时给 Added/Recommended Expansion Budget。
- CASE G：库存不足 → 不机械扩大关键词资本释放。
- CASE H：外围扩词变差 → 收缩外围，保留核心 Cluster。
- CASE I：Auto 出现新成交 Search Term → 以 `Source=OWN_SEARCH_TERM` 加入 Mother Pool。
- CASE J：H10 与 Own Product 冲突 → Own 真实成交证据优先，保留冲突记录。
- CASE K：用户批准完整 Expansion Proposal → prepare、比对、一致后 apply、Read-Back Verification。
- CASE L：用户未批准 → 绝不执行写操作。
