"""Intake V4 LED module wattage selection — preview, persistence, PBL regression."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schemas.intake_v4 import IntakeV4FinishSetup, IntakeV4WorkspacePayload, PILOT_V4_TEMPLATE_CODE
from services.intake_v4_led_lighting_service import (
    ALLOWED_LED_MODULE_POWER_W,
    DEFAULT_LED_MODULE_POWER_W,
    normalize_led_module_power_w,
)
from services.intake_v4_material_breakdown_service import build_intake_v4_material_breakdown
from services.intake_v4_pricing_input_service import build_v4_pricing_input_preview
from services.intake_v4_pricing_preview_sync_service import (
    apply_v4_pricing_preview_derived_state,
    sync_intake_v4_finish_lighting,
)

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "intake_v4"
GOLDEN_ANALYSIS = FIXTURE_DIR / "pbl_layere_golden_analysis.json"


def _load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _pbl_layer_role_setup() -> dict:
    return {
        "confirmation_status": "complete",
        "layers": [
            {
                "layer_key": "Layer_x0020_1",
                "layer_name": "Layer_x0020_1",
                "auto_role": "printed_artwork",
                "confirmed_role": "printed_artwork",
                "confirmation_state": "confirmed",
            },
            {
                "layer_key": "Layer_x0020_2",
                "layer_name": "Layer_x0020_2",
                "auto_role": "face",
                "confirmed_role": "face",
                "confirmation_state": "confirmed",
            },
            {
                "layer_key": "Layer_x0020_3",
                "layer_name": "Layer_x0020_3",
                "auto_role": "face",
                "confirmed_role": "face",
                "confirmation_state": "confirmed",
            },
        ],
        "warnings": [],
    }


def _pbl_finish_setup(*, module_wattage: float | None = None) -> dict:
    body = {
        "face_finish_type": "none",
        "return_finish_type": "standard_aluminum",
        "return_depth_mm": 60,
        "illuminated": True,
        "lighting_system_type": "led_modules",
        "light_color": "warm_white",
        "confirmed": True,
        "letter_group_finishes": [
            {
                "group_key": "Layer_x0020_2",
                "layer_name": "Layer_x0020_2",
                "face_finish_type": "none",
                "return_finish_type": "standard_aluminum",
                "return_depth_mm": 60,
            },
            {
                "group_key": "Layer_x0020_3",
                "layer_name": "Layer_x0020_3",
                "face_finish_type": "none",
                "return_finish_type": "standard_aluminum",
                "return_depth_mm": 60,
            },
        ],
        "artwork_finishes": [
            {
                "layer_key": "Layer_x0020_1",
                "layer_name": "Layer_x0020_1",
                "execution_type": "needs_decision",
                "return_finish_type": "standard_aluminum",
                "return_depth_mm": 60,
            }
        ],
    }
    if module_wattage is not None:
        body["led_module_power_w"] = module_wattage
    return body


def _pbl_payload_raw(*, module_wattage: float | None = None) -> dict:
    return {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
        "svg_analysis_json": _load_json(GOLDEN_ANALYSIS),
        "layer_role_setup": _pbl_layer_role_setup(),
        "finish_setup": _pbl_finish_setup(module_wattage=module_wattage),
        "path_geometry_summary": {"parse_status": "parsed"},
        "svg_source": {
            "file_name": "pbl-layere.svg",
            "file_size_bytes": 5605,
            "file_hash": "golden-fixture",
            "upload_status": "analyzed",
        },
    }


def _path_geometry_for_pbl() -> dict:
    raw = _pbl_payload_raw()
    apply_v4_pricing_preview_derived_state(raw)
    return raw["path_geometry_summary"]


class TestLedModuleWattageNormalization:
    def test_finish_setup_defaults_to_illuminated_led_modules(self):
        setup = IntakeV4FinishSetup()

        assert setup.illuminated is True
        assert setup.lighting_system_type == "led_modules"
        assert setup.light_color == "neutral"
        assert setup.led_module_power_w == pytest.approx(0.75, rel=0, abs=0.01)

    def test_default_uses_owner_selected_module_power(self):
        assert DEFAULT_LED_MODULE_POWER_W == 0.75
        assert normalize_led_module_power_w(None) == 0.75
        assert normalize_led_module_power_w(1.44) == 1.44
        assert 0.75 in ALLOWED_LED_MODULE_POWER_W

    def test_invalid_wattage_normalizes_to_default(self):
        assert normalize_led_module_power_w(2.5) == 0.75
        assert normalize_led_module_power_w(0.72) == 0.75


class TestPblLightingWattagePreview:
    @pytest.mark.parametrize(
        ("module_w", "expected_led_w", "expected_psu_required", "expected_psu_config"),
        [
            (1.44, 67.68, 87.98, [100]),
            (1.0, 47.0, 61.1, [100]),
            (0.75, 35.25, 45.83, [60]),
        ],
    )
    def test_sync_recalculates_for_module_wattage(
        self,
        module_w: float,
        expected_led_w: float,
        expected_psu_required: float,
        expected_psu_config: list[int],
    ) -> None:
        setup = IntakeV4FinishSetup.model_validate(_pbl_finish_setup(module_wattage=module_w))
        synced = sync_intake_v4_finish_lighting(setup, path_geometry=_path_geometry_for_pbl())
        assert synced.led_module_count == 47
        assert synced.led_module_power_w == pytest.approx(module_w, rel=0, abs=0.01)
        assert synced.estimated_led_watts == pytest.approx(expected_led_w, rel=0, abs=0.01)
        assert synced.required_psu_watts == pytest.approx(expected_psu_required, rel=0, abs=0.02)
        assert synced.psu_configuration == expected_psu_config

    def test_persisted_through_apply_v4_pricing_preview_derived_state(self):
        raw = _pbl_payload_raw(module_wattage=1.0)
        apply_v4_pricing_preview_derived_state(raw)
        finish = raw["finish_setup"]
        assert finish["led_module_power_w"] == 1.0
        assert finish["led_module_count"] == 47
        assert finish["estimated_led_watts"] == pytest.approx(47.0, rel=0, abs=0.01)


class TestPblMaterialAndPricingInputWattage:
    def test_material_breakdown_includes_wattage_metadata(self):
        raw = _pbl_payload_raw(module_wattage=1.44)
        apply_v4_pricing_preview_derived_state(raw)
        breakdown = build_intake_v4_material_breakdown("ws-pbl-lighting", raw)
        led_modules = next(r for r in breakdown.consumable_rows if r.material_key == "led_modules")
        assert led_modules.quantity == 47
        assert "1.44" in led_modules.display_name
        led_total = next(r for r in breakdown.consumable_rows if r.material_key == "led_total_watts")
        assert led_total.quantity == pytest.approx(67.68, rel=0, abs=0.01)
        assert led_total.unit == "W"

    def test_pricing_input_preview_includes_module_wattage(self):
        raw = _pbl_payload_raw(module_wattage=0.75)
        apply_v4_pricing_preview_derived_state(raw)
        payload = IntakeV4WorkspacePayload.model_validate(raw)
        preview = build_v4_pricing_input_preview(workspace_id="ws-pbl-lighting", payload=payload)
        qi = preview.quote_input_payload
        assert qi.get("led_module_power_w") == 0.75
        assert qi.get("module_wattage") == 0.75
        assert qi.get("led_module_count") == 47
        assert qi.get("estimated_led_watts") == pytest.approx(35.25, rel=0, abs=0.01)
        assert qi.get("required_psu_watts") == pytest.approx(45.83, rel=0, abs=0.02)
        assert preview.preview_only is True


class TestProductionBoundaries:
    def test_no_execution_plan_or_tasks_in_breakdown(self):
        raw = _pbl_payload_raw(module_wattage=1.44)
        apply_v4_pricing_preview_derived_state(raw)
        breakdown = build_intake_v4_material_breakdown("ws-pbl-lighting", raw)
        dumped = breakdown.model_dump(mode="json")
        assert "execution_plan" not in dumped
        assert "tasks_json" not in dumped
