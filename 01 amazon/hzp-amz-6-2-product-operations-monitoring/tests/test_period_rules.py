"""Compatibility tests for the DATA ONLY report's fact-window behavior."""
from datetime import date, timedelta
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from ad_facts_package import _window_views  # noqa: E402


def test_html_windows_filter_daily_facts_and_preserve_window_grain():
    today = date.today()
    rows = [{"Date": (today - timedelta(days=n)).isoformat(), "Spend": 1, "Clicks": 1,
             "Impressions": 2, "Orders": 0, "Sales": 0} for n in range(1, 41)]
    views = _window_views({"campaign": rows, "intent": [{"Date": None, "Spend": 99}]}, today - timedelta(days=1))
    assert len(views["YESTERDAY"]["tables"]["campaign"]) == 1
    assert len(views["3D"]["tables"]["campaign"]) == 3
    assert len(views["30D"]["tables"]["campaign"]) == 30
    assert len(views["7D"]["tables"]["intent"]) == 1
    assert views["7D"]["grain"] == "MIXED"
    assert views["7D"]["grainByLayer"] == {"campaign": "DAY", "intent": "SOURCE_WINDOW"}


def test_source_window_only_is_not_split_into_fictitious_days():
    today = date.today()
    views = _window_views({"campaign": [{"Date": None, "Spend": 7, "Clicks": 2,
                                          "Impressions": 10, "Orders": 1, "Sales": 20}]}, today - timedelta(days=1))
    assert views["YESTERDAY"]["grain"] == "SOURCE_WINDOW"
    assert views["YESTERDAY"]["tables"]["campaign"] == views["30D"]["tables"]["campaign"]
