from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from update_report_index import parse_report, rebuild


def test_index_keeps_current_and_history_but_skips_run_package(tmp_path):
    root = tmp_path / "product"
    report_root = root / "06_SKILL分析报告"
    skill = report_root / "6-3_广告运行事实数据"
    history = skill / "历史HTML"
    package = skill / "20260917_100000"
    history.mkdir(parents=True)
    package.mkdir(parents=True)
    current = skill / "6-3_B2_广告运行事实数据报告_20260917_100000.html"
    old = history / "6-3_B2_广告运行事实数据报告_20260916_100000.html"
    duplicate = package / current.name
    current.write_text("<h1>current</h1>", encoding="utf-8")
    old.write_text("<h1>old</h1>", encoding="utf-8")
    duplicate.write_text("<h1>package</h1>", encoding="utf-8")
    (root / "01_产品档案.md").write_text("产品编号：B2\n产品名称：测试\n", encoding="utf-8")

    assert parse_report(current, report_root)["history"] is False
    assert parse_report(old, report_root)["history"] is True
    assert parse_report(duplicate, report_root) is None
    index = rebuild(root)
    html = index.read_text(encoding="utf-8")
    assert current.name in html
    assert old.name in html
    assert f"/{package.name}/{duplicate.name}" not in html
