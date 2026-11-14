# Architecture

## Design goals

1. **A stranger can run it in 2 minutes** — no API key, no cluster, no cloud bill.
2. **Deterministic** — same incident in, same triage out. No hidden randomness in the demo path.
3. **Safe by construction** — the agent cannot mutate anything. There is no code path that calls `kubectl delete / scale / apply`, and the tests enforce that.

## Flow

```
Incident JSON
  → models.Incident.from_dict()
  → triage.analyse()          # rule-based, deterministic
  → runbooks.runbook_for()    # read-only commands + human steps
  → audit.append_audit()      # JSONL, append-only
  → CLI renders text or JSON
```

## Extension points

| Want to add… | Where |
|---|---|
| A new failure pattern | A new branch in `triage.analyse()` + a test in `tests/test_triage.py` |
| A new runbook | A new entry in `runbooks.RUNBOOKS` |
| Live cluster reads | A new `connectors/kubernetes.py` that only calls the read-only Kubernetes API (`list pods`, `read logs`) and feeds `Incident` objects in |
| Slack / PagerDuty ingestion | A new `connectors/alerts.py` that converts an alert payload to `Incident` |
| LLM explainer | A new `llm.py` with a `summarise(result) -> str` interface. It must only reword the explanation — it must not change severity, confidence, or execute anything. Off by default, bring your own key. |

## What this is not (yet)

- Not a live cluster agent — the demo uses sample JSON, not a real API server.
- Not an auto-remediator — there is intentionally no auto-fix path.
- Not a client delivery — see README Status. It is a prototype that shows how OrbitronOps builds.
