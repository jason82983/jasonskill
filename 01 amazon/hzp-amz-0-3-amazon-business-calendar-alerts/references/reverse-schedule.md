# 产品与新品 Launch 倒排

倒排链：

`Target Selling Start → Cold Start → FBA Receiving Buffer → International Shipping → Production → Sample/Development → Latest Development Start`

公式：

`Latest Development Start = Target Selling Start - Cold Start Days - FBA Receiving Buffer Days - Shipping Days - Production Days - Development/Sample Days`

Launch 还要倒排：Listing Ready、Inventory Ready、FBA Available、Advertising Start、Review/Conversion Observation、6-1 Initial Plan、6-2 Operating Diagnosis、6-3 Advertising Optimization。

参数优先级：真实产品/供应链数据 > 人工确认计划 > 公司默认规划参数 > AI规划假设。国际运输默认 30 天，新品 Cold Start 默认 30 天，均标 `[系统默认规划参数]`；实际运输 45 天就用 45 天。未知参数不能伪装为事实。

目标销售日已近而总链路超出剩余时间时，输出 `[计划时间不足]`，并逐项列出可验证的压缩方案与代价。超过 deadline 时标 `[明显滞后]`，不得只报错。
