import csv
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from scripts.stage6_artifact_contract import make_artifact_metadata, new_run_context, write_metadata_sidecar
from scripts import stage6_artifact_contract as shared
MODULE_PATH = REPO / "hzp-amz-6-0-6-benchmark-intent-market-occupancy-analysis" / "scripts" / "benchmark_intent_occupancy.py"
spec = importlib.util.spec_from_file_location("benchmark_intent_occupancy", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def fixture_data(codes=("A", "B", "C")):
    summary = [
        {"精准泛词": "sister gifts", "中文": "姐妹礼物", "层级": "L1", "父精准泛词": "", "直接搜索量": "2000", "汇总搜索量": "24000", "平均竞品数": "500", "意图机会比": "48", "直接对应词数": "1"},
        {"精准泛词": "sister birthday gifts", "中文": "姐妹生日礼物", "层级": "L2", "父精准泛词": "sister gifts", "直接搜索量": "22000", "汇总搜索量": "22000", "平均竞品数": "400", "意图机会比": "55", "直接对应词数": "2"},
    ]
    mapping = [
        {"Id": "kw1", "词": "sister gifts", "中文": "姐妹礼物", "市场容量": "2000", "竞争产品数": "500", "供需比": "4", "对标覆盖数": str(len(codes)), "最佳自然排名": "3", "自然排名中位数": "18", "精准泛词": "sister gifts", "精准泛词中文": "姐妹礼物"},
        {"Id": "kw2", "词": "sister birthday gifts", "中文": "姐妹生日礼物", "市场容量": "20000", "竞争产品数": "400", "供需比": "50", "对标覆盖数": str(len(codes)), "最佳自然排名": "3", "自然排名中位数": "18", "精准泛词": "sister birthday gifts", "精准泛词中文": "姐妹生日礼物"},
        {"Id": "kw3", "词": "birthday gifts for sister", "中文": "送姐妹生日礼物", "市场容量": "2000", "竞争产品数": "600", "供需比": "3.3333", "对标覆盖数": str(len(codes)), "最佳自然排名": "100", "自然排名中位数": "100", "精准泛词": "sister birthday gifts", "精准泛词中文": "姐妹生日礼物"},
    ]
    rank_sets = {"A": {"kw1": "12", "kw2": "3", "kw3": "100"},
                 "B": {"kw1": "22", "kw2": "18", "kw3": "90"},
                 "C": {"kw1": "", "kw2": "76", "kw3": "150"}}
    details = []
    for code in codes:
        for row in mapping:
            ranks = rank_sets.get(code, rank_sets["A"])
            details.append({"Id": row["Id"], "词": row["词"], "中文": row["中文"], "市场容量": row["市场容量"],
                            "竞争产品数": row["竞争产品数"], "供需比": row["供需比"], "对标编码": code,
                            "对标ASIN": f"ASIN-{code}", "自然排名": ranks[row["Id"]]})
    occ = [{"对标编码": code, "精准泛词": intent, "占领等级": level, "占领判断原因": f"{code} 在 {intent} 的有效排名与覆盖表现。"}
           for code in codes for intent, level in (("sister gifts", "中度占领"), ("sister birthday gifts", "强占领" if code != "C" else "弱占领"))]
    decisions = {"occupancy_decisions": occ, "consensus_decisions": [
        {"精准泛词": "sister gifts", "多对标共识等级": "中共识", "共识判断原因": "多个对标覆盖强度不一。"},
        {"精准泛词": "sister birthday gifts", "多对标共识等级": "单点验证", "共识判断原因": "只有一个对标形成明显较深排名。"},
    ]}
    return details, summary, mapping, decisions


def test_single_benchmark_mode_and_no_fake_consensus():
    details, summary, mapping, decisions = fixture_data(("ONLY",))
    result = mod.calculate(details, summary, mapping, {"occupancy_decisions": decisions["occupancy_decisions"]})
    assert {row["多对标共识等级"] for row in result["consensus"]} == {"单对标模式"}
    assert all("单对标模式" in row["共识判断原因"] for row in result["consensus"])


def test_three_benchmarks_do_not_multiply_market_capacity():
    details, summary, mapping, decisions = fixture_data()
    result = mod.calculate(details, summary, mapping, decisions)
    child_rows = [row for row in result["occupancy"] if row["精准泛词"] == "sister birthday gifts"]
    assert [row["Top20占领搜索量"] for row in child_rows] == ["20000", "20000", "0"]
    assert all(row["汇总搜索量"] == "22000" for row in child_rows)


def test_top_thresholds_are_cumulative():
    details, summary, mapping, decisions = fixture_data()
    result = mod.calculate(details, summary, mapping, decisions)
    for row in result["occupancy"]:
        assert row["Top10关键词数"] <= row["Top20关键词数"] <= row["Top50关键词数"] <= row["Top100关键词数"]
        assert Decimalish(row["Top10占领搜索量"]) <= Decimalish(row["Top20占领搜索量"]) <= Decimalish(row["Top50占领搜索量"]) <= Decimalish(row["Top100占领搜索量"])
        assert Decimalish(row["Top10搜索量覆盖率"]) <= Decimalish(row["Top20搜索量覆盖率"]) <= Decimalish(row["Top50搜索量覆盖率"]) <= Decimalish(row["Top100搜索量覆盖率"])


def Decimalish(value):
    from decimal import Decimal
    return Decimal(value)


def test_parent_subtree_contains_descendant_and_no_cross_level_addition():
    details, summary, mapping, decisions = fixture_data(("A",))
    result = mod.calculate(details, summary, mapping, {"occupancy_decisions": decisions["occupancy_decisions"]})
    parent = next(row for row in result["occupancy"] if row["精准泛词"] == "sister gifts")
    child = next(row for row in result["occupancy"] if row["精准泛词"] == "sister birthday gifts")
    assert parent["汇总搜索量"] == "24000"
    assert parent["Top20占领搜索量"] == "22000"
    assert child["汇总搜索量"] == "22000"
    assert child["Top20占领搜索量"] == "20000"


def test_weighted_rank_gives_more_influence_to_high_volume_keyword():
    details, summary, mapping, decisions = fixture_data(("A",))
    result = mod.calculate(details, summary, mapping, {"occupancy_decisions": decisions["occupancy_decisions"]})
    child = next(row for row in result["occupancy"] if row["精准泛词"] == "sister birthday gifts")
    assert child["平均自然排名"] == "51.5000"
    assert child["加权自然排名"] == "11.8182"


def test_best_benchmark_uses_stable_top20_top10_weighted_rank_code_tiebreaks():
    details, summary, mapping, decisions = fixture_data(("Z", "A", "B"))
    # Equalize every numeric tie-break on the Child intent; Benchmark Code wins last.
    for row in details:
        if row["Id"] == "kw2":
            row["自然排名"] = "4"
        if row["Id"] == "kw3":
            row["自然排名"] = "50"
    result = mod.calculate(details, summary, mapping, decisions)
    child = next(row for row in result["consensus"] if row["精准泛词"] == "sister birthday gifts")
    assert child["最佳对标编码"] == "A"


@pytest.mark.parametrize("rank_a,rank_b,expected", [("30", "15", "B"), ("15", "8", "B"), ("5", "2", "B")])
def test_best_benchmark_tiebreaks_top20_then_top10_then_weighted_rank(rank_a, rank_b, expected):
    details, summary, mapping, decisions = fixture_data(("A", "B"))
    for row in details:
        if row["Id"] == "kw2":
            row["自然排名"] = rank_a if row["对标编码"] == "A" else rank_b
        if row["Id"] == "kw3":
            row["自然排名"] = "50"
    result = mod.calculate(details, summary, mapping, decisions)
    child = next(row for row in result["consensus"] if row["精准泛词"] == "sister birthday gifts")
    assert child["最佳对标编码"] == expected


def test_missing_benchmark_observation_is_audited_without_inventing_a_rank():
    details, summary, mapping, decisions = fixture_data(("A", "B", "C"))
    details = [row for row in details if row["对标编码"] != "C"]
    result = mod.calculate(details, summary, mapping, decisions,
                           benchmark_identities={"A": "ASIN-A", "B": "ASIN-B", "C": "ASIN-C"})
    assert len(result["no_observation_audit"]) == len(mapping)
    c_child = next(row for row in result["occupancy"] if row["对标编码"] == "C" and row["精准泛词"] == "sister birthday gifts")
    assert c_child["有效排名词数"] == 0
    assert c_child["Top20搜索量覆盖率"] == "0.0000"
    assert "999" not in str(result["no_observation_audit"])


def test_consensus_decisions_are_explained_and_restricted_to_labels():
    details, summary, mapping, decisions = fixture_data()
    result = mod.calculate(details, summary, mapping, decisions)
    assert next(r for r in result["consensus"] if r["精准泛词"] == "sister gifts")["共识判断原因"] == "多个对标覆盖强度不一。"
    bad = json.loads(json.dumps(decisions))
    bad["consensus_decisions"][0]["多对标共识等级"] = "87分"
    with pytest.raises(ValueError, match="DECISION_COVERAGE_MISMATCH"):
        mod.calculate(details, summary, mapping, bad)


def test_html_disclaims_market_share_and_has_all_eleven_modules():
    details, summary, mapping, decisions = fixture_data()
    result = mod.calculate(details, summary, mapping, decisions)
    inputs = {k: {"file": f"{k}.csv", "run_id": "run-1"} for k in ("detail", "summary", "mapping")}
    page = mod.render_html("P1", result, inputs, run_id="run-606", generated_at="2026-09-16T12:00:00+08:00")
    assert "Organic Search Occupancy ≠ Sales Market Share" in page
    assert "110%" not in page
    assert all(f'id="m{i}"' in page for i in range(1, 12))
    assert "蓝海、低竞争或容易进入结论" in page


def test_latest_valid_601_and_same_run_603_bundle(tmp_path):
    root = tmp_path
    d601 = root / "06_SKILL分析报告" / mod.INPUT_DIR_601
    d603 = root / "06_SKILL分析报告" / mod.INPUT_DIR_603
    d601.mkdir(parents=True)
    d603.mkdir(parents=True)
    details, summary, mapping, _ = fixture_data(("A",))
    disk_details = [{**{key: row.get(key, "") for key in mod.DETAIL_COLUMNS}, "对标编号": "500"} for row in details]
    ctx601 = new_run_context("6-0-1", "hzp-amz-6-0-1-benchmark-organic-keyword-extraction", "P1", now=datetime.fromisoformat("2026-09-15T10:00:00+08:00"))
    older601 = new_run_context("6-0-1", "hzp-amz-6-0-1-benchmark-organic-keyword-extraction", "P1", now=datetime.fromisoformat("2026-09-14T10:00:00+08:00"))
    ctx603 = new_run_context("6-0-3", "hzp-amz-6-0-3-precision-broad-extraction", "P1", now=datetime.fromisoformat("2026-09-15T11:00:00+08:00"))
    p601 = d601 / ctx601.run_timestamp / f"6-0-1_P1_多对标关键词排名明细_{ctx601.run_timestamp}.csv"
    p601.parent.mkdir(parents=True, exist_ok=True)
    pool601 = d601 / ctx601.run_timestamp / f"6-0-1_P1_对标关键词母池_{ctx601.run_timestamp}.csv"
    c601 = d601 / ctx601.run_timestamp / f"所有对标自然排名关键词汇总_{ctx601.run_timestamp}.csv"
    write_csv(p601, disk_details, mod.DETAIL_COLUMNS)
    pool_rows = [{"Id": "K1", "词": "term", "中文": "词", "市场容量": 1000, "竞争产品数": 20, "供需比": "50.0000", "对标覆盖数": 1, "最佳自然排名": 5, "自然排名中位数": 5}]
    pool_schema = ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数", "最佳自然排名", "自然排名中位数")
    c_rows = [{**{key: value for key, value in row.items() if key != "对标编码"}, "ASIN": row["对标ASIN"], "产品编号": "500"} for row in disk_details]
    c_schema = tuple(column for column in mod.DETAIL_COLUMNS if column != "对标编码") + ("ASIN", "产品编号")
    raw_path = p601.parent / f"ASIN-A+关键词自然排名_{ctx601.run_timestamp}.csv"
    write_csv(raw_path, disk_details, mod.DETAIL_COLUMNS)
    write_csv(pool601, pool_rows, pool_schema)
    write_csv(c601, c_rows, c_schema)
    outputs601 = [str(p601), str(pool601), str(raw_path), str(c601)]
    extras601 = {"Benchmark_Count": 1, "Benchmark_Codes": ["A"], "Benchmark_ASINs": ["ASIN-A"],
                 "BenchmarkASINs": ["ASIN-A"], "BenchmarkRawOrganicFiles": [raw_path.name], "BenchmarkRawOrganicFileCount": 1,
                 "BenchmarkOrganicSummaryFile": c601.name, "BenchmarkOrganicSummaryRecordCount": len(c_rows),
                 "BenchmarkProductCodes": {"ASIN-A": "500"}, "PerBenchmarkObservationCounts": {"ASIN-A": len(details)}}
    for path, identity, schema, rows in ((p601, "BENCHMARK_KEYWORD_DETAIL", mod.DETAIL_COLUMNS, details),
                                        (pool601, "BENCHMARK_KEYWORD_POOL", pool_schema, pool_rows),
                                        (raw_path, "BENCHMARK_KEYWORD_RAW_ASIN-A", mod.DETAIL_COLUMNS, details),
                                        (c601, "BENCHMARK_KEYWORD_ALL_OBSERVATIONS", c_schema, c_rows)):
        write_metadata_sidecar(path, make_artifact_metadata(ctx601, identity, run_status="FULL_SUCCESS", schema=schema, record_count=len(rows), output_assets=outputs601, extra=extras601))
    old601 = d601 / older601.run_timestamp / f"6-0-1_P1_多对标关键词排名明细_{older601.run_timestamp}.csv"
    old601.parent.mkdir(parents=True, exist_ok=True)
    write_csv(old601, disk_details, mod.DETAIL_COLUMNS)
    write_metadata_sidecar(old601, make_artifact_metadata(
        older601, "BENCHMARK_KEYWORD_DETAIL", run_status="FULL_SUCCESS",
        schema=mod.DETAIL_COLUMNS, record_count=len(details),
        extra={"Benchmark_Count": 1, "Benchmark_Codes": ["A"], "Benchmark_ASINs": ["ASIN-A"]},
    ))
    for key, name, rows, schema, identity in (("summary", "精准泛词汇总", summary, mod.SUMMARY_COLUMNS, "PRECISION_BROAD_SUMMARY"), ("mapping", "词对应的精准泛词", mapping, mod.MAPPING_COLUMNS, "PRECISION_BROAD_MAPPING")):
        path = d603 / f"6-0-3_P1_{name}_{ctx603.run_timestamp}.csv"
        write_csv(path, rows, schema)
        write_metadata_sidecar(path, make_artifact_metadata(ctx603, identity, run_status="FULL_SUCCESS", schema=schema, record_count=len(rows)))
    loaded = mod.resolve_inputs(root, "P1")
    assert loaded["detail"].get("run_id") == ctx601.run_id
    assert {row["对标编码"] for row in loaded["detail_rows"]} == {"A"}
    assert loaded["summary"].get("run_id") == loaded["mapping"].get("run_id") == ctx603.run_id


def write_csv(path, rows, schema):
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=schema)
        writer.writeheader()
        writer.writerows(rows)


