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

## Market research objects and roles

Market research must keep two concepts separate:

- **ASIN = stable research object identity**. An ASIN identifies one product record and does not change because the reason for studying it changes.
- **Role = dynamic research context**. A role explains why the ASIN is being studied at a particular time or in a particular Niche.

One ASIN may have several roles at the same time, for example `对标新品`, `Niche 榜1`, `高速增长新品`, or `高价代表产品`. Roles are metadata about the research context, not a second storage location. Do not create folders such as `榜1产品/`, `高速新品/`, or `机会产品/`, and do not copy one ASIN's Keepa, Cerebro, Reviews, or other source files because its role changes.

When a role is recorded, keep it lightweight and human-readable in `01_产品档案.md`. A `Niche 榜1` role must be bound to the specific Niche and, whenever known, the data date. Do not record `ASIN = 榜1` without that market context. A role may be recorded only from a user instruction, explicit Amazon Niche evidence, or a reliable downstream analysis result; 0-1 must not infer `榜1`, `头部`, or `高速增长` from BSR, review count, sales estimates, or filenames.

The role recorded in `01_产品档案.md` is a known research context, not a permanent market fact. Later market-research Skills must revalidate dynamic roles against current data. If a role is unknown, leave it blank or mark it `待确认`; do not block Product Root creation because no research object or Niche leader is known yet.

## Three directory levels

Keep these levels separate:

1. **Products Root** — the common container for products and shared data;
2. **Shared Data** — runtime `01_公共资料/` (legacy `00_产品公用数据/` is accepted when present), one copy of reusable platform definitions, company standards, and non-sensitive system configuration;
3. **Product Root** — one product's identity, evidence, human input, and Skill outputs.

The governing rule is:

> **公共知识只保存一份，产品证据跟随产品。**

Do not copy Shared Data into each Product Root merely to make a later Skill easier to run.

## Runtime Products Root and product areas

For HZP Amazon runtime work, the default Products Root is:

`E:\\【所有产品目录专用】\\`

Unless the user supplies another root explicitly, resolve a `Product_Code` only
within these three product areas:

```text
E:\\【所有产品目录专用】\\
├─ 03_已上架产品\\    # products already listed
├─ 02_新品待开发\\    # new products pending development
└─ 00_OtherSPro\\     # other products outside the first two areas
```

Each product folder immediately below one of these areas is a candidate Product
Root. Locate it by reading `01_产品档案.md` and matching its authoritative
`产品编号` / `Product_Code`; never use a folder name or area name as a
substitute for the identity field. If more than one candidate matches, report
the conflict and stop rather than guessing. A product's current area is
reported as a storage classification; 0-1 must not infer or rewrite business
status solely from the path, and must not move a product between the three
areas without an explicit instruction or an authoritative mapping decision.

`01_公共资料\\` at this root is shared company/platform material, not a fourth
product area. Existing legacy shared-data names such as `00_产品公用数据\\` or
`00_公共资料\\` remain compatibility candidates when actually present; do
not rename or duplicate them merely to match this runtime layout.

## Scope and product identity

Work on one Product Root at a time. Use a directory explicitly supplied by the user first. Otherwise, start from the runtime Products Root above and search only its three product areas for `01_产品档案.md`; do not scan unrelated drives.

From a selected Product Root, search upward for the runtime Products Root or an explicitly supplied shared-data root. A product may be directly under one of the three areas. If there are multiple candidates, none, or an otherwise abnormal structure, report the candidates and ask the user to confirm; do not guess.

The primary product identity is the `产品编号` field in `01_产品档案.md`. The folder name, product name, ASIN, alias, and previous path are supporting clues only. If the identity cannot be established, stop and ask the user to choose or create the Product Root.

When creating a new product project, create `01_产品档案.md` with this minimum structure:

```markdown
# 产品档案

产品编号：
产品名称：
站点：

## 市场研究对象

### 对标产品

- ASIN：
  角色：
  数据日期：

### 细分市场头部代表

- Niche：
  ASIN：
  角色：
  数据日期：
```

Fill only fields supported by the user or an existing authoritative file. Leave unknown fields blank. Multiple roles may be written under one ASIN; do not create duplicate ASIN entries merely to represent roles. Never guess an ASIN, product name, ERP number, store, owner, status, competitor ASIN, Niche, market rank, or other business fact.

