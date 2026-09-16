from __future__ import annotations

import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "hzp-amz-6-0-5-new-product-advertising-battle-plan" / "scripts"))
import battle_plan as bp
import scripts.new_product_battle_plan_contract as contract
from scripts.stage6_artifact_contract import make_artifact_metadata, new_run_context, write_metadata_sidecar


def fixtures(multi=True):
    summary = [
        {"精准泛词": "sister gifts", "中文": "姐妹礼物", "层级": "L1", "父精准泛词": "",
         "直接搜索量": "12000", "汇总搜索量": "50000", "平均竞品数": "900", "意图机会比": "55.55", "直接对应词数": "2"},
        {"精准泛词": "sister birthday gifts", "中文": "姐妹生日礼物", "层级": "L2", "父精准泛词": "sister gifts",
         "直接搜索量": "18000", "汇总搜索量": "18000", "平均竞品数": "350", "意图机会比": "51.42", "直接对应词数": "2"},
    ]
    rows = []
    for kwid, keyword, intent, volume in (
        ("501", "sister birthday gift necklace", "sister birthday gifts", "7800"),
        ("502", "personalized sister birthday necklace", "sister birthday gifts", "3100"),
        ("503", "sister gifts", "sister gifts", "22000"),
        ("504", "best sister gifts", "sister gifts", "4200"),
    ):
        row = {"Id": kwid, "词": keyword, "中文": "中文词", "市场容量": volume,
               "竞争产品数": "500", "供需比": "15.6"}
        if multi:
            row.update({"对标覆盖数": "3", "最佳自然排名": "8", "自然排名中位数": "12"})
        else:
            row["自然排名"] = "10"
        row.update({"精准泛词": intent, "精准泛词中文": "中文意图"})
        rows.append(row)
    return summary, rows


def decisions(rows):
    return {
        "intents": [
            {"精准泛词": "sister gifts", "作战任务": "核心", "作战优先级": "P1",
             "作战方向": "Parent core; child beachhead first", "决策原因": "虽有更大宽泛容量，意图较散；由具体生日子意图验证后扩张。",
             "控制方式": "共享", "控制原因": "当前先在Phrase验证池收集数据，独立预算会分散新品学习。"},
            {"精准泛词": "sister birthday gifts", "作战任务": "首攻", "作战优先级": "P1",
             "作战方向": "Child beachhead", "决策原因": "相较宽泛姐妹礼物，购买对象与场景更收敛；多个对标有自然排名，且对应具体突破词。",
             "控制方式": "独立", "控制原因": "首攻需要隔离预算并独立观察该意图的转化与排名推动。"},
        ],
        "keywords": [
            {"Id": "501", "精准泛词": "sister birthday gifts", "作战任务": "首攻", "当前状态": "首攻", "新品期是否投放": "是", "计划阶段": "PHASE_1", "计划投放方式": "EXACT", "启动条件": "", "暂不投放原因": "", "作战目的": "验证具体生日购买意图的核心词转化。"},
            {"Id": "502", "精准泛词": "sister birthday gifts", "作战任务": "首攻", "当前状态": "首攻", "新品期是否投放": "是", "计划阶段": "PHASE_1", "计划投放方式": "EXACT", "启动条件": "", "暂不投放原因": "", "作战目的": "检验个性化属性能否形成细分突破。"},
            {"Id": "503", "精准泛词": "sister gifts", "作战任务": "核心", "当前状态": "待扩张", "新品期是否投放": "是", "计划阶段": "PHASE_2", "计划投放方式": "EXACT", "启动条件": "生日子意图首攻验证通过后", "暂不投放原因": "", "作战目的": "扩展到Parent Core。"},
            {"Id": "504", "精准泛词": "sister gifts", "作战任务": "核心", "当前状态": "储备", "新品期是否投放": "否", "计划阶段": "HOLD", "计划投放方式": "", "启动条件": "", "暂不投放原因": "先验证更具体的子意图，避免首期预算分散。", "控制方式": "不投", "控制原因": "本期暂缓该词，不进入当前执行结构。", "作战目的": ""},
        ],
    }


