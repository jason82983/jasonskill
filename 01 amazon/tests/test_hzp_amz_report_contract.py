from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.hzp_amz_report_contract import (  # noqa: E402
    build_report_filename, resolve_skill_report_dir, validate_hzp_amz_report_batch,
    validate_hzp_amz_report_path, report_data_dir, report_history_html_dir,
    report_system_dir, display_timestamp, build_latest_html_filename,
    publish_latest_html,
)

SKILLS = ROOT
STAMP = "20260916_221500"


def skill(number):
    return next(path for path in SKILLS.glob("hzp-amz-*") if path.name.startswith(f"hzp-amz-{number}-"))


def test_exact_filenames_and_dynamic_benchmark_code():
    assert build_report_filename(skill("6-0-3"), "精准泛词汇总", STAMP, "csv") == f"6-0-3_精准泛词汇总_{STAMP}.csv"
    assert build_report_filename(skill("6-0-5"), "新品广告作战规划报告", STAMP, "html") == f"6-0-5_新品广告作战规划报告_{STAMP}.html"
    assert build_report_filename(skill("6-0-2"), "B1_高度精准词", STAMP, "csv") == f"6-0-2_B1_高度精准词_{STAMP}.csv"
    assert build_report_filename(skill("6-0-6"), "对标意图市场占领分析报告", STAMP, "html") == f"6-0-6_对标意图市场占领分析报告_{STAMP}.html"


def test_fixed_skill_directory_and_forbidden_timestamp_folder(tmp_path):
    s = skill("6-0-3")
    directory = resolve_skill_report_dir(tmp_path, s)
    assert directory == tmp_path.resolve() / "06_SKILL分析报告" / "6-0-3_精准泛词提取"
    valid = directory / f"6-0-3_精准泛词汇总_{STAMP}.csv"
    assert validate_hzp_amz_report_path(valid, tmp_path, s, timestamp=STAMP) is None
    nested = directory / STAMP / valid.name
    assert validate_hzp_amz_report_path(nested, tmp_path, s, timestamp=STAMP) == "HZP_ONE_TIME_SKILL_RUN_FOLDER_FORBIDDEN"


def test_prefix_root_timestamp_identity_and_batch_validation(tmp_path):
    s = skill("6-0-5")
    directory = resolve_skill_report_dir(tmp_path, s)
    valid = directory / f"6-0-5_新品广告作战规划报告_{STAMP}.html"
    assert validate_hzp_amz_report_path(valid, tmp_path, s, timestamp=STAMP, report_identity="新品广告作战规划报告") is None
    assert validate_hzp_amz_report_path(tmp_path / "06_SKILL分析报告" / valid.name, tmp_path, s, timestamp=STAMP) == "HZP_REPORT_WRITTEN_TO_ROOT"
    assert validate_hzp_amz_report_path(directory / f"新品广告作战规划报告_{STAMP}.html", tmp_path, s, timestamp=STAMP) == "HZP_REPORT_PREFIX_MISSING"
    assert validate_hzp_amz_report_path(directory / f"6-0-5_新品广告作战规划报告_bad.html", tmp_path, s, timestamp=STAMP) == "HZP_REPORT_TIMESTAMP_INVALID"
    mismatch = directory / "6-0-5_新品意图市场作战表_20260916_221501.csv"
    assert validate_hzp_amz_report_batch([valid, mismatch], tmp_path, s, timestamp=STAMP) == "HZP_REPORT_TIMESTAMP_INVALID"


def test_continuous_skill_run_folder_is_allowed(tmp_path):
    s = skill("6-3")
    directory = resolve_skill_report_dir(tmp_path, s)
    report = directory / STAMP / f"6-3_广告优化决策报告_{STAMP}.html"
    assert validate_hzp_amz_report_path(report, tmp_path, s, timestamp=STAMP, allow_run_folder=True) is None


def test_603_writer_paths_are_flat_and_skill_prefixed(tmp_path):
    import importlib.util
    module_path = skill("6-0-3") / "scripts" / "broad_seed_cluster.py"
    spec = importlib.util.spec_from_file_location("layout_603", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    paths = module.output_paths(tmp_path, "B2", STAMP)
    assert {path.name for path in paths.values()} == {
        f"6-0-3_词对应的精准泛词_{STAMP}.csv",
        f"6-0-3_精准泛词汇总_{STAMP}.csv",
    }
    assert len({path.parent for path in paths.values()}) == 1
    assert paths["summary"].parent == tmp_path.resolve() / "06_SKILL分析报告" / "6-0-3_精准泛词提取"
    assert module.create_run_folder(tmp_path, STAMP) == paths["summary"].parent


def test_layered_report_layout_and_latest_history_rotation(tmp_path):
    s = skill("5-0-1")
    root = resolve_skill_report_dir(tmp_path, s)
    assert report_data_dir(tmp_path, s) == root / "data"
    assert report_history_html_dir(tmp_path, s) == root / "历史HTML"
    assert report_system_dir(tmp_path, s, "metadata") == root / "_system" / "metadata"
    assert display_timestamp(STAMP) == "2026-09-16_221500"
    assert build_latest_html_filename(s, "产品线上信息获取", STAMP).endswith("_最新_2026-09-16_221500.html")

    first = root / ".first.html.tmp"
    first.write_text("first", encoding="utf-8")
    published = publish_latest_html(first, tmp_path, s, "产品线上信息获取", STAMP)
    assert published.is_file() and "_最新_" in published.name

    second_stamp = "20260917_091111"
    second = root / ".second.html.tmp"
    second.write_text("second", encoding="utf-8")
    published2 = publish_latest_html(second, tmp_path, s, "产品线上信息获取", second_stamp)
    assert published2.is_file() and published2.read_text(encoding="utf-8") == "second"
    history = list((root / "历史HTML").glob("*.html"))
    assert len(history) == 1 and "_最新_" not in history[0].name
    assert history[0].read_text(encoding="utf-8") == "first"


def test_latest_html_duplicate_and_history_collision_fail_closed(tmp_path):
    s = skill("5-0-1")
    root = resolve_skill_report_dir(tmp_path, s)
    (root / build_latest_html_filename(s, "产品线上信息获取", STAMP)).write_text("a", encoding="utf-8")
    (root / build_latest_html_filename(s, "产品线上信息获取", "20260917_000000")).write_text("b", encoding="utf-8")
    candidate = root / ".candidate.html.tmp"
    candidate.write_text("c", encoding="utf-8")
    import pytest
    with pytest.raises(ValueError, match="HZP_HTML_LATEST_DUPLICATE"):
        publish_latest_html(candidate, tmp_path, s, "产品线上信息获取", "20260917_010000")
