# EXP-002: Accumulation comparison

**Created**: 2026-08-12
**Status**: completed
**Research questions**: [[RQ1]]

## Hypothesis

Across seeds 1 through 3, the mean final-validation-loss difference between
accumulated and true batches is below 0.02.

## Method

- **Instrument**: deterministic `scripts/simulate.py` toy simulator
- **Conditions**: `true-batch` and `accumulated`
- **Seeds**: 1, 2, and 3
- **Primary metric**: mean paired final-validation-loss difference
- **Revision**: `synthetic-code-v1`
- **Key command**: `python3 scripts/simulate.py --condition <condition> --seed <seed>`

## Estimands

### E1 Mean paired loss difference

**Registration**: registered. The statistic is the mean paired
final-validation-loss difference across seeds 1 through 3; the threshold is
0.02; a mean at or above it fails P1.

### E2 Per-seed loss difference

**Registration**: registered. Every paired difference must be below 0.02; one
seed at or above it fails P2.

## Informed by

- [[EXP-001-accumulation-pilot]], whose registered E1 passed at seed 1. Seed 1
  is reused here, so E1 in this record is a replication at that seed and a
  fresh test at seeds 2 and 3.
- [[2026-08-12-accumulation-controls]]

## Preregistered predictions (a priori)

- **P1: Mean equivalence (E1)**: the mean paired difference is below 0.02.
- **P2: Seed consistency (E2)**: every paired difference is below 0.02.

## Decision rule (a priori)

- **If P1 and P2 hold**: support a synthetic-scale equivalence finding.
- **Otherwise**: keep RQ1 open and report the failing seeds.

## Decisions

- **2026-08-14** — Kept the 0.02 margin rather than tightening it to 0.01 after
  [[EXP-001-accumulation-pilot]] came in at 0.004: a margin chosen after seeing
  the pilot would depend on the result it is meant to judge. Costs sensitivity
  to differences between 0.01 and 0.02. Source: pilot-gate review.
- **2026-08-14** — Reused seed 1 rather than drawing seeds 4 to 6: the paired
  comparison stays anchored to the pilot. Costs one fresh seed; E1 is a
  replication at seed 1 and a fresh test only at seeds 2 and 3. Source:
  pilot-gate review.

## Human review

- **Design**: paired-seed comparison approved after the pilot gate.
- **Preregistration**: predictions and threshold approved before the run.
- **Analysis and interpretation**: results, limitations, and proposed finding
  reviewed before synthesis.

## Runs

| Backend | Job ID | Description | Status | Artifacts |
|---|---|---|---|---|
| Slurm | 48161 | Both conditions at seeds 1 through 3 | completed | `results/EXP-002/48161/metrics.json` |

## Results

| Seed | True batch | Accumulated | Paired difference |
|---|---:|---:|---:|
| 1 | 0.799 | 0.803 | 0.004 |
| 2 | 0.803 | 0.807 | 0.004 |
| 3 | 0.796 | 0.800 | 0.004 |

The mean paired difference was 0.004.

### Outcomes against preregistered predictions

| Prediction | Verdict | Predicted | Observed |
|---|---|---|---|
| P1 | confirmed | Mean difference < 0.02 | 0.004 |
| P2 | confirmed | Every difference < 0.02 | All three were 0.004 |

## Conclusion

Both preregistered equivalence checks pass within the deterministic simulator.
The design does not test optimizer state, floating-point order, or a real model.

## Follow-ups

- [x] Synthesize the pilot and comparison in a finding.

## Artifacts

- `results/EXP-002/48161/metrics.json`, fictional artifact at revision `synthetic-code-v1`

## Findings

- [[2026-08-16-accumulation-matches-large-batch]]