def test_timestamped_outputs_share_run_time_and_never_overwrite(tmp_path, monkeypatch):
    details, summary, mapping, decisions = fixture_data(("A",))
    inputs = {"detail_rows": details, "summary_rows": summary, "mapping_rows": mapping,
              "benchmark_identities": {"A": "ASIN-A"},
              "detail": {"file": "detail.csv", "metadata": {"Skill_ID": "6-0-1", "Report_Identity": "BENCHMARK_KEYWORD_DETAIL"}, "record_count": len(details), "run_id": "r1", "run_timestamp": "t1"},
              "summary": {"file": "summary.csv", "metadata": {"Skill_ID": "6-0-3", "Report_Identity": "PRECISION_BROAD_SUMMARY"}, "record_count": len(summary), "run_id": "r3", "run_timestamp": "t3"},
              "mapping": {"file": "mapping.csv", "metadata": {"Skill_ID": "6-0-3", "Report_Identity": "PRECISION_BROAD_MAPPING"}, "record_count": len(mapping), "run_id": "r3", "run_timestamp": "t3"}}
    fixed = datetime.fromisoformat("2026-09-16T12:34:56+08:00")
    monkeypatch.setattr(mod, "new_run_context", lambda *args, **kwargs: shared.new_run_context(*args, now=fixed, **kwargs))
    out = mod.build_outputs(tmp_path, "P1", inputs, {"occupancy_decisions": decisions["occupancy_decisions"]})
    assert {p.stem.rsplit("_", 2)[-2:] and "_".join(p.stem.rsplit("_", 2)[-2:]) for p in out.values()} == {"20260916_123456"}
    assert all(p.with_name(p.name + ".meta.json").is_file() for p in out.values())
    assert all(p.read_bytes().startswith(b"\xef\xbb\xbf") for p in (out["occupancy"], out["consensus"]))
    output_meta = [json.loads(p.with_name(p.name + ".meta.json").read_text(encoding="utf-8")) for p in out.values()]
    assert {meta["RUN_ID"] for meta in output_meta} == {"6-0-6_P1_20260916_123456"}
    assert {meta["RUN_TIMESTAMP"] for meta in output_meta} == {"20260916_123456"}
    with pytest.raises(FileExistsError, match="OUTPUT_WOULD_OVERWRITE"):
        mod.build_outputs(tmp_path, "P1", inputs, {"occupancy_decisions": decisions["occupancy_decisions"]})
    partial_details = [dict(row) for row in details]
    partial_details[0]["自然排名"] = ""
    partial_inputs = dict(inputs, detail_rows=partial_details)
    partial = mod.build_outputs(tmp_path / "incomplete", "P1", partial_inputs,
                                {"occupancy_decisions": decisions["occupancy_decisions"]})
    partial_meta = json.loads(partial["occupancy"].with_name(partial["occupancy"].name + ".meta.json").read_text(encoding="utf-8"))
    assert partial_meta["Run_Status"] == "INCOMPLETE"


