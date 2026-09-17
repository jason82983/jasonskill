# 6-5 执行约束

只允许执行已批准且与 prepare_change_plan 完全一致的动作。Campaign、Ad Group、Keyword、Target、Bid、Budget、Placement、Negative、Status 的每次写入都必须有真实身份、能力状态、批准记录和 read-back。
