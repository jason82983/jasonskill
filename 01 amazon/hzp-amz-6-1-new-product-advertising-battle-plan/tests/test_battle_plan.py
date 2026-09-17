from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))
import battle_plan as bp
from report_renderer import _campaign_groups, read_embedded_snapshot


PRODUCT = "TST01"
TIMESTAMP = "20260916_101010"


def source_rows(profile: str = "MULTI_BENCHMARK"):
    summary = [
        {"精准泛词": "sister gifts", "中文": "姐妹礼物", "层级": "L1", "父精准泛词": "", "直接搜索量": "2000", "汇总搜索量": "2500", "平均竞品数": "100", "意图机会比": "25.0000", "直接对应词数": "3"},
        {"精准泛词": "sister birthday gifts", "中文": "姐妹生日礼物", "层级": "L2", "父精准泛词": "sister gifts", "直接搜索量": "500", "汇总搜索量": "500", "平均竞品数": "70", "意图机会比": "7.1429", "直接对应词数": "2"},
        {"精准泛词": "mother gifts", "中文": "母亲礼物", "层级": "L1", "父精准泛词": "", "直接搜索量": "300", "汇总搜索量": "300", "平均竞品数": "50", "意图机会比": "6.0000", "直接对应词数": "1"},
        {"精准泛词": "wife gifts", "中文": "妻子礼物", "层级": "L1", "父精准泛词": "", "直接搜索量": "180", "汇总搜索量": "180", "平均竞品数": "45", "意图机会比": "4.0000", "直接对应词数": "1"},
    ]
    intent_for_id = {
        "k1": ("sister gifts", "sister gift ideas", "200", "4", "4", "8", "10"),
        "k2": ("sister gifts", "gifts for sister", "100", "3", "1", "9", "11"),
        "k3": ("sister birthday gifts", "birthday gift for sister", "90", "2", "2", "7", "9"),
        "k4": ("sister birthday gifts", "sister birthday present", "80", "2", "2", "8", "10"),
        "k5": ("mother gifts", "present for mother", "150", "3", "1", "12", "14"),
        "k6": ("wife gifts", "gift for wife", "100", "2", "1", "15", "16"),
        "k7": ("sister gifts", "holiday gifts for sister", "110", "3", "1", "9", "10"),
    }
    mapping = []
    for record_id, (intent, keyword, volume, competitors, coverage, best_rank, median_rank) in intent_for_id.items():
        row = {"Id": record_id, "词": keyword, "中文": "中文 " + keyword, "市场容量": volume, "竞争产品数": competitors, "供需比": "30.0000", "精准泛词": intent, "精准泛词中文": intent + "中文"}
        if profile == "MULTI_BENCHMARK":
            row.update({"对标覆盖数": coverage, "最佳自然排名": best_rank, "自然排名中位数": median_rank})
        else:
            row["自然排名"] = best_rank
        mapping.append(row)
    return summary, mapping


