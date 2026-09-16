# Precision Judgment Contract (delegating to the active kernel)

本文件保留为既有引用路径。当前唯一有效的判断规则是 [`precision-judgment-kernel.md`](precision-judgment-kernel.md)，不再在此文件维护第二套判断逻辑。

6-0-2 必须先独立还原 Amazon 搜索者的购买意图，再比较 Current Product 是否为 CORE FIT；不能把产品类型词是否出现、搜索量、Benchmark 排名或词面重合当作精准度代理。Gift-led relationship intent 可在没有 figurine/statue 词时达到高度精准；明确商品类型、材质、数量/人物表达、个性化、兼容性、尺寸、功能或主题冲突必须阻止高度精准。

正式输出为十一列：`Id、词、中文、市场容量、竞争产品数、供需比、对标覆盖数、最佳自然排名、自然排名中位数、精准度、精准原因`。前九列从 6-0-1 唯一关键词母池按 Id 原值透传；市场事实和多对标覆盖/排名聚合值不进入精准判断 Prompt，也不参与精准度判断或重算。SQL NULL 以空 CSV 单元格保留，不转成 0。FILE A 校验输入/输出 Id 覆盖与前九列原值，FILE B 校验高度精准筛选数量、Id 与前九列原值；不一致时返回对应 mismatch code，禁止报告 `FULL_SUCCESS`。精准度只允许高度精准、精准、弱精准、不精准；排序、Coverage、双 CSV、Record ID 与其他数据来源契约不变。
