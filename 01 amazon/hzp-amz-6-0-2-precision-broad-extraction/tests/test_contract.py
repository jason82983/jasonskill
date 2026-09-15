from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = (ROOT / "SKILL.md").read_text(encoding="utf-8-sig")
README = (ROOT / "README.md").read_text(encoding="utf-8-sig")
REF = (ROOT / "references" / "broad-seed-cluster-v1.md").read_text(encoding="utf-8-sig")


def test_identity_and_boundaries():
    assert "hzp-amz-6-0-2-precision-broad-extraction" in SKILL
    assert "6-0-1_[Product_Code]_AI精准词.csv" in SKILL
    assert "不重新连接 SQL" in SKILL
    assert "排名、广告策略" in SKILL


def test_three_column_output_contract():
    for term in ("词", "中文", "同意思词的合并总量", "降序", "至少两个英文单词"):
        assert term in SKILL
    assert "关键词族" in SKILL and "不生成关键词族" in SKILL
    assert "6-0-2_[Product_Code]_精准泛词.csv" in REF


if __name__ == "__main__":
    test_identity_and_boundaries()
    test_three_column_output_contract()
    print("6-0-2 contract tests: PASS")
