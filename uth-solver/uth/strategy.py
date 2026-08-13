from __future__ import annotations

from collections import Counter

from .cards import rank, suit
from .cards import DECK
from .evaluator import HandCategory, evaluate
from .state import InformationState


def basic_opening_action(player: tuple[int, int]) -> str:
    """Wizard advanced DP1 table. The 3x option is dominated and omitted."""
    a, b = sorted((rank(player[0]), rank(player[1])), reverse=True)
    suited = suit(player[0]) == suit(player[1])
    if a == b:
        return "CHECK" if a == 2 else "4X"
    if suited:
        return "4X" if a >= 13 or (a == 12 and b >= 6) or (a == 11 and b >= 8) else "CHECK"
    return "4X" if a == 14 or (a == 13 and b >= 5) or (a == 12 and b >= 8) or (a == 11 and b == 10) else "CHECK"


def basic_flop_action(state: InformationState) -> str:
    """Wizard simple strategy, intentionally separate from the EV solver."""
    if len(state.board) != 3:
        raise ValueError("flop strategy requires three board cards")
    hand = evaluate((*state.player, *state.board))
    if hand.category >= HandCategory.TWO_PAIR:
        return "2X"
    counts = Counter(rank(card) for card in (*state.player, *state.board))
    hidden_pair = any(counts[rank(card)] >= 2 for card in state.player)
    if hidden_pair and not (rank(state.player[0]) == rank(state.player[1]) == 2):
        return "2X"
    for target_suit in range(4):
        cards = [card for card in (*state.player, *state.board) if suit(card) == target_suit]
        if len(cards) == 4 and any(suit(card) == target_suit and rank(card) >= 10 for card in state.player):
            return "2X"
    return "CHECK"


def basic_river_action(state: InformationState) -> str:
    """Conservative readable shortcut; exact river decisions use solver.river_decision."""
    if len(state.board) != 5:
        raise ValueError("river strategy requires five board cards")
    hand = evaluate((*state.player, *state.board))
    counts = Counter(rank(card) for card in (*state.player, *state.board))
    hidden_pair = any(counts[rank(card)] >= 2 for card in state.player)
    if hand.category >= HandCategory.TWO_PAIR or hidden_pair:
        return "1X"
    # Wizard's readable shortcut counts individual unseen cards that, together
    # with the board, already make a hand that beats the player. It deliberately
    # ignores dealer wins requiring a particular two-card combination.
    known = set(state.known_cards)
    outs = 0
    for card in DECK:
        if card not in known and evaluate((*state.board, card)) > hand:
            outs += 1
    return "1X" if outs < 21 else "FOLD"
