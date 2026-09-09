---
name: hzp-amz-0-1-product-file-structure
description: Create, check, organize, and safely migrate an Amazon Products Root Shared Data area or individual Product Root to the HZP Directory V1 structure while preserving original evidence and separating human input from Skill-generated analysis.
---

# HZP Amazon 0-1｜产品文件结构管理

## Purpose

This is the foundation Skill for the HZP Amazon workflow. It manages the file structure of one product project so that later research, development, listing, and promotion Skills can find the right inputs and outputs.

Its core rule is:

> **整理文件，不创造业务事实。**

This Skill can create folders, create lightweight blank templates, inspect files, classify evidence, move files, and rename files when the intended meaning is clear. It does not analyze a product, make a market or development decision, rewrite evidence, or invent missing product information.

## Three directory levels

Keep these levels separate:

1. **Products Root** — the common container for products and shared data;
2. **Shared Data** — `00_产品公用数据/`, one copy of reusable platform definitions, company standards, and non-sensitive system configuration;
3. **Product Root** — one product's identity, evidence, human input, and Skill outputs.

The governing rule is:

> **公共知识只保存一份，产品证据跟随产品。**

Do not copy Shared Data into each Product Root merely to make a later Skill easier to run.

## Scope and product identity

Work on one Product Root at a time. Use a directory explicitly supplied by the user first. Otherwise, start from the current working directory and search upward for `01_产品档案.md`. Do not scan unrelated drives or assume a fixed depth under a Products Root.

From a selected Product Root, search upward for a directory containing `00_产品公用数据/` and treat it as a Products Root candidate. A product may be directly under that directory or under an intermediate permissions/category folder. If there are multiple candidates, none, or an otherwise abnormal structure, report the candidates and ask the user to confirm; do not guess.

The primary product identity is the `产品编号` field in `01_产品档案.md`. The folder name, product name, ASIN, alias, and previous path are supporting clues only. If the identity cannot be established, stop and ask the user to choose or create the Product Root.

When creating a new product project, create `01_产品档案.md` with this minimum structure:

```markdown
# 产品档案

产品编号：
```

Fill the product number only when the user or an existing authoritative file clearly provides it. Leave all other unknown fields blank. Never guess an ASIN, product name, ERP number, store, owner, status, competitor ASIN, or other business fact.

## Products Root and Shared Data V1

When a Products Root is explicitly selected or safely identified, its shared-data structure is:

```text
[Products Root]/
├─ 00_产品公用数据/
│  ├─ 01_Amazon平台资料/
│  ├─ 02_公司标准/
│  └─ 03_系统配置/
└─ ... product directories ...
```

`01_Amazon平台资料/` contains external platform definitions and official explanations, such as Opportunity Explorer or Niche metric definitions. `02_公司标准/` contains internal cross-product judgment rules, evidence standards, SOPs, and product or profit requirements. `03_系统配置/` contains non-sensitive ERP, SQL, field-mapping, and query configuration. These are different evidence types and must not be silently mixed.

0-1 may create the three Shared Data folders when the user requests Products Root initialization or repair. It must not write platform definitions, company standards, credentials, or business conclusions into them. Passwords, Tokens, API Keys, and Secrets must come from a secure local mechanism rather than public Skill text or assumed plaintext files.

Shared Data is not a second copy of product evidence. Do not copy it into Product Roots. Other Skills should read the selected Product Root together with the selected Products Root's Shared Data at runtime.

## Product Directory V1

The standard structure is:

```text
[Product Root]/
├─ 01_产品档案.md
├─ 02_产品开发思路.md
├─ 03_产品页面思路.md
├─ 04_产品推广思路.md
├─ 05_分析源数据/
│  ├─ 01_产品数据/
│  │  ├─ 本产品/
│  │  └─ 对标产品/
│  ├─ 02_细分市场数据/
│  ├─ 03_关键词数据/
│  ├─ 04_用户反馈/
│  └─ 05_补充资料/
└─ 06_SKILL分析报告/
```

Create the five top-level source-data folders when creating or repairing the standard structure. Create niche, ASIN, report, and other deeper subfolders only when actual files or a requested output need them. Do not create a large collection of empty Skill-number folders in advance.

## Human input files

`02_产品开发思路.md`, `03_产品页面思路.md`, and `04_产品推广思路.md` are human-input files. Keep them lightweight. A suitable blank template is:

