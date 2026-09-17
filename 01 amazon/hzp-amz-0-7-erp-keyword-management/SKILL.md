---
name: hzp-amz-0-7-erp-keyword-management
description: "扫描 ERP PickKw 中缺失的 KeywordCn，生成可追溯的简体中文翻译，并以 Dry Run、并发校验、回读验证和审计报告为默认安全边界。"
---

# HZP Amazon 0-7｜ERP关键词管理

管理 ERP PickKw.KeywordCn 缺失翻译。唯一标识固定为自动编号字段 Id；只允许对当前为空的 KeywordCn 写入中文，不覆盖已有值、不修改其它字段、不判断精准词、不执行 Amazon Ads。

## 输入与范围
- 产品根目录按 0-1 契约从 E:\【所有产品目录专用】\ 定位，解析 Product_Code、ERP ProId 和当前身份。
- 每次运行必须明确数据范围：至少 Product_Code、ERP ProId、筛选条件或批次。缺少范围直接停止。
- 必须复用仓库现有 ERP Provider、认证、分页、限流、重试和日志。当前仓库没有可验证的 PickKw.KeywordCn Writer；真实写入默认 WRITE_BLOCKED，不创建 SQL、不硬编码凭证。

## 固定流程
1. DRY_RUN=true 默认启动；用 keyset/正式分页逐页扫描，禁止全表加载。
2. 根据估算数据量自动选择有上限的 page size；大数据量增大分页，减少无谓调用。
3. 以 TranslationItemId + Keyword 形成结构化翻译请求；一次 Run 内相同规范化 Keyword 只翻译一次。
4. 校验输出：非空、单条简体中文、无解释/JSON片段/编号/多条合并、长度不超过 ERP 限制。
5. Compare-And-Apply 必须同时校验 Id、原始 Keyword、KeywordCn 仍为空；只发送 KeywordCn 字段。
6. 写后立即 read-back，处理并发填充、源词变化、写入失败和 READBACK_MISMATCH。
7. 每次执行（包括 Dry Run）都生成独立 CSV、最新 HTML、历史 HTML、metadata 和审计统计，历史不覆盖。

## 状态
UPDATED_VERIFIED、SKIP_ALREADY_TRANSLATED、SKIP_CONCURRENTLY_FILLED、SOURCE_KEYWORD_EMPTY、SOURCE_KEYWORD_CHANGED、TRANSLATION_VALIDATION_FAILED、ERP_WRITE_FAILED、READBACK_MISMATCH、WRITE_BLOCKED、DRY_RUN_PROPOSED。

## 输出目录
[Product Root]\06_SKILL分析报告\0-7_ERP关键词管理\
- 0-7_ERP关键词管理报告_最新_{YYYY-MM-DD_HHMMSS}.html
- 历史HTML\
- data\0-7_关键词翻译更新结果_{YYYYMMDD_HHMMSS}.csv
- _system\

实现见 references/data-contract.md、references/translation-prompt.md 和 scripts/erp_keyword_management.py。
