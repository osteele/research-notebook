# Experiments

## Identity and lifecycle

Use stable IDs such as `EXP-001` or a project-specific ID such as `ACC-E1`.
IDs match `^[A-Z][A-Z0-9]*-[A-Z0-9]+$`, remain unique, and are recoverable
from the filename and first heading.

Canonical statuses:

| Status | Meaning |
|---|---|
| `proposed` | An idea exists; design is incomplete. |
| `planned` | Method and implementation are ready; no job is queued. |
| `queued` | Submitted but not running. |
| `running` | Executing now. |
| `in-progress` | Active work that is not queue-shaped. |
| `pilot-complete` | A bounded pilot finished; the full run awaits a decision. |
| `blocked` | Stopped, waiting on something named in the status line: a dependency, a dataset, another experiment. Someone intends to continue, and design is not the obstacle. |
| `completed` | Runs finished and results are documented. |
| `abandoned` | Stopped early; the reason is documented. |

Common path:

```text
proposed -> planned -> queued -> running -> pilot-complete -> completed
```

`abandoned` is a valid exit from any state. Skip `pilot-complete` when no pilot
gate exists.

### Writing the status line

Write `**Status**: completed`, with the colon outside the bold markers. A
qualifier may follow in parentheses: `completed (2026-05-29)`,
`pilot-complete (seed 42)`, `queued (full sweep)`. The token before the
parenthesis is what tools read.

The vocabulary is data. `notebook-schema.json` lists the canonical statuses,
the accepted legacy spellings, and the rejected ones, and the validator reads
that file rather than this prose.

- `complete`, `done`, `cancelled`, and `canceled` are accepted as legacy
  spellings and reported as warnings. New and edited records use the canonical
  token.
- `closed` is rejected. In practice it means `abandoned` in about half of the
  records that use it (stopped at a failed gate, no science run) and
  `completed` in the rest. Say which one applies.

### Duplicate IDs

Two experiments sharing one number is common in a long-running notebook. The
remedy depends on whether each side has run.

| Situation | Remedy |
|---|---|
| One side never ran (no jobs, no artifacts) | Renumber that side to the next free number above the notebook's maximum. |
| One side is a follow-up of the other: a pilot, a re-analysis of its output, the full-scale run of its pilot | Give it a revision-letter suffix (`EXP-045b`). It is not a separate experiment. |
| The same experiment was filed twice (a design stub beside the executed record) | Merge into the record that has results. |
| Both sides ran | Renumber one side and retag its jobs together. Keep both numbers, with a banner, only when the retagging cost is high enough to deserve an explicit decision. |

Renumber and retag together. An experiment ID is also a job tag, a script
name, and an output-directory path. A shared tag is visibly ambiguous: the ID
resolves to two candidate files. Renumbering without retagging makes it resolve
silently to one file and misattributes the moved line's jobs, which is worse
than the collision.

Count jobs before deciding. Grepping the experiment file for job IDs counts
mentions, not jobs; use the runner's own listing filtered by tag and project.
Where an artifact already exists on disk under the old number, leave the
filename alone, move only the notebook ID, and record the mismatch in the
experiment header.

A banner, when used, names the other line, the true job count, what each side
owns, and which inbound references mean which. Papers may not cite notebook
experiment numbers or job IDs, so no published paper can pin an ID. When a
banner names an ID that later moves, edit every file carrying that banner;
banner prose is not a link, and the validator cannot catch it.

### Analysis annexes

Breakdown tables that support an experiment's headline (per-subject residuals,
pattern counts, worked example cases) go in a sibling file that keeps the
experiment's ID and adds `.annex.md`:

```text
EXP-042-verifier-gap.md         the argument
EXP-042-verifier-gap.annex.md   the rows behind it
```

The ID in the filename is the join. An annex is not an experiment: it declares
no status, is not listed in the experiment index, and the validator only checks
that its ID belongs to an existing record. Split when the breakdown would crowd
out the argument, say in the experiment's `Results` that the annex exists, and
open the annex with what the breakdown shows.

## Estimands and registration

An experiment record names each quantity it measures as an **estimand**, with a
machine-readable registration status. The grammar:

```markdown
### E1 Short name of the quantity

**Registration**: registered | found | gate. One clause saying what was fixed.
```

- The heading matches `^#{2,4}\s+E\d+\b`. Numbering is per record and stable
  once cited.
- The `**Registration**:` line is the first such line after the heading and is
  required.
- The value must be one of three. An unrecognized value is an error.

