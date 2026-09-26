# Research Notebook System

Research Notebook is a system for managing research with coding agents. It
connects publication claims to the experiments that support them. A shared
Markdown record preserves the context needed to continue the work across
sessions.

The system records predictions and decision criteria before compute, then
places outcomes beside them. Claims cite their supporting experiments and
state the limits of the evidence.

This repository contains the notebook contracts, schemas, validator, starter
templates, and runnable examples. Portable [Agent Skills](https://agentskills.io)
teach coding agents to operate the same records across compute backends.

Start with the [guide](https://research-notebook.osteele.com/guide/) or consult
the [reference](https://research-notebook.osteele.com/reference/).
The current contract is defined by the
[notebook schema](skills/research-lab-notebook/references/notebook-schema.json).
Released versions and migration notes are in [CHANGELOG.md](CHANGELOG.md).

## Install

The [`skills` CLI](https://github.com/vercel-labs/skills) can install the
collection for Claude Code, Codex, Cursor, OpenCode, and many other agents:

Install the notebook skill into the current project:

```bash
npx skills add osteele/research-notebook --skill research-lab-notebook -y
```

List the available skills without installing them:

```bash
npx skills add osteele/research-notebook --list
```

Install globally for specific agents:

```bash
npx skills add osteele/research-notebook -g -a claude-code -a codex -y
```

Add the optional reference archiver too:

```bash
npx skills add osteele/research-notebook \
  --skill research-lab-notebook \
  --skill download-research-references \
  -y
```

The CLI uses a shared canonical copy when possible, so one update can serve
several agents. Project installs travel with the project configuration; global
installs are available across projects.

Try the notebook skill without installing it:

```bash
npx skills use osteele/research-notebook@research-lab-notebook
```

Maintain an installation with:

```bash
npx skills update research-lab-notebook
npx skills remove research-lab-notebook
```

Add `-g` to update or remove the global installation. Set
`DISABLE_TELEMETRY=1` if you do not want the CLI to send its anonymous install
telemetry. See the [`skills` CLI](https://github.com/vercel-labs/skills#readme)
for its current agent list and options.

### Manual installation

Clone the repository, then copy or symlink each directory under `skills/` into
your agent's skills directory. Common global locations include
`~/.claude/skills/` for Claude Code and `~/.codex/skills/` for Codex. Project
installs usually live under the corresponding hidden directory in the project.

Review any skill before installing it. Skills are instructions that an agent
may follow with your file, shell, and network permissions.

## Included skills

| Skill | Purpose |
|---|---|
| [`research-lab-notebook`](skills/research-lab-notebook/) | Creates, adapts, validates, and operates the notebook. It covers experiments, findings, plans, publication claims, and work launched through a local process, [Dagu](https://github.com/dagu-org/dagu), [Pueue](https://github.com/Nukesor/pueue), [SkyPilot](https://docs.skypilot.ai/), [Slurm](https://slurm.schedmd.com/), or [Weft](https://github.com/osteele/weft). |
| [`download-research-references`](skills/download-research-references/) | Archives open-access papers cited by a LaTeX or Typst draft into `references/` and maintains `BIBLIOGRAPHY.md`. |

After installation, ask your agent:

> Use $research-lab-notebook to add a research notebook to this project. Our
> jobs run through Slurm.

Some agents use `$research-lab-notebook` for explicit skill invocation. In an
agent without that syntax, say “Use the installed research-lab-notebook skill”
instead.

Substitute the system your project uses to launch long-running work. The skill
inspects how that system submits work, reports status and logs, retrieves
outputs, and records completed processing. It writes those project-specific
operations into a small adapter contract. When the system lacks durable,
queryable processing state, setup creates a ledger automatically. The prompt
does not need to mention the ledger.

## The notebook model

The core evidence path is deliberately small:

```text
research question
    -> experiment (hypothesis, method, predictions, runs, results)
    -> finding (only when evidence spans experiments)
    -> claim and publication plan
```

The baseline contains five top-level files and two directory indexes. The
claim ledger starts empty; add claims when evidence supports a paper-sized
argument. Add optional records when they have a current purpose.

| File | Question it answers | Add it when |
|---|---|---|
| `STATUS.md` | Where does the project stand now? | Baseline |
| `QUESTIONS.md` | What is known, open, or blocked? | Baseline |
| `PRIORITIES.md` | What should happen next? | Baseline |
| `CHANGELOG.md` | What was learned or decided, and when? | Baseline |
| `GLOSSARY.md` | What do project-specific terms, symbols, and acronyms mean? | Terminology needs a stable definition |
| `BIBLIOGRAPHY.md` | Which papers matter, what do they say, and how are they relevant? | Related work is being tracked or cited |
| `CLAIMS.md` | Which claims belong to each paper, what role do they play, and what supports them? | Baseline; initially empty |
| `PUBLICATION.md` | Where are the manuscript and packets, when were they synchronized, what blocks submission, and where might the paper go? | A paper enters active preparation |
| `COMPANION-DOCS.md` | Which reports, guides, presentations, or IP documents accompany the research? | Several non-paper artifacts need an index |
| `QA.md` | Which questions should a presentation be ready to answer? | Preparing a talk or defense |

The directories separate records with different lifecycles:

| Directory | Contents | Add it when |
|---|---|---|
| `experiments/` | One mutable record per experiment: prediction, method, runs, results, interpretation, and conclusion. | Baseline |
| `findings/` | Dated, immutable syntheses that integrate evidence across experiments. | Baseline; it may remain empty until evidence spans experiments |
| `plans/` | Versioned contracts for bounded, multi-step research objectives. | Work spans experiments, phases, agents, or sessions |
| `reports/` | Longer living analyses and their figures. | A synthesis is too large or too changeable for a finding |
| `papers/` | Content-canonical Typst manuscripts using Arkheion by default, plus one shared `references.bib`. | Drafting a paper inside the notebook |
| `references/` | Downloaded cited papers and source notes. PDFs are an ignored reading cache; tracked indexes and metadata may live beside them. | Archiving or annotating literature |
| `kb/` | Stable methodology, terminology, comparisons, and other reusable project knowledge. | Material should be maintained as reference, not evidence |
| `causal-models/` | Working mechanism hypotheses kept distinct from observed findings. | Several interventions inform one mechanism hypothesis |

The manuscript remains the natural-length source through arXiv revisions,
review, and publication. A venue submission packet is a constrained derivative
created only for a specific submission. It may omit manuscript content, but it
cannot add content absent from the manuscript. `PUBLICATION.md` records each
packet's state and `synced-as-of` date.

Each experiment keeps its a priori predictions next to observed outcomes, and
names each quantity it measures as an estimand whose registration status is
`registered`, `found`, or `gate`. A claim cites the estimand (`EXP-002:E1`),
so a claim resting on a found result is visibly a found result. The record
makes exploratory and confirmatory work distinguishable and gives later agent
sessions the decision context that would otherwise disappear.

### An example notebook

The repository includes a runnable [gradient-accumulation
example](examples/gradient-accumulation/) that asks whether accumulation
reproduces true large-batch training. Its record grows like this:

```text
QUESTIONS.md
  RQ1: Does accumulation preserve optimization behavior at fixed effective batch?

plans/completed/2026-08-12-accumulation-controls.md
  Phase 1: one cheap smoke test; continue only if loss curves are finite
  Phase 2: three seeds for true-batch and accumulated-batch conditions

experiments/EXP-001-accumulation-pilot.md
  E1 registered: loss difference at seed 1, threshold 0.02; E2 is a finiteness gate
  Prediction written before the run: final validation loss differs by < 0.02
  Run: slurm/48152; artifact: results/EXP-001/metrics.json

findings/2026-08-16-accumulation-matches-large-batch.md
  Synthesis across EXP-001 and EXP-002, with effect sizes and scope limits

plans/completed/2026-08-12-accumulation-controls.md
  Completion report: both goals met, limited to the deterministic simulator

CLAIMS.md
  C1 major, gradient-accumulation-note: cites EXP-001:E1, EXP-002:E1, EXP-002:E2
```

Each file owns one part of the argument. The plan coordinates the work, the
experiment preserves its prediction and result, the finding synthesizes direct
evidence, and the claim stays within the tested scale.

## Plans

A file under `plans/` is a version-controlled research plan. It coordinates one
bounded objective across experiments, phases, agents, or sessions. Claude Code
and Codex also provide planning interfaces for an agent's current task. The two
kinds of plan serve different time scales:

| Agent-native plan | `plans/*.md` notebook plan |
|---|---|
| Coordinates one agent task or conversation | Coordinates a research objective across experiments and phases |
| Optimized for the current agent's next actions | Readable by humans, other agents, CI, schedulers, or a custom harness |
| May end when the task or session ends | Survives context resets, agent changes, and many sessions |
| Tracks implementation steps | Tracks evidence, dependencies, gates, risks, stop conditions, and required notebook updates |
| Approval usually starts the current task | Never grants new authority for compute, destructive actions, publication, or external writes |

One agent can draft a plan, a researcher can approve its scope, a separate
agent or harness can execute one authorized phase, and a later agent can review
the evidence and resume at `next_action`. Version control preserves its status
and history across providers and sessions. Native planning modes remain useful
for creating or executing a notebook plan. See the [plan
specification](skills/research-lab-notebook/references/plans.md).

### Units and spend authority

Choose the cheapest instrument sufficient for the decision: existing-data
analysis, checks, a pilot, full measurement, or independent confirmation.
Preserve controls and valid uncertainty. The
[cost guide](https://research-notebook.osteele.com/guide/costs/) follows one
fictional campaign from estimate through final billing.

Experiment records and plans state resources in engineering units: GPU-hours
and device class, forward passes, calls and tokens, elapsed time, and the
Backend and Job ID of each attempt. Money has one home, `plans/spend/`.
`AUTHORITY.json` records each plan's approved ceiling, allocations, and their
history, keyed by plan filename stem so status moves cannot orphan it.
`LEDGER.md` records money per attempt, from which incurred, committed, and
remaining headroom are derived. Scripts receive their runtime caps in seconds
or calls and hold no currency. See
[Spend and units](skills/research-lab-notebook/references/spend.md).

Budget headroom grants no new scope or spending permission. Unknown charges
remain visible, and a later bill is a ledger correction carrying the difference
rather than new spend. Scientific processing can finish with billing pending
when the available evidence and follow-up owner are recorded.

### Independent review and gates

An optional `REVIEW-LEDGER.md` logs each requested review of a plan, design,
script, or result, including reviews that find nothing, with the reviewer's
relation to the author. Faults become gates: questions, each founded on a run
that failed that way, that are consulted before the next costly submission.
See [Review ledger and gates](skills/research-lab-notebook/references/review-ledger.md).

### Choose execution or read-only review

Use ordinary language to name the installed skill, plan path, and mode. For
example:

> Use the installed research-lab-notebook skill to execute the authorized work
> in lab-notebook/plans/2026-09-01-controls.md locally in stepped mode. After
> each EXP, explain its original design and setup before the findings, discuss
> interpretation and the next action, and stop until I say proceed.

> Use the installed research-lab-notebook skill for a results walkthrough of
> lab-notebook/plans/completed/2026-09-01-controls.md. Replay existing experiments
> in dependency order, design before results, and pause after each until I say
> next. Do not run anything or change the notebook.

Execution defaults to **narrated** mode: report each result and continue without
routine conversational pauses. **Stepped** pauses after every experiment,
**unattended** reports in the notebook, and **handoff** gives a terminal report.
Continuous execution means carrying out an explicitly authorized bounded plan.
Every mode preserves scientific, human-review, scope, budget, and permission
gates. Stepped execution does not prequeue the next experiment or continue a
parallel branch around its pause.

A **plan preview** explains proposed work, dependencies, controls, decision
rules, costs, and uncertainties without execution. A **results walkthrough**
(also called **replay**) reviews retained experiments and results; it never
launches, retries, repairs scripts, or recomputes measurements. Both work on
incomplete and completed plans. Missing evidence is disclosed, not regenerated.
Neither takes execution ownership nor changes notebook state unless the user
separately authorizes banking review corrections.

These are skill instructions, not standalone CLI flags or a bundled scheduler.
The [execution and review workflow](skills/research-lab-notebook/references/plan-execution.md)
defines the full contract and gives additional portable invocation examples.

## Running experiments

Research projects launch work on laptops, shared clusters, cloud services, and
workflow systems. The notebook needs the same small set of operations in each
case. It records the project-specific commands or procedures in `RUNNER.md`.
This mapping is called a runner adapter. It tells the agent how to:

1. submit a bounded job tagged with the experiment ID;
2. inspect status and logs;
3. retrieve immutable outputs and provenance;
4. cancel a job when authorized;
5. determine whether a completed job has been processed; and
6. mark processing complete only after notebook updates are durable.

`RUNNER.md` also maps supported usage and billing sources and their limitations.
Record available cost evidence and unresolved billing before the durable
update and processed mark. A processed job can still await financial settlement;
the [runner reference](skills/research-lab-notebook/references/job-runners.md#usage-and-billing-sources)
explains provenance, shared charges, and corrections.

### Runner comparison

| Runner | Best fit | What it manages | Separate processed ledger? |
|---|---|---|---|
| [Dagu](https://github.com/dagu-org/dagu) | Self-hosted workflows that run locally, through SSH, or on containers/Kubernetes | Scheduling, DAGs, retries, logs, notifications, and run history | Yes |
| [Pueue](https://github.com/Nukesor/pueue) | Persistent sequential or parallel commands on one machine | A durable command queue, groups, dependencies, status, and logs | Yes |
| [SkyPilot](https://docs.skypilot.ai/) | Portable AI jobs across clouds, Kubernetes, Slurm, and existing machines | Infrastructure provisioning, managed jobs, recovery, and teardown | Yes |
| [Slurm](https://slurm.schedmd.com/) | Multi-user Linux clusters with centrally administered resources | Allocation, queueing, execution, monitoring, and optional accounting | Yes |
| [Weft](https://github.com/osteele/weft) | Single-researcher jobs across workstations, shared servers, and GPU rentals | Placement, source and input staging, execution, logs, artifacts, and native processed tags | No, when native state is retained and queryable |

Setup adds a ledger for systems that track execution without tracking whether
the evidence has entered the notebook. Weft can record that distinction
directly when its native state is retained and queryable.

Dagu and Pueue need an artifact convention or wrapper when outputs are not
already written to durable storage. SkyPilot and Slurm also need
project-specific artifact locations. The notebook skill records
provider-specific syntax in the project adapter and keeps the notebook rules
portable.

## Project-controlled extensions

Each lab can add the automation and infrastructure that fits its environment.
This collection leaves the following choices to the project:

- infrastructure for long-running execution and any separately authorized
  open-ended research loops beyond the skill's bounded-plan workflow;
- code-audit hooks and research-script lint rules;
- credentials, hostnames, personal paths, project rosters, and private venue
  notes; and
- the service or command system that launches research jobs.

Those choices belong to each lab's environment and risk model. The notebook is
useful even when every job is launched by hand.

The portable skill supports explicitly authorized bounded plan execution,
including unattended reporting, without private tooling. Installing it or
requesting a preview or walkthrough does not authorize running experiments.
It does not start unsolicited or open-ended autonomous loops or add code-audit
behavior.

## License

MIT. See [LICENSE](LICENSE).
