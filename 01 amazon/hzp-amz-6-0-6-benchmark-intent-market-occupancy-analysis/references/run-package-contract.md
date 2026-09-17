# 6-0-6 Run Package and Data Contract

## Identity and lineage

Skill ID: hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis

Output root: Product Root/06_SKILL分析报告/6-0-6_对标意图市场占领分析/

Write each run directly under the fixed 6-0-6 output root; do not create a timestamp subfolder. Create one `RUN_TIMESTAMP` per run and reuse it in all three formal output filenames and `run_manifest_{RUN_TIMESTAMP}.json`. Refuse to overwrite any file belonging to an existing timestamped run.

The timestamped manifest in the fixed output root records at least:

- SkillId, Current Product, RUN_ID, RUN_TIMESTAMP, GeneratedAt
- 602 Input Run ID, 602 Input Timestamp, 602 Input Folder, 602 Benchmark D Input Files and per-file record counts
- 603 Input Run ID, 603 Input Timestamp, 603 Input Folder, 603 Input Files
- Benchmark Count, Benchmark Codes, Benchmark ASINs
- Input Keyword Count, Input Intent Count
- Output Folder, Output Files, Output Record Counts, Run Status
- Validation.Missing Organic Rank Audit, Validation.No 602 High-Precision Observation Audit, and Failure when applicable

RUNNING and FAILED packages are never latest-valid inputs. A package is valid only after all CSV and HTML files are written, read back, validated and declared with Run Status=VALID. Preserve prior timestamped files and manifests.

## Output A schema

Exact ordered headers:

1. 对标编码
2. 对标ASIN
3. 精准泛词
4. 中文
5. 层级
6. 父精准泛词
7. 汇总搜索量
8. 有效排名词数
9. Top10关键词数
10. Top20关键词数
11. Top50关键词数
12. Top100关键词数
13. 平均自然排名
14. 加权自然排名
15. Top10占领搜索量
16. Top10搜索量覆盖率
17. Top20占领搜索量
18. Top20搜索量覆盖率
19. Top50占领搜索量
20. Top50搜索量覆盖率
21. Top100占领搜索量
22. Top100搜索量覆盖率
23. 占领等级
24. 占领判断原因

One row represents one Benchmark × one 603 Intent. Materialize zero-evidence rows. Counts are integer strings; rates are percent strings to four decimal places, or DATA_NOT_AVAILABLE when the denominator is zero. Average and weighted rank retain four decimal places. Volume/rank values are program generated.

## Output B schema

Exact ordered headers:

1. 精准泛词
2. 中文
3. 层级
4. 父精准泛词
5. 汇总搜索量
6. 对标总数
7. 有效覆盖对标数
8. 核心占领对标数
9. 强占领对标数
10. 核心/强占领对标数
11. 最佳对标编码
12. 最佳对标ASIN
13. 最佳Top20搜索量覆盖率
14. Top20覆盖率中位数
15. Top50覆盖率中位数
16. 多对标共识等级
17. 共识判断原因

One row represents one Intent. Rebuild all numeric fields from OUTPUT A. Calculate best Benchmark by Top20 rate descending, then Top10 rate descending, weighted rank ascending, and Benchmark Code ascending. Do not sum coverage across Benchmarks. A one-Benchmark run uses grade 单对标模式.

## Judgment input for finalize

The LLM creates this JSON only after reading the deterministic evidence returned by prepare. It must not alter numeric evidence.

    {
      "individual": [
        {
          "benchmark_code": "CODE",
          "intent": "Intent name",
          "grade": "核心占领",
          "reason": "Concise explanation grounded in the precomputed row."
        }
      ],
      "consensus": [
        {
          "intent": "Intent name",
          "grade": "高共识",
          "reason": "Concise explanation grounded in precomputed consensus evidence."
        }
      ]
    }

There must be exactly one individual entry for each Benchmark × Intent pair and one consensus entry for every Intent. Individual grade must be 核心占领, 强占领, 中度占领, or 弱占领. For a single Benchmark, the engine ignores the submitted consensus grade and writes 单对标模式.

## HTML

The renderer receives OUTPUT A and OUTPUT B after UTF-8-with-BOM readback. It embeds a JSON snapshot from those rows in the report and makes no network request. The report sections are:

1. Executive Summary
2. Benchmark Overview
3. Search Intent Occupancy Matrix
4. Benchmark Core Intent Positions
5. Multi-Benchmark High Consensus
6. Single-Point Validation
7. Parent / Child Occupancy
8. Top Search Demand Control
9. Weak / White Space Evidence
10. Reality Evidence for 6-1
11. Sources and Boundaries

