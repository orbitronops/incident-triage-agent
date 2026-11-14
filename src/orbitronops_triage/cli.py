"""CLI: python -m orbitronops_triage triage <incident.json> [--format json]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from a checkout without installing: `src` on sys.path.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from orbitronops_triage.audit import append_audit  # noqa: E402
from orbitronops_triage.models import Incident  # noqa: E402
from orbitronops_triage.triage import analyse  # noqa: E402


def _render_text(result) -> str:
    lines = [
        f"Incident: {result.service}  ·  Severity: {result.severity}  ·  Confidence: {result.confidence:.2f}",
        f"Probable cause: {result.probable_cause}",
        "",
        "Signals:",
    ]
    lines += [f"  - {s}" for s in result.signals]
    lines += ["", "Recommended next steps (read-only first):"]
    lines += [f"  {i}. {cmd}" for i, cmd in enumerate(result.read_only_commands, 1)]
    lines += ["", "Human review:"]
    lines += [f"  - {step}" for step in result.recommended_next_steps]
    lines += [
        "",
        "Human approval: REQUIRED — no action was executed.",
        "This agent is read-only by design. See docs/SECURITY.md.",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="orbitronops-triage",
        description="Read-only incident triage agent (OrbitronOps demo).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    triage = sub.add_parser("triage", help="Triage one incident JSON file.")
    triage.add_argument("file", help="Path to an incident JSON file. See examples/.")
    triage.add_argument("--format", choices=["text", "json"], default="text")
    triage.add_argument(
        "--audit-file",
        default="audit/audit.jsonl",
        help="Where to append the audit record (default: audit/audit.jsonl).",
    )
    triage.add_argument(
        "--no-audit", action="store_true", help="Do not write an audit record."
    )

    args = parser.parse_args(argv)

    if args.command == "triage":
        try:
            data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(f"error: file not found: {args.file}", file=sys.stderr)
            return 2
        except json.JSONDecodeError as exc:
            print(f"error: invalid JSON in {args.file}: {exc}", file=sys.stderr)
            return 2

        incident = Incident.from_dict(data)
        result = analyse(incident)

        if not args.no_audit:
            append_audit(
                args.audit_file,
                "triage",
                {
                    "incident_id": result.incident_id,
                    "service": result.service,
                    "severity": result.severity,
                    "probable_cause": result.probable_cause,
                    "confidence": result.confidence,
                    "action_executed": False,
                },
            )

        if args.format == "json":
            print(json.dumps(result.to_dict(), indent=2))
        else:
            print(_render_text(result))
            if not args.no_audit:
                print(f"\nAudit record written to: {args.audit_file}")
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
