# HZP Amazon 5-0-1｜产品线上信息获取

Product-code-only evidence acquisition. It resolves the current Product Root and official identity, discovers and reads every in-scope module on the current Amazon detail page, validates extraction coverage, and writes a versioned HTML report for 6-0-2. Layer 0 reports retrieval quality; Layer 1 preserves raw Amazon evidence; Layer 2 is labelled AI interpretation. It performs no advertising, listing, ERP or price changes.

Every run emits a Section Coverage Matrix with explicit `RETRIEVED`, `PARTIAL`, `NOT_PRESENT`, `FAILED`, `BLOCKED`, `NOT_APPLICABLE`, or `NOT_CHECKED` status. Completion is governed by the gate: `FULL_SUCCESS` (no partial/failure and no unchecked), `PARTIAL_SUCCESS` (all attempted but limitations), `INCOMPLETE_EXECUTION` (any unchecked), or `FAILED` (identity/core page unavailable).

Run the provider-injected implementation with `scripts/online_information_retrieval.py`; use `tests/test_retrieval_contract.py` for deterministic contract checks.
