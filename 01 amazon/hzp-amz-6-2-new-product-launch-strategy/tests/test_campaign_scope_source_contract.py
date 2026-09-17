"""Regression checks for the 6-2 Runtime Campaign Scope source contract."""

import sys
from pathlib import Path


SKILLS_ROOT = Path(__file__).resolve().parents[1].parent
if str(SKILLS_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILLS_ROOT))

from scripts.campaign_scope_contract import load_product_campaign_scope  # noqa: E402


def test_scope_is_read_only_from_product_profile(tmp_path):
    (tmp_path / "01_产品档案.md").write_text(
        "ProductCode = B2\nCampaignTag = M\nCampaignPrefix = B2.M.\n",
        encoding="utf-8",
    )
    (tmp_path / "04_产品推广思路.md").write_text(
        "ProductCode = WRONG\nCampaignTag = WRONG\nCampaignPrefix = WRONG.\n",
        encoding="utf-8",
    )
    assert load_product_campaign_scope(tmp_path) == {
        "ProductCode": "B2",
        "CampaignTag": "M",
        "CampaignPrefix": "B2.M.",
    }


def test_skill_docs_identify_the_two_file_boundaries():
    root = Path(__file__).resolve().parents[1]
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    framework = (root / "references" / "launch-framework.md").read_text(encoding="utf-8")
    assert "01_产品档案.md` 是 6-2 Runtime Campaign Scope 的唯一技术配置来源" in skill
    assert "04_产品推广思路.md` 仅作为人工推广思路" in skill
    assert "01_产品档案.md` 是 6-2 Runtime Campaign Scope 的唯一技术配置来源" in framework
    assert "04_产品推广思路.md` 是人工输入和 AI 决策参考" in framework