The fixed A/B schemas contain Intent-level aggregates, not keyword-level rows. Therefore section 8 ranks high-demand Intents and displays per-Benchmark Top10/Top20 keyword counts, occupancy volume and rates. It must not claim to list individual keyword names. Section 1 reports effective Benchmark × Intent ranked observations, explicitly indicating that Parent subtree inclusion repeats descendant evidence; it cannot claim the upstream raw unique keyword count from A/B alone.

## Error codes and stop conditions

- 606_INPUT_NOT_FOUND: no current-product complete valid manifest package or formal input file was found.
- 606_INPUT_RUN_MISMATCH: declared run, folder, or file timestamps do not agree; 603 files differ in run/folder.
- 606_INPUT_SCHEMA_INVALID: an input header order/profile is incompatible or the Intent tree is invalid.
- 606_INPUT_EMPTY: a required input asset has no records.
- BENCHMARK_IDENTITY_MISSING: code or ASIN missing, or one code resolves to conflicting ASINs.
- BENCHMARK_OBSERVATION_JOIN_FAILED: a 602 D asset Id has no 603 mapping or keyword identity differs.
- INTENT_MAPPING_MISSING: a mapped record has no valid 603 Primary Intent.
- DUPLICATE_BENCHMARK_OBSERVATION: same normalized keyword/Id appears twice for one Benchmark.
- MISSING_ORGANIC_RANK: allowed null, recorded in the data-quality audit, never coerced to 999.
- NO_602_HIGH_PRECISION_OBSERVATION: a 603 Id has no observation row for a particular Benchmark; record it in the manifest audit and keep its counts/occupied volume at zero for that Benchmark.
- INVALID_ORGANIC_RANK: nonblank rank cannot be parsed as a positive number; reject analysis.
- MISSING_MARKET_CAPACITY: 602 D asset or mapped 603 market capacity is empty, invalid, or negative.
- OCCUPANCY_MONOTONICITY_FAILED: TopN volume/rate nesting or 100% ceiling fails.
- INTENT_VOLUME_MISMATCH: input capacity or TopN occupied volume conflicts with the 603 Intent denominator.
- CONSENSUS_SOURCE_MISMATCH: OUTPUT B math/coverage or consensus judgment does not reconcile to OUTPUT A.
- 606_RUN_PACKAGE_INCOMPLETE: one of the three formal outputs is missing, unreadable, wrong-schema, or invalid.
- 606_TIMESTAMP_MISMATCH: manifest or formal output timestamp differs from this run.
- HTML_DATA_RECONCILIATION_FAILED: HTML is not a same-run, self-contained snapshot from OUTPUT A/B.

## Latest valid 606 package

Scan only this Product's 6-0-6 output root. Sort `run_manifest_{RUN_TIMESTAMP}.json` candidates by timestamp descending and accept the first complete package whose manifest has the exact SkillId, Current Product, matching RUN_TIMESTAMP, Run Status=VALID, and whose declared output list is exactly:

- 对标意图市场占领明细_{RUN_TIMESTAMP}.csv
- 意图多对标占领共识_{RUN_TIMESTAMP}.csv
- 对标意图市场占领分析报告_{RUN_TIMESTAMP}.html

Validate both CSV headers and HTML presence before returning. Provide all outputs from that manifest's report root and with that same timestamp. The manifest output filenames are intentionally compatible with the existing 6-1 resolver.

## Upstream compatibility note

The 6-0-2 producer package supplies one high-precision D asset per Benchmark, while 6-0-3 supplies the multi-Benchmark Intent mapping. For 602, delegate package selection to `resolve_latest_valid_602_run_package()` in 6-0-3 and require all three shared assets plus every expected D file, matching timestamp, identities, schemas, sidecars and record counts. Skip invalid or incomplete batches and fall back to the newest complete VALID batch. Never read 601 files directly, select loose CSVs, or infer missing Benchmark facts.

For 6-0-3, resolve the newest producer-valid manifest-backed package by manifest timestamp. Require matching SkillId, Current Product, RUN_TIMESTAMP, Run Status, Output Folder, input lineage, exact two-file declaration, same-root timestamped CSVs, schemas, record counts, unique Ids, and Intent coverage. Skip failed or incomplete packages and fall back to the prior complete valid package. After selecting the newest valid package, enforce this Skill's multi-Benchmark mapping schema; if that valid package has the single-Benchmark profile, stop with `606_INPUT_SCHEMA_INVALID` instead of silently switching to an older run.
