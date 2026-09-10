# HTML visual style guide

Goal: executive clarity for desktop/browser/projector use. Clean, restrained, high-information, not flashy.

## General
- Self-contained HTML/CSS; no external fonts/assets required.
- Use a neutral system font stack.
- Content max-width around 1200–1320px.
- Generous outer whitespace, consistent section gaps.
- Use cards, light borders, subtle shadows only when needed.
- Use an 8px spacing rhythm, a small type scale (12/14/16/20/28px), and a restrained palette: pale neutral page background, dark ink, one blue information accent, green for positive, amber for validation, red for risk, and purple for inference. Every semantic color must also carry a text label.
- Prefer one subtle hero tint or accent rule over multiple gradients. Avoid saturated backgrounds, huge decorative icons, glassmorphism, and visual effects that compete with the decision.
- Keep the report visually calm but not flat: use a consistent card radius, one border weight, and shallow shadows only for primary panels.
- Add a compact print stylesheet (`@media print`) that removes sticky navigation, preserves contrast, and avoids splitting a review card or table row where practical. Respect `@media (prefers-reduced-motion: reduce)`.

## Information hierarchy
1. Page title / ASIN
2. subdued Skill source marker: `HZP Amazon 2-1｜产品市场分析`
3. one-sentence conclusion
4. decision badge
5. KPI row
6. four executive cards
7. detailed evidence sections
8. development direction + Product Definition V1 should receive strongest visual emphasis in the body

For reports longer than one screen, add a small local navigation row or table of contents below the source-validation strip. Use stable `id` anchors for the major sections and keep the current decision visible in the page header.

## Semantic tags
Use concise chips/badges for:
- `数据支持`
- `分析推断`
- `待供应链验证`
- `P0 必须解决`
- `P1 重要差异化`
- `P2 加分项`
- `数据缺失`

Do not use color as the only carrier of meaning; always keep the text label.

Place a small legend near the first evidence-heavy section so readers can decode fact, inference, supply-chain validation, and P0/P1/P2 tags without scrolling back to the top.

## Tables
- sticky/clear header if practical
- zebra rows optional, subtle only
- numeric columns aligned consistently
- no tiny fonts
- allow horizontal scroll on narrow screens
- H10 bid and bid-range columns must be clearly named
- use concise cell copy, aligned numeric values, and a visibly distinct header row; do not squeeze six or more long-text columns into a narrow viewport
- add a short caption or lead-in for any dense table that explains what the reader should notice

## Review cards
Each typical review card should visually separate:
- English original
- 中文翻译
- 开发启示

The English original must appear as a quotation and must be traceable to one review row.

Use a two-column card grid on desktop and one column on small screens. Give the English excerpt, Chinese translation, and `开发启示` three distinct visual blocks with comfortable line height. Keep cards short enough that a reader can compare themes without opening a separate page.

## Lightweight data visuals

Use a small visual when it makes a supported relationship easier to read than prose:

- Keepa: a milestone band or inline SVG sparkline for price and/or BSR, with dates and a note that BSR is a relative rank and lower is better.
- Reviews: a horizontal star-distribution bar or compact stacked bar using the source row counts.
- Cerebro: a demand-cluster matrix or ranked keyword bars only when the selected values are directly sourced.

Keep visuals self-contained with inline SVG or CSS; do not load chart libraries or remote assets. Show the underlying number next to or below every visual, use accessible text labels/`aria-label`, and never smooth, normalize, or extrapolate a trend beyond the source rows. If the sample is too sparse, use a milestone/table panel instead.

## Product-development matrix
Give this section a stronger border/title treatment than ordinary evidence sections.
Make P0 items easy to scan.

Use a slightly stronger accent border and a compact priority column. Keep the table readable by allowing horizontal scrolling and by moving long validation details into concise sentences rather than nested lists.

## Amazon page provenance and conflicts

- Put `Amazon 页面 已获取 / 部分获取 / 未获取` beside the core-file validation strip, with the request URL, final URL, fetch time, and displayed ASIN when available.
- Use small provenance chips or a source column for page snapshot, Keepa history, Cerebro export, and Reviews sample. Include dates/times in the text, not only in tooltips.
- Use a calm amber `冲突` or `待验证` treatment when current page facts differ from historical/file evidence; show both values and their sources. Do not use color alone.
- Use a neutral `数据缺失` treatment for blocked pages or fields that are not visible. Do not make a blocked page look like a product risk.
- Keep selected-child variation facts in a clearly labeled block so they cannot be mistaken for parent-ASIN totals.

## Sales and investment scenario panels

- Add two separate evidence panels after the page snapshot: `销量记录 / 销量预估` and `投资回报试算`.
- In the sales panel, show source format, date range, target-ASIN row count, quarantined foreign-ASIN row count, and 7/14/30-day file-range summaries. Put `文件范围内计算` beside derived totals and daily averages.
- In the investment panel, use a two-column layout or stacked cards for `手动输入/场景假设` and `自动计算/模型结果`. Keep currencies, percentages and units visible in each row.
- Give `试算模型` a neutral purple/amber provenance chip with a text label. Do not use the same green treatment as a realized business KPI.
- Use a small source caption for the image filename, read time, image section/field locator and any unreadable fields. A missing image field uses `数据缺失` and leaves the layout stable.
- Keep scenario numbers out of the decision hero unless they are explicitly labeled as assumptions or modeled ranges. The hero may summarize them as a validation dependency, not as confirmed profit or ROI.

## Product Definition V1
Use a single high-clarity product-brief panel, optionally with two-column layout on desktop.
Avoid burying it after long risk text.

Present it as a structured brief with clear labels, generous spacing, and a visually distinct “核心承诺 / P0 / P1 / 避免过度承诺” grouping. The panel should feel like a product brief, not a block of prose.

## Decision labels
Preferred top-level labels:
- GO
- CONDITIONAL GO
- NO-GO

A secondary WATCH note may be used inside risks/follow-up, but not as the primary executive badge.

The decision badge should be prominent but restrained, with the exact label in text and a one-sentence rationale beside it. Do not use a full-page red/green wash or an oversized decorative icon as the decision signal.

## Visual QA before delivery

After a successful report write and filename check, call `$hzp-amz-0-2-report-index` with the unchanged Product Code, Products Root, and Product Root captured at run start. Index generation and maintenance are exclusively owned by 0-2.

Open or render the finished HTML before handing it off. Check the first screen, one dense table, one review card, the product-development matrix, and Product Definition V1 at desktop width and a narrow width. Fix clipped text, unreadable contrast, broken overflow, awkward empty space, misaligned numbers, or a chart whose labels cannot be understood without the surrounding prose.
