# Security

## What the agent can do

- Read an incident JSON file you give it.
- Print a triage report (text or JSON).
- Append one line to `audit/audit.jsonl`.

## What the agent cannot do

- It has no network access in the demo path.
- It cannot run `kubectl`, shell commands, or any mutating Kubernetes action.
- It cannot delete, restart, scale, drain, cordon, or edit any workload.
- It stores no credentials. There is no place to put a token or API key in the demo.

## Human-in-the-loop

Every `TriageResult` has:

- `requires_human_approval: true`
- `action_executed: false`

That is not a flag you can flip in config — there is no execution path at all in v0.1.0. A future live connector must keep that gate: propose, log, wait for a named approver, then (and only then) execute a whitelisted read-only or explicitly approved action, and log that too.

## Reporting a problem

Open an issue in this repo. Do not include real cluster credentials, real customer data, or real incident logs with secrets in any issue or example.
