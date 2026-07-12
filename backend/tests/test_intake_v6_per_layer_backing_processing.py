"""Intake V6 per-layer Forex backing processing — Slice B."""

from __future__ import annotations

import copy

import pytest

from services.intake_v4_backing_mode_service import (
    finish_has_explicit_layer_backing_modes,
    resolve_layer_backing_mode,
)
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown
from services.shared_cnc_operation_model import (
    build_volumetric_letters_cnc_operation_rows_with_layer_backing,
    merge_cnc_operation_preview_rows,
)

FACE_ML = 13.62
SHEET_FACE_M2 = 0.5834


def _payload(
    *,
    backing_mode: str = "forex_10_no_bevel",
    letter_group_finishes: list[dict] | None = None,
    artwork_finishes: list[dict] | None = None,
) -> dict:
    finish: dict = {
        "face_finish_type": "oracal_651",
        "return_finish_type": "oracal_wrapped",
        "return_depth_mm": 60,
        "illuminated": True,
        "led_module_power_w": 1.44,
        "backing_mode": backing_mode,
    }
    if letter_group_finishes is not None:
        finish["letter_group_finishes"] = letter_group_finishes
    if artwork_finishes is not None:
        finish["artwork_finishes"] = artwork_finishes
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS_v2"},
        "svg_analysis_json": {
            "schemaVersion": "1.10.0",
            "nesting": {
                "sheets": [
                    {
                        "configId": "sheet_3000x2000",
                        "sheetsUsed": 1,
                        "usedSheetAreaSqm": SHEET_FACE_M2,
                        "placedItemsCount": 10,
                        "unplacedItemsCount": 0,
                        "efficiencyPercent": 70.0,
                    }
                ],
            },
            "layers": [
                {
                    "id": "litere-a",
                    "name": "litere-a",
                    "perimeterMl": 6.0,
                    "filledAreaSqm": 0.8,
                },
                {
                    "id": "litere-b",
                    "name": "litere-b",
                    "perimeterMl": 4.0,
                    "filledAreaSqm": 0.7,
                },
            ],
        },
        "quote_geometry": {
            "letter_perimeter_m": 10.0,
            "face_area_m2": 1.5,
            "face_cutting_perimeter_ml": FACE_ML,
            "backing_cnc_cutting_perimeter_ml": 10.0,
            "artwork_area_m2": 0.45,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "face_area_m2": 1.5,
            "face_cutting_perimeter_ml": FACE_ML,
            "cnc_cutting_perimeter_ml": FACE_ML,
            "backing_cnc_cutting_perimeter_ml": 10.0,
            "led_perimeter_ml": 10.0,
            "artwork_area_m2": 0.45,
        },
        "finish_setup": finish,
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "litere-a",
                    "layer_name": "litere-a",
                    "auto_role": "face",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "litere-b",
                    "layer_name": "litere-b",
                    "auto_role": "face",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                },
            ],
        },
    }


def _group(
    key: str,
    *,
    perimeter_m: float,
    backing_mode: str | None = None,
) -> dict:
    row = {
        "group_key": key,
        "layer_name": key,
        "face_finish_type": "oracal_651",
        "return_finish_type": "white_aluminum",
        "perimeter_m": perimeter_m,
        "face_area_m2": 0.75,
        "confirmed": True,
    }
    if backing_mode is not None:
        row["backing_mode"] = backing_mode
    return row


def _operation_quantities(payload: dict) -> dict[str, float]:
    result = build_intake_v4_material_breakdown("ws-per-layer-backing", payload)
    return {row.key: float(row.operation_equivalent_quantity or 0.0) for row in result.operation_rows}


class TestLayerBackingCompatibilityReader:
    def test_legacy_global_no_bevel_loads(self):
        finish = {"backing_mode": "forex_10_no_bevel"}
        assert resolve_layer_backing_mode({}, finish) == "forex_10_no_bevel"

    def test_legacy_global_bevel_loads(self):
        finish = {"backing_mode": "forex_10_with_bevel"}
        assert resolve_layer_backing_mode({}, finish) == "forex_10_with_bevel"

    def test_per_layer_value_is_authoritative(self):
        finish = {"backing_mode": "forex_10_with_bevel"}
        layer = {"backing_mode": "forex_10_no_bevel"}
        assert resolve_layer_backing_mode(layer, finish) == "forex_10_no_bevel"

    def test_explicit_layer_detection(self):
        finish = {
            "backing_mode": "forex_10_no_bevel",
            "letter_group_finishes": [{"group_key": "a", "backing_mode": "forex_10_with_bevel"}],
        }
        assert finish_has_explicit_layer_backing_modes(finish) is True


