# Data Findings

Everything here is measured against the committed data in `track2/`. If you change the
data, re-run and update this file. Reproduction commands are at the bottom.

"Today" in the dataset is **2026-04-01**. Stages are KNITTING, ASSEMBLY, WASHING, PACKING.

## Finding 1: the baselines are not a target

A five-line heuristic (pick the eligible shop with the earliest
`queue + pieces/capacity + lead_days`) beats all three provided baselines by a wide
margin:

| policy | mean days | p90 | % late | % defect | cost | max share |
|---|---|---|---|---|---|---|
| `random` | 21.5 | 45.6 | 34% | 4% | 111,780 | 23% |
| `greedy_biggest` | 49.0 | 80.6 | 84% | 4% | 108,430 | 70% |
| `cheapest` | 105.1 | 192.9 | 93% | 8% | 85,960 | 70% |
| **5-line earliest-finish** | **8.1** | **13.7** | **2%** | 5% | 115,640 | 26% |

Consequence: "we beat the baselines" is table stakes and must not be our headline. The
real comparison the spec asks for is our full system against the best short heuristic.

## Finding 2: the shock scenario is absorbed almost for free

Under `--shock`, earliest-finish degrades only 8.1 -> 8.4 mean days.

The reason is mechanical. When a workshop closes, `simulate.py` still advances that
shop's `queue_free`, so the `queues` dict handed to the allocator already encodes the
closure one batch after work starts piling up there. Any queue-aware policy therefore
"adapts" without ever detecting anything.

This is an honest negative result and we will report it as one. The interesting question
becomes what *explicit* shock detection adds on top, which we measure rather than assume.

## Finding 3: quality at speed is arithmetically impossible in this factory

This is structural, not a tuning problem.

| shop | defect rate | capacity/day | makes |
|---|---|---|---|
| W4 Little Loom | 0.02 | 70 | ACCESSORIES |
| W2 SteadyHands | 0.03 | 170 | TOPS+ACCESSORIES |
| W8 FreshStart | 0.04 | 100 | TOPS (max 300/batch) |
| W1 QuickStitch | 0.12 | 300 | TOPS |
| W5 GiantWeave | 0.06 | 400 | TOPS |

The two low-defect shops run 240 pieces/day combined. QuickStitch alone does 300/day at
six times W2's defect rate. So routing for quality starves capacity: a pure
minimise-defects policy reaches 2.7% expected defect but **95% late**. That tension is
the factory's real dilemma and it explains why both `cheapest` and a naive low-defect
policy collapse.

## Finding 4: accessories are the binding constraint

Only W2 (170/day), W4 (70/day) and W6 (130/day) make ACCESSORIES: 370 pieces/day in
total. But 27 of the 35 accessory orders exceed 300 pieces, and R20 alone asks for
2,000 scarves. Every genuinely hard allocation in the inbox is an accessories order.

## Finding 5: 12 of the 16 allocatable requests cannot hit the date they ask for

This is the finding most likely to be missed. Best achievable completion is computed as
`current_queue_days + pieces/capacity + pickup_lead_days` from 2026-04-01 across all
eligible shops.

| req | order | cat | pieces | requested | best possible | via | slip (days) |
|---|---|---|---|---|---|---|---|
| R04 | ORD-029 | ACCESSORIES | 1500 | 2026-04-01 | 2026-04-14 | SteadyHands | +13 |
| R06 | ORD-061 | ACCESSORIES | 800 | 2026-04-05 | 2026-04-09 | Nimble Needle | +4 |
| R07 | ORD-020 | TOPS | 1200 | 2026-03-31 | 2026-04-10 | QuickStitch | +10 |
| R09 | ORD-045 | TOPS | 150 | 2026-04-09 | 2026-04-04 | Nimble Needle | -5 |
| R12 | ORD-053 | TOPS | 800 | 2026-04-10 | 2026-04-09 | QuickStitch | -1 |
| R16 | ORD-114 | TOPS | 2000 | 2026-03-23 | 2026-04-13 | QuickStitch | +21 |
| R17 | ORD-120 | TOPS | 1500 | 2026-03-17 | 2026-04-11 | QuickStitch | +25 |
| R20 | ORD-103 | ACCESSORIES | 2000 | 2026-04-04 | 2026-04-17 | SteadyHands | +13 |
| R21 | ORD-081 | TOPS | 1500 | 2026-04-13 | 2026-04-11 | QuickStitch | -2 |
| R22 | ORD-083 | TOPS | 1000 | 2026-03-23 | 2026-04-09 | QuickStitch | +17 |
| R23 | ORD-093 | ACCESSORIES | 100 | 2026-03-29 | 2026-04-04 | Nimble Needle | +6 |
| R25 | ORD-109 | TOPS | 500 | 2026-04-13 | 2026-04-07 | Nimble Needle | -6 |
| R26 | ORD-107 | TOPS | 2000 | 2026-03-16 | 2026-04-13 | QuickStitch | +28 |
| R27 | ORD-055 | TOPS | 800 | 2026-03-31 | 2026-04-09 | QuickStitch | +9 |
| R28 | ORD-002 | TOPS | 1000 | 2026-03-29 | 2026-04-09 | QuickStitch | +11 |
| R30 | ORD-099 | TOPS | 1500 | 2026-04-05 | 2026-04-11 | QuickStitch | +6 |

