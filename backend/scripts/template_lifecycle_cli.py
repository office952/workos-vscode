#!/usr/bin/env python3
"""Template Lifecycle Control CLI.

Usage (from backend/ with venv + DATABASE_URL):

  python scripts/template_lifecycle_cli.py inspect TPL-VOLUMETRIC-LETTERS_v2
  python scripts/template_lifecycle_cli.py validate
  python scripts/template_lifecycle_cli.py validate --template TPL-VOLUMETRIC-LOGO_v1
  python scripts/template_lifecycle_cli.py impact TPL-ACM-BOXED-MOUNTING-SUPPORT_v1

Exit codes:
  inspect/impact: 0 always (unless hard error)
  validate: 0 if ok, 2 if activation-required stages BLOCKED for active roots
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))


def _ensure_env() -> None:
    os.environ.setdefault("APP_ENV", "development")
    os.environ.setdefault("ENVIRONMENT", "development")
    if not os.environ.get("DATABASE_URL"):
        db_path = (BACKEND_ROOT / "dev.db").resolve().as_posix()
        os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    os.environ.setdefault("JWT_SECRET_KEY", "local-dev-secret-not-for-production")


def _print_json(payload: object) -> None:
    text = json.dumps(payload, indent=2, ensure_ascii=False)
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    sys.stdout.buffer.write((text + "\n").encode("utf-8", errors="replace"))


def _print_ci_summary(result: object) -> None:
    """Human-readable CI summary (same payload as JSON; no duplicate rules)."""
    data = result.model_dump(mode="json") if hasattr(result, "model_dump") else dict(result)  # type: ignore[arg-type]
    items = list(data.get("items") or [])
    pass_n = sum(1 for i in items if i.get("lifecycle_status") in {"PASS", "WIRED", "VALIDATED"})
    owner_n = sum(1 for i in items if i.get("lifecycle_status") == "OWNER_GATE_REQUIRED")
    blocked_n = sum(1 for i in items if i.get("lifecycle_status") == "BLOCKED")
    lines = [
        "Template Lifecycle Validation",
        f"Validated: {data.get('checked', 0)}",
        f"Pass-like: {pass_n}",
        f"Owner gate required: {owner_n}",
        f"Blocked: {blocked_n}",
        "",
    ]
    if data.get("ok"):
        lines.append("All required lifecycle gates passed.")
        remaining_gates = sorted(
            {
                w
                for i in items
                for w in (i.get("warning_codes") or [])
                if w.endswith("_OWNER_GATE") or w in {"CPP_OWNER_GATE", "NO_PARALLEL_TASKING"}
            }
        )
        if remaining_gates:
            lines.append(f"Owner gates / warnings remain: {', '.join(remaining_gates)}")
        lines.append("Exit code: 0")
    else:
        lines.append("BLOCKED")
        for reason in data.get("fail_reasons") or []:
            lines.append(f"- {reason}")
        for item in items:
            if item.get("lifecycle_status") != "BLOCKED" and not item.get("blocking_codes"):
                continue
            lines.append(item.get("template_code") or "?")
            for code in item.get("blocking_codes") or []:
                lines.append(f"- {code}")
        lines.append("Exit code: 2")
    text = "\n".join(lines) + "\n"
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
    except Exception:
        pass
    sys.stdout.buffer.write(text.encode("utf-8", errors="replace"))


async def _run(args: argparse.Namespace) -> int:
    from core.database import db_manager
    from services.template_lifecycle_control_service import TemplateLifecycleControlService

    await db_manager.ensure_initialized()
    if not db_manager.async_session_maker:
        raise RuntimeError("No async_session_maker — check DATABASE_URL / backend/dev.db.")

    async with db_manager.async_session_maker() as session:
        service = TemplateLifecycleControlService(session)
        if args.command == "inspect":
            result = await service.inspect(args.template_code)
            _print_json(result.model_dump(mode="json"))
            return 0
        if args.command == "impact":
            result = await service.build_impact(args.template_code)
            _print_json(result.model_dump(mode="json"))
            return 0
        if args.command == "validate":
            codes = list(args.template) if args.template else None
            result = await service.validate(template_codes=codes, active_only=not args.all)
            if getattr(args, "ci", False):
                _print_ci_summary(result)
            else:
                _print_json(result.model_dump(mode="json"))
            return 0 if result.ok else 2
        raise SystemExit(f"Unknown command: {args.command}")


def main() -> int:
    # Windows consoles often default to cp1252 — lifecycle JSON may include RO text.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    parser = argparse.ArgumentParser(
        prog="template-lifecycle",
        description="WorkOS Template Lifecycle Control System V1",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    inspect_p = sub.add_parser("inspect", help="Inspect readiness + impact for one template")
    inspect_p.add_argument("template_code")

    impact_p = sub.add_parser("impact", help="Impact / reverse dependency map for one template")
    impact_p.add_argument("template_code")

    validate_p = sub.add_parser("validate", help="Validate active (or listed) templates for CI")
    validate_p.add_argument(
        "--template",
        action="append",
        default=None,
        help="Template code (repeatable). Default: active root-offerable templates.",
    )
    validate_p.add_argument(
        "--all",
        action="store_true",
        help="Include all db_active templates (not only offerable roots).",
    )
    validate_p.add_argument(
        "--ci",
        action="store_true",
        help="Print human-readable CI summary (same rules/service; exit 2 on required BLOCKED).",
    )

    args = parser.parse_args()
    _ensure_env()
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
