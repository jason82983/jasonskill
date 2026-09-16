---
name: hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis
description: 将多个Benchmark自然排名映射到当前产品603 Search Intent Tree，计算各Benchmark在各Intent中的自然搜索占领深度、需求覆盖与多对标共识，生成CSV和HTML Reality Evidence；不表示销量份额、不决定广告策略、不写入广告或ERP。
metadata:
  short-description: 对标意图市场占领分析
---

# HZP Amazon 6-0-6｜对标意图市场占领分析

正式身份：`6-0-6 | Benchmark Intent Market Occupancy Analysis | hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis`。

## 职责边界

606 回答每个 Benchmark 在当前产品已建立的 Search Intent 中自然排名覆盖多深、哪些 Intent 有多对标共同证据、哪些主要是单点成功。它衡量 **Organic Search Occupancy**，不代表真实销量、GMV、订单、点击或任何 Sales Market Share。606 只提供 Reality Evidence，不重判精准度、不建/改 Intent Tree、不决定 6-0-5 首攻/核心/扩展、不执行广告或 ERP 写入。

Keyword Market Fact（Id/词/中文/市场容量/竞争产品数/供需比）按唯一 KwId 只保存一份；Benchmark Observation（KwId/Benchmark Code/ASIN/自然排名）可有 N 份。Benchmark 数量不得放大任一市场事实或 603 Intent 需求分母。

## 正式输入与版本选择

调用 `6-0-6, Product_Code` 后按 0-1 产品目录规则定位唯一 Product Root，并仅从下列正式目录选择当前产品的有效资产：

1. 602 Benchmark D assets：LATEST VALID 602 Batch 中每个 `6-0-2_{所属产品编号}_高度精准词_{RUN_TIMESTAMP}.csv`，Report Identity `BENCHMARK_HIGH_PRECISION_KEYWORDS`，固定十一列 `所属产品编号,对标ASIN,Id,词,中文,市场容量,竞争产品数,供需比,自然排名,精准度,精准原因`；只接受 `精准度=高度精准` 的唯一词资产。
2. 603 汇总：`06_SKILL分析报告/6-0-3_精准泛词提取/6-0-3_精准泛词汇总_*.csv`，Identity `PRECISION_BROAD_SUMMARY`，固定九列见 [数据契约](references/data-contract.md)。
3. 603 映射：同目录 `6-0-3_词对应的精准泛词_*.csv`，Identity `PRECISION_BROAD_MAPPING`，使用正式多对标十一列 Schema。

602 必须解析最新完整有效的 3+N Batch；Resolver 校验三张公共表、所有预期 D 文件及 metadata 后，按 RUN_TIMESTAMP 回退到最近完整 VALID Batch。606 从同一批次读取全部 D 文件；603 汇总与映射必须来自同一非空 RUN_ID 和 RUN_TIMESTAMP，且是最新有效配套资产。校验 Report Identity、Schema、状态、路径、时间戳、产品身份与记录数。不得按 mtime、文件夹顺序或不同运行拼接。不得回退到旧单对标 603 Schema。缺输入、跨产品或运行不一致、Schema 不符、空数据时 fail closed。

`Id` 是跨 ProId 稳定唯一的 KwId；按它将 602 D 表的高精准 Benchmark 观察与 603 Primary Keyword 映射精确 Join。Benchmark Code 与 ASIN 来自同一 602 manifest 的 Benchmark Identities metadata，并须与对应 D 文件及所属产品编号一致。无 ASIN/Benchmark Code、Benchmark 身份冲突、重复 KwId×Benchmark、603 KwId 在 602 D 资产找不到、市场事实冲突、非高度精准、缺少 Primary Intent 映射、树结构非法或搜索量事实不一致时不得 `FULL_SUCCESS`。不按关键词文本、产品名称或 Benchmark 名称模糊 Join。

## 计算规则

603 是 Intent 与需求 Ground Truth，602 各 Benchmark D 表是高度精准自然排名 Ground Truth。对每个 603 Intent，分析其自身 Primary Records 和全部 Descendant Primary Records；每个 Keyword 在每个 Benchmark×Intent Subtree 只贡献一次。父级包含子级，父子统计允许重叠，禁止跨层相加。分母直接取 603 `汇总搜索量`，并校验其等于该 Subtree 唯一 Keyword Market Capacity 之和。

