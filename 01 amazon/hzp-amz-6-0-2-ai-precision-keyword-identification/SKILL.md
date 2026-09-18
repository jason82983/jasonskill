---
name: hzp-amz-6-0-2-ai-precision-keyword-identification
description: Judge every canonical keyword from the latest formal 6-0-1 benchmark observations against one current Amazon product, then publish complete four-level precision CSV and HTML assets for 6-0-3 and 6-0-6. Use for `6-0-2 {ProductCode}`; never query ERP, execute ads, or use a local heuristic precision judge.
---

# 6-0-2｜AI精准关键词识别

## INVOCATION CONTRACT

The only normal invocation is:

`6-0-2 {Product_Code}`

`Product_Code` is the complete task input. The caller must not provide a batch number,
offset, checkpoint, partial range, or "continue" instruction. Once invoked, the Agent
owns the task through final publication and must keep executing until the completion
criteria below are satisfied. A successful internal batch is never a user-facing
completion state, and the Agent must not ask the user to call the Skill again for the
next batch.

## GOAL

`6-0-2 {ProductCode}` means one complete business task:

`Current Product + latest formal 6-0-1 observations → one validated Product Profile → canonical unique keywords → AI judges every unique keyword once → deterministic observation backfill and configured filtering → four formal output classes → readback validation → COMPLETE`.

Do not report completion while any input unique keyword lacks a valid judgment or any output fails reconciliation. The task boundary is the business goal, not a configured batch size. The only normal loop condition is `PendingJudgmentCount > 0`; after each internal batch, validate and save progress, recompute the pending count, and immediately take the next batch. When the count reaches zero, run final reconciliation, publish, and read back all formal assets in the same invocation.

## INPUTS

Only these three business inputs are allowed:

1. `[Product Root]/05_分析源数据/01_产品数据/本产品/产品识别 - 文本文案.txt`
2. Latest filename-timestamped `6-0-1_05_所有对标自然排名关键词_*.csv` under `[Product Root]/06_SKILL分析报告/6-0-1_对标自然排名关键词提取/`
3. `E:\【所有产品目录专用】\01_公共资料\03_系统配置\生成精准词库的要求.txt`

Read `E:\【所有产品目录专用】\01_公共资料\03_系统配置\602_AI批次大小.txt` only as `PreferredBatchSize`. It is an internal throughput parameter, not a business input, task boundary, user interaction point, run-count limit, or completion limit. For each iteration use `CurrentBatchSize = min(PreferredBatchSize, PendingJudgmentCount)`; if a batch fails, reduce it and retry, then continue the same task after success. Never stop normally because one batch was prepared, saved, retried, or checkpointed.

Use `scripts/precision_keyword.py` for deterministic location, parsing, canonicalization, validation, derivation, output, sequence allocation and archival. The resolver uses exact Report Identity, filename timestamp and minimum schema validation. It must not use mtime, manifest, RunPackage, latest JSON or fuzzy filename guessing.

## GROUND TRUTH

Read the complete product text once and form one runtime Product Profile for the whole task. Understand at least:

`ProductType, PhysicalProductForm, CoreFunctions, PrimaryPurchaseDriver, SecondaryPurchaseDrivers, CorePurchaseMission, TargetAudience, Recipient, RelationshipIntent, GiftMission, PurchaseOccasions, Material, Theme, Style, UseCases, CriticalAttributes, Compatibility, InstallationMethod, ExplicitExclusions`.

Use `DATA_NOT_AVAILABLE` when evidence is absent and `NOT_APPLICABLE` when a field does not apply. Do not manufacture product facts. Do not create a formal Product Profile JSON by default.

The judgment grain is exactly:

`ONE CURRENT PRODUCT × ONE 6-0-1 KEYWORD Id × ONE CANONICAL KEYWORD = ONE PRECISION JUDGMENT`.

The stable 6-0-1 `Id` is the canonical record identity. Canonical text normalizes case, Unicode width and whitespace, but must not merge different `Id` values because their Market Facts may differ. Multiple Benchmark observations for the same `Id` share one judgment. The program backfills it to every observation.

## PRECISION RULES

Before judging, read [references/precision-guide.md](references/precision-guide.md).

For every canonical keyword, reconstruct the searcher's dominant purchase mission and answer:

> 搜索这个 Keyword 的人真正想完成什么购买任务？Current Product 是不是这个购买任务的合理购买答案？

Judge in this order:

1. Searcher Purchase Mission.
2. Hard Conflict Gate. Check product type, relationship, recipient, brand, personalization, material/feature, compatibility and theme conflicts before grading strength. A clear hard conflict is a veto and normally yields `不精准`; related tokens, gift fit, product-form match and Benchmark rank cannot override it.
3. Current Product Answer Role: `NATURAL_CORE_ANSWER`, `REASONABLE_ANSWER`, `ONE_OF_MANY_POSSIBLE_ANSWERS` or `NOT_A_VALID_ANSWER`.
4. Purchase Mission Convergence.
5. Initial Precision.
6. Benchmark Reality as supporting evidence only.
7. Decision Challenge.
8. FinalPrecision and keyword-specific ShortReason.

