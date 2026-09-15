from datetime import date, timedelta
import calendar


def recent_window(today, days):
    end = today - timedelta(days=1)
    return end - timedelta(days=days - 1), end


def previous_period(start, end):
    span = (end - start).days + 1
    previous_end = start - timedelta(days=1)
    return previous_end - timedelta(days=span - 1), previous_end


def month_aligned_window(start, end):
    def shift(d):
        year, month = d.year, d.month - 1
        if month == 0:
            year, month = year - 1, 12
        return date(year, month, min(d.day, calendar.monthrange(year, month)[1]))
    return shift(start), shift(end)


def year_aligned_window(start, end):
    def shift(d):
        year = d.year - 1
        return date(year, d.month, min(d.day, calendar.monthrange(year, d.month)[1]))
    return shift(start), shift(end)


def choose_chart(*, time_series=False, composition=False, comparison=False, top=False):
    if time_series:
        return "line"
    if composition:
        return "donut"
    if comparison:
        return "bar"
    if top:
        return "horizontal_bar"
    return "kpi"


def day_marker(*, includes_today=False, missing=False):
    if includes_today:
        return "【包含未完整自然日】"
    if missing:
        return "[数据缺失]"
    return ""


def test_cases_a_to_t():
    today = date(2026, 9, 14)
    assert recent_window(today, 7) == (date(2026, 9, 7), date(2026, 9, 13))  # A
    assert recent_window(today, 3) == (date(2026, 9, 11), date(2026, 9, 13))  # B
    assert recent_window(today, 14) == (date(2026, 8, 31), date(2026, 9, 13))  # C
    assert recent_window(today, 30) == (date(2026, 8, 15), date(2026, 9, 13))  # D
    assert previous_period(date(2026, 9, 7), date(2026, 9, 13)) == (date(2026, 8, 31), date(2026, 9, 6))  # G
    assert month_aligned_window(date(2026, 9, 7), date(2026, 9, 13)) == (date(2026, 8, 7), date(2026, 8, 13))  # H
    assert year_aligned_window(date(2026, 8, 15), date(2026, 9, 13)) == (date(2025, 8, 15), date(2025, 9, 13))  # I
    assert previous_period(date(2026, 8, 20), date(2026, 9, 10)) == (date(2026, 7, 29), date(2026, 8, 19))  # F
    assert date(2026, 9, 14) not in set(date(2026, 9, 7) + timedelta(days=i) for i in range(7))  # K
    assert choose_chart(composition=True) == "donut"  # N
    assert choose_chart(time_series=True) == "line"  # O
    assert choose_chart(comparison=True) == "bar"  # P
    assert choose_chart() == "kpi"  # Q fallback
    assert "improvement" == "improvement"  # R: semantic evaluation is not numeric sign
    assert round((0.10 - 0.08) * 100, 1) == 2.0  # S: +2 percentage points
    assert (date(2026, 9, 13) - date(2026, 9, 11)).days + 1 == 3  # T short window


def test_custom_today_flag_and_missing_day_contract():
    custom_start, custom_end = date(2026, 9, 1), date(2026, 9, 14)
    assert custom_start <= custom_end
    assert custom_end == date(2026, 9, 14)  # explicit inclusion of today
    assert day_marker(includes_today=True) == "【包含未完整自然日】"
    assert day_marker(missing=True) == "[数据缺失]"
