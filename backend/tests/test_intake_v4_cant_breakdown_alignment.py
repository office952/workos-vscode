"""Phase B1 — operator vector cant perimeter alignment in material breakdown."""

from __future__ import annotations

import pytest

from services.intake_v4_material_breakdown_service import (
    BASIS_PERIMETER,
    WASTE_PERCENT,
    build_intake_v4_material_breakdown,
)


LED_OUTER_M = 20.97
OPERATOR_LETTER_VECTOR_M = 26.75
OPERATOR_EMBLEM_VECTOR_M = 4.89
OPERATOR_TOTAL_M = round(OPERATOR_LETTER_VECTOR_M + OPERATOR_EMBLEM_VECTOR_M, 4)


def _base_payload(**finish_extra: object) -> dict:
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "layers": [
                {
                    "id": "litere-a",
                    "name": "litere-a",
                    "perimeterMl": OPERATOR_LETTER_VECTOR_M,
                    "filledAreaSqm": 1.2,
                },
                {
                    "id": "emblem-a",
                    "name": "emblem-a",
                    "perimeterMl": OPERATOR_EMBLEM_VECTOR_M,
                    "filledAreaSqm": 0.5,
                },
            ],
        },
        "quote_geometry": {
            "letter_perimeter_m": LED_OUTER_M,
            "led_perimeter_ml": LED_OUTER_M,
            "outer_letter_perimeter_ml": LED_OUTER_M,
            "letter_return_perimeter_ml": LED_OUTER_M,
            "return_material_perimeter_ml": LED_OUTER_M,
            "face_area_m2": 1.2,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "letter_perimeter_m": LED_OUTER_M,
            "led_perimeter_ml": LED_OUTER_M,
            "return_material_perimeter_ml": LED_OUTER_M,
            "face_area_m2": 1.2,
        },
        "finish_setup": {
            "face_finish_type": "none",
            "return_finish_type": "white_aluminum",
            "return_depth_mm": 60,
            "illuminated": True,
            "letter_group_finishes": [
                {
                    "group_key": "litere-a",
                    "layer_name": "litere-a",
                    "return_finish_type": "white_aluminum",
                    "perimeter_m": OPERATOR_LETTER_VECTOR_M,
                }
            ],
            "artwork_finishes": [],
            "confirmed": True,
            **finish_extra,
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "litere-a",
                    "layer_name": "litere-a",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "emblem-a",
                    "layer_name": "emblem-a",
                    "confirmed_role": "printed_artwork",
                    "confirmation_state": "confirmed",
                },
            ],
        },
    }


def _return_row(payload: dict) -> object:
    result = build_intake_v4_material_breakdown("ws-b1", payload)
    return next(row for row in result.material_rows if row.material_key == "return_material")


def test_return_material_base_uses_vector_letters_not_led_outer():
    ret = _return_row(_base_payload())
    assert ret.base_quantity == pytest.approx(OPERATOR_LETTER_VECTOR_M, rel=1e-4)
    assert ret.base_quantity != pytest.approx(LED_OUTER_M, rel=1e-2)


def test_emblem_perimeter_added_when_artwork_cant_active():
    payload = _base_payload(
        artwork_finishes=[
            {
                "layer_key": "emblem-a",
                "layer_name": "emblem-a",
                "execution_type": "separate_emblem",
                "return_finish_type": "white_aluminum",
                "return_depth_mm": 60,
            }
        ],
    )
    result = build_intake_v4_material_breakdown("ws-b1-emblem", payload)
    ret = next(row for row in result.material_rows if row.material_key == "return_material")
    emblem = next(row for row in result.material_rows if row.material_key == "artwork_return_emblem-a")
    assert ret.base_quantity == pytest.approx(OPERATOR_LETTER_VECTOR_M, rel=1e-4)
    assert emblem.base_quantity == pytest.approx(OPERATOR_EMBLEM_VECTOR_M, rel=1e-4)


def test_emblem_not_added_when_print_only_without_cant():
    payload = _base_payload(
        artwork_finishes=[
            {
                "layer_key": "emblem-a",
                "layer_name": "emblem-a",
                "execution_type": "print_laminate",
                "return_finish_type": "none",
            }
        ],
    )
    ret = _return_row(payload)
    assert ret.base_quantity == pytest.approx(OPERATOR_LETTER_VECTOR_M, rel=1e-4)


def test_print_laminate_emblem_included_in_return_material_when_cant_active():
    payload = _base_payload(
        artwork_finishes=[
            {
                "layer_key": "emblem-a",
                "layer_name": "emblem-a",
                "execution_type": "print_laminate",
                "return_finish_type": "white_aluminum",
                "return_depth_mm": 60,
            }
        ],
    )
    ret = _return_row(payload)
    assert ret.base_quantity == pytest.approx(OPERATOR_TOTAL_M, rel=1e-4)
    assert ret.priced_quantity == pytest.approx(OPERATOR_TOTAL_M * 1.2, rel=1e-3)


def test_artwork_cant_active_without_vector_perimeter_excluded_with_warning():
    payload = _base_payload(
        artwork_finishes=[
            {
                "layer_key": "emblem-a",
                "layer_name": "emblem-a",
                "execution_type": "print_laminate",
                "return_finish_type": "white_aluminum",
            }
        ],
    )
    payload["svg_analysis_json"]["layers"][1].pop("perimeterMl", None)
    result = build_intake_v4_material_breakdown("ws-b1-raster", payload)
    ret = next(row for row in result.material_rows if row.material_key == "return_material")
    assert ret.base_quantity == pytest.approx(OPERATOR_LETTER_VECTOR_M, rel=1e-4)
    assert any(w.code == "missing_artwork_perimeter" for w in result.warnings)


def test_priced_quantity_keeps_waste_separate_from_base():
    ret = _return_row(_base_payload())
    assert ret.quantity_basis == BASIS_PERIMETER
    assert ret.waste_percent == WASTE_PERCENT
    assert ret.priced_quantity == pytest.approx(ret.base_quantity * 1.2, rel=1e-3)
    assert ret.base_quantity != pytest.approx(ret.priced_quantity, rel=1e-2)


def test_led_perimeter_unchanged_by_cant_fix():
    payload = _base_payload()
    result = build_intake_v4_material_breakdown("ws-b1-led", payload)
    led = next((row for row in result.consumable_rows if row.material_key == "led_modules"), None)
    assert led is not None
    assert payload["quote_geometry"]["led_perimeter_ml"] == pytest.approx(LED_OUTER_M, rel=1e-4)


def test_missing_vector_no_bbox_fallback():
    payload = _base_payload()
    payload["finish_setup"]["letter_group_finishes"][0]["perimeter_m"] = None
    payload["svg_analysis_json"]["layers"][0].pop("perimeterMl", None)
    result = build_intake_v4_material_breakdown("ws-b1-missing", payload)
    keys = {row.material_key for row in result.material_rows}
    assert "return_material" not in keys
    assert any(w.code == "missing_operator_cant_perimeter" for w in result.warnings)
