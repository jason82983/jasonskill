from pathlib import Path
import json
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
README = (ROOT / "README.md").read_text(encoding="utf-8-sig")
REF = (ROOT / "references" / "broad-seed-cluster-v1.md").read_text(encoding="utf-8-sig")
spec = importlib.util.spec_from_file_location("broad", ROOT / "scripts" / "broad_seed_cluster.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def write_602_package(root, stamp="20260916_184400"):
    source = [{
        "Id": "1", "词": "sister gifts", "中文": "姐妹礼物", "市场容量": "100",
        "竞争产品数": "10", "供需比": "10.0000", "对标覆盖数": "1",
        "最佳自然排名": "1", "自然排名中位数": "1", "精准度": "高度精准",
        "精准原因": "符合当前产品的明确购买意图",
    }]
    paths = module.input_paths(root, "B2", stamp)
    paths["ai"].parent.mkdir(parents=True, exist_ok=True)
    benchmark_path = paths["ai"].parent / f"6-0-2_BM-1_高度精准词_{stamp}.csv"
    paths["benchmarks"] = {"BM-1": benchmark_path}
    all_paths = [paths[key] for key in ("ai", "high_precision", "deduplicated",)] + [benchmark_path]
    observation = {
        "所属产品编号": "BM-1", "对标ASIN": "ASIN-1", "Id": "1", "词": "sister gifts",
        "中文": "姐妹礼物", "市场容量": "100", "竞争产品数": "10", "供需比": "10.0000",
        "自然排名": "1", "精准度": "高度精准", "精准原因": "符合当前产品的明确购买意图",
    }
    module.write_csv(paths["ai"], [observation], module.OBSERVATION_COLUMNS)
    module.write_csv(paths["high_precision"], [observation], module.OBSERVATION_COLUMNS)
    module.write_csv(paths["deduplicated"], source, module.INPUT_COLUMNS)
    module.write_csv(benchmark_path, [observation], module.OBSERVATION_COLUMNS)
    manifest = {
        "SkillId": "hzp-amz-6-0-2-ai-precision-keyword-identification",
        "Current Product": "B2", "RUN_ID": stamp, "RUN_TIMESTAMP": stamp,
        "GeneratedAt": "2026-09-16T18:44:00+08:00", "Input Source": "test",
        "Input Skill": "hzp-amz-6-0-1-benchmark-organic-keyword-extraction",
        "Input Run ID": "601-test", "Input RUN_TIMESTAMP": "20260916_170000",
        "Input Folder": str(root / "601"), "Input File": str(root / "601" / "source.csv"),
        "Product Text Input": {"path": str(root / "product.txt"), "size_bytes": 1, "sha256": "abc"},
        "Input Record Count": 1, "Input Observation Count": 1, "Input Unique Keyword Count": 1,
        "Output Folder": str(paths["ai"].parent), "Output Files": [path.name for path in all_paths],
        "Benchmark Count": 1, "Expected Benchmark Count": 1,
        "Benchmark Product Codes": ["BM-1"],
        "Benchmark Identities": {"BM-1": {"对标编码": "CODE-1", "对标ASIN": "ASIN-1"}},
        "PerBenchmarkInputObservationCount": {"BM-1": 1},
        "PerBenchmarkHighPrecisionRecordCount": {"BM-1": 1},
        "Expected Benchmark Files": [benchmark_path.name], "GeneratedBenchmarkFiles": [benchmark_path.name],
        "Record Counts": {"Input Record Count": 1, "Input Observation Count": 1,
                          "Input Unique Keyword Count": 1, "AI Record Count": 1,
                          "High Precision Record Count": 1, "Unique High Precision Keyword Count": 1,
                          "Benchmark File Count": 1},
        "Output Record Counts": {"AI Precision Observation Count": 1,
                                 "High Precision Observation Count": 1,
                                 "Unique High Precision Keyword Count": 1, "Benchmark File Count": 1},
        "Run Status": "VALID",
    }
    (paths["ai"].parent / f"{module.INPUT_602_MANIFEST_PREFIX}{stamp}.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return paths


def test_identity_and_input_boundary():
    assert "hzp-amz-6-0-3-precision-broad-extraction" in SKILL
    assert "UNIQUE_HIGH_PRECISION_KEYWORDS" in SKILL
    assert "Report Identity" in SKILL
    assert "603_INPUT_NOT_ALL_HIGH_PRECISION" in SKILL
    assert "603_INPUT_DUPLICATE_KEYWORD" in SKILL
    assert "falls back over failed/incomplete runs" in README
    assert "精准判断所有词表" in README and "高度精准词表" in README
    assert "去对标去重 高度精准词" in README
    assert module.DEDUPLICATED_NAME.endswith(".csv")
    assert module.INPUT_REPORT_IDENTITY == "去对标去重 高度精准词"
    assert module.INPUT_REPORT_KEY == "UNIQUE_HIGH_PRECISION_KEYWORDS"
    assert "所属产品编号" not in module.INPUT_COLUMNS
    assert module.INPUT_RUN_DIR == "6-0-2_AI精准关键词识别"
    assert callable(module.resolve_latest_valid_602_run_package)


def test_two_output_contract():
    assert "Nine columns" in SKILL
    assert len(module.MAPPING_COLUMNS) == 9
    assert len(module.SUMMARY_COLUMNS) == 9
    assert module.MAPPING_COLUMNS[4:6] == ("竞争产品数", "供需比")
    assert module.SUMMARY_COLUMNS[6:8] == ("平均竞品数", "意图机会比")
    assert "意图机会比" in SKILL
    assert "SUM" in SKILL and "COUNT" in SKILL
    assert "average of child averages" in SKILL.lower()
    assert "after readback" in SKILL
    assert "not aggregated or used to recalculate any 6-0-3 metric" not in SKILL
    assert "Coverage" in REF and "Aggregation Consistency" in REF
    assert "PARENT_CYCLE_DETECTED" in REF


def test_timestamped_run_packages_latest_valid_and_preserved_history(tmp_path):
    assert module.format_run_timestamp(module.datetime(2026, 9, 16, 18, 44, 0)) == "20260916_184400"
    write_602_package(tmp_path)
    mapper = lambda record: {"精准泛词": "sister gifts", "精准泛词中文": "姐妹礼物"}
    older = module.run(tmp_path, "B2", mapper, generated_at="20260916_160000")
    newer = module.run(tmp_path, "B2", mapper, generated_at="20260916_160000")
    assert Path(older["run_folder"]) == module.output_root(tmp_path)
    assert Path(newer["run_folder"]) == module.output_root(tmp_path)
    assert Path(older["mapping"]).name == "6-0-3_B2_词对应的精准泛词_20260916_160000.csv"
    assert Path(older["summary"]).name == "6-0-3_B2_精准泛词汇总_20260916_160000.csv"
    for result in (older, newer):
        folder = Path(result["run_folder"])
        paths = [Path(result["summary"]), Path(result["mapping"])]
        assert all(path.parent == folder for path in paths)
        assert all(path.stem.endswith(f"_{result['run_timestamp']}") for path in paths)
        assert Path(result["run_manifest"]).is_file()
    assert Path(older["mapping"]).is_file() and Path(older["summary"]).is_file()
    assert len(list(module.output_root(tmp_path).glob("*20260916_160000.csv"))) == 2
    assert len(list(module.output_root(tmp_path).glob("*20260916_160001.csv"))) == 2
    latest = module.resolve_latest_valid_603_run_package(tmp_path, "B2")
    assert latest["status"] == "LATEST_VALID_603_RUN_PACKAGE_READY"
    assert latest["run_timestamp"] == "20260916_160001"
    assert module.latest_output_paths(tmp_path, "B2") == {"mapping": Path(newer["mapping"]), "summary": Path(newer["summary"])}

    failed_stamp = "20260916_160002"
    failed_folder = module.create_run_folder(tmp_path, failed_stamp)
    failed_paths = module.output_paths(tmp_path, "B2", failed_stamp)
    module.write_csv(failed_paths["summary"], [], module.SUMMARY_COLUMNS)
    failed_manifest = json.loads(Path(newer["run_manifest"]).read_text(encoding="utf-8"))
    failed_manifest.update({"RUN_ID": failed_stamp, "RUN_TIMESTAMP": failed_stamp, "Output Folder": str(failed_folder), "Output Files": [failed_paths["summary"].name, failed_paths["mapping"].name], "Run Status": "VALID"})
    module.write_run_manifest(failed_folder, failed_manifest)
    latest = module.resolve_latest_valid_603_run_package(tmp_path, "B2")
    assert latest["run_timestamp"] == "20260916_160001"


if __name__ == "__main__":
    test_identity_and_input_boundary()
    test_two_output_contract()
    print("6-0-3 contract tests: PASS")
