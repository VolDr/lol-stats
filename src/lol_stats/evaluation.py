from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from .models import CanonicalMatch


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    train_matches: int
    test_matches: int
    decisive_test_matches: int
    brier_score: float | None
    log_loss: float | None
    accuracy: float | None


class EloModel:
    def __init__(
        self,
        *,
        initial_rating: float = 1500.0,
        k_factor: float = 24.0,
        scale: float = 400.0,
        team_a_advantage: float = 0.0,
    ) -> None:
        if k_factor <= 0:
            raise ValueError("k_factor must be positive")
        if scale <= 0:
            raise ValueError("scale must be positive")
        self.initial_rating = initial_rating
        self.k_factor = k_factor
        self.scale = scale
        self.team_a_advantage = team_a_advantage
        self.ratings: dict[str, float] = {}

    def rating(self, team: str) -> float:
        return self.ratings.get(team, self.initial_rating)

    def predict(self, team_a: str, team_b: str) -> float:
        adjusted_a = self.rating(team_a) + self.team_a_advantage
        difference = self.rating(team_b) - adjusted_a
        return 1.0 / (1.0 + 10.0 ** (difference / self.scale))

    def update(self, team_a: str, team_b: str, result_a: float) -> None:
        if result_a not in {0.0, 0.5, 1.0}:
            raise ValueError("result_a must be 0.0, 0.5 or 1.0")
        predicted = self.predict(team_a, team_b)
        delta = self.k_factor * (result_a - predicted)
        self.ratings[team_a] = self.rating(team_a) + delta
        self.ratings[team_b] = self.rating(team_b) - delta


def evaluate_temporally(
    matches: Iterable[CanonicalMatch],
    *,
    train_start: date | None = None,
    train_end: date,
    test_start: date,
    test_end: date,
    update_during_test: bool = True,
    initial_rating: float = 1500.0,
    k_factor: float = 24.0,
    scale: float = 400.0,
    team_a_advantage: float = 0.0,
) -> EvaluationReport:
    if train_end >= test_start:
        raise ValueError("train_end must be before test_start")
    if test_start > test_end:
        raise ValueError("test_start must not be after test_end")
    if train_start is not None and train_start > train_end:
        raise ValueError("train_start must not be after train_end")

    ordered = sorted(matches, key=lambda item: (item.match_date, item.source_match_id))
    training = [
        item
        for item in ordered
        if item.match_date <= train_end and (train_start is None or item.match_date >= train_start)
    ]
    testing = [item for item in ordered if test_start <= item.match_date <= test_end]

    model = EloModel(
        initial_rating=initial_rating,
        k_factor=k_factor,
        scale=scale,
        team_a_advantage=team_a_advantage,
    )
    for match in training:
        model.update(match.team_a, match.team_b, match.result_a)

    squared_errors: list[float] = []
    log_losses: list[float] = []
    decisive_correct: list[bool] = []
    epsilon = 1e-12

    for match in testing:
        prediction = model.predict(match.team_a, match.team_b)
        squared_errors.append((prediction - match.result_a) ** 2)
        clipped = min(max(prediction, epsilon), 1.0 - epsilon)
        if match.result_a == 0.5:
            log_losses.append(-0.5 * (math.log(clipped) + math.log(1.0 - clipped)))
        else:
            log_losses.append(
                -(match.result_a * math.log(clipped) + (1.0 - match.result_a) * math.log(1.0 - clipped))
            )
            decisive_correct.append((prediction >= 0.5) == (match.result_a == 1.0))
        if update_during_test:
            model.update(match.team_a, match.team_b, match.result_a)

    return EvaluationReport(
        train_matches=len(training),
        test_matches=len(testing),
        decisive_test_matches=len(decisive_correct),
        brier_score=None if not squared_errors else sum(squared_errors) / len(squared_errors),
        log_loss=None if not log_losses else sum(log_losses) / len(log_losses),
        accuracy=None if not decisive_correct else sum(decisive_correct) / len(decisive_correct),
    )
