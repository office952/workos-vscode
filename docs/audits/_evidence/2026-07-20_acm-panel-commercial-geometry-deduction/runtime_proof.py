"""Runtime proof — commercial geometry deduction (offer-time, no DXF required)."""
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

OUT = Path(__file__).with_name("runtime-proof.json")
FIXTURES = BACKEND / "tests" / "fixtures" / "acm_panel_dxf"
DOUBLE_DXF = FIXTURES / "2-pliuri-100x30.dxf"

CONTROL_WS = "a7b0162b-dc91-467f-aa24-c1279fb3a073"  # IV6-DB2F86B7
MEASURED_QA_WS = "a7a74172-ad09-4f93-b0f5-f89fe5b9aad9"  # IV6-13D39D32


def _mount(*, fold_sides: str = "all", return_depth_mm: float = 60) -> dict:
    return {
        "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
        "configuration": {
            "fold_sides": fold_sides,
            "return_depth_mm": return_depth_mm,
        },
    }


def _payload(
    *,
    panels: list[dict],
    fold_count: int,
    l1: float,
    l2: float,
    assembly_w: float | None = None,
    assembly_h: float | None = None,
    production_geometry: dict | None = None,
    dxf_path: str | None = None,
) -> dict:
    aw = assembly_w
    ah = assembly_h
    if aw is None:
        aw = max((p["width_mm"] + float(p.get("position", {}).get("x_mm") or 0) for p in panels), default=0)
    if ah is None:
        ah = max(p["height_mm"] for p in panels) if panels else 0
    inst: dict = {
        "schema": "acm_panel_component_instance_v1",
        "component_instance_id": "acm_proof",
        "configuration": {
            "fold_count": fold_count,
            "l1_mm": l1,
            "l2_mm": l2,
            "finished_depth_mm": l1,
        },
        "geometry": {
            "panels": panels,
            "joints": [{"joint_id": f"j{i}"} for i in range(max(0, len(panels) - 1))],
        },
    }
    if production_geometry is not None:
        inst["production_geometry"] = production_geometry
    out: dict = {
        "finish_setup": {
            "acm_panel_instance": inst,
            "segmented_background": {
                "status": "PROPOSED",
                "panels": panels,
                "assembly_dimensions": {"width_mm": aw, "height_mm": ah},
            },
            "mounting_solution": _mount(return_depth_mm=l1 if l1 else 60),
        }
    }
    if dxf_path:
        out["acm_production_dxf_path"] = dxf_path
    return out


