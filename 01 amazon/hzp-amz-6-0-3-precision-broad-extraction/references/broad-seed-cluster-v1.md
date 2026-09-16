# 6-0-3 Search Intent Hierarchy contract

## Input and identity

The only input is `6-0-2_[Product_Code]_AI高度精准词.csv` (`HIGH_PRECISION_KEYWORDS`). All rows must already be `高度精准`; 603 does not rejudge them. `Id` is the source record identity and must be present, unique, and preserved.

## Primary and parent intent

AI assigns one natural Canonical Primary Precision Broad Intent per record and at most one Direct Parent per intent. Keep a dimension when removing it would merge independently operable purchase tasks; compress incidental modifiers and do not create children from isolated modifiers without cluster evidence. The mapping file stores only the primary. Parent truth is in the summary.

Example calibration: `gift for sister` -> `sister gifts`; `birthday gifts for sister` -> `sister birthday gifts` -> parent `sister gifts`; `50th birthday gifts for sister` normally remains `sister birthday gifts` unless an independently operable cluster is evidenced.

## Program checks

Aggregation Consistency is checked programmatically before output.

The program validates:

- Coverage and unique source Ids.
- One primary per record and one direct parent per intent.
- `ORPHAN_PARENT_INTENT` when a non-empty parent is absent.
- `PARENT_CYCLE_DETECTED` for any cycle.
- `AGGREGATION_MISMATCH` when direct counts or totals are inconsistent.
- `ROOT_VOLUME_MISMATCH` when all source volumes are available but L1 totals do not equal the input total.

Each source record contributes its `市场容量` once to its primary's Direct Search Volume. Aggregated Search Volume is the recursive sum of the intent plus descendants. Parent and child aggregates overlap by containment and must not be added together. Missing or unparsable volumes are `DATA_NOT_AVAILABLE`.

## Outputs

`6-0-3_[Product_Code]_词对应的精准泛词_YYYYMMDD_HHMMSS.csv` is eleven columns: `Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准泛词,精准泛词中文`. Each run writes a new timestamped file and preserves source order; all first nine unique-keyword fact/evidence columns are passed through unchanged. The summary uses source competitor counts only in the explicitly defined subtree average; keyword-level ratios are not summarized. One KwId enters this mapping once regardless of its Benchmark observation count.

`6-0-3_[Product_Code]_精准泛词汇总_YYYYMMDD_HHMMSS.csv` has nine columns: `精准泛词,中文,层级,父精准泛词,直接搜索量,汇总搜索量,平均竞品数,意图机会比,直接对应词数`. Levels are calculated from the tree (`L1` roots). Sort by level ascending, then aggregated volume descending, missing last, stable by first appearance. `平均竞品数` is the arithmetic mean of valid source `竞争产品数 > 0` values for unique source Ids in the intent's full subtree, rounded to two decimals. NULL, invalid, and zero counts are excluded; if none remain, output `DATA_NOT_AVAILABLE`. `意图机会比` is programmatically calculated as `汇总搜索量 / 平均竞品数`, rounded to four decimals, and is `DATA_NOT_AVAILABLE` if either input is unavailable.

These are internal Search Intent Opportunity Signals, not actual unique competing ASIN counts, official Amazon ratios, Keyword Difficulty, Rank Difficulty, or investment conclusions. Never SUM competitor counts, average keyword-level ratios, use weighted averages, or average child averages. A parent metric is calculated directly from the original unique source records across its full subtree; child metrics are independently calculated for their own subtrees. Downstream readers use the shared latest-valid bundle resolver for the newest valid mapping/summary pair with the same Product_Code, RUN_ID/RUN_TIMESTAMP, report identities, schemas and successful status.

Before success, integrity checks require exact pass-through of mapping `竞争产品数` and `供需比` by Id, verify each intent mean against its unique valid source records, verify the ratio formula and NULL pairing, and repeat the checks after CSV readback.

Both files use UTF-8 with BOM and one actual run timestamp/RUN_ID. Each has a `.meta.json` sidecar with input lineage; existing output history is never overwritten. The only input is selected from current Product Root via the shared resolver and must be the latest valid `HIGH_PRECISION_KEYWORDS` report. The summary is an internal 6-0-2 evidence aggregation, not Amazon's official intent market size. Shared contract: `../references/stage6-artifact-contract.md`.
