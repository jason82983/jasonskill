from pathlib import Path
import sys
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parents[2]))
sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))

from scripts.hzp_amz_report_contract import publish_latest_html
from erp_keyword_management import write_report


def test_publish_keeps_one_root_html_and_archives_sidecar(tmp_path):
    root = tmp_path / "报告"
    root.mkdir()
    old = root / "0-7_旧报告_20260916_100000.html"
    old.write_text("old", encoding="utf-8")
    Path(str(old) + ".meta.json").write_text("{}", encoding="utf-8")
    current = root / "0-7_新报告_20260917_100000.html"
    current.write_text("new", encoding="utf-8")

    result = publish_latest_html(current, root, copy_from_package=False)

    assert result["latest"] == current
    assert sorted(p.name for p in root.glob("*.html")) == [current.name]
    assert (root / "历史HTML" / old.name).read_text(encoding="utf-8") == "old"
    assert (root / "历史HTML" / (old.name + ".meta.json")).is_file()


def test_publish_package_html_copies_to_root(tmp_path):
    root = tmp_path / "报告"
    package = root / "20260917_100000"
    package.mkdir(parents=True)
    source = package / "6-3_广告运行数据报告_20260917_100000.html"
    source.write_text("package", encoding="utf-8")
    Path(str(source) + ".meta.json").write_text("{}", encoding="utf-8")

    result = publish_latest_html(source, root)

    target = root / source.name
    assert result["latest"] == target
    assert target.read_text(encoding="utf-8") == "package"
    assert Path(str(target) + ".meta.json").is_file()
    assert source.is_file()


def test_07_two_runs_leave_one_latest_root_report(tmp_path):
    result = {"Rows": [], "RunId": "run-1", "DryRun": True, "PageSize": 100, "Scope": {}, "Stats": {}}
    write_report(tmp_path, "ALL_PICKKW", result, datetime(2026, 9, 16, 18, 44, 0))
    result["RunId"] = "run-2"
    write_report(tmp_path, "ALL_PICKKW", result, datetime(2026, 9, 16, 18, 45, 0))
    report_root = tmp_path / "01_公共资料" / "0-7_ERP关键词管理"
    assert [p.name for p in report_root.glob("*.html")] == ["0-7_ERP关键词管理报告_最新_2026-09-16_184500.html"]
    # Governed publishing keeps only the current root HTML; the prior run is
    # archived once under 历史HTML.
    assert len(list((report_root / "历史HTML").glob("*.html"))) == 1
