from uth.cards import parse_cards
from uth.evaluator import evaluate7
from uth.rules import UTHRules, dealer_qualifies
from uth.settlement import settle, settle_fold


def ranks(player: str, dealer: str, board: str):
    board_cards = parse_cards(board)
    return evaluate7((*parse_cards(player), *board_cards)), evaluate7((*parse_cards(dealer), *board_cards))


def test_player_win_qualified_and_unqualified():
    p, d = ranks("As Ah", "Ks Qd", "Kc 3d 7h 8s 9c")
    assert settle(p, d, 4).total == 5  # ante + play; Blind pair win pushes
    p, d = ranks("As Kd", "Qs Jd", "2c 3d 7h 8s 9c")
    assert not dealer_qualifies(d)
    assert settle(p, d, 2).total == 2  # Ante and Blind push, Play wins


def test_dealer_win_nonqualification_still_loses_play_and_blind():
    p, d = ranks("Ts 6d", "Js 7d", "2c 3d 4h 8s 9c")
    assert not dealer_qualifies(d)
    payoff = settle(p, d, 1)
    assert (payoff.ante, payoff.blind, payoff.play, payoff.total) == (0, -1, -1, -2)


def test_tie_and_fold():
    p, d = ranks("2s 3s", "4s 5s", "As Ks Qs Js Ts")
    assert settle(p, d, 4).total == 0
    assert settle_fold().total == -2


def test_blind_paytable_is_configurable():
    p, d = ranks("As Ks", "2d 2h", "Qs Js Ts 3c 4d")
    assert settle(p, d, 1).blind == 500
    custom = UTHRules(blind_paytable={"royal_flush": 100.0, "straight_flush": 50.0,
        "four_of_a_kind": 10.0, "full_house": 3.0, "flush": 1.5, "straight": 1.0, "other": 0.0})
    assert settle(p, d, 1, custom).blind == 100


def test_dealer_qualification_boundary_is_exactly_a_pair():
    _, high = ranks("As Ah", "Ks Qd", "2c 3d 7h 8s 9c")
    _, pair = ranks("As Ah", "Ks Qd", "Kc 3d 7h 8s 9c")
    assert not dealer_qualifies(high)
    assert dealer_qualifies(pair)
