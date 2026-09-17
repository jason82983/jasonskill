---
name: hzp-amz-6-0-2-ai-precision-keyword-identification
description: 读取当前产品识别文本与6-0-1全部对标自然排名Observation，按Canonical Keyword只判断一次四级精准度，并依据共享配置输出A/B/C/D/E五类可追溯资产；不查询ERP或执行写操作。
metadata:
  short-description: AI精准关键词识别
---

# HZP Amazon 6-0-2｜AI精准关键词识别

Machine name: `hzp-amz-6-0-2-ai-precision-keyword-identification`  
English: AI Precision Keyword Identification

## Mission

Use the complete current-product text evidence and the formal 6-0-1 all-observation asset to let a Senior Amazon Marketplace Operator / Search Intent Expert AI judge each canonical Keyword once across all Benchmarks. The product text is the only current-product fact source for this judgment; 6-0-1 is the only keyword candidate source.

正式链路：

`05_分析源数据/01_产品数据/本产品/产品识别 - 文本文案.txt`（`CURRENT_PRODUCT_TEXT_EVIDENCE`） + 6-0-1 `BENCHMARK_KEYWORD_ALL_OBSERVATIONS` → one AI judgment per canonical Keyword → A 全量观察、B 配置筛选、C 对标内去重、D 去对标去重、E 按对标拆分。

## Goal-Driven Production Contract (V4)

用户调用 `6-0-2 {ProductCode}` 表示完成该产品的完整602目标，不表示处理一个Batch。唯一业务目标是：读取当前产品正式资料与最新601全部对标自然排名Observation，对全部Unique Canonical Keyword完成真实四级Precision Judgment，回填全部Observation，程序派生A/B/C/D/E，完成Schema、血缘、数量对账、Golden、回读和Publish。

完成条件只有全部Completion Criteria成立：Product Profile有效；601输入有效；所有Unique Keyword都有合法处理状态；所有SUCCESS都有合法FinalPrecision；全部Observation回填；配置和Alias正确；A/B/C/D/E完整；Unique/Observation对账通过；Golden PASS；正式文件回读通过；Publish成功。否则只能报告 `INCOMPLETE` 或 `PROGRESS`，不得把单个Batch完成报告为602完成。

当前执行本 Skill 的 Codex/Agent就是唯一Precision AI Judge。它直接读取Prepared Evidence，自主选择内部处理方法，完成 Searcher Purchase Mission、Purchase Mission Fit、Hard Conflict、Semantic Precision、Benchmark Reality、Decision Challenge 和FinalPrecision，再调用确定性Validation/Apply工具。正常入口不要求任何 `agent_judge`、`agent_batch_judge`、`precision_brain_client`、`external_ai_client`、第二阶段AI、CLI或Gateway。Python只有文件定位、Canonical/Observation处理、Schema、配置、派生、数量对账、保存和发布职责，没有Precision裁判权。

Batch、循环、Checkpoint、Resume只是内部实现细节。外部配置 `E:\【所有产品目录专用】\01_公共资料\03_系统配置\602_AI批次大小.txt` 只表示PreferredBatchSize；Agent可以因上下文、完整性或质量风险自主缩小。Checkpoint只用于防中断、避免重复和恢复有效结果，不是业务边界。只有真实宿主/Context/Tool Hard Limit才允许暂时中断；下一次同一Skill调用继续原Goal。

真实AI不可用时必须Fail Closed为 `INCOMPLETE` / `AI_PRECISION_JUDGMENT_UNAVAILABLE`，不得用Regex、Token Match、固定Score、Local Heuristic或Fallback生成四级Precision。

### Deprecated experimental paths

`run_codex_cli_production()`、`codex_cli_judge.py`、CLI Schema、Callback Push、Shared Gateway、Continuous Drain、复杂Production Queue，以及把 `agent_batch_judge` / `precision_brain_client`作为正常入口的路径，均为 `DEPRECATED_FOR_602_PRODUCTION` 或测试兼容层，不得进入正式主链。不得因保留兼容代码而改变唯一正式业务入口。

## Formal inputs

**Input A — Current Product Text Evidence**

