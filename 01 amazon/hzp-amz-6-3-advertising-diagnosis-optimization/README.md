# HZP Amazon 6-3｜广告诊断优化（DECIDE）

Formal Skill ID remains `hzp-amz-6-3-advertising-diagnosis-optimization`. The repository has not declared a separate English display name. The 6-3 role is **DECIDE**, between `6-2 DATA` and human approval / `6-4 APPLY`.

6-3 consumes one complete same-run 6-2 fact package, the approved 6-0-5 purpose plan, same-run 6-0-3 Intent context, and optional 6-0-6 Benchmark reality. It evaluates Intent, Campaign, Target, and Search Term objects and writes a same-run four-CSV plus HTML Decision Package under:

Each run requires ProductCode + opaque CampaignTag and inherits the matching exact prefix and source 6-2 Run ID. It never re-scans or widens the Campaign set; contaminated rows are excluded and recorded as a partial run.

`[Product Root]/06_SKILL分析报告/6-3_广告诊断优化/YYYYMMDD_HHMMSS/`

The helper `scripts/ad_decision_package.py` resolves existing upstream contracts, builds real dated windows, checks full coverage/reasons/next observations/current and proposed values/layer consistency, renders HTML from the CSV rows, and preserves Decision History. 6-3 never queries current Amazon/SellerSpace performance or performs any ad write. Human-approved daily operating decisions pass to 6-4, which rechecks live state, exact preview approval, and read-back. 6-1 is reserved for initial 6-0-5 BUILD.

References: [SKILL.md](SKILL.md), [decision-data-contract.md](references/decision-data-contract.md), [decision-readiness-kernel.md](references/decision-readiness-kernel.md), [handoff-schema.md](references/handoff-schema.md), and [report-outline.md](templates/report-outline.md).

Synthetic tests: `pytest hzp-amz-6-3-advertising-diagnosis-optimization/tests`.
