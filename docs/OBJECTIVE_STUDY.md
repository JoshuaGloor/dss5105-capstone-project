# Objective study: one scorer, five configurations

Sprint 2 adds three terms to the one weighted scorer and chooses one configuration per
course objective, plus our own priority (lateness first, then defects). Every choice
was made on development seeds and then run once on the course seeds.

Reproduce with `uv run python -m dss5105.objective_study` (about 10 seconds, no
provider calls). It writes [the evidence](evidence/objective-study.json): rules, grids,
every development and course metric, source hashes, and the course checks. A test keeps
`evaluate.PRESETS` equal to the frozen choices in that file.

## What changed in the scorer

The formula is still one weighted sum; a preset name never changes allocation logic.
New terms are zero by default, so a configuration with only the original weights
ranks exactly as before.

```text
score = lateness   * (max(0, expected + buffer - available) + reservation * reserved_days
                      + miss_charge * [expected misses the date]) / 7 days
      + defects    * defect_rate / 0.10 * pieces / 750
      + fairness   * projected_share / 0.25
      + robustness * max(0, expected + 14 days - available) / 7 days
      + cost       * cost_per_piece / 1
```

- **Capacity reservation** (inside lateness). Only three active workshops make
  accessories (370 pieces a day in total); two of them also make tops. A tops batch at
  SteadyHands or Nimble Needle uses accessory capacity that tops-only shops cannot
  replace. `reserved_days` is that batch's pieces divided by the other category's total
  capacity: zero at a tops-only shop. It is read from the workshop register, never from
  future orders.
- **Pieces-weighted defects.** `% def pcs` weights defective batches by pieces, so the
  term is expected defective pieces in units of a typical 750-piece batch.
- **Fairness** needs to know where earlier batches went. The simulator passes only
  queues, so the allocator keeps a ledger of the pieces it placed in the current replay
  (the desk uses saved bookings). With an empty ledger the term has no effect.
- **Robustness** asks whether the plan would still meet the date if the chosen workshop
  stopped for the course's two-week closure, and penalises the shortfall.
- **On-time first** (inside lateness). Missing the date costs a fixed week of lateness,
  so a workshop that meets the date beats one that misses it unless the other terms
  differ by more than a week. Without it, reservation could prefer a shop that is a
  fraction of a day late over a shared shop that is on time (inbox R12). It is a design
  constant, not tuned.

The common scale Tracks v4 asks for is these fixed reference units: a week of lateness,
a 10% defect risk on a 750-piece batch, a quarter of all pieces, one cost unit a piece.

## Protocol, fixed before the course seeds were run

Selection used development seeds 6000-6029 (30 seeds, normal and shock, paired).
Selection on expected `% def pcs` (the profile defect rate weighted by pieces) avoids
choosing on the noise of the defect draw; reports show both.

| Objective | Grid | Rule |
|---|---|---|
| Lateness | reservation 0, 0.5, 1, 2 | Lowest mean late days (normal and shock), then % late, then the rate nearest 1 |
| Hybrid (ours) | defects 0.02-0.3 x buffer 0-8 days, reservation fixed | Within 0.25 points of the lateness preset's % late and no more late days, in both scenarios: lowest expected defects |
| Defects | lateness 0.1-0.5 x buffer 0 or 5, defects 1 | % late at most 0.85 x random's (both scenarios): lowest expected defects |
| Fairness | fairness 0.02-1 | Within 1 point of the lateness preset's % late: lowest max share |
| Robustness | robustness 0.05-1, plus the lateness preset | Lowest shock-minus-normal change in % late, then late days |

Development chose reservation 1, `hybrid` = lateness 1, defects 0.2, buffer 2 days;
`defects` = lateness 0.2, defects 1, buffer 5 days; `fairness` = 1; `robustness` = 0.5.
All keep reservation 1 and the one-week miss charge.

**Protocol note.** The course seeds were run twice. The first study had no miss charge.
Reviewing the desk afterwards, inbox request R12 recommended GiantWeave, 0.06 days late,
over Nimble Needle, which meets the date. We then added the miss charge as a design
constant and re-ran the whole study (development selection, then the course seeds). The
change was motivated by that desk case, not by course metrics. Development showed no
change for the hybrid, lateness and robustness choices; the course rows for those three
are identical in both runs. The defects and fairness selections changed, and their rows
below come from the second run.

## Results on the course seeds 5105-5114

Normal runs (mean of ten seeds):

