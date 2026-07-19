"""League of Legends statistics toolkit."""

from .analytics import (
    MissingTeamError,
    WinProbabilities,
    kill_score_probability,
    matchup_probability,
    win_rate,
)
from .betting import BettingReport, BettingStrategy, evaluate_betting
from .config import Settings
from .db import MatchRepository
from .evaluation import EloModel, EvaluationReport, evaluate_temporally

__all__ = [
    "BettingReport",
    "BettingStrategy",
    "EloModel",
    "EvaluationReport",
    "MatchRepository",
    "MissingTeamError",
    "Settings",
    "WinProbabilities",
    "evaluate_betting",
    "evaluate_temporally",
    "kill_score_probability",
    "matchup_probability",
    "win_rate",
]
