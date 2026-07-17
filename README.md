# lol-stats

A reproducible rewrite of the original exploratory League of Legends statistics and betting
scripts.

The repository used to contain one large `analyzer.py` module that mixed SQLite access,
unsafe pickle deserialization, SQL string concatenation, simulation code, plotting,
hard-coded date ranges and many bankroll strategies. The current structure separates those
responsibilities and keeps `analyzer.py` only as a compatibility facade.

## What changed

- SQLite schema is versioned in `src/lol_stats/schema.sql`.
- Match event collections are stored as JSON, never as pickle blobs.
- SQL uses fixed statements and bound parameters.
- Database path and train/test dates come from configuration or environment variables.
- Ingestion, persistence, analytics, rating evaluation and betting evaluation are independent.
- The kill simulation is explicitly named as a kill-score model, not a match-win model.
- Decimal-odds snapshots are timestamped and linked to normalized matches.
- Tests cover empty samples, missing teams, ties, zero variance, chronological leakage,
  bookmaker margin, decision-time cutoffs and post-start odds.

## Install

```bash
python -m venv .venv
. .venv/bin/activate  # Windows: .venv\Scripts\activate
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

## Import normalized matches

Each JSONL line contains one match. `start_time_utc` is optional for ordinary rating
analysis but required for a leakage-safe betting backtest.

```json
{"source":"example","source_match_id":"42","match_date":"2020-01-10","start_time_utc":"2020-01-10T18:00:00Z","duration_seconds":1800,"server":"EUW","championship":"Example Cup","patch":"10.1","blue":{"team":"Alpha","result":1.0,"kills_by_role":{"top":[300.0],"jungle":[420.0]}},"red":{"team":"Beta","result":0.0,"kills_by_role":{"mid":[900.0]}}}
```

```bash
lol-stats import-jsonl matches.jsonl
```

Extraction from a website or API belongs in an adapter that produces this normalized
payload. The package deliberately does not couple analytics to a particular website DOM.

## Import odds snapshots

Odds are decimal and must use the same BLUE/RED team order as the normalized match.
`captured_at` must identify when the quote was actually available.

```json
{"source":"example","source_match_id":"42","bookmaker":"ExampleBook","captured_at":"2020-01-10T16:30:00Z","team_a":"Alpha","team_b":"Beta","team_a_odds":2.15,"team_b_odds":1.78}
```

```bash
lol-stats import-odds-jsonl odds.jsonl
```

## Temporal Elo evaluation

```bash
lol-stats evaluate \
  --train-end 2019-12-31 \
  --test-start 2020-01-01 \
  --test-end 2020-05-20 \
  --k-factor 24 \
  --elo-scale 400 \
  --blue-advantage 0
```

The evaluator trains only on matches up to `train-end`. Test matches are predicted in
chronological order before their result is applied to the online Elo state. Matches after
`test-end` are ignored, preventing future leakage. Add `--frozen-test` to keep the Elo state
fixed throughout the test window.

## Betting backtest

The win model first produces an independent probability. The bookmaker line is then used as
a price, not as the outcome label:

1. convert both decimal odds to implied probabilities;
2. normalize both sides to remove the bookmaker overround;
3. compute `edge = decision_probability - no_vig_market_probability`;
4. compute unit-stake `EV = decision_probability * decimal_odds - 1`;
5. place a bet only when both edge and EV exceed configured thresholds;
6. size it with fractional Kelly, capped by a maximum bankroll fraction.

The important separation is:

- Elo or a future match model estimates how likely the team is to win;
- the bookmaker coefficient determines the price and break-even probability;
- the strategy places a bet only when the model estimate is sufficiently above the market.

By default the decision probability is the model probability. `market_weight` can blend the
model with the no-vig market probability, but it defaults to zero so the market does not
silently become its own betting signal. Setting it to one reproduces the market and therefore
creates no value edge after margin removal.

```bash
lol-stats backtest-betting \
  --train-end 2019-12-31 \
  --test-start 2020-01-01 \
  --test-end 2020-05-20 \
  --decision-minutes 60 \
  --min-edge 0.03 \
  --min-ev 0.02 \
  --kelly-multiplier 0.25 \
  --max-stake-fraction 0.03
```

For each bookmaker the backtest takes the latest quote available at or before the decision
cutoff. Quotes after the cutoff or after match start are ignored. The report includes
bankroll return, turnover ROI, maximum drawdown, average odds and edge, plus model-versus-
market Brier scores.

## Environment variables

- `LOL_STATS_DB_PATH`
- `LOL_STATS_TRAIN_START`
- `LOL_STATS_TRAIN_END`
- `LOL_STATS_TEST_START`
- `LOL_STATS_TEST_END`
- `LOL_STATS_RANDOM_SEED`
- `LOL_STATS_BET_MIN_EDGE`
- `LOL_STATS_BET_MIN_EV`
- `LOL_STATS_BET_KELLY_MULTIPLIER`
- `LOL_STATS_BET_MAX_STAKE_FRACTION`
- `LOL_STATS_BET_DECISION_MINUTES`
- `LOL_STATS_BET_MARKET_WEIGHT`

## Legacy database note

Old databases may contain pickled Python objects. This rewrite intentionally refuses to
load them. Re-ingest the source data into the JSON schema, or convert a trusted legacy
database in an isolated one-off migration process. Runtime code must not call
`pickle.loads` on database content.
