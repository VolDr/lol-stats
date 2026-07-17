from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from datetime import date
from pathlib import Path

from .betting import BettingStrategy, evaluate_betting
from .config import Settings
from .db import MatchRepository
from .evaluation import evaluate_temporally
from .ingest import (
    JsonLinesSource,
    OddsJsonLinesSource,
    ingest_odds_source,
    ingest_source,
)


def _date(value: str) -> date:
    return date.fromisoformat(value)


def _add_dates(command: argparse.ArgumentParser) -> None:
    command.add_argument("--train-start", type=_date)
    command.add_argument("--train-end", type=_date)
    command.add_argument("--test-start", type=_date)
    command.add_argument("--test-end", type=_date)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(prog="lol-stats")
    subcommands = command.add_subparsers(dest="command", required=True)

    init_db = subcommands.add_parser("init-db", help="create or upgrade the SQLite schema")
    init_db.add_argument("--db-path")

    import_jsonl = subcommands.add_parser("import-jsonl", help="import normalized match JSONL")
    import_jsonl.add_argument("path")
    import_jsonl.add_argument("--db-path")

    import_odds = subcommands.add_parser(
        "import-odds-jsonl", help="import pre-match decimal odds JSONL"
    )
    import_odds.add_argument("path")
    import_odds.add_argument("--db-path")

    evaluate = subcommands.add_parser("evaluate", help="run a chronological Elo backtest")
    evaluate.add_argument("--db-path")
    _add_dates(evaluate)
    evaluate.add_argument("--frozen-test", action="store_true")
    evaluate.add_argument("--k-factor", type=float, default=24.0)
    evaluate.add_argument("--elo-scale", type=float, default=400.0)
    evaluate.add_argument("--blue-advantage", type=float, default=0.0)

    betting = subcommands.add_parser(
        "backtest-betting", help="backtest value betting against pre-match odds"
    )
    betting.add_argument("--db-path")
    _add_dates(betting)
    betting.add_argument("--bookmaker")
    betting.add_argument("--frozen-test", action="store_true")
    betting.add_argument("--starting-bankroll", type=float, default=100.0)
    betting.add_argument("--min-edge", type=float)
    betting.add_argument("--min-ev", type=float)
    betting.add_argument("--kelly-multiplier", type=float)
    betting.add_argument("--max-stake-fraction", type=float)
    betting.add_argument("--decision-minutes", type=int)
    betting.add_argument("--market-weight", type=float)
    betting.add_argument("--k-factor", type=float, default=24.0)
    betting.add_argument("--elo-scale", type=float, default=400.0)
    betting.add_argument("--blue-advantage", type=float, default=0.0)
    return command


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    settings = Settings.from_env()
    if getattr(args, "db_path", None):
        settings = replace(settings, db_path=Path(args.db_path))
    repository = MatchRepository(settings.db_path)

    if args.command == "init-db":
        repository.initialize()
        print(settings.db_path)
        return 0

    if args.command == "import-jsonl":
        count = ingest_source(repository, JsonLinesSource(args.path))
        print(json.dumps({"imported": count}))
        return 0

    if args.command == "import-odds-jsonl":
        count = ingest_odds_source(repository, OddsJsonLinesSource(args.path))
        print(json.dumps({"imported": count}))
        return 0

    train_start = args.train_start or settings.train_start
    train_end = args.train_end or settings.train_end
    test_start = args.test_start or settings.test_start
    test_end = args.test_end or settings.test_end

    if args.command == "evaluate":
        report = evaluate_temporally(
            repository.iter_canonical_matches(),
            train_start=train_start,
            train_end=train_end,
            test_start=test_start,
            test_end=test_end,
            update_during_test=not args.frozen_test,
            k_factor=args.k_factor,
            scale=args.elo_scale,
            team_a_advantage=args.blue_advantage,
        )
        print(json.dumps(asdict(report), sort_keys=True))
        return 0

    strategy = BettingStrategy(
        min_edge=settings.bet_min_edge if args.min_edge is None else args.min_edge,
        min_expected_value=(
            settings.bet_min_expected_value if args.min_ev is None else args.min_ev
        ),
        kelly_multiplier=(
            settings.bet_kelly_multiplier
            if args.kelly_multiplier is None
            else args.kelly_multiplier
        ),
        max_stake_fraction=(
            settings.bet_max_stake_fraction
            if args.max_stake_fraction is None
            else args.max_stake_fraction
        ),
        decision_minutes_before_start=(
            settings.bet_decision_minutes_before_start
            if args.decision_minutes is None
            else args.decision_minutes
        ),
        market_weight=(
            settings.bet_market_weight if args.market_weight is None else args.market_weight
        ),
    )
    report = evaluate_betting(
        repository.iter_canonical_matches(),
        repository.iter_odds_quotes(
            start_date=test_start,
            end_date=test_end,
            bookmaker=args.bookmaker,
        ),
        train_start=train_start,
        train_end=train_end,
        test_start=test_start,
        test_end=test_end,
        strategy=strategy,
        starting_bankroll=args.starting_bankroll,
        update_during_test=not args.frozen_test,
        k_factor=args.k_factor,
        scale=args.elo_scale,
        team_a_advantage=args.blue_advantage,
    )
    print(json.dumps(asdict(report), sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
