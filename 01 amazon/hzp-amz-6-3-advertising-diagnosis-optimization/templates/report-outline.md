# 6-3 广告优化决策报告 Dashboard

Render this report from the four CSVs just validated and written for this same Run Package. Embed the source rows in the HTML DOM. Do not run a second decision prompt during rendering.

1. **决策摘要** — 评估总数、可决策、继续观察、紧急处理、保持、调整、升级/降级独立控制、暂停候选、收割候选、否定候选。
2. **本次使用数据** — current Product_Code; 6-2 Run ID and four fact assets; 605 plan Run ID and three purpose assets; 603 Run ID/assets and resolver status; optional 606 status; date range/grain and unresolved facts.
3. **Intent 决策** — each Intent maturity, result, purpose, reason, next observation and confirmation.
4. **Campaign 决策** — current/proposed Budget and Placement where relevant.
5. **Target 决策** — current/proposed Bid, match/target and control destination.
6. **Search Term 决策** — source Target attribution, evidence, candidate handling and explicit warning that collect/negative candidates have not been applied.
7. **继续观察清单** — why each object is not changing now, missing/immature evidence, and what event/data will trigger the next decision.
8. **紧急处理候选** — concrete urgent fact, containment decision and confirmation state.
9. **Evidence 与决策窗口** — show actual date windows named in reasons; connect decisions to 605 purpose, 603 market context and 606 Benchmark evidence only when available.
10. **待确认变更 / 6-4** — only proposed daily-action rows; current/proposed values and pending approval are visible. No action is described as applied.
11. **决策历史** — when available, previous decision chain for the same stable object ID; otherwise show `DECISION_HISTORY_UNAVAILABLE`.
12. **边界与数据局限** — explicitly state that 6-3 DECIDES only; no Amazon Ads write operation was run. Distinguish `Organic Search Occupancy` from sales share.

The HTML is an offline, UTF-8, print-friendly dashboard. Any summary count must be calculated from these CSV rows, and every detail shown must match a row in the same run. Missing values stay unavailable; do not make up charts or trends.
