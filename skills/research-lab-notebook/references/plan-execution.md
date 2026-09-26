# Plan execution and read-only review

Use a notebook plan to bound research work. Choose an execution mode when the
user authorizes execution, or a read-only activity when they want to understand
the plan or its existing evidence. Plan preview and results walkthrough work
with incomplete and completed plans.

Resolve the activity before execution, ownership, or notebook updates. If "go
through this plan" is ambiguous, ask whether the user wants a preview,
execution, or a results walkthrough. A read-only request never enters the
execution workflow or the notebook-writing steps.

## Invoke the installed skill

Name the installed skill, the plan path, and the activity or execution mode in
ordinary language. These are portable instructions, not standalone CLI flags.
An agent's optional skill-invocation syntax is separate from this contract.

> Use the installed research-lab-notebook skill to preview
> lab-notebook/plans/2026-09-01-controls.md. Explain the proposed designs,
> dependencies, controls, decision rules, costs, and uncertainties. Do not run
> anything or change the notebook.

> Use the installed research-lab-notebook skill to execute the authorized work
> in lab-notebook/plans/2026-09-01-controls.md locally in stepped mode. After
> each experiment, explain its original design before its findings, discuss
> the interpretation and next action, and wait for me to say proceed.

> Use the installed research-lab-notebook skill to execute the authorized work
> in lab-notebook/plans/2026-09-01-controls.md in narrated mode. Continue within
> its scope and budget without routine conversational pauses. Keep every
> scientific and human-approval gate.

> Use the installed research-lab-notebook skill for a results walkthrough of
> lab-notebook/plans/completed/2026-09-01-controls.md. Replay the existing
> experiments in dependency order, explaining each design before the observed
> results. Stop after each experiment until I say next. Do not run, retry,
> repair, recompute, or change any records.

For notebook-only reporting, request **unattended mode**. For a terminal report
instead of per-result chat, request **handoff mode**. Specify the authorized
phase, resources, budget, and stop boundary when the plan does not already
supply them. Naming a mode grants no additional permissions.

Local execution uses the project's documented local procedure. Remote or queued
execution uses its [runner contract](job-runners.md). The skill supplies
instructions; it does not install a scheduler or depend on private tooling,
hosts, messaging services, or a particular coding agent.

## Plan preview

A preview explains prospective work without executing it. Read the plan,
linked experiment designs, and retained evidence needed to explain:

- the objective, research questions, and current state;
- the experiment inventory and count, including planned work with no results;
- dependencies, phase boundaries, and the order in which work becomes eligible;
- each design, measured quantity, controls, predictions, and null criterion;
- decision rules, acceptance and stop conditions, and required human reviews;
- expected resources and costs, their assumptions, and unresolved uncertainties.

Distinguish proposed work from work already executed. For a completed plan,
explain its recorded design and terminal state without implying work remains
authorized. Disclose absent designs, cost estimates, or evidence rather than
filling them in as facts. A preview does not acquire execution ownership,
change statuses or `next_action`, launch jobs, or generate missing evidence.
Discuss retained cost estimates and discrepancies as part of the preview.
Do not reconcile accounting records, retrieve missing evidence through a new
job, or change approvals. Banking a proposed correction requires separate
write authorization.

## Execution modes

State the mode at the start. Default to **narrated** for an authorized execution
request that does not name one. The mode controls conversational reporting and
routine pauses; it does not change evidence processing or review requirements.
An explicit user choice overrides the plan or delegation prompt; their
explicit choice overrides the default. Delegates inherit the selected mode
and cannot relax it.

| Mode | Reporting and continuation |
|---|---|
| Narrated | Report each processed result and its interpretation, then continue eligible authorized work without asking routinely whether to proceed. |
| Stepped | After each EXP, present the original design and setup before the findings. Discuss interpretation and the proposed next action, then stop until the user explicitly says proceed. |
| Unattended | Record results, interpretation, decisions, and blockers in the notebook without routine chat reports. Stop at any unmet approval or other gate. |
| Handoff | Maintain the same notebook record while working; give a terminal report when the authorized work ends or stops at a boundary. |

Narrated, unattended, and handoff support continuous execution. **Autonomous**
here means continuing the explicitly authorized bounded plan. It removes only
routine conversational pauses. It never licenses an unsolicited or open-ended
research loop, scope expansion, new spending, destructive actions, publication,
or external writes. Notebook-only reporting does not suppress a required
permission request or safety notice.

Stepped mode adds a human checkpoint after every experiment, even within a
phase. Do not prequeue the next experiment, submit a speculative successor, or
continue another branch while that checkpoint awaits a response. Multiple jobs
that constitute the current experiment may run within its approved design and
budget. A response authorizes only the next action within the existing scope;
it does not waive later gates.

## Execute the authorized scope

1. Read the plan, project instructions, relevant experiment records, and runner
   contract. Locate the current phase, dependencies, existing jobs, evidence,
   budget, and stop conditions. Resume from durable records without duplicating
   completed work or submissions.
