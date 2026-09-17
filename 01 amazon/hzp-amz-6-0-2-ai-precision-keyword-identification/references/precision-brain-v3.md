# Precision Brain V3 contract

602 is a complete judgment skill. `run_current_602(product_root, product_code)` reads the current product text and the newest timestamped 6-0-1 observation CSV, then calls `PrecisionJudgmentEngine`; callers do not provide a precomputed judgment.

The engine creates one stable `JudgmentItemId` per canonical keyword. Phase A receives only product and keyword semantics and returns the structured semantic judgment. Phase B is a late evidence reveal: it receives benchmark coverage/rank and returns only `BenchmarkRealityAssessment` (`SUPPORTS`, `WEAKLY_SUPPORTS`, `NEUTRAL`, `CONTRADICTS`, `INSUFFICIENT`). Phase B cannot replace the Phase A semantic level.

The only `FinalPrecision` values are `高度精准`, `精准`, `弱精准`, and `不精准`. `JudgmentStatus` is separate (`SUCCESS`, `REVIEW_REQUIRED`, `FAILED`). Legacy `PRECISION`, `NOT_PRECISION`, and `REVIEW_REQUIRED` strings are never accepted as `FinalPrecision` values. A failed model item is retained by its stable ID for review; it is never silently matched by array position or replaced by a numeric score.

Batch size is estimated from product-profile and prompt size, capped conservatively, and reduced after schema/coverage validation failure. A/B/C/D/E files are deterministic projections of the validated judgment map; no second AI call is allowed during filtering, deduplication, or benchmark splitting.