| Value | Meaning |
|---|---|
| `registered` | The statistic, the expected direction, and the label every outcome reaches were fixed before the data existed. |
| `found` | Nothing was fixed in advance. A claim drawing on it is a found result. Confirmatory use needs a fresh registered run, not a re-read of the same data. |
| `gate` | A precondition on interpreting another estimand: a headroom check, an instrument-health check. It is not a result to cite on its own. |

One record usually carries more than one value. An arm registered in advance
can go void while an arm that existed only as a gate produces the run's most
useful number. A single status for the whole record cannot express that, which
is why the status attaches to the estimand. A record that declares no estimands
is not flagged; the check applies to declared estimands only.

`CLAIMS.md` cites `EXP-NNN:E#` rather than the whole record. The validator
resolves the reference and warns when a claim draws on a `found` estimand or
on a `gate`.

### Record what informed the design

Add an `## Informed by` section at design time and again at each amendment.
List what was read or measured before the design was fixed, as links to
questions, plans, experiments, and findings. Say explicitly where a previous
run's unregistered facet is among them. That is the case that makes a later
confirmatory claim on the same data circular, and nothing else in the notebook
records it.

Every other fact about an experiment is recoverable later: provenance from the
artifact, replication breadth by counting cells, the job from the runner. What
the designer had already seen when the design was fixed exists only at the
write moment. A threshold chosen before looking and one chosen after produce
byte-identical code and output.

The validator checks that every link in this section resolves to a notebook
file. Research question IDs such as `[[RQ1]]` are exempt because questions
live inside `QUESTIONS.md`.

### Record design decisions

