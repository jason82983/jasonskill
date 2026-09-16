# 6-0-6 数据、输出与判断契约

## 输入 Schema

601 `BENCHMARK_KEYWORD_DETAIL`：`Id,词,中文,市场容量,竞争产品数,供需比,对标编号,对标ASIN,自然排名`。其中`对标编号`是档案中的 ERP 数字编号；6-0-6 用 601 metadata 中的 ASIN→ERP 编号与 Benchmark 身份映射恢复内部关联。601 Observation 汇总 CSV 不含`对标编码`，保留`对标编号`。

603 `PRECISION_BROAD_SUMMARY`：`精准泛词,中文,层级,父精准泛词,直接搜索量,汇总搜索量,平均竞品数,意图机会比,直接对应词数`。

603 `PRECISION_BROAD_MAPPING`：`Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准泛词,精准泛词中文`。

Current Product identity is the requested Product_Code and Product Root in each artifact's shared metadata. `Id` is stable unique KwId. 601 facts for the same Id must agree across all Benchmark observations and with 603 mapping facts. Rank observations join only on `(Id, 对标编码)`; verify that each code resolves to exactly one ASIN. Every 603 Id must exist in the 601 unique market-fact set. 603 direct and subtree capacities must reproduce its summary values.

## Outputs

### A. Individual Occupancy CSV — fixed 24 columns

`对标编码,对标ASIN,精准泛词,中文,层级,父精准泛词,汇总搜索量,有效排名词数,Top10关键词数,Top20关键词数,Top50关键词数,Top100关键词数,平均自然排名,加权自然排名,Top10占领搜索量,Top10搜索量覆盖率,Top20占领搜索量,Top20搜索量覆盖率,Top50占领搜索量,Top50搜索量覆盖率,Top100占领搜索量,Top100搜索量覆盖率,占领等级,占领判断原因`

### B. Consensus CSV — fixed 17 columns

`精准泛词,中文,层级,父精准泛词,汇总搜索量,对标总数,有效覆盖对标数,核心占领对标数,强占领对标数,核心/强占领对标数,最佳对标编码,最佳对标ASIN,最佳Top20搜索量覆盖率,Top20覆盖率中位数,Top50覆盖率中位数,多对标共识等级,共识判断原因`

Percentages are ratios from 0 to 1 in CSV with four fractional digits; counts and Market Capacity retain integer semantics. Rank AVG and weighted rank use Decimal arithmetic rounded to four digits. Empty/unavailable means `DATA_NOT_AVAILABLE`, never 999 or a fabricated value. Top thresholds are inclusive and cumulative.

Each Keyword's Market Capacity is counted once per Benchmark×Intent Subtree. Parent aggregates include all descendants; child aggregates are calculated independently. Do not sum across levels or Benchmarks. Intent denominator is copied from 603 `汇总搜索量`, checked against unique Subtree Keyword Market Capacity.

## Decisions JSON

Program-generated `inspect` output includes exact required keys. Supply:

```json
{
  "occupancy_decisions": [
    {"对标编码":"BENCH_A","精准泛词":"canonical intent","占领等级":"中度占领","占领判断原因":"结合该意图需求、有效覆盖及排名深度的简短解释。"}
  ],
  "consensus_decisions": [
    {"精准泛词":"canonical intent","多对标共识等级":"高共识","共识判断原因":"解释跨对标一致性和竞争成熟度边界。"}
  ]
}
```

Occupancy labels: `核心占领/强占领/中度占领/弱占领`. Consensus labels: `高共识/中共识/低共识/单点验证`; in a one-Benchmark run omit consensus decisions and the program enforces `单对标模式` with a fixed explanation. Reasons are mandatory and must be evidence-specific. AI receives calculated evidence from `inspect` JSON; it must not calculate or alter numeric values. No fixed weighted score or mechanical single-metric label mapping is allowed.

Guidance: assess whether the Benchmark controls meaningful head demand or only has a few deep ranks, using the full depth and coverage profile plus the Parent/Child role. `核心占领` requires evidence that the intent is a notable organic territory for that Benchmark; `强占领` means clearly established coverage/depth; `中度占领` means genuine but limited head/high-value control; `弱占领` means relatively shallow/deep-only or small observed coverage. Compare cross-Benchmark similarity, strength spread, valid coverage and per-Benchmark judgments for Consensus. These are qualitative guardrails, not numeric thresholds or a weighted score. A rank alone cannot decide either label.

`TopN搜索量覆盖率` and related ratio fields are numeric ratios from 0 to 1 in CSV. HTML renders them as percentages. CSV percentages are never summed across Benchmarks.

## HTML modules

1. Executive Summary; 2. Benchmark Overview; 3. Search Intent Occupancy Matrix; 4. Benchmark Core Territories; 5. Multi-Benchmark High Consensus; 6. Single-Point Validation; 7. Parent/Child Occupancy; 8. Top Search Demand Control; 9. Weak/White Space Evidence; 10. 6-0-5 Reality Evidence; 11. Sources and Limits.

“高共识”不表示低竞争。Weak/White Space 仅表示在这些 Benchmark 中相对薄弱或尚未验证充分。Reality Evidence may inform, never set 6-0-5's launch task or priority.

## Output identities and lineage

A uses Report Identity `BENCHMARK_INTENT_OCCUPANCY_DETAIL`; B uses `BENCHMARK_INTENT_OCCUPANCY_CONSENSUS`; HTML uses `BENCHMARK_INTENT_OCCUPANCY_REPORT`. All sidecars share 606 RUN_ID/RUN_TIMESTAMP and record Current Product, the chosen 601 report, both same-run 603 assets, Benchmark count/code/ASIN list, input counts, and resolution method.

## Integrity and error codes

Hard failure codes: `606_INPUT_NOT_FOUND`, `606_INPUT_RUN_MISMATCH`, `606_INPUT_SCHEMA_INVALID`, `606_INPUT_EMPTY`, `BENCHMARK_IDENTITY_MISSING`, `BENCHMARK_OBSERVATION_JOIN_FAILED`, `INTENT_MAPPING_MISSING`, `DUPLICATE_BENCHMARK_OBSERVATION`, `INVALID_INTENT_TREE`, `MISSING_MARKET_CAPACITY`, `INTENT_VOLUME_MISMATCH`, `CONSENSUS_SOURCE_MISMATCH`, `OCCUPANCY_MONOTONICITY_FAILED`, `DECISION_COVERAGE_MISMATCH`, `BEST_BENCHMARK_TIEBREAK_MISMATCH`.

Rank data-quality statuses: `MISSING_ORGANIC_RANK`, `INVALID_ORGANIC_RANK`. These rows are never treated as rank 999 or included in rank metrics; an output with such issues is `INCOMPLETE`, not `FULL_SUCCESS`. No observation row is separately listed as `NO_601_OBSERVATION` in the HTML audit; it does not create an invented Rank.

Other invariant checks: one Market Fact per Id; one observation per Id×Benchmark; Top10≤Top20≤Top50≤Top100 count/volume/rate; no combined Benchmark coverage; Consensus aggregates reconstruct from A; best Benchmark tie-break is Top20 rate DESC, Top10 rate DESC, weighted rank ASC, Benchmark Code ASC.
