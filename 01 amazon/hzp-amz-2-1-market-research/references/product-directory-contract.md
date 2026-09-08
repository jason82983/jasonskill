# HZP Portable Product Project Contract

所有 Amazon Skill 共用这套便携式产品项目契约。产品项目可以复制到任意电脑、盘符或工作目录；Skill 不依赖员工机器上的固定绝对路径。

## 产品项目根目录

产品项目根目录由一个必需的 `PRODUCT.md` 文件标识。Skill 启动时从当前工作目录向上逐级搜索：

1. 找到 `PRODUCT.md` 后，将其所在目录作为 `product_root`；
2. 如果用户明确提供了项目目录，先确认该目录内存在 `PRODUCT.md`，再使用它；
3. 找不到时停止并请用户选择或创建产品项目目录；
4. 不猜测、不扫描无关磁盘、不复用上一次任务的路径。

## PRODUCT.md 最终模板

`PRODUCT.md` 是“这是一个 HZP Product Project”的识别标志。它必须记录当前 Product Code，但不得记录员工电脑的绝对路径：

```text
# HZP AMAZON PRODUCT

Current Product Code: N24
Previous Product Code:
Product Code History:
- N24 | 新品项目阶段 | <日期或说明>

Product Name: <产品名称>
Alternative Names:
- <中文或英文别名，可为空>

Marketplace: Amazon US
Store: <店铺，可为空>

Amazon ASIN:
- <ASIN，可为空>

Benchmark ASIN(s):
- <基准 ASIN，可为空>

Current Stage: 2-1
Status: <ACTIVE / WAITING / HOLD / COMPLETED / CANCELLED>

Owner: <负责人>
Reviewer: <评审人>
Product Expert: QMT

Latest Handoff: ./<当前阶段目录>/<当前 Product Code>_HANDOFF.md
Manual Requirements: ./MANUAL_REQUIREMENTS.md
Decisions: ./DECISIONS.md
```

例如 2-1 当前 HANDOFF 应写为 `Latest Handoff: ./2-1-market-research/2-1-N24_HANDOFF.md`；进入 3-1 后改为 `Latest Handoff: ./3-1-product-development/3-1-N24_HANDOFF.md`。产品编码变化时，文件名和指针使用当前 Product Code。

`Current Product Code` 是产品唯一身份，优先级高于 `Product Name` 和 `Alternative Names`。当前已知的编码示例包括：

- `N24`：新品项目阶段，尚未最终确认生产、上架或正式 Amazon 产品；
- `A7`：已确认归属 A 店并已创建/确认的正式产品。

这只是当前已知含义，不得据此推断未来只有 N 类或 A 类。系统应接受其他未来编码，只要求 `Current Product Code` 非空且在项目内一致。

如果产品从 `N24` 变为 `A7`，将 `Current Product Code` 更新为 `A7`，把 `N24` 保留在 `Previous Product Code` 和 `Product Code History` 中。旧文件不强制重命名；新报告使用当前代码，并通过历史字段追溯旧代码。

旧项目若只有 `Product ID` 字段，可以暂时保留作兼容信息；生成新正式文件前必须补齐 `Current Product Code`，不能用产品名称或 ASIN 代替。

`Current Stage` 与 `Status` 必须分开。`Current Stage` 表示当前所在的 Amazon 环节；`Status` 只使用以下五种生命周期状态：

- `ACTIVE`：正在推进；
- `WAITING`：等待外部资料、确认、报价或样品；
- `HOLD`：暂停；
- `COMPLETED`：产品项目生命周期完成；
- `CANCELLED`：项目取消。

`ACTIVE` 才是默认可推进状态；`WAITING` 或 `HOLD` 需要用户明确要求恢复后再继续。Skill 可以根据执行结果提出状态变化建议，但不得擅自把项目改为 `COMPLETED` 或 `CANCELLED`。`GO / CONDITIONAL GO / NO-GO` 是阶段决策，不是 Product Status。

## 便携式目录结构

```text
<ProductRoot>/
├── PRODUCT.md
├── MANUAL_REQUIREMENTS.md          # 可选，不存在时正常继续
├── DECISIONS.md                    # 可选；重要正式决策
├── 0-source/                       # 用户/员工提供的原始资料和证据
├── 2-1-market-research/            # 2-1 报告与 HANDOFF
└── 3-1-product-development/        # 3-1 开发资料与 HANDOFF
```