def decisions():
    intent_decisions = {
        "sister gifts": {"task": "核心", "priority": "P1", "direction": "建立姐妹礼物核心词的长期自然排名和广告控制。", "control": "独立", "control_reason": "核心意图需要单独预算和表现责任。", "decision_reason": "父意图的机会比最高，保留为长期核心；不因该指标自动成为首攻。"},
        "sister birthday gifts": {"task": "首攻", "priority": "P2", "direction": "先验证生日场景中的产品适配和订单信号。", "control": "共享", "control_reason": "新品首轮先共享流量验证，避免拆碎有限预算。", "decision_reason": "子意图比父意图更适合作为局部突破点，父意图保留为核心。"},
        "mother gifts": {"task": "扩展", "priority": "P2", "direction": "待首攻验证后加入亲属礼物共享池。", "control": "共享", "control_reason": "当前只需低成本扩展验证，不需要单独控制。", "decision_reason": "精准需求存在，但先级低于首攻和核心。"},
        "wife gifts": {"task": "扩展", "priority": "P3", "direction": "与兼容扩展意图共用验证池。", "control": "共享", "control_reason": "独立控制价值不足，共享可减少预算碎片。", "decision_reason": "保留精准词资产，等核心与首攻验证后扩展。"},
    }
    keyword_decisions = {}
    for record_id in ("k1", "k2"):
        keyword_decisions[record_id] = {"current_state": "布局", "launch_investment": "是", "phase": "PHASE_1", "mode": "EXACT", "start_condition": "Listing、可售状态和经济门槛通过 6-2 检查。", "hold_reason": ""}
    keyword_decisions["k3"] = {"current_state": "首攻", "launch_investment": "是", "phase": "PHASE_1", "mode": "EXACT", "start_condition": "Listing、可售状态和经济门槛通过 6-2 检查。", "hold_reason": ""}
    keyword_decisions["k4"] = {"current_state": "首攻", "launch_investment": "是", "phase": "PHASE_1", "mode": "EXACT", "start_condition": "Listing、可售状态和经济门槛通过 6-2 检查。", "hold_reason": ""}
    keyword_decisions["k5"] = {"current_state": "待扩张", "launch_investment": "是", "phase": "PHASE_1", "mode": "EXACT", "start_condition": "首攻有初步有效订单后加入共享扩展池。", "hold_reason": ""}
    keyword_decisions["k6"] = {"current_state": "待扩张", "launch_investment": "是", "phase": "PHASE_1", "mode": "EXACT", "start_condition": "首攻有初步有效订单后加入共享扩展池。", "hold_reason": ""}
    keyword_decisions["k7"] = {"current_state": "季节等待", "launch_investment": "否", "phase": "SEASONAL", "mode": "", "start_condition": "到达对应节日规划窗口后复核。", "hold_reason": "当前季节不匹配，等待节日窗口。"}
    return {"intent_decisions": intent_decisions, "keyword_decisions": keyword_decisions}


def make_records(tmp_path: Path, profile: str = "MULTI_BENCHMARK"):
    summary, mapping = source_rows(profile)
    codes = bp.assign_stable_intent_codes(tmp_path / "skill-output", [row["精准泛词"] for row in summary])
    plan = bp.build_plan_records(summary, mapping, decisions(), codes, profile)
    return summary, mapping, plan, codes


def write_csv(path: Path, columns, rows):
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(columns))
        writer.writeheader()
        writer.writerows(rows)


def write_603_package(root: Path, stamp: str, *, malformed: bool = False, include_mapping: bool = True):
    directory = root / "06_SKILL分析报告" / bp.INPUT_603_DIR
    folder = directory / stamp
    folder.mkdir(parents=True, exist_ok=True)
    summary, mapping = source_rows("SINGLE_BENCHMARK")
    summary_path = folder / f"6-0-3_{PRODUCT}_精准泛词汇总_{stamp}.csv"
    mapping_path = folder / f"6-0-3_{PRODUCT}_词对应的精准泛词_{stamp}.csv"
    write_csv(summary_path, bp.SUMMARY_COLUMNS, summary)
    if malformed:
        write_csv(mapping_path, ["Id", "wrong"], [{"Id": "k"}])
    elif include_mapping:
        write_csv(mapping_path, bp.SINGLE_MAPPING_COLUMNS, mapping)
    input_folder = root / "06_SKILL分析报告" / "6-0-2_AI精准关键词识别" / "20260915_101010"
    (folder / bp.RUN_MANIFEST).write_text(json.dumps({
        "SkillId": "hzp-amz-6-0-3-precision-broad-extraction",
        "Current Product": PRODUCT,
        "RUN_ID": stamp,
        "RUN_TIMESTAMP": stamp,
        "GeneratedAt": "2026-09-16T10:10:10+08:00",
        "Input Skill": "hzp-amz-6-0-2-ai-precision-keyword-identification",
        "Input Run ID": "602-run",
        "Input RUN_TIMESTAMP": "20260915_101010",
        "Input Folder": str(input_folder),
        "Input File": str(input_folder / "6-0-2_TST01_AI高度精准词_20260915_101010.csv"),
        "Input Record Count": len(mapping),
        "Output Folder": str(folder),
        "Output Files": [summary_path.name, mapping_path.name],
        "Output Record Counts": {"Intent Count": len(summary), "Keyword Count": len(mapping)},
        "Run Status": "VALID",
    }, ensure_ascii=False), encoding="utf-8")
    return summary_path, mapping_path


