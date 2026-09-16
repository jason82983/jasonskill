---
name: hzp-amz-6-0-2-ai-precision-keyword-identification
description: 读取当前产品识别文本与6-0-1全部对标自然排名Observation，按Canonical Keyword只判断一次精准度，输出三张公共表及每个对标一张高度精准表；不查询ERP或执行写操作。
metadata:
  short-description: AI精准关键词识别
---

# HZP Amazon 6-0-2｜AI精准关键词识别

Machine name: `hzp-amz-6-0-2-ai-precision-keyword-identification`
English: AI Precision Keyword Identification

## Mission

Use the complete current-product text evidence and the formal 6-0-1 all-observation asset to let a Senior Amazon Marketplace Operator / Search Intent Expert AI judge each canonical Keyword once across all Benchmarks. The product text is the only current-product fact source for this judgment; 6-0-1 is the only keyword candidate source.

正式链路：

`05_分析源数据/01_产品数据/本产品/产品识别 - 文本文案.txt`（`CURRENT_PRODUCT_TEXT_EVIDENCE`） + 6-0-1 `BENCHMARK_KEYWORD_ALL_OBSERVATIONS` → one AI judgment per canonical Keyword → A/B/C shared assets + one D high-precision asset per benchmark product number.

## Formal inputs

**Input A — Current Product Text Evidence**

Read the entire file at `05_分析源数据/01_产品数据/本产品/产品识别 - 文本文案.txt`. It is free-form product identification text, not a fixed schema. Use only facts actually present in the text to understand Product Type, Core Function, problem solved, structure, usage, target object, compatibility, critical attributes and constraints. Do not infer or fill facts from a keyword. If the file is missing, empty, or unreadable, stop and return respectively `CURRENT_PRODUCT_TEXT_EVIDENCE_NOT_FOUND`, `CURRENT_PRODUCT_TEXT_EVIDENCE_EMPTY`, or `CURRENT_PRODUCT_TEXT_EVIDENCE_READ_FAILED`.

**Input B — 6-0-1**

Read only `所有对标自然排名关键词` from the latest complete VALID 6-0-1 Run Package. Its formal asset identity is `BENCHMARK_KEYWORD_ALL_OBSERVATIONS`; accept only its timestamped package filename with the matching `RUN_TIMESTAMP`. Never use `BENCHMARK_KEYWORD_POOL` / `对标关键词母池`, a timestamp-less CSV, mtime selection, or a different 6-0-1 output. If the newest batch is invalid or incomplete, fall back to the newest complete VALID batch by `RUN_TIMESTAMP`.

Input B is Benchmark × Keyword Observation grain. Preserve every observation, including repeated Canonical Keywords from different Benchmarks. `产品编号` / `所属产品编号` is source Ground Truth: carry it unchanged to A and B; do not generate, renumber, replace with ASIN, or combine values. Keep each observation's ASIN and organic rank with its source row. `Id` is the source stable keyword entity (`KwId`), not a writable PickPwK row ID.

Before judgment, build one Unique Keyword Judgment Unit per Canonical Keyword, summarize benchmark coverage, best organic rank and median organic rank as Reality Evidence, and let AI judge that keyword once. Apply the same level and reason to every source observation for that Canonical Keyword. Benchmark count is not a vote. Product identity, search meaning and fit with the shopper's purchase task/object/occasion take priority; market capacity, competitor count and supply-demand ratio do not affect precision. Coverage and rank are supporting evidence only. If required source identity or observation data is invalid, fail closed; do not query ERP or generate keywords.

Before precision judgment, construct the model input from `build_dual_views_from_601_output(...)["ai_blind_rows"]`; do not pass the raw 6-0-1 rows to the judgment prompt. This AI blind view omits `竞争产品数` and `供需比`, while the untouched source rows remain available for output projection and integrity checks. These are output-only pass-through fields for market opportunity analysis. They must not raise or lower any precision level; do not infer precision from their value, ratio, or NULL state.

