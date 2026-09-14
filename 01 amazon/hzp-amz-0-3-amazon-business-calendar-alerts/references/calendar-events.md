# Amazon US经营节点维护

每个节点应保存 `event_id`、名称、类型、市场、event_date、season_start、peak_start/peak_end、season_end、适用产品类别、各阶段天数、来源、来源日期、证据类型、置信度和最后核验时间。

固定节日使用可复核的日历规则；Easter、Mother's Day、Father's Day、Memorial Day、Labor Day、Thanksgiving、Black Friday、Cyber Monday 等按年份计算或读取可靠来源。Back to School 使用市场窗口而非虚构的单日。Prime Day、Prime Big Deal Days 和其他 Amazon 活动只有 Amazon 公布后才写具体日期；未公布时写 `[日期待Amazon公布]`，历史日期只标 `[历史规律参考]`。

同时记录消费者实际开始购买的 `season_start` 与高峰 `peak_start/peak_end`。它们不是节日当天，必须有来源或清楚标记为历史参考/AI规划假设。产品相关性需要结合产品档案和证据判断，不因节日名称自动判定相关。

建议验证频率：固定规则每年复核；可变节日按年份复核；Amazon活动在官方公布前保持待定，公布后记录来源与 `last_verified_at`。
