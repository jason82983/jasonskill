---
name: hzp-amz-6-0-2-precision-broad-extraction
description: 读取 6-0-1 AI 精准词资产，按共同购买意图提取最小精准泛词并合并已知搜索量；不重新判定精准词或执行广告写操作。
metadata:
  short-description: 精准泛词提取
---

# HZP Amazon 6-0-2｜精准泛词提取

## 定位与边界

6-0-2 的唯一核心职责是读取当前产品最新有效的 `6-0-1_[Product_Code]_AI精准词.csv`，按共同购买意图合并并提取 High-Precision Broad Seed（精准泛词），再按已知搜索量合计降序输出。精准词识别属于 6-0-1；排名、广告策略和 Amazon Ads 写操作不属于 6-0-2。

6-0-2 不重新查询 SQL Server 判断精准词，不使用 `IsExact`，不修改 ERP，不修改历史报告，不调用 `apply_change_plan`，不创建或修改广告。

## 运行与输入

支持 `6-0-2，Product_Code`。固定当前 Product Root 后，读取：

```text
06_SKILL分析报告/6-0-1_精准关键词识别/6-0-1_[Product_Code]_AI精准词.csv
```

默认只读取该六列 AI 文件；每行均视为 6-0-1 已确认精准词，`自动编号`只作上游追溯并被 6-0-2 忽略，不重新连接 SQL、不重新评估精准度。文件缺失时返回 `[6-0-1_AI_PRECISION_KEYWORD_INPUT_MISSING]`。

## 同意思合并与精准泛词

先规范化并按共同购买意图分组。词序、介词和单复数变化在购买意图一致时可合并；Birthday、Christmas、Graduation 等明确场景必须保持分组边界，不能为扩大总量强行合并。

精准泛词是 High-Precision Broad Seed：

- 至少两个英文单词，但不把“2 词”当成压缩目标。
- 必须保留最小有效搜索意图（Minimum Viable Search Intent）。删除一个词会改变类别、功能、人群、场景、购买对象、礼赠关系或扩大错误流量时，不得删除。
- 必须先聚类，再从族的共同意图提炼；不允许每个精准词机械删词生成一个 Broad。
- 一个语义组只提取一个最小有效精准泛词；只有单词的结果不输出。
- 删除词会扩大错误流量或改变类别、对象、功能、场景、关系、属性时停止缩短。
- 同一标准化 Keyword 只计一次搜索量，`自动编号`不参与聚类或搜索量计算；同词多 Record ID 且搜索量相同只计算一次。多个真实记录的搜索量不同且无法依据日期、新鲜度或已确认 Schema 语义解决时，输出 `[DUPLICATE_KEYWORD_VOLUME_CONFLICT]`，不得 SUM 或静默选择。

合并总量仅表示当前输入中已知搜索量的内部合计参考，不等于独立消费者数或 Amazon 官方市场容量；全部搜索量缺失的组排在有效总量之后。

## 输出

默认生成 UTF-8 with BOM：

```text
[Product Root]/06_SKILL分析报告/6-0-2_精准泛词提取/6-0-2_[Product_Code]_精准泛词.csv
```

最终 CSV 严格只有三列：`词`、`中文`、`同意思词的合并总量`，并按合并总量从大到小排列。

6-0-2 只生产精准泛词资产；不生成关键词族 CSV，不做 COR/EXP/DIS、排名、生命周期或广告决策。结构化 CSV 不进入 0-2 正式报告索引。

实现细节见 [references/broad-seed-cluster-v1.md](references/broad-seed-cluster-v1.md) 和 `scripts/broad_seed_cluster.py`。
