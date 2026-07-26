"""Read-only Intake V6 selected_layer_refs historical impact audit.

Uses canonical derivation from commit 9315fcf (`derive_selected_layer_refs_from_setup`).
No database writes. Opens SQLite in read-only URI mode only.
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from schemas.intake_v4 import IntakeV4LayerRoleSetup  # noqa: E402
from services.intake_v4_layer_role_service import (  # noqa: E402
    derive_selected_layer_refs_from_setup,
    selected_layer_refs_runtime_state,
)

FIXTURE_ID = "22ef834d-f2d0-453b-a7a7-118928c98a39"
OUTPUT_DIR = Path(__file__).resolve().parent
KNOWN_NON_DERIVABLE_ROLES = {
    "mounting_hole",
    "support",
    "mounting",
    "illumination",
    "back",
    "side",
    "unknown",
    "reference",
    "ignored",
}
MAPPED_ROLES = {"face", "printed_artwork", "logo"}


def _resolve_db_path() -> Path | None:
    database_url = os.environ.get("DATABASE_URL", "").strip()
    candidates: list[Path] = []
    if database_url and "sqlite" in database_url:
        raw = database_url.split("///", 1)[-1]
        path = Path(raw)
        if not path.is_absolute():
            path = BACKEND_ROOT / raw
        candidates.append(path)
    candidates.append(BACKEND_ROOT / "dev.db")
    for path in candidates:
        if path.exists():
            return path.resolve()
    return None


def _ref_list(refs: list[Any] | None) -> list[dict[str, Any]]:
    if not isinstance(refs, list):
        return []
    out: list[dict[str, Any]] = []
    for item in refs:
        if isinstance(item, dict):
            out.append(
                {
                    "layer_id": str(item.get("layer_id") or "").strip(),
                    "role": str(item.get("role") or "").strip(),
                    "confirmed": item.get("confirmed") is True,
                }
            )
    return out


def _layer_ids_from_setup(setup_raw: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for layer in setup_raw.get("layers") or []:
        if not isinstance(layer, dict):
            continue
        layer_id = str(layer.get("layer_id") or "").strip()
        if layer_id:
            ids.add(layer_id)
    return ids


def _confirmed_roles(setup_raw: dict[str, Any]) -> list[str]:
    roles: list[str] = []
    for layer in setup_raw.get("layers") or []:
        if not isinstance(layer, dict):
            continue
        if layer.get("confirmation_state") != "confirmed":
            continue
        role = str(layer.get("confirmed_role") or "").strip().lower()
        if role:
            roles.append(role)
    return roles


def _classify(
    *,
    setup_raw: dict[str, Any] | None,
    persisted: list[dict[str, Any]] | None,
    derived: list[dict[str, Any]],
    runtime: dict[str, Any],
) -> str:
    if not isinstance(setup_raw, dict) or not setup_raw.get("layers"):
        return "INCOMPLETE_SETUP"
    confirmation = str(setup_raw.get("confirmation_status") or "").strip().lower()
    if confirmation != "complete":
        return "INCOMPLETE_SETUP"
    if runtime.get("status") == "ambiguous":
        return "AMBIGUOUS_LAYER_IDENTITY"
    confirmed_roles = _confirmed_roles(setup_raw)
    if any(role not in MAPPED_ROLES and role not in KNOWN_NON_DERIVABLE_ROLES for role in confirmed_roles):
        return "UNKNOWN_ROLE"
    if "logo" in confirmed_roles:
        # legacy alias present in canonical setup
        if "printed_artwork" not in confirmed_roles and persisted is None:
            pass  # classification may still be MISSING; tag via counts separately
    persisted_norm = persisted or []
    if persisted_norm:
        layer_ids = [ref["layer_id"] for ref in persisted_norm if ref.get("layer_id")]
        if len(layer_ids) != len(set(layer_ids)):
            return "DUPLICATE_REFS"
        source_ids = _layer_ids_from_setup(setup_raw)
        if any(ref["layer_id"] not in source_ids for ref in persisted_norm if ref.get("layer_id")):
            return "INVALID_REF_TARGET"
    if not derived and not persisted_norm:
        return "EMPTY_COMPLETE_SETUP"
    if not persisted_norm and derived:
        if any(role == "printed_artwork" for role in confirmed_roles):
            return "PRINTED_ARTWORK_LOGO_GAP"
        return "MISSING_PERSISTED_REFS"
    if persisted_norm and derived and persisted_norm != derived:
        return "STALE_PERSISTED_REFS"
    if persisted_norm == derived:
        return "MATCH"
    if not derived and persisted_norm:
        return "STALE_PERSISTED_REFS"
    return "UNKNOWN_ROLE"


def _risk(
    classification: str,
    *,
    has_printed_artwork: bool,
    downstream: dict[str, bool],
) -> str:
    if classification in {"AMBIGUOUS_LAYER_IDENTITY", "UNKNOWN_ROLE", "DUPLICATE_REFS", "INVALID_REF_TARGET"}:
        return "UNKNOWN" if classification == "UNKNOWN_ROLE" else "HIGH"
    if classification == "STALE_PERSISTED_REFS" and any(downstream.values()):
        return "HIGH"
    if classification in {"MISSING_PERSISTED_REFS", "PRINTED_ARTWORK_LOGO_GAP", "EMPTY_COMPLETE_SETUP"}:
        if any(downstream.values()):
            return "HIGH"
        if has_printed_artwork:
            return "MEDIUM"
        return "LOW"
    if classification == "MATCH":
        return "LOW"
    if classification == "INCOMPLETE_SETUP":
        return "LOW"
    return "UNKNOWN"


def _downstream_exposure(conn: sqlite3.Connection, workspace_id: str) -> dict[str, bool]:
    snap_count = conn.execute(
        "SELECT COUNT(*) FROM quote_snapshots_v2 WHERE workspace_id = ?",
        (workspace_id,),
    ).fetchone()[0]
    quote_count = conn.execute(
        """
        SELECT COUNT(*) FROM quotes q
        INNER JOIN quote_snapshots_v2 s ON s.quote_id = q.id
        WHERE s.workspace_id = ?
        """,
        (workspace_id,),
    ).fetchone()[0]
    order_count = conn.execute(
        """
        SELECT COUNT(*) FROM orders o
        INNER JOIN quote_snapshots_v2 s ON s.id = o.quote_snapshot_v2_id
        WHERE s.workspace_id = ?
        """,
        (workspace_id,),
    ).fetchone()[0]
    exec_count = conn.execute(
        """
        SELECT COUNT(*) FROM execution_plan e
        INNER JOIN orders o ON o.id = e.order_id
        INNER JOIN quote_snapshots_v2 s ON s.id = o.quote_snapshot_v2_id
        WHERE s.workspace_id = ?
        """,
        (workspace_id,),
    ).fetchone()[0]
    return {
        "quote_snapshot_v2": snap_count > 0,
        "quote": quote_count > 0,
        "order": order_count > 0,
        "execution_plan": exec_count > 0,
        "product_truth_promotion": False,
    }


def _printed_artwork_details(payload: dict[str, Any], setup_raw: dict[str, Any]) -> dict[str, Any]:
    layers = setup_raw.get("layers") if isinstance(setup_raw, dict) else []
    confirmed_printed = 0
    for layer in layers or []:
        if not isinstance(layer, dict):
            continue
        if layer.get("confirmation_state") == "confirmed" and str(layer.get("confirmed_role") or "").lower() == "printed_artwork":
            confirmed_printed += 1
    svg = payload.get("svg") if isinstance(payload.get("svg"), dict) else {}
    persisted = _ref_list(svg.get("selected_layer_refs") if isinstance(svg.get("selected_layer_refs"), list) else None)
    persisted_logo = sum(1 for ref in persisted if ref.get("role") == "vector_logo")
    bindings = payload.get("product_system_bindings") or payload.get("linked_template_bindings") or []
    binding_count = len(bindings) if isinstance(bindings, list) else 0
    finish_setup = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    artwork_finishes = finish_setup.get("artwork_finishes") if isinstance(finish_setup.get("artwork_finishes"), list) else []
    logo_finish_confirmed = any(
        isinstance(item, dict) and item.get("confirmed") is True for item in artwork_finishes
    )
    return {
        "confirmed_printed_artwork_layers": confirmed_printed,
        "persisted_vector_logo_refs": persisted_logo,
        "linked_template_binding_count": binding_count,
        "logo_finish_confirmed": logo_finish_confirmed,
    }


def run_audit() -> dict[str, Any]:
    db_path = _resolve_db_path()
    if db_path is None:
        return {"status": "BLOCKED_BY_DATA_ACCESS", "reason": "No readable SQLite database found"}

    started = time.perf_counter()
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row

    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "intake_v6_workspaces" not in tables:
        return {"status": "BLOCKED_BY_DATA_ACCESS", "reason": "intake_v6_workspaces table missing"}

    rows = conn.execute(
        """
        SELECT id, workspace_code, template_code, status, readiness_status, payload_json, archived_at
        FROM intake_v6_workspaces
        """
    ).fetchall()

    counts = {
        "total_workspaces": len(rows),
        "with_layer_role_setup": 0,
        "complete_confirmed_setup": 0,
        "with_persisted_selected_layer_refs": 0,
        "missing_selected_layer_refs": 0,
        "empty_persisted_refs": 0,
        "confirmed_face_workspaces": 0,
        "confirmed_printed_artwork_workspaces": 0,
        "legacy_logo_alias_workspaces": 0,
        "unknown_unmapped_role_workspaces": 0,
        "derivation_matches_persisted": 0,
        "derivation_differs_from_persisted": 0,
        "duplicate_persisted_refs": 0,
        "invalid_ref_targets": 0,
        "ambiguous_layer_identity": 0,
    }
    classification_counts: dict[str, int] = {}
    risk_counts: dict[str, int] = {}
    representative_rows: list[dict[str, Any]] = []
    high_risk_rows: list[dict[str, Any]] = []
    printed_artwork_summary = {
        "workspaces_with_confirmed_printed_artwork": 0,
        "derive_vector_logo": 0,
        "lack_persisted_logo_refs": 0,
        "with_linked_template_binding": 0,
        "logo_finish_confirmed": 0,
        "remain_blocked_estimate": 0,
        "letter_only_misclassification_estimate": 0,
    }
    fixture_result: dict[str, Any] | None = None

    for row in rows:
        workspace_id = str(row["id"])
        try:
            payload = json.loads(row["payload_json"] or "{}")
        except json.JSONDecodeError:
            payload = {}
        setup_raw = payload.get("layer_role_setup") if isinstance(payload.get("layer_role_setup"), dict) else None
        svg = payload.get("svg") if isinstance(payload.get("svg"), dict) else {}
        persisted_raw = svg.get("selected_layer_refs") if isinstance(svg.get("selected_layer_refs"), list) else None
        persisted = _ref_list(persisted_raw) if persisted_raw is not None else None

        if isinstance(setup_raw, dict) and setup_raw.get("layers"):
            counts["with_layer_role_setup"] += 1
        else:
            continue

        confirmation = str(setup_raw.get("confirmation_status") or "").strip().lower()
        confirmed_roles = _confirmed_roles(setup_raw)
        has_face = "face" in confirmed_roles
        has_printed = "printed_artwork" in confirmed_roles
        has_legacy_logo = "logo" in confirmed_roles
        has_unknown = any(r not in MAPPED_ROLES and r not in KNOWN_NON_DERIVABLE_ROLES for r in confirmed_roles)

        if confirmation == "complete":
            counts["complete_confirmed_setup"] += 1
        if has_face:
            counts["confirmed_face_workspaces"] += 1
        if has_printed:
            counts["confirmed_printed_artwork_workspaces"] += 1
        if has_legacy_logo:
            counts["legacy_logo_alias_workspaces"] += 1
        if has_unknown:
            counts["unknown_unmapped_role_workspaces"] += 1

        if persisted_raw is not None:
            counts["with_persisted_selected_layer_refs"] += 1
            if len(persisted or []) == 0:
                counts["empty_persisted_refs"] += 1
        else:
            counts["missing_selected_layer_refs"] += 1

        derived: list[dict[str, Any]] = []
        runtime: dict[str, Any] = {"status": "missing", "refs": []}
        try:
            setup = IntakeV4LayerRoleSetup.model_validate(setup_raw)
            runtime = selected_layer_refs_runtime_state(setup)
            derived = [
                {
                    "layer_id": ref.layer_id,
                    "role": ref.role,
                    "confirmed": ref.confirmed,
                }
                for ref in derive_selected_layer_refs_from_setup(setup)
            ]
        except Exception:
            runtime = {"status": "error", "refs": []}

        classification = _classify(
            setup_raw=setup_raw,
            persisted=persisted,
            derived=derived,
            runtime=runtime,
        )
        classification_counts[classification] = classification_counts.get(classification, 0) + 1

        if classification == "DUPLICATE_REFS":
            counts["duplicate_persisted_refs"] += 1
        if classification == "INVALID_REF_TARGET":
            counts["invalid_ref_targets"] += 1
        if classification == "AMBIGUOUS_LAYER_IDENTITY":
            counts["ambiguous_layer_identity"] += 1
        if classification == "MATCH":
            counts["derivation_matches_persisted"] += 1
        elif classification in {
            "STALE_PERSISTED_REFS",
            "MISSING_PERSISTED_REFS",
            "PRINTED_ARTWORK_LOGO_GAP",
            "EMPTY_COMPLETE_SETUP",
        }:
            counts["derivation_differs_from_persisted"] += 1

        downstream = _downstream_exposure(conn, workspace_id)
        risk = _risk(classification, has_printed_artwork=has_printed, downstream=downstream)
        risk_counts[risk] = risk_counts.get(risk, 0) + 1

        pa = _printed_artwork_details(payload, setup_raw)
        if pa["confirmed_printed_artwork_layers"] > 0:
            printed_artwork_summary["workspaces_with_confirmed_printed_artwork"] += 1
            if any(ref.get("role") == "vector_logo" for ref in derived):
                printed_artwork_summary["derive_vector_logo"] += 1
            if pa["persisted_vector_logo_refs"] == 0:
                printed_artwork_summary["lack_persisted_logo_refs"] += 1
            if pa["linked_template_binding_count"] > 0:
                printed_artwork_summary["with_linked_template_binding"] += 1
            if pa["logo_finish_confirmed"]:
                printed_artwork_summary["logo_finish_confirmed"] += 1
            if not pa["logo_finish_confirmed"] or pa["linked_template_binding_count"] == 0:
                printed_artwork_summary["remain_blocked_estimate"] += 1
            if persisted and not any(ref.get("role") == "vector_logo" for ref in persisted) and has_printed:
                printed_artwork_summary["letter_only_misclassification_estimate"] += 1

        summary_row = {
            "workspace_id": workspace_id,
            "workspace_code": row["workspace_code"],
            "template_code": row["template_code"],
            "setup_state": confirmation,
            "persisted_ref_count": len(persisted or []),
            "derived_ref_count": len(derived),
            "persisted_roles": sorted({ref["role"] for ref in (persisted or []) if ref.get("role")}),
            "derived_roles": sorted({ref["role"] for ref in derived if ref.get("role")}),
            "difference": classification,
            "classification": classification,
            "risk": risk,
            "downstream": downstream,
            "readiness_status": row["readiness_status"],
            "workspace_status": row["status"],
        }
        if len(representative_rows) < 20 and classification != "MATCH":
            representative_rows.append(summary_row)
        if risk == "HIGH":
            high_risk_rows.append(summary_row)

        if workspace_id == FIXTURE_ID:
            fixture_result = {
                "workspace_id": workspace_id,
                "workspace_code": row["workspace_code"],
                "persisted_selected_layer_refs": persisted_raw,
                "derived_refs": derived,
                "classification": classification,
                "risk": risk,
                "readiness_status": row["readiness_status"],
                "row_mutated": False,
            }

    elapsed = round(time.perf_counter() - started, 3)

    if fixture_result is None:
        fixture_result = {"workspace_id": FIXTURE_ID, "found_in_database": False}

    return {
        "status": "OK",
        "audit_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "database": {
            "engine": "SQLite",
            "path": str(db_path),
            "environment": os.environ.get("APP_ENV", "unknown"),
            "identity": "local development (backend/dev.db)",
            "read_only_mode": True,
            "active_use_unknown": True,
            "backup_known": "dev.db.forensic.before_product_cleanup_20260630.db exists alongside dev.db",
        },
        "execution": {"duration_seconds": elapsed, "rows_audited": len(rows)},
        "counts": counts,
        "classification_counts": classification_counts,
        "risk_counts": risk_counts,
        "printed_artwork_summary": printed_artwork_summary,
        "fixture_result": fixture_result,
        "representative_rows": representative_rows,
        "high_risk_rows": high_risk_rows,
    }


def main() -> None:
    result = run_audit()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUTPUT_DIR / "impact_counts.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (OUTPUT_DIR / "representative_rows.json").write_text(
        json.dumps(result.get("representative_rows", []), indent=2),
        encoding="utf-8",
    )
    (OUTPUT_DIR / "high_risk_rows.json").write_text(
        json.dumps(result.get("high_risk_rows", []), indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"status": result.get("status"), "rows": result.get("execution", {}).get("rows_audited")}, indent=2))


if __name__ == "__main__":
    main()
