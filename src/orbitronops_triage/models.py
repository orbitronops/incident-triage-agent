"""Data models for the triage agent. Plain dataclasses, no dependencies."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Incident:
    """A single incident, as it would arrive from an alert or a pod event."""

    id: str
    service: str
    namespace: str = "prod"
    status: str = ""  # e.g. CrashLoopBackOff, ImagePullBackOff, Running
    restarts: int = 0
    restart_window_minutes: int = 10
    last_exit_code: int | None = None
    last_terminated_reason: str = ""  # e.g. OOMKilled, Error, Completed
    memory_usage_mi: int | None = None
    memory_limit_mi: int | None = None
    log_snippet: str = ""
    node_condition: str = ""  # e.g. DiskPressure, MemoryPressure
    probe_failing: str = ""  # e.g. readiness, liveness, ""

    @classmethod
    def from_dict(cls, data: dict) -> "Incident":
        return cls(
            id=str(data.get("id", "unknown")),
            service=str(data.get("service", "unknown")),
            namespace=str(data.get("namespace", "prod")),
            status=str(data.get("status", "")),
            restarts=int(data.get("restarts", 0) or 0),
            restart_window_minutes=int(data.get("restart_window_minutes", 10) or 10),
            last_exit_code=data.get("last_exit_code"),
            last_terminated_reason=str(data.get("last_terminated_reason", "")),
            memory_usage_mi=data.get("memory_usage_mi"),
            memory_limit_mi=data.get("memory_limit_mi"),
            log_snippet=str(data.get("log_snippet", "")),
            node_condition=str(data.get("node_condition", "")),
            probe_failing=str(data.get("probe_failing", "")),
        )


@dataclass
class TriageResult:
    """The agent's assessment. Advisory only — a human decides what happens next."""

    incident_id: str
    service: str
    severity: str  # LOW | MEDIUM | HIGH | CRITICAL
    probable_cause: str
    confidence: float  # 0.0 – 1.0
    signals: list[str] = field(default_factory=list)
    read_only_commands: list[str] = field(default_factory=list)
    recommended_next_steps: list[str] = field(default_factory=list)
    requires_human_approval: bool = True
    action_executed: bool = False

    def to_dict(self) -> dict:
        return {
            "incident_id": self.incident_id,
            "service": self.service,
            "severity": self.severity,
            "probable_cause": self.probable_cause,
            "confidence": self.confidence,
            "signals": self.signals,
            "read_only_commands": self.read_only_commands,
            "recommended_next_steps": self.recommended_next_steps,
            "requires_human_approval": self.requires_human_approval,
            "action_executed": self.action_executed,
        }
