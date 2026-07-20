"""Runtime proof — live DXF attachment binding (no IV6 golden contamination)."""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))
os.chdir(BACKEND)
os.environ.setdefault("APP_ENV", "development")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./dev.db")
os.environ.setdefault("JWT_SECRET_KEY", "local-dev-secret-not-for-production")

FIXTURES = BACKEND / "tests" / "fixtures" / "acm_panel_dxf"
OUT = Path(__file__).with_name("runtime-proof.json")


async def main() -> None:
    from services.acm_aci_semantic_mapping import ACM_ACI_SEMANTIC_MAPPING_VERSION, mapping_metadata
    from services.acm_production_geometry_attachment import (
        compute_config_fingerprint,
        measure_and_guard_dxf,
        validate_dxf_bytes,
    )
    from services.acm_production_geometry_metrics import resolve_production_geometry_metrics
    from core.database import db_manager
    from services.database import initialize_database
    from services.intake_v6_priced_quote_dry_run_service import build_intake_v6_priced_quote_dry_run

    single = measure_and_guard_dxf(FIXTURES / "un-pliu.dxf")
    double = measure_and_guard_dxf(FIXTURES / "2-pliuri-100x30.dxf")
    bad = validate_dxf_bytes(b"PK\x03\x04junk", filename="x.dxf")

    inst = {
        "schema": "acm_panel_component_instance_v1",
        "component_instance_id": "qa_double",
        "configuration": {"fold_count": 2, "l1_mm": 100, "l2_mm": 30, "finished_depth_mm": 100},
        "geometry": {
            "geometry_hash": "qa",
            "width_mm": 2000,
            "height_mm": 300,
            "panels": [
                {
                    "panel_id": "p1",
                    "width_mm": 2000,
                    "height_mm": 300,
                    "position": {"x_mm": 0, "y_mm": 0},
                }
            ],
            "joints": [],
        },
    }
    payload = {
        "finish_setup": {
            "acm_panel_instance": inst,
            "segmented_background": {
                "assembly_dimensions": {"width_mm": 2000, "height_mm": 300},
                "panels": inst["geometry"]["panels"],
            },
            "mounting_solution": {"configuration": {"fold_sides": "all"}},
        },
        "fold_sides": "all",
    }
    fp = compute_config_fingerprint(payload=payload, acm_instance=inst)
    inst["production_geometry"] = {
        "schema": "acm_panel_production_geometry_bundle_v1",
        "attachments": [
            {
                "attachment_id": "qa1",
                "workspace_id": "qa-ws",
                "component_instance_id": "qa_double",
                "panel_id": "p1",
                "geometry_role": "production_geometry",
                "measurement_status": "measured",
                "config_fingerprint": fp,
                "semantic_mapping_version": ACM_ACI_SEMANTIC_MAPPING_VERSION,
                "metrics_snapshot": {
                    "schema": "acm_panel_production_geometry_metrics_v1",
                    "panel_id": "p1",
                    "cut_length_ml": double["cut_length_ml"],
                    "v_groove_l1_ml": double["v_groove_l1_ml"],
                    "v_groove_l2_ml": double["v_groove_l2_ml"],
                    "v_groove_total_ml": double["v_groove_total_ml"],
                    "measurement_status": "measured",
                    "measurement_source": "imported_dxf",
                    "active_face_area_m2": 0.6,
                    "warnings": [],
                },
                "warnings": [],
            }
        ],
    }
    measured_asm = resolve_production_geometry_metrics(payload)

    # stale after L1 change
    inst["configuration"]["l1_mm"] = 90
    stale_asm = resolve_production_geometry_metrics(payload)

    await initialize_database()
    assert db_manager.async_session_maker is not None
    async with db_manager.async_session_maker() as db:
        dry = await build_intake_v6_priced_quote_dry_run(
            db, "a7b0162b-dc91-467f-aa24-c1279fb3a073"
        )
    preview = dry.get("acm_panel_commercial_preview") or {}
    geom = preview.get("geometry_summary") or {}

    proof = {
        "aci_mapping": mapping_metadata(),
        "golden_single": {
            "cut": single["cut_length_ml"],
            "v_total": single["v_groove_total_ml"],
            "status": single["measurement_status"],
        },
        "golden_double": {
            "cut": double["cut_length_ml"],
            "v_l2": double["v_groove_l2_ml"],
            "v_total": double["v_groove_total_ml"],
            "status": double["measurement_status"],
        },
        "corrupted_zip_rejected": bad.get("code"),
        "qa_bound_double": {
            "status": measured_asm.get("measurement_status"),
            "v_total": measured_asm.get("total_v_groove_ml"),
            "cut": measured_asm.get("total_cut_length_ml"),
        },
        "qa_stale_after_l1": {
            "status": stale_asm.get("measurement_status"),
            "cut": stale_asm.get("total_cut_length_ml"),
            "warnings": stale_asm.get("warnings"),
        },
        "iv6_db2f86b7_uncontaminated": {
            "face": geom.get("face_area_m2"),
            "path_status": geom.get("path_measurement_status"),
            "cut": geom.get("cut_length_m"),
            "final": preview.get("final_eligibility"),
            "offer": preview.get("offer_eligibility"),
            "exec": preview.get("execution_eligibility"),
            "note": "No golden 2000x300 DXF bound to IV6 2000x350",
        },
    }
    proof["ok"] = (
        abs(proof["golden_single"]["cut"] - 5.4) < 1e-4
        and abs(proof["golden_double"]["v_total"] - 10.000004) < 1e-4
        and proof["corrupted_zip_rejected"] == "archive_not_allowed"
        and proof["qa_bound_double"]["status"] == "measured"
        and abs(proof["qa_bound_double"]["v_total"] - 10.000004) < 1e-4
        and proof["qa_stale_after_l1"]["cut"] is None
        and proof["iv6_db2f86b7_uncontaminated"]["face"] == 0.7
        and proof["iv6_db2f86b7_uncontaminated"]["path_status"] == "unavailable"
        and proof["iv6_db2f86b7_uncontaminated"]["final"] is False
        and proof["iv6_db2f86b7_uncontaminated"]["offer"] is False
        and proof["iv6_db2f86b7_uncontaminated"]["exec"] is False
    )
    OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(json.dumps(proof, indent=2))
    raise SystemExit(0 if proof["ok"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
