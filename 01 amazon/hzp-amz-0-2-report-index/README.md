# HZP Amazon 0-2｜分析报告索引

这个 Skill 只负责扫描当前产品已经生成的正式 Amazon Skill HTML 报告，并生成或更新：

```text
[Product Root]\06_SKILL分析报告\index.html
```

运行时通常只需要告诉 Codex：

```text
使用 0-2 Skill
产品：P001
Products Root：E:\【产品总目录】
```

它会自动定位产品目录、扫描现有报告、按 Skill 和版本排序，并生成可离线打开的报告中心。正式报告成功生成后，2-1、2-2 等报告型 Skill 会自动调用 0-2 刷新索引。

详细规则和脚本见 `SKILL.md`、`references/report-index.md` 与 `scripts/update_report_index.py`。
