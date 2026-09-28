# Spend and units

Money has one home in a notebook: `plans/spend/`. Experiment records, plans, and
experiment scripts state scientific quantities and engineering units. They carry
no ceiling, estimate, rate, or actual in currency.

| Surface | Carries | Never carries |
|---|---|---|
| Experiment record | Scientific quantities; compute quantities such as GPU-hours, device class, forward passes, API calls, tokens, and retained bytes; elapsed time; Backend and Job ID for each attempt | Currency amounts of any kind |
| Plan | Scope, packages, the experiments in each package, and the resource estimate in units | Ceilings, allocations, rates, spend figures |
| Experiment script | The same units, and a runtime cap received as seconds, forward passes, calls, or tokens | Currency constants, rates, rate × time arithmetic, currency flags |
| `plans/spend/AUTHORITY.json` | The ceilings and allocations the owner approved, who approved them, when, and their history | — |
| `plans/spend/LEDGER.md` | Money committed and spent per authorized attempt | — |

Scientific budgets, such as a retry budget, a strike budget, or an alpha budget,
are design quantities. They stay in the record.

## Why money is kept out of records

A price is a market fact resolved when the job is placed. The same pilot can
bill differently on two devices a day apart, while its forward count, seconds
per forward, and device class stay fixed. A record that freezes a price freezes
a guess about the market. The units are the reproducible part.

A ceiling copied into a script or record becomes a second home for it, and the
copy is the one that goes stale. When the owner raises a plan's ceiling, a
script that still checks the old figure refuses the correct authorization and
admits one stating the old number.

Records are published. They serve as preregistration artifacts and paper
supplements, and compute-reporting checklists ask for hardware and GPU-hours.
Rates and an owner's ceilings are private operating detail.

## Units in records and plans

State each estimate in the units that determine it:

- compute quantity, with its unit and device count, such as 4 GPU-hours on one
  48 GB device, or 24,300 forward passes;
- calls and tokens for a provider API;
- elapsed time, including queueing and parallelism assumptions;
- human effort, in person-hours; and
- retained data, in bytes.

Keep them separate. Parallel execution shortens elapsed time without reducing
GPU-hours; a queue wait lengthens elapsed time without consuming compute.

A projection across providers or devices keeps the configuration and drops the
rate. "Two 8-GPU nodes for 3 hours" stays true when the price changes;
"about $400" does not. The configuration usually carries the scientific
argument, since it records what scale of hardware the arm requires.

## Prices as data

The rule governs spend on the research itself. A price can also be the object
of study, or an input to the model under study. Those dollars would mean the
same thing if someone else had paid for the compute, and they are scientific
quantities. A record keeps them inside a marked region:

```markdown
<!-- usd: measured — simulator objective: total cost per job -->
| Policy | Cost per job (USD) |
|---|---|
| greedy | $1.20 |
<!-- /usd -->
```

- `measured` is reserved for dollars a simulator or model outputs as its
  objective. They are experimental measurements.
- `parameter` is for external market inputs: spot prices, total-cost-of-ownership
  rates, market-derived cost-efficiency figures. The reason names the source or
  the model the parameter feeds.
- The marker wraps lines, not files. One record often holds both a simulator
  table and a line about what the rental cost, and a file-level exemption would
  license the second under cover of the first. Nothing is inferred from
  position: scientific dollars appear in prose as well as tables.
- The validator skips lines inside a marker, reports a marker that is unclosed,
  nested, stray, unlabeled, or missing its reason, and adds a NOTE giving each
  record's marked line count, so growth in exemptions stays visible.

The marker is for figures that remain once spend is out of the record, never for
spend itself. A study of cost-effectiveness reports the units that determine the
price (calls, tokens, device-hours, extrapolated volume) and marks the per-unit
price as a `parameter`.

## The spend directory

Both files are keyed by the plan's filename stem, never its path. Plans move
between status directories, and a file stored beside its plan would be orphaned
by an ordinary status change. The validator reports an authority entry whose
stem names no plan, so a rename fails loudly.

### `AUTHORITY.json`

