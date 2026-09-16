# Stage 6 Artifact Contract

Shared contract for Skills 6-0-1 through 6-0-4 and 6-1 through 6-3. Business input/output fields and analysis rules remain defined by each Skill; this contract only governs version selection, run identity, output naming, history preservation, and lineage.

## Shared implementation

`scripts/stage6_artifact_contract.py` is the common implementation. Callers must first scope candidate discovery to the confirmed current Product Root and exact formal output directory/report filename family. Do not scan other products, log folders, arbitrary CSVs, or the full product tree to guess an input.

`resolve_latest_valid_report(...)` filters by readable file, Product Root containment, Skill ID, Product Code, Report Identity, actual CSV schema where applicable, accepted `Run_Status` when a manifest exists, and caller-supplied identity/coverage checks; it then selects the newest valid candidate. Formal metadata `Generated_At` has priority. Filename `YYYYMMDD_HHMMSS` is only the timestamp fallback for historical files without metadata. Filesystem mtime is never a selection signal. A newer invalid candidate is skipped and reported as `LATEST_INVALID_FALLBACK_USED`; a future-dated candidate is marked `FUTURE_TIMESTAMP_DETECTED`. No valid candidate returns `NO_VALID_UPSTREAM_REPORT` (or the more specific not-found/ambiguous status in the resolver result).

Timestamped outputs require a `RunContext` from `new_run_context(...)`. The context is timezone-aware and carries one `RUN_TIMESTAMP` (`YYYYMMDD_HHMMSS`), `RUN_ID` (`{SkillNumber}_{ProductCode}_{RUN_TIMESTAMP}`), `Generated_At`, and timezone for the entire run. `timestamped_output_path(...)` preserves the existing business Report Name and appends the timestamp. `assert_new_outputs(...)` prevents CSV, HTML, or sidecar overwrites.

For multiple outputs from one run, use one context and `resolve_latest_valid_bundle(...)` downstream. A bundle is valid only when each required asset has the same `RUN_ID` or legacy run timestamp. Do not combine files from different runs. An old fixed-name asset is a legacy fallback only when no valid timestamped candidate exists; multiple un-timestamped candidates are ambiguous.

## Metadata and lineage

Each new formal CSV/HTML/JSON/MD artifact has a neighboring `<artifact>.meta.json` written with `write_metadata_sidecar(...)`. Its manifest includes `Skill_Number`, `Skill_ID`, `Product_Code`, `Report_Identity`, `RUN_ID`, `RUN_TIMESTAMP`, timezone-aware `Generated_At`, `Timezone`, `Run_Status`, `Schema` where applicable, `Record_Count`, `Inputs`, and `Output_Assets`. CSV business schemas must not gain lineage columns. Use `make_artifact_metadata(...)`; do not write credentials or secret values.

Every input entry records `Input_Skill`, `Input_Report_Identity`, `Input_File_Name` (null for live query), `Input_Run_Timestamp`, `Input_Generated_At`, `Input_Record_Count`, and `Input_Resolution_Method`. Use `LATEST_VALID_REPORT` or `LATEST_INVALID_FALLBACK_USED` for report inputs and `LIVE_QUERY` for data queried afresh during this run. Current fixed product text files may use `CURRENT_PRODUCT_ROOT_FIXED_INPUT` and have no report run timestamp.

HTML reports also show a short `本次使用数据 / Input Lineage` section with source identity/file, generated time, resolver status, and live query time. Reports must display actual chosen inputs and skipped newer invalid candidates; never claim a report is latest if that was not resolved.

## Skill-specific input/output identities