class TestPerLayerBackingCnc:
    def test_two_layers_different_bevel_quantities(self):
        rows = build_volumetric_letters_cnc_operation_rows_with_layer_backing(
            {"face_cutting_perimeter_ml": FACE_ML},
            layer_backing_specs=[
                (6.0, "forex_10_no_bevel"),
                (4.0, "forex_10_with_bevel"),
            ],
        )
        by_key = {row.key: row for row in rows}
        assert "cnc_face_cutting_plexiglas_3mm" in by_key
        assert "cnc_face_bevel_plexiglas_3mm" in by_key
        cut = by_key["cnc_backing_cutting_forex_10mm"]
        bevel = by_key["cnc_backing_bevel_forex_10mm"]
        assert cut.operation_equivalent_quantity == pytest.approx((6.0 + 4.0) * 3, rel=1e-3)
        assert bevel.operation_equivalent_quantity == pytest.approx(4.0 * 2, rel=1e-3)

    def test_only_selected_back_layer_changes_bevel_cost(self):
        only_no_bevel = build_volumetric_letters_cnc_operation_rows_with_layer_backing(
            {"face_cutting_perimeter_ml": FACE_ML},
            layer_backing_specs=[(6.0, "forex_10_no_bevel"), (4.0, "forex_10_no_bevel")],
        )
        mixed = build_volumetric_letters_cnc_operation_rows_with_layer_backing(
            {"face_cutting_perimeter_ml": FACE_ML},
            layer_backing_specs=[(6.0, "forex_10_no_bevel"), (4.0, "forex_10_with_bevel")],
        )
        no_bevel_qty = {
            row.key: row.operation_equivalent_quantity
            for row in only_no_bevel
            if row.key == "cnc_backing_bevel_forex_10mm"
        }
        mixed_qty = {
            row.key: row.operation_equivalent_quantity
            for row in mixed
            if row.key == "cnc_backing_bevel_forex_10mm"
        }
        assert no_bevel_qty.get("cnc_backing_bevel_forex_10mm") is None
        assert mixed_qty["cnc_backing_bevel_forex_10mm"] == pytest.approx(8.0, rel=1e-3)

    def test_face_rows_unaffected_by_layer_backing(self):
        global_rows = build_volumetric_letters_cnc_operation_rows_with_layer_backing(
            {"face_cutting_perimeter_ml": FACE_ML},
            layer_backing_specs=[(6.0, "forex_10_with_bevel"), (4.0, "forex_10_no_bevel")],
        )
        face_qty = {
            row.key: row.operation_equivalent_quantity
            for row in global_rows
            if row.key.startswith("cnc_face_")
        }
        assert face_qty["cnc_face_cutting_plexiglas_3mm"] == pytest.approx(FACE_ML, rel=1e-3)
        assert face_qty["cnc_face_bevel_plexiglas_3mm"] == pytest.approx(FACE_ML, rel=1e-3)


