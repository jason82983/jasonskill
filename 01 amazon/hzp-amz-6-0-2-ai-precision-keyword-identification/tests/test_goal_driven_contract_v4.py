from pathlib import Path


SKILL_ROOT = Path(__file__).resolve().parents[1]


def test_goal_driven_contract_makes_completion_business_goal_not_batch():
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "Goal-Driven Production Contract (V4)" in text
    assert "不得把单个Batch完成报告为602完成" in text
    assert "只有全部Completion Criteria成立" in text
    assert "当前执行本 Skill 的 Codex/Agent就是唯一Precision AI Judge" in text
    assert "Batch、循环、Checkpoint、Resume只是内部实现细节" in text


def test_goal_driven_contract_rejects_second_ai_and_local_fallback():
    text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert "正常入口不要求任何 `agent_judge`" in text
    assert "不得用Regex、Token Match、固定Score、Local Heuristic或Fallback" in text
    assert "DEPRECATED_FOR_602_PRODUCTION" in text


def test_agent_prompt_is_goal_driven():
    text = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert "complete the full goal" in text
    assert "The current Codex/Agent is the only Precision AI Judge" in text
    assert "never treat one batch as task completion" in text
    assert "never wait for or request a second AI" in text
