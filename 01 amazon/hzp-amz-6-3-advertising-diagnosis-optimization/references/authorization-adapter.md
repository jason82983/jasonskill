# 6-3 广告自动化授权适配器

本文件定义如何把映射表授权接入现有 Scope Resolver、Campaign Parser 和 Identity Resolver。它不改变广告诊断算法，也不替代 SellerSpace Provider。

## 解析步骤

1. 打开 Amazon产品店铺映射表.xlsx，枚举实际 Sheet。
2. 选择实际包含 Product_Code、Second_Code、Status 的授权 Sheet；不根据截图猜名称，也不新增授权字段。
3. 对三列做 trim/case-normalize；无效行标记 AUTO_AD_MAPPING_INVALID_ROW。
4. 以 (Product_Code, Second_Code) 为键：完全相同的 ACTIVE 行去重；ACTIVE 与非 ACTIVE 冲突标记 AUTO_AUTH_MAPPING_CONFLICT，整个键不得写入。
5. Second_Code 是 HZP 内部第二层广告管理代码，不是 Amazon ASIN、SKU 或强制的 Var_Code；一个 Second_Code 可对应多个 SKU/ASIN。
6. 用共享 Campaign Parser 按英文句点分段解析 Product_Code、Second_Code 和剩余 Campaign_Structure；授权只做前两段 Exact Match，禁止 startswith/contains/substring。
7. Identity Resolver 和 Provider 对象中的 Campaign ID、Store、Marketplace、Portfolio、Own ASIN、Advertised Product、SKU(s) 仍可用于数据归因和安全护栏，但不参与第一层授权 Scope 判断。
8. 只有 Scope、Product_Code + Second_Code + Status=ACTIVE、结构化 Exact Match 和所有既有护栏通过，才允许进入 prepare/diff/apply/read-back。

## 伪代码

sheet = find_sheet_with_columns(workbook, {Product_Code, Second_Code, Status})
rows = normalize_and_validate(sheet)
authorization = dedupe_exact_rows(rows)

for campaign in active_campaigns:
    parsed = parse_campaign_name(campaign.name)  # Product_Code, Second_Code, Structure
    auth = authorization[(parsed.product_code, parsed.second_code)]
    if not auth or auth.status != ACTIVE:
        campaign.state = AUTO_EXECUTION_NOT_AUTHORIZED
        continue
    if parsed.unresolved:
        campaign.state = CAMPAIGN_AUTH_IDENTITY_UNRESOLVED
        continue
    if not all_existing_guardrails_pass(campaign):
        campaign.state = WRITE_BLOCKED
        continue
    campaign.state = AUTHORIZED

ASIN-first 经营分析、同 ASIN 多 SKU、SKU Drill-down 和 Advertised Product 归因继续使用 Provider 实际数据；它们不增加自动授权复杂度。开自动的产品有.txt 不参与 6-3 最高授权判断，只保留给其它流程的兼容读取；不与 Excel 形成双重授权。


授权层说明：这是 HZP Business Authorization Layer；SellerSpace/优麦云仍是当前 Provider。授权表不与 Excel 形成双重授权，开自动的产品有.txt 不参与 6-3 最高授权判断。产品日报显示 Authorization State。
