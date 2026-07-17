from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import mean

from .evaluation import EloModel
from .models import CanonicalMatch, OddsQuoteRecord


@dataclass(frozen=True, slots=True)
class MarketProbabilities:
    team_a: float
    team_b: float
    overround: float


@dataclass(frozen=True, slots=True)
class BettingStrategy:
    min_edge: float = 0.03
    min_expected_value: float = 0.02
    kelly_multiplier: float = 0.25
    max_stake_fraction: float = 0.03
    decision_minutes_before_start: int = 60
    market_weight: float = 0.0
    min_odds: float = 1.01
    max_odds: float = 20.0

    def validate(self) -> None:
        if self.min_edge < 0 or self.min_expected_value < 0:
            raise ValueError("edge and expected-value thresholds must not be negative")
        if not 0.0 <= self.kelly_multiplier <= 1.0:
            raise ValueError("kelly_multiplier must be between 0 and 1")
        if not 0.0 < self.max_stake_fraction <= 1.0:
            raise ValueError("max_stake_fraction must be in (0, 1]")
        if self.decision_minutes_before_start < 0:
            raise ValueError("decision_minutes_before_start must not be negative")
        if not 0.0 <= self.market_weight <= 1.0:
            raise ValueError("market_weight must be between 0 and 1")
        if self.min_odds <= 1.0 or self.max_odds <= self.min_odds:
            raise ValueError("invalid odds limits")


@dataclass(frozen=True, slots=True)
class BetRecord:
    source_match_id: str
    match_date: date
    team: str
    opponent: str
    side: str
    bookmaker: str
    odds: float
    model_probability: float
    market_probability: float
    decision_probability: float
    edge: float
    expected_value: float
    stake: float
    profit: float
    bankroll_after: float


@dataclass(frozen=True, slots=True)
class BettingReport:
    train_matches: int
    test_matches: int
    priced_matches: int
    bets: int
    wins: int
    starting_bankroll: float
    final_bankroll: float
    profit: float
    turnover: float
    roi_on_turnover: float | None
    return_on_bankroll: float
    max_drawdown: float
    average_odds: float | None
    average_edge: float | None
    model_brier: float | None
    market_brier: float | None
    bet_records: tuple[BetRecord, ...]


def implied_probability(decimal_odds: float) -> float:
    if decimal_odds <= 1.0:
        raise ValueError("decimal odds must be greater than 1.0")
    return 1.0 / decimal_odds


def remove_overround(team_a_odds: float, team_b_odds: float) -> MarketProbabilities:
    raw_a = implied_probability(team_a_odds)
    raw_b = implied_probability(team_b_odds)
    total = raw_a + raw_b
    return MarketProbabilities(
        team_a=raw_a / total,
        team_b=raw_b / total,
        overround=total - 1.0,
    )


def expected_value(probability: float, decimal_odds: float) -> float:
    if not 0.0 <= probability <= 1.0:
        raise ValueError("probability must be between 0 and 1")
    return probability * decimal_odds - 1.0


def kelly_fraction(probability: float, decimal_odds: float) -> float:
    edge = expected_value(probability, decimal_odds)
    return max(0.0, edge / (decimal_odds - 1.0))


@dataclass(frozen=True, slots=True)
class _Candidate:
    side: str
    team: str
    opponent: str
    bookmaker: str
    odds: float
    model_probability: float
    market_probability: float
    decision_probability: float
    edge: float
    expected_value: float
    stake_fraction: float


def _latest_quotes_at_cutoff(
    quotes: list[OddsQuoteRecord],
    *,
    cutoff,
) -> list[OddsQuoteRecord]:
    latest: dict[str, OddsQuoteRecord] = {}
    for quote in quotes:
        if quote.captured_at > cutoff:
            continue
        previous = latest.get(quote.bookmaker)
        if previous is None or quote.captured_at > previous.captured_at:
            latest[quote.bookmaker] = quote
    return list(latest.values())


def _best_candidate(
    quotes: list[OddsQuoteRecord],
    *,
    model_probability_a: float,
    strategy: BettingStrategy,
) -> _Candidate | None:
    candidates: list[_Candidate] = []
    for quote in quotes:
        market = remove_overround(quote.team_a_odds, quote.team_b_odds)
        decision_a = (
            (1.0 - strategy.market_weight) * model_probability_a
            + strategy.market_weight * market.team_a
        )
        decision_b = 1.0 - decision_a
        for side, team, opponent, odds, model_p, market_p, decision_p in (
            (
                "A",
                quote.team_a,
                quote.team_b,
                quote.team_a_odds,
                model_probability_a,
                market.team_a,
                decision_a,
            ),
            (
                "B",
                quote.team_b,
                quote.team_a,
                quote.team_b_odds,
                1.0 - model_probability_a,
                market.team_b,
                decision_b,
            ),
        ):
            if not strategy.min_odds <= odds <= strategy.max_odds:
                continue
            edge = decision_p - market_p
            ev = expected_value(decision_p, odds)
            full_kelly = kelly_fraction(decision_p, odds)
            stake_fraction = min(
                strategy.max_stake_fraction,
                strategy.kelly_multiplier * full_kelly,
            )
            if (
                edge >= strategy.min_edge
                and ev >= strategy.min_expected_value
                and stake_fraction > 0.0
            ):
                candidates.append(
                    _Candidate(
                        side=side,
                        team=team,
                        opponent=opponent,
                        bookmaker=quote.bookmaker,
                        odds=odds,
                        model_probability=model_p,
                        market_probability=market_p,
                        decision_probability=decision_p,
                        edge=edge,
                        expected_value=ev,
                        stake_fraction=stake_fraction,
                    )
                )
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item.expected_value, item.edge, item.odds))


