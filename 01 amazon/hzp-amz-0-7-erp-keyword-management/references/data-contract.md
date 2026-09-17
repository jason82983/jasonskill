# 0-7 数据契约

正式源表：ERP PickKw。禁止使用 PickPwKView 视图。

唯一追溯键：PickKw.Id（自动编号字段）。
可读取：Id、Keyword、KeywordCn。
唯一可写字段：KeywordCn，且仅当当前值 NULL/空串/全空白时。

每次运行必须带 Limit=N（正整数）；N 是本次最多处理的缺失中文记录数，不是全表行数。还应记录筛选条件、RunId、page size。Provider 使用稳定 keyset/page token 和有上限的自适应 page size。

CSV 固定核心字段：
Id,Keyword,OriginalKeywordCn,ProposedKeywordCn,FinalKeywordCn,Action,ResultStatus,FailureReason

每次运行必须输出带时间戳 CSV、最新 HTML、历史 HTML 和 metadata。
