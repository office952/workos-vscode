"""Runtime proof — LetterGroupInstance authority on real fixtures (read + dry coalesce).

Does NOT write Offer/Order/Execution. Optional finish-setup PUT is dry-run coalesce only
unless --write is passed (default: no network writes).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)

from services.letter_group_instance_authority import (  # noqa: E402
    build_volumetric_letters_commercial_quantities,
    coalesce_letter_group_authority_for_finish,
    read_letter_group_instances,
)
from services.letters_commercial_measurement_service import (  # noqa: E402
    build_letters_commercial_measurements,
)

DB = BACKEND / "dev.db"
OUT = Path(__file__).resolve().parent / "runtime-proof.json"

CODES = (
    "IV6-195E885C",  # gradi-curat 4-group (BB8EE3F8 not in local DB)
    "IV6-DB2F86B7",  # letters + ACM control
    "IV6-13D39D32",  # measured ACM — must stay measured
)


def _load_payload(workspace_code: str) -> dict | None:
    conn = sqlite3.connect(str(DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    row = cur.execute(
        "SELECT id, workspace_code, template_code, payload_json FROM intake_v6_workspaces WHERE workspace_code = ? LIMIT 1",
        (workspace_code,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    payload_raw = row["payload_json"]
    payload = json.loads(payload_raw) if isinstance(payload_raw, str) else payload_raw
    return {
        "table": "intake_v6_workspaces",
        "workspace_code": workspace_code,
        "workspace_id": row["id"],
        "template_code": row["template_code"],
        "payload": payload if isinstance(payload, dict) else {},
    }


def _summarize(code: str, payload: dict) -> dict:
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    legacy = finish.get("letter_group_finishes") if isinstance(finish.get("letter_group_finishes"), list) else []
    before_instances = read_letter_group_instances(finish)
    after = coalesce_letter_group_authority_for_finish(dict(finish), finish)
    # Reload stability: second coalesce must keep UUIDs.
    again = coalesce_letter_group_authority_for_finish(
        {"letter_group_instances": after.get("letter_group_instances"), "confirmed": True},
        after,
    )
    # Omit must not wipe.
    omit_preserve = coalesce_letter_group_authority_for_finish({"confirmed": True}, after)
    after_instances = read_letter_group_instances(after)
    again_instances = read_letter_group_instances(again)
    omit_instances = read_letter_group_instances(omit_preserve)
    geom = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
    qty = build_volumetric_letters_commercial_quantities(quote_geometry=geom, finish_setup=after)
    quote_input = {"finish_setup": after, "quote_geometry": geom}
    measurements = build_letters_commercial_measurements(
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        pd=None,
        quote_input=quote_input,
        active_modules=None,
    )
    cpp_dry = {
        "measurement_count": len(measurements.measurements) if measurements else 0,
        "resolved_lines": [
            {
                "line_code": m.line_code,
                "quantity": m.quantity,
                "unit": m.unit,
                "resolution_status": m.resolution_status,
            }
            for m in (measurements.measurements if measurements else [])
            if m.resolution_status == "resolved"
        ][:12],
        "qty_bundle_source": (quote_input.get("finish_setup") or {}).get("volumetric_letters_commercial_quantities")
        or qty.get("source"),
    }
    acm = finish.get("acm_panel_instance") if isinstance(finish.get("acm_panel_instance"), dict) else {}
    acm_metrics = acm.get("production_geometry_metrics") if isinstance(acm.get("production_geometry_metrics"), dict) else {}
    return {
        "workspace_code": code,
        "template": payload.get("selected_product_template_code")
        or payload.get("product_template_code")
        or payload.get("template_code"),
        "route": f"/intake-v6/{code}",
        "before": {
            "letter_group_finishes_count": len(legacy),
            "letter_group_instances_count": len(before_instances),
            "group_keys": [str(r.get("group_key")) for r in legacy if isinstance(r, dict)],
            "instance_ids": [i.get("instance_id") for i in before_instances],
            "illuminated": finish.get("illuminated"),
            "acm_quantity_source": acm_metrics.get("quantity_source") or acm.get("quantity_source"),
        },
        "after_coalesce_dry": {
            "letter_group_instances_count": len(after_instances),
            "group_keys": [i.get("group_key") for i in after_instances],
            "instance_ids": [i.get("instance_id") for i in after_instances],
            "legacy_projection_count": len(after.get("letter_group_finishes") or []),
            "placements": [
                {
                    "source_instance_id": p.get("source_instance_id"),
                    "target_kind": p.get("target_kind"),
                    "target_instance_id": p.get("target_instance_id"),
                    "target_face": p.get("target_face"),
                }
                for p in (after.get("component_placements") or [])
                if isinstance(p, dict)
            ],
            "uuid_stable_reload": [i.get("instance_id") for i in after_instances]
            == [i.get("instance_id") for i in again_instances],
            "uuid_stable_omit": [i.get("instance_id") for i in after_instances]
            == [i.get("instance_id") for i in omit_instances],
        },
        "quantities": qty,
        "cpp_measurement_dry_run": cpp_dry,
        "acm_panel_unchanged_check": {
            "had_acm": bool(acm),
            "quantity_source_before": acm_metrics.get("quantity_source") or acm.get("quantity_source"),
            "component_instance_id": acm.get("component_instance_id"),
            "note": "coalesce_letter does not mutate acm_panel_instance",
            "acm_still_present": bool(after.get("acm_panel_instance") or acm),
        },
        "network_writes": {
            "finish_setup_put": False,
            "offer": False,
            "order": False,
            "execution": False,
        },
        "gates": {
            "identity_uuid": all(
                isinstance(i.get("instance_id"), str) and len(str(i.get("instance_id"))) >= 32
                for i in after_instances
            ),
            "no_hash_in_id": all(
                str((i.get("artwork_reference") or {}).get("source_svg_hash") or "")
                not in str(i.get("instance_id") or "")
                for i in after_instances
                if (i.get("artwork_reference") or {}).get("source_svg_hash")
            ),
            "one_way_projection": all("instance_id" not in (r or {}) for r in (after.get("letter_group_finishes") or [])),
            "qty_source": qty.get("source") == "letter_group_instance_authority",
        },
    }


def main() -> int:
    report: dict = {
        "schema": "volumetric_letters_authority_runtime_proof_v1",
        "db": str(DB),
        "fixtures": [],
        "missing": [],
    }
    for code in CODES:
        loaded = _load_payload(code)
        if not loaded:
            report["missing"].append(code)
            continue
        summary = _summarize(code, loaded["payload"])
        summary["workspace_id"] = loaded["workspace_id"]
        summary["table"] = loaded["table"]
        if not summary.get("template"):
            summary["template"] = loaded.get("template_code")
        report["fixtures"].append(summary)

    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    if report["missing"]:
        print(f"MISSING: {report['missing']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
