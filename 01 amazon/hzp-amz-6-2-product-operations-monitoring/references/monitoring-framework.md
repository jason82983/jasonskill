# 6-2 数据运行流程

该历史文件名继续保留以兼容目录链接；当前规则已改为 DATA ONLY。

1. 校验当前产品身份、只读数据源、报告窗口及查询时间。
2. 发现当前Provider实体/字段语义并显式映射；未确认日期、ID、单位或指标时保持空值/源粒度并记缺口。
3. 读取 Campaign、Target、Search Term 原始事实及 6-1 已验证身份事件、批准的 6-0-5 作战表。
4. 按 `CampaignId / AdGroupId / TargetId → BattleUnitId → approved 605 row → IntentCode` 精确连接。Search Term只经实际Target连接。失败记录UNMAPPED与原因。
5. 程序计算比率、Intent聚合、数据覆盖和完整性；不在本文或HTML中作经营解释。
6. 先写同一Run的四CSV，再从这四CSV读回生成静态HTML，最后完成Run Metadata与package校验。

不执行产品销量/页面/Review/库存诊断；不读取ERP关键词用于广告事实判断；不从HTML或旧CSV声称实时数据。