```markdown
# 产品开发思路

## 当前人工思路

提出人：
更新时间：

### 已有想法

### 特别关注

### 不希望做的方向

### 待 AI 重点验证

### 其他补充
```

Adapt the title and section wording for page or promotion thinking. Do not copy AI conclusions into these files. Do not turn an unconfirmed idea into `[FACT]`, a decision, or a product specification. If an old file is clearly a human-thinking file, preserve its text and may rename it to the corresponding standard file when the destination does not exist; report that rename.

`01_产品档案.md` is an identity file, not a place for analysis. `06_SKILL分析报告/` is the place for formal Skill outputs. This Skill itself does not generate a business `当前结论.md`.

## Evidence rules for `05_分析源数据`

`05_分析源数据` is an original-evidence repository. Original CSV, XLSX, XLS, TXT, PDF, images, DOCX, ZIP, and similar files may be read, classified, moved, and safely renamed. Their contents must not be rewritten, summarized over, or replaced by AI output. Never delete an evidence file, even when its category is unclear.

Classify by evidence type and research object, not by the Skill that may later read the file:

Always distinguish **Definition from Evidence**:

- A file answering “这个指标是什么意思？” is a platform or company definition and is a `SHARED-DATA-CANDIDATE` when found inside a Product Root.
- A file answering “这个产品或市场的指标是多少？” records product-specific evidence and stays in that Product Root.

For example, a general Opportunity Explorer metric glossary belongs in `00_产品公用数据/01_Amazon平台资料/商机探测/指标术语表/`. A Niche share screenshot for one product belongs in that product's `05_分析源数据/02_细分市场数据/[Niche]/`, even if it uses the same public metric.

### `01_产品数据`

- Files about the current product or its own ASIN go to `01_产品数据/本产品/`.
- Files clearly about one competitor or benchmark ASIN go to `01_产品数据/对标产品/[ASIN]/`.
- Keep that ASIN's Keepa, Cerebro, Reviews, listing, sales record, and investment inputs together when they are primarily used to study that ASIN.
- If a file is clearly about the whole market rather than an ASIN, use the market, keyword, feedback, or supplementary category instead.

### `02_细分市场数据`

Use one folder per Amazon Niche, plus `所有细分市场/` for cross-Niche tables such as the table showing where a product appears. Keep a Niche's head products, search terms, major metrics, share data, positive reviews, negative reviews, and return insights together. Do not split one Niche's evidence merely to make filenames look uniform.

### `03_关键词数据`

Use this for independent keyword or search-traffic research such as Cerebro, Magnet, Brand Analytics, Search Query Performance, search-term reports, and keyword trends. A Cerebro export that is clearly a single-ASIN research package may remain with that ASIN.

### `04_用户反馈`

Use this for general Amazon Reviews, VOC, Q&A, return reasons, consumer feedback, Reddit, forums, and similar consumer evidence. Reviews or return insights that are part of a specific Opportunity Explorer Niche stay with that Niche.

### `05_补充资料`

Use this for evidence that cannot be reliably classified above, including supplier material, inspection material, patent material, external research, temporary screenshots, and third-party files. An uncertain file belongs here rather than in a guessed category. Report the file as conservatively classified when applying a migration.

### Shared-data candidates found in a Product Root

In `CHECK`, `ORGANIZE`, and `MIGRATE`, flag an apparently reusable platform glossary, official explanation, company-wide standard, or common ERP field mapping as `SHARED-DATA-CANDIDATE`. Do not copy it. If its shared scope is clear and the Products Root is confirmed, propose moving one copy to the appropriate `00_产品公用数据/` category. If its scope is uncertain, leave it in place and ask the user to confirm.

## Shared data outside the Product Root

The environment may provide a company-level shared-data directory outside the Product Root, such as `00_产品公用数据/`. It can contain reusable platform definitions, company standards, field mappings, or other common material. This Skill may identify that such a directory exists, but must not copy shared data into every product or hardcode its path. Use it only when the user or runtime supplies the location.

## Formal Skill outputs

`06_SKILL分析报告/` contains processed Skill or AI deliverables, not original evidence. Organize actual outputs by Skill number and task, for example:

```text
06_SKILL分析报告/
├─ 2-1_产品分析/
└─ 2-2_细分市场分析/
```

Do not move original source exports into this directory. Do not create a report or `当前结论.md` merely because a Skill exists; there must be a real generated output. Historical reports must not be overwritten.