Read the entire file at `05_分析源数据/01_产品数据/本产品/产品识别 - 文本文案.txt`. It is free-form product identification text, not a fixed schema. Use only facts actually present in the text to understand Product Type, Core Function, problem solved, structure, usage, target object, compatibility, critical attributes and constraints. Do not infer or fill facts from a keyword. If the file is missing, empty, or unreadable, stop and return respectively `CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND`, `CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY`, or `CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED`.

**Input B — 6-0-1**

Read the newest timestamped `6-0-1_所有对标自然排名关键词_YYYYMMDD_HHMMSS.csv` in the 6-0-1 `data/` directory. Select by the filename timestamp and validate the minimum schema and current Product identity. A registry, manifest, RunPackage, sidecar, or filesystem mtime is not a prerequisite for this analysis handoff.

Input B is Benchmark × Keyword Observation grain. Preserve every observation, including repeated Canonical Keywords from different Benchmarks. `产品编号` / `所属产品编号` is source Ground Truth: carry it unchanged to A and B; do not generate, renumber, replace with ASIN, or combine values. Keep each observation's ASIN and organic rank with its source row. `Id` is the source stable keyword entity (`KwId`), not a writable PickPwK row ID.

### 强制新批次规则

每次调用本 Skill 都必须重新生成一套新的 6-0-2 Run Package：创建新的 `RUN_ID`、`RUN_TIMESTAMP` 和 A/B/C/D/E 全部输出文件。不得因为已经存在 `VALID` 的 6-0-2、输入没有变化、当前仍是同一天、或上一次运行刚完成而跳过、复用或直接返回旧批次。旧批次必须保留；即使输入完全相同，也要重新读取当前产品文本和最新有效 6-0-1 输入，重新完成本次判断、写入、回读和校验。只有本次新批次自身通过完整校验后，才能标记为 `VALID`；失败必须写入新的 `FAILED` 运行记录，不能冒充成功或覆盖旧批次。

Before judgment, read the shared precision-filter configuration at `E:\【所有产品目录专用】\01_公共资料\03_系统配置\生成精准词库的要求.txt` (relative path `01_公共资料/03_系统配置/生成精准词库的要求.txt`) from the unified product root. The configured levels are the sole B/C/D/E selection source; normalize the business alias `已精准` to the existing AI label `精准`, record both raw and normalized values in the Run Manifest, and fail closed when the file is missing, unreadable or malformed. Then build one Unique Keyword Judgment Unit per Canonical Keyword, summarize benchmark coverage, best organic rank and median organic rank as Reality Evidence, and let AI judge that keyword once. Apply the same level and reason to every source observation for that Canonical Keyword. Benchmark count is not a vote. Product identity, search meaning and fit with the shopper's purchase task/object/occasion take priority; market capacity, competitor count and supply-demand ratio do not affect precision. Coverage and rank are supporting evidence only. If required source identity or observation data is invalid, fail closed; do not query ERP or generate keywords.

Before precision judgment, construct the model input from `build_dual_views_from_601_output(...)["ai_blind_rows"]`; do not pass the raw 6-0-1 rows to the judgment prompt. This AI blind view omits `竞争产品数` and `供需比`, while the untouched source rows remain available for output projection and integrity checks. These are output-only pass-through fields for market opportunity analysis. They must not raise or lower any precision level; do not infer precision from their value, ratio, or NULL state.

## Precision Judgment Kernel

必须读取并执行 `references/precision-judgment-kernel.md` 与 [`references/precision-brain-v3.md`](references/precision-brain-v3.md)。前者定义语义边界，后者定义结构化 Brain、两阶段证据、稳定 ID 和失败处理；不要另加一套分类规则。

Precision Brain 在同一 Run 先从 Current Product Ground Truth 识别一次 `PrimaryPurchaseDriver`（`FUNCTIONAL`、`COMPATIBILITY`、`GIFT_EMOTIONAL`、`AESTHETIC_DECOR`、`OCCASION`、`HYBRID`），再按 Driver 选择主要证据。内部记录 Gift Mission Evidence、Physical/Purchase Mission/Compatibility Convergence 和 Decision Challenge；这些字段属于审计证据，不改变 A/B/C/D/E 的正式 CSV Schema。

