# Precision Judgment Contract (delegating to the active kernel)

本文件保留为既有引用路径。当前唯一有效的判断规则是 [`precision-judgment-kernel.md`](precision-judgment-kernel.md)，不再在此文件维护第二套判断逻辑。

6-0-2 必须先独立还原 Amazon 搜索者的购买意图，再比较 Current Product 是否为 CORE FIT；不能把产品类型词是否出现、搜索量、Benchmark 排名或词面重合当作精准度代理。Gift-led relationship intent 可在没有 figurine/statue 词时达到高度精准；明确商品类型、材质、数量/人物表达、个性化、兼容性、尺寸、功能或主题冲突必须阻止高度精准。

正式输出是同一 Run 的三张公共表加 N 张按所属产品编号拆分的 D 表，直接放在固定报告根目录，以 `run_manifest_{RUN_TIMESTAMP}.json` 绑定完整包，不创建时间戳子文件夹。A/B 保留 Observation 粒度（`所属产品编号,对标ASIN,Id,词,中文,市场容量,竞争产品数,供需比,自然排名,精准度,精准原因`）；C 为去对标、Canonical Keyword 唯一的高精准表（`Id,词,中文,市场容量,竞争产品数,供需比,对标覆盖数,最佳自然排名,自然排名中位数,精准度,精准原因`）；D 是从 B 按所属产品编号筛出的各对标高度精准表，并保留 A/B Schema。每个 Canonical Keyword 只判断一次，结果一致地回填 A/B；B 严格从 A 筛选，C 从 B 汇总，D 从 B 分组筛选，均不再调用 AI。市场事实在 C 只保留一次。SQL NULL 以空 CSV 单元格保留，不转成 0。Coverage、筛选、透传、唯一词去重、3+N完整性、文件时间戳及拆分覆盖都必须校验通过，才标记 `FULL_SUCCESS/VALID`。精准度只允许高度精准、精准、弱精准、不精准；排序、Record ID 与其他来源数据契约不变。
