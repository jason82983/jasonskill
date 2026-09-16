from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_multiple_benchmarks_do_not_multiply_launch_architecture_or_market_facts():
    for name in ("SKILL.md", "README.md"):
        text = (ROOT / name).read_text(encoding="utf-8-sig")
        assert "多个 Benchmark 不复制广告架构" in text or "多个 Benchmark remain evidence for one Current Product architecture" in text
        assert "只贡献一次" in text or "只计一次" in text
        assert "任何 Target 仍须由 6-0-5 明确批准" in text or "one Current Product architecture" in text
