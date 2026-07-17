from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timezone

import pytest

from lol_stats.db import MatchRepository
from lol_stats.models import OddsQuoteInput


def test_schema_uses_json_and_bound_parameters(tmp_path, match_factory) -> None:
    repository = MatchRepository(tmp_path / "stats.sqlite")
    suspicious_name = "Team ' OR 1=1 --"
    repository.save_match(
        match_factory("1", date(2020, 1, 1), suspicious_name, "Normal", 1.0)
    )

    rows = repository.iter_team_matches(team=suspicious_name)
    assert len(rows) == 1
    assert rows[0].team == suspicious_name

    with sqlite3.connect(repository.db_path) as connection:
        raw = connection.execute(
            "SELECT kills_json FROM team_match_stats WHERE team = ?", (suspicious_name,)
        ).fetchone()[0]
    assert isinstance(json.loads(raw), dict)


def test_missing_team_query_returns_empty_list(tmp_path) -> None:
    repository = MatchRepository(tmp_path / "stats.sqlite")
    assert repository.iter_team_matches(team="Nobody") == []


def test_odds_round_trip(tmp_path, match_factory) -> None:
    repository = MatchRepository(tmp_path / "stats.sqlite")
    repository.save_match(
        match_factory(
            "1",
            date(2020, 1, 2),
            "Alpha",
            "Beta",
            1.0,
            start_time_utc=datetime(2020, 1, 2, 18, tzinfo=timezone.utc),
        )
    )
    repository.save_odds_quote(
        OddsQuoteInput(
            source="test",
            source_match_id="1",
            bookmaker="Book",
            captured_at=datetime(2020, 1, 2, 16, tzinfo=timezone.utc),
            team_a="Alpha",
            team_b="Beta",
            team_a_odds=2.1,
            team_b_odds=1.8,
        )
    )
    quotes = repository.iter_odds_quotes()
    assert len(quotes) == 1
    assert quotes[0].team_a_odds == 2.1


def test_odds_team_order_must_match_match(tmp_path, match_factory) -> None:
    repository = MatchRepository(tmp_path / "stats.sqlite")
    repository.save_match(match_factory("1", date(2020, 1, 2), "Alpha", "Beta", 1.0))
    with pytest.raises(ValueError, match="team order"):
        repository.save_odds_quote(
            OddsQuoteInput(
                source="test",
                source_match_id="1",
                bookmaker="Book",
                captured_at=datetime(2020, 1, 2, 16, tzinfo=timezone.utc),
                team_a="Beta",
                team_b="Alpha",
                team_a_odds=2.1,
                team_b_odds=1.8,
            )
        )