def evaluate_betting(
    matches: Iterable[CanonicalMatch],
    quotes: Iterable[OddsQuoteRecord],
    *,
    train_start: date | None = None,
    train_end: date,
    test_start: date,
    test_end: date,
    strategy: BettingStrategy | None = None,
    starting_bankroll: float = 100.0,
    update_during_test: bool = True,
    initial_rating: float = 1500.0,
    k_factor: float = 24.0,
    scale: float = 400.0,
    team_a_advantage: float = 0.0,
) -> BettingReport:
    strategy = strategy or BettingStrategy()
    strategy.validate()
    if starting_bankroll <= 0:
        raise ValueError("starting_bankroll must be positive")
    if train_end >= test_start:
        raise ValueError("train_end must be before test_start")
    if test_start > test_end:
        raise ValueError("test_start must not be after test_end")
    if train_start is not None and train_start > train_end:
        raise ValueError("train_start must not be after train_end")

    ordered = sorted(matches, key=lambda item: (item.match_date, item.source_match_id))
    training = [
        match
        for match in ordered
        if match.match_date <= train_end
        and (train_start is None or match.match_date >= train_start)
    ]
    testing = [match for match in ordered if test_start <= match.match_date <= test_end]

    model = EloModel(
        initial_rating=initial_rating,
        k_factor=k_factor,
        scale=scale,
        team_a_advantage=team_a_advantage,
    )
    for match in training:
        model.update(match.team_a, match.team_b, match.result_a)

    quotes_by_match: dict[tuple[str, str], list[OddsQuoteRecord]] = {}
    for quote in quotes:
        quotes_by_match.setdefault((quote.source, quote.source_match_id), []).append(quote)

    bankroll = starting_bankroll
    peak_bankroll = starting_bankroll
    max_drawdown = 0.0
    turnover = 0.0
    wins = 0
    priced_matches = 0
    bet_records: list[BetRecord] = []
    model_errors: list[float] = []
    market_errors: list[float] = []

    for match in testing:
        model_probability_a = model.predict(match.team_a, match.team_b)
        match_quotes = quotes_by_match.get((match.source, match.source_match_id), [])
        available: list[OddsQuoteRecord] = []
        if match.start_time_utc is not None:
            cutoff = match.start_time_utc - timedelta(
                minutes=strategy.decision_minutes_before_start
            )
            available = _latest_quotes_at_cutoff(match_quotes, cutoff=cutoff)

        if available:
            priced_matches += 1
            reference = min(
                available,
                key=lambda quote: remove_overround(
                    quote.team_a_odds, quote.team_b_odds
                ).overround,
            )
            reference_market = remove_overround(
                reference.team_a_odds, reference.team_b_odds
            )
            model_errors.append((model_probability_a - match.result_a) ** 2)
            market_errors.append((reference_market.team_a - match.result_a) ** 2)

            if match.result_a != 0.5:
                candidate = _best_candidate(
                    available,
                    model_probability_a=model_probability_a,
                    strategy=strategy,
                )
                if candidate is not None:
                    stake = bankroll * candidate.stake_fraction
                    won = (candidate.side == "A" and match.result_a == 1.0) or (
                        candidate.side == "B" and match.result_a == 0.0
                    )
                    profit = stake * (candidate.odds - 1.0) if won else -stake
                    bankroll += profit
                    turnover += stake
                    wins += int(won)
                    peak_bankroll = max(peak_bankroll, bankroll)
                    drawdown = (peak_bankroll - bankroll) / peak_bankroll
                    max_drawdown = max(max_drawdown, drawdown)
                    bet_records.append(
                        BetRecord(
                            source_match_id=match.source_match_id,
                            match_date=match.match_date,
                            team=candidate.team,
                            opponent=candidate.opponent,
                            side=candidate.side,
                            bookmaker=candidate.bookmaker,
                            odds=candidate.odds,
                            model_probability=candidate.model_probability,
                            market_probability=candidate.market_probability,
                            decision_probability=candidate.decision_probability,
                            edge=candidate.edge,
                            expected_value=candidate.expected_value,
                            stake=stake,
                            profit=profit,
                            bankroll_after=bankroll,
                        )
                    )

        if update_during_test:
            model.update(match.team_a, match.team_b, match.result_a)

    profit = bankroll - starting_bankroll
    return BettingReport(
        train_matches=len(training),
        test_matches=len(testing),
        priced_matches=priced_matches,
        bets=len(bet_records),
        wins=wins,
        starting_bankroll=starting_bankroll,
        final_bankroll=bankroll,
        profit=profit,
        turnover=turnover,
        roi_on_turnover=None if turnover == 0 else profit / turnover,
        return_on_bankroll=profit / starting_bankroll,
        max_drawdown=max_drawdown,
        average_odds=None if not bet_records else mean(item.odds for item in bet_records),
        average_edge=None if not bet_records else mean(item.edge for item in bet_records),
        model_brier=None if not model_errors else mean(model_errors),
        market_brier=None if not market_errors else mean(market_errors),
        bet_records=tuple(bet_records),
    )
