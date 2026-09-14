from pathlib import Path

ROOT = Path(__file__).resolve().parents[0].parent
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8")

VARIANTS = [
    {"Product_Code": "B2", "Var_Code": "M", "Var_Name": "月亮款", "ASIN": "B0H8Y4B318"},
    {"Product_Code": "B2", "Var_Code": "S", "Var_Name": "石头款", "ASIN": "B0H8Y24R37"},
]
PRODUCT_ROWS = [{"Product_Code": "B2", "ASIN": "B0H8Y4B318"}]


def resolve_variant_command(product_code, var_code, rows=VARIANTS, product_rows=PRODUCT_ROWS):
    """Small read-only model of the 5-5 mapping contract for Mock Cases P-T."""
    matches = [
        row for row in rows
        if row["Product_Code"].casefold() == product_code.casefold()
        and var_code is not None
        and row["Var_Code"].casefold() == var_code.casefold()
    ]
    if var_code is None:
        defaults = [row.get("ASIN") for row in product_rows if row.get("Product_Code", "").casefold() == product_code.casefold()]
        if not defaults or not defaults[0]:
            return {"status": "默认ASIN缺失"}
        return {"status": "OK", "asin": defaults[0]}
    asins = {row.get("ASIN") for row in matches}
    if not matches:
        return {"status": "未找到对应变体ASIN"}
    if len(asins) != 1:
        return {"status": "变体ASIN映射冲突"}
    return {"status": "OK", "asin": next(iter(asins)), "rows": matches}


def test_skill_declares_variant_contract():
    assert "Variant-aware" in SKILL
    assert "Product_Code + Var_Code" in SKILL
    assert "[默认ASIN缺失]" in SKILL
    assert "[未找到对应变体ASIN]" in SKILL
    assert "[变体ASIN映射冲突]" in SKILL


def test_case_p_exact_m_only():
    result = resolve_variant_command("B2", "M")
    assert result["status"] == "OK"
    assert result["asin"] == "B0H8Y4B318"
    assert [row["Var_Code"] for row in result["rows"]] == ["M"]


def test_case_q_exact_s_only():
    result = resolve_variant_command("B2", "S")
    assert result["status"] == "OK"
    assert result["asin"] == "B0H8Y24R37"
    assert [row["Var_Code"] for row in result["rows"]] == ["S"]


def test_case_r_reads_product_mapping_default_asin():
    result = resolve_variant_command("B2", None)
    assert result["status"] == "OK"
    assert result["asin"] == "B0H8Y4B318"


def test_missing_product_mapping_default_is_explicit():
    assert resolve_variant_command("B2", None, product_rows=[{"Product_Code": "B2", "ASIN": ""}])["status"] == "默认ASIN缺失"


def test_case_s_unknown_variant_stops():
    assert resolve_variant_command("B2", "X")["status"] == "未找到对应变体ASIN"


def test_case_t_conflicting_asins_stop():
    rows = VARIANTS + [{"Product_Code": "B2", "Var_Code": "M", "Var_Name": "月亮款", "ASIN": "B0CONFLICT"}]
    assert resolve_variant_command("B2", "M", rows)["status"] == "变体ASIN映射冲突"
