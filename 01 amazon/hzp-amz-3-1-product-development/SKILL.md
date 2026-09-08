---
name: hzp-amz-3-1-product-development
description: Convert Amazon product research, customer evidence, samples, and supply-chain inputs into a testable product definition, specification, prototype plan, quality standard, and production handoff.
---

# HZP Amazon 3-1｜产品开发

## Purpose

Turn an approved or conditionally approved Amazon product opportunity into a product that can be specified, sampled, tested, revised, and handed to a factory. This Skill is the development stage after market research. It must keep source facts, design decisions, assumptions, test results, and approval gates separate.

## When to use

Use this Skill when the user wants to:

- continue from a product market research report into product development;
- define Product Definition V1, a product brief, or a requirement specification;
- convert reviews, returns, Q&A, or competitor weaknesses into product changes;
- plan samples, prototypes, tests, quality limits, or a factory handoff;
- review a sample and decide accept, revise, hold, or stop.

Do not repeat a complete market analysis when a valid research report is supplied. Do not treat this Skill as permission to order samples, contact suppliers, approve mass production, publish a listing, or launch advertising.

## Seamless handoff from product research

`3-1` is the direct downstream Skill of `2-1`. If `2-1-[ProductID]_HANDOFF.md` exists, read it first as the standard interface, then read the Human Report and raw files only as needed for verification or deeper work. Accept the output of `hzp-amz-2-1-market-research` as the starting point. Map its sections directly:

| Research output | Development input |
| --- | --- |
| GO / CONDITIONAL GO / NO-GO | development gate and scope |
| target user and core use case | user job and non-goals |
| review excerpts and pain points | failure modes and improvement requirements |
| Product Definition V1 | initial product brief and requirement IDs |
| development matrix | P0/P1/P2 feature priorities |
| Keepa, price, cost, and investment model | cost/price assumptions to verify, never confirmed profit |
| QMT questions and unknowns | supplier questions and test plan items |

Do not silently turn an inference into a requirement. In every 3-1 HANDOFF and formal output, use the canonical evidence labels `[FACT]`, `[INFERENCE]`, `[TO-VERIFY]`, and `[DECISION]`. The existing human-readable labels `资料事实`, `用户决定`, `开发假设`, and `待验证` may be shown alongside them, but do not replace the canonical labels. Never promote `[INFERENCE]` or `[TO-VERIFY]` without new evidence or an explicit HZP/QMT/user decision.

For a direct handoff, read the required Markdown HANDOFF first and use [templates/handoff-template.md](templates/handoff-template.md). The optional machine-readable compatibility file uses [references/handoff-schema.md](references/handoff-schema.md). If both the HANDOFF and report are missing, ask for them when the user expects a full development package; if the user explicitly requests a partial development, mark the package `部分证据` and list the missing evidence.

## Workspace and source priority

Use the shared product directory contract in [references/product-directory-contract.md](references/product-directory-contract.md). Every task should receive:

```text
产品根目录：<绝对路径>
产品相对目录：<相对于产品根目录的产品目录>
```

Resolve and verify `product_dir = 产品根目录 / 产品相对目录` with code before reading files. If the relative directory is missing, search by product code only when the result is unique; multiple or zero matches are a stop condition. Do not hardcode a drive or reuse a previous product directory.

Keep source materials read-only unless the user asks for annotation or cleanup.

- Source evidence: the supplied product materials root, including research reports, reviews, images, drawings, supplier files, cost notes, and test records.
- Development output: `product_dir\02 所有AI分析结果`. Do not write development results into `01 产品分析所需数据`.
- Manual boundary: prefer `手动判断开发方向.txt` inside `product_dir\01 产品分析所需数据` or `product_dir\02 所有AI分析结果`; it defines the user's intended direction, target scene, prohibited directions, must-have features, and decision priorities.
- Previous drafts: preserve them and create a new version when the change is material.

Before writing, report the supplied root, product-relative directory, verified product directory, input/output folders, manual direction file, and source files selected. Never put a product conclusion in a directory belonging to another product code.

## Core workflow

