# Plans

A plan is a version-controlled contract for one bounded research objective. It
records scope, dependencies, decisions, handoffs, review gates, and exit
conditions across experiments, agents, harnesses, and sessions. Use `plans/`
when several experiments or phases serve that objective.

Use [Plan execution and read-only review](plan-execution.md) to preview a plan,
execute it in narrated, stepped, unattended, or handoff mode, or conduct a
results walkthrough (replay) of existing experiments. Preview and walkthrough
work on incomplete or completed plans without launching jobs, taking execution
ownership, or changing the records.

## Plans persist across sessions

A notebook plan preserves the research contract in version control. One agent
can draft it, a researcher can review it, another agent or harness can execute
an authorized phase, and a later agent can close it. Every participant reads
the same objective, evidence, dependencies, gates, risks, and terminal
conditions.

Claude Code and Codex planning surfaces organize and approve an agent's current
task. Use them to reason about creating or executing the notebook plan. Keep the
research contract in the plan file so it remains available across context
resets, products, collaborators, and sessions.

Plans are appropriate when at least one of these is true:

- the objective spans several experiments or decision-gated phases;
- creation, execution, and review may belong to different people or agents;
- work must resume after the current session or context window;
- a scheduler, CI job, or harness needs a stable machine-readable `next_action`;
- stopping, cost, or evidence gates must remain visible before execution.

## Frontmatter

```yaml
---
status: draft
summary: Determine whether the effect survives two control families
next_action: Design the first pilot
owner: researcher
reviewer: collaborator
current_phase: Phase 1
created: YYYY-MM-DD
updated: YYYY-MM-DD
---
```

Required fields are `status`, `summary`, `next_action`, `created`, and `updated`.
Optional fields are `owner`, `reviewer`, and `current_phase`. Use `current_phase`
for active and blocked plans so a new executor can locate the live gate without
reconstructing the plan.

Statuses are `draft`, `active`, `blocked`, `gated`, `backlog`, `superseded`,
`completed`, and `abandoned`. Use a filename of the form
`YYYY-MM-DD-lowercase-topic.md`, where the date is the creation date. Active
plans live directly under `plans/`. Other plans live in the subdirectory named
for their status. `complete` (with a `plans/complete/` directory) and
`proposed` are accepted as legacy spellings of `completed` and `draft`, with a
warning.

Status-specific fields preserve why work is waiting or ended:

| Status | Required metadata |
|---|---|
| `gated` | `gate` and either `revisit_when` or `promote_when` |
| `backlog` | Either `revisit_when` or `promote_when` |
| `superseded` | `superseded_by` |
| `abandoned` | `abandoned_because` |

A gate is a testable external blocker: data, compute, a dependency, a
collaborator decision. "The user decides to run it" is not a gate. A plan that
is viable and waiting for someone to start it is `backlog` with a revisit
cadence.

`next_action` is a handoff pointer, not a task queue. Keep it bounded and update
it only after the owning phase's evidence and disposition are durable. It must
be non-empty for a nonterminal plan. Set it to an empty value, `none`, or
`null` when the status is `superseded`, `completed`, or `abandoned`.

### Completed versus abandoned

The distinction turns on whether the work was done, not on whether the answer
was welcome. A plan that ran its course and returned a negative result is
`completed`: the campaign answered its question, and the answer was no. A plan
whose own negative gate fired as designed is the clearest case, since the gate
firing is the experiment working. Reserve `abandoned` for plans that never got
their answer: the premise changed, the question stopped mattering, or the work
was judged not worth doing.

Filing a completed negative as `abandoned` has a cost. It reads to the next
person as "this was a mistake" rather than "this question is settled", so the
direction gets re-proposed by someone who cannot tell it was already closed by
evidence. Negative results are results; file them where they will be found.

## Body

```markdown
# Plan title

## Objective

A falsifiable outcome and the decision it informs.

## Existing evidence

Links to questions, experiments, findings, and claims.

## Phases

### Phase 1: Cheap validation

- Inputs and dependencies
- Bounded work
- Acceptance and stop conditions
- Expected notebook updates

### Phase 2: Full measurement

Created only after Phase 1 passes its gate.

## Risks and controls

Scientific, operational, cost, and data-loss risks.

## Terminal conditions

- Completed when ...
- Blocked when ...
- Abandoned when ...
```

Every plan requires `Objective`, `Existing evidence`, `Phases`, `Risks and
controls`, and `Terminal conditions`. Terminal plans add closing sections: a
completed plan carries a completion report and `## Evidence`; a superseded or
abandoned plan carries `## Disposition` and `## Evidence`.

```markdown
## Disposition

Why the plan ended and which terminal condition applied.

## Evidence

Links to the experiments, findings, claims, and revisions that support closure.
```

## Resources and spend

