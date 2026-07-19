from __future__ import annotations

from datetime import date

import numpy as np
import pytest

from lol_stats.analytics import MissingTeamError, matchup_probability, sample_empirical, win_rate
from lol_stats.db import MatchRepository


def test_empty_win_rate_is_none() -> None:
    assert win_rate([]) is None


def test_missing_team_is_explicit(tmp_path, match_factory) -> None:
    repository = MatchRepository(tmp_path / "stats.sqlite")
    repository.save_match(match_factory("1", date(2020, 1, 1), "Alpha", "Beta", 1.0))
    with pytest.raises(MissingTeamError):
        matchup_probability(repository.iter_team_matches(), "Alpha", "Missing", simulations=10)


def test_zero_variance_sampling_is_stable() -> None:
    rng = np.random.default_rng(1)
    sampled = sample_empirical([3.0, 3.0, 3.0], size=20, rng=rng)
    assert sampled.tolist() == [3.0] * 20


def test_zero_kill_teams_produce_only_ties(tmp_path, match_factory) -> None:
    repository = MatchRepository(tmp_path / "stats.sqlite")
    repository.save_match(
        match_factory(
            "1",
            date(2020, 1, 1),
            "Alpha",
            "Beta",
            0.5,
            blue_kills=0,
            red_kills=0,
        )
    )
    probabilities = matchup_probability(
        repository.iter_team_matches(), "Alpha", "Beta", simulations=100, seed=1
    )
    assert probabilities.team_a_win == 0.0
    assert probabilities.tie == 1.0
    assert probabilities.team_b_win == 0.0
