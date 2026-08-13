from collections import Counter
from itertools import combinations
import json
from math import comb, isinf
from pathlib import Path
from random import Random

import pytest

from uth.cards import DECK, parse_card, parse_cards
from uth.evaluator import HandCategory, evaluate, evaluate7
from uth.simulation import simulate_parallel
from uth.solver import opening_decision
from uth.state import InformationState
from uth.statistics import RunningStats, StratifiedStats


@pytest.mark.slow
def test_exhaustive_five_card_category_frequencies():
    expected = {
        HandCategory.HIGH_CARD: 1_302_540,
        HandCategory.PAIR: 1_098_240,
        HandCategory.TWO_PAIR: 123_552,
        HandCategory.THREE_OF_A_KIND: 54_912,
        HandCategory.STRAIGHT: 10_200,
        HandCategory.FLUSH: 5_108,
        HandCategory.FULL_HOUSE: 3_744,
        HandCategory.FOUR_OF_A_KIND: 624,
        HandCategory.STRAIGHT_FLUSH: 40,
    }
    observed = Counter(evaluate(hand).category for hand in combinations(DECK, 5))
    assert sum(observed.values()) == comb(52, 5) == 2_598_960
    assert observed == expected


def test_seven_card_evaluator_matches_best_of_twenty_one_five_card_hands():
    rng = Random(20260813)
    for _ in range(1_000):
        cards = tuple(rng.sample(DECK, 7))
        independent = max(evaluate(hand) for hand in combinations(cards, 5))
        assert evaluate7(cards) == independent


def test_python_reference_matches_shared_typescript_golden_corpus():
    fixture = Path(__file__).resolve().parents[2] / "blackjack" / "lib" / "uth" / "evaluator-golden.json"
    for case in json.loads(fixture.read_text(encoding="utf-8")):
        hand = evaluate7(tuple(parse_card(card) for card in case["cards"]))
        assert [int(hand.category), *hand.kickers] == case["rank"]


def test_stratified_finite_population_uncertainty_reaches_zero_at_census():
    census = RunningStats()
    for value in (1.0, 2.0, 3.0):
        census.add(value)
    sampled = RunningStats()
    sampled.add(0.0)
    sampled.add(2.0)
    exact = StratifiedStats([(3, census)])
    incomplete = StratifiedStats([(3, sampled)])
    assert exact.standard_error == 0
    assert incomplete.standard_error > 0
    assert isinf(StratifiedStats([(3, RunningStats(1, 1.0, 0.0))]).standard_error)


def test_opening_samples_information_states_and_solves_children_exactly():
    state = InformationState(parse_cards("As Qs"), (), parse_card("Kh"))
    result = opening_decision(state, samples=6)
    assert result.method == "PAIRED_STRATIFIED_MONTE_CARLO+EXACT_CHILDREN"
    assert result.outcomes == 6 * 45_540
    assert result.difference_statistics["count"] == 6
    assert result.difference_statistics["population"] == comb(49, 3)


def test_parallel_simulation_is_reproducible_and_preserves_all_hands():
    first = simulate_parallel("paired", 2_000, seed=91, workers=2)
    second = simulate_parallel("paired", 2_000, seed=91, workers=2)
    for key in ("ev_per_round", "variance", "average_play_wager", "actions"):
        assert first["baseline"][key] == second["baseline"][key]
        assert first["exposed"][key] == second["exposed"][key]
    assert first["information_value"]["mean"] == second["information_value"]["mean"]
    assert first["parallelism"] == second["parallelism"]
    assert first["baseline"]["statistics"]["count"] == 2_000
    assert first["exposed"]["statistics"]["count"] == 2_000
    assert first["information_value"]["count"] == 2_000
    assert sum(first["baseline"]["actions"].values()) == pytest.approx(1.0)