The design sections are amended in place during review, so they show the option
chosen and lose the one that was not. Arm order, the comparator, a threshold,
the decision rule's branches: these are the choices reviewers most often
contest, and without a log the alternative leaves no trace. Keep them in a
`## Decisions` section with the same rules as a plan's
([Plans](plans.md#decisions)): name the option that lost, state what the choice
costs, cite what settled it, never edit an entry, and reverse a choice only with
a new one.

**An entry made after results were seen links what had been seen**, even when
it did not bear on the choice. `## Informed by` records what the designer had
seen before the design was fixed; a choice made after further results is where
preregistration weakens unnoticed, and the entry is the only place that records
it. A deviation of the executed method from the design is also an entry, dated
when it was decided.

**A decision rule is not a decision log.** `## Decision rule (a priori)` states,
before results, what each outcome will license; `## Decisions` records, after
the fact, a choice and the option that lost. Setting a threshold puts the
threshold in the rule and, when a credible alternative value was weighed, an
entry in the log saying which value lost and why. Applying the rule to a result
is not a decision and gets no entry. Changing the rule after results exist is
both: amend the rule, and log the change with what had been seen. Write the
heading exactly `## Decisions`; the validator reads only that heading, and a
list of rules or actions under it is not a log.

## Experiment template

```markdown
# EXP-001: Short title

**Created**: YYYY-MM-DD
**Status**: proposed
**Research questions**: [[RQ1]]

## Hypothesis

A specific, falsifiable claim.

## Method

- **Instrument**: Model, apparatus, population, or system under test
- **Data**: Dataset, sampling, and preprocessing
- **Conditions**: Treatments, baselines, and controls
- **Metrics**: Primary and secondary outcomes
- **Script**: `scripts/exp_001.py`
- **Revision**: Commit or content identifier
- **Key command**: Minimal replication command

## Estimands

### E1 Primary quantity

**Registration**: registered. Statistic, direction, and threshold fixed on YYYY-MM-DD.

### E2 Instrument headroom

**Registration**: gate. Read E1 only if this check passes.

## Informed by

- [[RQ1]]
- [[EXP-000-earlier-pilot]], including its unregistered per-seed spread

## Preregistered predictions (a priori)

- **P1: Primary metric (E1)**: predicted range; reasoning; null condition.

## Decision rule (a priori)

- **If outcome A**: next action and rationale.
- **If outcome B**: diagnostic or stop condition.

## Decisions

- **YYYY-MM-DD** — Choice rather than the option that lost: why. Costs or
  forecloses what. Source: review, owner, or tracked decision.

## Runs

| Backend | Job ID | Description | Status | Artifacts |
|---|---|---|---|---|

## Results

Observed values, uncertainty, effect sizes, and checks.

### Outcomes against preregistered predictions

| Prediction | Verdict | Predicted | Observed |
|---|---|---|---|
| P1 | confirmed / partial / refuted / null-confirmed / not-tested | ... | ... |

## Conclusion

Interpretation, scope, and threats to validity.

## Follow-ups

- [ ] A concrete next test caused by the result

## Artifacts

- Output path or URI, content hash, and retrieval date

## Findings

Links only to syntheses that use more than this experiment.
```

## Resources

Keep per-attempt resource evidence beside `## Runs`, optionally under
`## Resources`. Record units, never money: compute quantity and device, elapsed
time, calls and tokens, and retained bytes. Money for each attempt is a row in
`plans/spend/LEDGER.md`, keyed by the same attempt identity; ceilings are in
`plans/spend/AUTHORITY.json`. See [Spend and units](spend.md). This is a
human-readable recording pattern, not a new required heading, Runs column, or
parsed schema.

Key evidence by the existing Backend + Job ID pair. Give manual runs a stable
attempt identity and retain it with their command and output location. Each
retry is a separate attempt linked to the failed one, including retries hidden
inside a backend's parent job. Where the source cannot separate attempts,
record that limitation and the parent total without inventing a split.

For each attempt, record the available quantities and their units, the source
identity or retained artifact, and the retrieval timestamp. State the time
interval so a later usage report can be matched to the same attempt. A process
duration is not necessarily a provisioned-resource duration. Include failed,
canceled, and partial attempts, setup, and idle time. Record unknown usage as
unknown, with the reason and the next retrieval check; a missing source is not
evidence of zero use. Follow the source mapping in
[RUNNER.md](job-runners.md#usage-and-billing-sources) rather than inferring
usage from job status alone.

Preserve corrections as dated history, stating which prior figure the new
evidence supersedes. A record that names its job ids loses nothing by omitting
their cost: the runner or provider holds the charge per job, and the ledger
holds it per plan.

## Before running

1. Reserve the next ID using the project's coordination mechanism, if any.
2. Write the method, primary outcomes, controls, and instrument checks.
3. Name each estimand and its registration value, and record what informed the
   design.
4. Pause for human review of the experiment design.
5. Write the predictions and decision rule, then pause for human review of the
   preregistration before inspecting outcomes.
6. Validate the manipulation or instrument on the cheapest sufficient test.
7. Run a bounded pilot when scale, cost, or failure risk warrants one.
8. Tag every job with the experiment ID.

## Processing a result

A finished process is not a finished experiment. The process is finished when
it exits. The experiment is finished when its artifacts are validated, its
record is written, and its decision rule has been applied. The obligations are
the same for a cluster job, a remote one-liner, and a script run on a laptop;
only the durability step differs.

1. **Validate the artifact and the instrument.** Confirm the run produced what
   it claims, the numbers span a plausible range, the manipulation shows the
   effect it was supposed to show, and varying the key parameter changes
   something. A run that completed and returned numbers can still be
   uninterpretable.
2. **Record the result in the experiment record.** Analyze primary outcomes
   before exploration. Compare every prediction with its observed value, note
   anomalies and missing checks, and write the conclusion at the tested scope.
3. **Apply the predeclared decision rule.** Failed and null results go through
   it too. Do not launch an unregistered rescue campaign.
4. **Pause for human review** of the analysis, interpretation, and any proposed
   follow-up branch. Then update question, status, index, priority, claim, and
   publication pointers that the result changes.
5. **Capture resource evidence.** Follow
   [Resources](#resources) for every attempt, including failed
   and partial runs. Link the sources and retrieval time, distinguish estimates
   from bills, and update the owning plan's as-of forecast when authorized.
   Record missing evidence and its follow-up owner; delayed billing does not
   prevent scientific processing from completing.
6. **Secure the durable copy.** This is the step that differs by substrate:

   | Substrate | Durable copy | What the step is |
   |---|---|---|
   | Job backend with retained artifacts | The job-keyed copy on the backend or in its artifact store | Retrieve and verify outputs, validate the notebook, commit, then mark the job processed last |
   | A persistent host reached by hand | The file on that host | Retrieve it, or record where it lives and that it is unsynced |
   | A run on the local machine | The local output is the only copy | Record the numbers before anything can overwrite them |

   The local row is the one that bites. Get the result into the experiment
   record before the next run of the same script, and treat "I can rerun it"
   as false whenever the run was expensive, stochastic without a pinned seed,
   or dependent on state that has since changed. A local run has no processed
   flag; the experiment record's status is its equivalent.

7. **Report** according to the [execution mode](plan-execution.md#execution-modes):
   narrated (default) reports each result without a routine pause; stepped
   presents design and setup before findings after each EXP, discusses the
   next action, and stops until the user says proceed; unattended reports in
   the notebook; handoff gives a terminal report. Name the mode at the start.
   Every mode retains the human-review gates above. Results walkthrough
   (replay) is a separate read-only review of retained evidence, not a reporting
   mode that launches or processes jobs.

Processing must be idempotent. If the job is already processed, verify the
linked notebook evidence rather than adding a second entry. Failed jobs can be
processed after their failure mode and useful partial artifacts are recorded.