def write_input_bundle(root: Path, multi=True, same_run=True):
    summary, mapping = fixtures(multi)
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S")
    context = new_run_context("6-0-3", "hzp-amz-6-0-3-precision-broad-extraction", "B2")
    directory = root / "06_SKILL分析报告" / "6-0-3_精准泛词提取"
    directory.mkdir(parents=True)
    paths = {
        "summary": directory / f"6-0-3_B2_精准泛词汇总_{stamp}.csv",
        "mapping": directory / f"6-0-3_B2_词对应的精准泛词_{stamp if same_run else '20200101_000001'}.csv",
    }
    schemas = {"summary": contract.SUMMARY_COLUMNS,
               "mapping": contract.MAPPING_MULTI_COLUMNS if multi else contract.MAPPING_SINGLE_COLUMNS}
    data = {"summary": summary, "mapping": mapping}
    for asset, path in paths.items():
        with path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=schemas[asset]); writer.writeheader(); writer.writerows(data[asset])
        meta = make_artifact_metadata(context, contract.SUMMARY_IDENTITY if asset == "summary" else contract.MAPPING_IDENTITY,
                                      run_status="FULL_SUCCESS", schema=schemas[asset], record_count=len(data[asset]))
        if not same_run and asset == "mapping":
            other = new_run_context("6-0-3", "hzp-amz-6-0-3-precision-broad-extraction", "B2", now=datetime(2020,1,1,tzinfo=datetime.now().astimezone().tzinfo))
            meta.update({"RUN_ID": other.run_id, "RUN_TIMESTAMP": other.run_timestamp, "Generated_At": other.generated_at})
        write_metadata_sidecar(path, meta)
    return paths


def test_child_can_be_first_attack_and_parent_core_without_volume_sorting(tmp_path):
    summary, mapping = fixtures()
    ds = decisions(mapping)
    summary[0]["汇总搜索量"], summary[0]["意图机会比"] = "99000", "999"
    result = bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                                "mapping_schema": contract.MAPPING_MULTI_COLUMNS}, ds,
                             product_code="B2", variant_code="M", registry_path=tmp_path / "registry.json")
    tasks = {r["精准泛词"]: r["作战任务"] for r in result["intent"]}
    assert tasks == {"sister gifts": "核心", "sister birthday gifts": "首攻"}


def test_all_keyword_coverage_and_b_derived_only_from_phase1(tmp_path):
    summary, mapping = fixtures()
    ds = decisions(mapping)
    tables = bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                                "mapping_schema": contract.MAPPING_MULTI_COLUMNS}, ds,
                             product_code="B2", variant_code="M", registry_path=tmp_path / "registry.json")
    assert len(tables["keyword"]) == len(mapping) == 4
    assert len({r["Id"] for r in tables["keyword"]}) == 4
    assert [r["Id"] for r in tables["battle"]] == ["501", "502"]
    assert len(bp.architecture_preview(tables, "B2", "M")["campaigns"]) == 1
    assert len(bp.architecture_preview(tables, "B2", "M")["ad_groups"]) == 1


def test_multiple_intents_can_share_campaign_when_role_and_method_match(tmp_path):
    summary, mapping = fixtures()
    ds = decisions(mapping)
    parent = next(row for row in ds["keywords"] if row["Id"] == "503")
    parent.update({"当前状态": "布局", "新品期是否投放": "是", "计划阶段": "PHASE_1",
                   "计划投放方式": "EXACT", "启动条件": "", "暂不投放原因": ""})
    for child_decision in (row for row in ds["keywords"] if row["Id"] in {"501", "502"}):
        child_decision.update({"控制方式": "共享", "控制原因": "与同角色意图共用验证预算。"})
    tables = bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                              "mapping_schema": contract.MAPPING_MULTI_COLUMNS}, ds,
                             product_code="B2", variant_code="M", registry_path=tmp_path / "registry.json")
    architecture = bp.architecture_preview(tables, "B2", "M")
    assert len(architecture["campaigns"]) == 1
    assert set(architecture["campaigns"][0]["Intent"].split("；")) == {"sister gifts", "sister birthday gifts"}


def test_duplicate_or_missing_kwid_fails_closed(tmp_path):
    summary, mapping = fixtures(); mapping[1]["Id"] = "501"
    with pytest.raises(ValueError, match="DUPLICATE_KEYWORD_ID|KEYWORD_LIFECYCLE_MISSING"):
        bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                                    "mapping_schema": contract.MAPPING_MULTI_COLUMNS}, decisions(mapping),
                         product_code="B2", registry_path=tmp_path / "registry.json")
    summary, mapping = fixtures(); ds = decisions(mapping); ds["keywords"].pop()
    with pytest.raises(ValueError, match="KEYWORD_LIFECYCLE_MISSING"):
        bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                                    "mapping_schema": contract.MAPPING_MULTI_COLUMNS}, ds,
                         product_code="B2", registry_path=tmp_path / "r2.json")


