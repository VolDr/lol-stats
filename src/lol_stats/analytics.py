from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np

from .models import TeamMatchRecord


class MissingTeamError(ValueError):
    pass


class InsufficientDataError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class WinProbabilities:
    team_a_win: float
    tie: float
    team_b_win: float

    def __post_init__(self) -> None:
        total = self.team_a_win + self.tie + self.team_b_win
        if not np.isclose(total, 1.0):
            raise ValueError("probabilities must sum to 1")


def win_rate(records: Iterable[TeamMatchRecord], team: str | None = None) -> float | None:
    relevant = [record.result for record in records if team is None or record.team == team]
    if not relevant:
        return None
    return float(sum(relevant) / len(relevant))


def kills_per_minute(record: TeamMatchRecord) -> float:
    return record.total_kills / (record.duration_seconds / 60.0)


def empirical_cdf(values: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
    data = np.asarray(values, dtype=float)
    if data.size == 0:
        raise InsufficientDataError("at least one value is required")
    ordered = np.sort(data)
    probabilities = np.arange(1, ordered.size + 1, dtype=float) / ordered.size
    return ordered, probabilities


def sample_empirical(
    values: Sequence[float],
    *,
    size: int,
    rng: np.random.Generator,
) -> np.ndarray:
    if size < 0:
        raise ValueError("size must not be negative")
    data = np.asarray(values, dtype=float)
    if data.size == 0:
        raise InsufficientDataError("cannot sample an empty distribution")
    return rng.choice(data, size=size, replace=True)


def kill_score_probability(
    records: Iterable[TeamMatchRecord],
    team_a: str,
    team_b: str,
    *,
    simulations: int = 10_000,
    seed: int = 42,
) -> WinProbabilities:
    """Estimate which team records more kills, not which team wins the LoL match."""

    if simulations <= 0:
        raise ValueError("simulations must be positive")
    materialized = list(records)
    team_a_rows = [row for row in materialized if row.team == team_a]
    team_b_rows = [row for row in materialized if row.team == team_b]
    missing = [team for team, rows in ((team_a, team_a_rows), (team_b, team_b_rows)) if not rows]
    if missing:
        raise MissingTeamError(f"no matches for: {', '.join(missing)}")

    duration_minutes = [row.duration_seconds / 60.0 for row in materialized]
    if not duration_minutes:
        raise InsufficientDataError("no match durations available")

    rng = np.random.default_rng(seed)
    durations = sample_empirical(duration_minutes, size=simulations, rng=rng)
    team_a_kpm = sample_empirical(
        [kills_per_minute(row) for row in team_a_rows], size=simulations, rng=rng
    )
    team_b_kpm = sample_empirical(
        [kills_per_minute(row) for row in team_b_rows], size=simulations, rng=rng
    )

    team_a_scores = rng.poisson(np.clip(team_a_kpm * durations, 0.0, None))
    team_b_scores = rng.poisson(np.clip(team_b_kpm * durations, 0.0, None))
    a_wins = float(np.mean(team_a_scores > team_b_scores))
    ties = float(np.mean(team_a_scores == team_b_scores))
    b_wins = 1.0 - a_wins - ties
    return WinProbabilities(team_a_win=a_wins, tie=ties, team_b_win=b_wins)


def matchup_probability(
    records: Iterable[TeamMatchRecord],
    team_a: str,
    team_b: str,
    *,
    simulations: int = 10_000,
    seed: int = 42,
) -> WinProbabilities:
    """Compatibility alias for :func:`kill_score_probability`."""

    return kill_score_probability(
        records,
        team_a,
        team_b,
        simulations=simulations,
        seed=seed,
    )
