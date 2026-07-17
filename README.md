# lol-stats

A reproducible rewrite of the original exploratory League of Legends statistics script.

The repository used to contain one large `analyzer.py` module that mixed SQLite access,
unsafe pickle deserialization, SQL string concatenation, simulation code, plotting and
hard-coded date ranges. The current structure separates those responsibilities and keeps
`analyzer.py` only as a compatibility facade.

## What changed

- SQLite schema is versioned in `src/lol_stats/schema.sql`.
- Match event collections are stored as JSON, never as pickle blobs.
- SQL uses fixed statements and bound parameters.
- Database path and train/test dates come from configuration or environment variables.
- Ingestion, persistence, analytics and temporal evaluation are independent modules.
- Tests cover empty samples, missing teams, ties, zero variance and chronological leakage.

## Install

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install -e ".[dev]"
pytest
```

## Initialize a database

```bash
lol-stats init-db
```

The default path is `data/lol_stats.sqlite`. Override it with:

```bash
LOL_STATS_DB_PATH=/path/to/lol.sqlite lol-stats init-db
```

## Import normalized JSONL

Each line must contain one match:

```json
{"source":"example","source_match_id":"42","match_date":"2020-01-10","duration_seconds":1800,"server":"EUW","championship":"Example Cup","patch":"10.1","blue":{"team":"Alpha","result":1.0,"kills_by_role":{"top":[300.0],"jungle":[420.0]}},"red":{"team":"Beta","result":0.0,"kills_by_role":{"mid":[900.0]}}}
```

```bash
lol-stats import-jsonl matches.jsonl
```

Extraction from a website or API belongs in an adapter that produces this normalized
payload. The package deliberately does not couple analytics to a particular website DOM.

## Temporal evaluation

```bash
lol-stats evaluate \
  --train-end 2019-12-31 \
  --test-start 2020-01-01 \
  --test-end 2020-05-20
```

The evaluator trains only on matches up to `train-end`. Test matches are predicted in
chronological order before their result is applied to the online Elo state. Matches after
`test-end` are ignored, preventing future leakage.

## Environment variables

- `LOL_STATS_DB_PATH`
- `LOL_STATS_TRAIN_START`
- `LOL_STATS_TRAIN_END`
- `LOL_STATS_TEST_START`
- `LOL_STATS_TEST_END`
- `LOL_STATS_RANDOM_SEED`

## Legacy database note

Old databases may contain pickled Python objects. This rewrite intentionally refuses to
load them. Re-ingest the source data into the JSON schema, or convert a trusted legacy
database in an isolated one-off migration process. Runtime code must not call
`pickle.loads` on database content.
