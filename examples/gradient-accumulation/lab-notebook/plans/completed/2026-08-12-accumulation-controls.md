---
status: completed
summary: Test synthetic gradient accumulation against true large batches
next_action: none
owner: example maintainer
reviewer: example reader
current_phase: Closed
created: 2026-08-12
updated: 2026-08-16
---

# Accumulation controls

## Objective

Determine whether the synthetic accumulated condition stays within 0.02 final
validation loss of the true-batch condition.

## Existing evidence

RQ1 was open when this plan was created. No result had been observed.

## Phases

### Phase 1: Cheap validation

Run seed 1 in both conditions. Continue only if both results are finite and the
paired difference is below 0.02. Record [[EXP-001]].

### Phase 2: Three-seed comparison

Run seeds 1 through 3 in both conditions. Support the scoped claim only if the
mean and every paired difference are below 0.02. Record [[EXP-002]].

## Risks and controls

- The simulator is not a training system; keep every conclusion synthetic.
- Write predictions and gates before recording outputs.
- Use separate job IDs and ledger records for the two phases.

## Terminal conditions

- Complete when both phases pass and their evidence is durable.
- Block if an output is non-finite or an artifact cannot be verified.
- Abandon if the simulator cannot represent both conditions deterministically.

## Human review

- The plan and Phase 1 design were approved before execution.
- Phase 1 evidence was reviewed at the pilot gate before Phase 2 was approved.
- Phase 2 evidence and the terminal disposition were reviewed before closure.

## Decisions

- **2026-08-16** — Closed the plan as completed rather than adding a
  real-training phase after [[EXP-002-accumulation-comparison]] passed: the
  objective was scoped to the simulator. Forecloses any claim about real models
  from this plan; a replication would be a new plan. Source: closure review.

## Completion report

Completed on 2026-08-16. Both phases passed their preregistered gates.

| Goal | Outcome | Record |
|---|---|---|
| Phase 1 pilot is finite and inside the margin | met | [[EXP-001-accumulation-pilot]] |
| Phase 2 mean and per-seed differences stay inside the margin | met | [[EXP-002-accumulation-comparison]] |

Limitations: the simulator is deterministic and has no optimizer state, so the
result says nothing about floating-point order or a real model. No follow-up is
open; a real-training replication would be a new plan. Both jobs are processed
and their ledger records are listed under Evidence.

## Evidence

- [[EXP-001-accumulation-pilot]]
- [[EXP-002-accumulation-comparison]]
- [[2026-08-16-accumulation-matches-large-batch]]
- Ledger records `jobs/processed/slurm/48152.json` and `48161.json`