## Products Root and Shared Data V1

When a Products Root is explicitly selected or safely identified, its current runtime shared-data structure is:

```text
[Products Root]/
├─ 01_公共资料/                 # current runtime shared-data name
│  ├─ 01_Amazon平台资料/
│  ├─ 02_公司标准/
│  └─ 03_系统配置/
└─ ... product areas ...
```

An existing `00_产品公用数据/` or `00_公共资料/` is a legacy compatibility
candidate; do not create it when `01_公共资料/` is the selected runtime area.

When the user requests Shared Data initialization, create the three folders and these blank guidance files if they do not already exist:

```text
01_公共资料/
├─ README.md
├─ 01_Amazon平台资料/平台资料模板.md
├─ 02_公司标准/公司标准模板.md
├─ 03_系统配置/系统配置模板.md
└─ 03_系统配置/sql-server-erp-connection.template.json
```

These are blank input templates, not platform definitions, company decisions, or system credentials. The SQL Server ERP JSON is a connection-shape template with placeholders and a secure credential reference; it must never contain a real password, token, or API key. Never overwrite an existing file with a template. Do not fill templates with guessed facts.

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
│  ├─ 05_补充资料/
│  └─ 06_广告数据下载/          # 广告系统原始导出，不是AI结论
├─ 06_SKILL分析报告/
│  └─ 广告表现汇报优化日志/       # 阶段6运行日志，不是正式报告
└─ 07_产品资料/
   ├─ 01_产品设计/
   ├─ 02_供应链与打样/
   ├─ 03_包装与说明书/
   ├─ 04_图片视频素材/
   └─ 05_合规与其他资料/
```

For a Product Root whose identity is confirmed, create the six top-level source-data folders and the five `07_产品资料` folders automatically when creating or repairing the standard structure. During an explicitly requested automatic organization, missing standard directories may be created before any file move. Create niche, ASIN, report, and other deeper subfolders only when actual files or a requested output need them. Do not create a large collection of empty Skill-number folders in advance.

### Current Product Attribute Source

Every Product Root's `05_分析源数据/01_产品数据/本产品/` is also a container for the confirmed current-product attribute source. During `CREATE`, and during `CHECK`, `ORGANIZE`, or `MIGRATE` when the standard structure is being completed, ensure this path exists and create the file `产品属性信息.txt` only when it is missing. The minimum local structure is:

```text
05_分析源数据/01_产品数据/本产品/
├─ 主图/
├─ 产品识别 - 文本文案.txt
└─ 产品属性信息.txt
```

The file is the `CURRENT_PRODUCT_ATTRIBUTE_SOURCE`: a human- or source-confirmed record of objective product facts for later Skills. Its initial contents are intentionally lightweight:

```text
【产品属性信息】

产品编码：
产品名称：

【基础属性】

【尺寸/规格】

【材质】

【数量/套装】

【结构/配件】

【安装/使用】

【兼容性】

【其他已确认属性】

