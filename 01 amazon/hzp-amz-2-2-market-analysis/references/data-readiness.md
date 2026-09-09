# Data Readiness

## P0 — decision gate

- `05_分析源数据/02_细分市场数据/所有细分市场/` exists and contains at least one readable `NichesProductAppears` export for the benchmark or target ASIN.
- The export's headers/content and ASIN fields support the target identity; filename alone is insufficient.
- A relationship map can be built from ASIN to candidate Niche.
- At least one candidate Niche core Amazon dataset.
- Niche head products.
- Main search terms.
- Core demand and market metrics.
- Product or brand click concentration.
- Candidate primary Niche has a detailed data folder, or the report explicitly records the missing folder/data.
- Current Niche data can identify a Leader, or the report explicitly records `Leader = [待验证]` and what evidence is missing.

If P0 cannot establish the market boundary or the dataset cannot be matched, stop the verdict and report HOLD / STOP — [证据不足].

In Benchmark-Driven Mode, also confirm the benchmark ASIN, role, evidence period, and at least one usable benchmark evidence package. If no benchmark can be resolved, switch explicitly to Market-Driven Mode or stop if the user required a benchmark-based decision. A current leader is strongly recommended; if unavailable, state the comparison limitation rather than inventing one.

## P1 — confidence enhancers

Niche positive/negative/return insights, benchmark Keepa/Cerebro/Reviews/listing facts, and current leader ASIN data. Missing P1 does not always stop analysis, but the report must state which conclusions lose confidence.

## P2 — optional

Additional representative ASINs, precisely matched third-party data, social data, Google Trends, and external industry data. Never fabricate P2 to make the report appear complete.

## Readiness table

| Level | Present | Match quality | Effect |
|---|---|---|---|
| P0 | yes/no | confirmed/uncertain | verdict allowed or stopped |
| P1 | yes/no | confirmed/uncertain | confidence and scope limitation |
| P2 | yes/no | confirmed/uncertain | optional enrichment |

## Market discovery checks

| Check | Required result | Failure handling |
|---|---|---|
| A. `所有细分市场` folder | Scanned recursively | If absent, record `[证据不足]`; do not ask the user to restate all Niche memberships before checking the rest of the Product Root. |
| B. Benchmark `NichesProductAppears` | At least one valid ASIN-to-Niche relationship | If absent or unreadable, P0 is not met. |
| C. Other ASIN exports | Competitor/leader/representative data found when available | Enhancement only; absence is not an automatic stop. |
| D. Benchmark → candidate Niches | Relationship map is reproducible from source rows | If not reproducible, stop the market-boundary verdict. |
| E. Candidate Niche detail | Core data folder found for each Strong Candidate Niche | Keep the candidate but mark missing depth data and lower confidence. |
| F. Leader evidence | Current data explicitly identifies a head role | If only membership is proven, mark `Leader = [待验证]`; never infer a rank. |

## Path status output

Data Readiness must show the path actually checked, not only a generic missing-file message:

```text
检查路径：05_分析源数据/02_细分市场数据/所有细分市场/
Benchmark NichesProductAppears：FOUND / MISSING / UNREADABLE / CONFLICT
位置：<relative path or none>
说明：<matched ASIN, date, or missing requirement>

Primary Niche 搜索词：FOUND / MISSING / UNREADABLE / CONFLICT
位置：05_分析源数据/02_细分市场数据/<normalized Niche>/

Leader ASIN 数据：FOUND / MISSING / UNREADABLE / CONFLICT
位置：05_分析源数据/01_产品数据/<ASIN>/
```

Use the same four statuses for Product Identity, candidate Niche detail, ASIN evidence, supporting data, shared definitions, and report output locations. `MISSING` means the path or expected data is absent; `UNREADABLE` means it exists but cannot be parsed; `CONFLICT` means multiple matched versions or identities remain unresolved. Do not ask for a file location while a standard path is present and readable.

## Discovery quality rules

1. Discover by directory, filename pattern, headers/content, and ASIN fields together. Accept variants such as `*所有细分市场*` and `*NichesProductAppears*`; do not require one fixed filename.
2. Parse the data date from the file metadata/content when available. If unavailable, record the file date as a limitation rather than inventing a research date.
3. A filename may identify the source ASIN, but business roles (Primary Market, Leader, rank, importance) require row-level or Niche-level evidence.
4. If files conflict, preserve both dated observations, prefer current Amazon data for the decision, and show `[数据冲突]` or `[研究角色发生变化]` in the report.
5. For repeated data types, select the newest matched date by default and retain older files for trend or role-change checks. Never delete, rename, or overwrite an older source file.
