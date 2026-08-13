from __future__ import annotations

from dataclasses import dataclass


def _validate(player: tuple[int, ...], board: tuple[int, ...], visible: int | None) -> None:
    if len(player) != 2 or len(board) not in (0, 3, 5):
        raise ValueError("UTH information requires 2 player cards and 0, 3, or 5 board cards")
    cards = (*player, *board, *((visible,) if visible is not None else ()))
    if any(card < 0 or card >= 52 for card in cards) or len(cards) != len(set(cards)):
        raise ValueError("cards must be distinct values in [0, 51]")


@dataclass(frozen=True, slots=True)
class InformationState:
    player: tuple[int, int]
    board: tuple[int, ...] = ()
    dealer_visible: int | None = None

    def __post_init__(self) -> None:
        _validate(self.player, self.board, self.dealer_visible)

    @property
    def stage(self) -> str:
        return {0: "opening", 3: "flop", 5: "river"}[len(self.board)]

    @property
    def known_cards(self) -> tuple[int, ...]:
        return (*self.player, *self.board, *((self.dealer_visible,) if self.dealer_visible is not None else ()))


@dataclass(frozen=True, slots=True)
class ActualState:
    player: tuple[int, int]
    dealer_visible: int
    dealer_hidden: int
    board: tuple[int, int, int, int, int]

    def __post_init__(self) -> None:
        cards = (*self.player, self.dealer_visible, self.dealer_hidden, *self.board)
        if len(set(cards)) != 9 or any(card < 0 or card >= 52 for card in cards):
            raise ValueError("actual deal must contain nine distinct cards")

    def information(self, board_cards: int, expose_dealer: bool) -> InformationState:
        if board_cards not in (0, 3, 5):
            raise ValueError("board_cards must be 0, 3, or 5")
        return InformationState(self.player, self.board[:board_cards], self.dealer_visible if expose_dealer else None)
