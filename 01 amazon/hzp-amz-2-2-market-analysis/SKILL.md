---
name: hzp-amz-2-2-market-analysis
description: Analyze an Amazon product's real Niche or submarket from Opportunity Explorer data, representative ASIN evidence, search demand, competition, reviews, and returns, then decide whether a benchmark-based improvement project is worth entering and provide a structured input for product-opportunity development. Use when the task is to validate market scope, compare Niches, test improvement opportunities around a benchmark ASIN, or decide GO, CONDITIONAL GO, or NO-GO; do not use for single-ASIN diagnosis, detailed product design, listing copy, or supplier execution.
---

# HZP Amazon 2-2｜细分市场分析

## Purpose and boundary

This Skill determines which Amazon submarket a target product truly belongs to, whether that market has durable demand, how competition is structured, what consumers still need, and whether a differentiated new product has an entry opportunity. It produces a clear `GO`, `CONDITIONAL GO`, or `NO-GO` decision and a concise opportunity input for `HZP Amazon 3-1｜产品机会定义`.

It is a market-level Skill, not a second 2-1 single-ASIN report. Do not decide from a user-supplied Niche name alone, and do not let a user's preference determine the verdict.

Resolve `Product Root` before reading product data. Prefer the current directory when it contains `01_产品档案.md` and `05_分析源数据/`; otherwise walk upward from a Product Root child. If the current directory is a Products Root, locate the Product Root by the requested product number/name. If multiple candidates remain, stop and ask the user rather than guessing. All data paths in this Skill are relative to the resolved Product Root; never hard-code a drive letter or a particular employee computer. Read [references/data-location-map.md](references/data-location-map.md).

The default decision question is: “如果以这个对标产品为开发起点，在它背后的真实 Amazon 市场中进行改良开发，这个项目是否值得进入 3-1？” The benchmark is an analysis anchor and opportunity clue, never the market itself.

## Analysis modes

