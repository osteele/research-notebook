---
name: research-lab-notebook
description: Set up and operate a durable, file-based research lab notebook with questions, priorities, experiments, registered estimands, preregistered predictions, job results, findings, plans, claims, and publication tracking. Use when creating or adapting a lab-notebook/ directory, editing its records, registering or processing experiments, estimating or reconciling research costs, previewing or executing an authorized bounded plan, walking through or replaying existing results without execution, connecting a local process or job system such as Dagu, Pueue, SkyPilot, Slurm, or Weft, or handing research work across agents and sessions.
---

# Research lab notebook

Treat the notebook as the durable research record. Job logs, chat history, and
metric dashboards are inputs, not substitutes. Existing notebook files are
records, not format specifications.

## Route the task

Read the matching reference before acting:

| Task | Read |
|---|---|
| Create or adopt a notebook | [Setup](references/setup.md), [Notebook structure](references/notebook-structure.md), and [Project instructions](references/project-instructions.md) |
| Decide where information belongs | [Notebook discipline](references/notebook-discipline.md) |
| Trace provenance across files, or decide where a new cross-reference belongs | [Notebook graph](references/notebook-graph.md) |
| Edit STATUS, QUESTIONS, GLOSSARY, BIBLIOGRAPHY, PRIORITIES, CHANGELOG, or indexes | [Notebook files](references/notebook-files.md) |
| Register an experiment, name its estimands, or process a run (local or remote) | [Experiments](references/experiments.md) and [Job runners](references/job-runners.md) |
| Analyze results or state a conclusion | [Research methodology](references/research-methodology.md) |
| Write a cross-experiment synthesis | [Findings](references/findings.md) |
| Create, resume, or close a plan | [Plans](references/plans.md) |
| Estimate resources, record spend authority, or reconcile spending | [Spend and units](references/spend.md), [Plan resources and spend](references/plans.md#resources-and-spend), [Experiment resources](references/experiments.md#resources), and [Usage and billing sources](references/job-runners.md#usage-and-billing-sources) |
| Log an independent review, or consult gates before submitting | [Review ledger and gates](references/review-ledger.md) |
| Preview or execute a plan; walk through or replay existing results | [Plan execution and read-only review](references/plan-execution.md) |
| Curate claims or publication readiness | [Publication](references/publication.md) |
| Adapt a compute backend | [Runner adapters](references/runner-adapters.md) and, when needed, [Processed-job ledger](references/processed-job-ledger.md) |

Route preview and results walkthrough requests before execution or notebook
updates. The writing steps below apply only when a write is authorized; a
read-only request does not acquire execution ownership or enter those steps.

## Before writing

1. Locate the notebook. Prefer `lab-notebook/` inside the project unless project
   instructions declare another path.
2. Read project instructions, `STATUS.md`, the relevant research question, and
   the authoritative record linked from the task.
3. Check whether the notebook has its own version-control boundary.
4. Preserve raw outputs. Record their job identity, code revision, parameters,
   provenance, location, and content hash when practical.
5. Write predictions and decision thresholds before inspecting outcomes. Never
   rewrite them after results are known.
6. Name each estimand with its registration value (`registered`, `found`, or
   `gate`) and record what informed the design. These two facts exist only at
   the design moment and cannot be recovered later.
7. When a plan or design changes by choosing between credible options, append
   a dated entry to its `## Decisions` log naming the option that lost. Edit the
   body freely; never edit an entry.

## Pause for human review

Treat these as decision gates, not courtesy notifications:

1. Review a plan before any phase executes.
2. Review experiment design before preregistration.
3. Review the preregistration before outcome inspection.
4. Review analysis and interpretation before synthesis or publication use.
5. Review the plan after each executed phase, especially before crossing a gate.
6. Approve a gated follow-up before submitting more work.
7. Review claim promotion before strengthening its status or scope.

An agent may prepare the materials for review. It must not record its own output
as human approval. Record the decision and resulting scope in the owning plan,
experiment, or claim update.

Execution modes govern routine reporting, not these gates. Use narrated mode
by default; stepped mode pauses after every EXP; unattended mode reports in the
notebook; handoff mode gives a terminal report. Continuous execution carries
out only the explicitly authorized bounded plan. It never waives human review,
scope, budget, or permissions.

Plan preview and results walkthrough (also called replay) are read-only
activities. Preview explains the proposed work. Walkthrough explains existing
experiments in dependency order, design before results, and stops after each
until the user says next. Neither launches work nor changes execution ownership
or notebook state. Missing evidence is disclosed, never regenerated. Use the
natural-language invocations in [Plan execution](references/plan-execution.md);
these activities are not standalone CLI commands.

## Place evidence once

- Keep one experiment's design, runs, results, and interpretation in its
  experiment file.
- Create a finding only when the conclusion depends on multiple experiments or
  evidence sources.
- Keep claims proportional to the tested instruments and scope.
- Update indexes and status pages with pointers instead of copied conclusions.
- Use a plan as a bounded research contract. Execution still requires the
  authority appropriate to each action.
- Keep estimates, approvals, and linked as-of rollups in plans; keep per-attempt
  cost evidence and corrections in experiments. Preserve unknown billing,
  count shared charges once, and never treat headroom as new scope approval.

## After writing

1. Update the relevant experiment or finding index and affected question,
   priority, claim, and publication pointers.
   When processing job results, capture available cost evidence and billing gaps
   before validation.
2. Add a changelog entry only for a result, decision, failure, consolidation, or
   publication milestone.
3. Run the bundled structural validator:

   ```bash
   python3 <skill-directory>/scripts/validate-notebook.py <project-or-notebook>
   ```

   Use `--strict` in automation to treat advisory warnings as failures.
   Use `--format json` when another tool consumes diagnostics. Add
   `--write-plan-index` to regenerate `plans/README.md` from frontmatter.

4. Make the update durable in the notebook's version-control boundary.
5. Mark a job processed only after its outputs are checked, the notebook update
   passes validation, and the durable write succeeds. Billing may remain
   pending with an explicit follow-up owner; processed is not financially
   settled. A local run has no processed flag and its output may be the only
   copy; record its numbers before anything can overwrite them.
6. When a value is corrected, state the superseded value beside the new one and
   search the notebook for both the old value and the experiment ID, so
   findings and terminal plans that relied on it get their pointer or
   retraction notice in the same session.

Stop at the user's requested boundary. Do not submit a real job, spend money,
publish, write externally, or start unattended execution without authorization.
