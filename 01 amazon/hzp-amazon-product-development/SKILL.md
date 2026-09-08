---
name: hzp-amazon-product-development
description: Convert Amazon product research, customer evidence, samples, and supply-chain inputs into a testable product definition, specification, prototype plan, quality standard, and production handoff.
---

# HZP Amazon Product Development

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

Accept the output of `hzp-amazon-product-market-research` as the starting point. Map its sections directly:

| Research output | Development input |
| --- | --- |
| GO / CONDITIONAL GO / NO-GO | development gate and scope |
| target user and core use case | user job and non-goals |
| review excerpts and pain points | failure modes and improvement requirements |
| Product Definition V1 | initial product brief and requirement IDs |
| development matrix | P0/P1/P2 feature priorities |
| Keepa, price, cost, and investment model | cost/price assumptions to verify, never confirmed profit |
| QMT questions and unknowns | supplier questions and test plan items |

Do not silently turn an inference into a requirement. Each requirement must carry one of these labels: `资料事实`, `用户决定`, `开发假设`, `待验证`.

For a direct handoff, read the report and create `product-handoff-v1-YYYYMMDD.json` using [references/handoff-schema.md](references/handoff-schema.md). If the report is missing, ask for it when the user expects a full development package; if the user explicitly requests a partial development, mark the package `部分证据` and list the missing evidence.

## Workspace and source priority

When a product code or product directory is supplied, resolve the exact product materials root before reading files. Keep source materials read-only unless the user asks for annotation or cleanup.

- Source evidence: the supplied product materials root, including research reports, reviews, images, drawings, supplier files, cost notes, and test records.
- Development output: `<product materials root>\05 开发方向分析` unless the user provides a valid `build product path.txt` with another directory.
- Manual boundary: prefer `手动判断开发方向.txt`; it defines the user's intended direction, target scene, prohibited directions, must-have features, and decision priorities.
- Previous drafts: preserve them and create a new version when the change is material.

Before writing, report the resolved product root, development directory, manual direction file, and source files selected. Never put a product conclusion in a directory belonging to another product code.

## Core workflow

1. **Confirm the handoff.** Verify ASIN/product code, report path, variation, marketplace, source dates, decision status, and missing evidence.
2. **Freeze the direction.** Separate the user's manual direction from analysis conclusions. Record prohibited scope and non-goals.
3. **Define the job.** State target user, use scene, trigger, desired outcome, and what the product must not attempt to solve.
4. **Build the evidence ledger.** For every proposed change, record source fact, customer impact, development hypothesis, cost/complexity risk, and validation method.
5. **Write Product Definition V1.** Specify the product form, core functions, measurable dimensions/performance, materials, appearance, packaging, cost target, price assumption, and P0/P1/P2 priorities. Use `数据缺失` or `待确认` instead of guessing.
6. **Plan prototypes.** Use a small number of versions. Each version must test a named hypothesis, such as packaging protection, weight reduction, stability, edge finish, or usability.
7. **Create the test plan.** Every test needs a requirement ID, method, sample size, owner, pass/fail threshold, result, and retest rule. If a threshold is unknown, write `待供应链/实验室确认`.
8. **Review samples.** Compare observed results to the requirement table. Mark `通过`, `不通过`, or `未测试`; link every failure to a corrective action and retest condition.
9. **Check feasibility.** Reconcile landed-cost components, tooling, MOQ, lead time, capacity, quality stability, packaging, and return/defect risk. Separate supplier quotes from assumptions.
10. **Make a gate decision.** Choose `继续打样`, `改版后再测`, `暂缓`, or `停止`. A conditional market decision is not approval for mass production.
11. **Prepare the handoff.** Deliver the controlled specification, BOM or component list, critical-to-quality points, inspection checklist, packaging requirements, open decisions, and change log.

## Required development outputs

For a substantial development task, write into the resolved development directory:

1. `01-开发结论与方向-vN-YYYYMMDD.html`
2. `02-产品需求规格书-vN-YYYYMMDD.md` (use `.xlsx` only when the user needs a spreadsheet)
3. `03-样品与测试计划-vN-YYYYMMDD.md` (use `.xlsx` when test rows need spreadsheet operation)
4. `04-质量验收标准-vN-YYYYMMDD.md`
5. `05-开发变更记录.md`
6. `product-handoff-vN-YYYYMMDD.json`
7. `sources-used.txt`

Do not create empty placeholder files. If the user asks only for a development direction, create one consolidated result and do not fabricate a complete specification package.

Every output must contain:

- product code/ASIN, variation, marketplace, version, and date;
- `资料事实 / 用户决定 / 开发假设 / 待验证` labels;
- unresolved questions and the gate that depends on them;
- source filenames and paths sufficient for another Skill or employee to trace the decision.

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
3. Product Definition V1；
4. P0/P1/P2 需求与取舍；
5. 结构、材料、尺寸、包装或交互建议；
6. 样品版本与测试计划；
7. 质量验收标准；
8. 成本、工艺、交期、合规与 IP 待确认项；
9. 开发变更记录与下一步。

When the user asks for a production-ready handoff, include copyable tables for requirements, BOM/components, tests, inspection, packaging, and open decisions.