def test_stable_intent_code_and_battle_id_across_runs(tmp_path):
    summary, mapping = fixtures(); registry = tmp_path / "registry.json"
    bundle = {"summary": {"rows": summary}, "mapping": {"rows": mapping}, "mapping_schema": contract.MAPPING_MULTI_COLUMNS}
    first = bp.build_tables(bundle, decisions(mapping), product_code="B2", variant_code="M", registry_path=registry)
    second = bp.build_tables(bundle, decisions(mapping), product_code="B2", variant_code="M", registry_path=registry)
    assert {r["精准泛词"]: r["意图代码"] for r in first["intent"]} == {r["精准泛词"]: r["意图代码"] for r in second["intent"]}
    assert [r["作战单元ID"] for r in first["battle"]] == [r["作战单元ID"] for r in second["battle"]]


def test_multibenchmark_keyword_market_fact_is_not_multiplied(tmp_path):
    summary, mapping = fixtures()
    mapping[0].update({"市场容量": "7800", "竞争产品数": "1200", "供需比": "6.5", "对标覆盖数": "3"})
    result = bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                                "mapping_schema": contract.MAPPING_MULTI_COLUMNS}, decisions(mapping),
                             product_code="B2", registry_path=tmp_path / "registry.json")
    row = next(r for r in result["keyword"] if r["Id"] == "501")
    assert (row["市场容量"], row["竞争产品数"], row["供需比"], row["对标覆盖数"]) == ("7800", "1200", "6.5", "3")


def test_legacy_single_benchmark_schema_is_kept_without_fake_multi_fields(tmp_path):
    summary, mapping = fixtures(multi=False)
    result = bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                                "mapping_schema": contract.MAPPING_SINGLE_COLUMNS}, decisions(mapping),
                             product_code="B2", registry_path=tmp_path / "registry.json")
    assert tuple(result["keyword"][0]) == contract.KEYWORD_SINGLE_COLUMNS
    assert "对标覆盖数" not in result["keyword"][0]
    assert result["keyword"][0]["自然排名"] == "10"


def test_campaign_names_use_shared_6_1_contract_and_ad_group_contract(tmp_path):
    summary, mapping = fixtures(); tables = bp.build_tables(
        {"summary": {"rows": summary}, "mapping": {"rows": mapping}, "mapping_schema": contract.MAPPING_MULTI_COLUMNS,
        }, decisions(mapping), product_code="B2", variant_code="M", registry_path=tmp_path / "registry.json")
    campaign = bp.architecture_preview(tables, "B2", "M")["campaigns"][0]
    assert campaign["Campaign Name"] == "B2.M.SP-COR-EXA-SBG-01"
    assert campaign["意图代码"]
    assert campaign["控制方式"] == "独立"
    assert campaign["意图代码"].split("；")[0] in campaign["Campaign Name"]


def test_control_mode_is_intent_decision_keyword_inheritance_and_b_passthrough(tmp_path):
    summary, mapping = fixtures()
    ds = decisions(mapping)
    tables = bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                              "mapping_schema": contract.MAPPING_MULTI_COLUMNS}, ds,
                             product_code="B2", variant_code="M", registry_path=tmp_path / "registry.json")
    assert tuple(tables["intent"][0]) == contract.INTENT_COLUMNS
    assert tuple(tables["keyword"][0]) == contract.KEYWORD_MULTI_COLUMNS
    assert "控制方式" in contract.BATTLE_MULTI_COLUMNS and "控制方式" in tables["battle"][0]
    mode_by_intent = {r["精准泛词"]: r["控制方式"] for r in tables["intent"]}
    for row in tables["keyword"]:
        if row["Id"] != "504":
            assert row["控制方式"] == mode_by_intent[row["精准泛词"]]
    assert next(r for r in tables["keyword"] if r["Id"] == "504")["控制方式"] == "不投"
    assert all(r["控制方式"] == next(k["控制方式"] for k in tables["keyword"] if k["Id"] == r["Id"])
               for r in tables["battle"])
    architecture = bp.architecture_preview(tables, "B2", "M")
    assert all("SBG" in c["Campaign Name"] for c in architecture["campaigns"] if c["控制方式"] == "独立")
    assert all(not any(code in c["Campaign Name"] for code in c["意图代码"].split("；"))
               for c in architecture["campaigns"] if c["控制方式"] == "共享")
    assert not any(c["控制方式"] == "不投" for c in architecture["campaigns"])


