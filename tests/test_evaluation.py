from __future__ import annotations

from datetime import date

from lol_stats.evaluation import EloModel, evaluate_temporally
from lol_stats.models import CanonicalMatch


def test_temporal_evaluation_ignores_future_matches() -> None:
    base = [
        CanonicalMatch("train", date(2019, 1, 1), "Alpha", "Beta", 1.0),
        CanonicalMatch("test", date(2020, 1, 1), "Alpha", "Beta", 1.0),
    ]
    future = CanonicalMatch("future", date(2022, 1, 1), "Beta", "Alpha", 1.0)
    kwargs = {
        "train_end": date(2019, 12, 31),
        "test_start": date(2020, 1, 1),
        "test_end": date(2020, 12, 31),
    }
    assert evaluate_temporally(base, **kwargs) == evaluate_temporally(base + [future], **kwargs)


def test_ties_are_scored_but_not_counted_as_decisive_accuracy() -> None:
    report = evaluate_temporally(
        [CanonicalMatch("tie", date(2020, 1, 1), "Alpha", "Beta", 0.5)],
        train_end=date(2019, 12, 31),
        test_start=date(2020, 1, 1),
        test_end=date(2020, 12, 31),
    )
    assert report.test_matches == 1
    assert report.decisive_test_matches == 0
    assert report.accuracy is None
    assert report.brier_score == 0.0


def test_empty_test_window_returns_none_metrics() -> None:
    report = evaluate_temporally(
        [CanonicalMatch("train", date(2019, 1, 1), "Alpha", "Beta", 1.0)],
        train_end=date(2019, 12, 31),
        test_start=date(2020, 1, 1),
        test_end=date(2020, 12, 31),
    )
    assert report.test_matches == 0
    assert report.brier_score is None
    assert report.log_loss is None
    assert report.accuracy is None


def test_blue_advantage_changes_initial_probability() -> None:
    model = EloModel(team_a_advantage=50.0)
    assert model.predict("Alpha", "Beta") > 0.5
