---
name: hzp-amz-5-0-1-product-online-information-retrieval
description: Product-code-only retrieval of the current Amazon detail page, preserving raw online evidence and a clearly labelled AI semantic profile in a formal HTML report.
---

# HZP Amazon 5-0-1｜产品线上信息获取

## Contract

- **Input:** `product_code` only. The caller does not supply ASIN, marketplace, URL, title or SKU.
- **Identity source:** the current Product Root's official `01_产品档案.md`, using the shared Product Root and Identity Resolver rules. Never infer identity from a filename, search result, brand or product name.
- **Required identity:** a confirmed Marketplace and Current/Child ASIN. Missing or conflicting values stop normal retrieval with an explicit status.
- **Primary source:** the current product's Amazon detail page at the mapped marketplace domain and `/dp/{ASIN}`.
- **Output:** a UTF-8 formal HTML report in `06_SKILL分析报告/`; raw Amazon evidence and AI interpretation are separate layers.
- **Downstream:** `6-0-2｜AI精准关键词识别` reads the latest valid 5-0-1 report as preferred current-online evidence.

## Execution

1. Resolve Product Code to exactly one Product Root and read the official profile.
2. Resolve Marketplace and ASIN from confirmed profile/identity fields; retain variant, parent ASIN and SKU when present.
3. Reuse the repository's marketplace/domain mapping. Do not default to US. Build the detail URL only after identity is confirmed.
4. Run the Retrieval Controller in this order: `Discover → Retrieve → Validate → Coverage Audit → Completion Gate`. Discover all required modules before interpreting the product, then retrieve the public Amazon page with the browser/web/HTTP provider. If blocked, retry only Amazon detail/search/index routes using the exact ASIN. Third-party retail pages cannot substitute Amazon evidence.
5. Validate retrieved ASIN, marketplace, brand, title and selected variant against expected identity. A mismatch is `PRODUCT_IDENTITY_CONFLICT`; do not silently use it.
6. Collect all available identity, title, bullets, description, A+, images, video, price/promotion, variations, technical attributes, package, installation, compatibility, use cases, audience, claims, rating/review summary and Q&A. Preserve dynamic values with retrieval time and retain additional attributes.
7. Emit a per-section retrieval checklist for every required module. Each row contains `section_name`, `discovery_status`, `retrieval_attempted`, `retrieval_status`, `evidence_count`, `source`, `retrieved_at`, `failure_reason`, `retry_count`, and `notes`. Use only `RETRIEVED`, `PARTIAL`, `NOT_PRESENT`, `FAILED`, `BLOCKED`, `NOT_APPLICABLE`, or `NOT_CHECKED`; never turn an unattempted module into `NOT_PRESENT`.
8. Validate discovered-versus-parsed evidence (including bullet, image, A+ and dynamic-attribute counts). If parsed coverage is lower, mark `PARTIAL`. Image coverage separately records discovered/retrieved/analyzed/failed counts; A+ text without its images is `PARTIAL`; sibling variation facts never become current-child facts.
9. Run Coverage Audit and Completion Gate. `FULL_SUCCESS` requires zero `NOT_CHECKED` and no `PARTIAL`/`FAILED`/`BLOCKED`; `PARTIAL_SUCCESS` requires zero `NOT_CHECKED` but has one of those limitations; any `NOT_CHECKED` yields `INCOMPLETE_EXECUTION`; core identity/page failure yields `FAILED`. The HTML must expose these counts and the Section Coverage Matrix.
10. Freeze Raw Amazon Evidence before building an `Online Product Semantic Profile` only as `AI INTERPRETATION`. Do not rewrite raw facts, judge keyword precision, choose ads, price, budget, SEO, go/no-go, or perform ERP writes.

## Failure statuses

`PRODUCT_CODE_NOT_FOUND`, `PRODUCT_PROFILE_NOT_FOUND`, `ASIN_NOT_FOUND_IN_PRODUCT_PROFILE`, `MARKETPLACE_NOT_FOUND_IN_PRODUCT_PROFILE`, `PRODUCT_IDENTITY_CONFLICT`, `AMAZON_DETAIL_PAGE_NOT_RETRIEVED`, `PARTIAL`, and `FAILED` are explicit evidence states. Identity failures do not permit guessing. Profile-vs-online differences are recorded as `PROFILE_VS_ONLINE_CONFLICT` for downstream review.

## Report contract

The report starts with Layer 0 `Retrieval Coverage & Data Quality`, including a Retrieval Coverage Summary and Section Coverage Matrix. It then keeps Layer 1 `Current Product Raw Amazon Evidence` and Layer 2 `Current Product AI Semantic Interpretation`. The report is saved as `06_SKILL分析报告/5-0-1_产品线上信息获取/5-0-1_产品线上信息获取_{YYYYMMDD_HHMMSS}.html`. `6-0-2` can read the Overall Retrieval Status and matrix before judging keyword precision.

The implementation is in `scripts/online_information_retrieval.py`. Pass a real browser or HTTP fetcher to `run`; tests inject deterministic fetchers and never call Amazon.


## 全局正式报告目录与命名规则

本 Skill 的正式报告保存在当前 Product Root 的 `06_SKILL分析报告/5-0-1_产品线上信息获取/`，正式文件名以 `5-0-1_` 开头并使用 `YYYYMMDD_HHMMSS` 时间戳；不建立时间子目录。历史报告不自动搬迁或删除。

## Shared AI Brain

本 Skill 遵守仓库共享 AI Brain：`../references/ai-brain/README.md`。运行时按 `context-manifest.md` 声明 GLOBAL、DOMAIN、UPSTREAM、HISTORY、FORBIDDEN；本 Skill 的业务 Contract、正式 Ground Truth 和职责边界优先于泛化推理。AI Judgment 必须区分 Evidence 类型，重要判断先执行 Decision Challenge，再由 Reason Trace 生成原因；程序确定的数学、Join、去重、筛选、聚合、Schema、Identity、Timestamp、Latest 和 Read-back 不交给 AI 计算。
