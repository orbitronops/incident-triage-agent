"""Deterministic triage engine.

Same input -> same output, every time. That is intentional for a demo:
a buyer can re-run it and verify it, and an on-call engineer can trust
that it is not inventing a cause from a single noisy signal.

An LLM explainer can be layered on top later (see docs/ARCHITECTURE.md).
It must never change the severity or execute an action — it only rewords
the explanation.
"""
from __future__ import annotations

from .models import Incident, TriageResult
from .runbooks import runbook_for


def _memory_at_limit(incident: Incident) -> bool:
    if incident.memory_usage_mi is None or incident.memory_limit_mi is None:
        return False
    if incident.memory_limit_mi <= 0:
        return False
    return incident.memory_usage_mi / incident.memory_limit_mi >= 0.95


def analyse(incident: Incident) -> TriageResult:
    """Triage one incident and return an advisory result. No side effects."""
    pod = f"{incident.service}-pod"
    signals: list[str] = []

    # --- OOMKilled ---------------------------------------------------------
    if incident.last_terminated_reason.lower() == "oomkilled" or incident.last_exit_code == 137:
        if incident.memory_usage_mi is not None and incident.memory_limit_mi is not None:
            signals.append(
                f"memory usage {incident.memory_usage_mi}Mi / {incident.memory_limit_mi}Mi limit"
            )
        signals.append(f"last exit code {incident.last_exit_code or 137} (OOMKilled)")
        if incident.restarts:
            signals.append(f"restarts={incident.restarts} in {incident.restart_window_minutes}m")
        book = runbook_for("oomkilled", pod, incident.namespace, incident.service)
        return TriageResult(
            incident_id=incident.id,
            service=incident.service,
            severity="HIGH",
            probable_cause="OOMKilled — container exceeded its memory limit",
            confidence=0.86,
            signals=signals,
            read_only_commands=book["commands"],
            recommended_next_steps=book["steps"],
        )

    # --- Image pull --------------------------------------------------------
    if incident.status.lower() in {"imagepullbackoff", "errimagepull"}:
        signals.append(f"pod status={incident.status}")
        if incident.log_snippet:
            signals.append(f"log: {incident.log_snippet[:120]}")
        book = runbook_for("image_pull", pod, incident.namespace, incident.service)
        return TriageResult(
            incident_id=incident.id,
            service=incident.service,
            severity="HIGH",
            probable_cause="Image pull failure — tag missing or registry auth",
            confidence=0.82,
            signals=signals,
            read_only_commands=book["commands"],
            recommended_next_steps=book["steps"],
        )

    # --- Node pressure -----------------------------------------------------
    if incident.node_condition:
        signals.append(f"node condition={incident.node_condition}")
        book = runbook_for("node_pressure", pod, incident.namespace, incident.service)
        return TriageResult(
            incident_id=incident.id,
            service=incident.service,
            severity="MEDIUM",
            probable_cause=f"Node pressure — {incident.node_condition}",
            confidence=0.71,
            signals=signals,
            read_only_commands=book["commands"],
            recommended_next_steps=book["steps"],
        )

    # --- Probe failing -----------------------------------------------------
    if incident.probe_failing:
        signals.append(f"{incident.probe_failing} probe failing")
        if incident.status:
            signals.append(f"pod status={incident.status}")
        book = runbook_for("probe_failing", pod, incident.namespace, incident.service)
        return TriageResult(
            incident_id=incident.id,
            service=incident.service,
            severity="MEDIUM",
            probable_cause="Readiness / liveness probe failing — app slow to start or probe too strict",
            confidence=0.68,
            signals=signals,
            read_only_commands=book["commands"],
            recommended_next_steps=book["steps"],
        )

    # --- CrashLoop with config-looking logs --------------------------------
    if incident.status.lower() == "crashloopbackoff":
        log = incident.log_snippet.lower()
        if any(k in log for k in ("config", "env", "missing", "not found", "invalid")):
            signals.append(f"pod status={incident.status}")
            signals.append(f"log: {incident.log_snippet[:120]}")
            if incident.restarts:
                signals.append(f"restarts={incident.restarts} in {incident.restart_window_minutes}m")
            book = runbook_for("config_error", pod, incident.namespace, incident.service)
            return TriageResult(
                incident_id=incident.id,
                service=incident.service,
                severity="HIGH",
                probable_cause="Config error — missing env var or bad config value",
                confidence=0.74,
                signals=signals,
                read_only_commands=book["commands"],
                recommended_next_steps=book["steps"],
            )
        # CrashLoop, but no clear signal yet — say so honestly.
        signals.append(f"pod status={incident.status}")
        if incident.restarts:
            signals.append(f"restarts={incident.restarts} in {incident.restart_window_minutes}m")
        book = runbook_for("unknown", pod, incident.namespace, incident.service)
        return TriageResult(
            incident_id=incident.id,
            service=incident.service,
            severity="MEDIUM",
            probable_cause="CrashLoopBackOff — cause not yet clear from available signals",
            confidence=0.45,
            signals=signals,
            read_only_commands=book["commands"],
            recommended_next_steps=book["steps"],
        )

    # --- Fallback ----------------------------------------------------------
    book = runbook_for("unknown", pod, incident.namespace, incident.service)
    return TriageResult(
        incident_id=incident.id,
        service=incident.service,
        severity="LOW",
        probable_cause="No clear failure signal in this incident — needs human review",
        confidence=0.30,
        signals=signals or ["no failure signals present"],
        read_only_commands=book["commands"],
        recommended_next_steps=book["steps"],
    )
