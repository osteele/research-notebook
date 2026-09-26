# Review ledger and gates

`REVIEW-LEDGER.md` is an optional notebook file that records independent reviews
and turns the faults they find into **gates**: questions to ask before the next
experiment is written or submitted. Each gate exists because a run failed that
way. The ledger answers two questions a notebook otherwise cannot: which checks
have paid for themselves, and how often review finds nothing.

Reviews in this process are requested. A person asks for one, or the project's
instructions require one at a named transition, such as before a script's first
paid submission. The ledger records reviews; it does not schedule them.

## What gets reviewed, and when

| Artifact | When | What the reviewer judges |
|---|---|---|
| Plan | Before execution, and at completion | Whether dependencies, gates, decision rules, and the completion condition are stated and testable |
| Experiment design | Before code is written against it | Whether the registered design can answer its question, and whether the decision rule computes the quantity the design measures |
| Experiment script | Before its first costly run, and after any change | Whether the code implements the design, and whether its statistics, artifacts, and provenance are sound |
| Results | Before a finding or claim relies on them | Whether the numbers and interpretation follow from the retained evidence |

Each review answers one of these questions. A design review does not establish
that the code implements the design, and neither review establishes that the
code runs or that the instrument can move the construct it measures. Those need
execution: a bounded smoke run, and a pilot with a predeclared positive control.

## Reviewer independence

Record how the reviewer relates to the author, because independence governs what
a review can catch:

| Relation | Meaning |
|---|---|
| `self` | The author reviewed their own work. |
| `same model, no shared context` | A fresh session of the same model, given only the artifact and its record. |
| `different model` | A reviewer from a different model family or provider. |
| `human` | A person other than the author. |

A fresh reviewer receives the artifact and the record it implements, and nothing
of the session that produced them. Consecutive repairs of one artifact benefit
from alternating authors as well as reviewers: a reviewer reports an author's
blind spot once per round, and the next repair by the same author tends to
reproduce it.

## File layout

```markdown
# Review ledger

## Review register

| ID | Date | Kind | Target | Reviewer | Relation | Findings |
| --- | --- | --- | --- | --- | --- | --- |
| R001 | 2026-09-10 | review-script | scripts/exp_002_comparison.py @ 3f1c9a2e | fresh session | same model, no shared context | F001, F002 |
| R002 | 2026-09-11 | review-script | scripts/exp_002_comparison.py @ 8b04d17c | second provider | different model | none |

## Open findings

| ID | Fault | Caught by | Severity | Status |
| --- | --- | --- | --- | --- |
| F002 | Summary averages over all cells, including the excluded pilot cell | R001 | silent | repair landed; awaiting review |

## Gates — checkable from the artifact

#### G1 — Does the summary aggregate over the intended slice?
**Added** 2026-09-10, at EXP-002. **Severity:** silent. **Tally: 1** — F001 (founding). **Slug:** `aggregation-slice`.

What failed, in two or three sentences, with the experiment it cost.

**Check:** the one question a reviewer answers from the artifact.

## Gates — need project history

## Promoted
```

### Review register

One row per review, **including reviews that found nothing**. Clean reviews are
the denominator: without them, neither the practice's value nor any single
gate's value can be measured, and the register becomes a list of successes.
Many similar reviews may share one summary row (`R040–R061: 22 script reviews,
2 findings`).

The Target names the exact bytes reviewed: a path with a content digest or
revision. A review of earlier bytes does not cover a revision.

### Findings

A finding stays open until a review verifies the repair. The author's own
passing tests show the repair runs; they do not show it is right. Record that a
repair landed, and close the finding when a review of the repaired bytes
settles it. Severity is `silent` when the fault would have produced a wrong
number with no error, and `loud` when it would have failed visibly.

### Gates

A gate is a question with a founding incident. Add one when a run fails for a
reason no existing gate covers. When a later finding is another instance of an
existing gate, attach it and increment the tally rather than adding a near
duplicate; resemblance between two faults is not by itself evidence that they
are the same.

Split gates into two sections. Gates decidable from a script and its output go
first, and a fresh-context reviewer receives only that section. Gates that need
the project's history, such as whether a sibling experiment already solved this
problem, stay with reviewers who have that history. A reviewer is never asked to
work out which gates it can reach.

A gate with a high tally is a candidate for **promotion**: into a template, a
shared checklist, or a mechanical check that makes the fault impossible to
write. Record the promotion and say what it does not cover; a template reaches
only records written from it. A gate that stops firing is a candidate for
retirement.

## Consulting the ledger

Before submitting a new or modified experiment script, read the gate titles and
open the detail only for gates that plausibly apply. The file is written to be
skimmed in under a minute. After the run, log the review that preceded it,
whatever it found.

Edit the ledger through a tool that allocates IDs and serializes concurrent
writers when one is available. Without one, append rows by hand and never
renumber or delete them.
