from __future__ import annotations

import argparse
import json

from uth.reports import metadata, write_json
from uth.simulation import simulate

WIZARD_OPTIMAL_EV = -0.02185
WIZARD_SIMPLE_EV = -0.0243


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate ordinary UTH before exposed-card research")
    parser.add_argument("--hands", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=20260813)
    parser.add_argument("--quality", choices=["basic", "exact-late"], default="basic")
    args = parser.parse_args()
    summary = simulate("baseline", args.hands, args.seed, args.quality)["baseline"]
    target = WIZARD_OPTIMAL_EV if args.quality == "exact-late" else WIZARD_SIMPLE_EV
    stats = summary["statistics"]
    low, high = stats["confidence_interval"]
    passed = low <= target <= high
    eligible = passed and args.quality == "exact-late" and stats["half_width"] <= 0.001
    result = {"metadata": metadata(args.hands, args.seed), "strategy": args.quality,
              "wizard_ev": target, "wizard_optimal_ev": WIZARD_OPTIMAL_EV,
              "our_ev": summary["ev_per_round"], "difference": summary["ev_per_round"] - target,
              "standard_error": stats["standard_error"], "confidence_interval_99_9": [low, high],
              "status": "PASS" if passed else "FAIL", "eligible_for_exposed_edge": eligible,
              "optimal_baseline_status": "PASS" if eligible else "NOT VALIDATED",
              "summary": summary,
              "note": "basic validates Wizard's readable strategy (-2.43%), not the optimal -2.185% baseline" if args.quality == "basic" else "exact-late uses exact flop/river and sampled exposed opening only"}
    write_json("results/uth/baseline_validation.json", result)
    print("UTH BASELINE VALIDATION")
    print(f"Wizard EV: {target:+.6f}\nOur EV:    {summary['ev_per_round']:+.6f}")
    print(f"Difference: {result['difference']:+.6f}\nSE: {stats['standard_error']:.6f}\n{result['status']}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
