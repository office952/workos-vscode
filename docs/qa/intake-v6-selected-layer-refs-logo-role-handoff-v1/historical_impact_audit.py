"""Read-only impact audit for Intake V6 selected_layer_refs handoff.

Does not mutate any workspace rows.
"""

from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

from services.intake_v4_layer_role_service import selected_layer_refs_runtime_state
from schemas.intake_v4 import IntakeV4LayerRoleSetup


def _resolve_db_path() -> Path | None:
    database_url = os.environ.get("DATABASE_URL", "")
    if "sqlite" not in database_url:
        return None
    raw = database_url.split("///", 1)[-1]
    path = Path(raw)
    if not path.is_absolute():
        path = Path(__file__).resolve().parents[2] / raw
    return path if path.exists() else None


def main() -> None:
    db_path = _resolve_db_path()
    if db_path is None:
        print(json.dumps({"status": "NOT_RUN", "reason": "sqlite DATABASE_URL unavailable or file missing"}))
        return

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if "intake_v6_workspaces" not in tables:
        print(json.dumps({"status": "NOT_RUN", "reason": "intake_v6_workspaces table missing"}))
        return

    rows = conn.execute("SELECT id, payload_json FROM intake_v6_workspaces").fetchall()
    with_layer_setup = 0
    missing_persisted_refs = 0
    with_printed_artwork = 0
    recompute_differs = 0
    unknown_roles = 0
    fixture_id = "22ef834d-f2d0-453b-a7a7-118928c98a39"
    fixture_persisted_refs = None

    for row in rows:
        payload = json.loads(row["payload_json"] or "{}")
        setup_raw = payload.get("layer_role_setup")
        if not isinstance(setup_raw, dict) or not setup_raw.get("layers"):
            continue
        with_layer_setup += 1
        svg = payload.get("svg") if isinstance(payload.get("svg"), dict) else {}
        persisted = svg.get("selected_layer_refs") if isinstance(svg.get("selected_layer_refs"), list) else None
        if not persisted:
            missing_persisted_refs += 1
        for layer in setup_raw.get("layers") or []:
            if not isinstance(layer, dict):
                continue
            role = str(layer.get("confirmed_role") or "").strip().lower()
            if role == "printed_artwork" and layer.get("confirmation_state") == "confirmed":
                with_printed_artwork += 1
            if role and role not in {"face", "printed_artwork", "logo", "ignored"} and layer.get("confirmation_state") == "confirmed":
                if role not in {"mounting_hole", "support", "mounting", "illumination", "back", "side", "unknown"}:
                    unknown_roles += 1
        try:
            setup = IntakeV4LayerRoleSetup.model_validate(setup_raw)
            runtime = selected_layer_refs_runtime_state(setup)
            if runtime["status"] == "confirmed":
                derived = [item.model_dump(mode="json") for item in runtime["refs"]]
                if derived != (persisted or []):
                    recompute_differs += 1
        except Exception:
            pass
        if str(row["id"]) == fixture_id:
            fixture_persisted_refs = persisted

    print(
        json.dumps(
            {
                "status": "OK",
                "db_path": str(db_path),
                "workspaces_total": len(rows),
                "with_layer_role_setup": with_layer_setup,
                "missing_selected_layer_refs": missing_persisted_refs,
                "confirmed_printed_artwork_layers": with_printed_artwork,
                "recomputed_projection_differs_from_persisted": recompute_differs,
                "confirmed_unknown_roles": unknown_roles,
                "fixture_id": fixture_id,
                "fixture_persisted_selected_layer_refs": fixture_persisted_refs,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