2. Confirm the user's authorized scope and the required human decisions. Review
   the plan before execution, the experiment design before preregistration,
   and the preregistration before outcome inspection. An agent's own review is
   not human approval. If a required decision or permission is absent, stop at
   that boundary; a mode selection is not approval.
   Before each submission or retry, check the plan's spend authority and
   ledger ([Spend and units](spend.md#deriving-the-account)): the approved
   ceiling, incurred A, committed C, and the planned remainder U priced at a
   current rate. Headroom after commitments must still cover planned U; an underspend
   grants no new scope. Use a conservative admission bound for concurrent jobs
   and permitted retries, coordinate reservations against shared limits, and
   check which limits the runner actually enforces. Stop when exposure exceeds
   approval or material unknowns prevent bounding it. Preserve controls,
   uncertainty, and independent confirmation when proposing a cheaper design.
3. Execute only eligible work. Follow [Experiments](experiments.md) for
   registration, instrument checks, pilots, and run identity. Apply the
   predeclared decision rules to positive, null, and failed outcomes alike.
   Preserve the original design and predictions when the executed method
   deviates; record the deviation and its timing separately.
4. Process each result into durable evidence using the experiment workflow.
   Preserve raw artifacts, provenance, uncertainties, and limitations. Review
   analysis and interpretation before synthesis or publication use. A proposed
   follow-up, including one selected by a decision rule, requires the human
   approval specified by the notebook before submission.
   Capture per-attempt usage in the record and money in the spend ledger
   before the durable update and processed mark. Scientific processing can
   close with billing pending if its gaps and follow-up owner are recorded. A
   later bill is a ledger correction carrying the difference, not new spend.
5. Report according to the selected mode. In stepped mode, first explain the
   original rationale, setup, controls, predictions, and null criterion; then
   present observed results, deviations, interpretation, and the proposed next
   action. Stop until the user says proceed. Other modes continue only when all
   scientific, budget, scope, and human-approval gates permit it.
6. After each phase, record its evidence and proposed disposition and pause for
   the required human plan review. Do not cross a gated follow-up on the
   strength of continuous-mode authorization. Record the decision and resulting
   scope before resuming.
7. End at the authorized boundary or a plan stop condition. Follow
   [Plans](plans.md) for status, `next_action`, terminal reports, and evidence
   pointers. Account for running jobs and artifact durability; a conversational
   pause does not cancel a job or authorize leaving additional work running.
   Do not mark an unfinished plan completed merely because the session ended.
   Reconcile resources against the original baseline in units, and name
   remaining ledger commitments and pending settlement. Reduce a canceled job's
   remaining commitment only after confirmation; retain fees and billing
   unknowns. Carry revised assumptions into any proposed successor without
   launching it.

Every mode preserves the same scientific and permission boundaries. If work
cannot continue, record the exact blocker and the decision needed to resume.
Do not invent a rescue experiment or silently increase the budget.

## Results walkthrough (replay)

A **results walkthrough**, shortened to **walkthrough**, reviews existing
experiments and results. **Replay** is a natural-language synonym for this
same read-only activity, not an execution mode. A **rerun** performs new
computation and requires separate authorization.

Start by stating the inventory and count of experiments in scope, their
statuses, and which have retained results. Traverse them in dependency order;
use a stable order for independent experiments. Explain unresolved dependencies
or gaps rather than inventing a history. An incomplete plan is still useful
for review: distinguish completed evidence, partial evidence, and work that
never ran.

For each experiment:

1. **Reconstruct the contemporaneous design before showing results.** Explain
   the question and rationale, inputs, setup, controls, intended measurement,
   recorded predictions, and null criterion or decision rule. Cite the retained
   record or artifact. If no contemporaneous prediction survives, say so; do
   not manufacture preregistration from the eventual outcome.
2. **Explain the executed method and observed evidence.** Describe deviations
   from the intended design, retained results, uncertainty, and the recorded
   decision-rule outcome. Keep intended design, executed method, and
   retrospective understanding distinct. State when evidence is missing or
   cannot support the recorded conclusion.
3. **Discuss interpretation and limitations.** Identify design defects, what
   they prevent the result from establishing, and when they were or could have
   been detected. Distinguish recorded detection timing from retrospective
   judgment. Propose repairs or follow-ups as proposals, with their costs and
   uncertainties; proposing a repair does not authorize implementing it.
4. **Stop after this experiment.** Invite discussion and wait until the user
   says next before continuing. Do not bypass this pause by reviewing another
   branch in parallel.

Use retained records and artifacts only. Never launch, retry, rerun, repair a
script, or recompute a measurement to make the walkthrough more complete.
Missing evidence remains a disclosed gap. Do not acquire execution ownership,
mark jobs processed, change plan or experiment state, or bank review corrections
unless the user separately authorizes those writes. Authorized corrections
must preserve the original record and must not retrofit preregistration.
Existing costs and accounting discrepancies may be discussed in a walkthrough.
Reconciliation writes and billing corrections require separate authorization,
just as scientific corrections do.

If the user explicitly requests **run-then-replay**, execute in a named
execution mode first, within all existing gates. Then enter the read-only
results walkthrough, state the available inventory, and pause after each
experiment. A walkthrough or replay request alone never authorizes the run.
