---
name: hzp-amz-6-0-3-precision-broad-extraction
description: Read only the 6-0-2去对标去重 高度精准词 asset from its latest complete VALID Run Package, organize each unique high-precision keyword into a semantic Search Intent hierarchy, and produce traceable mapping and hierarchy summary CSVs. Never rejudge precision or execute ad writes.
metadata:
  short-description: 精准泛词
---

# HZP Amazon 6-0-3 | 精准泛词

## Identity and boundary

Formal identity: 6-0-3 | 精准泛词 | Precision Broad Extraction | hzp-amz-6-0-3-precision-broad-extraction.

Read only the 6-0-2 C asset `去对标去重 高度精准词` (`Report_Key=UNIQUE_HIGH_PRECISION_KEYWORDS`) from one latest complete `VALID` 602 Run Package. Never use the 602 observation tables `精准判断所有词表` or `高度精准词表`, or per-benchmark D tables, as Intent inputs. Do not rejudge precision, read 6-0-1, query ERP, edit 6-0-2, or execute Amazon Ads writes. Each unique input keyword receives exactly one `PRIMARY PRECISION BROAD INTENT`; 603 then builds a one-parent Intent Tree and calculates all totals in code.

## Formal input

Invocation: `6-0-3, Product_Code`. Resolve the Product Root, then scan `06_SKILL分析报告/6-0-2_AI精准关键词识别/` for timestamped run manifests and legacy timestamp folders. Sort by `RUN_TIMESTAMP`, require `Run Status=VALID`, and validate the complete 3+N 602 package, including every expected per-benchmark D asset. Skip failed, incomplete, or mismatched runs and fall back to the newest complete valid package. The resolver is `resolve_latest_valid_602_run_package(product_root, product_code)`; it returns all companion paths from one package.

602 package members are `6-0-2_精准判断所有词表_{RUN_TIMESTAMP}.csv`, `6-0-2_高度精准词表_{RUN_TIMESTAMP}.csv`, `6-0-2_去对标去重 高度精准词_{RUN_TIMESTAMP}.csv`, plus one `6-0-2_{所属产品编号}_高度精准词_{RUN_TIMESTAMP}.csv` for every expected benchmark and `6-0-3_RunPackage_{RUN_TIMESTAMP}.json`. All files are directly under the fixed 602 report root, and all timestamps must match the manifest. The shared manifest and package validation are authoritative; 603 does not require per-CSV `.meta.json` files. 603 uses only C as keyword input. A, B and D may be checked for package completeness/schema but must never be passed to Intent extraction.

Report Identity is `去对标去重 高度精准词`; `Report_Key` is `UNIQUE_HIGH_PRECISION_KEYWORDS`. Required columns are `Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准度,精准原因`; benchmark identity fields including `所属产品编号` are not accepted in this unique-keyword schema. Every row must have `精准度=高度精准`, and `normalize_broad_keyword(词)` must be unique. Duplicate canonical keywords fail with `603_INPUT_DUPLICATE_KEYWORD`; any other precision level fails with `603_INPUT_NOT_ALL_HIGH_PRECISION`. Preserve each unique Id. `竞争产品数` and `供需比` are copied unchanged into the mapping CSV. The mapping column `自然排名` is sourced from `最佳自然排名`; the summary uses source `竞争产品数` only for the defined subtree arithmetic mean and does not aggregate keyword-level `供需比`.

Invalid input statuses include `NON_HIGH_PRECISION_RECORD_IN_603_INPUT`, `MISSING_RECORD_IDS`, and `DUPLICATE_RECORD_IDS`.

## Search Intent Hierarchy

The AI maps each source keyword to exactly one natural, canonical `精准泛词` and may assign one `父精准泛词`. A broad intent is the minimum independently operable intent: preserve a dimension when removing it would merge commercially distinct purchase tasks (for example, a stable purchase occasion), but compress incidental numbers, adjectives, wording order, or isolated modifiers. Do not use N-gram extraction, mechanical stop-word deletion, or a phrase-specific hardcoded table. A parent is direct and unique; it must itself be an intent. Do not create a child from a single incidental modifier without strong semantic and cluster evidence. If no reliable primary can be formed, keep the Id with `[PRECISION_BROAD_MAPPING_UNRESOLVED]` and report the unresolved condition.

A record such as `birthday gifts for sister` can map primarily to `sister birthday gifts`, whose direct parent is `sister gifts`. The mapping CSV stores only the primary intent; parent truth is stored in the summary CSV. One record never contributes base volume to both parent and child.

Before accepting the hierarchy, review over-fragmentation (especially singleton intents caused only by incidental modifiers) and over-merge (distinct occasion, relationship, product-type, or purpose tasks compressed into a parent). These are semantic audits; do not fix them by numeric thresholds or by hardcoding a product's phrases.

## Program validation and calculation

The program performs Coverage, unique Id checks, primary uniqueness, parent uniqueness, parent existence (`ORPHAN_PARENT_INTENT`), cycle detection (`PARENT_CYCLE_DETECTED`), and aggregation consistency before writing a formal success. It computes:

