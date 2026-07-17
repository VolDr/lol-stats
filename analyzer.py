"""Compatibility facade for the original monolithic analyzer module.

New code should import from ``lol_stats`` directly. The old exploratory betting and plotting
routines were intentionally not retained because they depended on unsafe pickle blobs,
dynamic SQL and hard-coded local tables.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from lol_stats.analytics import matchup_probability, win_rate
from lol_stats.config import Settings
from lol_stats.db import MatchRepository


def _repository(db_path: str | Path | None = None) -> MatchRepository:
    settings = Settings.from_env()
    return MatchRepository(db_path or settings.db_path)


def get_team_win_rate(
    team: str,
    *,
    db_path: str | Path | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    server: str | None = None,
) -> float | None:
    rows = _repository(db_path).iter_team_matches(
        team=team, start_date=start_date, end_date=end_date, server=server
    )
    return win_rate(rows, team)


def get_teams_win_rate(
    *,
    db_path: str | Path | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    server: str | None = None,
) -> dict[str, float | None]:
    repository = _repository(db_path)
    return {
        team: get_team_win_rate(
            team,
            db_path=db_path,
            start_date=start_date,
            end_date=end_date,
            server=server,
        )
        for team in repository.team_names()
    }


def get_P_win_in_match(
    server: str,
    team1: str,
    team2: str,
    start_date: date,
    last_date: date,
    table_name: str | None = None,
    *,
    db_path: str | Path | None = None,
    simulations: int = 10_000,
    seed: int = 42,
) -> list[list[float]]:
    if table_name not in {None, "team_match_stats"}:
        raise ValueError("dynamic table names are no longer supported")
    rows = _repository(db_path).iter_team_matches(
        start_date=start_date,
        end_date=last_date,
        server=server,
    )
    probabilities = matchup_probability(
        rows,
        team1,
        team2,
        simulations=simulations,
        seed=seed,
    )
    return [[probabilities.team_a_win, probabilities.team_b_win]]
