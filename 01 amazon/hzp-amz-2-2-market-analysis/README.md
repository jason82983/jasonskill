# HZP Amazon 2-2｜细分市场分析

## 30 秒运行

通常只需要提供三个信息：

1. Skill：`2-2`
2. 产品编号
3. Products Root

直接复制并替换产品编号和根目录：

```text
使用 2-2 Skill

产品：P001
Products Root：E:\【产品总目录】
```

如果当前会话已经位于产品目录，也可以直接说：

```text
运行 2-2，分析当前产品。
```

## 2-2 做什么

2-2 判断：是否值得以当前对标产品为起点，进入其真实 Amazon 细分市场并进行改良开发。

它会给出：

- `GO`
- `CONDITIONAL GO`
- `NO-GO`

并为 `HZP Amazon 3-1｜产品机会定义` 提供市场机会输入。

没有明确对标产品时，自动使用 `Market-Driven Mode`；有对标产品时，默认使用 `Benchmark-Driven Mode`。

## 使用前准备

只需按 0-1 标准目录放好资料，并确认 Products Root 可访问。无需逐个告诉 Codex Keepa、Cerebro、Reviews、Niche 或榜1文件的位置。

标准产品目录至少包含：

```text
[Product Root]/
├─ 01_产品档案.md
├─ 05_分析源数据/
└─ 06_SKILL分析报告/
```

## Codex 会自动查找

所有路径都相对于自动识别出的 Product Root：

```text
05_分析源数据/01_产品数据/                 ASIN级 Keepa、Cerebro、Reviews、Listing
05_分析源数据/02_细分市场数据/所有细分市场/  ASIN-Niche关系和NichesProductAppears
05_分析源数据/02_细分市场数据/[Niche]/       Niche详细市场数据
05_分析源数据/03_关键词数据/                 独立关键词资料
05_分析源数据/04_用户反馈/                   VOC、QA、退货等
05_分析源数据/05_补充资料/                   外部或临时补充资料
```

公共 Amazon 指标定义从 Products Root 的共享资料中读取。文件名不完全统一时，Skill 会结合路径、表头、内容、ASIN和日期识别。

Product Root 的识别顺序是：当前目录 → 向上查找 → Products Root 下按产品编号定位。多个候选无法确认时才会询问。

## 输出位置

```text
[Product Root]/06_SKILL分析报告/2-2_细分市场分析/
├─ 2-2-[产品编号]_细分市场分析报告_[YYYY-MM-DD].html
└─ 2-2-[产品编号]_HANDOFF.md
```

HTML 给人阅读，`HANDOFF.md` 给后续 Skill 使用。已有报告不会被覆盖。

## 什么时候会停止

只有在以下情况无法自动继续时，才会要求补充信息：

- Product Root 或产品身份无法确定；
- 关键 ASIN 冲突；
- `所有细分市场` 没有可读取的 Benchmark Niche 数据；
- 关键 P0 市场数据缺失或无法解析；
- 多个最新文件无法判断版本。

报告会标出实际路径状态：`FOUND / MISSING / UNREADABLE / CONFLICT`。

## 常用追加指令

```text
请重点判断这个对标产品的改良机会。
```

```text
请读取 2-2 HANDOFF，继续进入 3-1 产品机会定义。
```

详细内部规则见 [SKILL.md](SKILL.md)；标准路径映射见 [references/data-location-map.md](references/data-location-map.md)。
