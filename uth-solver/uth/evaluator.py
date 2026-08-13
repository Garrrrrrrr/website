from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from functools import total_ordering

from .cards import rank, suit


class HandCategory(IntEnum):
    HIGH_CARD = 0
    PAIR = 1
    TWO_PAIR = 2
    THREE_OF_A_KIND = 3
    STRAIGHT = 4
    FLUSH = 5
    FULL_HOUSE = 6
    FOUR_OF_A_KIND = 7
    STRAIGHT_FLUSH = 8


@total_ordering
@dataclass(frozen=True, slots=True)
class HandRank:
    category: HandCategory
    kickers: tuple[int, ...]

    @property
    def is_royal_flush(self) -> bool:
        return self.category == HandCategory.STRAIGHT_FLUSH and self.kickers == (14,)

    def key(self) -> tuple[int, ...]:
        return (int(self.category), *self.kickers)

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, HandRank):
            return NotImplemented
        return self.key() < other.key()

    def __eq__(self, other: object) -> bool:
        return isinstance(other, HandRank) and self.key() == other.key()


def _straight_high(values: set[int]) -> int:
    if 14 in values:
        values = {*values, 1}
    run = 0
    previous = -2
    for value in sorted(values):
        run = run + 1 if value == previous + 1 else 1
        if run >= 5:
            high = value
        previous = value
    return locals().get("high", 0)


def evaluate(cards: tuple[int, ...] | list[int]) -> HandRank:
    """Evaluate any 5-7 distinct cards; ordered tuples include every kicker."""
    if not 5 <= len(cards) <= 7 or len(set(cards)) != len(cards):
        raise ValueError("evaluate requires 5-7 distinct cards")
    counts = [0] * 15
    suited: list[list[int]] = [[], [], [], []]
    for card in cards:
        value = rank(card)
        counts[value] += 1
        suited[suit(card)].append(value)

    for values in suited:
        if len(values) >= 5:
            high = _straight_high(set(values))
            if high:
                return HandRank(HandCategory.STRAIGHT_FLUSH, (high,))

    quads = [value for value in range(14, 1, -1) if counts[value] == 4]
    if quads:
        quad = quads[0]
        kicker = max(value for value in range(2, 15) if value != quad and counts[value])
        return HandRank(HandCategory.FOUR_OF_A_KIND, (quad, kicker))

    trips = [value for value in range(14, 1, -1) if counts[value] >= 3]
    if trips:
        pairs = [value for value in range(14, 1, -1) if value != trips[0] and counts[value] >= 2]
        if pairs:
            return HandRank(HandCategory.FULL_HOUSE, (trips[0], pairs[0]))

    flushes = [sorted(values, reverse=True)[:5] for values in suited if len(values) >= 5]
    if flushes:
        return HandRank(HandCategory.FLUSH, tuple(max(flushes)))

    high = _straight_high({value for value in range(2, 15) if counts[value]})
    if high:
        return HandRank(HandCategory.STRAIGHT, (high,))
    if trips:
        kickers = [value for value in range(14, 1, -1) if value != trips[0] and counts[value]][:2]
        return HandRank(HandCategory.THREE_OF_A_KIND, (trips[0], *kickers))
    pairs = [value for value in range(14, 1, -1) if counts[value] >= 2]
    if len(pairs) >= 2:
        kicker = max(value for value in range(2, 15) if value not in pairs[:2] and counts[value])
        return HandRank(HandCategory.TWO_PAIR, (pairs[0], pairs[1], kicker))
    if pairs:
        kickers = [value for value in range(14, 1, -1) if value != pairs[0] and counts[value]][:3]
        return HandRank(HandCategory.PAIR, (pairs[0], *kickers))
    return HandRank(HandCategory.HIGH_CARD, tuple(value for value in range(14, 1, -1) if counts[value])[:5])


def evaluate7(cards: tuple[int, ...] | list[int]) -> HandRank:
    if len(cards) != 7:
        raise ValueError("evaluate7 requires exactly seven cards")
    return evaluate(cards)