async def main() -> None:
    from services.acm_production_geometry_metrics import (
        build_commercial_deduction_panel_metrics,
        resolve_production_geometry_metrics,
    )
    from services.acm_quote_input_helpers import merge_acm_boxed_mounting_derived_fields
    from core.database import db_manager
    from services.database import initialize_database
    from services.intake_v6_priced_quote_dry_run_service import build_intake_v6_priced_quote_dry_run

    single = build_commercial_deduction_panel_metrics(
        panel_id="g1",
        width_mm=2000,
        height_mm=300,
        l1_mm=100,
        l2_mm=0,
        fold_sides="all",
        construction_type="single_fold",
    )
    double = build_commercial_deduction_panel_metrics(
        panel_id="g2",
        width_mm=2000,
        height_mm=300,
        l1_mm=100,
        l2_mm=30,
        fold_sides="all",
        construction_type="double_fold",
    )

    unequal_panels = [
        {"panel_id": "a", "width_mm": 1000, "height_mm": 350, "position": {"x_mm": 0, "y_mm": 0}},
        {"panel_id": "b", "width_mm": 2000, "height_mm": 350, "position": {"x_mm": 1000, "y_mm": 0}},
    ]
    unequal = resolve_production_geometry_metrics(
        _payload(panels=unequal_panels, fold_count=1, l1=60, l2=0, assembly_w=3000, assembly_h=350)
    )
    p_a = build_commercial_deduction_panel_metrics(
        panel_id="a", width_mm=1000, height_mm=350, l1_mm=60, l2_mm=0, fold_sides="all"
    )
    p_b = build_commercial_deduction_panel_metrics(
        panel_id="b", width_mm=2000, height_mm=350, l1_mm=60, l2_mm=0, fold_sides="all"
    )

    ten_panels = [
        {
            "panel_id": f"p{i}",
            "width_mm": 1000,
            "height_mm": 350,
            "position": {"x_mm": i * 1000, "y_mm": 0},
        }
        for i in range(10)
    ]
    ten = resolve_production_geometry_metrics(
        _payload(panels=ten_panels, fold_count=1, l1=60, l2=0, assembly_w=10000, assembly_h=350)
    )

    measured = resolve_production_geometry_metrics(
        _payload(
            panels=[
                {
                    "panel_id": "p1",
                    "width_mm": 2000,
                    "height_mm": 300,
                    "position": {"x_mm": 0, "y_mm": 0},
                }
            ],
            fold_count=2,
            l1=100,
            l2=30,
            dxf_path=str(DOUBLE_DXF),
        )
    )

    stale = resolve_production_geometry_metrics(
        _payload(
            panels=[
                {
                    "panel_id": "p1",
                    "width_mm": 2000,
                    "height_mm": 300,
                    "position": {"x_mm": 0, "y_mm": 0},
                }
            ],
            fold_count=2,
            l1=100,
            l2=30,
            production_geometry={
                "schema": "acm_panel_production_geometry_bundle_v1",
                "attachments": [
                    {
                        "attachment_id": "att1",
                        "workspace_id": "ws1",
                        "component_instance_id": "acm_proof",
                        "panel_id": "p1",
                        "geometry_role": "production_geometry",
                        "measurement_status": "measured",
                        "config_fingerprint": "outdated",
                        "metrics_snapshot": {
                            "schema": "acm_panel_production_geometry_metrics_v1",
                            "panel_id": "p1",
                            "cut_length_ml": 99.0,
                            "v_groove_total_ml": 99.0,
                            "measurement_status": "measured",
                            "measurement_source": "imported_dxf",
                            "warnings": [],
                        },
                        "warnings": [],
                    }
                ],
            },
        )
    )

    sf_merged = merge_acm_boxed_mounting_derived_fields(
        _payload(
            panels=[
                {
                    "panel_id": "p1",
                    "width_mm": 2000,
                    "height_mm": 300,
                    "position": {"x_mm": 0, "y_mm": 0},
                }
            ],
            fold_count=1,
            l1=100,
            l2=0,
        )
    )
    df_merged = merge_acm_boxed_mounting_derived_fields(
        _payload(
            panels=[
                {
                    "panel_id": "p1",
                    "width_mm": 2000,
                    "height_mm": 300,
                    "position": {"x_mm": 0, "y_mm": 0},
                }
            ],
            fold_count=2,
            l1=100,
            l2=30,
        )
    )

    await initialize_database()
    assert db_manager.async_session_maker is not None
    control_preview = {}
    measured_preview = {}
    async with db_manager.async_session_maker() as db:
        control_dry = await build_intake_v6_priced_quote_dry_run(db, CONTROL_WS)
        measured_dry = await build_intake_v6_priced_quote_dry_run(db, MEASURED_QA_WS)
    control_preview = control_dry.get("acm_panel_commercial_preview") or {}
    measured_preview = measured_dry.get("acm_panel_commercial_preview") or {}
    cgeom = control_preview.get("geometry_summary") or {}
    mgeom = measured_preview.get("geometry_summary") or {}

    proof = {
        "build": "WORKOS_ACM_PANEL_COMMERCIAL_GEOMETRY_DEDUCTION_V1",
        "golden_single_deduction": {
            "cut": single["cut_length_ml"],
            "v_l1": single["v_groove_l1_ml"],
            "v_l2": single["v_groove_l2_ml"],
            "v_total": single["v_groove_total_ml"],
            "status": single["measurement_status"],
            "source": single["measurement_source"],
        },
        "golden_double_deduction": {
            "cut": double["cut_length_ml"],
            "v_l1": double["v_groove_l1_ml"],
            "v_l2": double["v_groove_l2_ml"],
            "v_total": double["v_groove_total_ml"],
            "status": double["measurement_status"],
        },
        "single_fold_no_dxf_merge": {
            "status": sf_merged.get("acm_path_quantity_status"),
            "cut": sf_merged.get("panel_perimeter_m"),
            "v": sf_merged.get("fold_length_m"),
        },
        "double_fold_no_dxf_merge": {
            "status": df_merged.get("acm_path_quantity_status"),
            "cut": df_merged.get("panel_perimeter_m"),
            "v": df_merged.get("fold_length_m"),
        },
        "unequal_panels": {
            "status": unequal.get("measurement_status"),
            "cut": unequal.get("total_cut_length_ml"),
            "expected_sum": round(p_a["cut_length_ml"] + p_b["cut_length_ml"], 6),
            "not_first_times_n": unequal.get("total_cut_length_ml")
            != round(p_a["cut_length_ml"] * 2, 6),
            "panel_count": unequal.get("panel_count"),
        },
        "ten_panels": {
            "status": ten.get("measurement_status"),
            "panel_count": ten.get("panel_count"),
            "cut": ten.get("total_cut_length_ml"),
            "expected": round(p_a["cut_length_ml"] * 10, 6),
        },
        "measured_override_filesystem": {
            "status": measured.get("measurement_status"),
            "source": measured.get("measurement_source"),
            "cut": measured.get("total_cut_length_ml"),
            "v": measured.get("total_v_groove_ml"),
        },
        "stale_falls_to_deduction": {
            "status": stale.get("measurement_status"),
            "source": stale.get("measurement_source"),
            "cut": stale.get("total_cut_length_ml"),
            "v": stale.get("total_v_groove_ml"),
            "warnings": stale.get("warnings"),
        },
        "iv6_control_db2f86b7": {
            "face": cgeom.get("face_area_m2"),
            "cut": cgeom.get("cut_length_m"),
            "v": cgeom.get("fold_length_m"),
            "path_status": cgeom.get("path_measurement_status"),
            "path_source": cgeom.get("path_measurement_source"),
            "final": control_preview.get("final_eligibility"),
            "offer": control_preview.get("offer_eligibility"),
            "exec": control_preview.get("execution_eligibility"),
        },
        "iv6_measured_qa_13d39d32": {
            "face": mgeom.get("face_area_m2"),
            "cut": mgeom.get("cut_length_m"),
            "v": mgeom.get("fold_length_m"),
            "path_status": mgeom.get("path_measurement_status"),
            "path_source": mgeom.get("path_measurement_source"),
            "final": measured_preview.get("final_eligibility"),
            "offer": measured_preview.get("offer_eligibility"),
            "exec": measured_preview.get("execution_eligibility"),
        },
        "writes": {
            "offer": False,
            "order": False,
            "execution": False,
            "note": "proof is read-only resolve/merge/dry-run — no Offer/Order/Execution APIs called",
        },
    }

    checks = {
        "single_golden": abs(single["cut_length_ml"] - 5.4) < 1e-6
        and abs(single["v_groove_total_ml"] - 5.4) < 1e-6,
        "double_golden": abs(double["cut_length_ml"] - 5.64) < 1e-6
        and abs(double["v_groove_total_ml"] - 10.0) < 1e-6,
        "double_no_dxf_available": df_merged.get("acm_path_quantity_status")
        in {"commercial_deduced", "commercial_deduced_with_assumptions"}
        and df_merged.get("panel_perimeter_m") is not None,
        "unequal_sum": abs(
            (unequal.get("total_cut_length_ml") or 0)
            - (p_a["cut_length_ml"] + p_b["cut_length_ml"])
        )
        < 1e-6,
        "ten_sum": abs((ten.get("total_cut_length_ml") or 0) - p_a["cut_length_ml"] * 10) < 1e-6,
        "measured_wins": measured.get("measurement_status")
        in {"measured", "measured_with_warnings"},
        "stale_deduction": stale.get("measurement_status")
        in {"commercial_deduced", "commercial_deduced_with_assumptions"}
        and abs((stale.get("total_cut_length_ml") or 0) - 5.64) < 1e-4,
        "gates_blocked_control": control_preview.get("final_eligibility") is False
        and control_preview.get("offer_eligibility") is False
        and control_preview.get("execution_eligibility") is False,
        "gates_blocked_measured": measured_preview.get("final_eligibility") is False
        and measured_preview.get("offer_eligibility") is False
        and measured_preview.get("execution_eligibility") is False,
        "control_has_cut_without_dxf": cgeom.get("cut_length_m") is not None
        or cgeom.get("path_measurement_status")
        in {"commercial_deduced", "commercial_deduced_with_assumptions", "measured", "measured_with_warnings"},
    }
    proof["checks"] = checks
    proof["ok"] = all(checks.values())
    OUT.write_text(json.dumps(proof, indent=2), encoding="utf-8")
    print(json.dumps(proof, indent=2))
    raise SystemExit(0 if proof["ok"] else 1)


if __name__ == "__main__":
    asyncio.run(main())
