# HZP Amazon 6-2｜产品经营监控与诊断

## 30 秒运行

```text
使用 6-2 Skill
产品：P001
Products Root：E:\【产品总目录】
```

6-2 用真实运营数据检查一个 Amazon 产品的销量、流量、转化、广告、自然排名、价格、Review、库存和竞争变化，区分正常波动与需要处理的异常，并把问题交给最合适的 Skill。

运行前准备：

- `[Product Root]/01_产品档案.md`
- `[Product Root]/04_产品推广思路.md`
- Products Root 下的只读身份主表：`00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`；先按共享身份规则解析并验证 Store、Marketplace、ASIN、SKU
- 最新有效的 6-1 报告，并按需读取最新有效 6-3 广告报告及其《6-2输入交接包》
- `[Product Root]/05_分析源数据/` 中真实运营数据
- 可用时提供 `[Product Root]/07_产品资料/` 中的价格、页面、Review、库存和运营记录

Skill 会自动定位 Product Root、读取实际字段和数据窗口，生成完整运营监控报告，并判断增长飞轮、放量资格和 Coupon 依赖。没有可靠数据时会标记【证据不足】或【关键数据不足｜暂无法判断整体运营状态】，不会编造销量、Sessions、CVR、排名、库存或利润，也不会制作假健康分。阶段6运行日志、人工决策、执行记录和 1/3/7 天验证统一写入 `06_SKILL分析报告/广告表现汇报优化日志/`，不进入正式报告索引。

店铺身份遵循 Amazon 行业共享规则 `Amazon产品身份解析规则.md`；身份主表只读，冲突或 SellerSpace 实时验证未完成时必须保留证据状态。

正式报告写入：

`[Product Root]/06_SKILL分析报告/6-2_[产品编号]_产品经营监控与诊断_[周期标识]_Vx_YYYYMMDD_HHMMSS.html`

周期可以是 `3D`、`7D`、`14D`、`30D`、`WEEKLY` 或自定义日期范围。历史不带周期标识的报告仍兼容。

报告成功后自动调用 0-2 更新当前产品索引；6-2 不自行维护 `index.html`。库存正式补货预测由 7-1 负责，广告专项诊断由 6-3 负责。

## 周期调用

```text
6-2，B2                  # 最近7个完整自然日，默认环比
6-2，B2，7天             # 最近7天，截止昨天
6-2，B2，M，30天         # 指定变体与最近30天
6-2，B2，上周            # 上一个完整周一至周日
6-2，B2，2026-09-01到2026-09-07，环比+同比
```

未指定周期时不包含今天；明确要求包含今天时，报告会标记【包含未完整自然日】。默认环比是紧邻上一等长周期，也会显示实际对比日期。3/7/14 天同比按上个月对应日期，30 天同比按去年同期。

报告首页会用 KPI 卡片、3～6 张真实数据图表和直接结论说明当前经营状态；专业证据、完整表格和数据缺口放在 LEVEL 2。没有真实时间序列时不生成趋势图。
### Portfolio 监控

6-2 可以按已验证 Portfolio 聚合广告表现，但会把组合广告销售与当前产品总销售分开。Portfolio 身份异常只做只读告警和路由，不自动修正广告。

6-2 复用共享身份解析并按 Product_NewCode→Product_Code→Portfolio→Var_Code→Campaign 监控；同一 ASIN 多 SKU 只形成一个 ASIN 经营视图，聚合前检查来源粒度，SKU 异常保留为下钻；没有可靠 Child ASIN、Mapped_SKUs[]/Advertised_SKUs[] 关系时标记变体身份不完整，不把其他变体静默归入当前产品。

命名只作为解析提示，使用共享 `parse_campaign_name()`；真实归属以映射表、Shared Resolver 和 SellerSpace 广告对象为准。旧命名身份清楚时只记录历史命名，不当作经营异常。

### ERP 关键词数据源

关键词正式来源是 SQL Server `Amazon.dbo.PickPwKView`，不是本地文件。6-2 先读取 `01_产品档案.md` 中的 ERP 编号（`ERP编号`），再通过共享 `scripts/erp_keyword_adapter.py` 参数化查询 `WHERE ProId = ?`；禁止用 Product_Code、ASIN、相似产品或首条记录替代。字段定义只取 `00_公共资料/03_系统配置/erp-amazon-pickpwkview-schema.md`，语义不明的字段不用于重要判断。

6-2 不使用 `IsExact`（当前业务定义为“暂无用”）判断 ERP 精准词。关键词身份和经营异常只保留必要证据；精准词识别统一路由 6-0-2，精准泛词提取统一路由 `6-0-3｜精准泛词提取`（`hzp-amz-6-0-3-precision-broad-extraction`）。6-2 不复制聚类、精准泛词或 Rankability 算法。连接失败、无匹配行、ProId 缺失或冲突时保留错误状态并继续其他监控章节。
### Provider Boundary

核心判断使用 HZP Canonical 业务语义；SellerSpace/优麦云等 Provider 的原始字段先由 Adapter 映射。能力缺失显示 `[CAPABILITY_NOT_AVAILABLE]`，语义不明不猜；未来接入其他 Provider 只新增真实适配器，不改本 Skill 核心流程。
## 关键词专项路由（6-0-2）

6-2 只识别 ASIN 经营层面的关键词异常或机会（例如 Search Term 覆盖变化、核心词自然排名信号、广告/自然词转化差异），不再复制 ERP 精准词筛选、精准泛词生成、Search Intent 聚类或 Rankability 算法。精准词问题输出 `Route → 6-0-2`；精准泛词问题输出 `Route → 6-0-3｜精准泛词提取`（`hzp-amz-6-0-3-precision-broad-extraction`），并读取对应最新有效资产。
