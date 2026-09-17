# Skill Context Manifest Index

所有 `hzp-amz-*` Skill 默认读取 `GLOBAL = Operating System + Evidence Contract`。下表定义 DOMAIN、UPSTREAM、HISTORY 和 FORBIDDEN 的最小边界；Skill 自身 Contract 可以进一步收紧，但不得扩大读取范围。

| Skill | DOMAIN | UPSTREAM | HISTORY | FORBIDDEN |
|---|---|---|---|---|
| 0-1 / 0-2 / 0-3 / 0-4 / 0-5 | Directory / Index / Calendar / Rules / Decision | 当前产品档案、规则资料或已锁定输入 | 按自身 Contract | 不把公共知识当产品事实 |
| 1-1 / 1-2 | Opportunity / Screening | 产品资料、市场证据和上游交接包 | 按自身 Contract | 不把估计指标写成事实 |
| 2-1 / 2-2 / 2-3 | Product Analysis / Market / Sync | 当前产品正式输入、2-1/2-2/人工交接 | 按自身 Contract | 不跨 Product Root，不静默覆盖冲突 |
| 3-1 / 3-2 / 3-3 | Opportunity Definition / Development / Review | 上游正式报告和产品资料 | 按自身 Contract | 不重做市场研究或替工程定版 |
| 4-1 / 4-2 | Sample / Preproduction | 3-3方案、样品、BOM、供应链和合规证据 | 按自身 Contract | 没有样品或量产证据不假装完成 |
| 5-0-1 / 5-1 / 5-2 / 5-3 / 5-4 / 5-5 | Retrieval / Listing / Visual / Audit | 当前页面、产品事实、上游页面策略与文案 | 按自身 Contract | 不把 AI 解释当原始页面事实 |
| 6-0-1 | Benchmark Organic Fact | PickPwKView 原始排名与产品档案 | 不读取判断历史 | 不做精准度或广告判断 |
| 6-0-2 | Keyword Precision | 601 Latest Valid + 当前产品识别文本 | 不读取历史判断 | 不把排名或多 Benchmark 投票当精准度 |
| 6-0-3 | Search Intent | 602 Latest Valid 去重高度精准词 | 不读取历史判断 | 不重判精准度、不按字符串造父子 |
| 6-0-4 | ERP Sync | 602 已确认精准词资产 | 按写入 Contract | 不重新判断精准词 |
| 6-0-5 | Launch Strategy | 603 Intent Tree、606 Reality、602 血缘 | 按自身 Contract | 不把机会比或排名直接当首攻 |
| 6-0-6 | Benchmark Reality | 602 分对标资产 + 603 Intent Tree | 按自身 Contract | 不重判精准度、不写销量份额 |
| 6-1 | Build / Reconcile | 605 Approved Plan + 产品档案 + Live Ads | 身份与执行历史 | 不重判 605、不扩大 Campaign Scope |
| 6-2 | Advertising Facts | Live Ads / Provider read-only facts | 按运行包 Contract | 不诊断、不推荐、不写广告 |
| 6-3 | Evidence Maturity / Optimization | 6-2 Facts + 605/603/606 context | 必须读取历史决策 | 不直接写 Amazon、不机械按天优化 |
| 6-4 | Safe Apply | 6-3 Approved decisions + Live Actual | 必须读取执行历史 | 不重判商业动作、不覆盖新状态 |
| 7-1 / 7-2 | Replenishment / Inventory Risk | 销售、库存、在途、Lead Time | 按自身 Contract | 缺关键证据不硬算 |
