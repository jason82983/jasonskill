from pathlib import Path
from tempfile import TemporaryDirectory

SKILL_ROOT = Path(__file__).resolve().parents[1]


TEMPLATE = """【产品属性信息】

产品编码：
产品名称：

【基础属性】

【尺寸/规格】

【材质】

【数量/套装】

【结构/配件】

【安装/使用】

【兼容性】

【其他已确认属性】

【数据备注】
"""


def ensure_attribute_source(root: Path) -> Path:
    directory = root / "05_分析源数据" / "01_产品数据" / "本产品"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "主图").mkdir(exist_ok=True)
    target = directory / "产品属性信息.txt"
    if not target.exists():
        target.write_text(TEMPLATE, encoding="utf-8")
    return target


def test_missing_file_is_created_and_existing_content_is_preserved():
    with TemporaryDirectory() as value:
        root = Path(value)
        target = ensure_attribute_source(root)
        assert target.read_text(encoding="utf-8") == TEMPLATE
        target.write_text("用户确认材质：树脂\n", encoding="utf-8")
        before = target.read_bytes()
        assert ensure_attribute_source(root).read_bytes() == before


def test_existing_neighbor_files_are_not_changed():
    with TemporaryDirectory() as value:
        root = Path(value)
        target = ensure_attribute_source(root)
        note = target.parent / "产品识别 - 文本文案.txt"
        image = target.parent / "主图" / "source.jpg"
        note.write_text("原有识别文本", encoding="utf-8")
        image.write_bytes(b"raw")
        ensure_attribute_source(root)
        assert note.read_text(encoding="utf-8") == "原有识别文本"
        assert image.read_bytes() == b"raw"


def test_runtime_products_root_and_three_product_areas_are_documented():
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
    readme = (SKILL_ROOT / "README.md").read_text(encoding="utf-8-sig")
    for area in ("03_已上架产品", "02_新品待开发", "00_OtherSPro"):
        assert area in skill and area in readme
    assert "E:\\【所有产品目录专用】\\" in skill
    assert "产品编号" in skill and "Product_Code" in skill
    assert "must not move a product between the three" in skill
