# HZP Amazon 6-1｜新品推广方案

## 30 秒运行

```text
使用 6-1 Skill
产品：P001
Products Root：E:\【产品总目录】
```

6-1 是新品推广架构师，用于完整链路新品、已上线产品或已有广告历史的产品，设计首阶段流量、Search Intent 投资决策、广告测试、预算、价格/促销协同和继续/停止规则。V2 固定遵循“广告结构服从购买意图结构”，先建立 Launch Search Intent Map，再按 Known Demand 与 Unknown Demand 双引擎决定 Campaign、Bid、Placement、Budget 和验证计划。它负责“开战前怎么布阵”，不负责运行后的广告诊断或旧广告修改；用户批准完整创建清单后，可按批准边界创建本批新广告。运行时自动选择 Pipeline Mode｜完整链路模式 或 Direct Launch Mode｜直接推广模式。

6-1 会先读取可获得的商业事实，再只询问无法可靠判断且会影响取舍的目标、时间压力、季节性、亏损容忍度、预算和库存目标。没有人工目标时会生成并标记 [系统默认目标]，默认采用 Standard Growth Launch｜标准增长型 Launch，并根据真实窗口、库存和经济边界修正。`$100/day` 只是缺乏充分预算证据时的 Fallback Planning Budget，不是所有新品固定预算；6-1 会先判断产品值得投入多少，再决定总投入、阶段预算和每日预算。

运行前需要：

- `[Product Root]/01_产品档案.md`
- `[Product Root]/04_产品推广思路.md`（没有时会标记待确认）
- Products Root 下的只读身份主表：`00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`（先解析唯一 ACTIVE，再用 SellerSpace 只读验证 Store、Marketplace、ASIN、SKU）
- 可用时提供当前产品最新有效的 5-4 页面审核报告；没有 5-4 时不会机械停止，而是执行最低必要推广前检查
- 可用时提供 `[Product Root]/05_分析源数据/03_关键词数据/`、`[Product Root]/05_分析源数据/06_广告数据下载/` 和 `07_产品资料/` 中的真实推广资料

SellerSpace MCP 可用时，6-1 会先用 `discover_capabilities`、`discover_fields` 确认真实字段，再以只读方式读取店铺、广告、商品、Listing、库存、订单、历史趋势和平台推荐。SellerSpace 不可用时，仍可使用本地广告原始文件、H10/Cerebro、Niche/Search Term 和人工目标启动新品冷启动方案。

身份解析遵循 Amazon 行业共享规则 `Amazon产品身份解析规则.md`：Product Code 不能直接当作店铺或 ASIN，映射缺失、重复 ACTIVE 或身份冲突时不猜测；MCP 不可用时标记 `【SellerSpace实时身份验证未完成】` 并受限降级。

有真实证据显示页面不满足推广条件时，6-1 会返回 5-4；缺少 5-4 本身不会触发返回。Direct Launch Mode 会检查身份、Listing/可售状态、页面最低承接、库存和经济边界，缺少非关键数据时仍可形成证据有限的小规模验证方案，但不会编造预算、CPC、CVR、ACoS、销量或订单。

正式定案前，6-1 先输出《6-1 新品广告初始化预案》，展示 Launch 目标、窗口、阶段路线、Campaign/Keyword/Product Target、Bid/Budget/Placement 和风险，提供 A 批准、B 局部修改、C 重新制定、D 暂缓启动。批准预案本身不等于写入授权。只有完整执行清单展示后，用户针对该清单回复“批准/A/批准创建/按这个执行”，才授权本批新广告创建；旧广告仍由用户人工处理。

## 输出

正式报告写入：

`[Product Root]/06_SKILL分析报告/6-1_[产品编号]_新品推广方案_Vx_YYYYMMDD_HHMMSS.html`

报告包括推广核心战略、当前新品推广目标、输入数据完整度、SellerSpace 数据摘要、H10/Cerebro 关键词摘要、新品关键词母池、Semantic/Purchase Intent Clusters、关键词来源交叉验证、关键词启动池、Held Keywords、动态 Campaign 架构、Launch Investment Decision（总 Launch 投入、Initial/Maximum Daily Budget、Phase Budget、Budget Release Gate、资金效率判断）、预算/Bid逻辑、经济边界、价格—推广关系、7天或动态首轮验证计划、继续/停止规则、禁止动作、关键待验证项和 6-2 交接包。实际运行、人工审批、执行记录和 1/3/7 天复盘写入 `06_SKILL分析报告/广告表现汇报优化日志/`；日志不进入正式报告索引。正式报告成功后自动调用 0-2 更新索引；6-1 不自行维护 `index.html`。

