from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import requests

BASE_URL = "https://api.odds-api.io/v3"
EARLIEST_HISTORY = datetime(2025, 12, 1, tzinfo=UTC)
DEFAULT_BOOKMAKERS = (
    "Bet365",
    "GG.BET",
    "Thunderpick",
    "Rivalry",
    "Betway",
    "1xBet",
    "Stake",
    "Unibet",
    "Betano",
)


def parse_rfc3339(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise argparse.ArgumentTypeError("datetime must include a timezone, for example Z")
    return parsed.astimezone(UTC)


def rfc3339(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def history_windows(start: datetime, end: datetime) -> Iterator[tuple[datetime, datetime]]:
    if start > end:
        raise ValueError("start must not be after end")
    cursor = start
    max_span = timedelta(days=31) - timedelta(seconds=1)
    while cursor <= end:
        window_end = min(cursor + max_span, end)
        yield cursor, window_end
        cursor = window_end + timedelta(seconds=1)


def split_csv(value: str) -> list[str]:
    values = [item.strip() for item in value.split(",") if item.strip()]
    if not values:
        raise argparse.ArgumentTypeError("at least one value is required")
    return values


class ApiClient:
    def __init__(self, api_key: str, *, timeout: float = 30.0, retries: int = 5) -> None:
        self.api_key = api_key
        self.timeout = timeout
        self.retries = retries
        self.session = requests.Session()

    def get(self, path: str, params: dict[str, Any]) -> Any:
        url = f"{BASE_URL}{path}"
        request_params = {"apiKey": self.api_key, **params}
        for attempt in range(self.retries + 1):
            response = self.session.get(url, params=request_params, timeout=self.timeout)
            if response.status_code == 429 and attempt < self.retries:
                retry_after = response.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else min(60.0, 2.0**attempt)
                print(f"rate limited; retrying in {delay:.1f}s", file=sys.stderr)
                time.sleep(delay)
                continue
            if response.status_code >= 500 and attempt < self.retries:
                delay = min(30.0, 2.0**attempt)
                print(
                    f"server error {response.status_code}; retrying in {delay:.1f}s",
                    file=sys.stderr,
                )
                time.sleep(delay)
                continue
            response.raise_for_status()
            remaining = response.headers.get("x-ratelimit-remaining")
            if remaining is not None:
                print(f"rate-limit remaining: {remaining}", file=sys.stderr)
            return response.json()
        raise RuntimeError("request failed after retries")


def list_lol_leagues(client: ApiClient, contains: str) -> int:
    leagues = client.get("/leagues", {"sport": "esports", "all": "true"})
    needle = contains.casefold()
    selected = [
        league
        for league in leagues
        if needle in str(league.get("name", "")).casefold()
        or needle in str(league.get("slug", "")).casefold()
    ]
    for league in selected:
        print(
            f"{league.get('slug', '')}\t{league.get('name', '')}"
            f"\tevents={league.get('eventsCount', 0)}"
        )
    print(f"found: {len(selected)}", file=sys.stderr)
    return 0


def load_completed_event_ids(path: Path) -> set[str]:
    if not path.exists():
        return set()
    completed: set[str] = set()
    with path.open("r", encoding="utf-8") as stream:
        for line in stream:
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("record_type") == "historical_odds":
                completed.add(str(record.get("event_id")))
    return completed


def append_record(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False, sort_keys=True))
        stream.write("\n")


def fetch_events(
    client: ApiClient,
    *,
    league: str,
    start: datetime,
    end: datetime,
    output: Path,
    pause: float,
) -> dict[str, dict[str, Any]]:
    events: dict[str, dict[str, Any]] = {}
    for window_start, window_end in history_windows(start, end):
        print(
            f"events {league}: {rfc3339(window_start)} .. {rfc3339(window_end)}",
            file=sys.stderr,
        )
        payload = client.get(
            "/historical/events",
            {
                "sport": "esports",
                "league": league,
                "from": rfc3339(window_start),
                "to": rfc3339(window_end),
            },
        )
        fetched_at = rfc3339(datetime.now(UTC))
        for event in payload:
            event_id = str(event["id"])
            events[event_id] = event
            append_record(
                output,
                {
                    "record_type": "historical_event",
                    "provider": "odds-api.io",
                    "fetched_at": fetched_at,
                    "league_slug": league,
                    "event": event,
                },
            )
        if pause:
            time.sleep(pause)
    return events


def fetch_event_odds(
    client: ApiClient,
    *,
    league: str,
    events: dict[str, dict[str, Any]],
    bookmakers: list[str],
    output: Path,
    pause: float,
    resume: bool,
    max_events: int | None,
) -> tuple[int, int]:
    completed = load_completed_event_ids(output) if resume else set()
    pending = [
        (event_id, event)
        for event_id, event in sorted(
            events.items(), key=lambda item: str(item[1].get("date", ""))
        )
        if event_id not in completed
    ]
    if max_events is not None:
        pending = pending[:max_events]

    downloaded = 0
    failed = 0
    for index, (event_id, event) in enumerate(pending, start=1):
        matchup = f"{event.get('home')} vs {event.get('away')}"
        print(f"odds {index}/{len(pending)}: {matchup}", file=sys.stderr)
        try:
            odds = client.get(
                "/historical/odds",
                {
                    "eventId": event_id,
                    "bookmakers": ",".join(bookmakers),
                },
            )
        except requests.HTTPError as exc:
            failed += 1
            print(f"failed event {event_id}: {exc}", file=sys.stderr)
            continue
        append_record(
            output,
            {
                "record_type": "historical_odds",
                "provider": "odds-api.io",
                "fetched_at": rfc3339(datetime.now(UTC)),
                "league_slug": league,
                "event_id": event_id,
                "event": event,
                "odds": odds,
            },
        )
        downloaded += 1
        if pause:
            time.sleep(pause)
    return downloaded, failed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Export historical League of Legends events and closing odds from Odds-API.io. "
            "Historical coverage starts in December 2025."
        )
    )
    parser.add_argument(
        "--api-key-env",
        default="ODDS_API_IO_KEY",
        help="environment variable containing the API key",
    )
    parser.add_argument(
        "--list-leagues",
        action="store_true",
        help="list esports leagues matching --contains",
    )
    parser.add_argument(
        "--contains",
        default="League of Legends",
        help="case-insensitive text used by --list-leagues",
    )
    parser.add_argument(
        "--league",
        action="append",
        help="league slug to export; repeat for multiple leagues",
    )
    parser.add_argument("--from", dest="start", type=parse_rfc3339)
    parser.add_argument("--to", dest="end", type=parse_rfc3339)
    parser.add_argument(
        "--bookmakers",
        type=split_csv,
        default=list(DEFAULT_BOOKMAKERS),
        help="comma-separated bookmaker names, maximum 30",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/raw/odds_api_io_lol_history.jsonl"),
    )
    parser.add_argument("--pause", type=float, default=0.25)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--retries", type=int, default=5)
    parser.add_argument("--max-events", type=int)
    parser.add_argument(
        "--resume",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="skip event IDs already written as historical_odds records",
    )
    parser.add_argument(
        "--events-only",
        action="store_true",
        help="download event metadata without requesting odds",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="perform API requests; without this flag only print the plan",
    )
    return parser