【数据备注】
```

`产品识别 - 文本文案.txt` answers “这个产品是什么？” and carries identification text, description, functions, usage and product semantics. `产品属性信息.txt` answers “这个产品有哪些已经确认的客观属性？” and carries material, dimensions, weight, color, size, quantity, included components, structure, installation, compatibility, power and other confirmed attributes. They are separate sources; the attribute file is not Listing copy, marketing language, an analysis report, competitor evidence, or an AI guess. 0-1 creates the container and template only. It does not research or decide attributes. Later Skills may read or supplement it only from user, supplier/factory, specification, packaging, physical inspection, or other reliable confirmed evidence; unknown values remain blank or `待确认`.

This is a non-destructive rule: `Missing → Create`; `Existing → Preserve`. Never overwrite, clear, normalize, or replace an existing `产品属性信息.txt`, and do not alter `主图/`, `产品识别 - 文本文案.txt`, or other existing files merely because this container is being repaired. `CHECK` reports the file as missing without changing the product. `ORGANIZE` and `MIGRATE` may create the missing file/template as part of an explicitly requested structure completion, but must not move or classify historical product facts into it and must not fill any attribute. 5-0-1 may use `CURRENT_PRODUCT_ATTRIBUTE_SOURCE` as current-product factual evidence; 6-0-2 continues to consume the unified 5-0-1 evidence and does not create a second attribute source.

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

## Product assets in `07_产品资料`

`07_产品资料/` stores real business assets created or used while designing, sampling, producing, packaging, photographing, and proving compliance for this product. It is distinct from research evidence in `05_分析源数据/` and processed conclusions in `06_SKILL分析报告/`:

- `01_产品设计/` — design drawings, structure and dimension drawings, CAD/3D/STEP files, specifications, material, color, finish, function, and confirmed design revisions;
- `02_供应链与打样/` — supplier and factory files, quotations, BOM, cost files, sample photos, sampling versions, modification records, factory feedback, material samples, process confirmations, and production confirmations;
- `03_包装与说明书/` — packaging and dielines, box/label/FNSKU/UPC/EAN designs, manuals, installation instructions, warning labels, package dimensions, carton designs, and final print files;
- `04_图片视频素材/` — product photography originals, white-background and lifestyle images, model and render assets, AI candidate assets, video source and final videos, final listing images, A+ visuals, and brand-story visuals;
- `05_合规与其他资料/` — test and certification reports, SDS/MSDS, material proof, laboratory reports, patent or authorization files, compliance statements, safety files, and other product business material that cannot be classified above. Use this as the fallback when a file is confirmed to belong to the product but its specific 07 subcategory cannot yet be determined.

`07_产品资料/` is not a default miscellaneous folder. Classify by the file's primary business purpose: market, competitor, consumer, or keyword evidence stays in `05_分析源数据/`; Skill-generated formal analysis stays in `06_SKILL分析报告/`; the product's own design, supply chain, sampling, packaging, visual, or compliance assets go in `07_产品资料/`. If the file is confirmed as a product asset but its specific 07 subcategory is uncertain, place it in `07_产品资料/05_合规与其他资料/` and report that conservative fallback. If it is not possible to confirm that the file is a product asset at all, leave it in place and report it for confirmation.

Keep one authoritative copy of each original asset. Other Skills may read files directly across `05_分析源数据/`, `06_SKILL分析报告/`, and `07_产品资料/`; never copy an asset into another directory merely to make it easier to read. ERP data that is already managed in a structured system does not need to be exported into `07_产品资料/` just to satisfy the folder structure.

## Evidence rules for `05_分析源数据`

`05_分析源数据` is an original-evidence repository. Original CSV, XLSX, XLS, TXT, PDF, images, DOCX, ZIP, and similar files may be read, classified, moved, and safely renamed. Their contents must not be rewritten, summarized over, or replaced by AI output. Never delete an evidence file, even when its category is unclear.

Classify by evidence type and research object, not by the Skill that may later read the file:

Always distinguish **Definition from Evidence**:

- A file answering “这个指标是什么意思？” is a platform or company definition and is a `SHARED-DATA-CANDIDATE` when found inside a Product Root.
- A file answering “这个产品或市场的指标是多少？” records product-specific evidence and stays in that Product Root.

For example, a general Opportunity Explorer metric glossary belongs in `01_公共资料/01_Amazon平台资料/商机探测/指标术语表/`. A Niche share screenshot for one product belongs in that product's `05_分析源数据/02_细分市场数据/[Niche]/`, even if it uses the same public metric.

### `01_产品数据`

- Files about the current product or its own ASIN go to `01_产品数据/本产品/`.
- Files clearly about one competitor or benchmark ASIN go to `01_产品数据/对标产品/[ASIN]/`.
- Keep that ASIN's Keepa, Cerebro, Reviews, listing, sales record, and investment inputs together when they are primarily used to study that ASIN.
- If a file is clearly about the whole market rather than an ASIN, use the market, keyword, feedback, or supplementary category instead.
- The ASIN folder is the single source of truth for that ASIN's original data. If the same ASIN is both an `对标产品` and a Niche leader or growth example, keep one authoritative set of files and express the additional roles in metadata; never duplicate the files into role-named folders.
- Do not force research roles into filenames. Prefer stable names such as `Keepa_[ASIN]_[日期].xlsx`, `Cerebro_[ASIN]_[日期].csv`, and `Amazon_Reviews_[ASIN]_[日期].xlsx`.

### `02_细分市场数据`

Use one folder per Amazon Niche, plus `所有细分市场/` for cross-Niche tables such as the table showing where a product appears. Keep a Niche's head products, search terms, major metrics, share data, positive reviews, negative reviews, and return insights together. Do not split one Niche's evidence merely to make filenames look uniform.

### `03_关键词数据`

Use this for independent keyword or search-traffic research such as Cerebro, Magnet, Brand Analytics, Search Query Performance, and keyword trends. Original advertising Search Term / search-query exports belong in `06_广告数据下载/`; a Cerebro export that is clearly a single-ASIN research package may remain with that ASIN.

### `04_用户反馈`

Use this for general Amazon Reviews, VOC, Q&A, return reasons, consumer feedback, Reddit, forums, and similar consumer evidence. Reviews or return insights that are part of a specific Opportunity Explorer Niche stay with that Niche.

### `05_补充资料`

Use this for evidence that cannot be reliably classified above, including supplier material, inspection material, patent material, external research, temporary screenshots, and third-party files. An uncertain file belongs here rather than in a guessed category. Report the file as conservatively classified when applying a migration.

### `06_广告数据下载`

This is the raw-evidence location for original advertising files downloaded or exported from Amazon Advertising, Seller Central, SellerSpace / 优麦云, SellerSpace MCP `export_data`, or another reliable advertising source. Typical files include Search Term, Keyword, Campaign, Ad Group, Advertised Product, Placement, Targeting, Purchased Product, negative-target, hourly, daily, period-summary, and other Excel, CSV, or JSON reports. Keep the original bytes, original filename, and time information unchanged: do not overwrite, edit, delete, or write AI conclusions back into these files. Do not place AI diagnoses, recommendations, human decisions, execution records, or effect-validation logs here; those belong in `06_SKILL分析报告/广告表现汇报优化日志/`.

If a cleaned or aggregated intermediate file is necessary, label it explicitly as `派生数据` / `Derived Data` and keep its relationship to the original source. A live MCP query that does not create a file does not need to be exported solely for archiving. When an export is intentionally saved, its default destination is `[Product Root]/05_分析源数据/06_广告数据下载/`. Preserve historical snapshots and do not mechanically create duplicate daily exports.

For later stage-6 Skills, the unified source boundary is: SellerSpace MCP live read-only data and files in this raw-data directory are both evidence sources; AI diagnoses, recommendations, human decisions, execution records, and 1/3/7-day validation belong in `06_SKILL分析报告/广告表现汇报优化日志/`. If both evidence sources cover the same window but disagree, preserve both and report `【广告数据源冲突】` with source A, source B, window, metric name and definition, difference, possible cause, and suggested verification; do not silently select one. Raw advertising files are not formal Skill reports and are not candidates for the 0-2 report index. This is a directory/interface rule; it does not change the business logic of 6-1, 6-2, or 6-3.

### Role recording examples

Use the lightweight `市场研究对象` section in `01_产品档案.md` to express the research context:

```markdown
## 市场研究对象

