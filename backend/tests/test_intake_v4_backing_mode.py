"""Intake V4 backing mode — material rows vs CNC operation rows."""

from __future__ import annotations

import pytest

from schemas.intake_v4 import IntakeV4ArtworkFinish, IntakeV4FinishSetup
from services.intake_v4_backing_mode_service import (
    BASIS_BACKING_AREA_FACE_QUOTEABLE_FALLBACK,
    resolve_backing_material_area_m2,
)
from services.intake_v4_material_breakdown_service import (
    PRICE_SOURCE_INFORMATIONAL,
    build_intake_v4_material_breakdown,
)
from services.intake_v4_pricing_preview_sync_service import sync_intake_v4_finish_lighting

FACE_ML = 13.62
SHEET_FACE_M2 = 0.5834


def _payload(backing_mode: str, **finish_extra: object) -> dict:
    finish = {
        "face_finish_type": "oracal_651",
        "return_finish_type": "oracal_wrapped",
        "return_depth_mm": 60,
        "illuminated": True,
        "led_module_power_w": 1.44,
        "backing_mode": backing_mode,
        **finish_extra,
    }
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
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
                    "id": "litere-volumetrice-1",
                    "name": "litere-volumetrice-1",
                    "perimeterMl": 10.0,
                    "filledAreaSqm": 1.5,
                }
            ],
        },
        "quote_geometry": {
            "letter_perimeter_m": 11.63,
            "face_area_m2": 1.5,
            "face_cutting_perimeter_ml": FACE_ML,
            "artwork_area_m2": 0.45,
        },
        "path_geometry_summary": {
            "parse_status": "parsed",
            "face_area_m2": 1.5,
            "face_cutting_perimeter_ml": FACE_ML,
            "cnc_cutting_perimeter_ml": FACE_ML,
            "led_perimeter_ml": 11.63,
            "artwork_area_m2": 0.45,
        },
        "finish_setup": finish,
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


def _material_keys(payload: dict) -> list[str]:
    result = build_intake_v4_material_breakdown("ws-backing-test", payload)
    return [r.material_key for r in result.material_rows]


def _operation_keys(payload: dict) -> list[str]:
    result = build_intake_v4_material_breakdown("ws-backing-test", payload)
    return [r.key for r in result.operation_rows]


class TestBackingMaterialAreaFallback:
    def test_resolve_uses_face_quoteable_when_backing_area_missing(self):
        qty, basis, source, used_fallback = resolve_backing_material_area_m2(
            backing_confirmed=True,
            backing_area_m2=None,
            sheet_backing_area_sqm=None,
            sheet_face_quoteable_area_sqm=SHEET_FACE_M2,
            face_area_gross_m2=1.5,
        )
        assert qty == SHEET_FACE_M2
        assert basis == BASIS_BACKING_AREA_FACE_QUOTEABLE_FALLBACK
        assert used_fallback is True
        assert "backing_area_missing" in (source or "")


class TestBackingModeMaterialRows:
    def test_legacy_none_maps_to_required_forex_material(self):
        keys = _material_keys(_payload("none"))
        assert "forex_backing" in keys
        assert "plexiglas_face" in keys

    def test_forex_no_bevel_emits_forex_material_via_fallback(self):
        payload = _payload("forex_10_no_bevel")
        result = build_intake_v4_material_breakdown("ws", payload)
        forex = next((r for r in result.material_rows if r.material_key == "forex_backing"), None)
        assert forex is not None
        assert forex.display_name == "Forex 10 mm / spate litere"
        assert forex.quantity_basis == BASIS_BACKING_AREA_FACE_QUOTEABLE_FALLBACK
        assert forex.quantity == pytest.approx(SHEET_FACE_M2, rel=1e-3)
        assert any(w.code == "backing_area_fallback_used" for w in result.warnings)

    def test_forex_with_bevel_emits_forex_material(self):
        keys = _material_keys(_payload("forex_10_with_bevel"))
        assert "forex_backing" in keys