def test_keyword_control_override_requires_and_preserves_reason(tmp_path):
    summary, mapping = fixtures(); ds = decisions(mapping)
    keyword = next(r for r in ds["keywords"] if r["Id"] == "501")
    keyword.update({"控制方式": "共享", "控制原因": "与同流量类型的子意图合并验证。"})
    tables = bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                              "mapping_schema": contract.MAPPING_MULTI_COLUMNS}, ds,
                             product_code="B2", variant_code="M", registry_path=tmp_path / "registry.json")
    row = next(r for r in tables["keyword"] if r["Id"] == "501")
    assert (row["控制方式"], row["控制原因"]) == ("共享", "与同流量类型的子意图合并验证。")
    keyword.pop("控制原因")
    with pytest.raises(ValueError, match="CONTROL_OVERRIDE_REASON_MISSING"):
        bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                          "mapping_schema": contract.MAPPING_MULTI_COLUMNS}, ds,
                         product_code="B2", variant_code="M", registry_path=tmp_path / "registry2.json")


def test_no_investment_cannot_be_emitted_as_battle_unit(tmp_path):
    summary, mapping = fixtures(); ds = decisions(mapping)
    row = next(r for r in ds["keywords"] if r["Id"] == "501")
    row.update({"控制方式": "不投", "控制原因": "本期不进入执行。"})
    with pytest.raises(ValueError, match="NO_INVESTMENT_CANNOT_ENTER_BATTLE_PLAN"):
        bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                          "mapping_schema": contract.MAPPING_MULTI_COLUMNS}, ds,
                         product_code="B2", variant_code="M", registry_path=tmp_path / "registry.json")


def test_many_small_shared_intents_do_not_fragment_into_campaign_per_intent(tmp_path):
    summary = []
    mapping = []
    ds = {"intents": [], "keywords": []}
    for i in range(10):
        intent = f"gift category {i}"
        summary.append({"精准泛词": intent, "中文": intent, "层级": "L1", "父精准泛词": "",
                        "直接搜索量": "100", "汇总搜索量": "100", "平均竞品数": "10", "意图机会比": "10", "直接对应词数": "1"})
        mapping.append({"Id": str(600+i), "词": intent, "中文": intent, "市场容量": "100", "竞争产品数": "10",
                        "供需比": "10", "对标覆盖数": "1", "最佳自然排名": "20", "自然排名中位数": "20",
                        "精准泛词": intent, "精准泛词中文": intent})
        ds["intents"].append({"精准泛词": intent, "作战任务": "探索", "作战优先级": "P2", "作战方向": "共享探索",
                              "控制方式": "共享", "控制原因": "单个小意图不足以单独控制预算。", "决策原因": "同一探索方向。"})
        ds["keywords"].append({"Id": str(600+i), "精准泛词": intent, "作战任务": "探索", "当前状态": "布局",
                               "新品期是否投放": "是", "计划阶段": "PHASE_1", "计划投放方式": "BROAD", "启动条件": "",
                               "暂不投放原因": "", "作战目的": "共享池验证。"})
    tables = bp.build_tables({"summary": {"rows": summary}, "mapping": {"rows": mapping},
                              "mapping_schema": contract.MAPPING_MULTI_COLUMNS}, ds,
                             product_code="B2", variant_code="M", registry_path=tmp_path / "registry.json")
    architecture = bp.architecture_preview(tables, "B2", "M")
    assert len(architecture["campaigns"]) == 1
    assert len(architecture["campaigns"][0]["Intent"].split("；")) == 10


