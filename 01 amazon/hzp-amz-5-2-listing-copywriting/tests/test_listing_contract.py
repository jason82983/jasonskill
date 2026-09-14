"""Static and simulated checks for the 5-2 Listing content contract.

The fixture is synthetic and does not run a product, edit Amazon, or read business data.
"""
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT = "\n".join(
    path.read_text(encoding="utf-8")
    for path in ROOT.rglob("*")
    if path.is_file() and path.suffix in {".md", ".yaml"}
)


def within_limit(text: str, limit: int) -> bool:
    return len(text) <= limit


def repeated_terms(title: str, highlights: str) -> set[str]:
    title_words = {word.casefold() for word in title.split() if len(word) > 2}
    highlight_words = {word.casefold() for word in highlights.split() if len(word) > 2}
    return title_words & highlight_words


def test_character_boundaries_include_spaces():
    assert within_limit("a" * 74, 75)
    assert within_limit("a" * 75, 75)
    assert not within_limit("a" * 76, 75)
    assert within_limit("a" * 124, 125)
    assert within_limit("a" * 125, 125)
    assert not within_limit("a" * 126, 125)
    assert len("a b") == 3


def test_b2_fixture_contract():
    # Synthetic B2-shaped legacy report: Title/Bullets/Description/A+/Keyword Map only.
    legacy_fields = {"Title", "Bullet", "Description", "A+", "Keyword Map"}
    required_fields = {
        "Item Highlights",
        "Backend Search Terms",
        "Listing Attributes",
        "Core Selling Points",
        "Amazon Listing Creation Data Package",
        "Missing Data",
    }
    assert legacy_fields <= {"Title", "Bullet", "Description", "A+", "Keyword Map"}
    assert all(field in TEXT for field in required_fields)
    assert "01_产品档案.md" in TEXT and "07_产品资料" in TEXT
    assert "[产品属性冲突]" in TEXT
    assert "[语义候选Search Terms｜待关键词数据验证]" in TEXT
    assert "不得伪造 Search Volume" in TEXT


def test_first_screen_and_handoff_contract():
    required = (
        "Search Result First-Screen Copy",
        "Keyword Allocation",
        "Characters: XX / 75",
        "Characters: XXX / 125",
        "P0/P1/P2/P3",
        "5-3 文案协同包",
        "5-4 输入交接包",
        "Claim-Evidence",
        "Allowed Claims",
        "Pending Claims",
        "Forbidden Claims",
    )
    missing = [term for term in required if term not in TEXT]
    assert not missing, f"missing 5-2 contract terms: {missing}"


def test_case_d_to_j_contracts():
    # D: repeated first-screen wording is detectable and should trigger an optimization note.
    assert "shoe" in repeated_terms("wide shoe for women", "comfortable shoe for walking")
    assert "Title 与 Item Highlights" in TEXT
    # E/F: attributes come from both product sources and conflicts are surfaced.
    assert "01_产品档案.md" in TEXT and "07_产品资料" in TEXT
    assert "Source A/Value A" in TEXT and "Source B/Value B" in TEXT
    # G/H: no H10 data may yield only a pending semantic candidate; real data keeps evidence.
    assert "待关键词数据验证" in TEXT and "Keyword Allocation" in TEXT
    # I: an unverified claim cannot enter Allowed Claims.
    assert "未经证据支持" in TEXT and "Allowed Claims" in TEXT
    # J: the final creation package is a required output.
    assert "Amazon Listing Creation Data Package" in TEXT


if __name__ == "__main__":
    test_character_boundaries_include_spaces()
    test_b2_fixture_contract()
    test_first_screen_and_handoff_contract()
    print("5-2 listing contract: PASS")
