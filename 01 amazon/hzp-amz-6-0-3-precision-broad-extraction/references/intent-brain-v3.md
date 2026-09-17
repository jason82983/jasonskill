# Intent Brain V3

603 uses a two-phase semantic process. Phase A turns each unique 602 C record into a compact semantic unit: keyword intent summary, purchase mission, expressed dimensions, and unresolved dimensions marked `NOT_SPECIFIED`. Phase B reconciles candidate groups globally, merges equivalent purchase missions, keeps independently operable recipient/occasion/product/compatibility tasks separate, assigns one Primary Intent, and builds a semantic parent/child hierarchy.

Batching is an implementation detail. Candidate groups from each batch must be reconciled globally before output; no batch-local intent tree may be appended directly. Stable identity is derived from the canonical intent identity and should reuse a product-scoped registry when one exists. Display-name changes do not create a new identity.

The mapping CSV is the source of truth. Summary rows are deterministic aggregates of mapping rows. AI may provide semantic labels, assignment reasons, and challenge status, but it must not calculate volumes, competitor averages, ratios, coverage, or reconciliation results.