- `直接搜索量`: SUM of source `市场容量` for records whose primary intent is this intent.
- `汇总搜索量`: direct volume plus all descendant aggregated volumes, recursively.
- `直接对应词数`: COUNT of records mapped directly to this intent.
- `平均竞品数`: arithmetic mean of valid source `竞争产品数 > 0` values across the intent's full subtree. The program resolves unique source `Id` records before averaging; NULL, invalid, and zero values do not enter the mean. If none are valid, output `DATA_NOT_AVAILABLE`.
- `意图机会比`: `汇总搜索量 / 平均竞品数`, rounded to four decimal places. Output `DATA_NOT_AVAILABLE` when either input is unavailable.

Missing or unparsable source volumes produce `DATA_NOT_AVAILABLE` for that intent. Root volume consistency compares the sum of L1 aggregate volumes with the sum of input volumes when all inputs are available. Parent and child totals may overlap by containment; never add totals across levels. This total is an internal aggregation of 6-0-2 evidence, not Amazon's official intent market size.

`平均竞品数` is not the number of unique competing ASINs for an intent. It is an internal average competition-environment signal based on keyword-level `PickPwKView.AsinQuantity`; keyword competitor sets can overlap. Intent `意图机会比` is an internal Search Intent Opportunity Signal, not Amazon's official competition ratio, Keyword Difficulty, Rank Difficulty, or an investment conclusion. Never SUM competitor counts, average keyword-level ratios, calculate a weighted average, or calculate an average of child averages. For each intent, calculate directly from unique source records in its full subtree; each parent and child gets its own independently calculated subtree metrics.

Before reporting success, integrity checks verify the mapping's `竞争产品数` and `供需比` match 6-0-2 by `Id`, each intent average matches the direct arithmetic mean of its unique valid subtree source records, and `意图机会比` matches aggregate search volume divided by that average. A missing average requires a missing ratio. The same checks run again on the written CSVs after readback; any mismatch blocks success.

## Outputs

Each run captures one `RUN_TIMESTAMP` in the strict `YYYYMMDD_HHMMSS` format
and creates a new package directly under
`06_SKILL分析报告/6-0-3_精准泛词提取/`. No timestamp subfolder is created.
Timestamped files and `6-0-3_RunPackage_{RUN_TIMESTAMP}.json` preserve each run;
existing files are not overwritten. The manifest and both formal filenames use
the same timestamp:

`6-0-3_词对应的精准泛词_{RUN_TIMESTAMP}.csv`

Nine columns: `Id,词,中文,市场容量,竞争产品数,供需比,自然排名,精准泛词,精准泛词中文`. Preserve input order, all Ids, and the input competitor count/ratio unchanged.

The hierarchy summary is:

`6-0-3_精准泛词汇总_{RUN_TIMESTAMP}.csv`

Nine columns: `精准泛词,中文,层级,父精准泛词,直接搜索量,汇总搜索量,平均竞品数,意图机会比,直接对应词数`. `平均竞品数` is rounded to two decimal places and `意图机会比` to four. Sort by level ascending, then aggregated volume descending, with missing totals last and stable first appearance.

The manifest records `SkillId`, `Current Product`, `RUN_ID`, `RUN_TIMESTAMP`,
`GeneratedAt`, `Input Skill=602`, `Input Report=去对标去重 高度精准词`, `Input Report Identity=去对标去重 高度精准词`, `Input Report Key=UNIQUE_HIGH_PRECISION_KEYWORDS`, the selected 602 Run ID/timestamp/folder/file, input record count, and input unique keyword count,
fixed output root/files/counts, validation, and Run Status. 603 resolves its own
latest output with `resolve_latest_valid_603_run_package()`;
`latest_output_paths()` returns both files from that one package. A run is
`VALID` only after both CSVs are written, read back, and pass Coverage,
hierarchy, calculation, and pass-through checks. Incomplete or failed runs
remain archived in their timestamped manifests and are skipped.

Downstream Skills must select the newest complete `VALID` 603 Run Package and
read both files named by its manifest from the fixed report root. 6-1 may use L1 aggregate volume for overall
scale and L2/L3 aggregate volume for sub-intents, but must not sum parent and
child aggregates. No keyword-family asset or advertising action is performed.
See `scripts/broad_seed_cluster.py` and `references/broad-seed-cluster-v1.md`.

## 全局正式报告目录与命名规则

本 Skill 面向确定 Product Root 生成正式报告或结构化分析报告时，统一保存到 `06_SKILL分析报告/{Skill编号}_{Skill中文正式名称}/`，文件名使用 `{Skill编号}_{报告名称}_{YYYYMMDD_HHMMSS}.{ext}`；同一运行的配套正式资产共用时间戳。6-0-1、6-0-2、6-0-3、6-0-5、6-0-6 的报告资产直接放固定 Skill 目录，不建时间戳子目录；6-2、6-3、6-4 可按每次运行建立 `YYYYMMDD_HHMMSS/` 子目录，子目录中的文件仍须带 Skill 编号前缀和时间戳。读取最新报告或运行包时按文件名/包内时间及有效性校验，不按文件修改时间选择。HTML 必须使用同批 CSV 回读快照渲染。历史报告不自动迁移或删除。跨产品公共知识、提醒状态、决策登记簿和运行日志等持续业务数据按各自数据契约保存，不作为 Product Root 正式分析报告迁移。
