from uth.cards import parse_cards
from uth.evaluator import HandCategory, evaluate7


def hand(text: str):
    return evaluate7(parse_cards(text))


def test_all_categories_and_ordering():
    hands = [
        hand("As Kd 9c 7h 5s 3d 2c"),
        hand("As Ad 9c 7h 5s 3d 2c"),
        hand("As Ad 9c 9h 5s 3d 2c"),
        hand("As Ad Ac 9h 5s 3d 2c"),
        hand("As 2d 3c 4h 5s 9d Tc"),
        hand("As Js 9s 5s 3s Kd 2c"),
        hand("As Ad Ac 9h 9s 3d 2c"),
        hand("As Ad Ac Ah 9s 3d 2c"),
        hand("9s Ts Js Qs Ks 3d 2c"),
    ]
    assert [item.category for item in hands] == list(HandCategory)
    assert hands == sorted(hands)


def test_wheel_and_kickers():
    wheel = hand("As 2d 3c 4h 5s 9d Tc")
    six_high = hand("2s 3d 4c 5h 6s 9d Tc")
    assert wheel.kickers == (5,)
    assert six_high > wheel
    assert hand("As Ad Kc Qh Js 3d 2c") > hand("As Ad Kc Qh Ts 3d 2c")


def test_royal_flush_label():
    assert hand("Ts Js Qs Ks As 3d 2c").is_royal_flush
