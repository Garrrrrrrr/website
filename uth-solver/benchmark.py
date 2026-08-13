from __future__ import annotations

import argparse
import json
from random import Random
from time import perf_counter

from uth.reports import metadata, write_json
from uth.simulation import deal, simulate
from uth.solver import flop_decision, river_decision


def rate(fn, states):
    start = perf_counter()
    outcomes = sum(fn(state).outcomes for state in states)
    seconds = perf_counter() - start
    return {"states": len(states), "terminal_outcomes": outcomes, "seconds": seconds,
            "states_per_second": len(states) / seconds, "terminal_outcomes_per_second": outcomes / seconds}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--states", type=int, default=3)
    parser.add_argument("--hands", type=int, default=1000)
    parser.add_argument("--workers", default="auto")
    args = parser.parse_args()
    rng = Random(20260813)
    deals = [deal(rng) for _ in range(args.states)]
    river = rate(river_decision, [item.information(5, True) for item in deals])
    flop = rate(flop_decision, [item.information(3, True) for item in deals])
    start = perf_counter(); simulate("baseline", args.hands, quality="basic"); complete = args.hands / (perf_counter() - start)
    rates = {"river": river, "flop": flop, "preflop": {"note": "sampled flops with exact children; state dependent"},
             "complete_hands_per_second_single_core_basic": complete}
    seconds = {label: count / complete for label, count in {"1M": 1e6, "10M": 1e7, "100M": 1e8,
        "1B": 1e9, "10B": 1e10, "100B": 1e11, "1T": 1e12}.items()}
    result = {"metadata": metadata(args.hands, 20260813), "rates": rates, "estimated_seconds": seconds,
              "all_core": "not implemented in Python reference runner", "memory": "streaming O(1), caches excluded"}
    write_json("results/uth/benchmark.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
