from __future__ import annotations

from dataclasses import dataclass
from random import Random
from time import perf_counter

from .cards import DECK, rank, suit
from .evaluator import evaluate7
from .rules import UTHRules
from .settlement import settle, settle_fold
from .solver import flop_decision, opening_decision, river_decision
from .state import ActualState
from .statistics import RunningStats
from .strategy import basic_flop_action, basic_opening_action, basic_river_action

POLICIES = {"baseline": 99, "river": 5, "flop": 3, "exposed": 0}


@dataclass(slots=True)
class Outcome:
    profit: float
    play: int
    action: str


def deal(rng: Random) -> ActualState:
    cards = rng.sample(DECK, 9)
    return ActualState((cards[0], cards[1]), cards[2], cards[3], tuple(cards[4:9]))


def play(actual: ActualState, policy: str, quality: str = "basic", opening_samples: int = 8,
         rules: UTHRules = UTHRules()) -> Outcome:
    reveal = POLICIES[policy]
    opening = actual.information(0, reveal <= 0)
    if quality == "exact-late" and reveal <= 0:
        first = opening_decision(opening, samples=opening_samples, precision=0.01, rules=rules).action
        if first.startswith("INCONCLUSIVE"):
            first = basic_opening_action(actual.player)
    else:
        first = basic_opening_action(actual.player)
    if first == "4X":
        wager, action = 4, "4X"
    else:
        flop = actual.information(3, reveal <= 3)
        second = flop_decision(flop, rules).action if quality == "exact-late" else basic_flop_action(flop)
        if second == "2X":
            wager, action = 2, "2X"
        else:
            river = actual.information(5, reveal <= 5)
            third = river_decision(river, rules).action if quality == "exact-late" else basic_river_action(river)
            if third == "FOLD":
                return Outcome(settle_fold(rules).total, 0, "FOLD")
            wager, action = 1, "1X"
    player = evaluate7((*actual.player, *actual.board))
    dealer = evaluate7((actual.dealer_visible, actual.dealer_hidden, *actual.board))
    return Outcome(settle(player, dealer, wager, rules).total, wager, action)


def _summary(stats: RunningStats, play_total: float, actions: dict[str, int], runtime: float) -> dict[str, object]:
    average_play = play_total / stats.count
    average_action = 2 + average_play
    variance = stats.variance
    ev = stats.mean
    return {"ev_per_round": ev, "house_edge_vs_ante": -ev, "player_edge_vs_ante": ev,
            "player_edge_vs_initial": ev / 2, "average_play_wager": average_play,
            "average_total_action": average_action, "edge_vs_average_action": ev / average_action,
            "sd_per_round": variance ** 0.5, "variance": variance,
            "n0": variance / (ev * ev) if ev > 0 else None,
            "actions": {key: value / stats.count for key, value in actions.items()},
            "statistics": stats.to_dict(), "runtime_seconds": runtime,
            "hands_per_second": stats.count / runtime if runtime else 0}


def simulate(mode: str, hands: int, seed: int = 20260813, quality: str = "basic",
             opening_samples: int = 8) -> dict[str, object]:
    if mode not in (*POLICIES, "paired", "stages"):
        raise ValueError("unknown mode")
    rng = Random(seed)
    policies = list(POLICIES) if mode == "stages" else (["baseline", "exposed"] if mode == "paired" else [mode])
    stats = {name: RunningStats() for name in policies}
    paired = RunningStats()
    action_counts = {name: {key: 0 for key in ("4X", "2X", "1X", "FOLD")} for name in policies}
    play_totals = {name: 0.0 for name in policies}
    started = perf_counter()
    for _ in range(hands):
        actual = deal(rng)
        outcomes = {}
        for name in policies:
            result = play(actual, name, quality, opening_samples)
            outcomes[name] = result
            stats[name].add(result.profit)
            action_counts[name][result.action] += 1
            play_totals[name] += result.play
        if "baseline" in outcomes and "exposed" in outcomes:
            paired.add(outcomes["exposed"].profit - outcomes["baseline"].profit)
    runtime = perf_counter() - started
    result: dict[str, object] = {name: _summary(stats[name], play_totals[name], action_counts[name], runtime) for name in policies}
    if paired.count:
        result["information_value"] = paired.to_dict()
    if mode == "stages":
        means = {name: stats[name].mean for name in policies}
        result["stage_value"] = {"river_only": means["river"] - means["baseline"],
            "additional_flop": means["flop"] - means["river"],
            "additional_preflop": means["exposed"] - means["flop"],
            "full": means["exposed"] - means["baseline"]}
    result["quality"] = quality
    return result


def dealer_categories(actual: ActualState) -> dict[str, object]:
    visible = actual.dealer_visible
    player_ranks = {rank(card) for card in actual.player}
    return {"rank": rank(visible), "shares_player_rank": rank(visible) in player_ranks,
            "shares_player_suit": any(suit(visible) == suit(card) for card in actual.player),
            "overcard": rank(visible) > max(player_ranks), "undercard": rank(visible) < min(player_ranks)}
