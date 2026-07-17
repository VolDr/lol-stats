from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Mapping, Sequence

VALID_ROLES = frozenset({"top", "jungle", "mid", "adc", "support", "unknown"})


@dataclass(frozen=True, slots=True)
class TeamMatchInput:
    team: str
    result: float
    kills_by_role: Mapping[str, Sequence[float]]

    def validate(self) -> None:
        if not self.team.strip():
            raise ValueError("team must not be empty")
        if self.result not in {0.0, 0.5, 1.0}:
            raise ValueError("result must be 0.0, 0.5 or 1.0")
        invalid_roles = set(self.kills_by_role) - VALID_ROLES
        if invalid_roles:
            raise ValueError(f"unsupported roles: {sorted(invalid_roles)}")
        for role, timestamps in self.kills_by_role.items():
            if any(float(value) < 0 for value in timestamps):
                raise ValueError(f"negative kill timestamp for role {role}")


@dataclass(frozen=True, slots=True)
class MatchInput:
    source: str
    source_match_id: str
    match_date: date
    duration_seconds: int
    server: str
    championship: str
    patch: str | None
    blue: TeamMatchInput
    red: TeamMatchInput

    def validate(self) -> None:
        if not self.source.strip() or not self.source_match_id.strip():
            raise ValueError("source and source_match_id must not be empty")
        if self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be positive")
        self.blue.validate()
        self.red.validate()
        if self.blue.team == self.red.team:
            raise ValueError("a team cannot play itself")
        if self.blue.result + self.red.result != 1.0:
            raise ValueError("blue and red results must sum to 1.0")


@dataclass(frozen=True, slots=True)
class TeamMatchRecord:
    source_match_id: str
    match_date: date
    duration_seconds: int
    server: str
    championship: str
    patch: str | None
    team: str
    opponent: str
    side: str
    result: float
    kills_by_role: dict[str, tuple[float, ...]]

    @property
    def total_kills(self) -> int:
        return sum(len(values) for values in self.kills_by_role.values())


@dataclass(frozen=True, slots=True)
class CanonicalMatch:
    source_match_id: str
    match_date: date
    team_a: str
    team_b: str
    result_a: float
