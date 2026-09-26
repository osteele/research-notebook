# Running research jobs

Research work may run on a laptop, shared cluster, cloud service, or workflow
system. The notebook needs stable procedures to submit work, inspect it,
retrieve its outputs, cancel it when authorized, and record that its evidence
has been processed. Record each procedure in the project's `RUNNER.md`. This
project-specific mapping is the runner contract.

For authorized bounded plan execution, follow the
[execution mode](plan-execution.md#execution-modes). Local and remote runs have
the same evidence-processing and human-review obligations in
[Experiments](experiments.md#processing-a-result); only artifact durability
differs. Reporting cadence does not change when a job may be marked processed.
Plan preview and results walkthrough (replay) read retained evidence without
submitting work, retrying jobs, recomputing measurements, or changing processed
state.

## Required capabilities

| Capability | Required result |
|---|---|
| Submit | Stable job ID, experiment tag, bounded command or workload, code revision |
| Status | Queued, running, succeeded, failed, or canceled |
| Logs | Read-only stdout/stderr or service logs |
| Artifacts | Immutable or versioned outputs with retrieval metadata |
| Cancel | Explicitly targeted cancellation when authorized |
| Processed check | Whether this job's evidence has entered the notebook |
| Processed mark | Idempotent mark written after durable notebook updates |

Useful optional fields include host or cluster, accelerator, image or
environment, start and end times, exit code, runtime, cost, parent job, retry,
and artifact hashes.

## Usage and billing sources

Document available usage and billing sources in the project's `RUNNER.md`.
Use supported CLI or API interfaces and retained provider reports, not a
runner's private database or registry. This mapping describes what the
installed backend actually exposes; it does not add a required runner
capability or promise a portable billing command.

For each source, record:

- the supported read-only command, API, or report retrieval procedure and any
  permissions it needs;
- the source's identity and join to Backend + Job ID, including parent jobs,
  automatic retry attempts, or provisioning IDs;
- available quantities, units, timestamps, and whether durations describe
  active work, allocation, or provisioned uptime;
- monetary fields, currency, rate date, billing scope, and whether amounts are
  estimates, provisional provider reports, or settled charges; and
- reporting lag, retention, attribution gaps, and known exclusions such as
  setup, idle capacity, storage, transfers, credits, or taxes.

Record usage observations, with source identity and retrieval time, in the
experiment's [Resources](experiments.md#resources), and money in the plan's
spend ledger ([Spend and units](spend.md#ledgermd)). Preserve the source period
or as-of time too; retrieving a stale report now does not make its figures
current. A job system may expose resource usage but no price. In that case, a
dated rate can support a ledger row marked `/provisional`, while final monetary
cost remains unavailable. A local run can have resource usage and no incremental
cash charge; state the accounting scope instead of treating all resources as free.

Use exact identifiers when available. Disclose ambiguous joins rather than
assigning a shared provider bill to the nearest job. Document how shared
provisioning, storage, and transfer charges will be attributed and counted once,
with any unallocated amount visible. Preserve missingness when a source cannot
separate retries or report billing yet.

Describe which resource, runtime, spending, and retry limits the runner really
enforces, and where project coordination must reserve capacity before parallel
submission. A notebook ceiling alone is not runtime enforcement. Cancellation
requests need confirmation; billing may continue through teardown or arrive
later. Keep remaining commitments and unresolved fees visible until supported
evidence changes them.

## Tagging

Attach the experiment ID to each submission. Also attach the project ID when a
runner spans projects. A sweep may add a condition or shard tag, but the
experiment ID remains the primary join key.

## Processed state

Processing state answers a different question from completion:

- `completed`: the backend finished the computation.
- `processed`: the outputs were checked and incorporated into durable evidence.

Prefer a backend's native processed marker when it is durable, queryable, and
namespaced. Otherwise use the [processed-job ledger](processed-job-ledger.md).

Write the processed mark last. Store a pointer to the experiment or finding and
the notebook revision when the backend allows metadata.
Capture available usage evidence in the record, and money in the spend ledger,
before that durable update. Processed state means scientific evidence processing
is complete; it does not certify financial settlement. A later bill is a
`correction` row in the ledger carrying the difference, without duplicating
spend or creating a second processing entry.

## Failure behavior

Do not mark failed or partial jobs processed until their failure mode is
recorded. Preserve logs and partial artifacts that explain the failure. A retry
gets a new job ID and links to the original; it does not overwrite history.

Avoid open-ended local wait processes. Prefer one-shot status and log checks or
a bounded monitor that will finish in the current session.
