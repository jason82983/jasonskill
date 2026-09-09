# ASIN-Niche Discovery and Role Validation

## Scope

Use this reference when 2-2 restores a product's market universe from the shared `所有细分市场` data pool. The pool may contain several ASIN exports and is not limited to the Product Root's Benchmark.

## File discovery

Scan recursively under:

```text
[Product Root]/05_分析源数据/02_细分市场数据/所有细分市场/
```

Treat a file as a candidate only after checking all available signals:

1. path contains `所有细分市场`;
2. filename contains `NichesProductAppears` or an equivalent export label;
3. headers/content contain Niche or product-appearance fields;
4. rows contain valid ASINs and Niche identifiers;
5. marketplace and data date can be matched when available.

The filename can locate an export or suggest its source ASIN. It cannot establish Niche rank, Leader, Primary Market, or importance. Record unreadable, duplicate, or mismatched files in Evidence & Limitations.

## Relationship-map construction

Normalize ASINs to uppercase and preserve the source spelling in the citation. For every valid row, emit:

```text
ASIN | Niche | source file | source field/row | data date | current research role
```

Then join the rows to `01_产品档案.md` and the known ASIN packages. Assign relation labels only after the join:

- `Benchmark` — the confirmed development anchor;
- `Competitor` — a comparable research ASIN;
- `Leader` — only when current Niche evidence explicitly proves a head role;
- `Representative` — a market example used for context;
- `Unknown` — identity or role is unresolved.

Do not copy the ASIN's source data into multiple role folders. A single ASIN may have multiple dated role observations.

## Candidate and overlap logic

1. Candidate Niches = all Niche values connected to the Benchmark ASIN.
2. Shared Niche = candidate Niche also connected to one or more competitor/leader/representative ASINs.
3. Benchmark-only = connected to Benchmark but no other valid research ASIN in the pool.
4. Competitor-only = connected to other ASINs but not Benchmark; use only as adjacent context.
5. Unclear = source or identity cannot be matched.

Shared appearance is a validation lead, not a market verdict. Confirm it with search intent, actual product function/form, use scene, click/purchase evidence, consumer feedback, and Niche-level quality.

## Current Leader validation

Use the candidate Niche's current head-product, product-tab, Top Products, or equivalent Amazon export. Accept a Leader only when the source explicitly identifies `榜1`, `Top Product`, `Top Clicked Product`, or an equivalent role with a date. Store:

```text
Niche | Leader ASIN | Role | Data Date | Evidence Source | Confidence
```

Membership-only evidence is insufficient. If the role cannot be proven after checking available head data, write `Leader = [待验证]` and list the missing source. On every later run, re-evaluate the role using the newest dated data; never inherit a historical “榜1” label as permanent.

## Conflict handling

When an archive role conflicts with current Amazon data, preserve both observations and report:

```text
上游/历史结论：...
当前新证据：...
为什么修改：...
当前结论：...
```

Prefer current Amazon market data for the 2-2 decision, without modifying original exports or silently changing the product archive.
