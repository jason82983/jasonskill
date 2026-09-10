---
name: hzp-amz-0-2-report-index
description: Scan a product project's formal Amazon Skill HTML reports and rebuild its offline 06_SKILL分析报告/index.html. Use when a user wants to create, refresh, repair, or inspect the report index; do not analyze products, edit reports, or change source data.
---

# HZP Amazon 0-2｜分析报告索引

## 唯一职责

只做：发现正式报告 → 解析元数据 → 分组排序 → 生成或更新 `06_SKILL分析报告/index.html`。

不做产品分析、市场判断、报告内容修改、原始数据修改，也不重命名、删除、移动或覆盖任何正式历史报告。`index.html` 是唯一允许覆盖的动态文件。

## Product Root 定位

优先使用用户明确提供的 Product Root。否则从当前目录向上查找 `PRODUCT.md` 或已确认的 `01_产品档案.md`；用户只提供 Products Root 和产品编号时，扫描候选产品目录并用产品身份文件确认。出现多个候选或身份冲突时停止询问，不凭文件夹名称、ASIN 或旧路径猜测。

产品编号和产品中文名称优先读取已确认的 `01_产品档案.md` 字段；没有时再读取 `PRODUCT.md` 的 `Current Product Code` / `Product Name`。不得仅凭文件夹名称猜测。

## 扫描与排除

每次运行都重新扫描：

```text
[Product Root]/06_SKILL分析报告/
```

递归发现实际存在的正式 `.html` 报告，排除 `index.html` 以及文件名或路径明确为 `test`、`temp`、`demo`、`debug` 的测试/临时输出。不得依赖上一次索引、人工清单或固定 Skill 列表；不存在的报告不显示。

## 文件名解析与排序

优先解析当前标准格式：

```text
[技能编号]_[产品编号]_[技能中文名称]_V[版本号]_[YYYYMMDD]_[HHMMSS].html
```

例如 `2-2_N24_细分市场分析_V3_20260928_192222.html`。解析 Skill 编号、产品编号、Skill 中文名称、版本、日期和时间。兼容旧格式；无法完整解析时仍索引文件名、所属 Skill 目录和打开链接，并标记 `历史报告`。

先按 Skill 编号自然排序（`2-1`、`2-2`、`3-1`）；同一 Skill 优先按版本号降序，再按文件名日期时间降序，最后以文件时间为后备。每个 Skill 分组第一份显示轻量 `[最新]` 标签并提供“打开最新报告”。

## index.html 生成要求

固定生成：

```text
[Product Root]/06_SKILL分析报告/index.html
```

页面顶部显示产品编号、产品名称、标题“分析报告中心”、正式报告总数、已产生报告的 Skill 数量和最近更新时间。每份报告显示 Skill 编号、Skill 中文名称、产品编号、版本/历史标记、生成日期时间、文件名和“打开报告”。索引采用与 HZP 报告一致的专业、克制、响应式视觉；使用内嵌 CSS/JS（如需要），不依赖互联网或服务器。

所有链接必须是相对于 `index.html` 的路径，例如 `./2-2_细分市场分析/2-2_N24_细分市场分析_V3_20260928_192222.html`。不得写入盘符、UNC、`file:///` 或其他绝对路径。

使用 [references/report-index.md](references/report-index.md) 了解兼容、排序和失败边界。使用 [scripts/update_report_index.py](scripts/update_report_index.py) 执行确定性的重建：

```text
python scripts/update_report_index.py --product-root <Product Root>
```

脚本必须幂等：重复运行只重建唯一的 `index.html`，不产生 `index_V2.html`、重复记录或循环调用。

## 两种调用方式

### 人工调用

用户可以说：

```text
使用 0-2 Skill
产品：P001
Products Root：E:\【产品总目录】
```

定位 Product Root 后扫描并更新索引。

### 报告型 Skill 调用

2-1、2-2 以及未来其他正式报告型 Skill 必须在 Human Report 成功落盘并确认文件存在后调用 0-2。索引失败时保留已成功生成的报告，并分别报告“正式报告生成成功”和“报告索引更新失败及原因”。0-2 自身生成 `index.html` 后不得再次调用自己；`index.html` 也不得被识别为正式报告。

## 完成检查

确认 Product Root 身份、索引路径、实际扫描范围、报告总数、Skill 分组、版本/时间排序、最新标记、旧格式标记和相对链接。不要修改正式报告、原始数据或其他目录。
