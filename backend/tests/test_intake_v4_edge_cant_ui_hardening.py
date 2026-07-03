"""Intake V4 edge/cant UI hardening — breakdown, dry-run, and handoff contract tests."""

from __future__ import annotations

import pytest

from schemas.intake_v4 import IntakeV4WorkspacePayload
from services.intake_v4_edge_cant_dry_run_service import build_edge_cant_dry_run_from_operation_rows
from services.intake_v4_template_option_contract_service import evaluate_v4_template_option_contract
from services.shared_edge_cant_rules import (
    EDGE_CANT_BOND_OPERATION_KEY,
    EDGE_CANT_ORACAL_MATERIAL_KEY,
    EDGE_CANT_ORACAL_WRAP_OPERATION_KEY,
    EDGE_CANT_LINEAR_UNIT,
    SHARED_EDGE_CANT_SOURCE,
    evaluate_edge_cant_rules,
    EdgeCantRuleInput,
)
from services.shared_vinyl_material_catalog import ORACAL_651_OWNER_EUR_PER_M2
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown

PBL_COMBINED_RETURN_ML = 15.4672
PBL_LETTER_RETURN_ML = 13.6211
PBL_WRAPPED_GROUP_ML = 6.1683


def _pbl_payload_oracal_wrapped() -> dict:
    payload = _pbl_payload("oracal_wrapped")
    payload["finish_setup"]["letter_group_finishes"] = [
        {
            "group_key": "litere-volumetrice-1",
            "face_finish_type": "oracal_651",
            "return_finish_type": "oracal_wrapped",
            "perimeter_m": PBL_WRAPPED_GROUP_ML,
        }
    ]
    return payload


def _pbl_payload(return_finish: str = "white_aluminum", **finish_extra: object) -> dict:
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
        "finish_setup": {
            "return_finish_type": return_finish,
            "return_depth_mm": 60,
            "backing_mode": "none",
            "emblem_lighting_mode": "needs_decision",
            "illuminated": True,
            "confirmed": True,
            **finish_extra,
        },
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "nesting": {
                "sheets": [
                    {
                        "configId": "sheet_3000x2000",
                        "sheetsUsed": 1,
                        "usedSheetAreaSqm": 0.5834,
                        "placedItemsCount": 10,
                        "unplacedItemsCount": 0,
                        "efficiencyPercent": 70.0,
                    }
                ],
            },
            "layers": [
                {
                    "id": "litere-volumetrice-1",
                    "name": "litere-volumetrice-1",
                    "perimeterMl": 10.0,
                    "filledAreaSqm": 1.5,
                }
            ],
        },
        "quote_geometry": {
            "return_material_perimeter_ml": PBL_COMBINED_RETURN_ML,
            "letter_perimeter_m": 11.6139,
            "face_cutting_perimeter_ml": PBL_LETTER_RETURN_ML,
            "face_area_m2": 1.5,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "face_cutting_perimeter_ml": PBL_LETTER_RETURN_ML,
            "return_material_perimeter_ml": PBL_COMBINED_RETURN_ML,
            "led_perimeter_ml": 11.6139,
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "litere-volumetrice-1",
                    "layer_name": "litere-volumetrice-1",
                    "auto_role": "face",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
        },
    }


def _build_breakdown(payload: dict) -> object:
    return build_intake_v4_material_breakdown("ws-pbl-edge-cant", payload)


def test_default_cant_material_lengths_in_breakdown():
    result = _build_breakdown(_pbl_payload())
    return_row = next(r for r in result.material_rows if r.material_key == "return_material")
    assert return_row.base_quantity > 0
    assert return_row.priced_quantity == pytest.approx(return_row.base_quantity * 1.2, rel=1e-3)
    assert return_row.unit == EDGE_CANT_LINEAR_UNIT


def test_default_cant_no_oracal_651_row():
    result = _build_breakdown(_pbl_payload())
    keys = {r.material_key for r in result.material_rows}
    assert EDGE_CANT_ORACAL_MATERIAL_KEY not in keys


