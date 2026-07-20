"""Runtime proof — golden DXF + IV6 fixture path status (read-only)."""
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
    from services.acm_dxf_path_measurement import measure_dxf_production_paths
    from services.acm_quote_input_helpers import merge_acm_boxed_mounting_derived_fields
    from core.database import db_manager
    from services.database import initialize_database
    from services.intake_v6_priced_quote_dry_run_service import build_intake_v6_priced_quote_dry_run

    single = measure_dxf_production_paths(FIXTURES / "un-pliu.dxf")
    double = measure_dxf_production_paths(FIXTURES / "2-pliuri-100x30.dxf")

    proxy = merge_acm_boxed_mounting_derived_fields(
        {
            "finish_setup": {
                "acm_panel_instance": {
                    "schema": "acm_panel_component_instance_v1",
                    "component_instance_id": "proxy",
                    "configuration": {
                        "fold_count": 1,
                        "l1_mm": 100,
                        "l2_mm": 0,
                        "finished_depth_mm": 100,
                    },
                    "geometry": {
                        "panels": [
                            {
                                "panel_id": "p1",
                                "width_mm": 1000,
                                "height_mm": 350,
                                "position": {"x_mm": 0, "y_mm": 0},
                            },
                            {
                                "panel_id": "p2",
                                "width_mm": 1000,
                                "height_mm": 350,
                                "position": {"x_mm": 1000, "y_mm": 0},
                            },
                        ],
                        "joints": [],
                    },
                },
                "segmented_background": {
                    "assembly_dimensions": {"width_mm": 2000, "height_mm": 350},
                    "panels": [
                        {
                            "panel_id": "p1",
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 0, "y_mm": 0},
                        },
                        {
                            "panel_id": "p2",
                            "width_mm": 1000,
                            "height_mm": 350,
                            "position": {"x_mm": 1000, "y_mm": 0},
                        },
                    ],
                },
                "mounting_solution": {
                    "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    "configuration": {
                        "panel_width_mm": 1000,
                        "panel_height_mm": 350,
                        "fold_sides": "all",
                        "return_depth_mm": 60,
                    },
                },
            }
        }
    )

    await initialize_database()
    assert db_manager.async_session_maker is not None
    async with db_manager.async_session_maker() as db:
        dry = await build_intake_v6_priced_quote_dry_run(
            db, "a7b0162b-dc91-467f-aa24-c1279fb3a073"
        )
    preview = dry.get("acm_panel_commercial_preview") or {}
    geom = preview.get("geometry_summary") or {}

    proof = {
        "golden_single": {
            "cut": single["cut_length_ml"],
            "v_l1": single["v_groove_l1_ml"],
            "v_l2": single["v_groove_l2_ml"],
            "v_total": single["v_groove_total_ml"],
            "status": single["measurement_status"],
        },
        "golden_double": {
            "cut": double["cut_length_ml"],
            "v_l1": double["v_groove_l1_ml"],
            "v_l2": double["v_groove_l2_ml"],
            "v_total": double["v_groove_total_ml"],
            "status": double["measurement_status"],
        },
        "proxy_sample": {
            "status": proxy.get("acm_path_quantity_status"),
            "cut": proxy.get("panel_perimeter_m"),
            "v": proxy.get("fold_length_m"),
            "face": proxy.get("panel_area_m2"),
        },
        "iv6_db2f86b7": {
            "face": geom.get("face_area_m2"),
            "cut": geom.get("cut_length_m"),
            "v": geom.get("fold_length_m"),
            "path_status": geom.get("path_measurement_status"),
            "path_source": geom.get("path_measurement_source"),
            "preview_status": preview.get("status"),
            "final": preview.get("final_eligibility"),
            "offer": preview.get("offer_eligibility"),
            "exec": preview.get("execution_eligibility"),
            "warnings": preview.get("warnings"),
        },
    }
    proof["ok"] = (
        abs(proof["golden_single"]["cut"] - 5.4) < 1e-4
        and abs(proof["golden_double"]["v_total"] - 10.000004) < 1e-4
        and proof["proxy_sample"]["status"] == "proxy_rectangular"
        and proof["iv6_db2f86b7"]["face"] == 0.7
        and proof["iv6_db2f86b7"]["path_status"] == "unavailable"
        and proof["iv6_db2f86b7"]["final"] is False
        and proof["iv6_db2f86b7"]["offer"] is False
        and proof["iv6_db2f86b7"]["exec"] is False
    )
    OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(json.dumps(proof, indent=2))
    raise SystemExit(0 if proof["ok"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
