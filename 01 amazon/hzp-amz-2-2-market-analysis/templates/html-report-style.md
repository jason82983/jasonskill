# HTML Report Style

Use a readable responsive layout suitable for investment and product-development meetings.

- Show HZP Amazon 2-2｜细分市场分析 in the header or report metadata.
- Put verdict, primary market, opportunity, and largest risk in the first viewport.
- Use restrained colors: neutral background, one accent color, and distinct but accessible colors for GO, CONDITIONAL GO, NO-GO, and evidence labels.
- Use cards for summary metrics, tables for Niche comparison, and callouts for [数据支持], [分析推断], [待验证], [证据不足].
- Render Market Relationship Map as a compact relationship table or Mermaid-style flow only when every edge has a source and date; render Candidate Niche Decision Table with visible classification and evidence-limit columns.
- Keep tables horizontally scrollable on small screens.
- Display source filename, date, and scope beside material data.
- Do not hide caveats in tooltips or collapse the only evidence supporting a verdict.
- Keep CSS self-contained so the HTML opens from a local file without a build step.
