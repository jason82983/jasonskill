# 6-1 input and Run Package contract

## 6-0-3 input resolution

Search only the current Product Root's `06_SKILL分析报告/6-0-3_精准泛词提取/`.

The preferred input is the newest complete valid package in the fixed 6-0-3 report root. Validate Product identity, `RUN_TIMESTAMP`, `Run Status=VALID`, declared files, filename timestamps, schemas, record counts, unique Ids, and Intent coverage. Skip failed or incomplete runs and continue to the previous complete valid run.

Every 6-0-3 candidate must be represented by `run_manifest_{RUN_TIMESTAMP}.json` in the fixed report root, declaring `SkillId=hzp-amz-6-0-3-precision-broad-extraction`, the current product, matching `RUN_TIMESTAMP` and `Output Folder`, `Run Status=VALID`, the two timestamp-matched formal CSV filenames, and the 602 input lineage. Both CSVs must be in that same report root and match the manifest timestamp. Skip incomplete, failed, mismatched, or malformed packages and fall back to the newest complete valid package. Never select the latest summary and mapping independently. A single-benchmark map contains `自然排名`; a multi-benchmark map contains `对标覆盖数`, `最佳自然排名`, and `自然排名中位数`. Do not synthesize fields absent from the source.

Summary columns:

`精准泛词,中文,层级,父精准泛词,直接搜索量,汇总搜索量,平均竞品数,意图机会比,直接对应词数`

Single-benchmark mapping columns:

`Id,词,中文,市场容量,竞争产品数,供需比,自然排名,精准泛词,精准泛词中文`

Multi-benchmark mapping columns:

`Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准泛词,精准泛词中文`

Record the selected 603 `RUN_ID`, timestamp, folder, and both source files in 6-1 lineage. The selected input is always a manifest-backed package.

## Output schemas

All CSV files use UTF-8 with BOM. A and C follow the fixed schemas in the task contract. C and B preserve the appropriate benchmark evidence profile: the single-benchmark output carries `自然排名`; the multi-benchmark output carries `对标覆盖数,最佳自然排名,自然排名中位数`.

B `新品关键词作战明细` additionally carries `目标类型,目标值` immediately after `投放方式`. Keyword rows are `KEYWORD` plus the exact keyword. ASIN, PT/Product Target, and Category rows must carry an explicit approved target value; a missing or mismatched target invalidates the Battle Unit package.

D `广告创建参数表` is mandatory, one row per approved Battle Unit. It carries the exact Campaign/Ad Group name preview, Campaign Role/Ad Type, status, dates, Portfolio, Daily Budget, Bidding Strategy, Top of Search/Rest of Search/Product Pages, Ad Group Default Bid, Target Type/Value/Bid, initial negatives, Own ASIN/SKU, Marketplace and Store, plus `Parameter Status` and evidence. Missing values are serialized as `DATA_NOT_AVAILABLE`; 6-2 must stop until every row is `READY_FOR_6_1`.

The code validates:

- A contains every 603 Summary Intent exactly once.
- C contains every 603 Mapping Id exactly once, preserving source order and source market fields.
- B equals the eligible PHASE_1 execution projection from C and contains no `不投` row.
- Every 6-1 Intent Code exists in A and matches each mapped C/B row.
- Parent/child metrics are copied from 603; 6-1 does not recalculate or cross-add them.
- The same logical Intent gets a stable code. Reuse one recognized existing Intent Code Registry under this output root; otherwise create `stable_intent_code_registry.json` beside the timestamped package files. Codes are deterministic and are not UUIDs.
- Battle Unit IDs are deterministic from the logical Campaign grouping key, not a keyword Id. Compatible keywords in one independent Intent share a unit; shared traffic pools by role and type. One keyword does not become one Campaign.

## Run package, manifest, and latest-valid selection

Write all 6-1 package files directly in `06_SKILL分析报告/6-1_新品广告作战规划/`; do not create a timestamp subfolder. Each run uses one `RUN_TIMESTAMP` in all five formal filenames and in `run_manifest_{RUN_TIMESTAMP}.json`. Reject a timestamp collision rather than overwrite existing files. The timestamped manifest is the package boundary: its declared files must all exist in the same fixed report root and pass validation. Keep historical timestamped files and manifests.

The manifest records at least `SkillId`, `Current Product`, `RUN_ID`, `RUN_TIMESTAMP`, 603 Run ID/timestamp/folder/files, optional 606 Run ID or `606_EVIDENCE_NOT_AVAILABLE`, input counts, output folder/files/counts, `GeneratedAt`, validation, and `Run Status`. Write `RUNNING` before package work, then `VALID` only after all files are read back and cross-validated. On any formal output or validation failure, preserve the timestamped manifest and mark it `INVALID`; the resolver skips it. Historical runs are not overwritten or deleted.

`scripts/battle_plan.py inspect-inputs --product-root <root> --product-code <code>` returns the selected 603 pair and optional 606 evidence for planning. Run with `scripts/battle_plan.py run --product-root <root> --product-code <code> --decisions-json <path> --expected-603-run-id <id> --expected-603-timestamp <timestamp> --expected-606-run-id <id-or-606_EVIDENCE_NOT_AVAILABLE>`. The source guards prevent a package change between inspection and writing.

`scripts/battle_plan.py resolve-latest-6-1 --product-root <root> --product-code <code>` scans timestamped manifests by `RUN_TIMESTAMP`, returns the newest complete valid package as a unit and falls back past invalid runs. 6-2 consumers must use all five paths from one returned package root, not find A/B/C/D independently. The 6-1 package keeps the requested `LATEST VALID 6-1 RUN PACKAGE` contract.

## Static HTML and campaign preview

Render the HTML only from this timestamp's A/C/B/D CSVs in the fixed report root. Embed the snapshot in the HTML; do not load latest CSVs or external assets when opened. Validate embedded data against CSV readback. Include the required dashboard sections from `SKILL.md` and explain that opportunity ratio is not Amazon's official metric, parent/child totals overlap, precise does not mean invest now, and benchmark rank does not equal sales share.

Derive proposed Campaign groups from B and materialize D:

- Independent control → Intent-aware Campaign including the stable Intent Code.
- Shared control → role-pool Campaign omitting Intent Code.
- No investment → no Campaign.

Group compatible keywords. CampaignTag is supplied at runtime; if absent show `{ProductCode}.{CampaignTag}.SP-COR-EXA-SBG-01` as a placeholder and do not guess a real tag. 6-1 owns all creation parameters; 6-2 only validates and applies the exact approved D values.