程序按 Rank 阈值累计计算 Top10/20/50/100 Keyword 数、Market Capacity 占领量和占 Intent 汇总搜索量比例；另算有效排名词数、算术平均排名和以 Market Capacity 加权的自然排名。有效排名仅为有限正数。NULL/空 Rank 进入 Data Quality Audit，不转为 999；非法、非正或不可解析 Rank 也进入 Audit，不参与排名指标。没有观察记录与显式 NULL Rank 分开显示。缺失/非法 Rank 会使运行状态为 `INCOMPLETE`，不掩盖缺证据。

程序负责所有 Join、去重、Subtree、COUNT/SUM/AVG/MEDIAN、加权排名、TopN、覆盖率、最佳 Benchmark、覆盖完整性、CSV、HTML 数据绑定、时间戳与血缘。必须校验 TopN 占领量/覆盖率单调不减且不超过 Intent 分母。任何 Benchmark 的覆盖率不能与其他 Benchmark 相加。

AI 只能基于程序计算好的指标和 Parent/Child 结构，逐个给单一 Benchmark×Intent 判定 `核心占领/强占领/中度占领/弱占领` 及有针对性的原因；逐个 Intent 判定多对标共识 `高共识/中共识/低共识/单点验证` 并说明证据。单 Benchmark 时输出 `单对标模式`（共识原因中说明仅一个对标，不宣称多对标共识）。不产生或使用 0–100 综合评分，不凭单指标机械映射等级。

## 输出

输出到固定目录 `06_SKILL分析报告/6-0-6_对标意图市场占领分析/`，不创建时间戳子目录。每次运行使用同一 RUN_TIMESTAMP 和 RUN_ID；三个正式文件与 sidecar 都直接写入该目录，文件名共享同一时间戳。保留历史文件，不覆盖已有运行；CSV 使用 UTF-8 with BOM，并为三个正式文件写 `.meta.json`：

- `6-0-6_对标意图市场占领明细_YYYYMMDD_HHMMSS.csv`：一行一个 Benchmark×Intent，固定 24 列。
- `6-0-6_意图多对标占领共识_YYYYMMDD_HHMMSS.csv`：一行一个 Intent，固定 17 列。
- `6-0-6_对标意图市场占领分析报告_YYYYMMDD_HHMMSS.html`：含至少 11 个模块，核心数据须存在于 DOM，响应式 Desktop-first、打印友好，无游戏化效果。

字段顺序、人工决策 JSON、状态与错误语义见 [数据契约](references/data-contract.md)。每份输出的 metadata sidecar 记录身份、批次与输入追溯；失败或不完整的输出不得成为 Latest Valid。报告必须明确“Organic Search Occupancy ≠ Sales Market Share”，并把薄弱证据称为 Benchmark 相对薄弱/验证不足，不称蓝海或容易打。

## 运行流程

先运行 `python scripts/benchmark_intent_occupancy.py inspect --product-root "<Product Root>" --product-code B2`。基于真实已解析输入生成逐 Benchmark×Intent 与逐 Intent 的 AI 判断 JSON（不让 AI 重算数学指标），然后运行 `build ... --decisions <json>`。程序写入前完成所有验证；关键错误不得生成 `FULL_SUCCESS`。成功生成 HTML 后按项目规则调用 0-2 更新索引。禁止直接使用真实写接口。

## 全局正式报告目录与命名规则

本 Skill 面向确定 Product Root 生成正式报告或结构化分析报告时，统一保存到 `06_SKILL分析报告/{Skill编号}_{Skill中文正式名称}/`，文件名使用 `{Skill编号}_{报告名称}_{YYYYMMDD_HHMMSS}.{ext}`；同一运行的配套正式资产共用时间戳。6-0-1、6-0-2、6-0-3、6-0-5、6-0-6 的报告资产直接放固定 Skill 目录，不建时间戳子目录；6-2、6-3、6-4 可按每次运行建立 `YYYYMMDD_HHMMSS/` 子目录，子目录中的文件仍须带 Skill 编号前缀和时间戳。读取最新报告或运行包时按文件名/包内时间及有效性校验，不按文件修改时间选择。HTML 必须使用同批 CSV 回读快照渲染。历史报告不自动迁移或删除。跨产品公共知识、提醒状态、决策登记簿和运行日志等持续业务数据按各自数据契约保存，不作为 Product Root 正式分析报告迁移。
