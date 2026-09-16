from datetime import datetime
import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import stage6_artifact_contract as stage6


def _csv(path: Path, columns=("Id", "词"), rows=(("1", "keyword"),)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows(rows)
    return path


def _meta(path: Path, *, stamp: str, status="FULL_SUCCESS", product="B2", identity="KEYWORDS", run_id=None):
    context = stage6.new_run_context(
        "6-0-1", "hzp-amz-6-0-1-benchmark-organic-keyword-extraction", product,
        now=datetime.strptime(stamp, "%Y%m%d_%H%M%S").astimezone(),
    )
    metadata = stage6.make_artifact_metadata(
        context, identity, run_status=status, schema=("Id", "词"), record_count=1,
    )
    if run_id:
        metadata["RUN_ID"] = run_id
    stage6.write_metadata_sidecar(path, metadata)


class Stage6ArtifactContractTests(unittest.TestCase):
  def setUp(self):
    self._tmp = tempfile.TemporaryDirectory()
    self.tmp_path = Path(self._tmp.name)

  def tearDown(self):
    self._tmp.cleanup()

  def test_run_context_and_multiple_outputs_share_one_timestamp(self):
    now = datetime(2026, 9, 16, 15, 8, 30).astimezone()
    context = stage6.new_run_context("6-0-2", "skill-id", "B2", now=now)
    a = stage6.timestamped_output_path(self.tmp_path, "6-0-2", "B2", "AI精准词", "csv", context.run_timestamp)
    b = stage6.timestamped_output_path(self.tmp_path, "6-0-2", "B2", "AI高度精准词", ".csv", context.run_timestamp)
    self.assertEqual(context.run_timestamp, "20260916_150830")
    self.assertEqual(context.run_id, "6-0-2_B2_20260916_150830")
    self.assertTrue(a.name.endswith("_20260916_150830.csv"))
    self.assertTrue(b.name.endswith("_20260916_150830.csv"))


  def test_manifest_generated_at_has_priority_over_filename_time(self):
    product_root = self.tmp_path / "B2"
    path = _csv(product_root / "6-0-1_B2_Keywords_20260916_160000.csv")
    _meta(path, stamp="20260916_140000")
    result = stage6.resolve_latest_valid_report(
        product_root, "hzp-amz-6-0-1-benchmark-organic-keyword-extraction", "KEYWORDS", [path],
        product_code="B2", required_schema=("Id", "词"),
        now=datetime(2026, 9, 16, 17, 0).astimezone(),
    )
    self.assertEqual(result["status"], "LATEST_VALID_REPORT_RESOLVED")
    self.assertTrue(result["generated_at"].startswith("2026-09-16T14:00:00"))
    self.assertEqual(result["input_resolution_method"], "LATEST_VALID_REPORT")


  def test_invalid_latest_falls_back_and_reports_reason(self):
    product_root = self.tmp_path / "B2"
    older = _csv(product_root / "6-0-1_B2_Keywords_20260916_140000.csv")
    newer = _csv(product_root / "6-0-1_B2_Keywords_20260916_150000.csv")
    _meta(older, stamp="20260916_140000")
    _meta(newer, stamp="20260916_150000", status="INCOMPLETE")
    result = stage6.resolve_latest_valid_report(
        product_root, "hzp-amz-6-0-1-benchmark-organic-keyword-extraction", "KEYWORDS", [older, newer],
        product_code="B2", required_schema=("Id", "词"),
        now=datetime(2026, 9, 16, 16, 0).astimezone(),
    )
    self.assertEqual(result["file"], str(older))
    self.assertEqual(result["input_resolution_method"], "LATEST_INVALID_FALLBACK_USED")
    self.assertEqual(result["skipped_candidates"][0]["reason"], "RUN_STATUS_NOT_CONSUMABLE")


  def test_product_identity_schema_and_future_timestamp_are_gates(self):
    product_root = self.tmp_path / "B2"
    wrong_product = _csv(product_root / "A3_Keywords_20260916_150000.csv")
    _meta(wrong_product, stamp="20260916_150000", product="A3")
    bad_schema = _csv(product_root / "B2_Keywords_20260916_140000.csv", columns=("Id", "wrong"))
    future = _csv(product_root / "B2_Keywords_20260917_140000.csv")
    result = stage6.resolve_latest_valid_report(
        product_root, "hzp-amz-6-0-1-benchmark-organic-keyword-extraction", "KEYWORDS",
        [wrong_product, bad_schema, future], product_code="B2", required_schema=("Id", "词"),
        now=datetime(2026, 9, 16, 16, 0).astimezone(),
    )
    self.assertEqual(result["status"], "NO_VALID_UPSTREAM_REPORT")
    reasons = {Path(item["path"]).name: item["reason"] for item in result["skipped_candidates"]}
    self.assertEqual(reasons[wrong_product.name], "PRODUCT_CODE_MISMATCH")
    self.assertEqual(reasons[bad_schema.name], "SCHEMA_MISMATCH")
    self.assertEqual(reasons[future.name], "FUTURE_TIMESTAMP_DETECTED")


  def test_bundle_requires_same_run_and_chooses_latest_complete_pair(self):
    product_root = self.tmp_path / "B2"
    a_old = _csv(product_root / "A_20260916_140000.csv")
    b_old = _csv(product_root / "B_20260916_140000.csv")
    a_new = _csv(product_root / "A_20260916_150000.csv")
    b_new_wrong_run = _csv(product_root / "B_20260916_150000.csv")
    _meta(a_old, stamp="20260916_140000", identity="ASSET_A", run_id="run-1400")
    _meta(b_old, stamp="20260916_140000", identity="ASSET_B", run_id="run-1400")
    _meta(a_new, stamp="20260916_150000", identity="ASSET_A", run_id="run-1500")
    _meta(b_new_wrong_run, stamp="20260916_150000", identity="ASSET_B", run_id="run-other")
    result = stage6.resolve_latest_valid_bundle(
        product_root, "hzp-amz-6-0-1-benchmark-organic-keyword-extraction",
        {"a": [a_old, a_new], "b": [b_old, b_new_wrong_run]},
        product_code="B2", report_identities={"a": "ASSET_A", "b": "ASSET_B"},
        required_schemas={"a": ("Id", "词"), "b": ("Id", "词")},
        now=datetime(2026, 9, 16, 16, 0).astimezone(),
    )
    self.assertEqual(result["status"], "LATEST_VALID_RUN_BUNDLE_RESOLVED")
    self.assertEqual(result["run_id"], "run-1400")
    self.assertEqual(result["assets"]["a"]["file"], str(a_old))
    self.assertEqual(result["assets"]["b"]["file"], str(b_old))


  def test_legacy_single_timestamp_fallback_and_no_mtime_selection(self):
    product_root = self.tmp_path / "B2"
    first = _csv(product_root / "legacy_20260916_140000.csv")
    second = _csv(product_root / "legacy_20260916_150000.csv")
    # Deliberately invert filesystem times: report-name time is authoritative.
    import os
    os.utime(first, (1_800_000_000, 1_800_000_000))
    os.utime(second, (1_700_000_000, 1_700_000_000))
    result = stage6.resolve_latest_valid_report(
        product_root, "hzp-amz-6-0-1-benchmark-organic-keyword-extraction", "KEYWORDS", [first, second],
        product_code="B2", required_schema=("Id", "词"),
        now=datetime(2026, 9, 16, 16, 0).astimezone(),
    )
    self.assertEqual(result["file"], str(second))
    self.assertEqual(result["input_resolution_method"], "FILENAME_TIMESTAMP_FALLBACK")

  def test_fixed_legacy_fallback_is_used_when_newer_timestamped_asset_is_invalid(self):
    product_root = self.tmp_path / "B2"
    legacy = _csv(product_root / "6-0-1_B2_Keywords.csv")
    invalid = _csv(product_root / "6-0-1_B2_Keywords_20260916_150000.csv", columns=("Id", "wrong"))
    result = stage6.resolve_latest_valid_report(
        product_root, "hzp-amz-6-0-1-benchmark-organic-keyword-extraction", "KEYWORDS",
        [legacy, invalid], product_code="B2", required_schema=("Id", "词"),
        now=datetime(2026, 9, 16, 16, 0).astimezone(),
    )
    self.assertEqual(result["file"], str(legacy))
    self.assertEqual(result["input_resolution_method"], "LATEST_INVALID_FALLBACK_USED")

  def test_bundle_requires_same_run_id_and_timestamp(self):
    product_root = self.tmp_path / "B2"
    a = _csv(product_root / "A_20260916_150000.csv")
    b = _csv(product_root / "B_20260916_150000.csv")
    _meta(a, stamp="20260916_150000", identity="ASSET_A", run_id="same-run")
    _meta(b, stamp="20260916_150000", identity="ASSET_B", run_id="same-run")
    # A matching RUN_ID alone is insufficient if run timestamps differ.
    sidecar = stage6.metadata_sidecar_path(b)
    payload = json.loads(sidecar.read_text(encoding="utf-8"))
    payload["RUN_TIMESTAMP"] = "20260916_145959"
    sidecar.write_text(json.dumps(payload), encoding="utf-8")
    result = stage6.resolve_latest_valid_bundle(
        product_root, "hzp-amz-6-0-1-benchmark-organic-keyword-extraction",
        {"a": [a], "b": [b]}, product_code="B2",
        report_identities={"a": "ASSET_A", "b": "ASSET_B"},
        required_schemas={"a": ("Id", "词"), "b": ("Id", "词")},
        now=datetime(2026, 9, 16, 16, 0).astimezone(),
    )
    self.assertEqual(result["status"], "NO_RUN_CONSISTENT_UPSTREAM_BUNDLE")

  def test_one_run_context_names_any_number_of_outputs_identically(self):
    context = stage6.new_run_context("6-0-2", "skill-id", "B2", now=datetime(2026, 9, 16, 15, 8, 30).astimezone())
    outputs = [
        stage6.timestamped_output_path(self.tmp_path, "6-0-2", "B2", name, ext, context.run_timestamp)
        for name, ext in (("AI精准词", "csv"), ("AI高度精准词", "csv"), ("报告", "html"), ("运行清单", "json"))
    ]
    self.assertTrue(all(path.stem.endswith(context.run_timestamp) for path in outputs))


  def test_sidecar_and_outputs_fail_closed_on_overwrite(self):
    path = _csv(self.tmp_path / "asset_20260916_150000.csv")
    try:
        stage6.assert_new_outputs([path])
    except FileExistsError as exc:
        self.assertIn("OUTPUT_WOULD_OVERWRITE", str(exc))
    else:
        raise AssertionError("existing timestamped output must not be overwritten")
    metadata = {"Run_Status": "FULL_SUCCESS"}
    sidecar = stage6.write_metadata_sidecar(path, metadata)
    self.assertEqual(json.loads(sidecar.read_text(encoding="utf-8")), metadata)
    try:
        stage6.write_metadata_sidecar(path, metadata)
    except FileExistsError:
        pass
    else:
        raise AssertionError("metadata sidecar must not be overwritten")
