# Amazon 产品身份解析规则

这是 HZP Amazon Skills 共用的产品身份接口。需要连接 Amazon、SellerSpace 或其他店铺真实数据的 Skill，必须先完成身份解析，再读取业务数据。各 Skill 不应自行根据 Product Code 猜测店铺、ASIN 或 SKU。

## 权威映射表

公共人工维护文件（只读）位于 Products Root 的：

`00_公共资料/01_Amazon平台资料/Amazon产品店铺映射表.xlsx`

该文件是 **Amazon 产品与 SellerSpace 店铺身份映射主表**。实际工作表为 `产品店铺映射`、`填写说明`、`产品对应变体`、`店铺产品代码前缀`；主表包含以下字段：

`Product_Code`、`Product_NewCode`、`Product_Name`、`广告组合`（Portfolio Name）、`SellerSpace_Store`、`Marketplace`、`ASIN`、`SKU`、`Status`、`Notes`。变体表提供 `Product_Code`、`Var_Code`、`Var_Name`；前缀表提供 `SellerSpace_Store`、`Product_Code_Prefix`。

`广告组合` 是人工维护的 Portfolio Name；映射表不保存 Portfolio ID。Portfolio ID 必须在当前 SellerSpace 店铺和 Marketplace 下通过只读能力解析，不能在 Skill、模板、测试或报告模板中写死真实 ID。

映射表的行、字段和状态由人工维护。Skill 可以读取和报告问题，但不得自动修改、删除或覆盖其中的用户数据，也不得把 API Key、密码或其他凭证写入该文件或 Skill。

## 解析顺序

1. 接收本次运行已经确定的 Product Code，并锁定同一次运行的 Products Root、Product Root 和 Product Code。
2. 读取映射表，按 `Product_Code` 或 `Product_NewCode` 精确匹配；前者是正式经营代码，后者是研究/新品代码，二者关系只从主表读取，文件名只是线索。
3. 只把 `Status=ACTIVE` 的记录作为正式运营候选。形成唯一的 `SellerSpace_Store + Marketplace + ASIN + SKU + Portfolio Name` 组合后，才可以进入 SellerSpace 验证。
4. 使用 SellerSpace MCP 只读查询验证该组合在指定店铺和站点确实存在，并在同一店铺/站点解析 `Portfolio Name → Portfolio ID`。映射表是身份声明，SellerSpace 是二次验证；二者都通过后才能查询广告、订单、库存、商品、店铺表现或历史指标。
5. 每项身份事实保留来源、读取时间和状态；不要把映射表的声明写成已由 SellerSpace 验证的事实。

### Advertising Identity 与 Portfolio 解析

阶段 6 的统一广告身份为：

`Product_NewCode → Product_Code → SellerSpace Store → Product_Code_Prefix → Marketplace → Own ASIN/Child ASIN → SKU → Portfolio Name → Portfolio ID → Var_Code → Campaign`

- `Own ASIN` 只能来自唯一 ACTIVE 映射，并用于自有商品、广告、订单和库存查询；Benchmark ASIN、Product Target ASIN 不得替代它。
- `Product_Code_Prefix` 只按 Store 运行时读取并校验，不能从前缀生成 Product_Code；N+数字代码是合法研究代码，不代表未创建。
- `Var_Code` 只能来自“产品对应变体”表；没有可靠 `Var_Code→Child ASIN→SKU` 关系时标记 `【变体广告身份映射不完整】`，禁止写入。
- `Portfolio Name` 只能来自映射表的 `广告组合` 列；缺失、空值或同一 Product Code 多个 ACTIVE 记录冲突时，禁止广告写入。
- `Portfolio ID` 只能由 SellerSpace 只读发现/查询在已验证 Store + Marketplace 范围内解析。解析不到、同名多 ID、跨店铺或跨站点命中时，状态为 `【广告组合身份未验证】` 或 `【广告组合身份冲突】`，禁止写入。
- 共享解析器只负责读取映射、规范化字段、接收只读 Portfolio 列表并返回状态；不创建、修改、删除广告组合，不调用写接口。
- 6-1、6-2、6-3 不得各自实现另一套身份解析；需要时引用本节和共享解析器/测试。

标准状态至少包括：`MAPPING_PORTFOLIO_MISSING`、`MCP_PORTFOLIO_PENDING`、`PORTFOLIO_VERIFIED`、`PORTFOLIO_ID_UNRESOLVED`、`PORTFOLIO_NAME_AMBIGUOUS`、`PORTFOLIO_SCOPE_CONFLICT`。

Product Code 只能来自用户本次输入或当前 Product Root 的 `01_产品档案.md`。禁止根据 ASIN、SKU、文件名、中文名称、Niche 或 SellerSpace 返回结果反推或替换 Product Code。

## 状态和异常

| 情况 | 必须输出 | 处理 |
|---|---|---|
| 找不到 Product Code | `【产品身份映射缺失】` | 不猜测店铺、站点、ASIN 或 SKU；提示补充主表 |
| 唯一 ACTIVE 且 MCP 完全匹配 | `【产品身份验证通过】` | 允许继续读取真实店铺数据 |
| 多个 ACTIVE，无法由已确认的站点/ASIN/SKU唯一确定 | `【存在多个有效产品身份映射｜需要人工确认】` | 停止真实店铺数据查询，不静默选择 |
| 映射组合与 SellerSpace 不匹配 | `【产品身份映射异常】` | 记录主表值、实际返回、冲突字段和核查建议；不得使用错误身份继续 |
| ASIN 存在但 SKU 不一致 | `【产品身份映射部分冲突】` | 不自动改主表；按冲突状态停止或降级 |
| 只有 INACTIVE 记录 | `【产品身份映射为 INACTIVE｜需要人工确认】` | 默认不作为当前阶段6正式运营对象 |
| TEST 记录 | `【测试映射】` | 仅在用户明确要求测试时使用，并与 ACTIVE 数据分开 |
| `01_产品档案.md` 中当前产品身份的站点、ASIN、SKU 或 Store 与主表冲突 | `【产品身份资料冲突】` | 不覆盖任一文件，要求人工核查 |

唯一匹配不是只看 Product Code：阶段6真实查询前必须锁定 Store、Marketplace、ASIN、SKU 四项。字段缺失、空值、重复或组合无法唯一确认时，不得假装身份已确认。

`01_产品档案.md` 的“市场研究对象/对标产品”ASIN 是研究对象记录，不自动等同于当前店铺商品身份；只有档案明确把某个 ASIN、SKU、Store 或站点写作当前产品身份时，才参与上述冲突判断。

## SellerSpace 不可用时

如果映射表可读但 SellerSpace MCP 不可用，Skill 可以使用映射表、本地 Product Root 原始资料、H10/Cerebro 和其他可靠输入进行受限或降级分析，但必须标记 `【SellerSpace实时身份验证未完成】`，不得把映射声明当作实时店铺验证，也不得编造广告、订单、库存或商品字段。

## 数据保护和下游复用

映射表只提供身份接口，不负责广告或产品决策。发现疑似错误时只输出 `【建议更新映射表】`，列出当前值、发现值、证据和建议修改内容，由人工决定是否更新。

6-1、6-2、6-3 应引用本规则而不是复制三套解析逻辑。下游 Skill 必须继承已经锁定的 Product Code、Products Root 和 Product Root，不重新扫描其他产品目录或根据报告文件名重新猜身份。
