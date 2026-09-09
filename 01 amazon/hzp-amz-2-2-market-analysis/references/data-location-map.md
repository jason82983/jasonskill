# 2-2 Data Location Map

All paths below are relative to the resolved `Product Root`. Do not hard-code a drive letter, product name, or a specific employee computer.

## Product Root identification

Use the current working directory when it contains both `01_产品档案.md` and `05_分析源数据/`. If the current directory is a Product Root child, walk upward until that pair is found. If the current directory is a Products Root, use the user's product number/name from `01_产品档案.md` to select the matching Product Root. If more than one candidate matches and identity cannot be resolved, stop and ask the user; do not guess.

The usual Product Root shape is:

```text
[Product Root]/
├─ 01_产品档案.md
├─ 02_产品开发思路.md
├─ 03_产品页面思路.md
├─ 04_产品推广思路.md
├─ 05_分析源数据/
├─ 06_SKILL分析报告/
└─ 07_产品资料/
```

## Standard relative paths and layers

| Layer | Relative path | Read for | Priority |
|---|---|---|---|
| Product Identity Layer | `01_产品档案.md` | 产品编号、名称、本产品/Benchmark ASIN、已知角色 | first |
| Market Discovery Layer | `05_分析源数据/02_细分市场数据/所有细分市场/` | all ASIN-to-Niche membership exports, especially `NichesProductAppears` | first market scan |
| Market Validation Layer | `05_分析源数据/02_细分市场数据/[Niche]/` | Niche search terms, head products, product tab, core metrics, shares, feedback, returns | candidate Niches only |
| Product Evidence Layer | `05_分析源数据/01_产品数据/` | ASIN folders containing Keepa, Cerebro, Reviews, Listing, images, and other ASIN evidence | selected ASINs only |
| Supporting Evidence Layer | `05_分析源数据/03_关键词数据/`, `04_用户反馈/`, `05_补充资料/` | independent keywords, VOC/QA/Returns/community feedback, external or temporary evidence | as needed |
| Human Hypothesis Layer | `02_产品开发思路.md` | 人工开发想法 | hypothesis only |
| Shared Definition Layer | `[Products Root]/00_产品公用数据/01_Amazon平台资料/商机探测/` | Amazon metric definitions and terminology | definitions only |
| Analysis Output Layer | `06_SKILL分析报告/2-2_细分市场分析/` | 2-2 HTML and HANDOFF outputs | write here only |

## Discovery rules

- Scan `所有细分市场` recursively before opening individual Niche folders.
- Match a Niche detail folder by normalized Niche name (case, spaces, punctuation, and common naming differences), then verify its contents and headers.
- Match ASIN data by ASIN fields and readable content, not by role folder names. A single ASIN can carry Benchmark, Leader, or Competitor roles without duplicate source folders.
- For multiple dated files of the same type, use the newest matched file by default; read older files too when trend or role change analysis needs them. Never delete, rename, or overwrite old evidence.
- If a path exists, inspect it before asking the user where the data is. Ask only when Product Root, identity, version, parsing, or P0 evidence remains unresolved.

## Read/write boundary

All locations under `05_分析源数据/` and shared definition data are read-only for 2-2. Write only formal outputs under `06_SKILL分析报告/2-2_细分市场分析/`, preserving the `2-2-` filename prefix and existing reports.
