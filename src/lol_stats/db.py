from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from importlib.resources import files
from pathlib import Path

from .models import CanonicalMatch, MatchInput, TeamMatchRecord


class LegacyDataError(ValueError):
    """Raised when a legacy non-JSON event payload is encountered."""


class MatchRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        schema = files("lol_stats").joinpath("schema.sql").read_text(encoding="utf-8")
        with self.connect() as connection:
            connection.executescript(schema)

    def save_match(self, match: MatchInput) -> int:
        match.validate()
        self.initialize()
        with self.connect() as connection:
            connection.execute(
                """
                INSERT INTO matches(
                    source, source_match_id, match_date, duration_seconds,
                    server, championship, patch
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(source, source_match_id) DO UPDATE SET
                    match_date = excluded.match_date,
                    duration_seconds = excluded.duration_seconds,
                    server = excluded.server,
                    championship = excluded.championship,
                    patch = excluded.patch
                """,
                (
                    match.source,
                    match.source_match_id,
                    match.match_date.isoformat(),
                    match.duration_seconds,
                    match.server,
                    match.championship,
                    match.patch,
                ),
            )
            row = connection.execute(
                "SELECT id FROM matches WHERE source = ? AND source_match_id = ?",
                (match.source, match.source_match_id),
            ).fetchone()
            assert row is not None
            match_id = int(row["id"])
            connection.execute("DELETE FROM team_match_stats WHERE match_id = ?", (match_id,))
            self._insert_team(
                connection,
                match_id,
                team=match.blue.team,
                opponent=match.red.team,
                side="BLUE",
                result=match.blue.result,
                kills_by_role=match.blue.kills_by_role,
            )
            self._insert_team(
                connection,
                match_id,
                team=match.red.team,
                opponent=match.blue.team,
                side="RED",
                result=match.red.result,
                kills_by_role=match.red.kills_by_role,
            )
            return match_id

    @staticmethod
    def _insert_team(
        connection: sqlite3.Connection,
        match_id: int,
        *,
        team: str,
        opponent: str,
        side: str,
        result: float,
        kills_by_role: object,
    ) -> None:
        normalized = {
            str(role): [float(value) for value in timestamps]
            for role, timestamps in dict(kills_by_role).items()
        }
        connection.execute(
            """
            INSERT INTO team_match_stats(
                match_id, team, opponent, side, result, kills_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (match_id, team, opponent, side, result, json.dumps(normalized, sort_keys=True)),
        )

    def team_names(self) -> list[str]:
        self.initialize()
        with self.connect() as connection:
            rows = connection.execute(
                "SELECT DISTINCT team FROM team_match_stats ORDER BY team"
            ).fetchall()
        return [str(row["team"]) for row in rows]

    def iter_team_matches(
        self,
        *,
        team: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        server: str | None = None,
    ) -> list[TeamMatchRecord]:
        self.initialize()
        clauses: list[str] = []
        params: list[object] = []
        if team is not None:
            clauses.append("stats.team = ?")
            params.append(team)
        if start_date is not None:
            clauses.append("matches.match_date >= ?")
            params.append(start_date.isoformat())
        if end_date is not None:
            clauses.append("matches.match_date <= ?")
            params.append(end_date.isoformat())
        if server is not None:
            clauses.append("matches.server = ?")
            params.append(server)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"""
            SELECT
                matches.source_match_id,
                matches.match_date,
                matches.duration_seconds,
                matches.server,
                matches.championship,
                matches.patch,
                stats.team,
                stats.opponent,
                stats.side,
                stats.result,
                stats.kills_json
            FROM team_match_stats AS stats
            JOIN matches ON matches.id = stats.match_id
            {where}
            ORDER BY matches.match_date, matches.source_match_id, stats.side
        """
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._team_record(row) for row in rows]

    @staticmethod
    def _team_record(row: sqlite3.Row) -> TeamMatchRecord:
        raw = row["kills_json"]
        try:
            parsed = json.loads(raw)
        except (TypeError, json.JSONDecodeError) as exc:
            raise LegacyDataError(
                "kills_json is not valid JSON; legacy pickle blobs are not supported"
            ) from exc
        if not isinstance(parsed, dict):
            raise LegacyDataError("kills_json must contain an object keyed by role")
        kills = {
            str(role): tuple(float(value) for value in values)
            for role, values in parsed.items()
        }
        return TeamMatchRecord(
            source_match_id=str(row["source_match_id"]),
            match_date=date.fromisoformat(str(row["match_date"])),
            duration_seconds=int(row["duration_seconds"]),
            server=str(row["server"]),
            championship=str(row["championship"]),
            patch=None if row["patch"] is None else str(row["patch"]),
            team=str(row["team"]),
            opponent=str(row["opponent"]),
            side=str(row["side"]),
            result=float(row["result"]),
            kills_by_role=kills,
        )

    def iter_canonical_matches(
        self,
        *,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[CanonicalMatch]:
        self.initialize()
        clauses: list[str] = []
        params: list[object] = []
        if start_date is not None:
            clauses.append("matches.match_date >= ?")
            params.append(start_date.isoformat())
        if end_date is not None:
            clauses.append("matches.match_date <= ?")
            params.append(end_date.isoformat())
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"""
            SELECT
                matches.source_match_id,
                matches.match_date,
                blue.team AS team_a,
                red.team AS team_b,
                blue.result AS result_a
            FROM matches
            JOIN team_match_stats AS blue
              ON blue.match_id = matches.id AND blue.side = 'BLUE'
            JOIN team_match_stats AS red
              ON red.match_id = matches.id AND red.side = 'RED'
            {where}
            ORDER BY matches.match_date, matches.source_match_id
        """
        with self.connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [
            CanonicalMatch(
                source_match_id=str(row["source_match_id"]),
                match_date=date.fromisoformat(str(row["match_date"])),
                team_a=str(row["team_a"]),
                team_b=str(row["team_b"]),
                result_a=float(row["result_a"]),
            )
            for row in rows
        ]
