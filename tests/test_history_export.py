from __future__ import annotations

from datetime import UTC, datetime

import pytest

from scripts.fetch_odds_api_io_history import history_windows, parse_rfc3339, split_csv


def test_history_windows_respect_31_day_limit() -> None:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 3, 15, tzinfo=UTC)
    windows = list(history_windows(start, end))

    assert windows[0][0] == start
    assert windows[-1][1] == end
    assert all((window_end - window_start).days <= 30 for window_start, window_end in windows)
    assert all(
        windows[index][1].timestamp() + 1 == windows[index + 1][0].timestamp()
        for index in range(len(windows) - 1)
    )


def test_parse_rfc3339_normalizes_to_utc() -> None:
    parsed = parse_rfc3339("2026-01-01T03:00:00+03:00")
    assert parsed == datetime(2026, 1, 1, tzinfo=UTC)


def test_parse_rfc3339_rejects_naive_datetime() -> None:
    with pytest.raises(Exception, match="timezone"):
        parse_rfc3339("2026-01-01T00:00:00")


def test_split_csv_removes_empty_values() -> None:
    assert split_csv("Bet365, GG.BET, ,Unibet") == ["Bet365", "GG.BET", "Unibet"]