class TestMaterialBreakdownPerLayerBacking:
    def test_legacy_global_no_bevel_breakdown(self):
        ops = _operation_quantities(_payload(backing_mode="forex_10_no_bevel"))
        assert ops["cnc_backing_cutting_forex_10mm"] > 0
        assert "cnc_backing_bevel_forex_10mm" not in ops

    def test_legacy_global_bevel_breakdown(self):
        ops = _operation_quantities(_payload(backing_mode="forex_10_with_bevel"))
        assert ops["cnc_backing_cutting_forex_10mm"] > 0
        assert ops["cnc_backing_bevel_forex_10mm"] > 0

    def test_per_layer_no_bevel_persists_in_payload(self):
        payload = _payload(
            backing_mode="forex_10_with_bevel",
            letter_group_finishes=[_group("litere-a", perimeter_m=6.0, backing_mode="forex_10_no_bevel")],
        )
        ops = _operation_quantities(payload)
        assert "cnc_backing_bevel_forex_10mm" not in ops

    def test_per_layer_bevel_persists_in_payload(self):
        payload = _payload(
            backing_mode="forex_10_no_bevel",
            letter_group_finishes=[_group("litere-a", perimeter_m=6.0, backing_mode="forex_10_with_bevel")],
        )
        ops = _operation_quantities(payload)
        assert ops["cnc_backing_bevel_forex_10mm"] == pytest.approx(6.0 * 2, rel=1e-3)

    def test_two_layers_can_differ(self):
        payload = _payload(
            backing_mode="forex_10_no_bevel",
            letter_group_finishes=[
                _group("litere-a", perimeter_m=6.0, backing_mode="forex_10_no_bevel"),
                _group("litere-b", perimeter_m=4.0, backing_mode="forex_10_with_bevel"),
            ],
        )
        ops = _operation_quantities(payload)
        assert ops["cnc_backing_bevel_forex_10mm"] == pytest.approx(8.0, rel=1e-3)

    def test_reload_preserves_per_layer_values(self):
        payload = _payload(
            backing_mode="forex_10_no_bevel",
            letter_group_finishes=[
                _group("litere-a", perimeter_m=6.0, backing_mode="forex_10_no_bevel"),
                _group("litere-b", perimeter_m=4.0, backing_mode="forex_10_with_bevel"),
            ],
        )
        reloaded = copy.deepcopy(payload)
        finish = reloaded["finish_setup"]
        groups = finish["letter_group_finishes"]
        assert resolve_layer_backing_mode(groups[0], finish) == "forex_10_no_bevel"
        assert resolve_layer_backing_mode(groups[1], finish) == "forex_10_with_bevel"

    def test_full_product_regression_unchanged_when_layers_match_global(self):
        legacy = _operation_quantities(_payload(backing_mode="forex_10_no_bevel"))
        layered = _operation_quantities(
            _payload(
                backing_mode="forex_10_no_bevel",
                letter_group_finishes=[
                    _group("litere-a", perimeter_m=6.0, backing_mode="forex_10_no_bevel"),
                    _group("litere-b", perimeter_m=4.0, backing_mode="forex_10_no_bevel"),
                ],
            )
        )
        assert legacy["cnc_backing_cutting_forex_10mm"] == pytest.approx(
            layered["cnc_backing_cutting_forex_10mm"],
            rel=1e-3,
        )
        assert "cnc_backing_bevel_forex_10mm" not in legacy
        assert "cnc_backing_bevel_forex_10mm" not in layered

    def test_linked_logo_neutral_identity_preserved(self):
        payload = _payload(
            backing_mode="forex_10_no_bevel",
            letter_group_finishes=[_group("litere-a", perimeter_m=6.0, backing_mode="forex_10_no_bevel")],
        )
        payload["quote_geometry"]["artwork_boxes"] = [
            {
                "layer_key": "logo-linked",
                "layer_name": "Logo linked",
                "area_m2": 0.2,
                "width_mm": 400,
                "height_mm": 500,
            }
        ]
        result = build_intake_v4_material_breakdown("ws-linked-logo", payload)
        finish = payload["finish_setup"]
        group = finish["letter_group_finishes"][0]
        assert resolve_layer_backing_mode(group, finish) == "forex_10_no_bevel"
        assert any(row.material_key == "forex_backing" for row in result.material_rows)
        assert "cnc_backing_cutting_forex_10mm" in {row.key for row in result.operation_rows}


class TestMergeCncRows:
    def test_merge_sums_equivalent_quantities(self):
        rows_a = build_volumetric_letters_cnc_operation_rows_with_layer_backing(
            {"backing_cnc_cutting_perimeter_ml": 6.0},
            layer_backing_specs=[(6.0, "forex_10_no_bevel")],
        )
        rows_b = build_volumetric_letters_cnc_operation_rows_with_layer_backing(
            {"backing_cnc_cutting_perimeter_ml": 4.0},
            layer_backing_specs=[(4.0, "forex_10_with_bevel")],
        )
        merged = merge_cnc_operation_preview_rows([*rows_a, *rows_b])
        by_key = {row.key: row for row in merged if row.key.startswith("cnc_backing_")}
        assert by_key["cnc_backing_cutting_forex_10mm"].operation_equivalent_quantity == pytest.approx(
            30.0,
            rel=1e-3,
        )
        assert by_key["cnc_backing_bevel_forex_10mm"].operation_equivalent_quantity == pytest.approx(
            8.0,
            rel=1e-3,
        )