def test_timestamped_four_outputs_share_run_and_never_overwrite(tmp_path):
    write_input_bundle(tmp_path)
    bundle = contract.resolve_603_bundle(tmp_path, "B2")
    paths = bp.write_outputs(tmp_path, "B2", "M", bundle, decisions(bundle["mapping"]["rows"]))
    assert len(paths) == 4
    stamps = {tuple(path.stem.rsplit("_", 2)[-2:]) for path in paths.values()}
    assert len(stamps) == 1
    manifests = [json.loads(Path(str(path)+".meta.json").read_text(encoding="utf-8")) for path in paths.values()]
    assert len({m["RUN_ID"] for m in manifests}) == 1
    assert all(m["Inputs"][0]["Input_Report_Identity"] == "PRECISION_BROAD_SUMMARY" for m in manifests)
    for path in paths.values():
        with path.open("r", encoding="utf-8-sig") as handle:
            headers = next(csv.reader(handle)) if path.suffix == ".csv" else None
        if headers:
            expected = contract.INTENT_COLUMNS if "意图市场" in path.name else (
                contract.BATTLE_MULTI_COLUMNS if "作战明细" in path.name else contract.KEYWORD_MULTI_COLUMNS
            )
            assert tuple(headers) == expected
    with pytest.raises(FileExistsError):
        bp._write_csv(paths["intent"], [], contract.INTENT_COLUMNS)


def test_html_architecture_is_traceable_to_tables_and_has_required_sections(tmp_path):
    summary, mapping = fixtures(); tables = bp.build_tables(
        {"summary": {"rows": summary}, "mapping": {"rows": mapping}, "mapping_schema": contract.MAPPING_MULTI_COLUMNS,
        }, decisions(mapping), product_code="B2", variant_code="M", registry_path=tmp_path / "registry.json")
    architecture = bp.architecture_preview(tables, "B2", "M")
    bundle = {"summary": {"file": "sum.csv", "generated_at": "2026-01-01", "rows": summary},
              "mapping": {"file": "map.csv", "generated_at": "2026-01-01", "rows": mapping},
              "run_id": "run", "method": "LATEST_VALID_RUN_BUNDLE"}
    page = bp.render_html("B2", "M", bundle, tables, architecture)
    for section in ("Executive Summary", "Search Intent Battlefield", "为什么选择首攻市场", "核心与扩展市场",
                    "Intent Expansion Path", "Keyword Lifecycle", "当前关键词作战计划", "暂不投放分析",
                    "风险与边界", "广告控制权设计", "拟创建广告架构", "6-1 执行交接摘要", "Input Lineage"):
        assert section in page
    assert "B2.M.SP-COR-EXA-SBG-01" in page
    assert tables["battle"][0]["Id"] in page
    assert "sister birthday gifts → sister gifts" in page
    broken = {"campaigns": [{**architecture["campaigns"][0], "source_ids": ["not-a-source-id"]}],
              "ad_groups": architecture["ad_groups"]}
    with pytest.raises(ValueError, match="ARCHITECTURE_TRACE_MISMATCH"):
        bp.architecture_trace_check(tables, broken)


def test_same_run_resolver_and_run_mismatch(tmp_path):
    write_input_bundle(tmp_path)
    assert contract.resolve_603_bundle(tmp_path, "B2")["status"] == "LATEST_VALID_RUN_BUNDLE_RESOLVED"
    other = tmp_path / "other"
    other.mkdir()
    write_input_bundle(other, same_run=False)
    with pytest.raises(ValueError, match="605_INPUT_RUN_MISMATCH"):
        contract.resolve_603_bundle(other, "B2")


def test_approved_resolver_requires_human_row_state_and_exact_b_set(tmp_path):
    write_input_bundle(tmp_path)
    bundle = contract.resolve_603_bundle(tmp_path, "B2")
    outputs = bp.write_outputs(tmp_path, "B2", "M", bundle, decisions(bundle["mapping"]["rows"]))
    with pytest.raises(ValueError, match="605_PLAN_NOT_APPROVED"):
        contract.resolve_latest_approved_battle_plan(tmp_path, "B2")
    for key in ("intent", "keyword", "battle"):
        rows = list(csv.DictReader(outputs[key].open("r", encoding="utf-8-sig", newline="")))
        for row in rows:
            row["确认状态"] = "APPROVED"
        with outputs[key].open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
        sidecar = Path(str(outputs[key])+".meta.json")
        meta = json.loads(sidecar.read_text(encoding="utf-8")); meta["Record_Count"] = len(rows)
        sidecar.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
    resolved = contract.resolve_latest_approved_battle_plan(tmp_path, "B2")
    assert resolved["status"] == "LATEST_VALID_RUN_BUNDLE_RESOLVED"
