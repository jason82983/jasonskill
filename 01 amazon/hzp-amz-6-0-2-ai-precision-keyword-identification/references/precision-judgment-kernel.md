# 6-0-2 Precision Judgment Kernel

这是 6-0-2 的唯一精准判断内核。它替换“产品类型词出现得越完整，精准度越高”的旧判断方式；输入、输出、Record ID、Coverage Check、文件路径和下游边界不变。

## 固定判断顺序

1. **先独立还原 Searcher Intent**：记录 purchase goal、显式商品类型、recipient/relationship、occasion、required attributes、quantity、material、feature、theme 和其他 hard modifiers。先回答消费者想买什么，再读取当前产品事实进行比较。
2. **识别 Search Mode**：PRODUCT-LED、GIFT-LED、BROAD-GIFT、RELATIONSHIP-ONLY、HARD-SPECIFIED。Gift-led 查询不要求出现 figurine/statue/decor 等产品类型词。
3. **区分 CORE FIT 与 CAN SERVE**：当前产品本身围绕该关系/礼物购买目的设计时是 CORE FIT；只是众多可送礼答案之一时是 CAN SERVE。
4. **检查所有 Hard Modifiers**：商品类型、材质、数量/人物表达、个性化、兼容性、尺寸、功能和主题要求逐项核对。任何明确冲突都否决“高度精准”，商品类型冲突通常为“不精准”。
5. **Benchmark 自然排名只作 Market Reality Evidence**：不得用排名升降精准等级。
6. **反事实检查**：把产品放到该词搜索结果第一页，买家是否会自然认为它就是本次要买的商品？若只是“也能当礼物”，属于 CAN SERVE。
7. **直接裁决四级**：高度精准、精准、弱精准、不精准；禁止数学评分、固定权重、词数阈值和硬编码词表。

## 关系型礼物边界

当前产品若已确认是 Sister/Friendship relationship keepsake gift，则 `sister birthday gifts`、`gift for sister`、`best friend gifts for women`、`friendship gifts for women` 可以是高度精准，即使没有写 figurine。`sister` 可为精准；`birthday gifts for women`、`gift for women` 通常是弱精准；`gift` 不精准。以上是 B2 校准样本，不得按完整字符串硬编码到程序。

## Modifier 反例

`3 sisters figurine` 在产品只有两个人物时存在 representation/quantity conflict；`wooden sisters figurine` 在产品为 resin 时存在 material conflict；`sister birthday card` 是 product-type conflict；不支持个性化的产品不能接受 `personalized gifts for women`。不得由 sister + figurine 自动通过，也不得由 gift 未写产品类型自动降级。

每条结果的理由必须用 1–2 句话说明搜索者主要想买什么，以及当前产品是 CORE FIT、CAN SERVE 还是发生冲突；不得批量复制同一句理由。`REVIEW_REQUIRED` 只作为内部证据不足状态，正式 CSV 仍使用四级之一。
