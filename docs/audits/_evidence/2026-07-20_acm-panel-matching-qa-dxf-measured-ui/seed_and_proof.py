"""QA seed + runtime proof — matching double-fold DXF measured UI (no IV6 mutation)."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
os.environ.setdefault("JWT_SECRET_KEY", "local-dev-secret-not-for-production")

FIXTURE_DXF = BACKEND / "tests" / "fixtures" / "acm_panel_dxf" / "2-pliuri-100x30.dxf"
IV6_ID = "a7b0162b-dc91-467f-aa24-c1279fb3a073"
IV6_CODE = "IV6-DB2F86B7"
OUT = Path(__file__).resolve().parent
TOL = 5e-5

COMPONENT_ID = "acm_qa_double_fold_2000x300"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _qa_finish_setup() -> dict:
    panels = [
        {
            "panel_id": "p1",
            "order": 1,
            "width_mm": 2000,
            "height_mm": 300,
            "position": {"x_mm": 0, "y_mm": 0},
        }
    ]
    inst = {
        "schema": "acm_panel_component_instance_v1",
        "component_instance_id": COMPONENT_ID,
        "component_template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        "intake_geometry_role_adapter": "SUPPORT_CONTOUR",
        "role_status": "confirmed",
        "association_status": "confirmed",
        "technical_configuration_status": "confirmed",
        "composition_status": "unconfirmed",
        "capabilities": {"active": ["boxed_returns", "segmented_panels"], "inactive": []},
        "geometry": {
            "contour_id": "qa_contour",
            "element_id": "qa_el",
            "geometry_hash": "qa_df_2000x300",
            "width_mm": 2000,
            "height_mm": 300,
            "area_mm2": 600000,
            "perimeter_mm": 4600,
            "panels": panels,
            "joints": [],
        },
        "configuration": {
            "acm_thickness_mm": 3,
            "fold_count": 2,
            "l1_mm": 100,
            "l2_mm": 30,
            "finished_depth_mm": 130,
            "internal_frame_enabled": False,
            "service_corner": None,
            "field_authority": {
                "panel_geometry": "operator_confirmed",
                "fold_count": "operator_confirmed",
                "l1_mm": "operator_confirmed",
                "l2_mm": "operator_confirmed",
                "finished_depth_mm": "operator_confirmed",
                "acm_thickness_mm": "operator_confirmed",
            },
            "field_class": {
                "panel_geometry": "critical",
                "fold_count": "critical",
                "l1_mm": "critical",
                "l2_mm": "critical",
            },
        },
        "relations": [],
        "svg_source_hash": "qa_df_hash",
        "updated_at": _utcnow(),
    }
    return {
        # confirmed=true avoids Review selectorPendingSave always-true autosave that can race-wipe ACM.
        "confirmed": True,
        "acm_panel_domain_action": "upsert",
        "acm_panel_instance": inst,
        "svg_support_selection": {
            "schema": "svg_support_selection_v1",
            "status": "confirmed",
            "role": "SUPPORT_CONTOUR",
            "acm_panel_instance": deepcopy(inst),
            "association_status": "confirmed",
            "technical_configuration_status": "confirmed",
        },
        "segmented_background": {
            "schema": "segmented_background_v1",
            "status": "CONFIRMED",
            "operator_confirmed": True,
            "panels": panels,
            "joints": [],
            "assembly_dimensions": {"width_mm": 2000, "height_mm": 300},
        },
        "mounting_solution": {
            "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
            "configuration": {
                "panel_width_mm": 2000,
                "panel_height_mm": 300,
                "fold_sides": "all",
                "return_depth_mm": 100,
                "acm_panel_instance": deepcopy(inst),
            },
        },
        "mounting_system": "acm_panel",
    }


def _preview_digest(preview: dict | None) -> dict:
    preview = preview or {}
    geom = preview.get("geometry_summary") or {}
    return {
        "status": preview.get("status"),
        "face_area_m2": geom.get("face_area_m2"),
        "cut_length_m": geom.get("cut_length_m"),
        "fold_length_m": geom.get("fold_length_m"),
        "v_groove_l1_ml": geom.get("v_groove_l1_ml"),
        "v_groove_l2_ml": geom.get("v_groove_l2_ml"),
        "v_groove_total_ml": geom.get("v_groove_total_ml"),
        "path_measurement_status": geom.get("path_measurement_status"),
        "path_measurement_source": geom.get("path_measurement_source"),
        "final_eligibility": preview.get("final_eligibility"),
        "offer_eligibility": preview.get("offer_eligibility"),
        "execution_eligibility": preview.get("execution_eligibility"),
        "warnings": preview.get("warnings"),
        "blockers": preview.get("blockers"),
        "lines": [
            {
                "code": ln.get("code"),
                "quantity": ln.get("quantity"),
                "unit": ln.get("unit"),
            }
            for ln in (preview.get("lines") or [])
            if str(ln.get("code") or "").startswith("acm_")
        ],
    }


async def main() -> None:
    from schemas.auth import UserResponse
    from schemas.intake_v6 import IntakeV6WorkspaceCreateRequest
    from services.acm_production_geometry_attachment import (
        compute_config_fingerprint,
        upload_and_optionally_bind_production_dxf,
    )
    from services.database import initialize_database
    from core.database import db_manager
    from services.intake_v6_priced_quote_dry_run_service import build_intake_v6_priced_quote_dry_run
    from services.intake_v6_workspace_service import (
        _get_record_or_404,
        _json_loads,
        _parse_payload,
        _persist_payload,
        create_intake_v6_workspace,
    )

    assert FIXTURE_DXF.is_file(), f"missing {FIXTURE_DXF}"
    user = UserResponse(
        id="qa-measured-ui",
        email="qa-measured-ui@workos.local",
        name="QA Measured UI",
        role="admin",
        last_login=None,
    )

    await initialize_database()
    assert db_manager.async_session_maker is not None

    async with db_manager.async_session_maker() as db:
        iv6_before_full = await build_intake_v6_priced_quote_dry_run(db, IV6_ID)
        iv6_before = _preview_digest(iv6_before_full.get("acm_panel_commercial_preview"))

        created = await create_intake_v6_workspace(
            db,
            IntakeV6WorkspaceCreateRequest(
                title="QA AcmPanel matching double-fold DXF measured UI",
                template_code="TPL-VOLUMETRIC-LETTERS_v2",
                client_name="QA",
                job_title="Matching DXF measured UI proof",
                source="qa_matching_dxf_measured_ui_v1",
            ),
            user,
        )
        ws_id = created.id
        ws_code = created.workspace_code
        assert ws_id != IV6_ID and ws_code != IV6_CODE

        record = await _get_record_or_404(db, ws_id)
        payload_raw = _json_loads(record.payload_json, {})
        if not isinstance(payload_raw, dict):
            payload_raw = {}

        # Read-only copy of IV6 SVG/analysis/layer scaffold so Review is analysisReady
        # (placeholder SVG re-triggers analysis-bundle and wipes finish_setup).
        # IV6 commercial geometry is NOT copied — AcmPanel config is QA 2000×300.
        iv6_record = await _get_record_or_404(db, IV6_ID)
        iv6_payload = _json_loads(iv6_record.payload_json, {})
        if not isinstance(iv6_payload, dict):
            raise RuntimeError("IV6 payload unreadable for QA scaffold copy")

        scaffold_keys = (
            "svg_source",
            "svg_source_text",
            "svg_analysis_json",
            "svg",
            "path_geometry_summary",
            "quote_geometry",
            "layer_role_setup",
            "layer_role_review",
            "analyzer_mode",
            "product_composition_recommendation",
            "product_composition_confirmed",
            "offer_scope",
            "offer_scope_confirmed",
            "selected_template_code",
            "product_binding",
        )
        for key in scaffold_keys:
            if key in iv6_payload:
                payload_raw[key] = deepcopy(iv6_payload[key])

        iv6_finish = iv6_payload.get("finish_setup")
        finish = _qa_finish_setup()
        if isinstance(iv6_finish, dict):
            # Keep IV6 lighting/face selectors so Review form is non-empty; overlay AcmPanel QA.
            merged = deepcopy(iv6_finish)
            for key, value in finish.items():
                merged[key] = deepcopy(value)
            finish = merged
        payload_raw["finish_setup"] = finish
        payload_raw["fold_sides"] = "all"
        payload_raw["source"] = "qa_matching_dxf_measured_ui_v1"

        payload = _parse_payload(payload_raw)
        await _persist_payload(db, record, payload, current_user=user)

        fp = compute_config_fingerprint(payload=payload_raw, acm_instance=finish["acm_panel_instance"])
        raw_bytes = FIXTURE_DXF.read_bytes()
        upload = await upload_and_optionally_bind_production_dxf(
            db,
            ws_id,
            raw_bytes=raw_bytes,
            filename="2-pliuri-100x30.dxf",
            content_type="application/dxf",
            component_instance_id=COMPONENT_ID,
            panel_id="p1",
            geometry_role="production_geometry",
            bind=True,
            uploaded_by=user.email,
            current_user=user,
        )

        qa_dry = await build_intake_v6_priced_quote_dry_run(db, ws_id)
        qa_preview = _preview_digest(qa_dry.get("acm_panel_commercial_preview"))

        # Reload attachment from DB
        record2 = await _get_record_or_404(db, ws_id)
        payload2 = _json_loads(record2.payload_json, {})
        inst = (
            (payload2.get("finish_setup") or {}).get("acm_panel_instance")
            if isinstance(payload2.get("finish_setup"), dict)
            else None
        )
        atts = []
        if isinstance(inst, dict):
            pg = inst.get("production_geometry") or {}
            atts = list(pg.get("attachments") or [])

        iv6_after_full = await build_intake_v6_priced_quote_dry_run(db, IV6_ID)
        iv6_after = _preview_digest(iv6_after_full.get("acm_panel_commercial_preview"))

    att = next((a for a in atts if a.get("measurement_status") not in {"replaced", "archived"}), None)
    cut_line = next((ln for ln in qa_preview["lines"] if ln.get("code") == "acm_panel_cut"), None)
    v_line = next((ln for ln in qa_preview["lines"] if ln.get("code") == "acm_v_groove"), None)

    checks = {
        "qa_workspace_distinct": ws_id != IV6_ID and ws_code != IV6_CODE,
        "upload_ok": bool(upload.get("ok") and upload.get("bound")),
        "measurement_status_measured": (att or {}).get("measurement_status") == "measured",
        "panel_id_p1": (att or {}).get("panel_id") == "p1",
        "fingerprint_current": (att or {}).get("config_fingerprint") == fp,
        "cut_exact": abs(float((att or {}).get("metrics_snapshot", {}).get("cut_length_ml") or 0) - 5.499412)
        < TOL
        or abs(float(qa_preview.get("cut_length_m") or 0) - 5.499412) < TOL,
        "v_l1_exact": abs(float(qa_preview.get("v_groove_l1_ml") or 0) - 5.4) < TOL,
        "v_l2_exact": abs(float(qa_preview.get("v_groove_l2_ml") or 0) - 4.600004) < TOL,
        "v_total_exact": abs(float(qa_preview.get("v_groove_total_ml") or 0) - 10.000004) < TOL,
        "path_status_measured": qa_preview.get("path_measurement_status")
        in {"measured", "measured_with_warnings"},
        "cpp_cut_qty": cut_line is not None
        and abs(float(cut_line.get("quantity") or 0) - 5.499412) < TOL,
        "cpp_v_qty": v_line is not None
        and abs(float(v_line.get("quantity") or 0) - 10.000004) < TOL,
        "gates_blocked": qa_preview.get("final_eligibility") is False
        and qa_preview.get("offer_eligibility") is False
        and qa_preview.get("execution_eligibility") is False,
        "iv6_face_before": iv6_before.get("face_area_m2") == 0.7,
        "iv6_unavailable_before": iv6_before.get("path_measurement_status") == "unavailable",
        "iv6_face_after": iv6_after.get("face_area_m2") == 0.7,
        "iv6_unavailable_after": iv6_after.get("path_measurement_status") == "unavailable",
        "iv6_cut_null_after": iv6_after.get("cut_length_m") is None,
        "iv6_gates_false_after": iv6_after.get("final_eligibility") is False
        and iv6_after.get("offer_eligibility") is False
        and iv6_after.get("execution_eligibility") is False,
        "no_unknown_aci": "unknown_aci" not in str((att or {}).get("warnings") or []),
    }

    proof = {
        "ok": all(checks.values()),
        "checks": checks,
        "qa": {
            "workspace_id": ws_id,
            "workspace_code": ws_code,
            "component_instance_id": COMPONENT_ID,
            "config_fingerprint": fp,
            "attachment": {
                "attachment_id": (att or {}).get("attachment_id"),
                "filename": (att or {}).get("filename"),
                "checksum": (att or {}).get("checksum"),
                "panel_id": (att or {}).get("panel_id"),
                "measurement_status": (att or {}).get("measurement_status"),
                "config_fingerprint": (att or {}).get("config_fingerprint"),
                "warnings": (att or {}).get("warnings"),
                "metrics_snapshot": (att or {}).get("metrics_snapshot"),
            },
            "preview": qa_preview,
            "upload": {
                "ok": upload.get("ok"),
                "bound": upload.get("bound"),
                "duplicate": upload.get("duplicate"),
            },
        },
        "iv6_control": {
            "workspace_id": IV6_ID,
            "workspace_code": IV6_CODE,
            "before": iv6_before,
            "after": iv6_after,
        },
        "dxf": str(FIXTURE_DXF.relative_to(ROOT)).replace("\\", "/"),
        "tolerance_ml": TOL,
    }

    (OUT / "runtime-proof.json").write_text(json.dumps(proof, indent=2), encoding="utf-8")
    (OUT / "iv6-before.json").write_text(json.dumps(iv6_before, indent=2), encoding="utf-8")
    (OUT / "iv6-after.json").write_text(json.dumps(iv6_after, indent=2), encoding="utf-8")
    (OUT / "qa-workspace.json").write_text(
        json.dumps(
            {
                "workspace_id": ws_id,
                "workspace_code": ws_code,
                "component_instance_id": COMPONENT_ID,
                "operator_route": f"/intake-v6/{ws_id}/operator",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(proof, indent=2))
    raise SystemExit(0 if proof["ok"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