未来 `4-production/`、`5-listing/`、`6-growth/`、`7-inventory/` 只在对应阶段实际使用时创建，不提前创建空目录。阶段目录保存对应 Skill 的正式报告、HANDOFF 和其他分析结果。

## MANUAL_REQUIREMENTS.md

`MANUAL_REQUIREMENTS.md` 是可选的人工补充要求、人工设计要求或项目补充要求文件。它可以由 HZP、QMT、产品开发、运营、设计、供应商、工厂、质检、财务、项目负责人或其他参与人员提出。文件不存在时，Skill 不报错、不阻塞流程。

建议使用以下结构；每条要求都要记录 ID、内容、提出人、日期、适用阶段、状态和备注：

```markdown
# MANUAL REQUIREMENTS

## Requirement

ID：MR-001
内容：外观不要做得太医疗化。
提出人：HZP
提出日期：2026-09-08
适用阶段：3-1 Product Development
状态：ACTIVE
备注：

## Requirement

ID：MR-002
内容：大底需要继续降低重量。
提出人：QMT
提出日期：2026-09-08
适用阶段：3-1 Product Development
状态：ACTIVE
备注：
```

`适用阶段` 可以写 `GLOBAL`、单个阶段（`2-1`、`3-1`、`4-1`、`5-1`、`6-1`、`7-1`）或逗号分隔的多个阶段，例如 `3-1, 5-1`。系统不限制未来新增的阶段编号。

状态至少支持：

- `ACTIVE`：当前有效，当前适用 Skill 必须考虑；
- `TO-VERIFY`：需要证据、测试或负责人确认后决定；
- `DONE`：已经完成/落实，仅作历史记录；
- `REJECTED`：明确否决，不作为当前要求；
- `SUPERSEDED`：已被新要求替代，不作为当前要求。

默认读取与当前阶段有关的 `ACTIVE`、`TO-VERIFY` 要求；不得把 `REJECTED` 或 `SUPERSEDED` 当成当前要求。人工要求在 HANDOFF 中使用 `[MANUAL-REQ]` 标签，它不是事实证据，也不自动升级为 `[FACT]`。

如果人工要求与事实、测试、正式决策或上游 HANDOFF 冲突，必须同时显示：

```text
人工要求：[MANUAL-REQ] <要求内容、提出人、日期、适用阶段>
证据/事实：[FACT] / [TO-VERIFY] <支持或反驳它的资料>
冲突：[INFERENCE] <冲突是什么>
建议：[INFERENCE] <保留、修改或验证的建议>
需要谁确认：[TO-VERIFY] <HZP / QMT / 供应商 / 其他负责人>
```

正式确认事实和正式决策优先，但不能静默忽略人工要求，也不能盲目执行人工要求。

## DECISIONS.md

`DECISIONS.md` 是可选的正式决策记录，只记录已经确认且会影响产品方向、阶段、代码、方案、材料、结构、价格策略或项目去留的重要决定。它不是工作日志、聊天记录或普通建议清单。普通建议先留在报告或 `MANUAL_REQUIREMENTS.md`，只有明确确认后才进入这里。

建议格式：

```markdown
# DECISIONS

## D-003

日期：2026-09-08
阶段：3-1
决策：第二版采用方案 B。
决定人：HZP / QMT

原因：<为什么做出该决定>
依据：<相对产品根目录的证据、测试或会议记录路径>
影响：<对需求、样品、成本或下一阶段的影响>

状态：ACTIVE
```

读取决策时保留其日期、阶段、决定人、依据和影响；如果后续正式决策替代旧决定，在新记录中说明替代关系，不删除历史记录。

## 信息边界

产品项目中的五类信息不能互相冒充：

1. `0-source/`：Source Evidence，原始证据；
2. 阶段 HANDOFF：上一阶段的结构化交接结论；
3. `MANUAL_REQUIREMENTS.md`：人工补充要求，使用 `[MANUAL-REQ]`；
4. `DECISIONS.md`：已经确认的重要正式决策，使用 `[DECISION]`；
5. `PRODUCT.md`：当前产品身份、阶段、生命周期 Status 和入口指针。

例如“鞋底再软一点”先属于人工要求；只有 HZP/QMT 明确确认采用某方案，才可作为正式决策写入 `DECISIONS.md`。

