# 0-7 数据契约

PickKw 必须由现有 ERP Provider 提供自动编号字段 Id、Keyword、KeywordCn。Id 是唯一追溯键；扫描使用稳定 keyset/page token，不用第一行或全表替代。每次运行必须携带明确 Scope（ProductCode、ERP ProId、筛选条件或批次）。Provider 根据估算数据量选择有上限的 page size。

翻译请求每个规范化 Keyword 一次，保留 TranslationItemId、Id、Keyword。缓存仅在单次 Run 有效。

CSV 使用 UTF-8 with BOM，固定核心字段：
Id,Keyword,OriginalKeywordCn,ProposedKeywordCn,FinalKeywordCn,Action,ResultStatus,FailureReason

已有非空 KeywordCn 永远 SKIP_ALREADY_TRANSLATED；空源词 SOURCE_KEYWORD_EMPTY；并发填充 SKIP_CONCURRENTLY_FILLED；源词变化 SOURCE_KEYWORD_CHANGED；Dry Run 为 DRY_RUN_PROPOSED；成功写后读回为 UPDATED_VERIFIED；读回不一致 READBACK_MISMATCH；Provider 未验证为 WRITE_BLOCKED。

每次运行必须记录 Scope、RunId、page size、扫描/缺失/已有/空源/翻译请求/缓存命中/更新/失败/回读不一致/写入阻断，并输出报告。