1. **Confirm the handoff.** Search the verified product workspace for `2-1-[ProductID]_HANDOFF.md`. If it exists, read it first, then verify ASIN/product code, report path, variation, marketplace, source dates, decision status, evidence labels, and missing evidence against the HTML report and raw files as needed. Do not silently discard upstream facts, requirements, risks, constraints, or decisions.
2. **Freeze the direction.** Separate the user's manual direction from analysis conclusions. Record prohibited scope and non-goals.
3. **Define the job.** State target user, use scene, trigger, desired outcome, and what the product must not attempt to solve.
4. **Build the evidence ledger.** For every proposed change, record source fact, customer impact, development hypothesis, cost/complexity risk, and validation method.
5. **Carry and refine Product Definition V1.** Use the upstream Product Definition V1 as the baseline. Specify the product form, core functions, measurable dimensions/performance, materials, appearance, packaging, cost target, price assumption, and P0/P1/P2 priorities. Use `数据缺失` or `待确认` instead of guessing.
6. **Plan prototypes.** Use a small number of versions. Each version must test a named hypothesis, such as packaging protection, weight reduction, stability, edge finish, or usability.
7. **Create the test plan.** Every test needs a requirement ID, method, sample size, owner, pass/fail threshold, result, and retest rule. If a threshold is unknown, write `待供应链/实验室确认`.
8. **Review samples.** Compare observed results to the requirement table. Mark `通过`, `不通过`, or `未测试`; link every failure to a corrective action and retest condition.
9. **Check feasibility.** Reconcile landed-cost components, tooling, MOQ, lead time, capacity, quality stability, packaging, and return/defect risk. Separate supplier quotes from assumptions.
10. **Make a gate decision.** Choose `继续打样`, `改版后再测`, `暂缓`, or `停止`. A conditional market decision is not approval for mass production.
11. **Write Product Definition V2.** After development decisions, sample evidence, and validation results, produce the current product definition. Mark every change from the 2-1 direction and keep unresolved specifications as `[TO-VERIFY]`.
12. **Prepare the handoff.** Deliver the controlled specification, BOM or component list, critical-to-quality points, inspection checklist, packaging requirements, open decisions, change log, and the required 3-1 HANDOFF.

## Required development outputs

For a substantial development task, write into `product_dir\02 所有AI分析结果`. Replace `[ProductID]` with the validated ASIN when available; otherwise use a stable, short product ID:

1. `3-1-[ProductID]_产品开发方案.html` — Human Report;
2. `3-1-[ProductID]_产品需求规格书-vN-YYYYMMDD.md` (use `.xlsx` only when the user needs a spreadsheet);
3. `3-1-[ProductID]_样品与测试计划-vN-YYYYMMDD.md` (use `.xlsx` when test rows need spreadsheet operation);
4. `3-1-[ProductID]_质量验收标准-vN-YYYYMMDD.md`;
5. `3-1-[ProductID]_开发变更记录.md`;
6. `3-1-[ProductID]_HANDOFF.md` — required AI Handoff;
7. `3-1-[ProductID]_product-handoff-vN-YYYYMMDD.json` — optional machine-readable compatibility file;
8. `3-1-[ProductID]_sources-used.txt` — source trace file.

Every formal output generated by this Skill must begin with `3-1-` and use the product ID plus output type. If a material revision needs a version/date, insert `-vN-YYYYMMDD` before the extension. Preserve historical files; do not rename old outputs merely to apply this rule.
The Human Report must show `HZP Amazon 3-1｜产品开发` near the title or in its report metadata as a subdued source marker.

Do not create empty placeholder files. If the user asks only for a development direction, create one consolidated result and do not fabricate a complete specification package.

Every output must contain:

- product code/ASIN, variation, marketplace, version, and date;
- `资料事实 / 用户决定 / 开发假设 / 待验证` labels;
- canonical evidence labels `[FACT]`, `[INFERENCE]`, `[TO-VERIFY]`, and `[DECISION]`, without upgrading an upstream evidence state;
- unresolved questions and the gate that depends on them;
- source filenames and paths sufficient for another Skill or employee to trace the decision.

### Required 3-1 HANDOFF content

Write `3-1-[ProductID]_HANDOFF.md` next to the Human Report using `templates/handoff-template.md`. It is the standard interface for `4-1 Sourcing & Production` and may also be read by future `5` Listing, `6` Launch & Growth, and `7` Inventory & Replenishment Skills. Keep it concise; do not copy the full HTML or the complete chat history.

