# 翻译契约

输出必须是 JSON 数组，每项只有 \`TranslationItemId\`、\`Keyword\`、\`ProposedKeywordCn\`。ProposedKeywordCn 是该英文搜索词的单条、简洁、自然的简体中文词组。

拒绝：空值、解释性前后缀、Markdown/JSON片段、编号列表、多条候选、把多个关键词合并、直接复制英文、超过 Provider 的 KeywordCn 长度限制。翻译不确定时返回验证失败，由流程人工处理；不要编造产品属性或营销文案。