```json
{
  "schema": "plan-spend-authority/v1",
  "plans": {
    "2026-09-01-retrieval-comparison": {
      "shared_ceiling_usd": 21.0,
      "authorized_by": "A. Researcher",
      "recorded_utc": "2026-09-09T00:00:00+00:00",
      "allocations": {
        "confirmation": {
          "ceiling_usd": 8.0,
          "experiments": ["EXP-004"],
          "note": "Held for independent confirmation after the comparison gate."
        }
      },
      "history": []
    }
  }
}
```

- `shared_ceiling_usd` is the plan's single ceiling, inclusive of everything
  already spent. Version 1 records amounts in US dollars.
- `allocations` are optional sub-ceilings inside the shared ceiling. They do not
  add to it. A `ceiling_usd` of `null` names a package whose terms are in its
  `note` without a separate figure.
- A raise or reallocation updates the current fields and appends the previous
  state to `history` with a dated note saying why. History is never deleted.
- This file is the authority, not a mirror of prose elsewhere. The plan names
  its packages and points here.

### `LEDGER.md`

Money per authorized attempt, including failed and voided attempts.
A run that billed before it failed still spent the money.

```markdown
| Row | Date | Plan | Experiment | Attempt | Job | Phase | Committed USD | Actual USD | Outcome |
|---|---|---|---|---|---|---|---|---|---|
| S001 | 2026-09-10 | 2026-09-01-retrieval-comparison | EXP-002 | pilot-r1 | demo:SYN-PILOT-2 | pilot | 3.00 | 2.00 | complete |
```

- **Plan** is a plan stem, or `-` for spend that belongs to no plan, such as an
  owner-directed evaluation with no ceiling. A `-` row needs no authority entry.
- **Attempt** is the stable attempt identity the experiment record uses; **Job**
  is `Backend:Job ID` when the attempt ran on a runner.
- **Committed** is the amount the authorization reserved. **Actual** is the best
  current figure for what the attempt cost, or `-` while unknown.
- **Outcome** is `authorized` or `running` while the attempt holds its
  commitment, and a terminal value afterward: `complete`, `failed`, `canceled`,
  `operational-void`, or `correction`. Append `/provisional` to a terminal
  value when the actual is usage-estimated or not yet billed.
- Rows are appended, with one exception: when an attempt resolves, its own row
  is completed in place, once. Its Outcome becomes terminal and Actual is
  filled; a `/provisional` suffix comes off when the bill confirms the figure.
  While the row is open its Actual stays `-`, so its money is counted once, as
  a commitment. Partial usage of a running attempt belongs in the record, in
  units.
- After that, a wrong or late figure is corrected by a new `correction` row
  naming the same Attempt, with `0.00` Committed and the **difference** as
  Actual, so the column sum stays the total.
  A final bill that adds 0.50 for idle time appends a 0.50 correction; it does
  not restate the attempt.

Rows are numbered across the whole file. A row with the wrong number of cells is
an error, never skipped: a skipped money row understates spend.

## Deriving the account

For one plan at one as-of time, taking only rows whose Plan is that stem:

| Quantity | Derived from |
|---|---|
| A: incurred | The sum of Actual. |
| C: committed | The sum of Committed on rows whose Outcome is `authorized` or `running`. |
| U: planned | Not stored. The plan's remaining work in units, priced at a current rate when an authorization is built. |

Headroom after commitments is the shared ceiling minus A minus C, and it must
still cover U. Neither headroom nor an underspend grants approval for more work.
Unknown spend renders as unknown, never as zero, and an incomplete subtotal is
not a settled total.

## How a run gets its budget

Tooling that runs where the notebook is readable builds each authorization. It
reads the authority and the ledger, checks the requested ceiling against
headroom, converts the ceiling and the placement's rate into seconds (or calls,
or tokens), writes the commitment as a ledger row, and hands the script an
authorization in those units. The script enforces the units it was given and
refuses an authorization that carries any currency field, since a tolerated
money field is how a stale ceiling survives. The script never reads the
notebook, which often does not reach the execution host, and holds no plan-level
number of its own.

A written limit does not stop a process. Describe which duration, concurrency,
and spending controls the runner actually enforces in `RUNNER.md`, and admit
concurrent attempts against conservative upper bounds so separate agents cannot
each spend the same headroom.
