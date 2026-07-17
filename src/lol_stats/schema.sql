PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS schema_meta (
    version INTEGER NOT NULL PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT OR IGNORE INTO schema_meta(version) VALUES (1);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    source_match_id TEXT NOT NULL,
    match_date TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL CHECK (duration_seconds > 0),
    server TEXT NOT NULL,
    championship TEXT NOT NULL,
    patch TEXT,
    UNIQUE(source, source_match_id)
);

CREATE TABLE IF NOT EXISTS team_match_stats (
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    team TEXT NOT NULL,
    opponent TEXT NOT NULL,
    side TEXT NOT NULL CHECK (side IN ('BLUE', 'RED')),
    result REAL NOT NULL CHECK (result IN (0.0, 0.5, 1.0)),
    kills_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY(match_id, team),
    CHECK(team <> opponent)
);

CREATE INDEX IF NOT EXISTS idx_matches_date ON matches(match_date);
CREATE INDEX IF NOT EXISTS idx_matches_server_date ON matches(server, match_date);
CREATE INDEX IF NOT EXISTS idx_team_match_stats_team ON team_match_stats(team, match_id);