Build `CURRENT_PRODUCT_UNDERSTANDING` once from the complete product text through the current Codex/Agent's `PRODUCT_PROFILE_JUDGMENT` phase. Validate a Structured Product Profile before any keyword judgment; core fields such as Product Type, Primary Purchase Driver and Core Purchase Mission cannot remain `DATA_NOT_AVAILABLE`. If the current Agent cannot judge, stop with `AI_PRECISION_JUDGMENT_UNAVAILABLE`; if the profile is insufficient, stop with `PRODUCT_PROFILE_INSUFFICIENT` and do not publish A/B/C/D/E.

Then independently reconstruct each Amazon US searcher's intent before comparing it with the product. Distinguish `PRODUCT-LED`, `GIFT-LED`, `BROAD-GIFT`, `RELATIONSHIP-ONLY` and `HARD-SPECIFIED`; a Gift-led query does not need to contain figurine/statue/decor. Decide `CORE FIT` versus `CAN SERVE`, then check every explicit hard modifier (product type, material, quantity/representation, personalization, compatibility, size, function and theme). A hard conflict vetoes `高度精准`; a product-type conflict is normally `不精准`.

**Hard Modifier** 必须逐项核对。`gift`、`sister`、泛礼物、泛对象和泛场景必须按完整短语的 Search Intent 判断；搜索量、Benchmark 排名和词面重合都不能代替语义判断。

Do not use string matches, product-type explicitness, a fixed formula, word count or numeric scoring as the final decision; never calculate or map a 0–100 score. The semantic check is **Product–Search Intent Fit** plus Query Specificity, but product-type explicitness is not a proxy for either. Gift/relationship intent can be `高度精准` when it is the product's core reason to buy; broad demographic/occasion queries are usually `弱精准` because the product is only one possible answer. Benchmark Organic Rank is Market Reality Evidence only and never promotes or demotes the semantic level. Apply the counterfactual test (“would a shopper naturally see this as the kind of item they intended to buy, or merely something that could also be a gift?”), then AI直接裁决 and directly choose `高度精准`, `精准`, `弱精准` or `不精准`.

Every reason must be keyword-specific and state what the shopper wants plus why the product is CORE FIT, CAN SERVE or in conflict. Do not batch-apply one reason or one level to a keyword class; 不得复制通用理由. Use `REVIEW_REQUIRED` internally when evidence is insufficient; its `FinalPrecision` is blank/NULL and it is excluded from B/C/D/E, never converted to `弱精准`. The formal CSV contract remains unchanged. Calibration examples are in `references/calibration-cases.md` and are not executable keyword mappings.

## Execution method is internal

Agent may use `get_next_602_batch()`、`save_602_batch_judgments()` and the existing Checkpoint internally, but these are implementation helpers only. They must never become a user-visible Batch/Resume contract or a fixed stopping rule. `ConfiguredBatchSize` does not change the Precision Brain, FinalPrecision, Product Profile, Benchmark Reality or Decision Challenge. A runtime failure leaves work incomplete/PENDING and never fabricates FAILED business judgments.

Before reporting COMPLETE, the Agent must audit InputUnique, valid processed count, remaining unprocessed records, Observation backfill, configuration, A/B/C/D/E existence, Unique/Observation reconciliation, Golden PASS and Publish status.

## Output and trace

One run produces five asset classes of UTF-8 with BOM CSVs. Every CSV uses the same `RUN_TIMESTAMP`. A manifest records the configuration lineage and validation:

- A `6-0-2_精准判断所有词表_{RUN_TIMESTAMP}.csv`: all Benchmark × Keyword observations, with schema `所属产品编号,对标ASIN,Id,词,中文,市场容量,竞争产品数,供需比,自然排名,精准度,精准原因`.
- B `6-0-2_筛选后的对标精准词_{RUN_TIMESTAMP}.csv`: A filtered by the normalized levels in `生成精准词库的要求.txt`, retaining Benchmark observation grain.
- C `6-0-2_去重_筛选后的对标精准词_{RUN_TIMESTAMP}.csv`: B deduplicated by `所属产品编号 + Canonical Keyword`, retaining Benchmark identity and observation fields.
- D `6-0-2_去对标去重_筛选后的精准词_{RUN_TIMESTAMP}.csv`: B deduplicated by Canonical Keyword with Benchmark fields removed; this is the sole 6-0-3 input.
- E `6-0-2_{所属产品编号}_筛选后的精准词_{RUN_TIMESTAMP}.csv`: B split by exact Benchmark product number, retaining all configured precision levels; these are the 6-0-6 inputs.

