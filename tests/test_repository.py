from __future__ import annotations

import json
import sqlite3
from datetime import date

from lol_stats.db import MatchRepository


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
