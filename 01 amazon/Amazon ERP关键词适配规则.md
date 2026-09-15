# Amazon ERP 关键词 Provider 边界

阶段 6 的 ERP 关键词读取统一通过 `scripts/erp_keyword_adapter.py`。6-1、6-2、6-3 不得各自编写 SQL 或根据列名猜测业务含义。

## 固定输入链

`Product_Code → Product Root → 01_产品档案.md → ERP编号 → Amazon.dbo.PickPwKView.ProId`

- 产品档案当前使用的 ERP 字段名是 `ERP编号`（适配器同时兼容文档中明确写出的 `ERP_ProId` 等等价标签）；适配器返回实际匹配到的字段名。
- 没有编号返回 `[ERP_PROID_MISSING]`；同一档案出现多个不同编号返回 `[ERP_PROID_CONFLICT]`。
- 查询只允许 `WHERE [ProId] = ?` 参数化条件，不能用 Product_Code、ASIN、文件名、第一条记录或相似产品替代，也不跨产品读取。

## 字段语义与 Canonical Evidence

字段定义唯一来源是 `00_公共资料/03_系统配置/erp-amazon-pickpwkview-schema.md`。当前文档明确记录 `ProId`、`Keyword`、`KeywordCn`、`UpdateTime`、`RecordDate` 的结构性用途；其余列原样保留并标记 `SEMANTICS_UNCERTAIN`，不得直接当作搜索量、点击、订单、销售、CVR、排名或竞价使用。适配器返回每行原始字段和以下追溯字段：`Provider`、`Source_View`、`ERP_ProId`、`Field_Definition_Source`、`Retrieved_At`、`Source_Grain`、`Metric_Semantics`、`Data_Through`、`Freshness`、`Aggregation_Method`。

## 安全与降级

连接配置复用 `03_系统配置/sql-server-erp-connection.json`；密码只从已有密钥管理器或 `passwordRef` 对应环境变量读取，不进入 Skill、报告、日志或 Git。SQL 账号必须是只读；适配器只执行参数化 `SELECT`。连接驱动或密钥不可用返回 `[ERP_KEYWORD_PROVIDER_UNAVAILABLE]`，无匹配行返回 `[ERP_KEYWORD_DATA_NOT_FOUND]`，阶段 6 其余证据继续运行。

## 阶段 6 使用边界

- 6-1：当前产品 ERP 关键词只能作为 COR 候选、EXP 候选和少量 DIS Broad Seed 的辅助证据；不能由 ERP 历史标记直接升级为核心成交词。
- 6-2：可作为当前产品历史关键词背景或监控解释；当前 Amazon 经营数据优先，语义不明不计算经营指标。
- 6-3：可作为历史 Search Term/生命周期参考；当前 Amazon 自有广告数据足够后由自有数据接管，不能跨产品扩展。

ERP 关键词是公司第一方历史证据，不替代 Amazon 当前广告事实、H10/Cerebro 竞品反查或 SellerSpace 实时数据。