The configuration path is fixed at `E:\【所有产品目录专用】\01_公共资料\03_系统配置\生成精准词库的要求.txt`. `已精准` is normalized to `精准`. Missing, empty or invalid configuration fails closed with `PRECISION_LIBRARY_CONFIG_NOT_FOUND`, `PRECISION_LIBRARY_CONFIG_EMPTY` or `CONFIG_PRECISION_LEVEL_INVALID`; real runs never silently use a default level. B/C/D/E are programmatic projections and make zero additional AI calls.

A and B must retain every source observation exactly once. Their product number, ASIN, keyword Id, keyword, translation, market facts and rank are source passthrough fields; precision and reason are the only AI-produced output fields. `INPUT_RECORD_COUNT` must equal A's `OUTPUT_RECORD_COUNT`. B is a strict filter of A; C is a programmatic projection from B; D files are programmatic filters of B by source product number. No later output calls AI. C Canonical Keywords and each D's Canonical Keywords must be unique. Market capacity, competitor count and supply-demand ratio in C are retained once rather than summed. Validate the full `A+B+C+D+N(E)` package, all schemas/counts, B filtering, C deduplication, D membership and per-benchmark uniqueness, total E coverage equal to B, and matching timestamps before marking the run VALID. Read back every CSV. Treat SQL NULL as a blank CSV cell, never as `0`.

The Run Manifest records the 601 Skill ID, `BENCHMARK_KEYWORD_ALL_OBSERVATIONS` identity and report name, 601 Run ID/timestamp/folder/file, input Observation count, Unique Keyword count, and the current-product text file path plus version fingerprint. Preserve the 6-0-1 and product-text source facts in lineage. If any output or validation fails, mark the 602 run FAILED so it cannot become Latest Valid.

The Run Manifest also records the shared precision-filter configuration path, raw configured labels, normalized labels, SHA-256, size and modification fingerprint. A later 6-0-3 resolver must compare the current shared configuration with this recorded selection before accepting the package.

Keep an internal Evidence Trace containing Canonical Keyword, keyword, current-product text path/version, Searcher Intent, convergence, Fit, conflicts, aggregated benchmark context, precision level and reason; it is not added to the CSV. 6-0-2 never performs ERP, Amazon, Listing, advertising, price or promotion writes and does not generate broad seeds, keyword clusters or advertising decisions.

No manual-precision CSV is generated. Existing historical manual files are not rewritten or deleted by this Skill. Use the maintained calibration examples in `references/calibration-cases.md` to align judgment boundaries; they guide the AI but are not executable keyword rules.

6-0-3 consumes only D (`去对标去重_筛选后的精准词`) from the newest timestamped 602 `data/` output. It must not use A, B, C or E as Intent input. 6-0-6 consumes the complete set of E assets plus the same-run 6-0-3 Intent Tree. 6-0-4 may consume the full judgment asset only under its own explicit ERP-sync safeguards; because `Id=KwId` is a cross-ProId keyword entity and not `PickPwK.Id`, it must fail closed unless a separately approved row-level identity expansion exists.

## Stage 6 artifact versioning

Resolve the 6-0-1 timestamped CSV from its `data/` directory with the simple resolver described above. 602 writes A/B/C/D/E into `06_SKILL分析报告/6-0-2_AI精准关键词识别/data/` (with the established report-governance layout), preserves historical runs, and validates schemas, coverage, filter derivation, and matching timestamps before publishing a valid batch. A RunPackage is lineage metadata, not a gate for downstream analysis.

## Precision Brain 增量硬契约

精准度判断对象是“搜索者是否正在寻找 Current Product 这种具体产品/解决方案”，不是一般语义相关性。必须区分 `RELEVANCE`、`SEMANTIC SIMILARITY`、`BENCHMARK ORGANIC RANK`、`SEARCH VOLUME` 与 `PURCHASE INTENT PRECISION`。

