from __future__ import annotations

import json
from collections.abc import Iterable, Iterator, Mapping
from datetime import date, datetime
from pathlib import Path
from typing import Any, Protocol

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .db import MatchRepository
from .models import MatchInput, OddsQuoteInput, TeamMatchInput


class MatchSource(Protocol):
    def iter_matches(self) -> Iterable[MatchInput]: ...


class OddsSource(Protocol):
    def iter_quotes(self) -> Iterable[OddsQuoteInput]: ...


def ingest_source(repository: MatchRepository, source: MatchSource) -> int:
    count = 0
    for match in source.iter_matches():
        repository.save_match(match)
        count += 1
    return count


def ingest_odds_source(repository: MatchRepository, source: OddsSource) -> int:
    count = 0
    for quote in source.iter_quotes():
        repository.save_odds_quote(quote)
        count += 1
    return count


def _datetime(value: object) -> datetime:
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("datetime must include a timezone")
    return parsed


class JsonLinesSource:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def iter_matches(self) -> Iterator[MatchInput]:
        with self.path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                    yield match_from_mapping(payload)
                except Exception as exc:
                    raise ValueError(f"invalid JSONL match at line {line_number}") from exc


class OddsJsonLinesSource:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def iter_quotes(self) -> Iterator[OddsQuoteInput]:
        with self.path.open("r", encoding="utf-8") as stream:
            for line_number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                try:
                    payload = json.loads(line)
                    yield odds_quote_from_mapping(payload)
                except Exception as exc:
                    raise ValueError(f"invalid JSONL odds quote at line {line_number}") from exc


class HttpJsonClient:
    """Retrying HTTP client for source adapters.

    Analytics never imports this module, so website/API changes remain isolated from the
    mathematical layer.
    """

    def __init__(self, timeout_seconds: float = 20.0) -> None:
        self.timeout_seconds = timeout_seconds
        self.session = requests.Session()
        retry = Retry(
            total=4,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET"}),
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))
        self.session.mount("http://", HTTPAdapter(max_retries=retry))

    def get_json(self, url: str) -> Any:
        response = self.session.get(url, timeout=self.timeout_seconds)
        response.raise_for_status()
        return response.json()


def match_from_mapping(payload: Mapping[str, Any]) -> MatchInput:
    def team(key: str) -> TeamMatchInput:
        item = payload[key]
        return TeamMatchInput(
            team=str(item["team"]),
            result=float(item["result"]),
            kills_by_role={
                str(role): tuple(float(value) for value in values)
                for role, values in dict(item.get("kills_by_role", {})).items()
            },
        )

    start_time = payload.get("start_time_utc")
    match = MatchInput(
        source=str(payload["source"]),
        source_match_id=str(payload["source_match_id"]),
        match_date=date.fromisoformat(str(payload["match_date"])),
        duration_seconds=int(payload["duration_seconds"]),
        server=str(payload.get("server", "UNKNOWN")),
        championship=str(payload.get("championship", "UNKNOWN")),
        patch=None if payload.get("patch") is None else str(payload["patch"]),
        blue=team("blue"),
        red=team("red"),
        start_time_utc=None if start_time is None else _datetime(start_time),
    )
    match.validate()
    return match


def odds_quote_from_mapping(payload: Mapping[str, Any]) -> OddsQuoteInput:
    quote = OddsQuoteInput(
        source=str(payload["source"]),
        source_match_id=str(payload["source_match_id"]),
        bookmaker=str(payload["bookmaker"]),
        captured_at=_datetime(payload["captured_at"]),
        team_a=str(payload["team_a"]),
        team_b=str(payload["team_b"]),
        team_a_odds=float(payload["team_a_odds"]),
        team_b_odds=float(payload["team_b_odds"]),
    )
    quote.validate()
    return quote