def test_child_beachhead_parent_core_and_high_ratio_is_not_automatic_first_attack(tmp_path):
    _, _, plan, _ = make_records(tmp_path)
    by_intent = {row["精准泛词"]: row for row in plan["A"]}
    assert by_intent["sister birthday gifts"]["作战任务"] == "首攻"
    assert by_intent["sister gifts"]["作战任务"] == "核心"
    assert by_intent["sister gifts"]["意图机会比"] == "25.0000"
    assert float(by_intent["sister gifts"]["意图机会比"]) > float(by_intent["sister birthday gifts"]["意图机会比"])


def test_lifecycle_covers_every_603_record_once(tmp_path):
    _, mapping, plan, _ = make_records(tmp_path)
    assert len(plan["C"]) == len(mapping)
    assert [row["Id"] for row in plan["C"]] == [row["Id"] for row in mapping]
    assert len({row["Id"] for row in plan["C"]}) == len(mapping)


def test_b_is_strict_projection_of_current_phase_1_rows(tmp_path):
    _, _, plan, _ = make_records(tmp_path)
    eligible = {row["Id"] for row in plan["C"] if row["计划阶段"] == "PHASE_1" and row["新品期是否投放"] == "是" and row["控制方式"] != "不投"}
    assert {row["Id"] for row in plan["B"]} == eligible
    assert all(row["计划阶段"] == "PHASE_1" for row in plan["B"])


def test_first_attack_can_be_shared_and_keeps_control_reason(tmp_path):
    _, _, plan, _ = make_records(tmp_path)
    child = next(row for row in plan["A"] if row["精准泛词"] == "sister birthday gifts")
    assert child["控制方式"] == "共享"
    assert child["控制原因"]


def test_shared_expansion_intents_pool_together(tmp_path):
    _, _, plan, _ = make_records(tmp_path)
    shared_expansion = [row for row in plan["B"] if row["作战任务"] == "扩展" and row["控制方式"] == "共享"]
    assert {row["精准泛词"] for row in shared_expansion} == {"mother gifts", "wife gifts"}
    assert len({row["作战单元ID"] for row in shared_expansion}) == 1


def test_multiple_exact_keywords_under_one_independent_intent_share_one_unit(tmp_path):
    _, _, plan, _ = make_records(tmp_path)
    independent = [row for row in plan["B"] if row["精准泛词"] == "sister gifts"]
    assert len(independent) == 2
    assert len({row["作战单元ID"] for row in independent}) == 1


def test_campaign_preview_has_code_only_for_independent_and_uses_no_tag_placeholder(tmp_path):
    _, _, plan, _ = make_records(tmp_path)
    campaigns = _campaign_groups(plan["B"], PRODUCT, None)
    independent = next(item for item in campaigns if item["control"] == "独立")
    shared_core = next(item for item in campaigns if item["control"] == "共享" and item["role_code"] == "COR")
    assert independent["intent_code"] in independent["name"]
    assert "INT-" not in shared_core["name"]
    assert shared_core["name"] == "{ProductCode}.{CampaignTag}.SP-COR-EXA-SBG-01"


def test_multi_benchmark_evidence_does_not_multiply_market_capacity(tmp_path):
    _, mapping, plan, _ = make_records(tmp_path)
    original = next(row for row in mapping if row["Id"] == "k1")
    actual = next(row for row in plan["C"] if row["Id"] == "k1")
    assert original["市场容量"] == actual["市场容量"] == "200"
    assert actual["对标覆盖数"] == "4"


def test_stable_intent_codes_reuse_registry_and_canonical_whitespace(tmp_path):
    output = tmp_path / "codes"
    first = bp.assign_stable_intent_codes(output, ["sister gifts", "wife gifts"])
    second = bp.assign_stable_intent_codes(output, ["  SISTER   GIFTS ", "wife gifts"])
    assert first["sister gifts"] == second["  SISTER   GIFTS "]
    assert first["wife gifts"] == second["wife gifts"]
    registry = json.loads((output / "stable_intent_code_registry.json").read_text(encoding="utf-8"))
    assert len(set(registry["canonical_to_code"].values())) == len(registry["canonical_to_code"])


