# HZP Amazon 6-2｜产品经营监控与诊断

**Skill ID:** `hzp-amz-6-2-product-operations-monitoring`

**职责：** DATA ONLY 广告运行事实数据层。

6-2将当前真实广告源整理为 Campaign、Intent、Target、Search Term 四层同次运行事实，输出四张机器CSV和一份从这些CSV内嵌生成的静态HTML。6-2不判断好坏、不诊断原因、不提出优化意见，也不写广告。经营分析与变更建议由6-3负责。

每轮必须输入 ProductCode + opaque CampaignTag。先从直播广告活动列表按精确带尾点的 `ProductCode.CampaignTag.` 筛选，再查询匹配 Campaign 的子级与表现；四张CSV不改Schema，HTML/Metadata记录Scope及账户、匹配、排除数量和匹配Campaign IDs。

参见 [SKILL.md](SKILL.md)、[广告事实合同](references/advertising-facts-contract.md) 与 [HTML模板](templates/report-outline.md)。`scripts/ad_facts_package.py`只构造/校验本地输入事实包，不连接SellerSpace；运行Skill时由已批准的只读Provider查询流程提供真实记录。

名称保留现有正式身份。当前“产品经营监控与诊断”名称与DATA ONLY职责存在不匹配，是否重命名由Skill所有者决定。
