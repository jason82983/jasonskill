---
name: hzp-amz-6-0-3-precision-broad-extraction
description: Read the newest 6-0-2 C precision asset, build a stable Current Product Search Intent map with one Primary Intent per keyword, and produce traceable mapping and hierarchy CSVs. Never rejudge precision or execute ad writes.
metadata:
  short-description: 精准泛词
---

# HZP Amazon 6-0-3 | 精准泛词

## Identity and boundary

Formal identity: 6-0-3 | 精准泛词 | Precision Broad Extraction | hzp-amz-6-0-3-precision-broad-extraction.

Read only the 6-0-2 D asset `去对标去重 高度精准词` (the configured 602 precision library output) from the 602 `data/` directory, selecting the greatest filename timestamp and validating the minimum C schema. RunPackage, Manifest, sidecar and mtime are not prerequisites. C remains the sole semantic Intent input; never use A/B/D as Intent inputs. Do not rejudge precision, read 6-0-1, query ERP, edit 6-0-2, or execute Amazon Ads writes.

## Formal input

Invocation: `6-0-3, Product_Code`. Resolve the Product Root, scan the 602 `data/` directory for the exact C filename, choose the greatest `YYYYMMDD_HHMMSS`, and validate its schema and Product identity. Historical folders are not selected.

The 602 D selection is controlled by the shared configuration `E:\【所有产品目录专用】\01_公共资料\03_系统配置\生成精准词库的要求.txt` (relative path `01_公共资料/03_系统配置/生成精准词库的要求.txt`) under the unified product root. 603 reads that configuration while validating the selected 602 package and rejects a package whose recorded normalized levels do not match the current file. The business label `已精准` is normalized to the existing AI label `精准`.

The 602 handoff passes only C to Intent extraction. A, B and D are never semantically extracted.
历史迁移兼容：若旧批次目录中残留旧名 B/C CSV，且新命名资产齐全，校验仅忽略这两个同时间戳旧别名，不读取其内容；所有必需的新命名资产仍须完整且通过校验。

Report Identity is `去重去对标后 筛选后的精准词表`; `Report_Key` is `UNIQUE_SELECTED_PRECISION_KEYWORDS`. Required columns are `Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准度,精准原因`; benchmark identity fields including `所属产品编号` are not accepted in this unique-keyword schema. Every row is accepted from 602 D without a second precision filter; `normalize_broad_keyword(词)` must be unique. Duplicate canonical keywords fail with `603_INPUT_DUPLICATE_KEYWORD`. Preserve each unique Id. `竞争产品数` and `供需比` are copied unchanged into the mapping CSV. The mapping column `自然排名` is sourced from `最佳自然排名`; the summary uses source `竞争产品数` only for the defined subtree arithmetic mean and does not aggregate keyword-level `供需比`.

Invalid input statuses include `NON_HIGH_PRECISION_RECORD_IN_603_INPUT`, `MISSING_RECORD_IDS`, and `DUPLICATE_RECORD_IDS`.

## Search Intent Hierarchy

Load the current-product profile once from `05_分析源数据/01_产品数据/本产品/产品识别 - 文本文案.txt` when available. It is semantic context only; missing or empty profile is recorded in lineage and must not be replaced with invented facts. Build Phase-A semantic units and Phase-B globally reconciled candidate intents. Semantic batches are sized from estimated prompt characters and profile length, not a fixed row count.

The AI maps each source keyword to exactly one natural, canonical `精准泛词` and may assign one `父精准泛词`. A broad intent is the minimum independently operable intent: preserve a dimension when removing it would merge commercially distinct purchase tasks (for example, a stable purchase occasion), but compress incidental numbers, adjectives, wording order, or isolated modifiers. Do not use N-gram extraction, mechanical stop-word deletion, or a phrase-specific hardcoded table. A parent is direct and unique; it must itself be an intent. Do not create a child from a single incidental modifier without strong semantic and cluster evidence. If no reliable primary can be formed, keep the Id with `[PRECISION_BROAD_MAPPING_UNRESOLVED]` and report the unresolved condition.

A record such as `birthday gifts for sister` can map primarily to `sister birthday gifts`, whose direct parent is `sister gifts`. The mapping CSV stores the primary intent and its `ParentIntentId`; parent truth is also reflected in the summary CSV. One record never contributes base volume to both parent and child.

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
The two formal CSVs are published as one validated batch directly under `data/`; the current `data/` contains the latest complete batch. A manifest may be stored under `_system/manifests/` for lineage, but it is not required for the 603 input resolver. Prior valid batches remain under `历史数据/<RUN_TIMESTAMP>/`. The manifest and both formal filenames use the same timestamp:

`6-0-3_词对应的精准泛词_{RUN_TIMESTAMP}.csv`

Fixed schema: `Id,词,中文,市场容量,竞争产品数,供需比,自然排名,精准泛词,精准泛词中文,PrimaryIntentId,PrimaryIntentCode,KeywordPurchaseMission,Intent层级,ParentIntentId,父精准泛词,IntentAssignmentReason,ChallengeResult,ChallengeReasonSummary`. Preserve input order, all Ids, and the input competitor count/ratio unchanged.