def test_603_resolver_falls_back_from_newer_invalid_package(tmp_path):
    root = tmp_path / "product"
    older = "20260915_101010"
    newer = "20260916_101010"
    write_603_package(root, older)
    write_603_package(root, newer, malformed=True)
    result = bp.resolve_latest_valid_603(root, PRODUCT)
    assert result["status"] == bp.STATUS_603_READY
    assert result["run_timestamp"] == older
    assert result["schema_profile"] == "SINGLE_BENCHMARK"


def test_603_manifest_package_is_read_as_a_unit(tmp_path):
    root = tmp_path / "product"
    stamp = TIMESTAMP
    folder = root / "06_SKILL分析报告" / bp.INPUT_603_DIR / stamp
    folder.mkdir(parents=True)
    summary, mapping = source_rows("MULTI_BENCHMARK")
    summary_name = f"6-0-3_{PRODUCT}_精准泛词汇总_{stamp}.csv"
    mapping_name = f"6-0-3_{PRODUCT}_词对应的精准泛词_{stamp}.csv"
    write_csv(folder / summary_name, bp.SUMMARY_COLUMNS, summary)
    write_csv(folder / mapping_name, bp.MULTI_MAPPING_COLUMNS, mapping)
    (folder / bp.RUN_MANIFEST).write_text(json.dumps({
        "SkillId": "hzp-amz-6-0-3-precision-broad-extraction",
        "RUN_ID": "603-manifest-run", "RUN_TIMESTAMP": stamp, "Current Product": PRODUCT,
        "GeneratedAt": "2026-09-16T10:10:10+08:00", "Run Status": "VALID",
        "Input Skill": "hzp-amz-6-0-2-ai-precision-keyword-identification",
        "Input Run ID": "602-run", "Input RUN_TIMESTAMP": "20260915_101010",
        "Input Folder": str(root / "06_SKILL分析报告" / "6-0-2_AI精准关键词识别" / "20260915_101010"),
        "Input File": str(root / "06_SKILL分析报告" / "6-0-2_AI精准关键词识别" / "20260915_101010" / "6-0-2_TST01_AI高度精准词_20260915_101010.csv"),
        "Input Record Count": 7, "Output Folder": str(folder),
        "Output Files": [summary_name, mapping_name],
        "Output Record Counts": {"Intent Count": 4, "Keyword Count": 7},
    }), encoding="utf-8")
    result = bp.resolve_latest_valid_603(root, PRODUCT)
    assert result["status"] == bp.STATUS_603_READY
    assert result["input_mode"] == "MANIFEST_RUN_PACKAGE"
    assert result["run_id"] == "603-manifest-run"
    assert result["schema_profile"] == "MULTI_BENCHMARK"
    assert Path(result["summary_file"]).parent == Path(result["mapping_file"]).parent


def test_603_resolver_ignores_root_level_timestamp_pairs(tmp_path):
    directory = tmp_path / "06_SKILL分析报告" / bp.INPUT_603_DIR
    directory.mkdir(parents=True)
    summary, mapping = source_rows("SINGLE_BENCHMARK")
    stamp = TIMESTAMP
    write_csv(directory / f"6-0-3_{PRODUCT}_精准泛词汇总_{stamp}.csv", bp.SUMMARY_COLUMNS, summary)
    write_csv(directory / f"6-0-3_{PRODUCT}_词对应的精准泛词_{stamp}.csv", bp.SINGLE_MAPPING_COLUMNS, mapping)
    result = bp.resolve_latest_valid_603(tmp_path, PRODUCT)
    assert result["status"] == "6-0-3_RUN_PACKAGE_NOT_FOUND"


