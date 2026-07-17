from __future__ import annotations

import argparse
import json
from dataclasses import asdict, replace
from datetime import date
from pathlib import Path

from .config import Settings
from .db import MatchRepository
from .evaluation import evaluate_temporally
from .ingest import JsonLinesSource, ingest_source


def _date(value: str) -> date:
    return date.fromisoformat(value)


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(prog="lol-stats")
    subcommands = command.add_subparsers(dest="command", required=True)

    init_db = subcommands.add_parser("init-db", help="create or upgrade the SQLite schema")
    init_db.add_argument("--db-path")

    import_jsonl = subcommands.add_parser("import-jsonl", help="import normalized match JSONL")
    import_jsonl.add_argument("path")
    import_jsonl.add_argument("--db-path")

    evaluate = subcommands.add_parser("evaluate", help="run a chronological Elo backtest")
    evaluate.add_argument("--db-path")
    evaluate.add_argument("--train-start", type=_date)
    evaluate.add_argument("--train-end", type=_date)
    evaluate.add_argument("--test-start", type=_date)
    evaluate.add_argument("--test-end", type=_date)
    evaluate.add_argument("--frozen-test", action="store_true")
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

    report = evaluate_temporally(
        repository.iter_canonical_matches(),
        train_start=args.train_start or settings.train_start,
        train_end=args.train_end or settings.train_end,
        test_start=args.test_start or settings.test_start,
        test_end=args.test_end or settings.test_end,
        update_during_test=not args.frozen_test,
    )
    print(json.dumps(asdict(report), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
