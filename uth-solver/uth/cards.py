from __future__ import annotations

RANKS = "23456789TJQKA"
SUITS = "cdhs"
DECK = tuple(range(52))


def parse_card(text: str) -> int:
    value = text.strip()
    if len(value) != 2:
        raise ValueError(f"invalid card: {text!r}")
    rank = RANKS.find(value[0].upper())
    suit = SUITS.find(value[1].lower())
    if rank < 0 or suit < 0:
        raise ValueError(f"invalid card: {text!r}")
    return suit * 13 + rank


def parse_cards(text: str) -> tuple[int, ...]:
    cards = tuple(parse_card(item) for item in text.split()) if text.strip() else ()
    if len(cards) != len(set(cards)):
        raise ValueError("duplicate card")
    return cards


def card_name(card: int) -> str:
    if not 0 <= card < 52:
        raise ValueError("card must be in [0, 51]")
    return RANKS[card % 13] + SUITS[card // 13]


def rank(card: int) -> int:
    return card % 13 + 2


def suit(card: int) -> int:
    return card // 13
