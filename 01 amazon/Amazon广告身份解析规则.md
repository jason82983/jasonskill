# Amazon 广告身份与广告组合解析规则

这是阶段 6 共用的最小接口。它补充 `Amazon产品身份解析规则.md`，不替代产品、店铺、ASIN、SKU 的主身份解析。

## 唯一身份链

`Product_NewCode → Product_Code → SellerSpace Store → Product_Code_Prefix → Marketplace → Own ASIN/Child ASIN → SKU → Portfolio Name → Portfolio ID → Var_Code → Campaign`

1. 从只读映射表按 `Product_Code` 或 `Product_NewCode` 精确匹配唯一 `Status=ACTIVE` 行；`Product_Code` 是正式经营代码，`Product_NewCode` 只保留研究/新品来源关系，不能互换或由 AI 生成。
2. `Product_Code_Prefix` 运行时从“店铺产品代码前缀”表按 Store 读取，只做校验，不能反推或生成正式 Product_Code。
2. `Portfolio Name` 读取映射表实际列 `广告组合`；该列为空、重复 ACTIVE 或与产品档案冲突时停止写入。
3. 在已经验证的 Store + Marketplace 范围内，通过 `discover_capabilities`、`discover_fields` 和只读 Portfolio 查询解析 `Portfolio ID`。不能按 ASIN、文件名或历史报告猜 Portfolio ID。
4. Portfolio ID 只作为当前运行的 SellerSpace 实时身份结果，不回写映射表，不写入 Skill、模板或固定测试数据。

## 统一返回对象

共享解析器/实现必须返回以下字段并保留来源与读取时间：

```text
product_new_code, product_code/formal_product_code, product_name,
seller_space_store, product_code_prefix, marketplace, own_asin,
parent_asin, child_asin, sku, portfolio_name, portfolio_id,
var_code/variants, mapping_status, prefix_status, portfolio_status,
variant_status, identity_status, conflicts
```

共享实现位于 `scripts/resolve_amazon_ad_identity.py`：`resolve_advertising_identity()` 解析身份，`format_campaign_name()` / `format_ad_group_name()` 生成名称，`parse_campaign_name()` / `validate_campaign_name()` / `classify_campaign_name()` 供 6-2、6-3 消费，`next_campaign_sequence()` 在审批前做重名检查。需要跨阶段时，6-1、6-2、6-3 传递同一返回对象，不能按 ASIN、文件名或中文名重新猜身份。

## 变体与广告对象边界

- `Own ASIN`、`Benchmark ASIN`、`Product Target ASIN` 永远分开；Benchmark/Product Target 不能作为 Advertised Product 或 SellerSpace 自有查询身份。
- “产品对应变体”表的 `Var_Code` 不能自动改名。只有可靠的 `Var_Code → Child ASIN → SKU` 关系才能生成变体广告；关系缺失时标记 `【变体广告身份映射不完整】`、停止写入。
- 6-1 有变体时使用 `[Product_Code].[Var_Code].[AdType]-[Role]-[Target/Match]-[Sequence]`；无变体时保留 `[Product_Code].[AdType]-[Role]-[Target/Match]-[Sequence]`。
- 6-2 扩词/竞品 Product Target 和 6-3 监控都沿 `Product_NewCode → Product_Code → Portfolio → Var_Code → Campaign` 层级继承，不能跨变体或跨组合静默聚合。

## 统一冲突状态与写入闸门

使用以下状态记录未决问题：`[Amazon经营身份映射结构不完整]`、`[正式Product_Code缺失]`、`[店铺产品代码前缀冲突]`、`[Portfolio映射缺失]`、`[Portfolio ID验证失败]`、`[存在多个有效产品身份映射｜需要人工确认]`、`[产品身份映射异常]`、`[产品身份资料冲突]`、`[变体广告身份映射不完整]`、`[Var_Code无法唯一解析]`、`[Var_Code与Child ASIN冲突]`、`[Advertised Child ASIN与批准方案不一致]`、`[SellerSpace实时身份验证未完成]`。关键身份未解决时只能只读分析，禁止任何真实广告写入。

`portfolio_status` 允许：

- `MAPPING_PORTFOLIO_MISSING`
- `MCP_PORTFOLIO_PENDING`
- `PORTFOLIO_VERIFIED`
- `PORTFOLIO_ID_UNRESOLVED`
- `PORTFOLIO_NAME_AMBIGUOUS`
- `PORTFOLIO_SCOPE_CONFLICT`

只有 `PORTFOLIO_VERIFIED` 才能把新建或扩展广告绑定到该 Portfolio。读取或诊断可以在状态不足时降级，但必须显示状态；任何写入前只要 Portfolio 缺失、未验证、歧义或不匹配，就输出 `【广告组合身份未验证/冲突｜禁止写入】`。

## 继承与边界

- 6-1 新 Campaign、Ad Group、Advertised Product、Keyword、Target 默认继承当前已验证 Portfolio；不能无理由放入“无广告组合”或另一个组合。
- 6-2 的扩词、竞品 Product Target 和其他扩展动作继承 6-1 的 Portfolio；实际 Campaign Portfolio 不匹配时允许只读诊断，但禁止写入。
- 6-3 可以按 Portfolio 聚合广告指标，但必须把 Portfolio Ad Sales 与 Product Total Sales 分开；Portfolio 身份异常路由回 6-2/6-1。
- 旧 Campaign 不因新规则自动迁移、改组合或重建。Legacy Campaign 与当前 Portfolio 重叠只记录风险。
- `Portfolio ID` 缺失或 SellerSpace 不支持 Portfolio 字段时，安全降级为“建议/只读”，不得假装已绑定。

## Approved 与 Prepared/Read-Back

6-1 的审批清单和 SellerSpace Prepared Change Plan 必须做 Portfolio Name、Portfolio ID、Store、Marketplace、Own ASIN、SKU 的字段级差异比对。任一重大差异都停止执行并要求重新确认。创建成功后用同一字段结构 Read-Back，状态只能为匹配、非关键差异、无法验证或冲突；失败时保留正式报告和审计证据，不自行补救或修改旧广告。

### 对用户显示的统一状态

机器状态至少包括：`MAPPING_PORTFOLIO_MISSING`、`MCP_PORTFOLIO_PENDING`、`PORTFOLIO_VERIFIED`、`PORTFOLIO_ID_UNRESOLVED`、`PORTFOLIO_NAME_AMBIGUOUS`、`PORTFOLIO_SCOPE_CONFLICT`。对用户显示分别使用：`[广告组合字段缺失]`、`[广告组合映射存在｜SellerSpace实时验证未完成]`、`[广告组合身份验证通过]`、`[广告组合身份无法唯一确认]`、`[广告组合身份无法唯一确认]`、`[广告组合身份映射异常]`。映射表指定 Portfolio 但 SellerSpace 找不到时显示 `[广告组合不存在]`；同一 Product Code 存在多个不同 ACTIVE Portfolio 且无法唯一解析时显示 `[存在多个有效广告组合映射｜需要人工确认]`；Mapping、MCP 和 Campaign 实际归属冲突时显示 `[广告组合数据源冲突]`。上述异常在任何写入前都等价于禁止写入。
