# 6-2 ERP 精准词分析参考

> 兼容性参考：精准词识别的维护主体现为 `hzp-amz-6-0-2-ai-precision-keyword-identification`，精准泛词提取由 `hzp-amz-6-0-3-precision-broad-extraction` 维护。6-2 只读取共享证据、识别经营异常并路由对应 Skill；本文件不授权 6-2 自行生成关键词战略或广告动作。

## 数据链与安全边界

`Product_Code → Product Root → 01_产品档案.md → ERP编号 → Amazon.dbo.PickPwKView.ProId`

通过共享 `scripts/erp_keyword_adapter.py` 查询；精准词读取使用参数化 `ProId` 与完整标签参数 `|1精准|`（`CHARINDEX(?, COALESCE([Tags], '')) > 0`），SQL 只允许参数化 `SELECT`。本文件不保存服务器、账号或密码。`03_系统配置` 只提供 `erp-amazon-data-mapping.json`、连接配置和字段字典，不存放产品关键词数据。

## 精准词字段

1. 先确认 `Keyword` 与 `Tags` 在 `erp-amazon-pickpwkview-schema.md` 中均为 `DOCUMENTED`。
2. 仅把 `Tags` 包含完整业务标签 `|1精准|` 的行纳入 ERP 精准词池；不得只搜索“精准”“1精准”或数字 `1`，也不得使用 `IsExact`（当前定义为“暂无用”）。
3. 关键词文本固定读取 `Keyword`；为空或无效的行不生成关键词。规范化只用于去重/聚类，原文、中文、ProId、记录时间和完整 `raw_fields` 必须保留。
4. 可用质量字段与语义状态逐项展示：`IsMain`、`IsLongTail`、`IsGoodCvt`、`IsSold`、`SearchVolume30`、`SearchVolumeDaily`、`SearchGrowthRate30`、`IQScore`、`SearchSoldSum`、`SearchCvtRate`、`SearchHitSum`、`SearchHitRate`。如果字段字典或编码不完整，显示 `SEMANTICS_UNCERTAIN`，不计算派生结论。
5. `RankOra`、`RankAdv`、`RankRec`、`abarank` 的排名体系、金额字段的币种/单位、站点号和其他未定义字段不得猜测。

## 关键词专项路由

6-2 只在 ASIN 经营监控中识别关键词覆盖、转化或自然排名异常，并保留 ProId、Keyword、数据窗口和证据缺口。需要确认人工/AI 精准词时输出 `Route → 6-0-2`；需要 Search Intent 或精准泛词时输出 `Route → 6-0-3`。6-2 不在自身报告中重新查询 ERP 判断精准词，不生成 Broad Seed。

## 报告最少字段

报告至少显示：ProId/ASIN、查询窗口、经营异常、相关 Keyword/Search Term、证据字段、语义状态、缺失/冲突状态和后续路由 6-0-2、6-0-3 或 6-3 的理由。
