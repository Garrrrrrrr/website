from __future__ import annotations

from dataclasses import dataclass

from .evaluator import HandRank
from .rules import UTHRules, dealer_qualifies


@dataclass(frozen=True, slots=True)
class UTHPayoff:
    ante: float
    blind: float
    play: float

    @property
    def total(self) -> float:
        return self.ante + self.blind + self.play


def settle(player: HandRank, dealer: HandRank, play_units: int, rules: UTHRules = UTHRules()) -> UTHPayoff:
    """Canonical net-profit settlement. Stakes returned on a push are not profit."""
    if play_units not in (1, 2, 4):
        raise ValueError("Play must be 1x, 2x, or 4x")
    if player == dealer:
        return UTHPayoff(0.0, 0.0, 0.0)
    qualifies = dealer_qualifies(dealer)
    if player > dealer:
        return UTHPayoff(rules.ante if qualifies else 0.0, rules.blind_payout(player), float(play_units))
    return UTHPayoff(-rules.ante if qualifies else 0.0, -rules.blind, -float(play_units))


def settle_fold(rules: UTHRules = UTHRules()) -> UTHPayoff:
    return UTHPayoff(-rules.ante, -rules.blind, 0.0)
