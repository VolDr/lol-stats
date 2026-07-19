from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path


def _env_date(name: str, default: date) -> date:
    raw = os.getenv(name)
    return date.fromisoformat(raw) if raw else default


@dataclass(frozen=True, slots=True)
class Settings:
    db_path: Path = Path("data/lol_stats.sqlite")
    train_start: date = date(2015, 12, 18)
    train_end: date = date(2019, 12, 31)
    test_start: date = date(2020, 1, 1)
    test_end: date = date(2020, 5, 20)
    random_seed: int = 42
    bet_min_edge: float = 0.03
    bet_min_expected_value: float = 0.02
    bet_kelly_multiplier: float = 0.25
    bet_max_stake_fraction: float = 0.03
    bet_decision_minutes_before_start: int = 60
    bet_market_weight: float = 0.0

    def __post_init__(self) -> None:
        if self.train_start > self.train_end:
            raise ValueError("train_start must not be after train_end")
        if self.test_start > self.test_end:
            raise ValueError("test_start must not be after test_end")
        if self.train_end >= self.test_start:
            raise ValueError("training and test windows must not overlap")
        if self.bet_min_edge < 0 or self.bet_min_expected_value < 0:
            raise ValueError("bet thresholds must not be negative")
        if not 0.0 <= self.bet_kelly_multiplier <= 1.0:
            raise ValueError("bet_kelly_multiplier must be between 0 and 1")
        if not 0.0 < self.bet_max_stake_fraction <= 1.0:
            raise ValueError("bet_max_stake_fraction must be in (0, 1]")
        if self.bet_decision_minutes_before_start < 0:
            raise ValueError("bet decision offset must not be negative")
        if not 0.0 <= self.bet_market_weight <= 1.0:
            raise ValueError("bet_market_weight must be between 0 and 1")

    @classmethod
    def from_env(cls) -> Settings:
        defaults = cls()
        return cls(
            db_path=Path(os.getenv("LOL_STATS_DB_PATH", str(defaults.db_path))),
            train_start=_env_date("LOL_STATS_TRAIN_START", defaults.train_start),
            train_end=_env_date("LOL_STATS_TRAIN_END", defaults.train_end),
            test_start=_env_date("LOL_STATS_TEST_START", defaults.test_start),
            test_end=_env_date("LOL_STATS_TEST_END", defaults.test_end),
            random_seed=int(os.getenv("LOL_STATS_RANDOM_SEED", str(defaults.random_seed))),
            bet_min_edge=float(os.getenv("LOL_STATS_BET_MIN_EDGE", defaults.bet_min_edge)),
            bet_min_expected_value=float(
                os.getenv("LOL_STATS_BET_MIN_EV", defaults.bet_min_expected_value)
            ),
            bet_kelly_multiplier=float(
                os.getenv("LOL_STATS_BET_KELLY_MULTIPLIER", defaults.bet_kelly_multiplier)
            ),
            bet_max_stake_fraction=float(
                os.getenv("LOL_STATS_BET_MAX_STAKE_FRACTION", defaults.bet_max_stake_fraction)
            ),
            bet_decision_minutes_before_start=int(
                os.getenv(
                    "LOL_STATS_BET_DECISION_MINUTES",
                    defaults.bet_decision_minutes_before_start,
                )
            ),
            bet_market_weight=float(
                os.getenv("LOL_STATS_BET_MARKET_WEIGHT", defaults.bet_market_weight)
            ),
        )
