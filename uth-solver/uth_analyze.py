from __future__ import annotations

import argparse
import json

from uth.cards import card_name, parse_card, parse_cards
from uth.solver import solve
from uth.state import InformationState


def main() -> None:
    parser = argparse.ArgumentParser(description="Ultimate Texas Hold'em hand analyzer")
    parser.add_argument("--player", required=True)
    parser.add_argument("--dealer-visible")
    parser.add_argument("--board", default="")
    parser.add_argument("--samples", type=int, default=200)
    parser.add_argument("--seed", type=int, default=20260813)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    player, board = parse_cards(args.player), parse_cards(args.board)
    visible = parse_card(args.dealer_visible) if args.dealer_visible else None
    state = InformationState(player, board, visible)
    informed = solve(state, samples=args.samples, seed=args.seed)
    normal_state = InformationState(player, board)
    normal = informed if visible is None else solve(normal_state, samples=args.samples, seed=args.seed)
    informed_best = max(informed.evs.values())
    normal_action_conditional_ev = informed.evs.get(normal.action, informed_best)
    output = {"game": "Ultimate Texas Hold'em", "stage": state.stage,
        "player": [card_name(card) for card in player], "dealer_visible": args.dealer_visible,
        "board": [card_name(card) for card in board], "informed": informed.to_dict(),
        "normal": normal.to_dict(), "information_value": informed_best - normal_action_conditional_ev,
        "normal_action_ev_conditioned_on_exposed_card": normal_action_conditional_ev,
        "action_changed": informed.action != normal.action}
    if args.json:
        print(json.dumps(output, indent=2))
        return
    print("ULTIMATE TEXAS HOLD'EM\n")
    print(f"Stage: {state.stage.title()}\nPlayer: {' '.join(output['player'])}")
    print(f"Dealer exposed: {args.dealer_visible or 'None'}")
    if board:
        print(f"Board: {' '.join(output['board'])}")
    for action, ev in informed.evs.items():
        print(f"{action:8} EV: {ev:+.6f}")
    print(f"\nOPTIMAL: {informed.action}\nMethod: {informed.method}\nStatus: {informed.status}")
    print(f"Without dealer information: {normal.action}")
    print(f"Value of exposed information: {output['information_value']:+.6f}")


if __name__ == "__main__":
    main()
