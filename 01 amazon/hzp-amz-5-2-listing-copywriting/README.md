# HZP Amazon 5-2｜Listing文案

## 30 秒运行

```text
使用 5-2 Skill
产品：P001
Products Root：E:\【产品总目录】
```

5-2 读取最新 5-1 页面策略、01 产品档案、07 产品资料和真实关键词/产品证据，生成可支持 Amazon 最终创建/更新 Listing 的内容数据包。除 Title、Bullet Points、Product Description、A+ 文字基础外，还包含 Item Highlights、Backend Search Terms、动态 Listing Attributes、Core Selling Points、Keyword Allocation 和全字段 Claim 审核。

## 使用前

当前 Product Root 应有 `01_产品档案.md`、`03_产品页面思路.md`、最新 5-1 正式报告，以及可用时的 `05_分析源数据\03_关键词数据`、`07_产品资料`。5-2 会主动读取实际内容，不要求你手工整理所有字段。

当前 Amazon US 非 Media 类目规则：Product Title ≤75 characters（包含空格），Item Highlights ≤125 characters（包含空格）。每次运行都会自动计算字符数，超限版本不得标为最终推荐；规则来源和更新时间以 [Amazon Seller Central 2026-07-27 公告](https://sellercentral.amazon.com/seller-forums/discussions/t/33f0a42a-17f1-46ef-b110-ba7512a3c881) 及本地最新版平台资料为准。

## 输出

正式报告写入：

`[Product Root]/06_SKILL分析报告/5-2_[产品编号]_Listing文案_Vx_YYYYMMDD_HHMMSS.html`

报告包含 Search Result First-Screen Copy、Title/Item Highlights 字符数检查、Keyword Allocation、正式 Bullet、Description、Backend Search Terms、动态 Listing Attributes、Core Selling Points、Amazon Listing Creation Data Package、Claim—Evidence 检查、SEO/可读性检查和 5-3/5-4 交接包。正式报告成功后自动调用 0-2 更新索引；5-2 不自行维护 `index.html`。

关键词资料不足时，仍可在事实充分的前提下形成转化版文案，并明确缺口；不会编造搜索量、排名、CPC、转化率或消费者评价。正式 Amazon 文案以自然美国英语为准，中文只用于报告解释。
