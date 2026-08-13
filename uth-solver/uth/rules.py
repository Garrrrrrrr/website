from __future__ import annotations

from dataclasses import dataclass, field

from .evaluator import HandCategory, HandRank

STANDARD_BLIND_PAYTABLE: dict[str, float] = {
    "royal_flush": 500.0,
    "straight_flush": 50.0,
    "four_of_a_kind": 10.0,
    "full_house": 3.0,
    "flush": 1.5,
    "straight": 1.0,
    "other": 0.0,
}


@dataclass(frozen=True, slots=True)
class UTHRules:
    name: str = "Wizard of Odds standard U.S. (4x opening strategy)"
    rules_version: str = "Wizard of Odds, accessed 2026-08-13; page updated 2026-08-03"
    ante: float = 1.0
    blind: float = 1.0
    opening_play: int = 4
    flop_play: int = 2
    river_play: int = 1
    blind_paytable: dict[str, float] = field(default_factory=lambda: dict(STANDARD_BLIND_PAYTABLE))

    def blind_payout(self, hand: HandRank) -> float:
        if hand.is_royal_flush:
            key = "royal_flush"
        else:
            key = {
                HandCategory.STRAIGHT_FLUSH: "straight_flush",
                HandCategory.FOUR_OF_A_KIND: "four_of_a_kind",
                HandCategory.FULL_HOUSE: "full_house",
                HandCategory.FLUSH: "flush",
                HandCategory.STRAIGHT: "straight",
            }.get(hand.category, "other")
        return self.blind_paytable[key]


def dealer_qualifies(hand: HandRank) -> bool:
    return hand.category >= HandCategory.PAIR
