---
name: hzp-amz-6-1-new-product-advertising-battle-plan
description: Plan which precise Amazon search intents and keywords a new product should advertise first, how each should be controlled, and what initial campaign structure to review before 6-2 execution. Never writes Amazon ads.
metadata:
  short-description: 新品广告作战规划
---

# HZP Amazon 6-1 | 新品广告作战规划

## Identity and boundary

Formal identity: `6-1 | 新品广告作战规划 | New Product Advertising Battle Plan | hzp-amz-6-1-new-product-advertising-battle-plan`.

6-1 is the pre-execution PLAN and the sole source of the complete Campaign Creation Blueprint. It decides which precise Intent markets to pursue, their sequence, the lifecycle of every 603 keyword record, campaign-control architecture, and every Campaign/Ad Group/Target creation parameter for 6-2.

- Do not create or change Amazon Campaigns, bids, budgets, placements, or status.
- Do not rejudge 6-0-2 precision or redo 6-0-3 precision-broad mapping, Primary Intent, or Parent/Child Tree.
- Do not leave bid, budget, placement, strategy, ASIN/SKU, Portfolio or status parameters for 6-2 to infer. Take them from the approved decision inputs and emit them in the Creation Blueprint; if evidence is missing, write `DATA_NOT_AVAILABLE` and `Parameter Status=EXECUTION_NOT_READY` so 6-2 stops instead of guessing.
- Do not modify 6-2, 6-5, 6-3, or 6-4 as part of a 6-1 run.
- Intent, role, match type, and campaign are different concepts. Never make one campaign per keyword by default.

## Inputs and run sequence

1. Resolve the confirmed Product Code and Product Root under `E:\【所有产品目录专用】\` unless the user supplies another root. Read the current `01_产品档案.md` and `04_产品推广思路.md` for product core demand and launch constraints; do not infer product identity from ASINs or filenames.
2. Run `scripts/battle_plan.py inspect-inputs --product-root <ProductRoot> --product-code <ProductCode>`. It resolves the governed 603 Registry/Manifest and reads the exact summary and mapping identities from the current complete `data/` Batch; both files must share the Registry/Manifest `RUN_TIMESTAMP`. Filesystem mtime and greatest filename selection are not version signals.
3. Read the paired 6-0-3 Intent Summary and Keyword Mapping completely. Accept the current single-benchmark mapping schema or the multi-benchmark schema documented in [run-package-contract.md](references/run-package-contract.md). Preserve source metrics and record Ids; do not add benchmark rows together or recalculate parent/child totals.
4. If a complete latest valid 6-0-6 run exists, read its Intent occupation detail and multi-benchmark consensus in the `inspect-inputs` result as reality evidence. If it does not exist, record `606_EVIDENCE_NOT_AVAILABLE` and continue without fabricating it.
5. Make the business decisions described in [decision-contract.md](references/decision-contract.md). Consider product core need, parent/child Intent relationships, market scale, competition environment, concrete breakthrough keywords, and benchmark evidence together. Do not use fixed weights or mechanically promote the largest search volume, highest opportunity ratio, lowest competitor count, or best benchmark rank.
6. Assign a lifecycle decision to every 603 Keyword Mapping Id. Build Output A from the 603 Intent Summary; build Output C from every 603 mapping record plus the approved decisions; derive Output B only by filtering eligible PHASE_1 execution records from C. Do not reselect keywords while creating B.
7. Before writing, include the exact inspected 603 Run ID/timestamp and 606 Run ID (or `606_EVIDENCE_NOT_AVAILABLE`) in the run command. The writer re-resolves inputs and stops if either source changed after planning. A run is valid only when all three UTF-8-BOM CSVs and the same-run static HTML pass schema, coverage, identity, derivation, and timestamp checks. Keep failed run records marked `INVALID`; never overwrite an earlier run.
8. After the package is `VALID`, use `hzp-amz-0-2-report-index` to refresh the current Product Root's HTML report index. The index is outside the timestamped 6-1 package files and does not change the Run Status.

## Required output

Write under the current Product Root:

`06_SKILL分析报告/6-1_新品广告作战规划/`

The four formal CSV deliverables are one validated batch under `data/`; only the current complete `LATEST VALID` batch remains there. The RunPackage/Manifest is under `_system/manifests/`, sidecars under `_system/metadata/`, stable Registry under `_system/registry/`, and old valid batches under `历史数据/<RUN_TIMESTAMP>/`. The HTML is published as the single current human report in the Skill root; older HTML goes to `历史HTML/`. All five formal deliverables use one `RUN_TIMESTAMP`. See [run-package-contract.md](references/run-package-contract.md) for schemas, the stable registry, and approval rules.

## Report and handoff

The HTML is a self-contained decision dashboard rendered from this run's A/C/B and Creation Blueprint CSVs. It must explain first-attack selection, core/expansion/hold markets, parent-child expansion, complete keyword lifecycle, independent/shared/no-investment controls, PHASE_1 execution, held-back keywords, risk limits, the complete creation parameters, and the 6-2 handoff.

Independent campaigns are Intent-aware and include the stable Intent Code. Shared campaigns are role pools and omit Intent Code. The campaign preview uses `{ProductCode}.{CampaignTag}.{AdType}-{Role}-{TargetType}-[IntentCode]-{Seq}`; an independent CampaignTag is a runtime input and must not be guessed. When missing, display the supplied placeholder `{ProductCode}.{CampaignTag}.SP-COR-EXA-SBG-01`.

State in the completion report which 603 run was consumed, whether 606 evidence was available, the output package path/status, and any unresolved compatibility limit. The 6-2 handoff points to this one complete package; downstream readers must not combine files from different runs.

## Human Report Publishing

本 Skill 生成正式 HTML 报告时，遵循统一的人类可见报告规则：Skill 报告根目录只保留一个当前最新 HTML；旧 HTML（以及同名 `.meta.json`）全部移动到同级 `历史HTML/`，不删除、不覆盖。一次性 Skill 的正式机器 CSV/JSON 只进入当前 Skill 报告目录的 `data/`，且只保留完整 `LATEST VALID` Batch；RunPackage/Manifest、metadata sidecar、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。HTML 仅按人类报告规则发布到根目录或 `历史HTML/`。完成写入、回读和校验后才发布当前报告；失败或不完整 Run 不得发布。公共实现与索引规则见 [`skills/references/human-report-publishing.md`](../references/human-report-publishing.md)。

## 全局报告文件治理（适用本 Skill）

本 Skill 遵循公共 `scripts/hzp_amz_report_contract.py`、[human-report-publishing.md](../references/human-report-publishing.md) 与 [report-governance.md](../references/report-governance.md)：正式机器业务数据只进入当前 Skill 报告目录的 `data/`，`data/` 只保留完整 `LATEST VALID` Batch；旧 VALID Batch 整包进入 `历史数据/<RUN_TIMESTAMP>/`。RunPackage/Manifest、metadata、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。新 Batch 必须先 Staging、验证完整性后再原子发布；失败不得替换旧 data。根目录只保留最新人类 HTML（如有）及正式子目录，机器数据不得写根目录。下游通过正式 Registry/Resolver 读取 `data/`，不得按 HTML 或根目录 mtime 选数。已有成熟时间戳 Run Package 的持续 Skill 可保留其内部运行包，但仍遵守根目录清洁和系统资产分层。