## Precision Judgment Kernel

必须读取并执行 `references/precision-judgment-kernel.md`。这是替换旧 Product-Type Explicitness 判断偏差的唯一内核；不要在此基础上另加一套分类规则。

Build `CURRENT_PRODUCT_UNDERSTANDING` once from the complete product text, then independently reconstruct each Amazon US searcher's intent before comparing it with the product. Distinguish `PRODUCT-LED`, `GIFT-LED`, `BROAD-GIFT`, `RELATIONSHIP-ONLY` and `HARD-SPECIFIED`; a Gift-led query does not need to contain figurine/statue/decor. Decide `CORE FIT` versus `CAN SERVE`, then check every explicit hard modifier (product type, material, quantity/representation, personalization, compatibility, size, function and theme). A hard conflict vetoes `高度精准`; a product-type conflict is normally `不精准`.

**Hard Modifier** 必须逐项核对。`gift`、`sister`、泛礼物、泛对象和泛场景必须按完整短语的 Search Intent 判断；搜索量、Benchmark 排名和词面重合都不能代替语义判断。

Do not use string matches, product-type explicitness, a fixed formula, word count or numeric scoring as the final decision; never calculate or map a 0–100 score. The semantic check is **Product–Search Intent Fit** plus Query Specificity, but product-type explicitness is not a proxy for either. Gift/relationship intent can be `高度精准` when it is the product's core reason to buy; broad demographic/occasion queries are usually `弱精准` because the product is only one possible answer. Benchmark Organic Rank is Market Reality Evidence only and never promotes or demotes the semantic level. Apply the counterfactual test (“would a shopper naturally see this as the kind of item they intended to buy, or merely something that could also be a gift?”), then AI直接裁决 and directly choose `高度精准`, `精准`, `弱精准` or `不精准`.

Every reason must be keyword-specific and state what the shopper wants plus why the product is CORE FIT, CAN SERVE or in conflict. Do not batch-apply one reason or one level to a keyword class; 不得复制通用理由. Use `REVIEW_REQUIRED` internally when evidence is insufficient; the formal CSV contract remains unchanged. Calibration examples are in `references/calibration-cases.md` and are not executable keyword mappings.

## Output and trace

One run produces three shared UTF-8 with BOM CSV assets plus one D asset per valid benchmark product number, all directly in the fixed 602 report root. Every CSV uses the same `RUN_TIMESTAMP`. The shared `6-0-2_RunPackage_{RUN_TIMESTAMP}.json` is the package metadata source; 602 does not create per-CSV `.meta.json` files:

- A `6-0-2_精准判断所有词表_{RUN_TIMESTAMP}.csv`: all Benchmark × Keyword observations, with schema `所属产品编号,对标ASIN,Id,词,中文,市场容量,竞争产品数,供需比,自然排名,精准度,精准原因`.
- B `6-0-2_高度精准词表_{RUN_TIMESTAMP}.csv`: derived only by filtering A where `精准度 == 高度精准`; it keeps observation grain and the source `所属产品编号`.
- C `6-0-2_去对标去重 高度精准词_{RUN_TIMESTAMP}.csv`: derived from B, one row per Canonical Keyword, with schema `Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准度,精准原因`. It has no benchmark identity fields. Its `Report_Identity` is `去对标去重 高度精准词`, its `Report_Key` is `UNIQUE_HIGH_PRECISION_KEYWORDS`, and it is the sole 6-0-3 keyword input.
- D one `6-0-2_{所属产品编号}_高度精准词_{RUN_TIMESTAMP}.csv` per valid source product number. Each D is filtered from B by exact `所属产品编号`, retains that field and all other A/B columns, and has unique Canonical Keywords within the benchmark. Product numbers are used unchanged.

