---
name: hzp-amz-0-6-skill-sync-github
description: 同步 HZP Amazon 技能：将 .codex/skills 下 hzp-amz-* 技能镜像到 JasonSkill，并在用户明确说“同步git”时提交并推送到 GitHub。
metadata:
  short-description: HZP Amazon 技能双向镜像与 GitHub 同步
---

# 0-6 HZP Amazon 技能同步

## 触发

调用本 Skill 时按输入执行：空输入不执行任何动作；输入 `1` 执行完整流程，校验 `.codex` 与 JasonSkill 两边，将 `.codex` 中全部 `hzp-amz-*` 技能镜像到 JasonSkill，提交并推送 GitHub，确保两边与远端一致。本 Skill 只处理名称以 `hzp-amz-` 开头的技能。

## 固定路径

- 源技能：`C:\Users\qmhzp\.codex\skills\hzp-amz-*`
- 镜像仓库：`E:\codex\JasonSkill\01 amazon\hzp-amz-*`
- 远端：JasonSkill 当前 Git 仓库的 `origin`（GitHub）

## 执行顺序

1. 扫描源目录和仓库目录，按技能目录名建立一一对应关系。
2. 先做差异预检：缺失目录、文件差异、删除风险、未跟踪文件、当前分支和远端状态。
3. 将源技能内容同步到仓库对应目录；同步每个技能的完整说明与资源，必须包含 `SKILL.md` 和 `README.md`（若源目录存在），以及 `agents/`、`scripts/`、`references/`、`templates/`、`assets/` 等文件；同时更新 JasonSkill 的 `01 amazon/README.md` 与仓库根目录 `README.md` 中的技能索引；以 `.codex` 内容覆盖 JasonSkill 中旧的 README 和其它技能文件。差异比对后不得视为完成。不同步 `__pycache__`、`.pyc`、临时输出和运行报告。
4. 运行 Skill 格式校验，并检查 Git diff；源目录不存在的仓库 `hzp-amz-*` 技能必须删除，并在提交报告中列出删除清单。
5. 输入 `1` 时，在核对 diff 后提交并推送 `origin`。提交信息说明同步范围；推送失败必须保留本地提交并报告原因。空输入不执行同步、提交或推送。

## 约束

- 两个位置都必须同步：`.codex` 是技能源，JasonSkill 是可审计镜像；默认执行完成后逐项确认两边存在且内容一致；源目录不存在的旧技能从 JasonSkill 删除，不从 JasonSkill 反向覆盖源技能。
- 不修改产品数据、分析报告或非 `hzp-amz-*` 技能。
- 发现同名技能内容冲突、仓库有用户未提交改动或远端领先时，先报告并停止有风险的覆盖/推送。
- 同步完成后报告：技能数量、变更文件、校验结果、提交号和推送结果。

## 推荐脚本

仓库中的 `scripts/sync_hzp_amz_skills.py` 提供预检和镜像；默认只同步并显示 diff，使用 `--push` 才执行提交和推送。