class TestBackingModeCncOperationRows:
    def test_face_cutting_and_bevel_always(self):
        ops = _operation_keys(_payload("none"))
        assert "cnc_face_cutting_plexiglas_3mm" in ops
        assert "cnc_face_bevel_plexiglas_3mm" in ops
        result = build_intake_v4_material_breakdown("ws", _payload("none"))
        cut = next(r for r in result.operation_rows if r.key == "cnc_face_cutting_plexiglas_3mm")
        bevel = next(r for r in result.operation_rows if r.key == "cnc_face_bevel_plexiglas_3mm")
        assert cut.quantity == pytest.approx(FACE_ML, rel=1e-3)
        assert bevel.quantity == pytest.approx(FACE_ML, rel=1e-3)

    def test_legacy_none_keeps_backing_cutting_without_back_bevel(self):
        ops = _operation_keys(_payload("none"))
        assert "cnc_backing_cutting_forex_10mm" in ops
        assert "cnc_backing_bevel_forex_10mm" not in ops

    def test_forex_no_bevel_cutting_five_passes(self):
        result = build_intake_v4_material_breakdown("ws", _payload("forex_10_no_bevel"))
        back = next(r for r in result.operation_rows if r.key == "cnc_backing_cutting_forex_10mm")
        assert back.passes == 5
        assert back.owner_pass_override is True
        assert back.operation_equivalent_quantity == pytest.approx(FACE_ML * 5, rel=1e-3)
        assert "cnc_backing_bevel_forex_10mm" not in [r.key for r in result.operation_rows]

    def test_forex_with_bevel_adds_backing_bevel(self):
        ops = _operation_keys(_payload("forex_10_with_bevel"))
        assert "cnc_backing_cutting_forex_10mm" in ops
        assert "cnc_backing_bevel_forex_10mm" in ops

    def test_operation_rows_separate_from_material_rows(self):
        result = build_intake_v4_material_breakdown("ws", _payload("forex_10_with_bevel"))
        material_keys = {r.material_key for r in result.material_rows}
        for op in result.operation_rows:
            assert op.key not in material_keys

    def test_missing_cnc_rates_do_not_invent_costs(self):
        result = build_intake_v4_material_breakdown("ws", _payload("forex_10_with_bevel"))
        for op in result.operation_rows:
            assert op.estimated_cost is None
            assert op.unit_price is None

    def test_preview_flags(self):
        result = build_intake_v4_material_breakdown("ws", _payload("forex_10_with_bevel"))
        assert result.stock_consumption is False
        for op in result.operation_rows:
            assert op.consumes_stock_now is False
            assert op.creates_task_now is False


