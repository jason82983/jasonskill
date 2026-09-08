# Amazon 产品目录契约

所有 Amazon Skill 共用一套运行时目录参数，不把某个盘符或旧目录写死在 Skill 规则中。

## 每次任务的两个路径参数

```text
产品根目录：<绝对路径>
产品相对目录：<相对于产品根目录的目录>
```

当前工作区示例：

```text
产品根目录：E:\【所有产品目录专用】
产品相对目录：N24 置物架
```

实际产品目录由 `产品根目录 / 产品相对目录` 组成。根目录未来变化时，只替换任务参数；Skill 逻辑、产品相对目录和文件识别规则不变。

## 产品目录结构

```text
<产品根目录>/
└── <产品相对目录>/
    ├── 01 产品分析所需数据/
    │   ├── <ASIN>/
    │   └── ...
    └── 02 所有AI分析结果/
```

- `01 产品分析所需数据`：用户和员工采集的原始资料、导出文件、图片、供应商数据、样品记录等。Skill 只读，除非用户明确要求整理或标注。
- `02 所有AI分析结果`：所有 Skill 生成的 HTML、Markdown、JSON、表格、图表和交接文件。不得把 AI 结果写回 `01`。
- ASIN 子目录是可选的；Skill 要递归读取 `01`，不能只依赖固定的 ASIN 子目录名。
- 临时文件、缓存和中间截图不应混入正式结果目录；需要保留的中间证据要有清晰文件名和来源说明。

## 代码校验规则

1. 先把根目录解析为绝对路径并确认它是目录。
2. 规范化相对目录；拒绝盘符、绝对路径和包含 `..` 的路径，防止越出根目录。
3. 计算并解析 `product_dir = root / relative_dir`，确认它存在且仍位于根目录内。
4. 若提供产品编码，用大小写不敏感的精确前缀边界校验目录名，例如 `N24` 只能匹配 `N24`、`N24 `、`N24-`、`N24_`，不能匹配 `N240`。
5. 若未提供相对目录，用产品编码在根目录内递归搜索；找到 0 个时停止，找到多个时列出候选并让用户选择，不能复用上一次产品目录。
6. 检查 `01 产品分析所需数据`。缺失时，对需要原始资料的完整任务停止并说明；不要自动把旧目录当作替代。
7. 检查 `02 所有AI分析结果`。缺失时可以创建；创建后记录在任务状态中。
8. 所有来源在报告中优先保存为相对 `product_dir` 的路径；报告内链接相对于报告所在 HTML，不能写死 `file:///`、盘符或旧根目录。

## 推荐校验代码

```python
from pathlib import Path

root = Path(root_arg).expanduser().resolve()
relative = Path(relative_arg)
if not root.is_dir() or relative.is_absolute() or ".." in relative.parts:
    raise ValueError("产品根目录或产品相对目录无效")
product_dir = (root / relative).resolve()
if root not in product_dir.parents and product_dir != root:
    raise ValueError("产品目录越出根目录")
if not product_dir.is_dir():
    raise FileNotFoundError(product_dir)
input_dir = product_dir / "01 产品分析所需数据"
output_dir = product_dir / "02 所有AI分析结果"
if not input_dir.is_dir():
    raise FileNotFoundError(input_dir)
output_dir.mkdir(exist_ok=True)
```

## 任务状态必须记录

每次任务开始时，报告或日志至少写出：

- 收到的产品根目录；
- 产品相对目录；
- 代码解析出的产品目录；
- 产品编码和 ASIN（如有）；
- `01 产品分析所需数据` 和 `02 所有AI分析结果` 的绝对路径；
- 实际读取的文件和实际生成的文件，路径优先用相对产品目录的形式。
