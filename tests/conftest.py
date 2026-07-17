from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from lol_stats.models import MatchInput, TeamMatchInput


@pytest.fixture
def match_factory():
    def make(
        match_id: str,
        match_date: date,
        blue_team: str,
        red_team: str,
        blue_result: float,
        *,
        blue_kills: int = 1,
        red_kills: int = 1,
        duration_seconds: int = 1800,
        start_time_utc: datetime | None = None,
    ) -> MatchInput:
        red_result = 0.5 if blue_result == 0.5 else 1.0 - blue_result
        return MatchInput(
            source="test",
            source_match_id=match_id,
            match_date=match_date,
            duration_seconds=duration_seconds,
            server="EUW",
            championship="Test League",
            patch="1.0",
            blue=TeamMatchInput(
                team=blue_team,
                result=blue_result,
                kills_by_role={"unknown": tuple(range(blue_kills))},
            ),
            red=TeamMatchInput(
                team=red_team,
                result=red_result,
                kills_by_role={"unknown": tuple(range(red_kills))},
            ),
            start_time_utc=start_time_utc
            or datetime.combine(match_date, datetime.min.time(), tzinfo=timezone.utc),
        )

    return make
