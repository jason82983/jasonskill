# JasonSkill

这是 HZP 的个人与团队 Skill 仓库。根目录 README 只负责说明行业分类和 Skill 索引；每个具体 Skill 的详细用途、输入、输出和使用方法，写在自己的 `README.md` 中。

## 行业目录

| 行业 | 目录 | 当前状态 | 说明 |
|---|---|---|---|
| Amazon | [01 amazon](<01 amazon/README.md>) | 已建立 | Amazon 产品资料、市场分析和产品开发相关 Skills |
| 其他行业 | 待建立 | 未建立 | 后续按行业新增独立目录和行业 README |

## 当前 Skill 总览

| Skill | 所属行业 | 目标 |
|---|---|---|
| `hzp-amz-0-1-product-file-structure` | Amazon | 管理 Products Root 和 Product Root 的标准文件结构 |
| `hzp-amz-2-1-market-research` | Amazon | 分析单个 Amazon 产品的市场表现、证据和开发可行性 |
| `hzp-amz-2-2-market-analysis` | Amazon | 判断细分市场范围、市场进入机会和改良开发价值 |
| `hzp-amz-3-1-product-development` | Amazon | 将研究结论转成产品定义、打样、测试和开发交接 |

## 使用约定

- 每个 Skill 都有独立目录和自己的 `SKILL.md`；
- 每个 Skill 都应提供面向使用者的 `README.md`；
- 行业目录 README 说明该行业的 Skill 体系和衔接关系；
- 根目录 README 只维护行业分类和基础索引，不重复具体 Skill 方法论；
- 修改 Skill 时，以本仓库对应目录为源版本，再同步到本机 Codex Skill 目录；
- 提交前运行 Skill 校验，避免把临时报告、原始业务数据或个人敏感信息加入仓库。

## 目录结构

```text
JasonSkill/
├─ README.md
└─ 01 amazon/
   ├─ README.md
   └─ hzp-amz-*/
      ├─ SKILL.md
      ├─ README.md
      ├─ agents/
      ├─ references/
      └─ templates/
```