`FinalPrecision` must be exactly one of:

- `高度精准`
- `精准`
- `弱精准`
- `不精准`

Hard rule: `RELEVANCE != PRECISION`. Token overlap, search volume and organic rank cannot replace purchase-mission judgment. Hard conflicts cannot be overridden by related tokens or Benchmark rank. A product being usable as a gift is not sufficient for Selected admission when the query is broad.

`高度精准` requires all of the following: a clear core purchase mission, high convergence with the Current Product core mission, `NATURAL_CORE_ANSWER`, and no hard conflict. Before assigning it, ask: “Would many ordinary products in this broad category satisfy this query just as naturally?” If yes, use `精准` or `弱精准` instead.

`精准` is reserved for a clearly matching mission where the product is a `REASONABLE_ANSWER` and the search space is somewhat broader. `ONE_OF_MANY_POSSIBLE_ANSWERS` is normally `弱精准`; `NOT_A_VALID_ANSWER` is `不精准`.

The current Codex Agent is the precision judge. Python has no precision authority. Do not use regex, token matching, keyword contains, fixed scores, local heuristics, a callback AI, Codex CLI, API gateway, Queue or Production Checkpoint as the normal path.

## OUTPUT CONTRACT

Write every formal output directly to:

`[Product Root]/06_SKILL分析报告/6-0-2_AI精准关键词识别/`

One complete run shares one three-digit `RunSequence` and one `YYYYMMDD_HHMMSS` timestamp:

1. `6-0-2_{RunSequence}_精准判断所有词表_{Timestamp}.csv` — one row per Benchmark observation; all four levels retained.
2. `6-0-2_{RunSequence}_去对标去重_筛选后的精准词_{Timestamp}.csv` — configured levels only; one row per canonical keyword; this is the sole 6-0-3 input identity `UNIQUE_SELECTED_PRECISION_KEYWORDS`.
3. `6-0-2_{RunSequence}_{所属产品编号}_筛选后的精准词_{Timestamp}.csv` — configured levels only; canonical-deduplicated within each Benchmark; these are the 6-0-6 Benchmark input identity `BENCHMARK_SELECTED_PRECISION_KEYWORDS`.
4. `6-0-2_{RunSequence}_AI精准关键词识别_{Timestamp}.html` — human-readable report.

Normalize configuration alias `已精准` to `精准`. The configuration selects library membership only; it never changes `FinalPrecision`.

`RunSequence` is the maximum legal sequence found in the report root, `历史数据/`, and `历史html/`, plus one. It advances only for a complete formal run. Before publishing a new validated run, archive the prior root CSV files to `历史数据/` and prior root HTML to `历史html/`. Preserve historical files and never delete product evidence, 6-0-1, ERP data, or 6-0-3/6-0-6 reports.

Do not emit RunPackage, manifest, meta, latest, status, runtime, CLI or checkpoint JSON as formal assets.

## AVAILABLE DETERMINISTIC TOOLS

Import functions from `scripts/precision_keyword.py`:

- `locate_inputs()` and `load_product_text()`
- `load_601()` and `prepare_unique_keyword_evidence()`
- `read_preferred_batch_size()`
- `validate_ai_judgments()`
- `read_precision_selection_config()`
- `build_all_observation_output()`
- `build_dedup_selected_output()`
- `build_benchmark_selected_outputs()`
- `allocate_run_sequence()` and `archive_previous_run()`
- `publish_complete_run()` and `validate_outputs()`

These tools only perform deterministic work. The Agent may internally divide a dynamic `N` into safe batches, but must continue in the same invocation until every canonical keyword has one valid AI judgment before publication. `N` is discovered at runtime; never assume 3267, 5000, or any other fixed size. Checkpoints, if used by the runtime, only protect resumability and never authorize a normal stop.

## COMPLETION CRITERIA

Report `COMPLETE` only after all checks pass:

1. Every canonical input keyword was judged exactly once.
2. Every 6-0-1 observation was backfilled exactly once.
3. The configured precision levels were applied without altering judgments.
4. Output classes 1–4 were generated with one shared sequence and timestamp.
5. Unique and observation counts reconcile.
6. Output 2 has one row per canonical keyword and no Benchmark dimension.
7. Every Benchmark required by Output 1 has one Output 3 file.
8. CSV and HTML files pass readback validation.
9. The report root contains only the latest formal run; older formal runs are preserved in history folders.

If any check fails, report `INCOMPLETE` with the exact failed invariant. Never publish partial formal outputs and never fabricate missing judgments.

## EXECUTION ACCEPTANCE

For `6-0-2 {Product_Code}`, acceptance is a single end-to-end result: either `COMPLETE`
with all formal assets published and reconciled, or `INCOMPLETE` with the blocking
invariant and no claim that a batch was the task result. Do not return a batch preview,
partial judgment table, or "run again to continue" as the normal response.