def test_optional_606_is_marked_unavailable_or_reads_one_valid_package(tmp_path):
    root = tmp_path / "product"
    missing = bp.resolve_latest_valid_606(root, PRODUCT)
    assert missing["status"] == "606_EVIDENCE_NOT_AVAILABLE"
    stamp = TIMESTAMP
    run_folder = root / "06_SKILL分析报告" / "6-0-6_test" / stamp
    run_folder.mkdir(parents=True)
    detail = f"6-0-6_{PRODUCT}_对标意图市场占领明细_{stamp}.csv"
    consensus = f"6-0-6_{PRODUCT}_意图多对标占领共识_{stamp}.csv"
    write_csv(run_folder / detail, ["精准泛词", "占领状态"], [{"精准泛词": "sister gifts", "占领状态": "evidence"}])
    write_csv(run_folder / consensus, ["精准泛词", "共识"], [{"精准泛词": "sister gifts", "共识": "evidence"}])
    (run_folder / bp.RUN_MANIFEST).write_text(json.dumps({"RUN_ID": "606-2", "RUN_TIMESTAMP": stamp, "Current Product": PRODUCT, "Run Status": "VALID", "Output Files": [detail, consensus]}), encoding="utf-8")
    loaded = bp.resolve_latest_valid_606(root, PRODUCT)
    assert loaded["status"] == bp.STATUS_606_READY
    assert loaded["run_id"] == "606-2"
    assert len(loaded["rows"]["detail"]) == 1


def test_run_package_timestamp_consistency_and_same_run_html_snapshot(tmp_path):
    summary, mapping, plan, _ = make_records(tmp_path)
    input_603 = {"run_id": "603-1", "run_timestamp": "20260915_101010", "run_folder": "603-folder", "files": ["summary.csv", "mapping.csv"], "input_mode": "MANIFEST_RUN_PACKAGE"}
    result = bp.write_run_package(product_root=tmp_path / "product", product_code=PRODUCT, input_603=input_603, input_606={"status": "606_EVIDENCE_NOT_AVAILABLE"}, records=plan, run_timestamp=TIMESTAMP)
    folder = Path(result["run_folder"])
    assert folder == bp.output_root(tmp_path / "product")
    assert all(bp._timestamp_from_filename(Path(path).name) == TIMESTAMP for path in result["files"])
    snapshot = read_embedded_snapshot((folder / f"新品广告作战规划报告_{TIMESTAMP}.html").read_text(encoding="utf-8"))
    assert snapshot["run_timestamp"] == TIMESTAMP
    assert len(snapshot["A"]) == len(summary)
    assert len(snapshot["C"]) == len(mapping)
    assert len(snapshot["B"]) == len(plan["B"])
    assert "fetch(" not in (folder / f"新品广告作战规划报告_{TIMESTAMP}.html").read_text(encoding="utf-8").casefold()


def test_formal_output_failure_marks_run_invalid(monkeypatch, tmp_path):
    _, _, plan, _ = make_records(tmp_path)
    input_603 = {"run_id": "603-1", "run_timestamp": "20260915_101010", "run_folder": "603-folder", "files": [], "input_mode": "MANIFEST_RUN_PACKAGE"}
    def fail(*args, **kwargs):
        raise OSError("simulated renderer output failure")
    monkeypatch.setattr(bp, "_write_html_atomic", fail)
    folder = bp.output_root(tmp_path / "product")
    with pytest.raises(OSError):
        bp.write_run_package(product_root=tmp_path / "product", product_code=PRODUCT, input_603=input_603, input_606={"status": "606_EVIDENCE_NOT_AVAILABLE"}, records=plan, run_timestamp=TIMESTAMP)
    manifest = json.loads((folder / f"{bp.RUN_MANIFEST_PREFIX}{TIMESTAMP}.json").read_text(encoding="utf-8"))
    assert manifest["Run Status"] == "INVALID"
    assert bp.resolve_latest_valid_6_1(tmp_path / "product", PRODUCT)["status"] == "6-1_RUN_PACKAGE_INVALID"


