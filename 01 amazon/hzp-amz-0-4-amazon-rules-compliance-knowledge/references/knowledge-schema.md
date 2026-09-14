# 0-4 知识元数据接口

每个专项知识条目建议保存一个同名 `.json` 元数据文件：

| 字段 | 必填 | 说明 |
|---|---|---|
| knowledge_id | 是 | 稳定唯一 ID，用于去重和更新 |
| title | 是 | 人类可读主题 |
| marketplace | 是 | US 或适用站点 |
| category | 是 | 十个标准分类之一 |
| keywords | 否 | 检索关键词数组 |
| status | 是 | 知识状态标签 |
| change_risk | 是 | HIGH/MEDIUM/LOW |
| last_verified_at | 是 | 最后核验日期 |
| version | 是 | V1/V2…，独立于产品 Skill 版本 |
| source_types | 是 | 官方、法规、物流、公司经验等 |
| affected_skills | 否 | 受影响 Skill 编号 |
| affected_product_types | 否 | 受影响产品类型 |
| report_path | 是 | 相对知识根目录的 HTML 路径 |
| superseded_by | 否 | 新版 knowledge_id |

HTML 报告可在 `<head>` 中写 `knowledge-id`、`knowledge-title`、`marketplace`、`category`、`status`、`change-risk`、`last-verified-at` 和 `version` meta 标签。`scripts/build_index.py` 优先使用同名 JSON，缺失时读取 HTML meta。
