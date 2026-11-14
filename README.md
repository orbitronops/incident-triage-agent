# OrbitronOps Incident Triage Agent

> **A read-only, human-in-the-loop on-call copilot for Kubernetes / platform teams.**
> It triages an incident, explains the probable cause, and proposes the next safe step — it never runs a mutating command on its own.

[![CI](https://github.com/orbitronops/incident-triage-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/orbitronops/incident-triage-agent/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status: Demo](https://img.shields.io/badge/status-demo%20%E2%80%94%20not%20client%20work-lightgrey.svg)](#status)

**By [OrbitronOps](https://www.orbitronops.com)** — Production AI Infrastructure on Kubernetes.
North Vancouver, BC · Canada Remote / BC Hybrid

---

## What this proves

A buyer doesn't have to take our word for it. They can run this in 2 minutes:

```bash
git clone https://github.com/orbitronops/incident-triage-agent.git
cd incident-triage-agent
python -m orbitronops_triage triage examples/crashloop.json
```

And get a triage report like this:

```
Incident: checkout-api CrashLoopBackOff  ·  Severity: HIGH  ·  Confidence: 0.86
Probable cause: OOMKilled — container exceeded its memory limit (512Mi)
  Signals: restarts=12 in 10m, last exit code 137, memory usage 511Mi / 512Mi

Recommended next steps (read-only first):
  1. kubectl describe pod checkout-api-7d9f8 -n prod
  2. kubectl logs checkout-api-7d9f8 -n prod --previous
  3. kubectl top pod checkout-api-7d9f8 -n prod

Human approval: REQUIRED — no action was executed.
Audit record written to: audit/audit.jsonl
```

No API key needed for the demo. No cluster needed. No cloud bill.

## Why read-only first?

This is the OrbitronOps rule for agents in production:

1. **Read-only first** — `get`, `describe`, `logs`, `top` only.
2. **Human-in-the-loop** — every proposed action waits for a named approver.
3. **Full audit log** — every triage and every approval is written to `audit/audit.jsonl`, with who, when, and what was approved.

That is how you ship an agent to a regulated team without asking them to trust a black box.

## Quickstart

**Requirements:** Python 3.10+ only. No dependencies for the demo.

```bash
# 1. Clone
git clone https://github.com/orbitronops/incident-triage-agent.git
cd incident-triage-agent

# 2. Triage a sample incident
python -m orbitronops_triage triage examples/crashloop.json
python -m orbitronops_triage triage examples/oomkilled.json --format json
python -m orbitronops_triage triage examples/imagepull.json

# 3. Run the tests
python -m pytest -q
# or, with no pytest installed:
python -m unittest discover -s tests -v
```

### Try your own incident

Copy an example and edit it:

```bash
cp examples/crashloop.json my-incident.json
# edit my-incident.json, then:
python -m orbitronops_triage triage my-incident.json
```

See [`examples/`](examples/) for the incident schema, and [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) for how the triage engine works.

## How it works

```
Incident JSON → Triage Engine → Probable cause + confidence
                               → Runbook steps (read-only)
                               → Human approval gate
                               → Audit log (JSONL)
```

| Incident signal | Probable cause | Confidence |
|---|---|---|
| `CrashLoopBackOff` + exit 137 + memory at limit | OOMKilled — memory limit too low | High |
| `ImagePullBackOff` / `ErrImagePull` | Image tag missing, or registry auth | High |
| `CrashLoopBackOff` + exit 1 + config error in logs | Bad config / missing env var | Medium |
| Pod evicted / `NodePressure` | Node disk / memory pressure | Medium |
| Readiness probe failing, app responding slowly | App not ready, or probe too strict | Medium |

The engine is deliberately deterministic for the demo — same input, same output, every time. An LLM summariser is a pluggable interface (`src/orbitronops_triage/llm.py` — optional, bring your own key), never required, and never allowed to execute an action.

## Project layout

```
.
├── src/orbitronops_triage/   # the agent: models, triage engine, runbooks, audit, CLI
│   ├── models.py             # Incident / TriageResult dataclasses
│   ├── triage.py             # deterministic triage rules
│   ├── runbooks.py           # read-only runbook steps per cause
│   ├── audit.py              # JSONL audit log
│   └── cli.py                # `python -m orbitronops_triage triage <file>`
├── examples/                 # sample incidents + a sample output report
├── tests/                    # pytest / unittest tests for every rule
├── docs/
│   ├── ARCHITECTURE.md       # design, safety model, extension points
│   └── SECURITY.md           # what the agent can / cannot do
├── .github/workflows/ci.yml  # lint + tests on every push
├── Dockerfile                # run the demo in a container, no local Python needed
└── pyproject.toml
```

## Status

**Demo — not client work.**

OrbitronOps has not yet delivered a client AI agent. This repository is a working prototype built to show how we build one: the safety model, the code quality, and the audit trail a client would actually get.

If you want this wired to *your* cluster, alerts, and runbooks, talk to us: [orbitronops.com](https://www.orbitronops.com) · [LinkedIn](https://www.linkedin.com/company/orbitronops/)

## Roadmap

- [x] Deterministic triage engine + read-only runbooks + audit log
- [ ] Live Kubernetes read-only connector (`kubectl get/describe/logs` via API)
- [ ] Slack / PagerDuty alert ingestion
- [ ] Postmortem draft generator from the audit log
- [ ] Optional LLM explainer (pluggable provider, off by default)

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Issues and PRs welcome — please keep the read-only safety rule intact.

## License

MIT — see [LICENSE](LICENSE).