def test_new_run_preserves_history_and_timestamp_collision_does_not_overwrite(tmp_path):
    _, _, plan, _ = make_records(tmp_path)
    input_603 = {"run_id": "603-1", "run_timestamp": "20260915_101010", "run_folder": "603-folder", "files": [], "input_mode": "MANIFEST_RUN_PACKAGE"}
    product_root = tmp_path / "product"
    first = bp.write_run_package(product_root=product_root, product_code=PRODUCT, input_603=input_603, input_606={"status": "606_EVIDENCE_NOT_AVAILABLE"}, records=plan, run_timestamp=TIMESTAMP)
    first_report = Path(first["run_folder"]) / f"新品广告作战规划报告_{TIMESTAMP}.html"
    before = first_report.read_bytes()
    second_stamp = "20260916_101011"
    second = bp.write_run_package(product_root=product_root, product_code=PRODUCT, input_603=input_603, input_606={"status": "606_EVIDENCE_NOT_AVAILABLE"}, records=plan, run_timestamp=second_stamp)
    assert Path(first["run_folder"]).is_dir() and Path(second["run_folder"]).is_dir()
    assert first_report.read_bytes() == before
    with pytest.raises(bp.ContractError, match="RUN_OUTPUT_ALREADY_EXISTS"):
        bp.write_run_package(product_root=product_root, product_code=PRODUCT, input_603=input_603, input_606={"status": "606_EVIDENCE_NOT_AVAILABLE"}, records=plan, run_timestamp=TIMESTAMP)


def test_latest_valid_6_1_resolver_returns_one_same_run_folder_for_6_1(tmp_path):
    _, _, plan, _ = make_records(tmp_path)
    input_603 = {"run_id": "603-1", "run_timestamp": "20260915_101010", "run_folder": "603-folder", "files": [], "input_mode": "MANIFEST_RUN_PACKAGE"}
    product_root = tmp_path / "product"
    bp.write_run_package(product_root=product_root, product_code=PRODUCT, input_603=input_603, input_606={"status": "606_EVIDENCE_NOT_AVAILABLE"}, records=plan, run_timestamp=TIMESTAMP)
    latest = bp.resolve_latest_valid_6_1(product_root, PRODUCT)
    assert latest["status"] == "LATEST_VALID_6-1_RUN_PACKAGE_READY"
    assert {Path(path).parent for path in latest["files"]} == {Path(latest["run_folder"])}
    assert {bp._timestamp_from_filename(Path(path).name) for path in latest["files"]} == {TIMESTAMP}


def test_marking_control_as_no_investment_cannot_enter_b(tmp_path):
    summary, mapping = source_rows()
    data = decisions()
    data["keyword_decisions"]["k3"].update({"launch_investment": "否", "hold_reason": "Keep on reserve."})
    codes = bp.assign_stable_intent_codes(tmp_path / "output", [row["精准泛词"] for row in summary])
    plan = bp.build_plan_records(summary, mapping, data, codes, "MULTI_BENCHMARK")
    assert "k3" not in {row["Id"] for row in plan["B"]}


def test_intent_marked_no_investment_is_excluded_from_b(tmp_path):
    summary, mapping = source_rows()
    data = decisions()
    data["intent_decisions"]["mother gifts"]["control"] = "不投"
    data["keyword_decisions"]["k5"].update({"launch_investment": "否", "phase": "HOLD", "hold_reason": "No current investment."})
    codes = bp.assign_stable_intent_codes(tmp_path / "output", [row["精准泛词"] for row in summary])
    plan = bp.build_plan_records(summary, mapping, data, codes, "MULTI_BENCHMARK")
    assert "k5" not in {row["Id"] for row in plan["B"]}


def test_run_stops_if_603_package_changes_after_decisions_were_made(tmp_path):
    product_root = tmp_path / "product"
    stamp = "20260915_101010"
    write_603_package(product_root, stamp)
    with pytest.raises(bp.ContractError, match="603_INPUT_CHANGED_AFTER_PLANNING"):
        bp.run_6_1(
            product_root=product_root,
            product_code=PRODUCT,
            decisions=decisions(),
            expected_603_run_id="a-different-run",
            expected_603_timestamp=stamp,
            expected_606_run_id="606_EVIDENCE_NOT_AVAILABLE",
        )


def test_investment_plan_requires_a_mode_even_after_phase_1(tmp_path):
    summary, mapping = source_rows()
    data = decisions()
    data["keyword_decisions"]["k5"].update({"phase": "PHASE_2", "mode": ""})
    codes = bp.assign_stable_intent_codes(tmp_path / "output", [row["精准泛词"] for row in summary])
    with pytest.raises(bp.ContractError, match="PLANNED_AD_TYPE_REQUIRED"):
        bp.build_plan_records(summary, mapping, data, codes, "MULTI_BENCHMARK")