| Skill | Report identity / input | Output identity |
|---|---|---|
| 6-0-1 | Fresh parameterized `PickPwKView` read for each configured Benchmark; never consume a prior 6-0-1 CSV as this run's live source | `BENCHMARK_KEYWORD_DETAIL`, unique-keyword `BENCHMARK_KEYWORD_POOL`, N `BENCHMARK_KEYWORD_RAW_<ASIN>` assets, and one `BENCHMARK_KEYWORD_ALL_OBSERVATIONS` UNION ALL summary, same run; a complete package contains all |
| 6-0-2 | Latest valid `BENCHMARK_KEYWORD_POOL` nine-column 6-0-1 CSV plus current product text | `AI_PRECISION_KEYWORDS` and `HIGH_PRECISION_KEYWORDS`, same run; both eleven-column unified keyword assets |
| 6-0-3 | Latest valid `HIGH_PRECISION_KEYWORDS` eleven-column 6-0-2 CSV | `PRECISION_BROAD_MAPPING` and `PRECISION_BROAD_SUMMARY`, same run; one mapping per unique KwId |
| 6-0-4 | Latest valid 6-0-2 `AI_PRECISION_KEYWORDS`; a pooled `Id=KwId` must never be treated as writable `PickPwK.Id`. If row identity cannot be safely resolved, fail closed | Per-run operational MD log and metadata; this is not a formal report/index entry |
| 6-1 | Existing current-product formal upstream reports and freshly queried SellerSpace/Amazon evidence | Formal versioned HTML; preserve existing V version and append this run's timestamp |
| 6-2 | Existing current-product formal reports plus fresh allowed business data | Formal versioned HTML; preserve existing period/version name and append this run's timestamp |
| 6-3 | One latest-valid 6-2 four-CSV DATA Run Package; latest-valid approved 6-0-5 purpose package; same-run 6-0-3 summary/mapping; optional 6-0-6 occupancy evidence | Immutable timestamped DECIDE Run Package (four fixed-schema decision CSVs + HTML) under `6-3_广告优化决策/YYYYMMDD_HHMMSS/`; no fresh advertising query, Amazon Ads writes, or Campaign/daily mutation logs |

## Live sources and operational log exception

For Skills whose own contracts require fresh SQL, SellerSpace MCP, Amazon endpoints, or other permitted API reads, query them again for each run. Other Skills may consume an explicitly approved immutable upstream Run Package instead; do not add a live query where the Skill does not require one. A source export/report substitutes for a live query only when that Skill expressly defines it as ground truth.

6-3 decision packages are immutable per-run evidence and remain outside the 0-2 formal report index. Preserve prior run packages for Decision History; never rewrite them. The 6-0-4 per-run execution log also stays outside the formal report index; its filename includes the run timestamp.

## Failure and compatibility

### Multi-Benchmark ground-truth contract

`PickPwKView.KwId` is the user-confirmed Keyword Entity ID, stable and unique for the same keyword across ProIds. `PickPwKView.Id` remains a source View-row ID and is not emitted in the unique-keyword pool `Id` field. 6-0-1 distinguishes one `Keyword Market Fact` per KwId from N `Benchmark Observations` per `(KwId, Benchmark_Code)`. SearchVolume30, AsinQuantity and their computed ratio are stored once per keyword; Benchmark count never multiplies them. Conflicting market facts fail as `KEYWORD_MARKET_FACT_CONFLICT` and remain unresolved.

The 6-0-2 and 6-0-3 product-level assets contain one row per unique KwId. Their market facts and rank-summary evidence must be copied unchanged by Id; precision judgment is semantic only, and 6-0-3 aggregates the unique keyword market capacity once. No Benchmark-specific precision pass, intent tree, current-product campaign architecture, monitoring run, or ad optimization architecture is created. 6-1, 6-2 and 6-3 operate once for the current product; Benchmark ASINs can only remain explicitly identified as comparison or target evidence.

The pooled KwId does not replace the `PickPwK.Id` row key required by the restricted 6-0-4 writer. Until a unique approved row-level expansion is supplied, 6-0-4 must reject the pooled entity ID rather than write it as a row ID.

Candidate validation is performed before latest selection. Do not silently use a corrupt, wrong-product, wrong-Skill, wrong-identity, invalid-status, insufficient-coverage, schema-mismatched, or future-dated artifact. Legacy assets without sidecars may use exact caller-scoped names and filename timestamps; fixed-name legacy assets are only a fallback when no valid timestamped version exists. If legacy identity/status/coverage cannot be established by the Skill's existing checks, return an explicit unresolved status rather than infer.

The shared contract does not change a Skill's business decisions, CSV columns, report content, ERP writes, advertising writes, identity rules, or 0-2 formal report indexing rules.
