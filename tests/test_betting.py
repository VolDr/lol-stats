from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from lol_stats.betting import (
    BettingStrategy,
    evaluate_betting,
    expected_value,
    kelly_fraction,
    remove_overround,
)
from lol_stats.models import CanonicalMatch, OddsQuoteRecord


def quote(
    match_id: str,
    captured_hour: int,
    odds_a: float,
    odds_b: float,
    *,
    bookmaker: str = "Book",
) -> OddsQuoteRecord:
    start = datetime(2020, 1, 2, 18, 0, tzinfo=UTC)
    return OddsQuoteRecord(
        source="test",
        source_match_id=match_id,
        match_date=date(2020, 1, 2),
        start_time_utc=start,
        team_a="Alpha",
        team_b="Beta",
        result_a=1.0,
        bookmaker=bookmaker,
        captured_at=datetime(2020, 1, 2, captured_hour, 0, tzinfo=UTC),
        team_a_odds=odds_a,
        team_b_odds=odds_b,
    )


def test_overround_is_removed() -> None:
    market = remove_overround(1.80, 2.10)
    assert market.team_a + market.team_b == pytest.approx(1.0)
    assert market.overround > 0


def test_expected_value_and_kelly_are_consistent() -> None:
    assert expected_value(0.60, 2.0) == pytest.approx(0.20)
    assert kelly_fraction(0.60, 2.0) == pytest.approx(0.20)
    assert kelly_fraction(0.40, 2.0) == 0.0


def test_backtest_uses_latest_quote_before_decision_cutoff() -> None:
    start = datetime(2020, 1, 2, 18, 0, tzinfo=UTC)
    matches = [
        CanonicalMatch("train", date(2019, 1, 1), "Alpha", "Beta", 1.0, source="test"),
        CanonicalMatch(
            "test",
            date(2020, 1, 2),
            "Alpha",
            "Beta",
            1.0,
            start_time_utc=start,
            source="test",
        ),
    ]
    quotes = [
        quote("test", 16, 2.20, 1.75),
        quote("test", 18, 3.50, 1.30),
    ]
    report = evaluate_betting(
        matches,
        quotes,
        train_end=date(2019, 12, 31),
        test_start=date(2020, 1, 1),
        test_end=date(2020, 12, 31),
        strategy=BettingStrategy(
            min_edge=0.0,
            min_expected_value=0.0,
            kelly_multiplier=0.25,
            max_stake_fraction=0.05,
            decision_minutes_before_start=60,
        ),
    )
    assert report.bets == 1
    assert report.bet_records[0].odds == 2.20
    assert report.bet_records[0].profit > 0


def test_quote_after_start_is_ignored() -> None:
    start = datetime(2020, 1, 2, 18, 0, tzinfo=UTC)
    matches = [
        CanonicalMatch(
            "test",
            date(2020, 1, 2),
            "Alpha",
            "Beta",
            1.0,
            start_time_utc=start,
            source="test",
        )
    ]
    quotes = [quote("test", 19, 10.0, 1.05)]
    report = evaluate_betting(
        matches,
        quotes,
        train_end=date(2019, 12, 31),
        test_start=date(2020, 1, 1),
        test_end=date(2020, 12, 31),
    )
    assert report.priced_matches == 0
    assert report.bets == 0


def test_market_weight_one_produces_no_value_signal() -> None:
    start = datetime(2020, 1, 2, 18, 0, tzinfo=UTC)
    matches = [
        CanonicalMatch(
            "test",
            date(2020, 1, 2),
            "Alpha",
            "Beta",
            1.0,
            start_time_utc=start,
            source="test",
        )
    ]
    report = evaluate_betting(
        matches,
        [quote("test", 16, 2.20, 1.75)],
        train_end=date(2019, 12, 31),
        test_start=date(2020, 1, 1),
        test_end=date(2020, 12, 31),
        strategy=BettingStrategy(
            min_edge=0.001,
            min_expected_value=0.001,
            market_weight=1.0,
        ),
    )
    assert report.bets == 0
