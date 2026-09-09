# HZP Amazon 0-1｜产品文件结构管理

这个 Skill 负责管理单个 Amazon 产品项目的文件结构，为后续产品分析、细分市场分析、产品开发、页面和推广工作提供稳定的文件接口。

核心原则：**整理文件，不创造业务事实。**

## 三层目录架构

0-1 明确区分：

1. **Products Root**：所有产品和公共资料的共同容器；
2. **Shared Data**：`00_产品公用数据/`，保存多个产品共同使用的平台定义、公司标准和非敏感系统配置；
3. **Product Root**：单个产品的档案、人工思路、原始证据和 Skill 成果。

公共知识只保存一份，产品证据跟随产品。0-1 不把公共资料复制到每个产品目录；运行其他 Skill 时，应同时读取选定的 Product Root 和 Products Root 下的 Shared Data。

Products Root 的 Shared Data V1：

```text
[Products Root]/
├─ 00_产品公用数据/
│  ├─ 01_Amazon平台资料/
│  ├─ 02_公司标准/
│  └─ 03_系统配置/
└─ ... product directories ...
```

Amazon 平台资料是外部定义，公司标准是内部判断规则，系统配置是非敏感运行配置，三者不能混为一类。密码、Token、API Key、Secret 等敏感凭证不写入公开 Skill。

## 能做什么

- 为新产品创建标准 Product Directory V1；
- 检查现有产品目录；
- 扫描旧结构并提出整理计划；
- 在确认无覆盖和数据丢失风险后，移动或安全重命名文件；
- 把原始证据、人工思路和 Skill 分析成果分开保存。

## 不做什么

- 不做产品分析、市场分析或产品开发决策；
- 不修改 CSV、XLSX、TXT、PDF、图片等原始证据内容；
- 不猜测 ASIN、产品名称、店铺、负责人或产品状态；
- 不删除无法识别的文件；
- 不把 AI 结论写入人工思路文件。

## 标准结构

```text
[Product Root]/
├─ 01_产品档案.md
├─ 02_产品开发思路.md
├─ 03_产品页面思路.md
├─ 04_产品推广思路.md
├─ 05_分析源数据/
│  ├─ 01_产品数据/
│  │  ├─ 本产品/
│  │  └─ 对标产品/
│  ├─ 02_细分市场数据/
│  ├─ 03_关键词数据/
│  ├─ 04_用户反馈/
│  └─ 05_补充资料/
└─ 06_SKILL分析报告/
```

产品身份以 `01_产品档案.md` 中的 `产品编号` 为主要依据。`05_分析源数据` 按证据类型和研究对象组织；`06_SKILL分析报告` 只保存真正生成的 Skill/AI 成果，不提前创建大量空目录。

分类时区分 **Definition ≠ Evidence**：回答“这个指标是什么意思？”的公共定义进入 Shared Data；回答“这个产品或市场的指标是多少？”的实际数据留在对应 Product Root。发现产品目录内明显的公共术语表、平台说明、公司统一标准或 ERP 字段映射时，标记为 `SHARED-DATA-CANDIDATE`，不自动复制；Products Root 已确认且无冲突时，才提出移动到 `00_产品公用数据/` 的计划。

## 调用方式

在新产品目录中创建结构：

```text
Use $hzp-amz-0-1-product-file-structure in CREATE mode for this Product Root.
```

检查目录但不修改：

```text
Use $hzp-amz-0-1-product-file-structure in CHECK mode.
```

扫描并提出迁移方案：

```text
Use $hzp-amz-0-1-product-file-structure in ORGANIZE mode.
```

执行已经确认且无风险的迁移：

```text
Use $hzp-amz-0-1-product-file-structure in MIGRATE mode.
```

完整规则见同目录的 `SKILL.md`。
