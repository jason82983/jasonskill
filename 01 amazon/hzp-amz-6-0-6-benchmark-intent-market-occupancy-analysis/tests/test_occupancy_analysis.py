from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL.parent / "scripts"))
sys.path.insert(0, str(SKILL / "scripts"))
from stage6_artifact_contract import write_metadata_sidecar
import occupancy_analysis as oa  # noqa: E402


def write_csv(path: Path, columns: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def summary_row(
    name: str, volume: int, parent: str = "", level: str = "L1",
    direct: int | None = None, direct_count: int = 1,
) -> dict[str, object]:
    return {
        "精准泛词": name, "中文": name + " 中文", "层级": level, "父精准泛词": parent,
        "直接搜索量": volume if direct is None else direct, "汇总搜索量": volume,
        "平均竞品数": "10", "意图机会比": "2.0000", "直接对应词数": direct_count,
    }


def mapping_row(record_id: str, keyword: str, capacity: int, intent: str) -> dict[str, object]:
    return {
        "Id": record_id, "词": keyword, "中文": keyword, "市场容量": capacity,
        "竞争产品数": "10", "供需比": "2.0000", "对标覆盖数": "3",
        "最佳自然排名": "3", "自然排名中位数": "18",
        "精准泛词": intent, "精准泛词中文": intent + " 中文",
    }


def observation(record_id: str, keyword: str, capacity: int, code: str, rank: object, asin: str | None = None) -> dict[str, object]:
    return {
        "Id": record_id, "词": keyword, "中文": keyword, "市场容量": capacity,
        "竞争产品数": "10", "供需比": "2.0000", "对标编码": code,
        "对标ASIN": asin or f"B0{code}", "自然排名": "" if rank is None else rank,
    }


def package_folder(root: Path, skill_dir: str, stamp: str) -> Path:
    folder = root / "06_SKILL分析报告" / skill_dir / stamp
    folder.mkdir(parents=True)
    return folder


def make_602_package(root: Path, stamp: str, rows: list[dict[str, object]], status: str = "VALID") -> Path:
    folder = root / "06_SKILL分析报告" / "6-0-2_AI精准关键词识别"
    folder.mkdir(parents=True, exist_ok=True)
    codes = list(dict.fromkeys(str(row["对标编码"]) for row in rows))
    product_ids = {code: f"PROID-{code}" for code in codes}
    identities = {}
    observations = []
    for row in rows:
        code = str(row["对标编码"])
        asin = str(row["对标ASIN"])
        identities[product_ids[code]] = {"对标编码": code, "对标ASIN": asin}
        observations.append({
            "所属产品编号": product_ids[code], "对标ASIN": asin, "Id": row["Id"], "词": row["词"],
            "中文": row["中文"], "市场容量": row["市场容量"], "竞争产品数": row["竞争产品数"],
            "供需比": row["供需比"], "自然排名": row["自然排名"], "精准度": "高度精准",
            "精准原因": "满足当前产品的高度精准搜索意图",
        })
    unique = {}
    for row in observations:
        canonical = " ".join(str(row["词"]).casefold().split())
        unique.setdefault(canonical, []).append(row)
    deduplicated = []
    for group in unique.values():
        first = group[0]
        ranks = [float(row["自然排名"]) for row in group if str(row["自然排名"] or "").strip()]
        deduplicated.append({
            "Id": first["Id"], "词": first["词"], "中文": first["中文"],
            "市场容量": first["市场容量"], "竞争产品数": first["竞争产品数"], "供需比": first["供需比"],
            "对标覆盖数": len({row["所属产品编号"] for row in group}),
            "最佳自然排名": min(ranks) if ranks else "",
            "自然排名中位数": sorted(ranks)[len(ranks) // 2] if ranks else "",
            "精准度": "高度精准", "精准原因": first["精准原因"],
        })
    names = {
        "ai": f"6-0-2_精准判断所有词表_{stamp}.csv",
        "high_precision": f"6-0-2_高度精准词表_{stamp}.csv",
        "deduplicated": f"6-0-2_去对标去重 高度精准词_{stamp}.csv",
    }
    paths = {key: folder / name for key, name in names.items()}
    paths["benchmarks"] = {
        product_id: folder / f"6-0-2_{product_id}_高度精准词_{stamp}.csv"
        for product_id in product_ids.values()
    }
    all_paths = [paths[key] for key in ("ai", "high_precision", "deduplicated")] + list(paths["benchmarks"].values())
    write_csv(paths["ai"], oa.INPUT_602_COLUMNS, observations)
    write_csv(paths["high_precision"], oa.INPUT_602_COLUMNS, observations)
    write_csv(paths["deduplicated"], (
        "Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数",
        "最佳自然排名", "自然排名中位数", "精准度", "精准原因",
    ), deduplicated)
    for product_id, path in paths["benchmarks"].items():
        write_csv(path, oa.INPUT_602_COLUMNS, [row for row in observations if row["所属产品编号"] == product_id])
    per_input = {product_id: sum(row["所属产品编号"] == product_id for row in observations)
                 for product_id in product_ids.values()}
    per_high = dict(per_input)
    manifest = {
        "SkillId": "hzp-amz-6-0-2-ai-precision-keyword-identification", "Current Product": "TEST",
        "RUN_ID": f"602-{stamp}", "RUN_TIMESTAMP": stamp, "GeneratedAt": "2026-09-16T12:00:00+08:00",
        "Input Source": "test fixture", "Input Skill": "hzp-amz-6-0-1-benchmark-organic-keyword-extraction",
        "Input Run ID": "601-run", "Input RUN_TIMESTAMP": "20260916_090000",
        "Input Folder": str(root / "601"), "Input File": str(root / "601" / "source.csv"),
        "Product Text Input": str(root / "product.txt"), "Input Record Count": len(observations),
        "Input Unique Keyword Count": len(deduplicated), "Output Folder": str(folder),
        "Output Files": [path.name for path in all_paths], "Benchmark Count": len(product_ids),
        "Expected Benchmark Count": len(product_ids), "Benchmark Product Codes": list(product_ids.values()),
        "Benchmark Identities": identities, "PerBenchmarkInputObservationCount": per_input,
        "PerBenchmarkHighPrecisionRecordCount": per_high,
        "Expected Benchmark Files": [paths["benchmarks"][code].name for code in product_ids.values()],
        "GeneratedBenchmarkFiles": [paths["benchmarks"][code].name for code in product_ids.values()],
        "Record Counts": {
            "Input Observation Count": len(observations), "Input Unique Keyword Count": len(deduplicated),
            "AI Record Count": len(observations), "High Precision Record Count": len(observations),
            "Unique High Precision Keyword Count": len(deduplicated), "Benchmark Count": len(product_ids),
            "Benchmark File Count": len(product_ids), "Benchmark High Precision Observation Count": len(observations),
        },
        "Output Record Counts": {
            "AI Precision Observation Count": len(observations),
            "High Precision Observation Count": len(observations),
            "Unique High Precision Keyword Count": len(deduplicated),
        },
        "Run Status": status,
    }
    (folder / f"{oa.RUN_MANIFEST_PREFIX}{stamp}.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    definitions = [
        (paths["ai"], "AI_PRECISION_KEYWORD_OBSERVATIONS", observations, oa.INPUT_602_COLUMNS, {}),
        (paths["high_precision"], "HIGH_PRECISION_KEYWORD_OBSERVATIONS", observations, oa.INPUT_602_COLUMNS, {}),
        (paths["deduplicated"], "去对标去重 高度精准词", deduplicated,
         ("Id", "词", "中文", "市场容量", "竞争产品数", "供需比", "对标覆盖数", "最佳自然排名", "自然排名中位数", "精准度", "精准原因"),
         {"Report_Key": "UNIQUE_HIGH_PRECISION_KEYWORDS"}),
    ]
    for asset, identity, asset_rows, schema, extra in definitions:
        metadata = {
            "Report_Identity": identity, "Skill_ID": "hzp-amz-6-0-2-ai-precision-keyword-identification",
            "Product_Code": "TEST", "RUN_ID": f"602-{stamp}", "RUN_TIMESTAMP": stamp,
            "Run_Status": "FULL_SUCCESS", "Schema": list(schema), "Record_Count": len(asset_rows),
            "Output_Assets": [str(path) for path in all_paths], **extra,
        }
        write_metadata_sidecar(asset, metadata)
    for product_id, asset in paths["benchmarks"].items():
        asset_rows = [row for row in observations if row["所属产品编号"] == product_id]
        metadata = {
            "Report_Identity": "BENCHMARK_HIGH_PRECISION_KEYWORDS", "Benchmark_Product_Code": product_id,
            "Skill_ID": "hzp-amz-6-0-2-ai-precision-keyword-identification", "Product_Code": "TEST",
            "RUN_ID": f"602-{stamp}", "RUN_TIMESTAMP": stamp, "Run_Status": "FULL_SUCCESS",
            "Schema": list(oa.INPUT_602_COLUMNS), "Record_Count": len(asset_rows),
            "Output_Assets": [str(path) for path in all_paths],
        }
        write_metadata_sidecar(asset, metadata)
    return folder
def make_603_package(
    root: Path, stamp: str, intents: list[dict[str, object]], mapping: list[dict[str, object]],
    *, declared_stamp: str | None = None, status: str = "VALID",
) -> Path:
    folder = root / "06_SKILL分析报告" / oa.INPUT_603_ROOT
    folder.mkdir(parents=True, exist_ok=True)
    file_stamp = declared_stamp or stamp
    summary_name = f"6-0-3_TEST_精准泛词汇总_{file_stamp}.csv"
    mapping_name = f"6-0-3_TEST_词对应的精准泛词_{file_stamp}.csv"
    write_csv(folder / summary_name, oa.INPUT_603_SUMMARY_COLUMNS, intents)
    write_csv(folder / mapping_name, oa.INPUT_603_MAPPING_COLUMNS, mapping)
    (folder / f"{oa.RUN_MANIFEST_PREFIX}{stamp}.json").write_text(json.dumps({
        "SkillId": "hzp-amz-6-0-3-precision-broad-extraction",
        "Current Product": "TEST", "RUN_ID": stamp, "RUN_TIMESTAMP": stamp,
        "GeneratedAt": "2026-09-16T12:01:00+08:00",
        "Input Skill": "hzp-amz-6-0-2-ai-precision-keyword-identification",
        "Input Run ID": "602-run", "Input RUN_TIMESTAMP": "20260916_090000",
        "Input Folder": str(root / "06_SKILL分析报告" / "6-0-2_AI精准关键词识别"),
        "Input File": str(root / "06_SKILL分析报告" / "6-0-2_AI精准关键词识别" / "6-0-2_去对标去重 高度精准词_20260916_090000.csv"),
        "Input Record Count": len(mapping), "Output Folder": str(folder),
        "Output Files": [summary_name, mapping_name],
        "Output Record Counts": {"Intent Count": len(intents), "Keyword Count": len(mapping)},
        "Run Status": status,
    }, ensure_ascii=False), encoding="utf-8")
    return folder


def make_judgments(prepared: dict[str, object], *, multi_grade: str = "高共识") -> dict[str, object]:
    details = prepared["detail_evidence"]
    intents = {row["精准泛词"] for row in details}
    codes = {row["对标编码"] for row in details}
    return {
        "individual": [
            {"benchmark_code": code, "intent": intent, "grade": "强占领", "reason": "已计算的头部覆盖支持明显自然占领。"}
            for code in codes for intent in intents
        ],
        "consensus": [
            {"intent": intent, "grade": multi_grade, "reason": "依据程序输出的多对标覆盖与中位数判断。"}
            for intent in intents
        ],
    }


def save_judgments(folder: Path, value: dict[str, object]) -> Path:
    path = folder / "ai_judgments.json"
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def setup_product(tmp_path: Path, *, stamps: tuple[str, str] = ("20260916_120000", "20260916_120100")) -> Path:
    root = tmp_path / "product"
    root.mkdir()
    summaries = [summary_row("All", 30000, direct=20000), summary_row("Child", 10000, "All", "L2")]
    mappings = [mapping_row("a", "cat intent", 10000, "Child"), mapping_row("b", "general intent", 20000, "All")]
    rows = [
        observation("a", "cat intent", 10000, "BEN-A", 3),
        observation("b", "general intent", 20000, "BEN-A", 15),
        observation("a", "cat intent", 10000, "BEN-B", 18),
        observation("b", "general intent", 20000, "BEN-B", 30),
    ]
    make_602_package(root, stamps[0], rows)
    make_603_package(root, stamps[1], summaries, mappings)
    return root


def test_case_a_single_benchmark_forces_single_mode(tmp_path: Path) -> None:
    root = tmp_path / "product"
    root.mkdir()
    make_602_package(root, "20260916_120000", [observation("x", "single", 20000, "ONE", 2)])
    make_603_package(root, "20260916_120100", [summary_row("Intent", 20000)], [mapping_row("x", "single", 20000, "Intent")])
    prepared = oa.prepare_run(root, "TEST", "20260916_120200")
    result = oa.finalize_run(root, "TEST", "20260916_120200", save_judgments(
        Path(prepared["run_folder"]), make_judgments(prepared),
    ))
    rows = oa._read_output_csv(Path(result["run_folder"]) / f"意图多对标占领共识_20260916_120200.csv", oa.CONSENSUS_COLUMNS)
    assert rows[0]["多对标共识等级"] == "单对标模式"


def test_case_b_capacity_is_independent_per_benchmark(tmp_path: Path) -> None:
    root = tmp_path / "product"
    root.mkdir()
    rows = [
        observation("x", "one query", 20000, "A", 3),
        observation("x", "one query", 20000, "B", 18),
        observation("x", "one query", 20000, "C", 76),
    ]
    make_602_package(root, "20260916_120000", rows)
    make_603_package(root, "20260916_120100", [summary_row("Intent", 20000)], [mapping_row("x", "one query", 20000, "Intent")])
    prepared = oa.prepare_run(root, "TEST", "20260916_120200")
    by_code = {row["对标编码"]: row for row in prepared["detail_evidence"]}
    assert by_code["A"]["Top20占领搜索量"] == "20000"
    assert by_code["B"]["Top20占领搜索量"] == "20000"
    assert by_code["C"]["Top20占领搜索量"] == "0"
    assert all(float(row["Top20搜索量覆盖率"].rstrip("%")) <= 100 for row in by_code.values())


def test_case_c_thresholds_and_case_d_parent_subtree(tmp_path: Path) -> None:
    root = setup_product(tmp_path)
    prepared = oa.prepare_run(root, "TEST", "20260916_130000")
    rows = [row for row in prepared["detail_evidence"] if row["对标编码"] == "BEN-A"]
    parent = next(row for row in rows if row["精准泛词"] == "All")
    child = next(row for row in rows if row["精准泛词"] == "Child")
    volumes = [int(parent[f"Top{n}占领搜索量"]) for n in (10, 20, 50, 100)]
    assert volumes == sorted(volumes)
    assert volumes == [10000, 30000, 30000, 30000]
    assert child["Top100占领搜索量"] == "10000"
    assert parent["汇总搜索量"] == "30000"
    assert child["汇总搜索量"] == "10000"


def test_case_e_weighted_rank_uses_market_capacity(tmp_path: Path) -> None:
    root = tmp_path / "product"
    root.mkdir()
    observations = [
        observation("big", "big query", 9000, "A", 10),
        observation("small", "small query", 1000, "A", 90),
    ]
    make_602_package(root, "20260916_120000", observations)
    intent = summary_row("Intent", 10000)
    intent["直接对应词数"] = 2
    make_603_package(root, "20260916_120100", [intent], [
        mapping_row("big", "big query", 9000, "Intent"), mapping_row("small", "small query", 1000, "Intent"),
    ])
    prepared = oa.prepare_run(root, "TEST", "20260916_120200")
    row = prepared["detail_evidence"][0]
    assert row["平均自然排名"] == "50"
    assert row["加权自然排名"] == "18"


def test_missing_rank_and_no_observation_are_audited_without_becoming_rank_999(tmp_path: Path) -> None:
    root = tmp_path / "product"
    root.mkdir()
    rows = [
        observation("x", "first query", 10000, "A", None),
        observation("y", "second query", 20000, "A", 20),
        observation("x", "first query", 10000, "B", 10),
    ]
    make_602_package(root, "20260916_120000", rows)
    make_603_package(root, "20260916_120100", [summary_row("Intent", 30000, direct_count=2)], [
        mapping_row("x", "first query", 10000, "Intent"), mapping_row("y", "second query", 20000, "Intent"),
    ])
    prepared = oa.prepare_run(root, "TEST", "20260916_120200")
    assert prepared["missing_rank_count"] == 1
    assert prepared["no_observation_count"] == 1
    assert prepared["no_observation_audit"][0]["对标编码"] == "B"
    assert prepared["no_observation_audit"][0]["Id"] == "y"
    row_b = next(row for row in prepared["detail_evidence"] if row["对标编码"] == "B")
    assert row_b["有效排名词数"] == "1"
    assert row_b["Top10占领搜索量"] == "10000"
    judgments = make_judgments(prepared)
    for entry in judgments["individual"]:
        entry["grade"] = "中度占领"
        entry["reason"] = "按有效Rank证据判断；空排名保持未观测，不替换为999。"
    result = oa.finalize_run(
        root, "TEST", "20260916_120200",
        save_judgments(Path(prepared["run_folder"]), judgments),
    )
    run_manifest = json.loads((Path(result["run_folder"]) / f"{oa.RUN_MANIFEST_PREFIX}{result['run_timestamp']}.json").read_text(encoding="utf-8"))
    assert run_manifest["Run Status"] == "VALID"
    assert run_manifest["Validation"]["Missing Organic Rank Count"] == 1
    assert run_manifest["Validation"]["No 602 High-Precision Observation Count"] == 1


def test_invalid_nonblank_rank_blocks_run(tmp_path: Path) -> None:
    root = tmp_path / "product"
    root.mkdir()
    make_602_package(root, "20260916_120000", [observation("x", "query", 100, "A", 0)])
    make_603_package(root, "20260916_120100", [summary_row("Intent", 100)], [mapping_row("x", "query", 100, "Intent")])
    with pytest.raises(oa.ContractError, match="INVALID_ORGANIC_RANK"):
        oa.prepare_run(root, "TEST", "20260916_120200")
    manifest = json.loads(
        (root / "06_SKILL分析报告" / oa.REPORT_ROOT / f"{oa.RUN_MANIFEST_PREFIX}20260916_120200.json").read_text(encoding="utf-8")
    )
    assert manifest["Run Status"] == "FAILED"


def synthetic_detail(code: str, asin: str, intent: str, top10: str, top20: str, top50: str, rank: str, grade: str = "弱占领") -> dict[str, str]:
    return {
        "对标编码": code, "对标ASIN": asin, "精准泛词": intent, "中文": intent,
        "层级": "L1", "父精准泛词": "", "汇总搜索量": "1000", "有效排名词数": "1",
        "Top10关键词数": "1", "Top20关键词数": "1", "Top50关键词数": "1", "Top100关键词数": "1",
        "平均自然排名": rank, "加权自然排名": rank,
        "Top10占领搜索量": top10, "Top10搜索量覆盖率": top10 + ".0000%",
        "Top20占领搜索量": top20, "Top20搜索量覆盖率": top20 + ".0000%",
        "Top50占领搜索量": top50, "Top50搜索量覆盖率": top50 + ".0000%",
        "Top100占领搜索量": top50, "Top100搜索量覆盖率": top50 + ".0000%",
        "占领等级": grade, "占领判断原因": "synthetic",
    }


def test_case_f_best_benchmark_tiebreak_order() -> None:
    detail = [
        synthetic_detail("Z", "BZ", "Intent", "800", "900", "950", "1"),
        synthetic_detail("B", "BB", "Intent", "900", "900", "950", "5"),
        synthetic_detail("A", "BA", "Intent", "900", "900", "950", "5"),
    ]
    result = oa.calculate_consensus(
        detail, benchmark_count=3,
        judgments={"Intent": {"grade": "中共识", "reason": "存在重复验证。"}},
    )[0]
    assert result["最佳对标编码"] == "A"


def test_case_g_and_h_consensus_is_not_combined_share() -> None:
    detail = [
        synthetic_detail("A", "BA", "Intent", "80", "90", "95", "5", "核心占领"),
        synthetic_detail("B", "BB", "Intent", "60", "70", "80", "12", "强占领"),
    ]
    result = oa.calculate_consensus(
        detail, benchmark_count=2,
        judgments={"Intent": {"grade": "高共识", "reason": "两个对标均有头部占领证据。"}},
    )[0]
    assert result["多对标共识等级"] == "高共识"
    assert result["核心/强占领对标数"] == "2"
    assert not any("combined" in key.casefold() or "group share" in key.casefold() for key in result)
    assert float(detail[0]["Top20搜索量覆盖率"].rstrip("%")) <= 100
    assert float(detail[1]["Top20搜索量覆盖率"].rstrip("%")) <= 100


def test_cases_i_j_resolve_latest_manifest_packages_as_whole_runs(tmp_path: Path) -> None:
    root = tmp_path / "product"
    root.mkdir()
    make_602_package(root, "20260916_100000", [observation("x", "query", 100, "OLD", 1)])
    make_602_package(root, "20260916_110000", [observation("x", "query", 100, "NEW", 1)])
    make_603_package(root, "20260916_120000", [summary_row("Intent", 100)], [mapping_row("x", "query", 100, "Intent")])
    one = oa.resolve_latest_valid_602(root, "TEST")
    two = oa.resolve_latest_valid_603(root, "TEST")
    assert one["run_timestamp"] == "20260916_110000"
    assert Path(next(iter(one["files"]["benchmarks"].values()))).parent.name == oa.INPUT_602_ROOT
    assert all(Path(path).stem.endswith(one["run_timestamp"]) for path in one["files"]["benchmarks"].values())
    assert Path(two["files"]["summary"]).parent == Path(two["files"]["mapping"]).parent
    assert Path(two["files"]["summary"]).parent == root / "06_SKILL分析报告" / oa.INPUT_603_ROOT


def test_incomplete_latest_602_package_falls_back_to_older_complete_package(tmp_path: Path) -> None:
    root = tmp_path / "product"
    root.mkdir()
    make_602_package(root, "20260916_100000", [observation("x", "query", 100, "OLD", 1)])
    latest = make_602_package(root, "20260916_110000", [observation("x", "query", 100, "NEW", 1)])
    manifest = json.loads((latest / f"{oa.RUN_MANIFEST_PREFIX}20260916_110000.json").read_text(encoding="utf-8"))
    missing = latest / manifest["Expected Benchmark Files"][0]
    missing.unlink()
    missing.with_name(missing.name + ".meta.json").unlink()
    make_603_package(root, "20260916_120000", [summary_row("Intent", 100)], [mapping_row("x", "query", 100, "Intent")])
    assert oa.resolve_latest_valid_602(root, "TEST")["run_timestamp"] == "20260916_100000"
    oa.prepare_run(root, "TEST", "20260916_130000")
    run_manifest = json.loads((root / "06_SKILL分析报告" / oa.REPORT_ROOT / f"{oa.RUN_MANIFEST_PREFIX}20260916_130000.json").read_text(encoding="utf-8"))
    assert run_manifest["602 Input Timestamp"] == "20260916_100000"


def test_case_j_rejects_cross_run_603_pair(tmp_path: Path) -> None:
    root = tmp_path / "product"
    root.mkdir()
    make_602_package(root, "20260916_100000", [observation("x", "query", 100, "A", 1)])
    make_603_package(
        root, "20260916_110000", [summary_row("Intent", 100)], [mapping_row("x", "query", 100, "Intent")],
        declared_stamp="20260916_090000",
    )
    with pytest.raises(oa.ContractError, match="606_INPUT_RUN_MISMATCH"):
        oa.prepare_run(root, "TEST", "20260916_120000")


def test_cases_k_l_m_n_o_full_package_timestamp_retention_and_6_1_compatibility(tmp_path: Path) -> None:
    root = setup_product(tmp_path)
    first_stamp = "20260916_130000"
    prepared = oa.prepare_run(root, "TEST", first_stamp)
    judgments_path = save_judgments(Path(prepared["run_folder"]), make_judgments(prepared))
    finished = oa.finalize_run(root, "TEST", first_stamp, judgments_path)
    folder = Path(finished["run_folder"])
    assert folder == root / "06_SKILL分析报告" / oa.REPORT_ROOT
    assert {Path(name).stem[-15:] for name in finished["files"]} == {first_stamp}
    assert all((folder / path).is_file() for path in finished["files"])
    run_manifest = json.loads((folder / f"{oa.RUN_MANIFEST_PREFIX}{first_stamp}.json").read_text(encoding="utf-8"))
    assert run_manifest["Run Status"] == "VALID"
    assert run_manifest["602 Input Timestamp"] == "20260916_120000"
    assert run_manifest["603 Input Timestamp"] == "20260916_120100"
    assert oa.resolve_latest_valid_606(root, "TEST")["status"] == "LATEST_VALID_606_RUN_PACKAGE_READY"
    assert "fetch(" not in (folder / finished["files"][2]).read_text(encoding="utf-8")
    assert "same-run-csv-snapshot" in (folder / finished["files"][2]).read_text(encoding="utf-8")

    # A later run adds new timestamped files while preserving the prior package.
    second_stamp = "20260916_130100"
    second = oa.prepare_run(root, "TEST", second_stamp)
    second_path = save_judgments(Path(second["run_folder"]), make_judgments(second))
    oa.finalize_run(root, "TEST", second_stamp, second_path)
    assert (folder / finished["files"][0]).is_file()
    assert (Path(second["run_folder"]) / f"对标意图市场占领明细_{second_stamp}.csv").is_file()

    # A newer partial package is skipped and the previous complete package remains valid.
    incomplete_stamp = "20260916_130200"
    incomplete = folder
    (incomplete / f"{oa.RUN_MANIFEST_PREFIX}{incomplete_stamp}.json").write_text(json.dumps({
        "SkillId": oa.SKILL_ID, "Current Product": "TEST", "RUN_ID": incomplete_stamp,
        "RUN_TIMESTAMP": incomplete_stamp, "Output Folder": str(incomplete), "Output Files": [
            f"对标意图市场占领明细_{incomplete_stamp}.csv",
            f"意图多对标占领共识_{incomplete_stamp}.csv",
            f"对标意图市场占领分析报告_{incomplete_stamp}.html",
        ], "Run Status": "RUNNING",
    }, ensure_ascii=False), encoding="utf-8")
    latest = oa.resolve_latest_valid_606(root, "TEST")
    assert latest["run_timestamp"] == second_stamp
    (Path(latest["html_file"])).unlink()
    assert oa.resolve_latest_valid_606(root, "TEST")["run_timestamp"] == first_stamp

    # The existing 6-1 reader consumes the same-folder detail and consensus files.
    source = SKILL.parent / "hzp-amz-6-1-new-product-advertising-battle-plan" / "scripts" / "battle_plan.py"
    spec = importlib.util.spec_from_file_location("battle_plan_6-1_contract_test", source)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.path.insert(0, str(source.parent))
    prior_renderer = sys.modules.pop("report_renderer", None)
    prior_bytecode_setting = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = prior_bytecode_setting
        sys.path.pop(0)
        sys.modules.pop("report_renderer", None)
        if prior_renderer is not None:
            sys.modules["report_renderer"] = prior_renderer
    read_6_1 = module.resolve_latest_valid_606(root, "TEST")
    assert read_6_1["status"] == module.STATUS_606_READY
    assert Path(read_6_1["files"][0]).parent == Path(read_6_1["files"][1]).parent