### 对标产品

- ASIN：B0FZRQDRYS
  角色：对标新品

### 细分市场头部代表

- Niche：marble shelf
  ASIN：B0XXXXXXXX
  角色：榜1
  数据日期：2026-09-09
```

If the benchmark itself is the Niche leader, keep one ASIN entry and list both roles with their context:

```markdown
### 对标产品

- ASIN：B0FZRQDRYS
  角色：对标产品、marble shelf 榜1
  数据日期：2026-09-09
```

If one ASIN is also a growth example, append that role to the same entry. If the benchmark and the Niche leader are different ASINs, record two objects; neither object should be copied into a role-named directory. These are research-context records only. A later 2-2 market-analysis Skill must validate the current Niche, rank, and growth status again rather than treating this file as a permanent market fact.

### Shared-data candidates found in a Product Root

In `CHECK`, `ORGANIZE`, and `MIGRATE`, flag an apparently reusable platform glossary, official explanation, company-wide standard, or common ERP field mapping as `SHARED-DATA-CANDIDATE`. Do not copy it. If its shared scope is clear and the Products Root is confirmed, propose moving one copy to the appropriate `01_公共资料/` category. If its scope is uncertain, leave it in place and ask the user to confirm.

## Shared data outside the Product Root

The environment may provide a company-level shared-data directory outside the Product Root, normally `01_公共资料/` in the current runtime (or a legacy `00_产品公用数据/` / `00_公共资料/`). It can contain reusable platform definitions, company standards, field mappings, or other common material. This Skill may identify that such a directory exists, but must not copy shared data into every product or hardcode its path. Use it only when the user or runtime supplies the location.

### Amazon product/store identity mapping

When the supplied Products Root contains `01_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`, register it as the read-only **Amazon 产品与 SellerSpace 店铺身份映射主表**. The workbook's required sheets are `产品店铺映射`, `填写说明`, `产品对应变体`, and `店铺产品代码前缀`. Key fields include `Product_Code`, `Product_NewCode`, `Product_Name`, `广告组合`, `SellerSpace_Store`, `Marketplace`, `ASIN`, `SKU`, `Status`, `Var_Code`, `Var_Name`, and `Product_Code_Prefix`. Do not copy it into Product Roots or modify its rows, fields, or status values. 0-1 only defines the location and performs a read-only schema/existence check; it does not derive a formal code from a prefix or make a store decision. Missing sheets/fields are reported as `[Amazon经营身份映射结构不完整]`; multiple ACTIVE rows are reported for human confirmation. The shared resolution and SellerSpace secondary-verification contract is in the Amazon industry shared file `Amazon广告身份解析规则.md`.

`00_公共资料/` and `00_产品公用数据/` remain accepted legacy names when actually present; do not rename them or move the workbook merely to match the current runtime label. When the Products Root is explicitly supplied, CHECK must inspect `01_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx` first, then report any legacy path separately.

## Formal Skill outputs

`06_SKILL分析报告/` contains processed Skill or AI deliverables, not original evidence. Its formal-report classification uses one first-level folder per Skill, named `[Skill编号]_[Skill中文名称]`. The one fixed exception is `广告表现汇报优化日志/`, which stores high-frequency stage-6 operational logs and is not a formal-report folder:

```text
06_SKILL分析报告/
├─ 广告表现汇报优化日志/       # Operational Logs; excluded from formal-report indexing
├─ 2-1_产品分析/
└─ 2-2_细分市场分析/
```

Create the operational-log directory for every confirmed Product Root. Create a formal Skill folder only when that Skill has actually produced a formal report for the Product Root. Do not pre-create empty folders for future Skills. Do not create other unnumbered category folders such as product analysis, page analysis, market analysis, history/archive/index folders. Do not move original source exports into a formal Skill folder. The 0-2 report-index Skill must exclude `广告表现汇报优化日志/` from formal-report scanning; logs may be read as stage-6 evidence but never replace a versioned formal report.

Historical reports stay in the same Skill folder and are distinguished by the date in their filenames. Never overwrite or delete an existing formal report. `当前结论.md` is not a required 0-1 file; the newest dated formal report is the current report for that Skill. Do not create a report or any report folder merely because a Skill exists; there must be a real generated output.

Required formal report filename:

```text
[Skill编号]-[产品编号]_[分析对象可选]_[报告类型]_[日期].html
```

The Skill number must also be the first part of the destination folder name. For example:

```text
06_SKILL分析报告/
└─ 2-1_产品分析/
   ├─ 2-1-N24_B0FJRYJH1J_产品分析报告_2026-09-01.html
   └─ 2-1-N24_B0FJRYJH1J_产品分析报告_2026-09-09.html
