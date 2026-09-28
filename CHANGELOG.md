# Changelog

## [Unreleased]

### Changed

- Notebook schema 7. Money has one home, `plans/spend/`: `AUTHORITY.json`
  (schema `plan-spend-authority/v1`) holds each plan's approved ceiling,
  allocations, and dated history, keyed by plan filename stem, and `LEDGER.md`
  holds money per authorized attempt. Experiment records and plans state
  resources in engineering units and carry no currency amounts. Scripts receive
  runtime caps in seconds or calls. The validator reports a currency amount in
  an experiment record, an authority entry that names no plan, and a malformed
  ledger row, and no longer reads `plans/spend/` as plans. See
  [Spend and units](skills/research-lab-notebook/references/spend.md) and the
  [cost guide](https://research-notebook.osteele.com/guide/costs/).
- Dollars that are data rather than spend stay in a record inside
  `<!-- usd: measured|parameter — reason -->` … `<!-- /usd -->`: `measured` for
  a simulator's objective, `parameter` for an external market input whose
  source the reason names. The validator skips marked lines, reports malformed
  markers, and adds a NOTE with each record's marked line count. See
  [Prices as data](skills/research-lab-notebook/references/spend.md#prices-as-data).
- An optional `REVIEW-LEDGER.md` records independent reviews, open findings,
  and gates. The validator checks its register and findings table shapes when
  the file exists. See
  [Review ledger and gates](skills/research-lab-notebook/references/review-ledger.md).
- The project is published as Research Notebook System at
  `osteele/research-notebook`. Install commands use the new repository name;
  the two skill names are unchanged.
- Notebook schema 6 requires `CLAIMS.md` in the core set. Existing notebooks
  can add the bundled empty claim ledger; an empty, correctly shaped table is
  valid until the project has publication claims.
- The site contract check targets the standalone Research Notebook
  documentation site.

### Plans

- Authorized bounded plans support narrated, stepped, unattended, and handoff
  execution modes. Continuous execution removes routine conversational pauses
  while preserving scientific, human-review, scope, budget, and permission gates.
- Plan preview explains proposed work without execution. Results walkthrough
  (replay) reviews retained evidence in dependency order, design before results,
  and pauses after each experiment. Neither activity launches work, regenerates
  missing evidence, or changes execution state.
- A dedicated plan-execution reference provides portable natural-language
  invocation examples for local execution and read-only review.

### Publications

- Notebook manuscripts are content-canonical Typst sources that use Arkheion
  by default and share one `papers/references.bib`.
- Venue submission packets are constrained derivatives. The publication record
  tracks their state and synchronization with the evolving manuscript.
- The bundled optional `papers/` assets provide the default manuscript source
  and shared bibliography.

## v0.2.0

Notebook schema 5. A notebook that validated under schema 4 may report new
warnings or errors; each is listed here with the rule behind it.

### Experiments

- Estimands. An experiment names each quantity it measures under a `### E#`
  heading with a `**Registration**:` line whose value is `registered`,
  `found`, or `gate`. A declared estimand without a recognized value is an
  error. Records that declare no estimands are unchanged.
- `## Informed by` records what the design drew on. Every link in the section
  must resolve to a notebook file; research question IDs are exempt.
- `blocked` is a canonical status. `complete`, `done`, `cancelled`, and
  `canceled` are accepted as legacy spellings with a warning. `closed` is
  rejected because it means `abandoned` in some records and `completed` in
  others. A parenthesized qualifier may follow the status token.
- An experiment ID may carry a revision-letter suffix (`EXP-045b`) for a
  follow-up that is not a separate experiment.
- The `Pre-registered predictions (a priori)` and `Outcomes against
  pre-registered predictions` headings are accepted with or without the hyphen.
- Plan status `complete` (in `plans/complete/`) and claim status `live` are
  accepted as legacy spellings of `completed` and `supported`, with a warning.
- Analysis annexes (`EXP-NNN-topic.annex.md`) hold breakdown tables beside an
  experiment. They carry no status, are not indexed, and must name an existing
  experiment ID.
- Duplicate-ID remedies are documented, with the rule that renumbering and
  retagging happen together.
- Processing a result is one procedure for every substrate. A run on the local
  machine carries the same obligations as a cluster job; only the durability
  step differs.

### Claims

- A claim may cite an estimand as `EXP-NNN:E#`. An unresolved reference is an
  error. Citing a `found` estimand or a `gate` is a warning.
- Dates in publication records are external venue deadlines. Internal target
  dates are replaced by urgency, gate, and ready-since fields.

### Plans

- A completed plan carries a `## Completion report` (per-goal outcomes,
  limitations, follow-ups, artifact status) and `## Evidence`. Older
  completed plans that record their outcome under `Completion`, `Completion
  note`, `Completion audit`, `Outcome`, `Execution outcome`, `Execution
  result`, `Closed`, or `Disposition` are recognized as they are. Superseded
  and abandoned plans still carry `## Disposition` and `## Evidence`.
- A `## Confirmation reserve` section, when present, must carry both
  `**Held back:**` and `**Decision rule:**`.
- Retraction notices annotate a terminal plan whose stated outcome an
  experiment later corrects.
- A plan that answered its question negatively is `completed`, not
  `abandoned`.

### References

- `notebook-graph.md` maps node kinds, edges, each edge's write-moment owner,
  and the checker for it.
- `research-methodology.md` adds instrument-reach checks at phase boundaries,
  structural versus contingent limits, and matched-magnitude controls with
  dose ladders.

## v0.1.0

Initial release: the `research-lab-notebook` and `download-research-references`
skills, notebook schema 4, the structural validator, and the
gradient-accumulation example.
