# HZP Amazon Skills

本目录集中维护 Amazon 行业 Skills。它们按产品工作流程衔接：

```text
产品文件结构 → 产品分析 → 细分市场分析 → 产品开发
0-1              2-1        2-2             3-1
```

每个 Skill 的详细使用说明，见对应目录中的 `README.md`；本文件只说明 Amazon 行业的基本分工和入口。

## Skill 清单

| 编号 | Skill | 用途 | 下一步 |
|---|---|---|---|
| 0-1 | `hzp-amz-0-1-product-file-structure` | 建立、检查和整理产品资料目录，保护原始数据 | 进入分析 |
| 2-1 | `hzp-amz-2-1-market-research` | 分析单个 Amazon 产品、需求、竞品、评论和开发可行性 | 进入 2-2 或 3-1 |
| 2-2 | `hzp-amz-2-2-market-analysis` | 判断产品所属细分市场、市场机会和改良开发价值 | 进入 3-1 |
| 3-1 | `hzp-amz-3-1-product-development` | 输出产品定义、规格、样品、测试和开发交接 | 生产与后续阶段 |

## 基本使用方式

通常告诉 Codex：

```text
使用 [Skill名称]
产品：P001
Products Root：E:\【产品总目录】
```

Skill 会根据标准 Product Root 结构自动查找资料。具体数据位置、输入要求和输出文件名，以对应 Skill 的 README 为准。

## 目录约定

```text
[Products Root]/
├─ 00_产品公用数据/
└─ [Product Root]/
   ├─ 01_产品档案.md
   ├─ 05_分析源数据/
   └─ 06_SKILL分析报告/
```

不同员工或电脑可以使用不同的 Products Root；Skill 应依靠产品身份和标准相对路径定位资料，不依赖固定盘符。

## 衔接原则

- 0-1 负责资料结构和产品身份；
- 2-1 负责单个产品证据和市场表现；
- 2-2 负责细分市场和进入机会；
- 3-1 负责把市场机会转成可打样、可测试的产品定义；
- 上一个 Skill 的正式报告和 `HANDOFF.md` 是下一个 Skill 的优先输入；
- 下游 Skill 可以验证、修正或否定上游推断，但必须保留证据来源和变化原因。

## 具体 Skill 说明

- [0-1 产品文件结构管理](<hzp-amz-0-1-product-file-structure/README.md>)
- [2-1 产品市场分析](<hzp-amz-2-1-market-research/README.md>)
- [2-2 细分市场分析](<hzp-amz-2-2-market-analysis/README.md>)
- [3-1 产品开发](<hzp-amz-3-1-product-development/README.md>)
