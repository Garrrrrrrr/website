from uth.cards import parse_card, parse_cards
from uth.solver import flop_decision, reference_opening_decision, river_decision
from uth.state import ActualState


def actual(hidden: str) -> ActualState:
    return ActualState(parse_cards("As Qs"), parse_card("Kh"), parse_card(hidden), parse_cards("Js 8s 3c 2d 7h"))


def test_hidden_card_never_enters_information_state():
    world_a, world_b = actual("2c"), actual("Ac")
    for board_cards in (0, 3, 5):
        assert world_a.information(board_cards, True) == world_b.information(board_cards, True)


def test_hidden_worlds_produce_same_exact_decision():
    info_a, info_b = actual("2c").information(5, True), actual("Ac").information(5, True)
    decision_a, decision_b = river_decision(info_a), river_decision(info_b)
    assert decision_a.action == decision_b.action
    assert decision_a.evs == decision_b.evs


def test_obvious_river_call_and_fold():
    call = ActualState(parse_cards("As Ah"), parse_card("Kh"), parse_card("2c"), parse_cards("Ad 8s 3c 4d 7h")).information(5, True)
    fold = ActualState(parse_cards("2s 3d"), parse_card("Ah"), parse_card("Kc"), parse_cards("4c 7d 9h Js Qs")).information(5, True)
    assert river_decision(call).action == "1X"
    assert river_decision(fold).action == "FOLD"


def test_exposed_flop_is_exact_backward_induction():
    info = ActualState(parse_cards("As Qs"), parse_card("Kh"), parse_card("2c"), parse_cards("Js 8s 3c 2d 7h")).information(3, True)
    result = flop_decision(info)
    assert result.exact and result.method == "EXACT"
    assert result.outcomes == 45_540
    assert set(result.evs) == {"2X", "CHECK"}


def test_uninformed_opening_reference_does_not_invent_an_ev_margin():
    state = ActualState(parse_cards("As Qs"), parse_card("Kh"), parse_card("2c"), parse_cards("Js 8s 3c 2d 7h")).information(0, False)
    result = reference_opening_decision(state)
    assert result.action == "4X"
    assert result.evs == {}
    assert result.method == "PUBLISHED_OPTIMAL_STRATEGY"
