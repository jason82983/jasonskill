---
name: hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis
description: 将多个Benchmark自然排名映射到当前产品603 Search Intent Tree，计算各Benchmark在各Intent中的自然搜索占领深度、需求覆盖与多对标共识，生成CSV和HTML Reality Evidence；不表示销量份额、不决定广告策略、不写入广告或ERP。
metadata:
  short-description: 对标意图市场占领分析
---

# HZP Amazon 6-0-6｜对标意图市场占领分析

正式身份：`6-0-6 | Benchmark Intent Market Occupancy Analysis | hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis`。

## 职责边界

606 回答每个 Benchmark 在当前产品已建立的 Search Intent 中自然排名覆盖多深、哪些 Intent 有多对标共同证据、哪些主要是单点成功。它衡量 **Organic Search Occupancy**，不代表真实销量、GMV、订单、点击或任何 Sales Market Share。606 只提供 Reality Evidence，不重判精准度、不建/改 Intent Tree、不决定 6-1 首攻/核心/扩展、不执行广告或 ERP 写入。

Keyword Market Fact（Id/词/中文/市场容量/竞争产品数/供需比）按唯一 KwId 只保存一份；Benchmark Observation（KwId/Benchmark Code/ASIN/自然排名）可有 N 份。Benchmark 数量不得放大任一市场事实或 603 Intent 需求分母。

## 正式输入与版本选择

调用 `6-0-6, Product_Code` 后按 0-1 产品目录规则定位唯一 Product Root，并仅从下列正式目录选择当前产品的有效资产：

1. 602 Benchmark D assets：通过 6-0-2 正式 Registry/Manifest 定位当前完整 `LATEST VALID` Batch，再从其 `data/` 读取每个 `6-0-2_{所属产品编号}_高度精准词_{YYYYMMDD_HHMMSS}.csv`。Registry/Manifest 必须证明 3+N 资产完整、同批、Schema/Coverage 有效；只接受 `精准度=高度精准` 的唯一词资产。
2. 603 汇总和映射：通过 6-0-3 正式 Registry/Manifest 定位当前完整 `LATEST VALID` Batch，从其 `data/` 读取 `6-0-3_精准泛词汇总_{YYYYMMDD_HHMMSS}.csv` 与 `6-0-3_词对应的精准泛词_{YYYYMMDD_HHMMSS}.csv`，两表必须来自同一 Manifest `RUN_TIMESTAMP`。

606 只按正式 Registry/Manifest 解析的完整 Batch 取数；不得按 mtime、文件夹顺序或最大文件名猜测版本，也不得拼接不同运行。缺输入、Batch 不完整、时间戳不一致、Schema 不符或空数据时 fail closed。

`Id` 是跨 ProId 稳定唯一的 KwId；按它将 602 D 表的高精准 Benchmark 观察与 603 Primary Keyword 映射精确 Join。Benchmark Code 与 ASIN 来自同一 602 manifest 的 Benchmark Identities metadata，并须与对应 D 文件及所属产品编号一致。无 ASIN/Benchmark Code、Benchmark 身份冲突、重复 KwId×Benchmark、603 KwId 在 602 D 资产找不到、市场事实冲突、非高度精准、缺少 Primary Intent 映射、树结构非法或搜索量事实不一致时不得 `FULL_SUCCESS`。不按关键词文本、产品名称或 Benchmark 名称模糊 Join。

## 计算规则

603 是 Intent 与需求 Ground Truth，602 各 Benchmark D 表是高度精准自然排名 Ground Truth。对每个 603 Intent，分析其自身 Primary Records 和全部 Descendant Primary Records；每个 Keyword 在每个 Benchmark×Intent Subtree 只贡献一次。父级包含子级，父子统计允许重叠，禁止跨层相加。分母直接取 603 `汇总搜索量`，并校验其等于该 Subtree 唯一 Keyword Market Capacity 之和。

程序按 Rank 阈值累计计算 Top10/20/50/100 Keyword 数、Market Capacity 占领量和占 Intent 汇总搜索量比例；另算有效排名词数、算术平均排名和以 Market Capacity 加权的自然排名。有效排名仅为有限正数。NULL/空 Rank 进入 Data Quality Audit，不转为 999；非法、非正或不可解析 Rank 也进入 Audit，不参与排名指标。没有观察记录与显式 NULL Rank 分开显示。缺失/非法 Rank 会使运行状态为 `INCOMPLETE`，不掩盖缺证据。

程序负责所有 Join、去重、Subtree、COUNT/SUM/AVG/MEDIAN、加权排名、TopN、覆盖率、最佳 Benchmark、覆盖完整性、CSV、HTML 数据绑定、时间戳与血缘。必须校验 TopN 占领量/覆盖率单调不减且不超过 Intent 分母。任何 Benchmark 的覆盖率不能与其他 Benchmark 相加。

