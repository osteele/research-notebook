# The notebook as a graph

A lab notebook is a typed graph. The files are nodes of a small number of
kinds, and the conventions in the sibling references each mandate specific
edges, name which file writes each edge, and say what checks it. This page
draws that map whole. It adds no rules; every edge below is normative in
another reference, and that reference wins on detail. Knowing the shape makes
several operations easier to state: a provenance question is a walk, an audit
is a traversal, a dashboard is a materialized view, and "which experiments did
this plan produce" is a one-hop lookup rather than a search across prose.

## Node kinds

| Kind | Identity | Lives at |
|---|---|---|
| Research question | `RQ#` | `QUESTIONS.md` |
| Plan | date basename (`2026-07-05-topic`) | `plans/<status>/` |
| Experiment | `EXP-NNN` | `experiments/EXP-NNN-topic.md` |
| Estimand | `EXP-NNN:E#` | `### E#` heading inside the experiment |
| Run or job | backend job ID | experiment `## Runs` table |
| Finding | date basename | `findings/YYYY-MM-DD-topic.md` |
| Claim | `C#` | `CLAIMS.md` row |
| Publication | paper key | `PUBLICATION.md`, `papers/` |

## Edge list

Each edge has exactly one write-moment owner: the file whose author writes it
at the moment the fact comes into existence. Two files recording the same edge
drift, so the reverse direction is computed (a search, an index, a dashboard
join), never stored.

| Edge | Written in | Written when | Checked by |
|---|---|---|---|
| plan → plan (supersedes) | `superseded_by:` frontmatter | at supersession | validator |
| plan → experiment | plan phases and completion report | when the experiment record is created | validator (link resolution) |
| experiment → research question | `**Research questions**:` | at creation | template |
| experiment → job | `## Runs` row and the job's tag | at submission | runner cross-check |
| upstream experiment → downstream experiment | upstream `## Decision rule` or `## Follow-ups` | when the gating is decided | prose; the forward link is required |
| experiment → prior evidence (informed by) | experiment `## Informed by` | at design, and again at each amendment | validator (link resolution) |
| experiment → its own estimands | `### E#` heading and `**Registration**:` line | at design | validator (registration values) |
| claim → experiment estimand | `CLAIMS.md` Evidence cell, as `EXP-NNN:E#` | when a claim is banked | validator (resolution; found and gate warnings) |
| claim → publication | `CLAIMS.md` Paper cell | when a paper consumes it | validator |
| experiment → claim (refutation only) | experiment `## Conclusion` (`Refutes C12`) | when evidence refutes | prose |
| plan → its completion evidence | `## Completion report` links | at terminal status | validator (heading presence) |
| plan or experiment → what settled a choice | `## Decisions` entry links | when the choice is made | validator (dated entries, newest last, link resolution) |
| terminal plan → correction | retraction notice beneath the affected passage | when a correction is applied | the retracting session's sweep |

Two asymmetries look like omissions until the rule behind them is known.
Experiments carry no back-link to plans or claims: the plan and the claims
ledger own those edges, and a search for `EXP-NNN` is the computed reverse.
And a finding cites its experiments, while an experiment's `## Findings`
section is a courtesy pointer, not the authoritative edge.

### Why "informed by" cannot be derived

Every other edge records structure that is recoverable from the artifacts.
This one records what the designer had already seen when the design was
fixed, and no artifact carries that. A threshold chosen before looking and
one chosen after produce byte-identical code, a byte-identical lockfile, and
byte-identical output. The distinction exists only at the write moment, which
is why this edge has to be authored and why it decays irrecoverably if it is
not.

The names are borrowed from [W3C PROV](https://www.w3.org/TR/prov-o/); the
format is not. PROV's own guarantee applies: `wasDerivedFrom` cannot always be
inferred from the underlying used/generated structure, because when an
activity has several inputs and several outputs it is not determined which
output came from which input. Derivation is authored, not computed. If the
graph ever needs external querying, export to PROV rather than authoring in it.

### Why a claim cites an estimand rather than a record

Role is a property of a path, not of a node. One run routinely has several
facets with different standing: an arm registered in advance and tested as
designed, and a pattern that fell out of an arm that existed for some other
purpose. Both are in one artifact and one record. A record-level label
("pilot", "probe", "confirmatory") cannot express that, and a project that
tries will find its label contradicted by its own best result.

So the record names its estimands separately, each with the status of its
registration, and the claim cites `EXP-NNN:E#`. The check that becomes
possible: does this claim's role exceed what that estimand registered? A claim
drawing on an unregistered facet is a found result and must be marked so;
making it confirmatory needs a fresh run, and "same data or fresh data?" has to
be answerable.

## Questions as traversals

- *Is this claim still supported?* claim → evidence estimands → each
  experiment's status and conclusion → later findings that cite those
  experiments.
- *Which experiments did this plan produce?* plan phases and completion
  report → experiments.
- *Is this direction settled?* plan → completion report → linked evidence. A
  successor edge (`superseded_by`, or a follow-up plan named in the report)
  means the question moved rather than closed.
- *Who relied on this value?* the retracting experiment's ID and the
  superseded numbers, searched across the notebook.

## What this deliberately is not

There is no central graph store, and there should not be one. The notebook
files are authoritative; every index (a dashboard, a plan index, a review
queue) is a rebuildable view over them. Adding an edge to the system means
giving it a write-moment owner and a checker in the owning reference, not a
row in a database.
