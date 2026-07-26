"""ACM panel-alone — suppress VL letter capture fatals for support_only composition."""

from schemas.intake_v4 import (
    IntakeV4MaterialBreakdownResponse,
    IntakeV4MaterialBreakdownTotals,
    IntakeV4MaterialQuantityRow,
)
from services.intake_v6_canonical_readiness_service import list_runtime_capture_fatal_blocker_codes
from services.intake_v6_offer_scope_live_calc_service import (
    filter_logical_list_rows_by_offer_scope,
    filter_material_breakdown_by_offer_scope,
)
from services.intake_v6_subset_capture_filter import (
    ACM_PANEL_ONLY_LETTER_CAPTURE_FATAL_CODES,
    is_acm_panel_only_composition,
    inactive_module_capture_codes_for_payload,
)


def _acm_panel_only_payload() -> dict:
    return {
        "finish_setup": {
            "confirmed": True,
            "mounting_scope": "mounting_included",
            "applied_content": "none",
            "mounting_solution": {
                "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                "configuration": {
                    "panel_width_mm": 2000,
                    "panel_height_mm": 500,
                    "acm_thickness_mm": 3,
                    "return_depth_mm": 60,
                    "rear_lip_mm": 25,
                    "fold_sides": "all",
                },
            },
            "acm_panel_instance": {
                "schema": "acm_panel_component_instance_v1",
                "component_instance_id": "acm_1",
                "association_status": "confirmed",
                "technical_configuration_status": "confirmed",
                "composition_status": "confirmed",
                "geometry": {
                    "width_mm": 2000,
                    "height_mm": 500,
                    "panels": [
                        {
                            "panel_id": "p1",
                            "width_mm": 2000,
                            "height_mm": 500,
                            "position": {"x_mm": 0, "y_mm": 0},
                        }
                    ],
                    "joints": [],
                },
                "configuration": {
                    "finished_depth_mm": 60,
                    "fold_count": 1,
                    "l1_mm": 60,
                    "l2_mm": 0,
                    "field_authority": {
                        "panel_geometry": "operator_confirmed",
                        "fold_count": "operator_confirmed",
                        "l1_mm": "operator_confirmed",
                        "acm_thickness_mm": "operator_confirmed",
                        "finished_depth_mm": "operator_confirmed",
                    },
                },
            },
        },
        "product_composition_recommendation": {
            "composition_type": "support_only",
            "status": "needs_confirmation",
        },
        "product_composition_confirmed": {
            "confirmed": True,
            "items": [
                {
                    "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
                    "component_role": "support_panel",
                }
            ],
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "bond",
                    "layer_id": "bond",
                    "layer_name": "Alucobond Casetat",
                    "confirmed_role": "support_panel",
                    "auto_role": "support_panel",
                    "confirmation_state": "confirmed",
                }
            ],
        },
    }


def test_detects_support_only_composition() -> None:
    assert is_acm_panel_only_composition(_acm_panel_only_payload()) is True


def test_inactive_codes_include_letter_artwork_fatals() -> None:
    inactive = inactive_module_capture_codes_for_payload(_acm_panel_only_payload())
    assert "FINISH_TARGET_MISSING" in inactive
    assert "SELECTED_LAYER_REFS_EMPTY" in inactive
    assert inactive >= ACM_PANEL_ONLY_LETTER_CAPTURE_FATAL_CODES


def test_runtime_capture_fatals_cleared_for_acm_panel_only() -> None:
    codes = list_runtime_capture_fatal_blocker_codes(
        _acm_panel_only_payload(),
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
    )
    assert codes == []


def test_live_calc_filters_letter_adhesive_keeps_acm_lines() -> None:
    """Legacy full-product scope still drops VL adhesive; keeps acm_* CPP rows."""
    payload = _acm_panel_only_payload()
    rows = [
        {
            "module_code": "modelare_cant",
            "line_id": "material.adhesive_return_to_face",
            "label": "Adeziv lipire cant pe fețe litere",
        },
        {
            "module_code": "debitare_fata",
            "line_id": "material.plexiglas_face",
            "label": "Plexiglas față",
        },
        {
            "module_code": None,
            "code": "acm_v_groove",
            "line_id": "acm_v_groove",
            "label": "V-groove ACM",
        },
        {
            "code": "acm_panel_face_material",
            "label": "Față panou ACM",
        },
    ]
    filtered = filter_logical_list_rows_by_offer_scope(rows, payload_raw=payload)
    codes = {str(r.get("code") or r.get("line_id")) for r in filtered}
    assert "material.adhesive_return_to_face" not in codes
    assert "material.plexiglas_face" not in codes
    assert "acm_v_groove" in codes
    assert "acm_panel_face_material" in codes

    breakdown = IntakeV4MaterialBreakdownResponse(
        workspace_id="ws-acm-only",
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        material_rows=[
            IntakeV4MaterialQuantityRow(
                material_key="adhesive_return_to_face",
                display_name="Adeziv cant",
                category="material",
                quantity=0.1,
                unit="ml",
                quantity_source="test",
                quantity_quality="estimate",
                estimated_cost=None,
            ),
            IntakeV4MaterialQuantityRow(
                material_key="acm_panel_face_material",
                display_name="Față ACM",
                category="material",
                quantity=1.0,
                unit="m2",
                quantity_source="test",
                quantity_quality="estimate",
                estimated_cost=15.0,
            ),
        ],
        consumable_rows=[],
        operation_rows=[],
        edge_cant_operation_rows=[],
        warnings=[],
        totals=IntakeV4MaterialBreakdownTotals(
            material_cost_total=15.0,
            estimated_cost_total=15.0,
            currency="EUR",
            contains_estimates=False,
            contains_missing_prices=True,
        ),
    )
    filtered_bd = filter_material_breakdown_by_offer_scope(breakdown, payload_raw=payload)
    keys = {r.material_key for r in filtered_bd.material_rows}
    assert "adhesive_return_to_face" not in keys
    assert "acm_panel_face_material" in keys
    assert filtered_bd.totals.contains_missing_prices is False
