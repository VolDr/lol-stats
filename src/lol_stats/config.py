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

    def __post_init__(self) -> None:
        if self.train_start > self.train_end:
            raise ValueError("train_start must not be after train_end")
        if self.test_start > self.test_end:
            raise ValueError("test_start must not be after test_end")
        if self.train_end >= self.test_start:
            raise ValueError("training and test windows must not overlap")

    @classmethod
    def from_env(cls) -> "Settings":
        defaults = cls()
        return cls(
            db_path=Path(os.getenv("LOL_STATS_DB_PATH", str(defaults.db_path))),
            train_start=_env_date("LOL_STATS_TRAIN_START", defaults.train_start),
            train_end=_env_date("LOL_STATS_TRAIN_END", defaults.train_end),
            test_start=_env_date("LOL_STATS_TEST_START", defaults.test_start),
            test_end=_env_date("LOL_STATS_TEST_END", defaults.test_end),
            random_seed=int(os.getenv("LOL_STATS_RANDOM_SEED", str(defaults.random_seed))),
        )
