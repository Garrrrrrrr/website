from __future__ import annotations

import argparse
import json
from pathlib import Path

from uth.reports import metadata, write_json
from uth.simulation import simulate_parallel


def main() -> None:
    parser = argparse.ArgumentParser(description="UTH paired/full-game simulation")
    parser.add_argument("--mode", choices=["baseline", "river", "flop", "exposed", "paired", "stages"], default="paired")
    parser.add_argument("--hands", type=int, default=1000)
    parser.add_argument("--workers", default="auto", help="Reserved for compiled multicore runner compatibility")
    parser.add_argument("--seed", type=int, default=20260813)
    parser.add_argument("--quality", choices=["basic", "exact-late"], default="basic")
    parser.add_argument("--opening-samples", type=int, default=8)
    parser.add_argument("--output")
    parser.add_argument("--allow-unvalidated", action="store_true", help="Development only: bypass optimal-baseline gate")
    args = parser.parse_args()
    if args.mode != "baseline" and not args.allow_unvalidated:
        validation_path = Path("results/uth/baseline_validation.json")
        validation = json.loads(validation_path.read_text(encoding="utf-8")) if validation_path.exists() else {}
        if not validation.get("eligible_for_exposed_edge"):
            raise SystemExit("STOP: optimal baseline has not passed at the required precision; exposed-card edge calculation is gated. Use --allow-unvalidated only for development diagnostics.")
    result = {"metadata": metadata(args.hands, args.seed),
              "result": simulate_parallel(args.mode, args.hands, args.seed, args.quality, args.opening_samples, args.workers)}
    output = args.output or f"results/uth/{args.mode}.json"
    write_json(output, result)
    print(json.dumps(result, indent=2))
    print(f"\nSaved {Path(output)}")


if __name__ == "__main__":
    main()