Use \`Benchmark-Driven Analysis Mode\` by default when \`01_产品档案.md\` contains an \`对标产品\` or \`对标新品\` role:

1. **Level 1 — Benchmark**: the proposed development starting point;
2. **Level 2 — Niche Leader**: the mature market reference;
3. **Level 3 — Niche**: the market demand and competition context.

Analyze these as \`Benchmark vs Leader vs Market\`, then ask what HZP should keep, improve, and refuse to copy. If no benchmark is confirmed, use \`Market-Driven Analysis Mode\`: validate the candidate market first and derive opportunities without inventing a benchmark. Do not block the Skill merely because a benchmark is absent.

## Boundary with 2-1 and 3-1

- **2-1 产品分析** explains why one benchmark product succeeds or fails from its history, keywords, listing, reviews, and product evidence.
- **2-2 细分市场分析** decides whether a market-entry project based on that benchmark is commercially worth pursuing, and validates whether its improvement opportunities are market-wide.
- **3-1 产品机会定义** turns the accepted opportunity into our own detailed product definition, structure, dimensions, materials, BOM, prototype plan, and validation standard.

2-2 may identify a market gap, consumer problem, improvement direction, and entry condition. It must not silently complete 3-1's detailed product design.

## Non-negotiable evidence rules

- `Definition ≠ Evidence`: read public Amazon metric definitions from Products Root Shared Data; read product and market values from the selected Product Root's `05_分析源数据/`.
- Prefer Amazon market behavior, then precisely matched third-party data, then user-supplied market labels, then AI inference.
- A mismatched market dataset is more dangerous than a missing dataset. If the match cannot be established, label it `[证据不足]` and exclude it from decisive calculations.
- Never turn BSR, review count, price, one keyword's search volume, or a sales estimate into an unverified market-size, sales, or profit fact.
- Label material statements as `[数据支持]`, `[分析推断]`, or `[待验证]`. Preserve the unified evidence state; an inference never becomes a fact without new evidence or explicit confirmation.
- Do not edit, overwrite, delete, or duplicate original source files.

Apply the source hierarchy and evidence labels in [references/evidence-priority.md](references/evidence-priority.md) whenever sources disagree or a market match is uncertain.

## Product identity and research roles

Start with `01_产品档案.md`. The stable product identity is `产品编号`; ASINs and their research roles are context metadata. An ASIN can simultaneously be an `对标产品`, `Niche 榜1`, `高速增长新品`, or another role, but its original data is read from one authoritative ASIN location. Never duplicate a dataset because roles differ.

If `01_产品档案.md` records a Niche leader, bind the role to its Niche and date. Treat that record as a research context that must be revalidated against current Niche data. A saved role is not permanent: do not silently repair the archive, but report a current role change when newer Amazon data disagrees.

## Input discovery

Use the resolved Product Root and standard relative paths. Read:

1. `01_产品档案.md` for identity and declared research roles;
2. `05_分析源数据/02_细分市场数据/所有细分市场/` first. This is the Market Discovery Layer and must be scanned for every valid `NichesProductAppears` file, across all research ASINs;
3. matching folders under `05_分析源数据/02_细分市场数据/[候选Niche]/` for core market data, head products, search terms, share data, positive/negative review insights, and returns;
4. `05_分析源数据/01_产品数据/` for the target, benchmark, leader, and representative ASIN packages;
5. `05_分析源数据/03_关键词数据/`, `04_用户反馈/`, and `05_补充资料/` when they contain additional evidence;
6. `[Products Root]/00_产品公用数据/01_Amazon平台资料/商机探测/` for metric definitions, without treating definitions as market values;
7. `02_产品开发思路.md` only as `[人工假设]`, never as market evidence.

The `所有细分市场` directory is a shared research pool, not a directory for only the benchmark ASIN. It may contain `NichesProductAppears` exports for the benchmark, leader, competitors, fast-growing products, and other representative ASINs. Discover files by path, filename pattern, readable headers/content, and ASIN fields together; do not require one fixed filename. A filename can locate a file, but cannot prove a Primary Market, Leader role, rank, or market importance. Read [references/asin-niche-discovery.md](references/asin-niche-discovery.md).

Keep original ASIN files together by ASIN. If the same ASIN is declared under several roles, read it once and annotate the roles in the report.

When Benchmark-Driven Mode is active, first resolve the benchmark ASIN and its role, then identify the current Niche leader or mature representative and the Niche-level data. If a dated 2-1 report exists, read and cite its conclusions and source evidence instead of recreating the full single-ASIN analysis. A leader is a reference point, not a second benchmark project.

## Required workflow

### 1. Data Readiness Check

Classify inputs before analysis:

- **P0**: the target product's Niche appearances from `所有细分市场`, at least one candidate Niche's core Amazon data, head products, main search terms, core market metrics, and click or brand concentration data;
- **P1**: Niche positive/negative/return insights, benchmark Keepa/Cerebro/Reviews/listing evidence, and current Niche leader evidence;
- **P2**: more representative ASINs, precisely matched third-party data, social or Google Trends data, and external industry data.

If the market boundary cannot be determined because P0 is missing or mismatched, stop the verdict and report `Data Readiness: STOP — [证据不足]`. For every checked standard location, report `FOUND`, `MISSING`, `UNREADABLE`, or `CONFLICT`, including the relative path and what is missing. If P1 is missing, continue only with an explicit confidence limitation. Do not add invented estimates to make the checklist complete. Read [references/data-readiness.md](references/data-readiness.md) and [references/data-location-map.md](references/data-location-map.md).

### 2. Market Discovery and Scope Validation (P0)

Follow this order: read the archive; scan all valid `NichesProductAppears` files; build the `ASIN → Niche` Relationship Map; identify every Niche containing the benchmark; cross-check overlaps with competitor and leader ASINs; locate each candidate Niche's detailed folder; then validate market scope. Use search terms, products actually receiving clicks or purchases, consumer use, product form, search intent, reviews/returns, and the target's real function. Classify each as:

- `Primary Market / 主市场`
- `Secondary Market / 次级市场`
- `Overlapping Market / 重叠市场`
- `Adjacent Market / 邻近市场`
- `False or Weak Match / 弱匹配或错误市场`

Do not select a market because its name sounds similar. Read [references/market-scope-validation.md](references/market-scope-validation.md).

The `ASIN → Niche` map must include ASIN, research role, Niche, relation to Benchmark, evidence source, and data date. Use it to distinguish a Niche shared by the benchmark and several competitors from a single-ASIN incidental appearance. The shared appearance count is supporting evidence only, not a Primary Market decision by itself.

For each candidate, perform `Primary Market Determination` from Amazon data and product fit: benchmark appearance, functional/use-scene match, search intent, head-product fit, click/purchase evidence, cross-ASIN overlap, and detailed Niche quality. Classify `Primary`, `Secondary`, `Overlapping`, `Adjacent`, or `Weak / False`; do not use row order or a user label as the decision. If two markets remain materially close and the choice would change the decision, report the conflict and ask for clarification instead of inventing certainty.

For Leader identification, use current Niche data that explicitly identifies a `榜1`, `Top Product`, `Top Clicked Product`, or equivalent head-product role. Bind every recorded role to `Niche + Data Date + evidence source`. If an appearance file only proves membership, continue to the Niche head-product/product-tab/Top Products data. If the role still cannot be proven, write `Leader = [待验证]`; never guess.

### Benchmark Definition (Benchmark-Driven Mode)

When a benchmark is confirmed, define the development anchor ASIN, its role, evidence period, and the dated 2-1 findings being reused. Record its strengths, weaknesses, growth signals, and unknowns. Never treat the benchmark's success as proof that the whole market is attractive.

### Improvement Opportunity Validation

For every potential improvement found in the benchmark, run this sequence:

1. **Benchmark Problem** — state the observed problem without proposing a solution;
2. **Evidence** — link benchmark Reviews, Niche negative reviews, returns, leader Reviews, search terms, or market data;
3. **Market Validation** — determine whether it is benchmark-specific or repeated across the market;
4. **Consumer Importance** — assess frequency, severity, and effect on purchase, rating, or return;
5. **Existing Solution Check** — verify whether the leader or another mature product already solves it;
6. **Commercial Opportunity** — assess possible conversion, rating, return, differentiation, use-scene, audience, or price effect;
7. **Development Handoff** — pass only supported opportunities and validation needs to 3-1.

Do not write “建议改良” without completing these checks. Use the matrix in [references/improvement-opportunity-validation.md](references/improvement-opportunity-validation.md). Classify improvement value as P0 (core development opportunity), P1 (valuable but not decisive), or P2 (optional enhancement). Do not manufacture differences merely to make the product look differentiated.

For every benchmark feature, also classify SHOULD KEEP, SHOULD IMPROVE, OPTIONAL DIFFERENTIATION, or SHOULD NOT COPY. These classifications express evidence-backed development input; they do not replace 3-1's detailed product definition.

### 3. Candidate Niche comparison

For every viable candidate Niche, compare demand, trend evidence, search conversion, price structure, product count, new-product count, successful new products, concentration, consumer intent, product fit, and entry conditions. Select a `Primary Entry Market`, optional `Secondary Opportunity Market`, and any `Avoid / Weak Match Market`. Do not force a single Niche when the evidence supports multiple entry paths. Deep-analyze Strong Candidate Niches first; a discovered Niche does not automatically require a full analysis.

When multiple ASIN exports exist, run `Cross-ASIN Niche Validation`: compare benchmark, competitors, leader, and other representative ASINs across their Niche sets, identify shared and unique Niches, and test the shared Niche against search intent, product fit, consumer evidence, and Niche-level quality. Read [references/asin-niche-discovery.md](references/asin-niche-discovery.md).

Use the following discovery order and narrow the scope before deep reading: resolve Product Root → read `01_产品档案.md` → scan `所有细分市场` → build Market Universe and relationship map → identify candidate Niches → read only matching Niche folders → classify markets → identify Benchmark, current Leader, and necessary competitors → read only those ASIN folders → read supporting layers as needed → write the report to `06_SKILL分析报告/2-2_细分市场分析/`. If a standard path exists, inspect it instead of asking the user where Keepa, Cerebro, Reviews, Niches, or Leader data are located.

### 4. Demand, size, and trend

Explain whether the market is large and mature, large but crowded, medium and healthy, small but high-margin, small and stagnant, growing, showing only a temporary/false increase, or seasonal. Use historical data when available. If only a snapshot exists, state: `当前只能判断市场截面，不能可靠判断长期趋势。`

### 5. Competition structure

Use available Amazon data to assess Top 5/20 product click concentration, Top 5/20 brand click concentration, brands, sellers, total products, new products, successful new products, and head-product maturity. Do not mechanically map high concentration to `NO-GO` or low concentration to `GO`; connect concentration to demand, new-product evidence, and differentiation space. Read [references/market-analysis-framework.md](references/market-analysis-framework.md).

### 6. Benchmark, leader, and consumer triangle

When a benchmark/new product and a Niche leader exist, compare:

- the Niche as a whole: what demand is actually purchased;
- the mature leader: the currently successful solution;
- the benchmark/new product: how it entered, what it changed, and whether its performance is reproducible.

Upgrade the triangle to four questions:

- **Market** — what consumers truly need;
- **Leader** — what mature products successfully solve;
- **Benchmark** — why this product can still grow and what it changed;
- **Our Opportunity** — what HZP should keep, improve, avoid copying, and validate.

The chain must be explicit: \`Market Need → Leader Solution → Benchmark Innovation / Weakness → Unmet Need → HZP Development Opportunity\`.

Use Keepa, Cerebro, Reviews, listing facts, images, and Niche feedback as available. Do not recreate a complete 2-1 report for every representative ASIN. Read [references/benchmark-vs-leader.md](references/benchmark-vs-leader.md).

Build a `Consumer Need Map` from Niche feedback, returns, benchmark Reviews, and leader Reviews: purchase motives, satisfaction points, recurring pains, return reasons, unmet needs, and opportunity implications. A small sample must be labeled `[样本有限]`; an individual review is not a market consensus. Read [references/consumer-need-analysis.md](references/consumer-need-analysis.md).

### 7. Price and opportunity

Describe the main price bands, dispersion, accepted premium, and common new-product pricing. Without real cost, FBA, advertising, and return-cost inputs, say only whether price space is worth further development; do not output true net profit.

For each opportunity, show:

`Evidence → Consumer Problem → Market Gap → Opportunity Type`

Opportunity types may include function, structure, material, size, style, use scene, audience, bundle, premium, low-price, installation, or packaging experience. Distinguish `[数据支持]` from `[分析推断]` and list supplier or prototype validation as `[待验证]`.

The market metrics in the preceding sections must answer what they mean for a benchmark-based improvement project: whether consumers are concentrated in mature solutions, whether a new entrant can acquire demand, whether an improvement can command a viable price, and what would make the project fail.

### 8. Decision

Apply the framework in [references/decision-framework.md](references/decision-framework.md):

- **GO**: market quality, demand, entry conditions, and differentiation are sufficiently supported;
- **CONDITIONAL GO**: market value exists, but named conditions such as pain-point resolution, cost, price position, keyword focus, or differentiation must be met;
- **NO-GO**: current evidence shows poor market quality, blocked competition, no credible differentiation, or an unattractive risk/return;
- **HOLD / STOP**: use only for missing or mismatched P0 evidence before a final GO/CONDITIONAL GO/NO-GO can be responsibly issued.

Do not use vague verdicts such as “可以考虑”.

### Benchmark-Based Entry Thesis

Before the final verdict, state the entry logic in eight answers:

1. Why this benchmark is the development starting point;
2. Which market demand it validates;
3. Which benchmark strengths should be kept;
4. Which benchmark problems are evidenced;
5. Which problems are market-wide rather than benchmark-specific;
6. Whether the leader already solves them;
7. Where HZP's improvement opportunity comes from;
8. Why a consumer could switch from the benchmark or leader to our product.

The thesis must connect benchmark evidence to a market opportunity and then to explicit development conditions. A benchmark weakness alone is not enough.

### 9. Output for 3-1

Write a concise `3-1 Product Opportunity Input` containing the primary and secondary markets, markets to avoid, target consumer, core buying motive, largest unmet need, must-solve pains, market gap, price position, differentiation direction, prohibited copying, risks, validation tasks, and GO conditions. Preserve unknowns and evidence states so `3-1` can supplement, validate, revise, or reject an inference without silently erasing its source.

If the benchmark is a new or fast-growing product, explicitly test whether growth is sustained, whether natural keyword coverage is expanding, whether review growth tracks the sales signal, whether rating is deteriorating, whether growth depends on low price or promotion, and whether new problems are emerging. If the history is too short, label the conclusion \`[持续性待验证]\`.

If the benchmark itself is the current Niche leader, mark \`Benchmark = Leader\` and do not duplicate the analysis. Add a second mature representative only when it resolves a specific comparison question.

The 3-1 input must additionally include: Benchmark ASIN, Benchmark Role, Benchmark Strengths to Keep, Benchmark Problems to Improve, Leader Strengths to Learn From, P0/P1 Improvement Opportunities, Do-Not-Copy List, Development Constraints, Validation Needed, and GO Conditions. It defines opportunity and constraints only; detailed structure, dimensions, materials, BOM, and final Product Definition belong to 3-1.

## Outputs and naming

Create formal outputs under the confirmed Product Root:

```text
06_SKILL分析报告/
└─ 2-2_细分市场分析/
   ├─ 2-2-[产品编号]_[分析对象可选]_细分市场分析报告_[YYYY-MM-DD].html
   └─ 2-2-[产品编号]_HANDOFF.md