AI 只能基于程序计算好的指标和 Parent/Child 结构，逐个给单一 Benchmark×Intent 判定 `核心占领/强占领/中度占领/弱占领` 及有针对性的原因；逐个 Intent 判定多对标共识 `高共识/中共识/低共识/单点验证` 并说明证据。单 Benchmark 时输出 `单对标模式`（共识原因中说明仅一个对标，不宣称多对标共识）。不产生或使用 0–100 综合评分，不凭单指标机械映射等级。

## 输出

输出到固定目录 `06_SKILL分析报告/6-0-6_对标意图市场占领分析/`。一次性运行先写 `_system/staging/<RUN_TIMESTAMP>_build/`；只有两张正式 CSV、HTML、Schema/Coverage/Join/Manifest 全部验证为 `VALID`，才将两张 CSV 原子发布到 `data/`（data 只保留当前完整 Batch），将旧 Batch 整包归档到 `历史数据/<RUN_TIMESTAMP>/`，将 RunPackage/Manifest、sidecar、Registry、日志分别归入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。根目录只保留一个当前 HTML，旧 HTML 进 `历史HTML/`；失败不得替换旧 data。每次运行使用同一 RUN_TIMESTAMP 和 RUN_ID，CSV 使用 UTF-8 with BOM：

- `6-0-6_对标意图市场占领明细_YYYYMMDD_HHMMSS.csv`：一行一个 Benchmark×Intent，固定 24 列。
- `6-0-6_意图多对标占领共识_YYYYMMDD_HHMMSS.csv`：一行一个 Intent，固定 17 列。
- `6-0-6_对标意图市场占领分析报告_YYYYMMDD_HHMMSS.html`：含至少 11 个模块，核心数据须存在于 DOM，响应式 Desktop-first、打印友好，无游戏化效果。

字段顺序、人工决策 JSON、状态与错误语义见 [数据契约](references/data-contract.md)。每份输出的 metadata sidecar 记录身份、批次与输入追溯；失败或不完整的输出不得成为 Latest Valid。报告必须明确“Organic Search Occupancy ≠ Sales Market Share”，并把薄弱证据称为 Benchmark 相对薄弱/验证不足，不称蓝海或容易打。

## 运行流程

先运行 `python scripts/benchmark_intent_occupancy.py inspect --product-root "<Product Root>" --product-code B2`。基于真实已解析输入生成逐 Benchmark×Intent 与逐 Intent 的 AI 判断 JSON（不让 AI 重算数学指标），然后运行 `build ... --decisions <json>`。程序写入前完成所有验证；关键错误不得生成 `FULL_SUCCESS`。成功生成 HTML 后按项目规则调用 0-2 更新索引。禁止直接使用真实写接口。

## Human Report Publishing

本 Skill 生成正式 HTML 报告时，遵循统一的人类可见报告规则：Skill 报告根目录只保留一个当前最新 HTML；旧 HTML（以及同名 `.meta.json`）全部移动到同级 `历史HTML/`，不删除、不覆盖。一次性 Skill 的正式机器 CSV/JSON 只进入当前 Skill 报告目录的 `data/`，且只保留完整 `LATEST VALID` Batch；RunPackage/Manifest、metadata sidecar、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。HTML 仅按人类报告规则发布到根目录或 `历史HTML/`。完成写入、回读和校验后才发布当前报告；失败或不完整 Run 不得发布。公共实现与索引规则见 [`skills/references/human-report-publishing.md`](../references/human-report-publishing.md)。

## 全局报告文件治理（适用本 Skill）

本 Skill 遵循公共 `scripts/hzp_amz_report_contract.py`、[human-report-publishing.md](../references/human-report-publishing.md) 与 [report-governance.md](../references/report-governance.md)：正式机器业务数据只进入当前 Skill 报告目录的 `data/`，`data/` 只保留完整 `LATEST VALID` Batch；旧 VALID Batch 整包进入 `历史数据/<RUN_TIMESTAMP>/`。RunPackage/Manifest、metadata、稳定 Registry、日志分别进入 `_system/manifests/`、`_system/metadata/`、`_system/registry/`、`_system/logs/`。新 Batch 必须先 Staging、验证完整性后再原子发布；失败不得替换旧 data。根目录只保留最新人类 HTML（如有）及正式子目录，机器数据不得写根目录。下游通过正式 Registry/Resolver 读取 `data/`，不得按 HTML 或根目录 mtime 选数。已有成熟时间戳 Run Package 的持续 Skill 可保留其内部运行包，但仍遵守根目录清洁和系统资产分层。
