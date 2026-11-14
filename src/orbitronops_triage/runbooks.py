"""Read-only runbook steps per probable cause.

Safety rule: every command here is read-only — get / describe / logs / top.
Nothing in this file deletes, restarts, scales, or edits anything.
"""
from __future__ import annotations

RUNBOOKS: dict[str, dict[str, list[str]]] = {
    "oomkilled": {
        "commands": [
            "kubectl describe pod {pod} -n {ns}",
            "kubectl logs {pod} -n {ns} --previous",
            "kubectl top pod {pod} -n {ns}",
        ],
        "steps": [
            "Confirm the memory limit in the Deployment / StatefulSet spec — do not raise it blindly.",
            "Check for a memory leak: compare usage over the last hour, not just the last minute.",
            "If usage grows steadily per request, escalate to the service owner with the graph; a limit raise only buys time.",
        ],
    },
    "image_pull": {
        "commands": [
            "kubectl describe pod {pod} -n {ns}",
            "kubectl get events -n {ns} --sort-by=.lastTimestamp | tail -20",
        ],
        "steps": [
            "Confirm the image tag exists in the registry — a typo'd tag is the most common cause.",
            "Check imagePullSecrets and registry credentials for this namespace.",
            "Check registry / network status before retrying the rollout.",
        ],
    },
    "config_error": {
        "commands": [
            "kubectl describe pod {pod} -n {ns}",
            "kubectl logs {pod} -n {ns} --previous",
            "kubectl get configmap -n {ns} | grep {service}",
        ],
        "steps": [
            "Read the first error line in the previous logs — it usually names the missing env var or config key.",
            "Diff the ConfigMap / Secret against the last known-good revision.",
            "Do not roll back until a human confirms which change introduced it.",
        ],
    },
    "node_pressure": {
        "commands": [
            "kubectl describe node",
            "kubectl get pods -A --field-selector spec.nodeName=<node> | head -20",
            "kubectl top node",
        ],
        "steps": [
            "Identify whether it is disk or memory pressure — they have different fixes.",
            "Check for a single noisy pod consuming the node.",
            "Cordon / drain is a human decision, not an automatic one.",
        ],
    },
    "probe_failing": {
        "commands": [
            "kubectl describe pod {pod} -n {ns}",
            "kubectl logs {pod} -n {ns} --tail=50",
        ],
        "steps": [
            "Check whether the app is actually slow, or the probe timeout is too strict.",
            "Compare probe settings with the app's real startup time.",
            "Do not relax a probe to hide a real slowness problem.",
        ],
    },
    "unknown": {
        "commands": [
            "kubectl describe pod {pod} -n {ns}",
            "kubectl logs {pod} -n {ns} --previous --tail=100",
            "kubectl get events -n {ns} --sort-by=.lastTimestamp | tail -20",
        ],
        "steps": [
            "Gather the three read-only outputs above and attach them to the incident.",
            "Escalate to the on-call engineer — do not guess a fix from one signal.",
        ],
    },
}


def runbook_for(cause_key: str, pod: str, namespace: str, service: str) -> dict[str, list[str]]:
    """Return the runbook for a cause, with pod / namespace / service filled in."""
    book = RUNBOOKS.get(cause_key, RUNBOOKS["unknown"])
    commands = [
        cmd.replace("{pod}", pod).replace("{ns}", namespace).replace("{service}", service)
        for cmd in book["commands"]
    ]
    return {"commands": commands, "steps": list(book["steps"])}
