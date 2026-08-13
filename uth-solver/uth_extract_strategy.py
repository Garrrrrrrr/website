from __future__ import annotations

import argparse
from random import Random

from uth.cards import card_name
from uth.reports import metadata, write_json
from uth.simulation import deal
from uth.solver import solve


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract exact UTH exposed-card strategy changes")
    parser.add_argument("--states", type=int, default=100)
    parser.add_argument("--stage", choices=["flop", "river"], default="river")
    parser.add_argument("--seed", type=int, default=20260813)
    args = parser.parse_args()
    rng = Random(args.seed)
    board_cards = 3 if args.stage == "flop" else 5
    changes = []
    for _ in range(args.states):
        actual = deal(rng)
        normal = solve(actual.information(board_cards, False))
        exposed = solve(actual.information(board_cards, True))
        if normal.action != exposed.action:
            normal_action_conditional_ev = exposed.evs[normal.action]
            changes.append({"player": [card_name(card) for card in actual.player],
                "board": [card_name(card) for card in actual.board[:board_cards]],
                "dealer_exposed": card_name(actual.dealer_visible), "normal_action": normal.action,
                "exposed_action": exposed.action, "normal_ev": max(normal.evs.values()),
                "exposed_ev": max(exposed.evs.values()), "normal_margin": normal.difference,
                "exposed_margin": exposed.difference,
                "conditional_ev_shift": max(exposed.evs.values()) - max(normal.evs.values()),
                "normal_action_ev_conditioned_on_exposed_card": normal_action_conditional_ev,
                "policy_improvement": max(0.0, max(exposed.evs.values()) - normal_action_conditional_ev)})
    result = {"metadata": metadata(args.states, args.seed), "stage": args.stage,
              "states_examined": args.states, "changes": changes}
    write_json("results/uth/strategy_changes.json", result)
    print(f"Stored {len(changes)} action changes from {args.states} states.")


if __name__ == "__main__":
    main()