def validate_export_args(args: argparse.Namespace) -> None:
    if not args.league:
        raise SystemExit("provide at least one --league slug")
    if args.start is None or args.end is None:
        raise SystemExit("provide --from and --to in RFC3339 format")
    if args.start < EARLIEST_HISTORY:
        raise SystemExit(
            "Odds-API.io historical coverage starts in December 2025; "
            f"requested start was {rfc3339(args.start)}"
        )
    if args.start > args.end:
        raise SystemExit("--from must not be after --to")
    if not 1 <= len(args.bookmakers) <= 30:
        raise SystemExit("--bookmakers must contain between 1 and 30 names")
    if args.pause < 0 or args.timeout <= 0 or args.retries < 0:
        raise SystemExit("invalid pause, timeout, or retries value")
    if args.max_events is not None and args.max_events <= 0:
        raise SystemExit("--max-events must be positive")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    api_key = os.getenv(args.api_key_env)
    if not api_key:
        raise SystemExit(f"environment variable {args.api_key_env} is not set")
    client = ApiClient(api_key, timeout=args.timeout, retries=args.retries)

    if args.list_leagues:
        return list_lol_leagues(client, args.contains)

    validate_export_args(args)
    windows_per_league = len(list(history_windows(args.start, args.end)))
    print("sport: esports")
    print(f"leagues: {', '.join(args.league)}")
    print(f"period: {rfc3339(args.start)} .. {rfc3339(args.end)}")
    print(f"event-list requests: {windows_per_league * len(args.league)}")
    print(f"bookmakers: {', '.join(args.bookmakers)}")
    print(f"output: {args.out}")
    print("odds requests: one per discovered finished event")
    if not args.execute:
        print("plan only; add --execute to download")
        return 0

    total_events = 0
    total_downloaded = 0
    total_failed = 0
    for league in args.league:
        events = fetch_events(
            client,
            league=league,
            start=args.start,
            end=args.end,
            output=args.out,
            pause=args.pause,
        )
        total_events += len(events)
        print(f"unique events in {league}: {len(events)}", file=sys.stderr)
        if args.events_only:
            continue
        downloaded, failed = fetch_event_odds(
            client,
            league=league,
            events=events,
            bookmakers=args.bookmakers,
            output=args.out,
            pause=args.pause,
            resume=args.resume,
            max_events=args.max_events,
        )
        total_downloaded += downloaded
        total_failed += failed

    print(
        json.dumps(
            {
                "events": total_events,
                "odds_downloaded": total_downloaded,
                "odds_failed": total_failed,
                "output": str(args.out),
            },
            sort_keys=True,
        )
    )
    return 1 if total_failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