| Policy | % late | late days | % def pcs | max share | cost |
|---|---|---|---|---|---|
| random | 34.167 | 6.133 | 5.599 | 22.6 | 111,780 |
| greedy_biggest | 84.250 | 26.528 | 5.278 | 70.2 | 108,430 |
| cheapest | 91.833 | 81.916 | 8.241 | 70.2 | 85,960 |
| earliest_finish | 1.667 | 0.178 | 7.182 | 26.3 | 115,566 |
| Sprint 1 lateness | 1.667 | 0.180 | 7.492 | 26.2 | 115,592 |
| **hybrid (default)** | **1.417** | **0.057** | 6.444 | 41.3 | 107,209 |
| lateness | 1.917 | 0.106 | 7.824 | 28.9 | 115,656 |
| defects | 27.500 | 3.532 | **4.904** | 39.5 | 111,116 |
| fairness | 1.833 | 0.147 | 6.818 | **19.2** | 112,166 |
| robustness | 1.667 | 0.132 | 8.198 | 28.8 | 114,578 |

Shock runs and the paired change (shock minus normal):

| Policy | % late | late days | % def pcs | change in % late (points) | change in late days |
|---|---|---|---|---|---|
| random | 38.167 | 7.166 | 5.599 | +4.000 | +1.033 |
| greedy_biggest | 84.917 | 28.047 | 5.278 | +0.667 | +1.518 |
| cheapest | 91.833 | 84.120 | 8.241 | +0.000 | +2.204 |
| earliest_finish | 1.917 | 0.191 | 7.118 | +0.250 | +0.013 |
| Sprint 1 lateness | 1.917 | 0.181 | 7.374 | +0.250 | +0.001 |
| hybrid (default) | 2.083 | 0.102 | 6.444 | +0.667 | +0.045 |
| lateness | 2.167 | 0.133 | 7.909 | +0.250 | +0.027 |
| defects | 27.833 | 3.663 | 4.861 | +0.333 | +0.131 |
| fairness | 2.250 | 0.171 | 6.893 | +0.417 | +0.024 |
| robustness | 1.750 | 0.136 | 8.048 | +0.083 | +0.004 |

## What this means

- **Primary objective (lateness).** Every configuration beats all three baselines on
  both lateness metrics. The default hybrid now also beats the earliest-finish rule
  that tied us in Sprint 1: 1.417% late against 1.667% and 68% fewer late days in normal
  runs, 47% fewer late days under shock. It is 0.17 points worse on the shock late rate
  (two batches over ten runs).
- **Secondary objective (defects).** The hybrid cuts defective pieces from 7.18% to
  6.44% and cost by 7.2% against earliest finish, without giving up lateness.
- **Defects as an objective.** The defects configuration beats all three baselines on
  `% def pcs`: 4.904 against greedy_biggest's 5.278, and 4.861 under the shock. It stays
  inside the guardrail (27.5% late against random's 34.2%). This reverses the Sprint 1
  finding that greedy_biggest still won.
- **Fairness.** Max share 19.2% against random's 22.6%, at 1.8% late: a more even
  spread than random while delivering on time, which Tracks v4 counts as a win.
- **Robustness.** The robustness configuration moves least under the closure among the
  policies that pass the lateness guardrail (+0.083 points). The Sprint 1 lateness preset
  moves fewer late days (+0.001); cheapest moves 0 points only because it is late 92% of
  the time. We do not claim a universal robustness win.
- **Reservation alone** reduces late days on both seed sets but its late rate is mixed
  (better on development, 0.25 points worse on the course seeds). That is why the
  default is the hybrid, not the reservation-only lateness preset.

## Why it works, and where it stops

Two 2,000-piece accessory orders (ORD-108 and ORD-062) arrive five days apart with
17-day windows. Total accessory capacity is 370 pieces a day, so at least one of them is
late under any whole-batch policy. Over the 30 development seeds (normal runs):

- Earliest finish sends about 4,900 tops pieces a run to SteadyHands and Nimble Needle,
  the two shops that also make accessories. Both accessory orders are always late, by
  3.9 and 15.1 days on average.
- With reservation, no tops go to those two shops. ORD-108 is still late, by 2.2 days.
- The hybrid's buffer and quality term change where the earlier accessory work goes,
  and ORD-062 is on time in 20 of 30 seeds.

The cost is concentration: GiantWeave takes about 41% of all pieces in the hybrid.

## Limits

- Development and course seeds replay the same 120 orders, so this guards against tuning
  to defect and closure draws, not to the order stream.
- Ten course seeds are a small sample; one late batch moves `% late` by 0.083 points.
- The fairness ledger counts only this replay's (or this plan's) pieces, not work the
  workshops hold for other customers.
- Splits remain outside the simulator, so the accessory pair stays a hard case.
