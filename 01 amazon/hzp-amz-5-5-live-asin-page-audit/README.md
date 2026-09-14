# HZP Amazon 5-5｜线上ASIN页面审计与优化

## 30 秒运行

    使用 5-5 Skill
    产品：P001
    Products Root：E:\【产品总目录】

指定变体时可使用：

    5-5，B2，M

这里的 `M` 是中央映射表“产品对应变体”中的 `Var_Code`，不是 Var_Name。未指定变体时使用 `5-5，B2`，直接读取“产品店铺映射”中的默认 ASIN。

5-5 用于审计已经上线的真实 Amazon ASIN 页面：确认消费者当前看到的内容，核对 5-1～5-4 是否被执行，找出影响点击、转化、信任或真实性的实际问题，并把问题路由给正确 Skill。

它不是 Listing 写作、图片制作、广告优化或产品开发 Skill，也不会直接修改页面、价格、Coupon 或广告。

## 运行前

- Product Root 中应有 01_产品档案.md。
- 5-1、5-2、5-3、5-4 正式报告放在 06_SKILL分析报告/；Skill 会按最新有效版本读取。
- 真实页面截图、Listing 导出、图片、视频等可放在 07_产品资料/。
- 需要真实店铺字段时，Skill 会读取公司映射表并进行身份核验。

## 会检查什么

Live Page Snapshot、页面完整性、策略到线上执行、文案—视觉一致性、主图和首屏、购买路径、Claim、Offer、Review/VOC、竞争现实和根因。每个问题给出证据、业务影响、P0/P1/P2/P3 优先级、责任 Skill 和验证方法。

如果页面已经足够好，结论可以是【建议保持当前页面】，不会为了制造任务而强行修改。

## 证据与限制

真实 Amazon 前台优先；SellerSpace/API 后台数据会标注【后台Listing数据】。图片只有实际查看后才能审计，无法查看时标记【图片内容未验证】。Own ASIN、Child ASIN、Parent ASIN、Benchmark ASIN 和 Product Target ASIN 始终分开。

## 变体短命令

- `5-5，B2，M`：按 `Product_Code + Var_Code` 精确找到 M 对应 ASIN，只审计该变体。
- `5-5，B2，S`：同理，只审计 S 对应 ASIN，不读取 M 页面。
- `5-5，B2`：从中央映射表“产品店铺映射”中读取 `Product_Code=B2` 的默认 ASIN；如果该 ASIN 为空，返回 `[默认ASIN缺失]`。不会默认使用 Excel 第一行或任意变体。
- 不存在的变体返回 `[未找到对应变体ASIN]`；一个变体对应多个冲突 ASIN 返回 `[变体ASIN映射冲突]`，两者都在访问页面前停止。

正式报告身份区应显示：Product Code、Var_Code、Var_Name、ASIN。

## 输出

正式报告写入：

[Product Root]/06_SKILL分析报告/

默认命名：

5-5_[产品编号]_线上ASIN页面审计与优化_Vx_YYYYMMDD_HHMMSS.html

报告成功后调用 0-2 更新索引，5-5 不自行生成或维护 index.html。符合条件时报告包含《6-1输入交接包》，否则只给页面问题与路由清单。

## 常见结果

- HEALTHY：页面健康，可保持不动。
- MINOR_OPTIMIZATION：有低风险、高价值的小改进。
- MAJOR_OPTIMIZATION：存在明显页面问题。
- STRATEGY_MISALIGNMENT：线上执行偏离原策略。
- LIVE_PAGE_ANOMALY：线上展示异常。
- INSUFFICIENT_EVIDENCE：证据不足，先补数据。

详细审计字段见 references/audit-framework.md，交接字段见 references/handoff-schema.md，报告章节见 templates/report-outline.md。

## 报告怎么看

5-5 报告采用两层阅读：

- **LEVEL 1｜老板版**：首页先给一句话结论、【不用改/小改/建议重点优化/建议重做部分页面/暂时无法判断】、页面体检结果、现在最值得做的 3 件事、这次不建议动的地方，以及接下来交给哪个 Skill。
- **LEVEL 2｜专业版**：保留 Live Page Snapshot、输入版本追溯、策略矩阵、证据、根因和机器状态码，供团队复核。

首页使用中文经营语言；机器状态码只放详细证据区。图片按“这张图要完成什么任务 → 现在怎么样 → 建议 → 交给谁”逐张点评，Offer 无法确认时直接说明暂不下结论。