def test_oracal_wrapped_includes_edge651_area_and_cost():
    result = _build_breakdown(_pbl_payload_oracal_wrapped())
    edge_row = next(r for r in result.material_rows if r.material_key == EDGE_CANT_ORACAL_MATERIAL_KEY)
    assert edge_row.unit == "m2"
    # Single wrapped group PBL fixture: 6.1683 m × band (60+10 mm) / 1000
    assert edge_row.base_quantity == pytest.approx(0.5181, rel=1e-2)
    assert edge_row.unit_price == pytest.approx(ORACAL_651_OWNER_EUR_PER_M2, rel=1e-2)
    assert edge_row.estimated_cost == pytest.approx(0.5181 * ORACAL_651_OWNER_EUR_PER_M2, rel=1e-2)


def test_edge_cant_operations_use_linear_meter_not_ml():
    result = evaluate_edge_cant_rules(
        EdgeCantRuleInput(
            letter_return_ml=PBL_LETTER_RETURN_ML,
            total_return_ml=PBL_COMBINED_RETURN_ML,
            default_return_finish="white_aluminum",
            edge_depth_mm=60,
        )
    )
    for row in result.operation_rows:
        assert row.unit == EDGE_CANT_LINEAR_UNIT
        assert row.unit != "ml"


def test_adhesive_uses_ml():
    result = _build_breakdown(_pbl_payload())
    adhesive = next(r for r in result.consumable_rows if r.material_key == "adhesive_return_to_face")
    assert adhesive.unit == "ml"
    assert adhesive.quantity > 0
    assert adhesive.quantity == pytest.approx(adhesive.base_quantity or adhesive.quantity, rel=1e-6)


def test_oracal_wrapped_wrap_operation_quantity():
    result = evaluate_edge_cant_rules(
        EdgeCantRuleInput(
            letter_return_ml=PBL_LETTER_RETURN_ML,
            total_return_ml=PBL_COMBINED_RETURN_ML,
            letter_groups=[
                {
                    "group_key": "a",
                    "return_finish_type": "oracal_wrapped",
                    "perimeter_m": PBL_WRAPPED_GROUP_ML,
                }
            ],
            default_return_finish="white_aluminum",
            edge_depth_mm=60,
        )
    )
    wrap = next(r for r in result.operation_rows if r.key == EDGE_CANT_ORACAL_WRAP_OPERATION_KEY)
    bond = next(r for r in result.operation_rows if r.key == EDGE_CANT_BOND_OPERATION_KEY)
    assert bond.quantity == pytest.approx(PBL_LETTER_RETURN_ML, rel=1e-3)
    assert wrap.quantity == pytest.approx(PBL_WRAPPED_GROUP_ML * 1.2, rel=1e-2)


def test_edge_cant_dry_run_candidates_from_breakdown_rows():
    breakdown = _build_breakdown(_pbl_payload())
    _, candidates = build_edge_cant_dry_run_from_operation_rows(
        list(breakdown.edge_cant_operation_rows),
        workspace_id="ws-edge",
        template_code="TPL-VOLUMETRIC-LETTERS",
        source_fingerprint="fp",
    )
    assert len(candidates) >= 1
    assert all(c.unit == EDGE_CANT_LINEAR_UNIT for c in candidates)
    assert all(c.source == SHARED_EDGE_CANT_SOURCE for c in candidates)


def test_finish_setup_hydration_fields_preserved():
    payload = IntakeV4WorkspacePayload.model_validate(
        _pbl_payload(
            "white_aluminum",
            backing_mode="forex_10_with_bevel",
            emblem_lighting_mode="area_lit",
        )
    )
    setup = payload.finish_setup
    assert setup.backing_mode == "forex_10_with_bevel"
    assert setup.emblem_lighting_mode == "area_lit"
    assert setup.return_finish_type == "white_aluminum"


def test_handoff_warning_clarifies_cnc_source_not_catalog_bundle():
    result = evaluate_v4_template_option_contract(
        IntakeV4WorkspacePayload.model_validate(_pbl_payload())
    )
    warn = next(w for w in result.warnings if w.code == "production_preview_not_template_backed")
    assert "operation_rows" in warn.message
    assert "face_and_backing_cnc_cut" in warn.message
    assert "legacy" in warn.message.lower() or "dossier" in warn.message.lower()


def test_cnc_operation_rows_still_present_in_breakdown():
    result = _build_breakdown(_pbl_payload())
    assert len(result.operation_rows or []) >= 2

