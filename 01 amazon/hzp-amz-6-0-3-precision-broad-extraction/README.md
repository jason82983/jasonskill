# HZP Amazon 6-0-3 | 精准泛词

`hzp-amz-6-0-3-precision-broad-extraction` reads only C, `去对标去重 高度精准词` (`Report_Key=UNIQUE_HIGH_PRECISION_KEYWORDS`), from the latest complete `VALID` 6-0-2 Run Package under `06_SKILL分析报告/6-0-2_AI精准关键词识别/`. Its `Report_Identity` is `去对标去重 高度精准词`. `resolve_latest_valid_602_run_package(product_root, product_code)` validates the timestamped manifest, the three shared assets and all N per-benchmark D assets, schemas and counts, then falls back over failed/incomplete runs. 603 never uses A (`精准判断所有词表`), B (`高度精准词表`) or D as Intent input and never looks up a latest standalone CSV. The unique input must contain only `高度精准` rows and one canonical keyword per row; duplicate canonical keywords fail with `603_INPUT_DUPLICATE_KEYWORD`, and other precision values fail with `603_INPUT_NOT_ALL_HIGH_PRECISION`. The input lineage records the 602 Run ID, timestamp, folder, C file, record count and unique keyword count. It never rejudges precision, queries ERP, or performs advertising writes.

The AI maps every source record to exactly one canonical primary Search Intent and at most one direct parent. It preserves commercially independent dimensions such as a stable purchase occasion when the dimension is independently operable, while compressing incidental modifiers. A parent must exist as an intent and the tree cannot contain cycles.

The program preserves each source `Id`, `竞争产品数` and `供需比`, validates Coverage and tree integrity, calculates direct volume and recursive aggregated volume from the input `市场容量`, and checks root-volume consistency. Intent `平均竞品数` is the direct arithmetic mean of valid (`> 0`) keyword-level competitor counts from unique source Ids across the full intent subtree; NULL, invalid, and zero values are excluded, with `DATA_NOT_AVAILABLE` when no valid value exists. Intent `意图机会比` is `汇总搜索量 / 平均竞品数`, rounded to four decimals. It is an internal opportunity signal, not an official Amazon ratio, difficulty score, unique ASIN count, or investment conclusion. Never sum competitor counts, average keyword ratios, use weighted averages, or average child averages. Parent and child aggregates can overlap by containment; they must never be added across levels. Missing inputs produce `DATA_NOT_AVAILABLE`.

Each run captures one strict `RUN_TIMESTAMP` (`YYYYMMDD_HHMMSS`) and writes one
complete package directly to `06_SKILL分析报告/6-0-3_精准泛词提取/`; no timestamp
subfolder is created. The two UTF-8-BOM CSV filenames and
`run_manifest_{RUN_TIMESTAMP}.json` belong to the same run. Historical files
are preserved:

1. `6-0-3_[Product_Code]_词对应的精准泛词_YYYYMMDD_HHMMSS.csv` (nine columns: `Id,词,中文,市场容量,竞争产品数,供需比,自然排名,精准泛词,精准泛词中文`)
2. `6-0-3_[Product_Code]_精准泛词汇总_YYYYMMDD_HHMMSS.csv` (nine columns: `精准泛词,中文,层级,父精准泛词,直接搜索量,汇总搜索量,平均竞品数,意图机会比,直接对应词数`)

Before success, data-integrity checks compare mapping pass-through fields by Id and validate subtree average and ratio formulas. The generated CSV pair is read back and checked again.

The timestamped manifest records the selected 602 Run lineage, product
identity, output files/counts, validation, and status. A run becomes `VALID`
only after both files are written and pass readback integrity checks. Use
`resolve_latest_valid_603_run_package(product_root, product_code)` or
`latest_output_paths(product_root, product_code)` to select both files from the
newest complete valid package; incomplete and failed runs are skipped. The
summary is an internal aggregation of 6-0-2 evidence, not Amazon's official
intent volume.