def test_null_and_invalid_ranks_are_audited_not_converted_to_999():
    details, summary, mapping, decisions = fixture_data(("A",))
    details[0]["自然排名"] = "NULL"
    details[1]["自然排名"] = "-1"
    result = mod.calculate(details, summary, mapping, {"occupancy_decisions": decisions["occupancy_decisions"]})
    assert {row["状态"] for row in result["rank_audit"]} == {"MISSING_ORGANIC_RANK", "INVALID_ORGANIC_RANK"}
    parent = next(row for row in result["occupancy"] if row["精准泛词"] == "sister gifts")
    assert parent["有效排名词数"] == 1
    assert "999" not in str(parent)


def test_duplicate_benchmark_observation_is_rejected():
    details, summary, mapping, decisions = fixture_data(("A",))
    details.append(dict(details[0]))
    with pytest.raises(ValueError, match="DUPLICATE_BENCHMARK_OBSERVATION"):
        mod.calculate(details, summary, mapping)


def test_missing_join_and_summary_volume_mismatch_fail_closed():
    details, summary, mapping, _ = fixture_data(("A",))
    details = [row for row in details if row["Id"] != "kw1"]
    with pytest.raises(ValueError, match="BENCHMARK_OBSERVATION_JOIN_FAILED"):
        mod.calculate(details, summary, mapping)
    details, summary, mapping, _ = fixture_data(("A",))
    summary[1]["汇总搜索量"] = "22001"
    with pytest.raises(ValueError, match="INTENT_VOLUME_MISMATCH"):
        mod.calculate(details, summary, mapping)


def test_csv_schema_and_parent_child_values_are_reconstructable():
    details, summary, mapping, decisions = fixture_data()
    result = mod.calculate(details, summary, mapping, decisions)
    assert tuple(result["occupancy"][0].keys())[:24] == mod.OCCUPANCY_COLUMNS
    assert tuple(result["consensus"][0].keys())[:17] == mod.CONSENSUS_COLUMNS
    for row in result["consensus"]:
        assert row["对标总数"] == len(result["benchmarks"])
        assert row["有效覆盖对标数"] <= row["对标总数"]