A and B must retain every source observation exactly once. Their product number, ASIN, keyword Id, keyword, translation, market facts and rank are source passthrough fields; precision and reason are the only AI-produced output fields. `INPUT_RECORD_COUNT` must equal A's `OUTPUT_RECORD_COUNT`. B is a strict filter of A; C is a programmatic projection from B; D files are programmatic filters of B by source product number. No later output calls AI. C Canonical Keywords and each D's Canonical Keywords must be unique. Market capacity, competitor count and supply-demand ratio in C are retained once rather than summed. Validate the full `3+N` package, all schemas/counts, B filtering, C deduplication, D membership and per-benchmark uniqueness, total D coverage equal to B, and matching timestamps before marking the run VALID. Read back every CSV. Treat SQL NULL as a blank CSV cell, never as `0`.

The Run Manifest records the 601 Skill ID, `BENCHMARK_KEYWORD_ALL_OBSERVATIONS` identity and report name, 601 Run ID/timestamp/folder/file, input Observation count, Unique Keyword count, and the current-product text file path plus version fingerprint. Preserve the 6-0-1 and product-text source facts in lineage. If any output or validation fails, mark the 602 run FAILED so it cannot become Latest Valid.

Keep an internal Evidence Trace containing Canonical Keyword, keyword, current-product text path/version, Searcher Intent, convergence, Fit, conflicts, aggregated benchmark context, precision level and reason; it is not added to the CSV. 6-0-2 never performs ERP, Amazon, Listing, advertising, price or promotion writes and does not generate broad seeds, keyword clusters or advertising decisions.

No manual-precision CSV is generated. Existing historical manual files are not rewritten or deleted by this Skill. Use the maintained calibration examples in `references/calibration-cases.md` to align judgment boundaries; they guide the AI but are not executable keyword rules.

6-0-3 consumes only C (`去对标去重 高度精准词`) from the latest VALID 602 Run Package. It must not use A, B or D as Intent input. 6-0-6 consumes the complete set of D assets plus the same-run 6-0-3 Intent Tree. 6-0-4 may consume the full judgment asset only under its own explicit ERP-sync safeguards; because `Id=KwId` is a cross-ProId keyword entity and not `PickPwK.Id`, it must fail closed unless a separately approved row-level identity expansion exists. Neither downstream Skill changes this judgment contract.

## Stage 6 artifact versioning

Resolve 6-0-1 using `../references/stage6-artifact-contract.md` and the shared `scripts/stage6_artifact_contract.py`; validate current Product Root, Skill ID, `BENCHMARK_KEYWORD_ALL_OBSERVATIONS` identity, observation schema and complete package, then choose the latest VALID Run by `RUN_TIMESTAMP`, never by latest standalone CSV. 602 writes A/B/C/D directly into `06_SKILL分析报告/6-0-2_AI精准关键词识别/` and preserves each run with timestamped filenames and `6-0-2_RunPackage_{RUN_TIMESTAMP}.json`; it does not create a timestamp subfolder. A 602 batch is valid only when all three shared assets and all N expected D assets are present and validated.

## 全局正式报告目录与命名规则

本 Skill 面向确定 Product Root 生成正式报告或结构化分析报告时，统一保存到 `06_SKILL分析报告/{Skill编号}_{Skill中文正式名称}/`，文件名使用 `{Skill编号}_{报告名称}_{YYYYMMDD_HHMMSS}.{ext}`；同一运行的配套正式资产共用时间戳。6-0-1、6-0-2、6-0-3、6-0-5、6-0-6 的报告资产直接放固定 Skill 目录，不建时间戳子目录；6-2、6-3、6-4 可按每次运行建立 `YYYYMMDD_HHMMSS/` 子目录，子目录中的文件仍须带 Skill 编号前缀和时间戳。读取最新报告或运行包时按文件名/包内时间及有效性校验，不按文件修改时间选择。HTML 必须使用同批 CSV 回读快照渲染。历史报告不自动迁移或删除。跨产品公共知识、提醒状态、决策登记簿和运行日志等持续业务数据按各自数据契约保存，不作为 Product Root 正式分析报告迁移。