A plan states its resource estimate in units and names its packages and their
experiments. It carries no money: no ceiling, allocation, rate, or spend figure.
Spend authority, including the plan's ceiling, any package allocations, and
their dated history, is recorded in `plans/spend/AUTHORITY.json` under the
plan's filename stem, and money per attempt in `plans/spend/LEDGER.md`. See
[Spend and units](spend.md) for the formats and the
[cost guide](https://research-notebook.osteele.com/guide/costs/) for a worked
campaign.

Choose the cheapest instrument sufficient for the scientific decision. Compare
analysis of existing data, an instrument check, a bounded pilot, a full
measurement, and independent confirmation. Record what each option can resolve
and why cheaper options are insufficient. Preserve necessary controls, valid
uncertainty, and independent confirmation. A pilot that checks the instrument
does not become evidence for a claim beyond its design.

Build the estimate from setup and data preparation, attempt counts, resource
quantities, and conditional branches. Include likely operational exposure such
as failed attempts, retries, provisioning, idle time, storage, and transfer when
they are in scope. Keep separate:

- compute quantity, with units such as GPU-hours and the device count;
- calls and tokens for provider APIs;
- elapsed time, including queueing and parallelism assumptions; and
- human effort, including setup, review, and result processing.

Explain uncertainty with ranges, bounded scenarios, or unknowns; use outcome
probabilities only when there is evidence for them. Conditional scientific
branches need explicit resource estimates and entry conditions, not invented
expected-value probabilities. A projection across providers or devices keeps
the configuration each option needs and leaves the rate to the spend files.

Record the dated baseline estimate, the retry policy, and which branches are
authorized. Contingency is capacity inside the approved ceiling, recorded as an
allocation in the authority file; it is not spent and is not added again to the
forecast. Keep it distinct from the statistical
[confirmation reserve](#confirmation-reserve): holding back evidence protects
inference, whereas holding back money covers financial uncertainty. Budget room
cannot replace either scientific or human-review gates, and a larger ceiling
does not authorize a different study.

Before admitting work, check headroom as [Spend and units](spend.md#deriving-the-account)
derives it, using a conservative bound for concurrent attempts and permitted
retries. Coordinate reservations so separate agents cannot each spend the same
headroom. A documented runner limit is a safeguard only if the runner actually
enforces it. If credible exposure exceeds the approved ceiling, or a material
unknown prevents bounding it, stop for a decision on scope, resources, or
budget. See [execution preflight](plan-execution.md#execute-the-authorized-scope).

At closure, compare the resources used with the baseline estimate in units and
explain the variance. The ledger holds the money; name any pending charges and
the owner of their follow-up. A scientifically completed plan can have
financial settlement pending; say both. Carry lessons about rates, idle time,
and retries into successor estimates without authorizing successor jobs.

## Confirmation reserve

A plan that will end in a confirmatory claim carries a `## Confirmation
reserve` section, written at plan creation and before any exploration. It
names the evidence the plan is holding back and the rule that will judge it:

```markdown
## Confirmation reserve

**Held back:** seeds 7 and 11; eval tasks 40 to 60 of the held-out split

**Decision rule:** accept if reserve accuracy beats the baseline by more
than 2pp on the preregistered metric
```

Both markers are required, and the validator rejects a section carrying only
one. A reserve that names what is held back but not how it will be judged
leaves the rule to be written once the numbers are known, which is the failure
the reserve exists to prevent.

This is the one plan record that cannot be written later. Everything else in a
plan can be reconstructed from evidence that already exists; a reserve created
after exploration is not a reserve. Commit the section as soon as it exists so
version control fixes its date. Omit the section for plans that make no
confirmatory claim; an empty declaration is not a declaration.

## Decisions

Plans are edited in place during review and execution, so the plan body shows
the option that was chosen and loses the one that was not. A `## Decisions`
section keeps the choice: one entry per choice among credible options, dated,
newest last.

```markdown
## Decisions

- **2026-09-01** — Ran Phase 1 on one seed rather than three: the gate only
  needs to show the instrument works. Costs a weaker headroom estimate.
  Source: design review.
- **2026-09-12** — After [[EXP-004-headroom-pilot]] showed a ceiling effect,
  dropped the large-batch arm rather than adding seeds. Forecloses the
  scaling claim for this plan. Source: owner instruction.
```

Each entry states the choice, the option that lost, why, what it costs or
forecloses, and what settled it: a review, an owner instruction, or a tracked
decision request. Two rules carry the weight:

- **Name the option that lost.** If no one with the same information could
  credibly have chosen otherwise, the change is an edit, not a decision, and
  gets no entry. A log of every edit stops being read.
- **Never edit an entry.** A reversal is a new entry that names the earlier
  one. The plan body is amended freely; the log is what lets a reader see what
  it used to say and why it changed.

A choice made after results exist links what had been seen, the plan-level
counterpart of an experiment's `## Informed by`. A choice that changes one
experiment's design belongs in that experiment's record. Omit the section until
the first decision. The validator checks that entries are dated, run newest
last, and link to notebook files that exist.

## Completion report

A plan that reaches `completed` carries a `## Completion report` section,
written by the executing session before the terminal status is set. It is the
persisted form of the final handoff, so the summary survives the session. It
states:

- the terminal disposition and the evidence that caused it;
- per-goal outcomes (met, unmet, void), each linking the experiment or finding
  that carries the result;
- limitations and instrument caveats worth a future reader's attention;
- follow-ups left on the table, naming the successor plan when one exists;
- job and artifact status at closure;
- a link to the resource reconciliation against the baseline, when resources are
  tracked, including any pending settlement and its follow-up owner.

Canonical numbers and interpretation still live in `experiments/` and
`findings/`; the report links them rather than restating them. A terminal
plan's report may run to a page, because it is the record a later reader uses
to decide whether the question is settled.

Write the heading exactly as `## Completion report`. Notebooks that predate
the convention record the same thing under other names, and the validator
recognizes those rather than requiring a rename: `Completion`, `Completion
note`, `Completion audit`, `Outcome`, `Execution outcome`, `Execution result`,
`Closed`, and `Disposition`. Matching is on the exact heading, case
insensitively, never on a keyword. `## Completion gates` and `## Outcome tree`
are prospective sections that belong in an open plan, and one word separates
them from their retrospective counterparts.

Do not rename an old heading into the prescribed spelling to make it match.
The rename asserts that the section states a terminal disposition, per-goal
outcomes, caveats, and follow-ups, which is a claim about text nobody has
re-read. Recognizing the heading costs nothing and claims nothing.

Do not compose findings the plan does not record. Where the recorded outcome
is too thin to promote into a report, inventory the plan for a decision
instead: abandon the follow-up, move the plan back from `completed`, or write
the report from the records it names, one plan at a time.

## Retraction notices on terminal plans

A completed plan is terminal, but the experiments it cites are not. When an
experiment record later corrects a result the plan stated as its outcome, the
plan keeps asserting the superseded value to every future reader. Nothing in
the frontmatter marks it, since `superseded_by` is for a plan replaced by
another plan.

Record a retraction notice directly beneath the affected passage, leaving the
original text untouched:

```markdown
> **Retracted YYYY-MM-DD.** EXP-NNN supersedes the figures above: mean 0.996,
> range 0.009 (was mean 0.987, range 0.031). The narrow-spread reading is
> withdrawn. Applied YYYY-MM-DD.
```

Four rules:

- **Annotate, never rewrite.** The original claim stays verbatim. Editing the
  numbers out destroys the record of what was believed and when.
- **Point, do not restate.** Corrected values and citations only. A notice that
  paraphrases the correction becomes a second claim to verify.
- **Apply, do not assume.** Write the notice when a correction is acted on,
  not when it is reported. A review finding can be wrong.
- **State the superseded values, then sweep.** The experiment that retracts
  writes the new value beside the old one, and the same session searches the
  notebook for the superseded values and the experiment ID, annotating whatever
  it finds.

Notebook edges point forward: a plan names its experiments, and a search for
the experiment ID is the computed reverse. At the moment a correction is
recorded, nothing asks who relied on the old value unless the sweep does.

## Execution boundary

A plan records intent and approved scope. An agent or harness may carry out only
the phase or actions the user authorized. Expensive, destructive, privileged,
publication, and external actions require their own authority. Keep
`next_action` bounded. Continuous or autonomous execution means following the
explicitly authorized bounded plan without routine conversational pauses; it
does not permit unsolicited or open-ended research loops.

Pause for human review before changing a draft plan to active. After each phase,
write its evidence and proposed disposition, then pause again. The reviewer
chooses whether to continue, revise, move the plan to `gated` or `backlog`, or
close it. A gated follow-up requires another explicit review before execution.
Record the gate and the condition that permits reconsideration.

The [execution mode](plan-execution.md#execution-modes) never removes these
human-review gates. Stepped mode adds a stop after every experiment: explain
the original design and setup before findings, discuss interpretation and the
next action, then wait for the user to say proceed. Do not prequeue another
experiment or bypass the stop through parallel branches.

When handing a phase to another agent or harness, pass the plan path and phase
name rather than copying its instructions into a prompt. The executor records
job IDs and outputs in experiment files, updates the plan's status and
`next_action`, and leaves scientific conclusions in experiments or findings.
The plan coordinates evidence production. Experiments and findings own the
evidence.

When the plan reaches a terminal state, write the completion report or
disposition and the evidence, update indexes and pointers, then remove it from
active queues.

Regenerate and validate the plan index with:

```bash
python3 <skill-directory>/scripts/validate-notebook.py <notebook> \
  --write-plan-index --strict
```

Use `--format json` when a dashboard, editor, or external research tool consumes
diagnostics. This interface is the integration boundary. The notebook format
remains application-independent.
