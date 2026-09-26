# Notebook structure

Prefer a self-contained `lab-notebook/` directory:

```text
project/
  lab-notebook/
    STATUS.md
    QUESTIONS.md
    PRIORITIES.md
    CHANGELOG.md
    GLOSSARY.md             # recommended when terminology needs definition
    BIBLIOGRAPHY.md         # recommended for related-work annotations
    RUNNER.md               # optional tracked compute adapter
    experiments/
      README.md
      EXP-001-short-topic.md
    findings/
      README.md
      2026-08-10-cross-experiment-result.md
    plans/                  # optional multi-step research plans
      spend/                # optional: AUTHORITY.json and LEDGER.md, the only home for money
    reports/                # optional living syntheses
    papers/                 # optional canonical Typst manuscripts and shared bibliography
    references/             # optional cited-paper cache and tracked source notes
    kb/                     # optional stable reference material
    causal-models/          # optional working mechanism hypotheses
    CLAIMS.md               # core claim ledger; initially empty
    REVIEW-LEDGER.md        # optional review register, findings, and gates
    PUBLICATION.md          # optional paper readiness and venues
  scripts/                  # executable research code
  data/                     # raw or structured results
```

Keep executable scripts with project code, not inside the notebook. The
notebook records the command, revision, parameters, and outputs needed to
reproduce the run.

## Create optional files only when needed

- Add `plans/` for a bounded objective with several experiments or phases.
- Add `RUNNER.md` when the project submits or processes jobs through a runner.
- Add `plans/spend/` when work spends money under an approved ceiling. It holds
  every currency amount in the notebook; see [Spend and units](spend.md).
- Add `REVIEW-LEDGER.md` when the project logs independent reviews; see
  [Review ledger and gates](review-ledger.md).
- Add `reports/` for a living analysis that does not fit one experiment or one
  immutable finding.
- Add `papers/` for notebook-resident, content-canonical manuscripts authored
  by the project. New manuscripts use the Arkheion Typst template and share
  `papers/references.bib`; venue submission packets live outside the notebook.
- Add `references/` and `BIBLIOGRAPHY.md` when tracking cited work. Ignore
  `references/**/*.pdf`, not the whole directory, so indexes and source notes
  remain trackable.
- Add `kb/` for stable methodology, terminology, or comparison notes.
- Add `causal-models/` when multiple interventions inform a shared mechanism
  hypothesis that must remain distinct from observed findings.
- Add `GLOSSARY.md` when project-specific terms, acronyms, or equations need a
  stable definition.
- Add `PUBLICATION.md` when at least one paper is in active preparation.

Empty scaffolding creates false affordances. A small notebook that grows with
the project is easier to trust.

## Version control

The notebook may share the code repository or use its own repository. Record
the boundary in project instructions. Never assume that an ignored
`lab-notebook/` is unversioned; it may be a nested repository.

Keep raw data and large artifacts outside Markdown. Store stable references to
their locations and content hashes when practical.