```

Use the stable product number; include ASIN or Niche only when it clarifies the analysis object. Add `_v2`, `_v3` only for genuinely separate same-day formal versions. Never overwrite an existing report. The HTML must display `HZP Amazon 2-2｜细分市场分析` in its header or report metadata area.

The HANDOFF is a compact downstream interface, not a copy of the HTML. Use [templates/handoff-template.md](templates/handoff-template.md). It must preserve the decision, market scope, target consumers, JTBD/mother need, keyword demand clusters, competitor and leader evidence, pain points, opportunity definition, price position when supported, risks, unknowns, validation tasks, QMT/supplier questions, source files, and `Next Recommended Skill: hzp-amz-3-1-product-development`.

Use [templates/report-outline.md](templates/report-outline.md) for the report sections and [templates/html-report-style.md](templates/html-report-style.md) for a professional, readable HTML presentation.

## HTML report minimum structure

The first screen must answer:

- Product
- Benchmark ASIN
- Primary Market
- Development Mode: Benchmark-Based Improvement or Market-Driven Analysis
- Decision: GO / CONDITIONAL GO / NO-GO
- One-sentence answer to “是否值得基于该对标进行改良开发？”
- Why follow the benchmark
- Largest improvement opportunity
- Largest risk
- Key condition for entering 3-1

Use this order:

1. Executive Decision
2. Benchmark Definition
3. Market Scope Validation
4. Market Relationship Map
5. Candidate Niche Decision Table
6. Candidate Market Comparison
7. Market Quality
8. Competition Structure
9. Search Demand
10. Consumer Need Map
11. Benchmark Performance
12. Leader Reference
13. Benchmark vs Leader vs Market
14. Improvement Opportunity Matrix
15. Benchmark-Based Entry Thesis
16. Risks & Failure Conditions
17. GO / CONDITIONAL GO / NO-GO
18. Input for 3-1 Product Opportunity Definition
19. Evidence & Limitations

Write for investment decisions, product-development meetings, and team review: put conclusions first, trace key numbers to files, avoid data dumping, state action meaning and risk, and keep fact, inference, and verification separate.

## Safety and completion checks

Before finishing, confirm: Product Root identity; selected analysis mode; benchmark and leader roles when present; P0/P1/P2 readiness; market-match quality; ASIN-role consistency; no duplicate source copies; Niche + date for recorded leader roles; every improvement opportunity has market validation and an evidence grade; HTML and HANDOFF use the `2-2-` naming prefix; no original source was changed; and no old report was overwritten.

This Skill does not modify N24 or any other product unless the user separately instructs it to run the analysis.