Only **R09, R12, R21 and R25** are feasible as requested. Nine of the twelve misses ask
for a date that is already in the past on 2026-04-01; R06, R20 and R30 are future-dated
but still unreachable once queues are counted.

Design consequence: `INFEASIBLE_DEADLINE` is a first-class outcome, not an error. The
correct behaviour on 12 of 16 allocatable requests is *allocate and report the slip*
with the earliest achievable date. A system that replies "sent to QuickStitch" without
naming the slip is wrong on 75% of the allocatable inbox.

Note also R27, which asks for the lowest defect rate but whose fastest option is
QuickStitch, the worst-defect shop. Objective and deadline genuinely conflict there.

## Finding 6: the objectives partially co-optimise; defects is the odd one out

Swept 624 weight configurations over (lateness, defects, fairness, cost).

| config | mean days | % late | expected defect | cost | max share |
|---|---|---|---|---|---|
| pure lateness | 8.1 | 2% | 6.9% | 114,065 | **24%** |
| **lateness + cost + fairness** | 9.9 | **2%** | 6.1% | **103,920** | 34% |
| pure defects | 162.5 | 95% | **2.7%** | 129,920 | 70% |
| pure cost | 105.1 | 93% | 7.8% | **85,960** | 70% |

Lateness, cost and fairness are largely compatible: we can hold 2% late while cutting
about 10,000 of cost relative to optimising lateness alone. Minimising defects is the
only objective that forces a genuine sacrifice, for the structural reason in Finding 3.

## Finding 7: a metric objection worth reporting

`simulate.py` draws defects stochastically, one Bernoulli trial per batch, so the
reported `% defect` is noisy across policies and partly reflects the RNG rather than the
allocation. We additionally report **pieces-weighted expected defect rate of the chosen
shops**, which carries the same signal with no variance.

The track explicitly invites arguing with the harness given evidence, so this belongs in
`Evaluation.pdf`. We report both numbers; we do not silently substitute ours.

## The eight workshops

| id | name | cap/day | lead | defect | cost | makes | status | max batch | queue today |
|---|---|---|---|---|---|---|---|---|---|
| W1 | QuickStitch | 300 | 1 | 0.12 | 1.5 | TOPS | ACTIVE | - | 4.0 |
| W2 | SteadyHands | 170 | 2 | 0.03 | 1.3 | TOPS+ACC | ACTIVE | - | 2.5 |
| W3 | BudgetWorks | 230 | 3 | 0.09 | 0.8 | TOPS | ACTIVE | - | 5.0 |
| W4 | Little Loom | 70 | 1 | 0.02 | 1.6 | ACCESSORIES | ACTIVE | - | 0.5 |
| W5 | GiantWeave | 400 | 4 | 0.06 | 1.1 | TOPS | ACTIVE | - | 3.0 |
| W6 | Nimble Needle | 130 | 1 | 0.05 | 1.2 | TOPS+ACC | ACTIVE | - | 1.0 |
| W7 | OldMill | 200 | 2 | 0.10 | 0.9 | TOPS+ACC | **SUSPENDED** | - | 0.0 |
| W8 | FreshStart | 100 | 2 | 0.04 | 1.0 | TOPS | ACTIVE | **300** | 0.0 |

W7 is never eligible. W8 rejects any batch over 300 pieces.

## Order data shape

120 orders, 86 COMPLETE and 34 IN_PROGRESS. 85 TOPS, 35 ACCESSORIES. Pieces range
100 to 2000, mean 779. Order dates 2026-01-01 to 2026-03-27; due dates 2026-01-18 to
2026-05-01. Lead time from order to due date is 14 to 35 days, mean 25.1.

Eight customers, the largest being Cotton Club and Maple & Co at 19 orders each and
TrendCart at 17. That matters for ambiguity: "the TrendCart order" has 17 candidates and
"the vests" has 18.

## Reproducing

```
python3 track2/harness/simulate.py            # the three baselines
python3 track2/harness/simulate.py --shock    # with the mid-run closure
```

The simulator is seeded (5105) and deterministic. The heuristic, sweep and feasibility
numbers above were produced by throwaway probe scripts; they are reproduced as committed
code under the allocation-engine and evaluation workstreams.
