# Ultimate Texas Hold'em solver

Auditable UTH research engine for the website's **Ultimate Texas Hold'em** page.
The core models Ante, Blind, and Play only; Trips and other side bets are excluded.

## Verified rules

Primary source: [Wizard of Odds UTH](https://wizardofodds.com/games/ultimate-texas-hold-em/),
accessed 2026-08-13 (page updated 2026-08-03).

- One 52-card deck; Ante and Blind are one unit each.
- Wizard's standard U.S. rules allow a 3x or 4x opening Play wager. The optimal
  chart uses 4x, and this project intentionally exposes only the requested 4x/check choice.
- After a check: 2x/check on the three-card flop, then 1x/fold after all five board cards.
- Each side uses the best five of its two hole cards plus five community cards.
- Dealer qualifies with **a pair or better**. Non-qualification pushes Ante only.
  Play and Blind retain action. Ties push all three wagers.
- Winning Ante and Play pay even money. Standard Blind pays 500/50/10/3/1.5/1
  for royal/straight flush/quads/full house/flush/straight; lower winning hands push.
- The Auckland both-hole-cards rule, Genting automatic Play win, Australian
  non-qualifying Blind variation, payout caps, and side bets are not the default.

Every EV is expected **final net profit for the whole round in Ante units**.
`ActualState` owns the complete simulated deal. `InformationState` cannot store
the hidden dealer card, and every solver API accepts only the latter.

## Methods and current quality boundary

- River: exact enumeration (44 exposed or 990 normal dealer holdings).
- Flop: exact board-grouped backward induction (45,540 exposed or about 1.07M
  normal terminal assignments). Checking includes the optimal exact river choice.
- Opening: paired sampling over flops, with exact conditional flop and river
  children. Recommendations remain `INCONCLUSIVE` unless their paired 99.9% CI
  excludes zero and has half-width at most 0.001.
- The fast full-game runner uses Wizard's readable strategy and is suitable for
  plumbing/variance tests, not claims about perfect exposed-card play. `exact-late`
  invokes exact later decisions and is deliberately slower.

Wizard publishes optimal EV -0.02185/Ante, 4.152252 average total wager, 0.526%
element of risk, and SD 4.94. Wizard's simpler chart returns about -0.0243/Ante.
The validation artifact identifies which target was tested. No exposed-card edge
should be promoted until a high-precision **optimal** baseline validation passes.

## Commands

```bash
python -m pytest -q
python uth_analyze.py --player "As Qs" --dealer-visible "Kh"
python uth_analyze.py --player "As Qs" --dealer-visible "Kh" --board "Js 8s 3c"
python uth_analyze.py --player "As Qs" --dealer-visible "Kh" --board "Js 8s 3c 2d 7h"
python uth_validate.py --hands 100000
python uth_simulate.py --mode baseline --hands 100000000 --workers auto
python uth_simulate.py --mode exposed --hands 100000000 --workers auto
python uth_simulate.py --mode paired --hands 100000000 --workers auto
python uth_simulate.py --mode stages --hands 100000
python uth_extract_strategy.py --stage river --states 10000
python benchmark.py
```

Non-baseline simulation modes are safety-gated by
`results/uth/baseline_validation.json`. They stop unless an optimal validation
has passed with a 99.9% half-width no greater than 0.001. The explicit
`--allow-unvalidated` switch exists only for development diagnostics; its output
must not be reported as an exposed-card edge.

Exports include rules version, paytable, sample count, seed, solver version, Git
commit, confidence data, and runtime under `results/uth/`.
