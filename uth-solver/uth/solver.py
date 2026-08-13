from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from random import Random
from time import perf_counter

from .cards import DECK, rank, suit
from .evaluator import evaluate7
from .rules import UTHRules
from .settlement import settle, settle_fold
from .state import InformationState
from .statistics import RunningStats, StratifiedStats, recommendation_status
from .strategy import basic_opening_action


@dataclass(frozen=True, slots=True)
class Decision:
    action: str
    evs: dict[str, float]
    difference: float
    method: str
    exact: bool
    outcomes: int
    runtime_seconds: float
    status: str = "CONFIRMED"
    difference_statistics: dict[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {"action": self.action, "evs": self.evs, "difference": self.difference,
                "method": self.method, "exact": self.exact, "outcomes": self.outcomes,
                "runtime_seconds": self.runtime_seconds, "status": self.status,
                "difference_statistics": self.difference_statistics}


def _remaining(state: InformationState) -> tuple[int, ...]:
    known = set(state.known_cards)
    return tuple(card for card in DECK if card not in known)


def _dealer_holes(state: InformationState, cards: tuple[int, ...]):
    if state.dealer_visible is None:
        for hidden in combinations(cards, 2):
            yield hidden
    else:
        for hidden in cards:
            yield (state.dealer_visible, hidden)


def river_decision(state: InformationState, rules: UTHRules = UTHRules()) -> Decision:
    if len(state.board) != 5:
        raise ValueError("river decision requires a five-card board")
    started = perf_counter()
    remaining = _remaining(state)
    player_rank = evaluate7((*state.player, *state.board))
    total = 0.0
    count = 0
    for dealer in _dealer_holes(state, remaining):
        total += settle(player_rank, evaluate7((*dealer, *state.board)), 1, rules).total
        count += 1
    call = total / count
    fold = settle_fold(rules).total
    action = "1X" if call >= fold else "FOLD"
    return Decision(action, {"1X": call, "FOLD": fold}, abs(call - fold), "EXACT", True,
                    count, perf_counter() - started)


def flop_decision(state: InformationState, rules: UTHRules = UTHRules(), include_opening: bool = False) -> Decision:
    """Exact board-grouped backward induction; the river action never sees hidden holes."""
    if len(state.board) != 3:
        raise ValueError("flop decision requires a three-card board")
    started = perf_counter()
    remaining = _remaining(state)
    bet2_total = check_total = bet4_total = 0.0
    board_count = outcomes = 0
    for future in combinations(remaining, 2):
        board = (*state.board, *future)
        future_set = set(future)
        dealer_pool = tuple(card for card in remaining if card not in future_set)
        player_rank = evaluate7((*state.player, *board))
        sum1 = sum2 = sum4 = 0.0
        dealer_count = 0
        for dealer in _dealer_holes(state, dealer_pool):
            dealer_rank = evaluate7((*dealer, *board))
            sum1 += settle(player_rank, dealer_rank, 1, rules).total
            sum2 += settle(player_rank, dealer_rank, 2, rules).total
            if include_opening:
                sum4 += settle(player_rank, dealer_rank, 4, rules).total
            dealer_count += 1
        bet2_total += sum2 / dealer_count
        check_total += max(sum1 / dealer_count, settle_fold(rules).total)
        if include_opening:
            bet4_total += sum4 / dealer_count
        board_count += 1
        outcomes += dealer_count
    evs = {"2X": bet2_total / board_count, "CHECK": check_total / board_count}
    if include_opening:
        evs["4X"] = bet4_total / board_count
    action = "2X" if evs["2X"] >= evs["CHECK"] else "CHECK"
    return Decision(action, evs, abs(evs["2X"] - evs["CHECK"]), "EXACT", True,
                    outcomes, perf_counter() - started)


def opening_decision(state: InformationState, samples: int = 200, seed: int = 20260813,
                     confidence: float = 0.999, precision: float = 0.001,
                     rules: UTHRules = UTHRules()) -> Decision:
    """Stratified sampled flops with exact conditional backward induction.

    The only sampling error is over flop information states. Every turn, river,
    dealer holding, and legal continuation below a selected flop is enumerated.
    """
    if state.board:
        raise ValueError("opening decision requires no board")
    started = perf_counter()
    groups: dict[tuple[tuple[int, ...], tuple[int, ...]], list[tuple[int, int, int]]] = {}
    for flop in combinations(_remaining(state), 3):
        rank_counts = sorted(({rank(card): sum(rank(other) == rank(card) for other in flop)
                               for card in flop}).values(), reverse=True)
        suit_counts = sorted(({suit(card): sum(suit(other) == suit(card) for other in flop)
                               for card in flop}).values(), reverse=True)
        groups.setdefault((tuple(rank_counts), tuple(suit_counts)), []).append(flop)
    population = sum(map(len, groups.values()))
    sample_count = max(len(groups), min(samples, population))
    minimum = 2 if sample_count >= len(groups) * 2 else 1
    allocations = [min(minimum, len(flops)) for flops in groups.values()]
    remaining_samples = sample_count - sum(allocations)
    while remaining_samples:
        candidates = [index for index, flops in enumerate(groups.values()) if allocations[index] < len(flops)]
        selected = max(candidates, key=lambda index: (len(tuple(groups.values())[index]) - allocations[index]) / (allocations[index] + 1))
        allocations[selected] += 1
        remaining_samples -= 1
    state_seed = seed
    for card in state.known_cards:
        state_seed = ((state_seed ^ card) * 16_777_619) & ((1 << 64) - 1)
    rng = Random(state_seed)
    strata: list[tuple[int, RunningStats]] = []
    bet_strata: list[tuple[int, RunningStats]] = []
    check_strata: list[tuple[int, RunningStats]] = []
    outcomes = 0
    for flops, allocated in zip(groups.values(), allocations, strict=True):
        rng.shuffle(flops)
        delta_stats, bet_stats, check_stats = RunningStats(), RunningStats(), RunningStats()
        for flop in flops[:allocated]:
            child = flop_decision(InformationState(state.player, flop, state.dealer_visible), rules, include_opening=True)
            ev4 = child.evs["4X"]
            ev_check = max(child.evs["2X"], child.evs["CHECK"])
            bet_stats.add(ev4)
            check_stats.add(ev_check)
            delta_stats.add(ev4 - ev_check)
            outcomes += child.outcomes
        strata.append((len(flops), delta_stats))
        bet_strata.append((len(flops), bet_stats))
        check_strata.append((len(flops), check_stats))
    delta = StratifiedStats(strata)
    bet = StratifiedStats(bet_strata).mean
    check = StratifiedStats(check_strata).mean
    exact = sample_count == population
    status = "CONFIRMED" if exact else recommendation_status(delta, precision, confidence)
    action = ("4X" if delta.mean >= 0 else "CHECK") if status == "CONFIRMED" else status
    method = "EXACT" if exact else "PAIRED_STRATIFIED_MONTE_CARLO+EXACT_CHILDREN"
    return Decision(action, {"4X": bet, "CHECK": check}, abs(delta.mean), method,
                    exact, outcomes, perf_counter() - started, status, delta.to_dict(confidence))


def reference_opening_decision(state: InformationState) -> Decision:
    """Published optimal 4X/check action; deliberately makes no numeric EV claim."""
    if state.board or state.dealer_visible is not None:
        raise ValueError("reference opening requires an uninformed opening state")
    return Decision(basic_opening_action(state.player), {}, 0.0, "PUBLISHED_OPTIMAL_STRATEGY",
                    False, 0, 0.0)


def solve(state: InformationState, **kwargs) -> Decision:
    if len(state.board) == 5:
        return river_decision(state, kwargs.get("rules", UTHRules()))
    if len(state.board) == 3:
        return flop_decision(state, kwargs.get("rules", UTHRules()))
    return opening_decision(state, **kwargs)