## 目录和文件规则

- 读入资料：`product_root/0-source/`，必要时递归读取子目录；不得要求固定的 ASIN 子目录名。
- 2-1 输出：`product_root/2-1-market-research/`。
- 3-1 输出：`product_root/3-1-product-development/`。
- 文件名中的 `[ProductCode]` 必须来自 `PRODUCT.md` 的 `Current Product Code`；ASIN 和产品名称是辅助字段。
- 报告、HANDOFF、JSON 和来源清单中的路径一律使用相对于 `product_root` 的路径或裸文件名，例如 `0-source/keepa.xlsx`、`2-1-market-research/2-1-N24_HANDOFF.md`。
- HTML 可点击链接根据 HTML 文件位置计算相对 URL；不得使用员工盘符、UNC、`/mnt/...` 或 `file:///...`。
- 原始资料保持只读；正式输出只写入当前阶段目录，不写回 `0-source/`。
- 阶段目录缺失时，只创建当前 Skill 需要的目录，不创建未来阶段的空目录。
- `0-source/` 中的 Source Evidence 只读；新版资料必须新增文件，不能覆盖或修改旧原始文件。

## 启动时统一读取顺序

每个 Skill 都按以下顺序恢复上下文：

1. 找到当前 Product Root；
2. 读取 `PRODUCT.md`；
3. 确认 `Current Product Code`，并以它作为唯一产品身份；
4. 读取上游最新 HANDOFF；
5. 检查 `MANUAL_REQUIREMENTS.md` 是否存在，存在则读取当前阶段的 `ACTIVE` / `TO-VERIFY` 要求；
6. 检查 `DECISIONS.md` 是否存在，存在则读取与当前阶段相关的重要正式决策；
7. 执行当前 Skill 的 Entry Gate；
8. 读取当前阶段新增资料；
9. 必要时回查 `0-source/` 原始证据；
10. 执行当前 Skill；
11. 生成当前阶段正式报告；
12. 生成新的 HANDOFF；
13. 执行 Exit Gate；
14. 将仍影响未来阶段的人工要求写入 HANDOFF 的 `Active Cross-Stage Requirements`；
15. 必要时更新 `PRODUCT.md` 的当前代码、历史代码、阶段、Status 和 Latest Handoff。

## 推荐目录发现代码

```python
from pathlib import Path

def find_product_root(start=None):
    here = (Path(start) if start else Path.cwd()).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "PRODUCT.md").is_file():
            return candidate
    raise FileNotFoundError("未找到 PRODUCT.md，请提供或创建产品项目目录")

product_root = find_product_root()
product_meta = product_root / "PRODUCT.md"
source_dir = product_root / "0-source"
manual_requirements = product_root / "MANUAL_REQUIREMENTS.md"
stage_dir = product_root / "2-1-market-research"

if not source_dir.is_dir():
    raise FileNotFoundError("产品项目缺少 0-source/，无法读取原始资料")
stage_dir.mkdir(exist_ok=True)
```

读取 `PRODUCT.md` 后，必须确认 `Current Product Code` 存在且新文件名、HANDOFF 元数据与其一致。若项目目录下出现多个可能的产品项目，停止并请用户选择；不得凭产品名称、ASIN 或旧路径猜测。

## 跨员工和代码迁移

员工只需共享整个产品项目文件夹或其 Git 工作树。下一台电脑将当前工作目录切换到项目内任意子目录，Skill 即可通过 `PRODUCT.md` 找到根目录。下游 Skill 先读取上游阶段 HANDOFF，再按需核对报告和 `0-source/` 原始文件；所有相对路径在换电脑、换盘符后仍然有效。

当 Product Code 从 N24 变为 A7：

1. 在 `PRODUCT.md` 写入 `Current Product Code: A7`；
2. 把 `N24` 保留到 `Previous Product Code` 和 `Product Code History`；
3. 新阶段正式文件使用 `A7`；
4. 旧的 `2-1-N24_...`、`3-1-N24_...` 历史文件保留；
5. 在新 HANDOFF 的来源和变更说明中写出代码迁移关系，不静默断链。

任务状态可以在当前对话中显示本机解析出的路径用于诊断，但不得把该绝对路径写入可移植报告、HANDOFF 或 `PRODUCT.md`。正式文件中记录相对于 `product_root` 的路径。