每个 Canonical Keyword 只判断一次，按以下顺序形成可审计记录：Search Intent → Shopping Intent Strength → Intent Convergence → Product–Intent Fit → Hard Conflict → Initial Precision → Benchmark Reality Check → Decision Challenge → Final Precision。Keyword 未表达的字段保持 UNKNOWN/NOT_SPECIFIED，不得补造。

Initial Precision 不读取排名；Benchmark 只作为 SUPPORTS、WEAKLY_SUPPORTS、NEUTRAL、CONTRADICTS 或 INSUFFICIENT 的 Reality Evidence，不能覆盖 Hard Conflict、投票决定等级或因排名好而自动升高。Final Reason 必须说明搜索者主要想买什么、意图是否收敛、产品如何匹配、是否存在冲突以及 Benchmark 的实际作用。

Decision Challenge 必须检查：是否把相关误当精准、是否只是宽泛 Category/Occasion/Recipient 词、购物意图是否不明确、是否存在 Hard Conflict、是否被多个 Benchmark 或排名锚定、去掉 Benchmark 后方向是否仍成立。Challenge 结果只能为 CONFIRMED、DOWNGRADED、UPGRADED、RECONSIDERED_NO_CHANGE。

内部 Judgment Record 至少保留 PrimaryPurchaseDriver、SecondaryPurchaseDrivers、PurchaseDriverReason、SearcherPrimaryIntent、ShoppingIntentStrength、IntentConvergence、ExpectedProductType、ExpectedCoreFunction、ExpectedRecipient、ExpectedOccasion、ExpectedInstallationMethod、ExpectedCriticalAttributes、HardConflictType、InitialPrecision、BenchmarkRealityAssessment、ChallengeResult、FinalPrecisionReason，以及 Gift Mission 和 Physical/Purchase Mission/Compatibility Convergence Evidence；这些是业务证据，不是隐藏思维链。

Batch 必须按模型上下文、Profile 长度、字段数量、历史截断/校验失败自适应规划；每个词使用稳定 JudgmentItemId 按 ID Join，失败时缩小批次重试，禁止静默接受缺字段或位置错配。任何 Precision Brain 修改必须运行 Golden Regression，并报告 ExactPrecisionMatch、MismatchCount、FalseHighPrecision、HighPrecisionRecall、GiftHighMissionFitRecall、FalseHighPrecisionRate、BroadGiftFalseHighPrecisionRate，并检查 Grade Compression。

## Human Report Publishing

本 Skill 生成正式 HTML 报告时，遵循统一的人类可见报告规则：Skill 报告根目录只保留一个当前最新 HTML；旧 HTML（以及同名 `.meta.json`）全部移动到同级 `历史HTML/`，不删除、不覆盖。一次性 Skill 的正式机器 CSV/JSON 只进入当前 Skill 报告目录的 `data/`，且只保留完整有效批次；Manifest、metadata、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`，用于血缘和审计而不是603/606取数前置门槛。HTML 仅按人类报告规则发布到根目录或 `历史HTML/`。完成写入、回读和校验后才发布当前报告；失败或不完整 Run 不得发布。公共实现与索引规则见 [`skills/references/human-report-publishing.md`](../references/human-report-publishing.md)。

## 全局报告文件治理（适用本 Skill）

本 Skill 遵循公共 `scripts/hzp_amz_report_contract.py`、[human-report-publishing.md](../references/human-report-publishing.md) 与 [report-governance.md](../references/report-governance.md)：正式机器业务数据只进入当前 Skill 报告目录的 `data/`，`data/` 只保留完整有效批次；旧批次整包进入 `历史数据/<RUN_TIMESTAMP>/`。系统 Manifest、metadata、稳定 Registry、日志只承担血缘与审计。新 Batch 必须先 Staging、验证完整性后再原子发布；失败不得替换旧 data。根目录只保留最新人类 HTML（如有）及正式子目录，机器数据不得写根目录。下游可通过简单 timestamp resolver 读取 `data/`，不得按 HTML 或根目录 mtime 选数。

602 的正式 Report Identity 为：`精准判断所有词表`、`筛选后的对标精准词`、`去重_筛选后的对标精准词`、`去对标去重_筛选后的精准词`以及每个 Benchmark 的`筛选后的精准词`。旧历史文件保留，不覆盖、不删除；新运行只使用上述新资产。

