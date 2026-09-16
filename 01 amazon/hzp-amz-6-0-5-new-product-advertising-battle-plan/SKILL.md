---
name: hzp-amz-6-0-5-new-product-advertising-battle-plan
description: Plan which precise Amazon search intents and keywords a new product should advertise first, how each should be controlled, and what initial campaign structure to review before 6-1 execution. Never writes Amazon ads.
metadata:
  short-description: 新品广告作战规划
---

# HZP Amazon 6-0-5 | 新品广告作战规划

## Identity and boundary

Formal identity: `6-0-5 | 新品广告作战规划 | New Product Advertising Battle Plan | hzp-amz-6-0-5-new-product-advertising-battle-plan`.

605 is a pre-execution PLAN. It decides which precise Intent markets to pursue, their sequence, the lifecycle of every 603 keyword record, and a proposed campaign-control architecture for human review and handoff to 6-1.

- Do not create or change Amazon Campaigns, bids, budgets, placements, or status.
- Do not rejudge 6-0-2 precision or redo 6-0-3 precision-broad mapping, Primary Intent, or Parent/Child Tree.
- Do not calculate final bid, budget, or placement amounts. 6-1 decides those using current execution evidence and the existing economic contract.
- Do not modify 6-1, 6-2, 6-3, or 6-4 as part of a 605 run.
- Intent, role, match type, and campaign are different concepts. Never make one campaign per keyword by default.

## Inputs and run sequence

1. Resolve the confirmed Product Code and Product Root under `E:\【所有产品目录专用】\` unless the user supplies another root. Read the current `01_产品档案.md` and `04_产品推广思路.md` for product core demand and launch constraints; do not infer product identity from ASINs or filenames.
2. Run `scripts/battle_plan.py inspect-inputs --product-root <ProductRoot> --product-code <ProductCode>`. It selects the newest complete valid 6-0-3 manifest-backed Run Package as one unit and falls back to the previous complete valid run. Never select the summary and mapping independently or read legacy root-level pairs.
3. Read the paired 6-0-3 Intent Summary and Keyword Mapping completely. Accept the current single-benchmark mapping schema or the multi-benchmark schema documented in [run-package-contract.md](references/run-package-contract.md). Preserve source metrics and record Ids; do not add benchmark rows together or recalculate parent/child totals.
4. If a complete latest valid 6-0-6 run exists, read its Intent occupation detail and multi-benchmark consensus in the `inspect-inputs` result as reality evidence. If it does not exist, record `606_EVIDENCE_NOT_AVAILABLE` and continue without fabricating it.
5. Make the business decisions described in [decision-contract.md](references/decision-contract.md). Consider product core need, parent/child Intent relationships, market scale, competition environment, concrete breakthrough keywords, and benchmark evidence together. Do not use fixed weights or mechanically promote the largest search volume, highest opportunity ratio, lowest competitor count, or best benchmark rank.
6. Assign a lifecycle decision to every 603 Keyword Mapping Id. Build Output A from the 603 Intent Summary; build Output C from every 603 mapping record plus the approved decisions; derive Output B only by filtering eligible PHASE_1 execution records from C. Do not reselect keywords while creating B.
7. Before writing, include the exact inspected 603 Run ID/timestamp and 606 Run ID (or `606_EVIDENCE_NOT_AVAILABLE`) in the run command. The writer re-resolves inputs and stops if either source changed after planning. A run is valid only when all three UTF-8-BOM CSVs and the same-run static HTML pass schema, coverage, identity, derivation, and timestamp checks. Keep failed run records marked `INVALID`; never overwrite an earlier run.
8. After the package is `VALID`, use `hzp-amz-0-2-report-index` to refresh the current Product Root's HTML report index. The index is outside the timestamped 605 package files and does not change the Run Status.

## Required output

Write under the current Product Root:

`06_SKILL分析报告/6-0-5_新品广告作战规划/`

The package contains:

- `6-0-5_新品意图市场作战表_{timestamp}.csv` (A)
- `6-0-5_新品关键词阶段规划表_{timestamp}.csv` (C)
- `6-0-5_新品关键词作战明细_{timestamp}.csv` (B)
- `6-0-5_新品广告作战规划报告_{timestamp}.html`
- per-file `.meta.json` lineage sidecars

The four formal deliverables and their sidecars use one `RUN_TIMESTAMP`. Reports are written directly in the fixed 605 output root without a timestamp subfolder, with previous files preserved. See [run-package-contract.md](references/run-package-contract.md) for schemas, the stable registry, and approval rules.

## Report and handoff

The HTML is a self-contained decision dashboard rendered only from this run's A/C/B CSVs. It must explain first-attack selection, core/expansion/hold markets, parent-child expansion, complete keyword lifecycle, independent/shared/no-investment controls, PHASE_1 execution, held-back keywords, risk limits, proposed campaign architecture, and the 6-1 handoff.

Independent campaigns are Intent-aware and include the stable Intent Code. Shared campaigns are role pools and omit Intent Code. The campaign preview uses `{ProductCode}.{CampaignTag}.{AdType}-{Role}-{TargetType}-[IntentCode]-{Seq}`; an independent CampaignTag is a runtime input and must not be guessed. When missing, display the supplied placeholder `{ProductCode}.{CampaignTag}.SP-COR-EXA-SBG-01`.

State in the completion report which 603 run was consumed, whether 606 evidence was available, the output package path/status, and any unresolved compatibility limit. The 6-1 handoff points to this one complete package; downstream readers must not combine files from different runs.

## 全局正式报告目录与命名规则

本 Skill 面向确定 Product Root 生成正式报告或结构化分析报告时，统一保存到 `06_SKILL分析报告/{Skill编号}_{Skill中文正式名称}/`，文件名使用 `{Skill编号}_{报告名称}_{YYYYMMDD_HHMMSS}.{ext}`；同一运行的配套正式资产共用时间戳。6-0-1、6-0-2、6-0-3、6-0-5、6-0-6 的报告资产直接放固定 Skill 目录，不建时间戳子目录；6-2、6-3、6-4 可按每次运行建立 `YYYYMMDD_HHMMSS/` 子目录，子目录中的文件仍须带 Skill 编号前缀和时间戳。读取最新报告或运行包时按文件名/包内时间及有效性校验，不按文件修改时间选择。若 HTML 由同批 CSV 生成，必须从文件名时间戳相同的 CSV 读取并生成不可变快照；禁止运行时另找“最新 CSV”。未由 CSV 构成输入的 HTML 报告遵循对应 Skill 的原有报告内容逻辑。此规则优先于本文档中旧的目录和文件名示例。历史报告不自动迁移或删除。跨产品公共知识、提醒状态、决策登记簿和运行日志等持续业务数据按各自数据契约保存，不作为 Product Root 正式分析报告迁移。