Recommended formal report filename:

```text
[Skill编号]-[产品编号]_[分析对象可选]_[报告类型]_[日期].html
```

If multiple formal versions are created on one day, use `_v1`, `_v2`, and so on only when needed. Preserve historical names and files during a migration.

## Operating modes

Support four explicit modes at either the Products Root or one Product Root:

1. **CREATE** — create a requested Products Root Shared Data skeleton or a Product Directory V1. Create only the standard folders for the selected level; leave unknown product fields blank.
2. **CHECK** — read-only inspection. Report Products Root candidates, Product Root identity evidence, missing or extra paths, misplaced-looking files, `SHARED-DATA-CANDIDATE` files, duplicate names, and possible historical files. Do not modify anything.
3. **ORGANIZE** — scan an existing Products Root or Product Root and produce a migration plan. Include the current tree, target tree, proposed new folders, every planned move or rename, uncertain classifications, shared-data candidates, and collision/overwrite risks. Do not apply the plan in this mode.
4. **MIGRATE** — apply a reviewed or explicitly requested plan after a fresh scan. Only create folders and move or rename files when every destination is checked and no overwrite or data-loss risk exists. Never copy Shared Data into a Product Root.

If the user's intent is ambiguous, prefer `CHECK` or `ORGANIZE`. Do not start a large migration merely because the directory looks old.

## Safe migration protocol

### SCAN

Before any change:

- verify the selected Product Root and `产品编号` evidence;
- identify and verify the Products Root candidate from `00_产品公用数据/`, when Shared Data management is in scope;
- enumerate all files and folders recursively, including hidden items where available;
- read lightweight text metadata when needed to determine purpose; do not alter source files;
- distinguish human input, original evidence, formal reports, generated media, and legacy indexes;
- distinguish platform/company definitions from product-specific evidence and flag shared candidates;
- identify duplicate names, existing destinations, ambiguous ownership, and important historical files.

### PLAN

Show the user:

- current Product Root and directory tree;
- target V1 tree;
- directories and templates to create;
- each move and rename, with source and destination;
- files placed conservatively in `05_补充资料`;
- `SHARED-DATA-CANDIDATE` files and a proposed Shared Data destination, if applicable;
- duplicate, overwrite, broken-link, and historical-file risks.

If a destination already contains a file, never overwrite it. Propose a distinct destination or stop for a user decision. If two files have the same name but different contents, keep both in separate history or source subfolders; do not merge them.

### APPLY

Apply only safe, explicit filesystem operations:

- create missing directories and blank standard templates;
- move files without changing their bytes;
- rename a file only when its purpose is clear and the destination is free;
- preserve original subfolders when that prevents collisions;
- move a confirmed shared definition to the selected Products Root only when the user requested migration and the destination is free; never copy it into Product Roots;
- remove a legacy directory only after verifying it is empty, and report that only an empty directory was removed.

Never delete a file, overwrite a destination, edit source evidence, rewrite a human note, fabricate an identity field, or treat an uncertain file as disposable. If a risk appears during APPLY, stop immediately and report the exact source and destination involved.

### VERIFY

After applying:

- enumerate the final complete tree;
- confirm every planned source file exists at its destination;
- confirm no files remain in an unintended legacy location;
- confirm required standard files exist and identity content was not guessed;
- confirm Shared Data remains outside Product Roots and no public/common file was duplicated;
- confirm original file count plus any newly created templates;
- report all moves, renames, conservative classifications, and empty-directory cleanup;
- state explicitly that no original evidence file was deleted or overwritten.

## Public Skill boundary

This Skill is intended for public distribution. Do not put private drive paths, database credentials, tokens, API keys, server addresses, company secrets, real customer data, or private product evidence in this file. Use `[Product Root]`, `[ProductCode]`, and `[ASIN]` placeholders. Runtime-specific paths and shared company data must be supplied by the user or environment.

## Response contract

For `CHECK`, return findings only and state that no changes were made.

For `ORGANIZE`, return the scan and plan before any filesystem mutation.

For `MIGRATE`, return:

1. the final complete tree;
2. every actual move and rename;
3. files conservatively placed in `05_补充资料` or otherwise not confidently categorized;
4. collision or unresolved-risk findings;
5. confirmation that no original evidence file was deleted or overwritten.

Use precise paths and distinguish facts from classification judgments. Do not report a guessed business fact as if it came from the file structure.
