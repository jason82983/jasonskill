"""Regression checks that 6-1 no longer owns PLAN decisions."""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(p.read_text(encoding="utf-8") for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".md", ".yaml", ".py"})

def test_605_plan_6_1_apply_separation():
    for term in ("6-0-5 是唯一 PLAN 层", "6-1 是 APPLY 层", "不再运行第二套 Launch Strategy", "唯一战略目标来源", "不得重判或静默改写 605 战略"):
        assert term in TEXT

def test_technical_role_translation_and_guardrails():
    for term in ("首攻/核心 + EXACT → COR-EXA", "ROLE_TRANSLATION_AMBIGUOUS", "Base Bid", "Top of Search +50%", "只有在 605 已批准", "不突破人工上限"):
        assert term in TEXT

def test_strategy_inputs_cannot_expand_approved_targets():
    for term in ("不得扩展已批准 Target 集合", "6-1 不得自行添加 Target", "H10"):
        assert term in TEXT