class TestEmblemLedAndWattsDoubleCount:
    def test_emblem_area_lit_adds_to_total_modules(self):
        setup = IntakeV4FinishSetup(
            emblem_lighting_mode="area_lit",
            illuminated=True,
            led_module_power_w=1.44,
        )
        synced = sync_intake_v4_finish_lighting(
            setup,
            path_geometry={"led_perimeter_ml": 11.63, "artwork_area_m2": 0.45},
        )
        assert synced.letter_led_module_count == 47
        assert synced.emblem_led_module_count == 36
        assert synced.total_led_module_count == 83

    def test_area_lit_recalculates_watts_and_psu_from_stale_letter_derived(self):
        setup = IntakeV4FinishSetup(
            emblem_lighting_mode="area_lit",
            illuminated=True,
            led_module_power_w=1.44,
            estimated_led_watts=67.68,
            required_psu_watts=87.98,
            psu_configuration=[100],
            led_module_count=47,
        )
        synced = sync_intake_v4_finish_lighting(
            setup,
            path_geometry={
                "led_perimeter_ml": 11.6299,
                "artwork_area_m2": 0.1976,
                "artwork_boxes": [{"width_mm": 585.8, "height_mm": 337.3, "area_m2": 0.1976}],
            },
        )
        assert synced.letter_led_module_count == 47
        assert synced.emblem_led_module_count == 15
        assert synced.total_led_module_count == 62
        assert synced.estimated_led_watts == pytest.approx(89.28, abs=0.01)
        assert synced.required_psu_watts == pytest.approx(116.06, abs=0.02)
        assert synced.psu_configuration is not None
        assert sum(synced.psu_configuration) >= synced.required_psu_watts

    def test_emblem_modules_follow_artwork_return_depth_not_letter_depth(self):
        path_geometry = {
            "led_perimeter_ml": 10,
            "artwork_area_m2": 1,
            "artwork_boxes": [
                {"layer_key": "logo", "width_mm": 1000, "height_mm": 1000, "area_m2": 1}
            ],
        }

        setup_80 = IntakeV4FinishSetup(
            emblem_lighting_mode="area_lit",
            illuminated=True,
            led_module_power_w=1.44,
            return_depth_mm=60,
            artwork_finishes=[
                IntakeV4ArtworkFinish(layer_key="logo", layer_name="Logo", return_depth_mm=80)
            ],
        )
        setup_100 = setup_80.model_copy(
            update={
                "artwork_finishes": [
                    IntakeV4ArtworkFinish(layer_key="logo", layer_name="Logo", return_depth_mm=100)
                ]
            },
        )

        synced_80 = sync_intake_v4_finish_lighting(setup_80, path_geometry=path_geometry)
        synced_100 = sync_intake_v4_finish_lighting(setup_100, path_geometry=path_geometry)

        assert synced_80.letter_led_module_count == 40
        assert synced_100.letter_led_module_count == 40
        assert synced_80.emblem_led_module_count == 63
        assert synced_100.emblem_led_module_count == 56
        assert synced_80.total_led_module_count == 103
        assert synced_100.total_led_module_count == 96

    def test_led_watts_row_informational_not_priced(self):
        setup = IntakeV4FinishSetup(illuminated=True, led_module_power_w=1.44)
        synced = sync_intake_v4_finish_lighting(
            setup,
            path_geometry={"led_perimeter_ml": 11.63},
        )
        raw = _payload("none")
        raw["finish_setup"] = {**raw["finish_setup"], **synced.model_dump(mode="json")}
        result = build_intake_v4_material_breakdown("ws", raw)
        led_watts = next(r for r in result.consumable_rows if r.material_key == "led_total_watts")
        assert led_watts.price_source == PRICE_SOURCE_INFORMATIONAL
        assert led_watts.estimated_cost is None
        assert led_watts.material_cost is None

    def test_area_lit_adhesive_uses_total_modules(self):
        setup = IntakeV4FinishSetup(
            emblem_lighting_mode="area_lit",
            illuminated=True,
            led_module_power_w=1.44,
            estimated_led_watts=67.68,
            required_psu_watts=87.98,
            psu_configuration=[100],
        )
        synced = sync_intake_v4_finish_lighting(
            setup,
            path_geometry={
                "led_perimeter_ml": 11.6299,
                "artwork_area_m2": 0.1976,
                "artwork_boxes": [{"width_mm": 585.8, "height_mm": 337.3, "area_m2": 0.1976}],
            },
        )
        raw = _payload("none")
        raw["finish_setup"] = {**raw["finish_setup"], **synced.model_dump(mode="json")}
        result = build_intake_v4_material_breakdown("ws", raw)
        adhesive = next(r for r in result.consumable_rows if r.material_key == "adhesive_led_modules")
        assert adhesive.quantity == pytest.approx(12.4, abs=0.01)

    def test_no_quote_order_tasks_fields(self):
        raw = _payload("forex_10_no_bevel")
        result = build_intake_v4_material_breakdown("ws", raw)
        dumped = result.model_dump(mode="json")
        assert "execution_plan" not in dumped
        assert "tasks_json" not in dumped