The HANDOFF must contain:

- `# HZP AMAZON SKILL HANDOFF`;
- `## Metadata`: Product ID, ASIN, Product Name, Marketplace, Source Skill (`3-1`), Source Skill Name (`HZP Amazon 3-1｜产品开发`), Generated Date, and Next Recommended Skill (`4-1`);
- `## Decision`: current development status `GO / CONDITIONAL GO / HOLD / NO-GO`;
- `## Product Definition V2`;
- `## Target Customer` and `## Use Cases`;
- `## Confirmed Product Requirements`, `## P0 Requirements`, `## P1 Differentiators`, and `## P2 Enhancements`;
- `## Materials / Structure / Specifications`, recording only supported or confirmed values and marking unknowns `[TO-VERIFY]`;
- `## Sample Requirements` and `## Validation / Testing`;
- `## Risks`, `## Unknowns`, and `## Decisions Required`;
- `## Changes From 2-1`, when the development direction changes an upstream conclusion;
- `## Source Files` and `## Next Stage Instructions`.

Each statement must carry exactly one canonical status: `[FACT]`, `[INFERENCE]`, `[TO-VERIFY]`, or `[DECISION]`. `[DECISION]` is only for an explicit HZP/QMT/authorized-owner decision. Never invent dimensions, materials, thickness, hardness, structure, process, formulation, performance targets, test standards, cost, compliance, or supplier capability when the HANDOFF does not support them.

When new evidence changes a 2-1 conclusion, preserve the chain `上游结论` → `新证据` → `修改原因` → `新结论`; never silently overwrite it. The next-stage instruction must state which specifications are fixed, which cannot be changed, which require factory confirmation, which need quotation, which need production testing, and which risks require control.

## Requirement and test rules

- Make each requirement observable and testable. Replace “更高级”“更结实”“好用” with measurable criteria or `待确认`.
- Keep must-have, performance, experience, appearance, cost, packaging, compliance, and risk requirements separate.
- Do not invent dimensions, material performance, load limits, waterproofing, certifications, cost, test results, or supplier capability.
- Treat natural material variation, surface defects, color, and finish as acceptance criteria only after the user or supplier defines the allowed range.
- Do not claim a product is safe, compliant, patented, durable, waterproof, or certified without the relevant evidence.
- Do not copy competitor branding, artwork, protected design, or trade dress. Flag patent, trademark, copyright, and compliance questions for separate review.

## Cost and launch boundary

Use a cost table with currency and source for product cost, packaging, first-mile freight, FBA/fulfillment, referral fee, returns, defects, tooling, and other known components. Show missing fields explicitly. If contribution or break-even CPC is calculated, show the formula and mark any estimated CVR, CPC, price, or cost as an assumption. An investment screenshot is a scenario model, not realized profit.

Do not place orders, approve tooling, approve mass production, contact factories, upload listings, launch ads, or change live accounts without a separate explicit authorization. The normal stopping point is a reviewable development package and a clear next gate.

## Handoff to adjacent Skills

- Use the market research Skill for missing demand, competitor, keyword, review, or page evidence.
- Use the supply-chain workflow for factory capability, quotes, capacity, and manufacturing risk.
- Pass approved product requirements and verified claims to the listing/page workflow.
- Pass packaging, landed-cost, MOQ, lead-time, and reorder inputs to the inventory/shipping workflow when that Skill is available.
- Pass only verified price, contribution, conversion, and inventory constraints to promotion/ads workflows.

## Default development answer

Answer in Chinese and organize the decision as:

1. 开发结论与当前闸门；
2. 用户问题、目标场景与非目标；
3. 上游 Product Definition V1 与继承边界；
4. P0/P1/P2 需求与取舍；
5. 结构、材料、尺寸、包装或交互建议；
6. 样品版本与测试计划；
7. 质量验收标准；
8. 成本、工艺、交期、合规与 IP 待确认项；
9. Product Definition V2；
10. 开发变更记录、3-1 HANDOFF 与下一步。

When the user asks for a production-ready handoff, include copyable tables for requirements, BOM/components, tests, inspection, packaging, and open decisions.
