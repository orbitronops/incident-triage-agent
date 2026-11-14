"""Tests for the triage engine. Run: python -m pytest -q"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from orbitronops_triage.models import Incident
from orbitronops_triage.triage import analyse


def test_oomkilled_is_high_confidence():
    result = analyse(Incident(
        id="INC-1", service="checkout-api",
        status="CrashLoopBackOff", restarts=12,
        last_exit_code=137, last_terminated_reason="OOMKilled",
        memory_usage_mi=511, memory_limit_mi=512,
    ))
    assert result.severity == "HIGH"
    assert "OOMKilled" in result.probable_cause
    assert result.confidence >= 0.8
    assert result.requires_human_approval is True
    assert result.action_executed is False
    assert all("kubectl" in c for c in result.read_only_commands)


def test_image_pull_is_high():
    result = analyse(Incident(
        id="INC-2", service="web",
        status="ImagePullBackOff",
        log_snippet="Failed to pull image \"web:v2.4.1\": not found",
    ))
    assert result.severity == "HIGH"
    assert "Image pull" in result.probable_cause


def test_node_pressure_is_medium():
    result = analyse(Incident(
        id="INC-3", service="worker",
        status="Evicted", node_condition="DiskPressure",
    ))
    assert result.severity == "MEDIUM"
    assert "Node pressure" in result.probable_cause


def test_probe_failing_is_medium():
    result = analyse(Incident(
        id="INC-4", service="api",
        status="Running", probe_failing="readiness",
    ))
    assert result.severity == "MEDIUM"
    assert "probe" in result.probable_cause.lower()


def test_config_error_from_logs():
    result = analyse(Incident(
        id="INC-5", service="billing",
        status="CrashLoopBackOff", restarts=6,
        log_snippet="FATAL: missing env var DATABASE_URL",
    ))
    assert "Config error" in result.probable_cause


def test_unknown_crashloop_is_honest_about_low_confidence():
    result = analyse(Incident(
        id="INC-6", service="api",
        status="CrashLoopBackOff", restarts=3,
    ))
    assert result.confidence < 0.6
    assert "not yet clear" in result.probable_cause


def test_no_mutating_commands_anywhere():
    banned = ("delete", "restart", "scale", "apply", "edit", "drain", "cordon")
    for cause in ("oomkilled", "image_pull", "config_error", "node_pressure", "probe_failing", "unknown"):
        result = analyse(Incident(id="INC-X", service="s", status="CrashLoopBackOff"))
        for cmd in result.read_only_commands:
            assert not any(b in cmd.lower() for b in banned), cmd