```

Use the stable product number in the filename; include an ASIN or other analysis object only when useful. Do not add a version suffix by default. If multiple formal versions are genuinely created on the same date, append `_v2`, `_v3`, and so on. Preserve historical names and files during a migration.

## Operating modes

Support four explicit modes at either the Products Root or one Product Root:

1. **CREATE** — create a requested Products Root Shared Data skeleton or a Product Directory V1 inside one of the three product areas. For a Product Root, create the standard 01–07 structure, the six `05_分析源数据` subfolders including `06_广告数据下载/`, the five `07_产品资料` subfolders, and `06_SKILL分析报告/广告表现汇报优化日志/`; leave unknown product fields blank.
2. **CHECK** — read-only inspection. Search the three product areas under `E:\【所有产品目录专用】\`, report each Product Root's identity and current area (`03_已上架产品`, `02_新品待开发`, or `00_OtherSPro`), then report missing or extra paths, including missing `05_分析源数据/06_广告数据下载/` or `广告表现汇报优化日志/`, misplaced-looking files, `SHARED-DATA-CANDIDATE` files, duplicate names, and possible historical files. A legacy Product Root missing this new directory is a reported compatibility gap, not a destructive error. Do not modify anything.
3. **ORGANIZE** — scan an existing Product Root in one of the three areas and produce a migration plan. Include the current area, current tree, target tree, proposed new folders, every planned move or rename, uncertain classifications, shared-data candidates, and collision/overwrite risks. If the user explicitly requests automatic structure creation, create missing standard directories, including `05_分析源数据/06_广告数据下载/` and `广告表现汇报优化日志/`, for a confirmed Product Root. Preserve its current area unless the user explicitly requests a category move; do not modify, overwrite, delete, or casually rename an existing raw advertising file; do not move an uncertain historical file.
4. **MIGRATE** — apply a reviewed or explicitly requested plan after a fresh scan. Create missing `05_分析源数据/06_广告数据下载/` and operational-log directories within the Product Root's current area. Move a historical file into the raw-advertising directory only when it is reliably an original advertising download/export; move a file into the operational-log directory only when its stage-6 log purpose is reliable. Do not move the Product Root between the three areas without explicit instruction or authoritative mapping. Check the destination and do not overwrite or risk data loss. If a file's purpose is unclear, leave it in place, mark it `【需人工确认】`, and report it. Never copy Shared Data into a Product Root.

If the user's intent is ambiguous, prefer `CHECK` or `ORGANIZE`. Do not start a large migration merely because the directory looks old.

## Safe migration protocol

### SCAN

Before any change:

- verify the selected Product Root, its current one of three product areas, and `产品编号` evidence;
- identify and verify the runtime Products Root and its shared-data area (`01_公共资料/`; accept an existing legacy shared-data name when explicitly supplied), when Shared Data management is in scope;
- enumerate all files and folders recursively, including hidden items where available;
- read lightweight text metadata when needed to determine purpose; do not alter source files;
- distinguish human input, original evidence, formal reports, product assets, generated media, and legacy report folders or index files;
- classify each file by primary purpose across `05_分析源数据/`, `06_SKILL分析报告/`, and `07_产品资料/`; treat `05_分析源数据/06_广告数据下载/` as the dedicated destination for reliably identified original advertising downloads/exports, and `06_SKILL分析报告/广告表现汇报优化日志/` as the dedicated destination only for reliably identified stage-6 operational logs; do not use `07_产品资料/` as a catch-all;
- inspect `01_产品档案.md` for `市场研究对象` metadata, keeping ASIN identity separate from roles and checking that every `榜1` role has a Niche and data date when known;
- detect role-named folders, role-prefixed filenames, duplicated ASIN source files, and conflicting ASIN entries as structure risks; do not infer or silently repair a market role;
- distinguish platform/company definitions from product-specific evidence and flag shared candidates;
- identify duplicate names, existing destinations, ambiguous ownership, important historical files, and unnumbered legacy report categories.

### PLAN

Show the user:

- current Product Root and directory tree;
- target V1 tree;
- directories and templates to create;
- each move and rename, with source and destination;
- files placed conservatively in `05_补充资料`;
- historical files proposed for `06_SKILL分析报告/广告表现汇报优化日志/`, with the evidence that they are stage-6 operational logs; uncertain files stay at their current paths;
- original advertising files proposed for `05_分析源数据/06_广告数据下载/`, with the evidence that they are raw downloads/exports; uncertain files stay at their current paths;
- files proposed for `07_产品资料/` with the specific subfolder and classification reason; use `05_合规与其他资料/` as the fallback for confirmed product assets whose subcategory is uncertain;
- any duplicate or copied asset that would violate the single-source-of-truth rule;
- any duplicate ASIN data caused by research roles, any role-named evidence folder, any role-prefixed source filename, and any `榜1` record missing its Niche or data date;
- any role metadata that is user-confirmed, source-supported, or still `待确认`; do not turn a role classification into a market conclusion;
- `SHARED-DATA-CANDIDATE` files and a proposed Shared Data destination, if applicable;
- duplicate, overwrite, broken-link, historical-file, and legacy-category risks;
- for every legacy report, the evidence that supports its destination Skill folder; if the Skill cannot be confirmed, leave it in place and report it as unresolved.

If a destination already contains a file, never overwrite it. Propose a distinct dated filename or stop for a user decision. If two files have the same name but different contents, keep both at their current paths or stop for a user decision; do not create a history/archive subfolder or merge them.

### APPLY

Apply only safe, explicit filesystem operations:

- create missing directories and blank standard templates;
- move files without changing their bytes;
- rename a file only when its purpose is clear and the destination is free;
- move a legacy formal report directly into its confirmed `[Skill编号]_[Skill中文名称]` folder only when its source Skill is clear and the dated destination is free;
- move a historical advertising report, diagnosis, recommendation, execution record, or effect-validation log into `06_SKILL分析报告/广告表现汇报优化日志/` only when its stage-6 operational-log purpose is reliable and the destination is free; otherwise leave it in place and report it;
- move an original advertising download/export into `05_分析源数据/06_广告数据下载/` only when its raw-evidence purpose is reliable and the destination is free; preserve bytes and never mix AI analysis or operational logs into that directory;
- move a confirmed product asset directly into the appropriate `07_产品资料/` subfolder when its primary purpose is clear and the destination is free; when only product ownership is clear, move it to `07_产品资料/05_合规与其他资料/` and record the conservative classification;
- move a confirmed shared definition to the selected Products Root only when the user requested migration and the destination is free; never copy it into Product Roots;
- list empty legacy report directories as candidates for removal, but do not remove them in the same operation; deletion requires a separate explicit user approval after the scan.

Never delete a file, overwrite a destination, edit source evidence, rewrite a human note, fabricate an identity field, or treat an uncertain file as disposable. If a risk appears during APPLY, stop immediately and report the exact source and destination involved.

### VERIFY

After applying:

- enumerate the final complete tree;
- confirm every planned source file exists at its destination;
- confirm every migrated report is in its confirmed numbered Skill folder and no unresolved file was moved;
- confirm required standard files exist and identity content was not guessed;
- confirm one authoritative original-data set per ASIN, that research roles remain metadata rather than folder or filename categories, and that `榜1` records retain their Niche and data date;
- confirm Shared Data remains outside Product Roots and no public/common file was duplicated;
- confirm `07_产品资料/` contains product assets only and no original asset was duplicated into `05_分析源数据/` or `06_SKILL分析报告/`;
- confirm original file count plus any newly created templates;
- report all moves, renames, conservative classifications, unresolved legacy files, and any separately approved empty-directory cleanup;
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

## 全局正式报告目录与命名规则

本 Skill 面向确定 Product Root 生成正式报告或结构化分析报告时，统一保存到 `06_SKILL分析报告/{Skill编号}_{Skill中文正式名称}/`，文件名使用 `{Skill编号}_{报告名称}_{YYYYMMDD_HHMMSS}.{ext}`；同一运行的配套正式资产共用时间戳。6-0-1、6-0-2、6-0-3、6-0-5、6-0-6 的报告资产直接放固定 Skill 目录，不建时间戳子目录；6-2、6-3、6-4 可按每次运行建立 `YYYYMMDD_HHMMSS/` 子目录，子目录中的文件仍须带 Skill 编号前缀和时间戳。读取最新报告或运行包时按文件名/包内时间及有效性校验，不按文件修改时间选择。若 HTML 由同批 CSV 生成，必须从文件名时间戳相同的 CSV 读取并生成不可变快照；禁止运行时另找“最新 CSV”。未由 CSV 构成输入的 HTML 报告遵循对应 Skill 的原有报告内容逻辑。此规则优先于本文档中旧的目录和文件名示例。历史报告不自动迁移或删除。跨产品公共知识、提醒状态、决策登记簿和运行日志等持续业务数据按各自数据契约保存，不作为 Product Root 正式分析报告迁移。
