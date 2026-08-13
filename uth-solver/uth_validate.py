from __future__ import annotations

import argparse
import json
from statistics import NormalDist

from uth.reports import metadata, write_json
from uth.simulation import simulate_parallel

WIZARD_OPTIMAL_EV = -0.02185
WIZARD_SIMPLE_EV = -0.0243
WIZARD_AVERAGE_ACTION = 4.152252
WIZARD_SD = 4.94


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate ordinary UTH before exposed-card research")
    parser.add_argument("--hands", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=20260813)
    parser.add_argument("--quality", choices=["basic", "exact-late"], default="basic")
    parser.add_argument("--workers", default="auto")
    args = parser.parse_args()
    simulation = simulate_parallel("baseline", args.hands, args.seed, args.quality, workers=args.workers)
    summary = simulation["baseline"]
    target = WIZARD_OPTIMAL_EV if args.quality == "exact-late" else WIZARD_SIMPLE_EV
    stats = summary["statistics"]
    low, high = stats["confidence_interval"]
    consistent = low <= target <= high
    precise = stats["half_width"] <= 0.001
    action_matches = abs(summary["average_total_action"] - WIZARD_AVERAGE_ACTION) <= 0.01 if args.quality == "exact-late" else None
    sd_matches = abs(summary["sd_per_round"] - WIZARD_SD) <= 0.05 if args.quality == "exact-late" else None
    eligible = consistent and precise and action_matches is True and sd_matches is True and args.quality == "exact-late"
    z = NormalDist().inv_cdf(0.9995)
    required_hands = {str(tolerance): int(summary["variance"] * (z / tolerance) ** 2) + 1
                      for tolerance in (0.001, 0.0005, 0.00025)}
    status = ("VALIDATED" if eligible else "FAIL" if not consistent else
              "CONSISTENT_BUT_POLICY_LIMITED" if args.quality != "exact-late" and precise else
              "CONSISTENT_BUT_UNDERPOWERED")
    result = {"metadata": metadata(args.hands, args.seed), "strategy": args.quality,
              "wizard_ev": target, "wizard_optimal_ev": WIZARD_OPTIMAL_EV,
              "wizard_average_total_action": WIZARD_AVERAGE_ACTION, "wizard_sd": WIZARD_SD,
              "our_ev": summary["ev_per_round"], "difference": summary["ev_per_round"] - target,
              "standard_error": stats["standard_error"], "confidence_interval_99_9": [low, high],
              "status": status, "consistent_with_ev_target": consistent, "precision_passed": precise,
              "average_action_passed": action_matches, "sd_passed": sd_matches,
              "estimated_hands_for_99_9_half_width": required_hands,
              "eligible_for_exposed_edge": eligible,
              "optimal_baseline_status": "VALIDATED" if eligible else "NOT VALIDATED",
              "parallelism": simulation["parallelism"],
              "summary": summary,
              "note": "basic validates Wizard's readable strategy (-2.43%), not the optimal -2.185% baseline" if args.quality == "basic" else "exact-late uses the published advanced opening chart and exact flop/river decisions"}
    write_json("results/uth/baseline_validation.json", result)
    print("UTH BASELINE VALIDATION")
    print(f"Wizard EV: {target:+.6f}\nOur EV:    {summary['ev_per_round']:+.6f}")
    print(f"Difference: {result['difference']:+.6f}\nSE: {stats['standard_error']:.6f}\n{status}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
