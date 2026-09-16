# 6-2 Fact Windows and Static Tables

This legacy reference now routes to [advertising-facts-contract.md](advertising-facts-contract.md). It does not authorize business comparisons or judgments.

- Use only real dates in the same Run Package CSVs. Yesterday/3D/7D/14D/30D/Since Launch views are client-side filters over embedded rows.
- Source-window rows remain unsplit and display their source interval and grain. Missing dates are not zero.
- Use neutral tables/KPI cards and fact labels only. No red/green performance semantics, trend diagnosis, or recommendations.
- HTML is static and self-contained; no runtime fetch or API call.
