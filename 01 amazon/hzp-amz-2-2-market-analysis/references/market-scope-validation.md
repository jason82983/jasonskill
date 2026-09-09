# Market Scope Validation

## Goal

判断目标产品真正进入哪些 Amazon Niche，不把用户提供的 Niche 名称直接当作市场事实。

## Procedure

1. 从目标 ASIN 的 Niche 出现记录开始，列出所有候选 Niche。
2. 为每个 Niche 建立证据行：主要搜索词、头部商品、点击/购买行为、消费者用途、产品形态、评论与退货、目标产品真实功能。
3. 为每个 Niche 标记 Primary Market、Secondary Market、Overlapping Market、Adjacent Market 或 False / Weak Match。
4. 只有证据支持产品形态、用途和搜索意图同时匹配时，才可作为主切入口。
5. 证据不足时写 [证据不足]，保留候选，不强行归类。

## Output table

| Niche | 搜索意图 | 产品/用途匹配 | 头部商品匹配 | 消费者证据 | 分类 | 关键限制 |
|---|---|---|---|---|---|---|

市场名称是标签；搜索、点击、购买、评论和产品功能才是边界证据。一个产品可以拥有多个真实市场，不必强制只选一个。

