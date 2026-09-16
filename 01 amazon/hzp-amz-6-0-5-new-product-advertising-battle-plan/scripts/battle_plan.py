"""Build traceable 6-0-5 battle-plan assets from AI decisions and latest 6-0-3 inputs.

This module does not make Amazon decisions or write to Amazon/ERP.  The AI supplies
semantic decisions; this module validates, preserves source facts, derives stable
IDs/architecture, writes timestamped assets and renders their dashboard.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Mapping

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
from scripts.new_product_battle_plan_contract import (  # noqa: E402
    BATTLE_MULTI_COLUMNS, BATTLE_SINGLE_COLUMNS, INTENT_COLUMNS,
    KEYWORD_MULTI_COLUMNS, KEYWORD_SINGLE_COLUMNS, MAPPING_MULTI_COLUMNS,
    MAPPING_SINGLE_COLUMNS, OUTPUT_DIR, OUTPUT_IDENTITIES, SUMMARY_COLUMNS,
    resolve_603_bundle,
)
from scripts.resolve_amazon_ad_identity import format_ad_group_name, format_campaign_name  # noqa: E402
from scripts.stage6_artifact_contract import (  # noqa: E402
    assert_new_outputs, make_artifact_metadata, new_run_context,
    timestamped_output_path, write_metadata_sidecar,
)
from scripts.hzp_amz_report_contract import (  # noqa: E402
    build_report_filename, resolve_skill_report_dir, validate_hzp_amz_report_batch,
)

SKILL_ID = "hzp-amz-6-0-5-new-product-advertising-battle-plan"
TASKS = {"首攻", "核心", "扩展", "探索", "暂缓"}
PHASES = {"PHASE_1", "PHASE_2", "PHASE_3", "SEASONAL", "HOLD"}
METHODS = {"EXACT", "PHRASE", "BROAD", "AUTO", "ASIN", "CATEGORY", ""}
STATES = {"首攻", "布局", "待扩张", "季节等待", "储备", "暂缓"}
PRIORITIES = {"P1", "P2", "P3", "HOLD"}
APPROVAL = "PROPOSED"
CONTROL_MODES = {"独立", "共享", "不投"}


def _text(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _as_intent_map(decisions: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    rows = decisions.get("intents")
    if not isinstance(rows, list):
        raise ValueError("INTENT_CODE_CONFLICT: decisions.intents must be a list")
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        canonical = _text(row.get("精准泛词"))
        if not canonical or canonical in result:
            raise ValueError("INTENT_CODE_CONFLICT")
        result[canonical] = row
    return result


def _read_registry(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        mapping = payload.get("intents", {})
        if not isinstance(mapping, dict) or len(set(mapping.values())) != len(mapping):
            raise ValueError
        return {str(k): str(v) for k, v in mapping.items()}
    except (OSError, json.JSONDecodeError, AttributeError, ValueError):
        raise ValueError("INTENT_CODE_CONFLICT: invalid stable intent registry")


def _suggest_code(canonical: str, used: set[str]) -> str:
    tokens = re.findall(r"[A-Za-z0-9]+", canonical)
    base = "".join(token[0].upper() for token in tokens) or "IN"
    base = base[:8]
    if base not in used:
        return base
    for size in range(2, min(8, len("".join(tokens))) + 1):
        candidate = "".join("".join(tokens)[:size]).upper()
        if candidate not in used:
            return candidate
    suffix = 2
    while f"{base}{suffix}" in used:
        suffix += 1
    return f"{base}{suffix}"


def stable_intent_codes(canonicals: list[str], registry_path: Path) -> dict[str, str]:
    registry = _read_registry(registry_path)
    used = set(registry.values())
    if len(used) != len(registry):
        raise ValueError("INTENT_CODE_CONFLICT")
    for canonical in canonicals:
        if canonical not in registry:
            registry[canonical] = _suggest_code(canonical, used)
            used.add(registry[canonical])
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    temp = registry_path.with_name(registry_path.name + ".tmp")
    temp.write_text(json.dumps({"intents": registry}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(registry_path)
    return {name: registry[name] for name in canonicals}


def _decision_by_id(decisions: Mapping[str, Any], source_ids: set[str]) -> dict[str, Mapping[str, Any]]:
    rows = decisions.get("keywords")
    if not isinstance(rows, list):
        raise ValueError("KEYWORD_LIFECYCLE_MISSING")
    result: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        record_id = _text(row.get("Id"))
        if not record_id or record_id in result:
            raise ValueError("DUPLICATE_KEYWORD_ID")
        result[record_id] = row
    if set(result) != source_ids:
        raise ValueError("KEYWORD_LIFECYCLE_MISSING")
    return result


def _copy_market_fields(source: Mapping[str, str], multi: bool) -> dict[str, str]:
    fields = ("市场容量", "竞争产品数", "供需比")
    fields += ("对标覆盖数", "最佳自然排名", "自然排名中位数") if multi else ("自然排名",)
    return {field: _text(source.get(field)) for field in fields}


def _stable_battle_id(product_code: str, variant_code: str, intent_code: str, kwid: str, method: str, phase: str) -> str:
    # Readable identity fragments plus a short hash avoid unsafe/path-length names.
    raw = "|".join((product_code, variant_code, intent_code, kwid, method, phase))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:10].upper()
    return f"{product_code}-{variant_code or 'NA'}-{intent_code}-{kwid}-{method or 'NONE'}-{phase}-{digest}"


def build_tables(bundle: Mapping[str, Any], decisions: Mapping[str, Any], *, product_code: str,
                 variant_code: str = "", registry_path: Path) -> dict[str, Any]:
    summary = bundle["summary"]["rows"]
    keywords = bundle["mapping"]["rows"]
    mapping_schema = tuple(bundle.get("mapping_schema") or bundle["mapping"].get("schema") or ())
    multi = mapping_schema == MAPPING_MULTI_COLUMNS
    if not multi and mapping_schema != MAPPING_SINGLE_COLUMNS:
        raise ValueError("605_INPUT_SCHEMA_INVALID")
    intent_decisions = _as_intent_map(decisions)
    input_intents = {_text(row.get("精准泛词")) for row in summary}
    if "" in input_intents or set(intent_decisions) != input_intents:
        raise ValueError("INTENT_CODE_CONFLICT")
    if len(input_intents) != len(summary):
        raise ValueError("INTENT_CODE_CONFLICT")
    codes = stable_intent_codes(sorted(input_intents), registry_path)
    intent_rows: list[dict[str, Any]] = []
    task_by_intent: dict[str, str] = {}
    for source in summary:
        name = _text(source.get("精准泛词"))
        decision = intent_decisions[name]
        task = _text(decision.get("作战任务"))
        control_mode = _text(decision.get("控制方式"))
        control_reason = _text(decision.get("控制原因"))
        priority = _text(decision.get("作战优先级"))
        if task not in TASKS:
            raise ValueError("INVALID_BATTLE_TASK")
        if priority not in PRIORITIES:
            raise ValueError("INVALID_BATTLE_TASK")
        if control_mode not in CONTROL_MODES or not control_reason:
            raise ValueError("INVALID_CONTROL_DECISION")
        task_by_intent[name] = task
        row = {column: "" for column in INTENT_COLUMNS}
        row.update({key: _text(source.get(key)) for key in SUMMARY_COLUMNS})
        row.update({"意图代码": codes[name], "作战任务": task, "作战优先级": priority,
                    "作战方向": _text(decision.get("作战方向")),
                    "控制方式": control_mode, "控制原因": control_reason,
                    "决策原因": _text(decision.get("决策原因")), "确认状态": APPROVAL})
        if not row["决策原因"] or not row["作战方向"]:
            raise ValueError("INTENT_CODE_CONFLICT: intent rationale/direction missing")
        intent_rows.append(row)

    source_ids = {_text(row.get("Id")) for row in keywords}
    keyword_decisions = _decision_by_id(decisions, source_ids)
    summary_by_intent = {_text(row.get("精准泛词")): row for row in summary}
    intent_row_by_name = {row["精准泛词"]: row for row in intent_rows}
    code_to_intent = {code: name for name, code in codes.items()}
    keyword_rows: list[dict[str, Any]] = []
    decision_by_id: dict[str, Mapping[str, Any]] = {}
    for source in keywords:
        record_id = _text(source.get("Id"))
        decision = keyword_decisions[record_id]
        intent = _text(source.get("精准泛词"))
        if intent not in summary_by_intent:
            raise ValueError("KEYWORD_LIFECYCLE_MISSING")
        requested_intent = _text(decision.get("精准泛词"))
        if requested_intent != intent:
            raise ValueError("INTENT_CODE_CONFLICT")
        task = _text(decision.get("作战任务"))
        state = _text(decision.get("当前状态"))
        yes_no = _text(decision.get("新品期是否投放"))
        phase = _text(decision.get("计划阶段"))
        method = _text(decision.get("计划投放方式"))
        control_override = _text(decision.get("控制方式"))
        control_mode = control_override or intent_row_by_name[intent]["控制方式"]
        if control_mode not in CONTROL_MODES:
            raise ValueError("INVALID_CONTROL_MODE")
        control_reason = _text(decision.get("控制原因")) or intent_row_by_name[intent]["控制原因"]
        if control_override and control_mode != intent_row_by_name[intent]["控制方式"] and not _text(decision.get("控制原因")):
            raise ValueError("CONTROL_OVERRIDE_REASON_MISSING")
        if task not in TASKS:
            raise ValueError("INVALID_BATTLE_TASK")
        if state not in STATES:
            raise ValueError("INVALID_BATTLE_TASK")
        if phase not in PHASES:
            raise ValueError("INVALID_PHASE")
        if method not in METHODS:
            raise ValueError("INVALID_EXECUTION_METHOD")
        if yes_no not in {"是", "否"}:
            raise ValueError("KEYWORD_LIFECYCLE_MISSING")
        if control_mode == "不投" and yes_no != "否":
            raise ValueError("NO_INVESTMENT_CANNOT_ENTER_BATTLE_PLAN")
        if (phase == "PHASE_1" and yes_no != "是") or (yes_no == "是" and (phase == "HOLD" or not method)):
            raise ValueError("INVALID_PHASE")
        if yes_no == "否" and not _text(decision.get("暂不投放原因")):
            raise ValueError("KEYWORD_LIFECYCLE_MISSING")
        if method in {"ASIN", "CATEGORY"}:
            raise ValueError("BATTLE_UNIT_SOURCE_MISSING")
        row = {"Id": record_id, "词": _text(source.get("词")), "中文": _text(source.get("中文")),
               "精准泛词": intent, "意图代码": codes[intent]}
        row.update(_copy_market_fields(source, multi))
        row.update({"作战任务": task, "控制方式": control_mode, "控制原因": control_reason,
                    "当前状态": state, "新品期是否投放": yes_no,
                    "计划阶段": phase, "计划投放方式": method,
                    "启动条件": _text(decision.get("启动条件")),
                    "暂不投放原因": _text(decision.get("暂不投放原因")), "确认状态": APPROVAL})
        if phase != "PHASE_1" and yes_no == "是" and not row["启动条件"]:
            raise ValueError("KEYWORD_LIFECYCLE_MISSING")
        keyword_rows.append(row)
        decision_by_id[record_id] = decision

    if len(keyword_rows) != len(keywords) or len({row["Id"] for row in keyword_rows}) != len(keywords):
        raise ValueError("OUTPUT_COVERAGE_MISMATCH")
    battle_rows: list[dict[str, Any]] = []
    for row in keyword_rows:
        if row["计划阶段"] != "PHASE_1" or row["新品期是否投放"] != "是":
            continue
        method = row["计划投放方式"]
        objective = _text(decision_by_id[row["Id"]].get("作战目的"))
        if not objective:
            raise ValueError("BATTLE_UNIT_SOURCE_MISSING")
        priority = next(item["作战优先级"] for item in intent_rows if item["精准泛词"] == row["精准泛词"])
        battle = {"作战单元ID": _stable_battle_id(product_code, variant_code, row["意图代码"], row["Id"], method, row["计划阶段"]),
                  "精准泛词": row["精准泛词"], "意图代码": row["意图代码"], "作战任务": row["作战任务"],
                  "作战优先级": priority, "控制方式": row["控制方式"], "Id": row["Id"], "词": row["词"], "中文": row["中文"],
                  "市场容量": row["市场容量"], "竞争产品数": row["竞争产品数"], "供需比": row["供需比"],
                  "计划阶段": row["计划阶段"], "投放方式": method, "作战目的": objective, "确认状态": APPROVAL}
        if multi:
            battle.update({field: row[field] for field in ("对标覆盖数", "最佳自然排名", "自然排名中位数")})
        else:
            battle["自然排名"] = row["自然排名"]
        battle_rows.append(battle)
    ids_c = {row["Id"] for row in keyword_rows if row["计划阶段"] == "PHASE_1" and row["新品期是否投放"] == "是"}
    ids_b = [row["Id"] for row in battle_rows]
    if len(ids_b) != len(set(ids_b)) or set(ids_c) != set(ids_b):
        raise ValueError("OUTPUT_COVERAGE_MISMATCH")
    unit_ids = [row["作战单元ID"] for row in battle_rows]
    if len(unit_ids) != len(set(unit_ids)):
        raise ValueError("BATTLE_UNIT_ID_CONFLICT")
    return {"intent": intent_rows, "keyword": keyword_rows, "battle": battle_rows,
            "multi": multi, "task_by_intent": task_by_intent, "code_to_intent": code_to_intent}


def _ad_role(task: str, method: str) -> tuple[str, str, str]:
    method_map = {"EXACT": "EXA", "PHRASE": "PHR", "BROAD": "BRO", "AUTO": "AUT", "ASIN": "ASI", "CATEGORY": "CAT"}
    if method not in method_map:
        raise ValueError("INVALID_EXECUTION_METHOD")
    if method == "ASIN":
        role = "COM"
    elif method == "CATEGORY":
        role = "CAT"
    else:
        role = {"首攻": "COR", "核心": "COR", "扩展": "EXP", "探索": "DIS"}.get(task)
    if not role:
        raise ValueError("INVALID_BATTLE_TASK")
    return role, method_map[method], "SP"


def architecture_preview(tables: Mapping[str, Any], product_code: str, variant_code: str) -> dict[str, list[dict[str, Any]]]:
    """Group compatible shared pools and independent Intent control boundaries."""
    groups: dict[tuple[str, str, str, str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for battle in tables["battle"]:
        control = battle["控制方式"]
        if control == "不投":
            raise ValueError("NO_INVESTMENT_CANNOT_ENTER_BATTLE_PLAN")
        if control not in {"独立", "共享"}:
            raise ValueError("INVALID_CONTROL_MODE")
        role, tool, ad_type = _ad_role(battle["作战任务"], battle["投放方式"])
        boundary = battle["意图代码"] if control == "独立" else ""
        groups[(control, ad_type, role, tool, battle["计划阶段"], boundary)].append(battle)
    campaigns, ad_groups = [], []
    for (control, ad_type, role, tool, phase, boundary), units in sorted(groups.items()):
        # Sequence 01 is a preview only; 6-1 must resolve actual collisions before apply.
        campaign_name = format_campaign_name(product_code, ad_type, role, tool, 1, variant_code or None,
                                             intent_code=boundary or None, control_mode=control)
        intents = sorted({unit["精准泛词"] for unit in units})
        codes = sorted({unit["意图代码"] for unit in units})
        campaign_key = f"{control}-{role}-{tool}-{boundary or 'SHARED'}"
        purposes = sorted({unit["作战目的"] for unit in units})
        campaigns.append({"Campaign Name": campaign_name, "Intent": "；".join(intents),
                           "意图代码": "；".join(codes), "作战任务": "；".join(sorted({u["作战任务"] for u in units})),
                           "计划阶段": phase, "控制方式": control, "Technical Role": f"{role}-{tool}",
                           "投放方式": units[0]["投放方式"], "广告类型": ad_type,
                           "Target数量": len(units), "计划状态": APPROVAL,
                           "作战目的": "；".join(purposes), "campaign_key": campaign_key,
                           "source_ids": [unit["Id"] for unit in units]})
        ad_groups.append({"Ad Group Name": format_ad_group_name(product_code, role, 1, variant_code or None),
                          "Target Type": units[0]["投放方式"], "Keyword Count": len(units),
                          "Match Type": units[0]["投放方式"], "Intent": "；".join(intents),
                          "作战目的": "；".join(purposes), "Campaign Name": campaign_name})
    result = {"campaigns": campaigns, "ad_groups": ad_groups}
    architecture_trace_check(tables, result)
    return result


def architecture_trace_check(tables: Mapping[str, Any], architecture: Mapping[str, Any]) -> None:
    source_ids = [row["Id"] for row in tables["battle"]]
    preview_ids = [record_id for campaign in architecture["campaigns"] for record_id in campaign["source_ids"]]
    if len(preview_ids) != len(set(preview_ids)) or set(preview_ids) != set(source_ids):
        raise ValueError("ARCHITECTURE_TRACE_MISMATCH")
    if sum(group["Keyword Count"] for group in architecture["ad_groups"]) != len(source_ids):
        raise ValueError("ARCHITECTURE_TRACE_MISMATCH")


def render_html(product_code: str, variant_code: str, bundle: Mapping[str, Any], tables: Mapping[str, Any], architecture: Mapping[str, Any]) -> str:
    intents = tables["intent"]
    keywords = tables["keyword"]
    summary = bundle["summary"]["rows"]
    phases = Counter(row["计划阶段"] for row in keywords)
    tasks = Counter(row["作战任务"] for row in intents)
    first = [r for r in intents if r["作战任务"] == "首攻"]
    core = [r for r in intents if r["作战任务"] == "核心"]
    expansion = [r for r in intents if r["作战任务"] == "扩展"]
    held = [r for r in keywords if r["新品期是否投放"] == "否"]
    source_names = {k: Path(bundle[k]["file"]).name for k in ("summary", "mapping")}

    def cell(v: Any) -> str:
        return html.escape(_text(v))

    def table(headers: list[str], rows: list[list[Any]], empty: str = "暂无记录") -> str:
        if not rows:
            return f'<p class="empty">{cell(empty)}</p>'
        return "<div class=\"table-wrap\"><table><thead><tr>" + "".join(f"<th>{cell(h)}</th>" for h in headers) + "</tr></thead><tbody>" + "".join(
            "<tr>" + "".join(f"<td>{cell(v)}</td>" for v in row) + "</tr>" for row in rows) + "</tbody></table></div>"

    intent_view = [[r["意图代码"], r["精准泛词"], r["中文"], r["层级"], r["父精准泛词"], r["直接搜索量"], r["汇总搜索量"], r["平均竞品数"], r["意图机会比"], r["直接对应词数"], r["作战任务"], r["作战优先级"], r["作战方向"], r["控制方式"], r["控制原因"], r["决策原因"], r["确认状态"]] for r in intents]
    keyword_view = [[r["Id"], r["词"], r["中文"], r["精准泛词"], r["作战任务"], r["控制方式"], r["控制原因"], r["市场容量"], r["竞争产品数"], r["供需比"], r.get("对标覆盖数", r.get("自然排名", "")), r.get("最佳自然排名", ""), r.get("自然排名中位数", ""), r["当前状态"], r["计划阶段"], r["计划投放方式"], r["新品期是否投放"], r["启动条件"], r["暂不投放原因"]] for r in keywords]
    held_view = [[r["Id"], r["词"], r["精准泛词"], r["当前状态"], r["计划阶段"], r["暂不投放原因"]] for r in held]
    campaign_view = [[r["Campaign Name"], r["Intent"], r["意图代码"], r["作战任务"], r["计划阶段"], r["控制方式"], r["Technical Role"], r["投放方式"], r["广告类型"], r["Target数量"], r["计划状态"], r["作战目的"]] for r in architecture["campaigns"]]
    adgroup_view = [[r["Ad Group Name"], r["Target Type"], r["Keyword Count"], r["Match Type"], r["Intent"], r["作战目的"]] for r in architecture["ad_groups"]]
    handoff = "人工批准后，6-1 只能读取本次有效且已批准资产；6-1 不重判意图、作战任务、阶段或投放方式。当前所有输出均为 PROPOSED，不构成广告创建授权。"
    summary_by_name = {r["精准泛词"]: r for r in intents}
    route_parts = []
    for row in first:
        chain = [row["精准泛词"]]
        parent = row["父精准泛词"]
        visited = set(chain)
        while parent and parent in summary_by_name and parent not in visited:
            chain.append(parent)
            visited.add(parent)
            parent = summary_by_name[parent]["父精准泛词"]
        route_parts.append(" → ".join(chain))
    covered = {name for part in route_parts for name in part.split(" → ")}
    route_parts.extend(row["精准泛词"] for row in core + expansion if row["精准泛词"] not in covered)
    route = " ｜ ".join(route_parts) or "待人工审核后形成"
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{cell(product_code)} 新品广告作战规划</title><style>
    :root{{--ink:#14243b;--muted:#64748b;--line:#dbe4ef;--blue:#1d4ed8;--pale:#eff6ff;--amber:#a16207;--bg:#f5f8fc}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:14px/1.55 "Segoe UI","Microsoft YaHei",sans-serif}}main{{max-width:1600px;margin:auto;padding:28px}}header{{background:#102b50;color:white;padding:28px;border-radius:16px}}h1{{margin:0 0 8px;font-size:28px}}h2{{font-size:19px;margin:0 0 14px}}h3{{font-size:16px}}p{{margin:6px 0}}.muted{{color:var(--muted)}}header .muted{{color:#dbeafe}}.badge{{display:inline-block;border-radius:999px;background:#fff2cc;color:#805800;padding:3px 10px;font-weight:700}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:12px;margin:16px 0}}.card,section{{background:white;border:1px solid var(--line);border-radius:12px;padding:18px;margin:14px 0}}.card b{{display:block;font-size:22px;color:var(--blue)}}.table-wrap{{overflow:auto}}table{{border-collapse:collapse;width:100%;min-width:850px;font-size:13px}}th,td{{border-bottom:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}}th{{background:#f0f5fb;position:sticky;top:0;white-space:nowrap}}td{{max-width:380px;overflow-wrap:anywhere}}.risk{{border-left:4px solid #d97706;background:#fffbeb;padding:14px}}.road{{display:flex;gap:10px;flex-wrap:wrap;align-items:center}}.step{{padding:10px 12px;background:var(--pale);border:1px solid #bfdbfe;border-radius:10px}}.empty{{color:var(--muted);font-style:italic}}footer{{color:var(--muted);padding:12px}}@media print{{body{{background:#fff}}main{{max-width:none;padding:0}}section,.card,header{{break-inside:avoid}}.table-wrap{{overflow:visible}}th{{position:static}}}}
    </style></head><body><main><header><p class="muted">HZP AMAZON · 6-0-5 NEW PRODUCT ADVERTISING BATTLE PLAN</p><h1>新品广告作战规划</h1><p>{cell(product_code)}{'.'+cell(variant_code) if variant_code else ''} · <span class="badge">PROPOSED｜待人工确认</span></p><p class="muted">规划层负责选择市场、词、阶段与投放方式；本报告不创建广告，也不决定 Bid / Budget / Placement 金额。</p></header>
    <section><h2>1. Executive Summary</h2><div class="grid"><div class="card"><span>首攻意图</span><b>{cell('、'.join(r['精准泛词'] for r in first) or '未分配')}</b></div><div class="card"><span>核心意图</span><b>{cell('、'.join(r['精准泛词'] for r in core) or '未分配')}</b></div><div class="card"><span>扩展意图</span><b>{cell('、'.join(r['精准泛词'] for r in expansion) or '未分配')}</b></div><div class="card"><span>PHASE_1关键词</span><b>{sum(1 for r in keywords if r['计划阶段']=='PHASE_1' and r['新品期是否投放']=='是')}</b></div><div class="card"><span>暂缓/不投放词</span><b>{len(held)}</b></div></div><p><b>路线：</b>{cell(route)}</p><p><b>任务分布：</b>{cell('；'.join(f'{k} {v}' for k,v in tasks.items()))}</p></section>
    <section><h2>2. Search Intent Battlefield</h2>{table(list(INTENT_COLUMNS), intent_view)}</section>
    <section><h2>3. 为什么选择首攻市场</h2><p>首攻由定性综合决策，不以最大搜索量、最高意图机会比、最低平均竞品数、最佳自然排名或最高对标覆盖数单项自动决定。决策原因需同时解释市场环境、父子层级与具体突破词/对标现实证据。</p>{table(["Intent","层级","父Intent","作战方向","决策原因"], [[r["精准泛词"],r["层级"],r["父精准泛词"],r["作战方向"],r["决策原因"]] for r in first])}</section>
    <section><h2>4. 核心与扩展市场</h2>{table(["任务","Intent","层级","方向","原因"], [[r["作战任务"],r["精准泛词"],r["层级"],r["作战方向"],r["决策原因"]] for r in intents if r["作战任务"] in {"核心","扩展","探索","暂缓"}])}</section>
    <section><h2>5. Intent Expansion Path</h2><div class="road">{''.join(f'<span class="step">{cell(label)}</span>' for label in (['Child Beachhead']+[r['精准泛词'] for r in first]+['Parent Core']+[r['精准泛词'] for r in core]+['Second Intent / Scale / Seasonal']+[r['精准泛词'] for r in expansion]))}</div><p class="muted">按 603 父子层级展示；父子汇总搜索量有包含关系，不跨层相加。</p></section>
    <section><h2>6. Keyword Lifecycle</h2>{table(["阶段","关键词数"], [[phase,count] for phase,count in sorted(phases.items())])}</section>
    <section><h2>7. 当前关键词作战计划</h2>{table(["Id","Keyword","中文","Intent","任务","控制方式","控制原因","市场容量","竞争产品数","供需比","对标覆盖/自然排名","最佳自然排名","排名中位数","状态","阶段","投放方式","新品期投放","启动条件","暂不投放原因"], keyword_view)}</section>
    <section><h2>8. 暂不投放分析</h2>{table(["Id","Keyword","Intent","当前状态","计划阶段","暂不投放原因"], held_view)}</section>
    <section><h2>9. 风险与边界</h2><div class="risk"><ul><li>意图机会比是内部机会信号，不是 Amazon 官方竞争指标。</li><li>父子 Intent 汇总搜索量存在包含关系，不能跨层相加。</li><li>高度精准不等于新品期必须立即投放；预算有限时避免过度分散。</li><li>多对标排名是 Reality Evidence，不代表真实销量或市场份额；市场容量与竞争数按唯一关键词事实只计一次。</li><li>6-0-5 不决定最终 Bid、Daily Budget、Placement 百分比。</li></ul></div></section>
    <section><h2>10. 广告控制权设计 · Campaign Control Design</h2><p>独立=Budget、Bid、Placement、流量隔离与增长节奏独立；共享=在兼容广告类型、角色、Target/Traffic Type、阶段及预算/广告位策略的池内低成本验证；不投=不进入当前结构。</p>{table(["Intent","作战任务","控制方式","控制原因","汇总搜索量","意图机会比"], [[r["精准泛词"],r["作战任务"],r["控制方式"],r["控制原因"],r["汇总搜索量"],r["意图机会比"]] for r in intents])}<p class="risk">首攻/核心仅是控制判断的Evidence，不机械等于独立。小意图不因命名需要拆分预算；过度拆分导致学习数据稀释时优先考虑兼容共享池。实际预算与Placement兼容性若须执行时确定，由6-1核验，发现冲突回605修订。</p></section>
    <section><h2>11. 拟创建广告架构 · Proposed Advertising Architecture</h2><p>架构由 A/C/B 表派生；Sequence 01 仅为命名预览，6-1 必须按账户现存活动校验碰撞。Campaign 根据控制方式、AdType、Technical Role、Target/Traffic Type与阶段分组；独立名称含Intent Code，共享名称不含Intent Code，不投不生成Campaign。独立Intent内可包含多个Keyword。共享池的预算/Placement兼容性由执行前核验。</p>{table(["Campaign Name","Intent","意图代码","作战任务","阶段","控制方式","Technical Role","投放方式","广告类型","Target数量","计划状态","作战目的"], campaign_view)}<h3>Ad Group</h3>{table(["Ad Group Name","Target Type","Keyword Count","Match Type","Intent","作战目的"], adgroup_view)}<h3>PHASE_1 关键词追溯</h3>{table(["Id","Keyword","中文","市场容量","竞争产品数","供需比","Primary Intent","任务","控制方式","阶段","投放方式","作战目的"], [[r["Id"],r["词"],r["中文"],r["市场容量"],r["竞争产品数"],r["供需比"],r["精准泛词"],r["作战任务"],r["控制方式"],r["计划阶段"],r["计划投放方式"],next((b["作战目的"] for b in tables["battle"] if b["Id"]==r["Id"]),"")] for r in keywords if r["计划阶段"]=="PHASE_1" and r["新品期是否投放"]=="是"])}</section>
    <section><h2>12. 6-1 执行交接摘要</h2><p>{cell(handoff)}</p><p>当前状态：A/C/B 全部 PROPOSED。仅当人工作出明确批准且资产血缘、覆盖和身份验证通过后，才可进入 6-1；批准不等于广告写入授权。</p></section>
    <section><h2>本次使用数据｜Input Lineage</h2><p>Product Code：{cell(product_code)} · Variant Code：{cell(variant_code or '未指定')}</p><p>603 Summary：{cell(source_names['summary'])} · 603 Mapping：{cell(source_names['mapping'])}</p><p>603 RUN_ID：{cell(bundle.get('run_id'))} · Generated At：{cell(bundle['summary'].get('generated_at'))}</p><p>Intent Count：{len(summary)} · Keyword Count：{len(bundle['mapping']['rows'])} · Resolution：{cell(bundle.get('method'))}</p></section>
    <footer>本报告属于作战规划建议，所有行状态初始为 PROPOSED。真实投放配置、预算与竞价由 6-1 基于执行时证据再校验。</footer></main></body></html>'''


def _write_csv(path: Path, rows: list[Mapping[str, Any]], schema: tuple[str, ...]) -> None:
    with path.open("x", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=schema, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)


def write_outputs(product_root: str | Path, product_code: str, variant_code: str,
                  bundle: Mapping[str, Any], decisions: Mapping[str, Any]) -> dict[str, Path]:
    root = Path(product_root).resolve()
    out_dir = resolve_skill_report_dir(root, Path(__file__).resolve().parents[1])
    registry_path = out_dir / "intent-code-registry.json"
    context = new_run_context("6-0-5", SKILL_ID, product_code)
    mapping_schema = tuple(bundle.get("mapping_schema") or bundle["mapping"].get("schema") or ())
    if mapping_schema not in (MAPPING_MULTI_COLUMNS, MAPPING_SINGLE_COLUMNS):
        raise ValueError("605_INPUT_SCHEMA_INVALID")
    schemas = {"intent": INTENT_COLUMNS,
               "keyword": KEYWORD_MULTI_COLUMNS if mapping_schema == MAPPING_MULTI_COLUMNS else KEYWORD_SINGLE_COLUMNS,
               "battle": BATTLE_MULTI_COLUMNS if mapping_schema == MAPPING_MULTI_COLUMNS else BATTLE_SINGLE_COLUMNS}
    names = {"intent": "新品意图市场作战表", "keyword": "新品关键词阶段规划表",
             "battle": "新品关键词作战明细", "html": "新品广告作战规划报告"}
    paths = {key: out_dir / build_report_filename(Path(__file__).resolve().parents[1], name,
                                          context.run_timestamp, "html" if key == "html" else "csv")
             for key, name in names.items()}
    report_error = validate_hzp_amz_report_batch(
        list(paths.values()), root, Path(__file__).resolve().parents[1], timestamp=context.run_timestamp,
    )
    if report_error:
        raise ValueError(report_error)
    sidecars = [Path(str(path)+".meta.json") for path in paths.values()]
    assert_new_outputs([*paths.values(), *sidecars])
    tables = build_tables(bundle, decisions, product_code=product_code,
                          variant_code=variant_code, registry_path=registry_path)
    architecture = architecture_preview(tables, product_code, variant_code)
    for key in ("intent", "keyword", "battle"):
        _write_csv(paths[key], tables[key], schemas[key])
    readback_tables = dict(tables)
    for key in ("intent", "keyword", "battle"):
        with paths[key].open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if tuple(reader.fieldnames or ()) != tuple(schemas[key]):
                raise ValueError("605_OUTPUT_READBACK_SCHEMA_MISMATCH")
            rows = list(reader)
        expected = tables[key]
        if len(rows) != len(expected) or any(
            str(row.get(column) if row.get(column) is not None else "") != actual[column]
            for row, actual in zip(expected, rows) for column in schemas[key]
        ):
            raise ValueError("605_OUTPUT_READBACK_MISMATCH")
        readback_tables[key] = rows
    readback_architecture = architecture_preview(readback_tables, product_code, variant_code)
    content = render_html(product_code, variant_code, bundle, readback_tables, readback_architecture)
    with paths["html"].open("x", encoding="utf-8", newline="") as handle:
        handle.write(content)
    inputs = []
    for asset in ("summary", "mapping"):
        item = bundle[asset]
        inputs.append({"Input_Skill": "hzp-amz-6-0-3-precision-broad-extraction",
                       "Input_Report_Identity": "PRECISION_BROAD_SUMMARY" if asset == "summary" else "PRECISION_BROAD_MAPPING",
                       "Input_File_Name": item["file"], "Input_Run_Timestamp": bundle.get("run_timestamp"),
                       "Input_Generated_At": item.get("generated_at"),
                       "Input_Record_Count": item.get("record_count", len(item.get("rows") or [])),
                       "Input_Resolution_Method": bundle.get("method")})
    for key, identity in OUTPUT_IDENTITIES.items():
        count = len(tables[key]) if key != "html" else None
        metadata = make_artifact_metadata(context, identity, run_status="FULL_SUCCESS",
                                          schema=schemas.get(key), record_count=count,
                                          inputs=inputs, output_assets=[str(p) for p in paths.values()],
                                          extra={"Approval_Status": "PROPOSED", "Product_Root": str(root),
                                                 "603_RUN_ID": bundle.get("run_id"),
                                                 "Input_Intent_Count": len(bundle["summary"]["rows"]),
                                                 "Input_Keyword_Count": len(bundle["mapping"]["rows"]),
                                                 "Input_Resolution_Method": bundle.get("method")})
        write_metadata_sidecar(paths[key], metadata)
    return paths


def inspect_inputs(product_root: str | Path, product_code: str) -> dict[str, Any]:
    bundle = resolve_603_bundle(product_root, product_code)
    return {"status": bundle["status"], "run_id": bundle["run_id"], "run_timestamp": bundle["run_timestamp"],
            "input_resolution_method": bundle["method"],
            "summary": {"file": bundle["summary"]["file"], "generated_at": bundle["summary"].get("generated_at"), "rows": bundle["summary"]["rows"]},
            "mapping": {"file": bundle["mapping"]["file"], "generated_at": bundle["mapping"].get("generated_at"), "rows": bundle["mapping"]["rows"], "schema": list(bundle["mapping_schema"])} }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    inspect_parser = sub.add_parser("inspect", help="resolve and print the latest valid 6-0-3 same-run inputs")
    inspect_parser.add_argument("--product-root", required=True)
    inspect_parser.add_argument("--product-code", required=True)
    build_parser = sub.add_parser("build", help="write assets from a reviewed AI decision JSON; no ad/ERP writes")
    build_parser.add_argument("--product-root", required=True)
    build_parser.add_argument("--product-code", required=True)
    build_parser.add_argument("--variant-code", default="")
    build_parser.add_argument("--decisions", required=True)
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            print(json.dumps(inspect_inputs(args.product_root, args.product_code), ensure_ascii=False, indent=2))
            return 0
        bundle = resolve_603_bundle(args.product_root, args.product_code)
        decisions = json.loads(Path(args.decisions).read_text(encoding="utf-8-sig"))
        paths = write_outputs(args.product_root, args.product_code, args.variant_code, bundle, decisions)
        print(json.dumps({"status": "FULL_SUCCESS", "outputs": {k: str(v) for k, v in paths.items()}}, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        print(str(exc) or exc.__class__.__name__, file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
