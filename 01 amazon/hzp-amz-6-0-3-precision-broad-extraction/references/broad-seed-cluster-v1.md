# 6-0-3 Search Intent Hierarchy contract

## Input and identity

The only keyword input is the C CSV `去对标去重 高度精准词` (`Report_Identity=去对标去重 高度精准词`, `Report_Key=UNIQUE_HIGH_PRECISION_KEYWORDS`) inside the latest complete `VALID` 6-0-2 Run Package. Resolve timestamped run manifests in `06_SKILL分析报告/6-0-2_AI精准关键词识别/` with `resolve_latest_valid_602_run_package(product_root, product_code)`; require the complete 3+N package and fall back over failed or incomplete runs. Read the C asset `6-0-2_去对标去重 高度精准词_{RUN_TIMESTAMP}.csv` named by that manifest. A (`精准判断所有词表`), B (`高度精准词表`) and D (`6-0-2_{所属产品编号}_高度精准词`) are package companions and must not be used as Intent inputs. The C schema is `Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准度,精准原因`; it has no benchmark identity fields. All rows must be `高度精准`, and canonical `词` values must be unique. Fail with `603_INPUT_NOT_ALL_HIGH_PRECISION` or `603_INPUT_DUPLICATE_KEYWORD` instead of filtering or deduplicating. `Id` is present and unique.

## Primary and parent intent

AI assigns one natural Canonical Primary Precision Broad Intent per record and at most one Direct Parent per intent. Keep a dimension when removing it would merge independently operable purchase tasks; compress incidental modifiers and do not create children from isolated modifiers without cluster evidence. The mapping file stores only the primary. Parent truth is in the summary.

Example calibration: `gift for sister` -> `sister gifts`; `birthday gifts for sister` -> `sister birthday gifts` -> parent `sister gifts`; `50th birthday gifts for sister` normally remains `sister birthday gifts` unless an independently operable cluster is evidenced.

## Program checks

Aggregation Consistency is checked programmatically before output.

The program validates:

- Coverage and unique canonical input keywords and source Ids.
- One primary per record and one direct parent per intent.
- `ORPHAN_PARENT_INTENT` when a non-empty parent is absent.
- `PARENT_CYCLE_DETECTED` for any cycle.
- `AGGREGATION_MISMATCH` when direct counts or totals are inconsistent.
- `ROOT_VOLUME_MISMATCH` when all source volumes are available but L1 totals do not equal the input total.

Each source record contributes its `市场容量` once to its primary's Direct Search Volume. Aggregated Search Volume is the recursive sum of the intent plus descendants. Parent and child aggregates overlap by containment and must not be added together. Missing or unparsable volumes are `DATA_NOT_AVAILABLE`.

## Outputs

Each run writes one complete package directly under `06_SKILL分析报告/6-0-3_精准泛词提取/`, without a timestamp subfolder. `RUN_TIMESTAMP` is strict `YYYYMMDD_HHMMSS`; both CSV filenames and `run_manifest_{RUN_TIMESTAMP}.json` share it. Historical files are preserved. The mapping file `6-0-3_[Product_Code]_词对应的精准泛词_{RUN_TIMESTAMP}.csv` is nine columns: `Id,词,中文,市场容量,竞争产品数,供需比,自然排名,精准泛词,精准泛词中文`. It preserves source order; competitor count and ratio are passed through unchanged. The summary uses source competitor counts only in the explicitly defined subtree average; keyword-level ratios are not summarized.

`6-0-3_[Product_Code]_精准泛词汇总_{RUN_TIMESTAMP}.csv` has nine columns: `精准泛词,中文,层级,父精准泛词,直接搜索量,汇总搜索量,平均竞品数,意图机会比,直接对应词数`. Levels are calculated from the tree (`L1` roots). Sort by level ascending, then aggregated volume descending, missing last, stable by first appearance. `平均竞品数` is the arithmetic mean of valid source `竞争产品数 > 0` values for unique source Ids in the intent's full subtree, rounded to two decimals. NULL, invalid, and zero counts are excluded; if none remain, output `DATA_NOT_AVAILABLE`. `意图机会比` is programmatically calculated as `汇总搜索量 / 平均竞品数`, rounded to four decimals, and is `DATA_NOT_AVAILABLE` if either input is unavailable.

These are internal Search Intent Opportunity Signals, not actual unique competing ASIN counts, official Amazon ratios, Keyword Difficulty, Rank Difficulty, or investment conclusions. Never SUM competitor counts, average keyword-level ratios, use weighted averages, or average child averages. A parent metric is calculated directly from the original unique source records across its full subtree; child metrics are independently calculated for their own subtrees. Downstream readers select the newest complete timestamped pair for the same Product_Code.

Before success, integrity checks require exact pass-through of mapping `竞争产品数` and `供需比` by Id, verify each intent mean against its unique valid source records, verify the ratio formula and NULL pairing, and repeat the checks after CSV readback. Only after both files pass readback and package timestamp/completeness validation does the manifest become `VALID`. Failed and incomplete timestamped manifests remain archived and are excluded by `resolve_latest_valid_603_run_package(product_root, product_code)`. The `latest_output_paths()` helper returns both paths from that one valid package. Downstream Skills must not select the two files independently.

Both files use UTF-8 with BOM. The summary is an internal 6-0-2 evidence aggregation, not Amazon's official intent market size.
