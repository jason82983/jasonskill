# 6-0-2 Golden Calibration Cases

这些样本用于校准 `Searcher Intent → Current Product Fit` 的边界，不是关键词黑名单或可执行字符串映射。实际运行必须读取当前产品事实并逐词分析完整 modifier。

当前 B2 校准产品：Sister / Friendship relationship gift；resin keepsake figurine；white-moon symbolic connection；home décor / collectible figurine。

| Keyword | 期望等级 | 关键判断 |
|---|---|---|
| sister birthday gifts | 高度精准 | 关系、对象、场景和礼物目的共同构成产品核心购买意图 |
| gift for sister | 高度精准 | 明确关系礼物目的，产品是该意图下的核心答案 |
| best friend gifts for women | 高度精准 | 友情礼物意图与产品纪念关系主题直接匹配 |
| friendship gifts for women | 高度精准 | 友情关系礼物是产品核心用途，不要求出现 figurine |
| sister | 精准 | 关系主题匹配，但没有明确商品或送礼目的 |
| birthday gifts for women | 弱精准 | 宽泛人群/场景下存在大量其他商品答案 |
| gift for women | 弱精准 | demographic recipient 过宽，产品只是 CAN SERVE |
| gift | 不精准 | 没有足够购买对象或商品约束 |
| sister figurine | 高度精准 | 商品类型和关系对象共同直接匹配 |
| 3 sisters figurine | 不精准 | 两人物产品面对明确数量/representation conflict |
| 4 sisters figurine | 不精准 | 明确人物数量与当前产品冲突 |
| 5 sisters figurine | 不精准 | 明确人物数量与当前产品冲突 |
| wooden sisters figurine | 不精准 | wooden 材质要求与 resin 产品冲突 |
| sister birthday card | 不精准 | 明确寻找 card，发生商品类型冲突 |
| personalized gifts for women | 不精准 | 明确要求个性化而产品无该能力 |

完成一批关键词后必须做 Cross-Level Consistency Check：不能把“没有 figurine”一律降级，也不能把“出现 figurine”一律升为高度精准。Benchmark 自然排名只作为 Market Reality Evidence。

## Golden Case 增量字段

每个 Golden Case 同时记录 `PrimaryPurchaseDriver`、`PurchaseMissionFit`、`PhysicalProductConvergence`、`CaseType`。Gift 相关类型包括 `GIFT_HIGH_MISSION_FIT`、`GIFT_BROAD_INTENT`、`GIFT_RELATIONSHIP_ONLY`、`GIFT_OCCASION_ONLY`、`GIFT_HARD_CONFLICT`。这些案例用于回归，不是按 Keyword 字符串硬编码答案；Current Product 未确认前不得把案例自动写入正式判断。

| CaseType | Keyword | Driver | PurchaseMissionFit | PhysicalProductConvergence | 期望等级 |
|---|---|---|---|---|---|
| GIFT_HIGH_MISSION_FIT | sister birthday gifts | GIFT_EMOTIONAL | HIGH | MEDIUM | 高度精准 |
| GIFT_HIGH_MISSION_FIT | friendship gifts for women | GIFT_EMOTIONAL | HIGH | MEDIUM | 高度精准 |
| GIFT_BROAD_INTENT | birthday gifts for women | GIFT_EMOTIONAL | LOW | LOW | 弱精准 |
| GIFT_RELATIONSHIP_ONLY | sister | GIFT_EMOTIONAL | MEDIUM | LOW | 精准 |
| GIFT_HARD_CONFLICT | personalized gifts for women | GIFT_EMOTIONAL | HIGH | LOW | 不精准 |
