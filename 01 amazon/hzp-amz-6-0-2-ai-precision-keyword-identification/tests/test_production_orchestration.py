import csv
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("precision", ROOT / "scripts" / "dual_precision_csv.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cli_spec = importlib.util.spec_from_file_location("codex_cli_judge", ROOT / "scripts" / "codex_cli_judge.py")
cli = importlib.util.module_from_spec(cli_spec)
cli_spec.loader.exec_module(cli)
fixture_spec = importlib.util.spec_from_file_location("contract", ROOT / "tests" / "test_full_judgment_contract.py")
fixture = importlib.util.module_from_spec(fixture_spec)
fixture_spec.loader.exec_module(fixture)


def _profile():
    return {
        "Core_Product_Type": "sisterhood keepsake figurine",
        "Physical_Product_Form": "resin figurine",
        "Core_Functions": "relationship keepsake gift",
        "PrimaryPurchaseDriver": "GIFT_EMOTIONAL",
        "Target_Customer": "gift buyers",
        "Recipient": "sisters",
        "Relationship_Intent": "sisterhood",
        "Gift_Mission": "relationship keepsake",
        "Core_Purchase_Mission": "buy a sisterhood keepsake gift",
    }


def test_checkpoint_round_trip(tmp_path):
    path = tmp_path / "checkpoint.json"
    payload = {"schema": module.PRODUCTION_CHECKPOINT_SCHEMA, "records": {"J-1": {"Status": "SUCCESS"}}}
    module.save_production_checkpoint(path, payload)
    assert module.load_production_checkpoint(path)["records"]["J-1"]["Status"] == "SUCCESS"


def test_atomic_task_defaults_to_adaptive_safe_batch_candidates(tmp_path):
    assert module.DEFAULT_SAFE_BATCH_PROBES == (32, 64, 128, 256, 512)
    path = tmp_path / "checkpoint.json"
    module.save_production_checkpoint(path, {
        "schema": module.PRODUCTION_CHECKPOINT_SCHEMA,
        "TotalUniqueKeywordCount": 2,
        "records": {"J-1": {"Status": "SUCCESS"}},
    })
    status = module.get_602_production_status(tmp_path, "B2", checkpoint=path)
    assert status["PendingCount"] == 1
    assert status["NextAvailable"] is True


def test_production_queue_calibrates_and_applies_after_resume(tmp_path):
    units = [{"JudgmentItemId": f"J-{index}", "Keyword": f"keyword {index}"} for index in range(3)]
    prepared = {"keyword_units": units}
    original_prepare = module.prepare_602
    original_apply = module.run_current_602
    original_batch_config = module.read_602_batch_size
    module.prepare_602 = lambda *args, **kwargs: prepared
    module.run_current_602 = lambda *args, **kwargs: {"status": "FULL_SUCCESS"}
    module.read_602_batch_size = lambda: {"RequestedBatchSize": 1, "ConfigStatus": "OK", "ConfigPath": "test"}
    first = units[0]
    initial = {first["JudgmentItemId"]: {
        "FinalPrecision": "精准", "FinalPrecisionReason": "已验收的关系礼物意图与产品使命匹配",
        "JudgmentStatus": "SUCCESS", "ChallengeResult": "CONFIRMED",
    }}
    calls = []

    def agent(profile, batch, phase):
        calls.append((phase, len(batch)))
        if phase == "A":
            return [{"JudgmentItemId": item["JudgmentItemId"], "FinalPrecision": "不精准",
                     "FinalPrecisionReason": "合成测试中的购买意图与产品类型不匹配",
                     "JudgmentStatus": "SUCCESS", "ChallengeResult": "CONFIRMED"} for item in batch]
        return [{"JudgmentItemId": item["JudgmentItemId"], "BenchmarkRealityAssessment": "NEUTRAL"} for item in batch]

    try:
        result = module.run_current_602_production(
            tmp_path, "B2", product_profile=_profile(), agent_batch_judge=agent,
            initial_judgments=initial, calibration_sizes=(2, 3), resume=False,
        )
    finally:
        module.prepare_602 = original_prepare
        module.run_current_602 = original_apply
        module.read_602_batch_size = original_batch_config
    assert result["status"] == "FULL_SUCCESS"
    assert result["production_checkpoint"]
    assert result["production_batch_size"] == 3
    checkpoint = module.load_production_checkpoint(result["production_checkpoint"])
    assert len(checkpoint["records"]) == len(prepared["keyword_units"])
    assert all(size in {2, 3} for _, size in calls)


def test_agent_pull_get_save_resume_and_finalize_gate(tmp_path):
    units = [{"JudgmentItemId": f"J-{index}", "Keyword": f"keyword {index}"} for index in range(3)]
    prepared = {"keyword_units": units}
    original_prepare = module.prepare_602
    original_apply = module.run_current_602
    original_batch_config = module.read_602_batch_size
    module.prepare_602 = lambda *args, **kwargs: prepared
    module.run_current_602 = lambda *args, **kwargs: {"status": "FULL_SUCCESS"}
    module.read_602_batch_size = lambda: {"RequestedBatchSize": 1, "ConfigStatus": "OK", "ConfigPath": "test"}
    path = tmp_path / "queue.json"
    state = {"schema": module.PRODUCTION_CHECKPOINT_SCHEMA, "Product_Code": "B2", "TotalUniqueKeywordCount": 3,
             "BrainVersion": "CURRENT_FROZEN_BRAIN", "ProductProfileId": "PROFILE", "records": {
                 "J-0": {"JudgmentItemId": "J-0", "Status": "SUCCESS", "JudgmentStatus": "SUCCESS"},
                 "J-1": {"JudgmentItemId": "J-1", "Status": "PENDING_JUDGMENT", "JudgmentStatus": "PENDING_JUDGMENT"},
                 "J-2": {"JudgmentItemId": "J-2", "Status": "PENDING_JUDGMENT", "JudgmentStatus": "PENDING_JUDGMENT"},
             }}
    module.save_production_checkpoint(path, state)
    try:
        status = module.get_602_production_status(tmp_path, "B2", checkpoint=path)
        assert status["SuccessCount"] == 1 and status["PendingCount"] == 2
        batch = module.get_next_602_batch(tmp_path, "B2", batch_size=1, checkpoint=path)
        assert [item["JudgmentItemId"] for item in batch["items"]] == ["J-1"]
        judgment = {"JudgmentItemId": "J-1", "FinalPrecision": "精准", "FinalPrecisionReason": "合成测试理由充分",
                    "JudgmentStatus": "SUCCESS", "ChallengeResult": "CONFIRMED"}
        after = module.save_602_batch_judgments(tmp_path, "B2", batch, [judgment], checkpoint=path)
        assert after["SuccessCount"] == 2 and after["PendingCount"] == 1
        next_batch = module.get_next_602_batch(tmp_path, "B2", batch_size=1, checkpoint=path)
        assert [item["JudgmentItemId"] for item in next_batch["items"]] == ["J-2"]
        assert module.finalize_602(tmp_path, "B2", checkpoint=path)["status"] == "PENDING"
    finally:
        module.prepare_602 = original_prepare
        module.run_current_602 = original_apply
        module.read_602_batch_size = original_batch_config


def test_current_batch_is_capped_by_dynamic_pending_count(tmp_path):
    units = [{"JudgmentItemId": f"J-{index}", "Keyword": f"keyword {index}"} for index in range(2)]
    original_prepare = module.prepare_602
    module.prepare_602 = lambda *args, **kwargs: {"keyword_units": units, "product_profile": {}}
    path = tmp_path / "queue.json"
    module.save_production_checkpoint(path, {
        "schema": module.PRODUCTION_CHECKPOINT_SCHEMA,
        "TotalUniqueKeywordCount": 2,
        "ProductProfileId": "PROFILE",
        "records": {item["JudgmentItemId"]: {"Status": "PENDING_JUDGMENT"} for item in units},
    })
    try:
        batch = module.get_next_602_batch(tmp_path, "B2", batch_size=512, checkpoint=path)
    finally:
        module.prepare_602 = original_prepare
    assert batch["BatchSize"] == 2
    assert len(batch["items"]) == 2


def test_next_batch_does_not_reuse_stale_last_batch_size(tmp_path):
    units = [{"JudgmentItemId": f"J-{index}", "Keyword": f"keyword {index}"} for index in range(40)]
    original_prepare = module.prepare_602
    module.prepare_602 = lambda *args, **kwargs: {
        "keyword_units": units,
        "product_profile": {},
        "adaptive_batch_plan": {"suggested_batch_size": 32},
    }
    path = tmp_path / "queue.json"
    module.save_production_checkpoint(path, {
        "schema": module.PRODUCTION_CHECKPOINT_SCHEMA,
        "TotalUniqueKeywordCount": len(units),
        "CurrentBatchSize": 16,
        "records": {},
    })
    try:
        batch = module.get_next_602_batch(tmp_path, "B2", checkpoint=path)
    finally:
        module.prepare_602 = original_prepare
    assert batch["BatchSize"] == 40


def test_complete_agent_entry_drains_queue_without_manual_resume(tmp_path):
    units = [{"JudgmentItemId": f"J-{index}", "Keyword": f"keyword {index}"} for index in range(3)]
    original_prepare = module.prepare_602
    original_apply = module.run_current_602
    module.prepare_602 = lambda *args, **kwargs: {
        "keyword_units": units,
        "product_profile": {},
        "product_evidence": {},
        "adaptive_batch_plan": {"suggested_batch_size": 2},
    }
    module.run_current_602 = lambda *args, **kwargs: {"status": "FULL_SUCCESS"}

    def profile(_prepared):
        return {"product_profile": _profile()}

    def batch_judge(_profile_value, batch, phase):
        if phase == "A":
            return [{"JudgmentItemId": item["JudgmentItemId"], "FinalPrecision": "精准",
                     "FinalPrecisionReason": "合成测试理由充分", "JudgmentStatus": "SUCCESS",
                     "ChallengeResult": "CONFIRMED"} for item in batch]
        return [{"JudgmentItemId": item["JudgmentItemId"], "BenchmarkRealityAssessment": "NEUTRAL"} for item in batch]

    try:
        result = module.run_current_602_agent(
            tmp_path, "B2", agent_judge=profile, agent_batch_judge=batch_judge,
            checkpoint=tmp_path / "queue.json",
        )
    finally:
        module.prepare_602 = original_prepare
        module.run_current_602 = original_apply
    assert result["status"] == "FULL_SUCCESS"
    assert result["production_checkpoint"]


def test_v4_single_entry_requires_real_ai(tmp_path):
    try:
        module.run_602(tmp_path, "B2")
    except RuntimeError as exc:
        assert str(exc) == module.AI_PRECISION_JUDGMENT_UNAVAILABLE
    else:
        raise AssertionError("V4 must fail closed when no real AI handoff exists")


def test_v4_single_entry_validates_all_unique_judgments(tmp_path):
    units = [
        {"JudgmentItemId": "J-1", "Canonical_Keyword": "sister gift", "词": "sister gift"},
        {"JudgmentItemId": "J-2", "Canonical_Keyword": "birthday gift", "词": "birthday gift"},
    ]
    prepared = {"keyword_units": units, "input_rows": [], "product_evidence": {},
                "resolved_601": {}, "benchmark_identities": {}}
    original_prepare = module.prepare_602
    original_apply = module.run_current_602
    captured = {}
    module.prepare_602 = lambda *args, **kwargs: dict(prepared)
    module.run_current_602 = lambda *args, **kwargs: captured.update(kwargs) or {"status": "FULL_SUCCESS"}
    profile = {"Core_Product_Type": "keepsake figurine", "PrimaryPurchaseDriver": "GIFT_EMOTIONAL",
               "Core_Purchase_Mission": "buy a relationship keepsake gift"}

    def judge(_prepared):
        return {"product_profile": profile, "judgments": [
            {"JudgmentItemId": item["JudgmentItemId"], "FinalPrecision": "精准",
             "FinalPrecisionReason": "该词表达关系礼物购买任务，产品使命直接匹配",
             "JudgmentStatus": "SUCCESS", "ChallengeResult": "CONFIRMED",
             "BenchmarkRealityAssessment": "NEUTRAL"}
            for item in units
        ]}

    try:
        result = module.run_602(tmp_path, "B2", ai_judge=judge)
    finally:
        module.prepare_602 = original_prepare
        module.run_current_602 = original_apply
    assert result["status"] == "FULL_SUCCESS"
    assert result["execution_mode"] == "V4_COMPLETE_602_TASK"
    assert len(captured["agent_judgments"]) == 2
    assert set(captured["agent_judgments"]) == {"sister gift", "birthday gift"}


def test_v4_single_entry_rejects_partial_unique_coverage(tmp_path):
    units = [{"JudgmentItemId": "J-1", "Canonical_Keyword": "one", "词": "one"},
             {"JudgmentItemId": "J-2", "Canonical_Keyword": "two", "词": "two"}]
    original_prepare = module.prepare_602
    module.prepare_602 = lambda *args, **kwargs: {"keyword_units": units}
    try:
        try:
            module.run_602(tmp_path, "B2", ai_judge=lambda _: {
                "product_profile": {"Core_Product_Type": "item", "PrimaryPurchaseDriver": "FUNCTIONAL",
                                     "Core_Purchase_Mission": "buy item"},
                "judgments": [{"JudgmentItemId": "J-1", "FinalPrecision": "精准",
                               "FinalPrecisionReason": "合成测试的购买意图与产品使命匹配",
                               "JudgmentStatus": "SUCCESS", "ChallengeResult": "CONFIRMED"}],
            })
        except ValueError as exc:
            assert str(exc) == "STRUCTURED_JUDGMENT_COVERAGE_FAILED"
        else:
            raise AssertionError("V4 must reject a partial Unique Keyword result")
    finally:
        module.prepare_602 = original_prepare


def test_v4_audits_v3_checkpoint_without_mixing(tmp_path):
    path = tmp_path / "legacy.json"
    module.save_production_checkpoint(path, {"schema": module.PRODUCTION_CHECKPOINT_SCHEMA,
        "TotalUniqueKeywordCount": 2, "ProductProfileId": "P", "BrainVersion": "CURRENT_FROZEN_BRAIN", "records": {}})
    audit = module.audit_legacy_checkpoint(path)
    assert audit["status"] == "LEGACY_CHECKPOINT_INCOMPATIBLE"


def test_codex_cli_worker_drains_two_batches_without_user_resume(tmp_path):
    units = [{"JudgmentItemId": f"J-{index}", "Canonical_Keyword": f"keyword {index}",
              "词": f"keyword {index}", "Keyword": f"keyword {index}"} for index in range(3)]
    prepared = {"keyword_units": units, "input_rows": [], "product_evidence": {"product_text": "keepsake gift"},
                "product_evidence_package": {"content_sha256": "PROFILE"}, "resolved_601": {},
                "benchmark_identities": {}}
    original_prepare = module.prepare_602
    original_apply = module.run_current_602
    original_version = module.codex_version
    original_login = module.codex_login_status
    original_cli = module.run_codex_cli_judge
    original_batch_config = module.read_602_batch_size
    module.prepare_602 = lambda *args, **kwargs: dict(prepared)
    module.run_current_602 = lambda *args, **kwargs: {"status": "FULL_SUCCESS"}
    module.codex_version = lambda: "codex-cli test"
    module.codex_login_status = lambda: "Logged in using ChatGPT"
    calls = []

    def cli(payload, **kwargs):
        calls.append(payload["BatchId"])
        return {"BatchId": payload["BatchId"], "ProductProfileId": "PROFILE",
                "BrainVersion": "CURRENT_FROZEN_BRAIN", "Judgments": [
                    {"JudgmentItemId": item["JudgmentItemId"], "FinalPrecision": "精准",
                     "JudgmentStatus": "SUCCESS", "ReasonCode": "FIT",
                     "ShortReason": "合成测试购买意图与产品使命匹配",
                     "HardConflictType": "NONE", "BenchmarkRealityAssessment": "NEUTRAL",
                     "ChallengeResult": "CONFIRMED"}
                    for item in payload["Judgments"]]}

    module.run_codex_cli_judge = cli
    module.read_602_batch_size = lambda: {"RequestedBatchSize": 2, "ConfigStatus": "OK", "ConfigPath": "test"}
    checkpoint = tmp_path / "cli.json"
    try:
        result = module.run_codex_cli_production(tmp_path, "B2", checkpoint=checkpoint, initial_batch_size=2)
    finally:
        module.prepare_602 = original_prepare
        module.run_current_602 = original_apply
        module.codex_version = original_version
        module.codex_login_status = original_login
        module.run_codex_cli_judge = original_cli
        module.read_602_batch_size = original_batch_config
    assert result["status"] == "FULL_SUCCESS"
    assert len(calls) == 2
    state = module.load_production_checkpoint(checkpoint)
    assert all(record.get("Status") == "SUCCESS" for record in state["records"].values())


def test_codex_cli_adapter_uses_stdin_schema_and_output_file(tmp_path, monkeypatch):
    schema = tmp_path / "schema.json"
    schema.write_text("{}", encoding="utf-8")
    observed = {}

    def fake_run(args, **kwargs):
        observed["args"] = args
        observed["input"] = kwargs["input"]
        output = Path(args[args.index("--output-last-message") + 1])
        output.write_text(json.dumps({"BatchId": "B-1"}), encoding="utf-8")
        return type("Completed", (), {"returncode": 0, "stdout": "{}\n", "stderr": ""})()

    monkeypatch.setattr(cli.subprocess, "run", fake_run)
    result = cli.run_codex_cli_judge({"hello": "structured"}, schema_path=schema, timeout=1)
    assert result["BatchId"] == "B-1"
    args = observed["args"]
    assert args
    assert args[:3] == [cli.codex_executable(), "exec", "-"]
    assert "--json" in args and "--output-schema" in args and "--ephemeral" in args
    assert "-a" not in args
    assert json.loads(observed["input"])["hello"] == "structured"


def test_batch_size_config_missing_and_invalid_use_safe_default(tmp_path):
    missing = module.read_602_batch_size(tmp_path / "missing.txt")
    assert missing["RequestedBatchSize"] is None
    assert missing["ConfigStatus"] == "602_BATCH_SIZE_CONFIG_MISSING"
    invalid_path = tmp_path / "invalid.txt"
    invalid_path.write_text("abc", encoding="utf-8")
    invalid = module.read_602_batch_size(invalid_path)
    assert invalid["RequestedBatchSize"] is None
    assert invalid["ConfigStatus"] == "602_BATCH_SIZE_CONFIG_INVALID"


def test_batch_size_config_reads_positive_integer(tmp_path):
    path = tmp_path / "batch.txt"
    path.write_text("512\n", encoding="utf-8")
    result = module.read_602_batch_size(path)
    assert result["RequestedBatchSize"] == 512
    assert result["ConfigStatus"] == "OK"
