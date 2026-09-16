from pathlib import Path
import importlib.util

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
README = (ROOT / "README.md").read_text(encoding="utf-8-sig")
REF = (ROOT / "references" / "broad-seed-cluster-v1.md").read_text(encoding="utf-8-sig")
spec = importlib.util.spec_from_file_location("broad", ROOT / "scripts" / "broad_seed_cluster.py")
module = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(module)


def test_identity_and_input_boundary():
    assert "hzp-amz-6-0-3-precision-broad-extraction" in SKILL
    assert "HIGH_PRECISION_KEYWORDS" in SKILL
    assert "Report Identity" in SKILL
    assert "NON_HIGH_PRECISION_RECORD_IN_603_INPUT" in SKILL
    assert "唯一 KwId" in README
    assert module.HIGH_PRECISION_NAME.startswith("6-0-2_")


def test_two_output_contract():
    assert "Eleven columns" in SKILL
    assert len(module.MAPPING_COLUMNS) == 11
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


def test_timestamped_outputs_and_latest_pair(tmp_path):
    older = module.output_paths(tmp_path, "B2", generated_at="20260915_160000")
    newer = module.output_paths(tmp_path, "B2", generated_at="20260915_170000")
    assert older["mapping"].name.endswith("_20260915_160000.csv")
    assert older["summary"].name.endswith("_20260915_160000.csv")
    module.write_csv(older["mapping"], [], module.MAPPING_COLUMNS)
    module.write_csv(older["summary"], [], module.SUMMARY_COLUMNS)
    module.write_csv(newer["mapping"], [], module.MAPPING_COLUMNS)
    assert module.latest_output_paths(tmp_path, "B2") == older
    module.write_csv(newer["summary"], [], module.SUMMARY_COLUMNS)
    assert module.latest_output_paths(tmp_path, "B2") == newer


def test_latest_pair_supports_exact_fixed_legacy_names_only_as_fallback(tmp_path):
    directory = tmp_path / "06_SKILL分析报告" / module.OUTPUT_DIR
    legacy = {
        "mapping": directory / f"{module.MAPPING_STEM.format(product_code='B2')}.csv",
        "summary": directory / f"{module.SUMMARY_STEM.format(product_code='B2')}.csv",
    }
    for key, path in legacy.items():
        columns = module.MAPPING_COLUMNS if key == "mapping" else module.SUMMARY_COLUMNS
        module.write_csv(path, [], columns)
    assert module.latest_output_paths(tmp_path, "B2") == legacy


if __name__ == "__main__":
    test_identity_and_input_boundary()
    test_two_output_contract()
    print("6-0-3 contract tests: PASS")