新品没有广告历史时，不会编造 CPC、CVR、ACoS、订单或利润，而是用自有产品事实、对标 ASIN、H10/Cerebro、Niche/Search Term、SellerSpace 推荐、价格/Coupon、库存和人工目标形成小规模可验证的 Cold Start 方案。SellerSpace 商品、库存、广告、订单和 Listing 查询只能使用映射表确认的 Own ASIN；Benchmark ASIN 仅用于市场和竞品证据。真实 CPC 只能来自实际运行数据。批准前 6-1 只读，不创建 Campaign、不修改 Bid/Budget、不添加 Keyword/Negative、不修改 Placement 或 Listing；批准后仅按完整批准清单创建本批新广告，并执行 Read-Back Verification。旧广告仍不修改。

Launch 阶段使用“时间负责节奏，证据负责晋级”：验证 → 聚焦 → 放量 → 稳态/扩量，可提前晋级或延长。点击和订单区间仅作参考，1 click + 1 order 只能是首单验证；可靠 CVR 存在时才计算 Expected Orders。

详细字段和边界见同目录的 SKILL.md、references/v2-launch-decision-model.md、references/launch-framework.md、references/evidence-gated-keyword-expansion.md、references/creation-blueprint.md、references/approved-creation.md、references/handoff-schema.md 和 templates/report-outline.md。

## 新品广告创建蓝图

正式创建前会先展示两层视图：LEVEL 1 Executive Approval View 让老板快速看到经营结论、Campaign总览、钱和关键词释放到哪里；LEVEL 2 Detailed Creation Blueprint 逐项列出 Campaign、Ad Group、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、每个 Keyword/Target、Bid、Budget、Match Type、Bidding Strategy、Placement、Auto 和 Negative。完整字段缺失时不会标记 Ready to Create。

## 批准后的广告创建

完整清单会先列出店铺、Own ASIN、Mapped_SKUs[]/Advertised_SKUs[]、Campaign、Ad Group、关键词/Target、Bid、Budget、策略和广告位。明确批准后，6-1 才通过 SellerSpace 执行 `prepare_change_plan → 比对 → apply_change_plan → Read-Back Verification`。授权只覆盖本次清单中的新广告；旧 Campaign 不会被暂停、删除或修改。


## 证据驱动扩词

6-1 会建立完整 Keyword Mother Pool 和语义/购买意图 Cluster，只释放首批高置信验证词；未释放词保留给 6-2 后续扩词。母词池不是广告创建清单，Benchmark 证据不会冒充自有成交事实。
### 广告组合身份

6-1 的新广告默认进入映射表 `广告组合` 指定的 Portfolio。Portfolio ID 只从已验证 Store + Marketplace 的 SellerSpace 只读结果获取；报告、审批清单、Prepared Plan 和 Read-Back 均展示 Portfolio Name/ID/状态。身份未验证或字段不一致时只读/停止写入，旧广告不自动迁移。

身份解析同时保留 Product_NewCode、正式 Product_Code、店铺前缀和 Var_Code；变体多行 SKU 按 `Product_Code + Var_Code + ASIN` 归并为 `Mapped_SKUs[]`，创建前依据实际 eligibility 形成 `Advertised_SKUs[]`，不得取第一行 SKU 或重复创建 Campaign。Campaign 使用共享命名辅助函数，Own/Benchmark/Product Target ASIN 严格分开。

Campaign 采用稳定格式：`[Product_Code].[Var_Code].[AdType]-[Role]-[Target/Match]-[Sequence]`（无独立变体时省略 Var_Code），Ad Group 采用 `[Product_Code].[Var_Code].[Role]-[Sequence]`。日期、Bid、Budget、Placement 等可变参数不进入名称；创建前会检查重名，历史 Campaign 不自动改名。

### ERP 关键词数据源

阶段 6 可通过共享 `scripts/erp_keyword_adapter.py` 读取当前产品档案中的 ERP 编号，再以参数化 `PickPwKView.ProId` 查询历史关键词。字段定义以 `00_公共资料/03_系统配置` 为准，语义不明的列不会被猜测；缺失编号、无匹配数据或 Provider 不可用时保留状态并继续其他证据来源。
阶段 6 共用精准词定义：`PickPwKView.Tags` 包含完整标签 `|1精准|` 且 `Keyword` 有效；`IsExact` 当前定义为“暂无用”，不得用于精准词判定。6-1 只消费共享适配器输出，不复制筛选逻辑。
### Provider Boundary

核心判断使用 HZP Canonical 业务语义；SellerSpace/优麦云等 Provider 的原始字段先由 Adapter 映射。能力缺失显示 `[CAPABILITY_NOT_AVAILABLE]`，语义不明不猜；未来接入其他 Provider 只新增真实适配器，不改本 Skill 核心流程。

## 6-0-1 关键词专业输出

如果当前产品已有 6-0-1/6-0-2 latest-valid 关键词资产，6-1 可读取 6-0-1 双轨精准词 CSV 以及 6-0-2 精准泛词结果，作为初始广告蓝图输入；6-1 仍负责整体 Launch、预算、阶段与经济边界，不复制关键词识别或聚类算法。