The hierarchy summary is:

`6-0-3_精准泛词汇总_{RUN_TIMESTAMP}.csv`

Fixed schema: `精准泛词,中文,层级,父精准泛词,直接搜索量,汇总搜索量,平均竞品数,意图机会比,直接对应词数,IntentId,IntentCode,IntentDefinition,PrimaryPurchaseDriver,ChallengeStatus,ChallengeReasonSummary`. `平均竞品数` is rounded to two decimal places and `意图机会比` to four. Sort by level ascending, then aggregated volume descending, with missing totals last and stable first appearance.

The manifest records `SkillId`, `Current Product`, `RUN_ID`, `RUN_TIMESTAMP`,
`GeneratedAt`, `Input Skill=602`, `Input Report=去重去对标后 筛选后的精准词表`, `Input Report Identity=去重去对标后 筛选后的精准词表`, `Input Report Key=UNIQUE_SELECTED_PRECISION_KEYWORDS`, the selected 602 Run ID/timestamp/folder/file, input record count, and input unique keyword count,
fixed output root/files/counts, validation, and Run Status. 603 resolves its own
latest output with `resolve_latest_valid_603_run_package()`;
`latest_output_paths()` returns both files from that one package. A run is
`VALID` only after both CSVs are written, read back, and pass Coverage,
hierarchy, calculation, and pass-through checks. Incomplete or failed runs
remain archived in their timestamped manifests and are skipped.

Downstream Skills must select the newest timestamped valid A/B assets from the 603 `data/` directory using the specified Report Identity and minimum schema; a manifest may enrich lineage but is not a required input gate. 6-2 may use L1 aggregate volume for overall
scale and L2/L3 aggregate volume for sub-intents, but must not sum parent and
child aggregates. No keyword-family asset or advertising action is performed.
See `scripts/broad_seed_cluster.py` and `references/broad-seed-cluster-v1.md`.

## Human Report Publishing

本 Skill 生成正式 HTML 报告时，遵循统一的人类可见报告规则：Skill 报告根目录只保留一个当前最新 HTML；旧 HTML（以及同名 `.meta.json`）全部移动到同级 `历史HTML/`，不删除、不覆盖。一次性 Skill 的正式机器 CSV/JSON 只进入当前 Skill 报告目录的 `data/`，且只保留完整 `LATEST VALID` Batch；RunPackage/Manifest、metadata sidecar、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。HTML 仅按人类报告规则发布到根目录或 `历史HTML/`。完成写入、回读和校验后才发布当前报告；失败或不完整 Run 不得发布。公共实现与索引规则见 [`skills/references/human-report-publishing.md`](../references/human-report-publishing.md)。

## 全局报告文件治理（适用本 Skill）

本 Skill 遵循公共 `scripts/hzp_amz_report_contract.py`、[human-report-publishing.md](../references/human-report-publishing.md) 与 [report-governance.md](../references/report-governance.md)：正式机器业务数据只进入当前 Skill 报告目录的 `data/`，`data/` 只保留完整 `LATEST VALID` Batch；旧 VALID Batch 整包进入 `历史数据/<RUN_TIMESTAMP>/`。RunPackage/Manifest、metadata、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。新 Batch 必须先 Staging、验证完整性后再原子发布；失败不得替换旧 data。根目录只保留最新人类 HTML（如有）及正式子目录，机器数据不得写根目录。下游通过指定 Report Identity 扫描 `data/` 并按文件名 `YYYYMMDD_HHMMSS` 取最新，不得按 HTML、根目录或文件修改时间选数。已有成熟时间戳 Run Package 的持续 Skill 可保留其内部运行包，但仍遵守根目录清洁和系统资产分层。

## V3 Intent Contract
603 不重新筛选 Precision，不使用本地 token、字符串或规则生成最终 Intent。必须由真实 AI Intent Engine 负责 Primary Intent、语义合并及父子关系；AI 不可用时返回 INTENT_AI_ENGINE_UNAVAILABLE，不得本地降级。失败项保留 PrimaryIntent=NULL 并标记 REVIEW_REQUIRED/FAILED。RunPackage、Manifest、meta、mtime 均不是输入前提；按 602 D 正式文件名时间戳读取。

## V3 Agent Pull Queue 执行锁定
603 通过 get_603_status、get_next_603_semantic_batch、save_603_semantic_batch 采用 Agent Pull Queue；禁止 Python Callback Push。602 D 是唯一输入，接受 D 中全部配置筛选后的关键词，不在 603 二次筛选 Precision。PrimaryIntent、PurchaseMission、Intent 合并及 Parent/Child 必须由真实 AI Agent 判断；本地 token、字符串、规则只能做候选或校验，AI 不可用时返回 INTENT_AI_ENGINE_UNAVAILABLE，不得生成正式 Intent。
