"""PBL pricing preview completeness — geometry counters, perimeter, lighting consumables."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from schemas.intake_v4 import IntakeV4FinishSetup, IntakeV4WorkspacePayload, PILOT_V4_TEMPLATE_CODE
from seeds.seed_intake_v6_unified_pricing import seed_intake_v6_unified_pricing
from services.intake_v4_material_breakdown_service import (
    build_intake_v4_material_breakdown,
    build_intake_v4_material_breakdown_with_registry,
)
from services.intake_v4_pricing_input_service import build_v4_pricing_input_preview
from services.intake_v4_pricing_preview_sync_service import (
    apply_v4_pricing_preview_derived_state,
    sync_intake_v4_finish_lighting,
)
from services.intake_v4_quote_geometry_service import resolve_v4_quote_geometry

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
                "artwork_execution": "needs_decision",
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


def _pbl_finish_setup() -> dict:
    return {
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


def _pbl_finish_setup_with_confirmed_artwork_print() -> dict:
    setup = _pbl_finish_setup()
    setup["artwork_finishes"] = [
        {
            "layer_key": "Layer_x0020_1",
            "layer_name": "Layer_x0020_1",
            "execution_type": "print_laminate",
            "color_mode": "polychrome",
            "print_transparency": "translucent",
            "confirmed": True,
            "return_finish_type": "standard_aluminum",
            "return_depth_mm": 60,
            "estimated_area_m2": 0.19756515182246506,
        }
    ]
    return setup


def _pbl_payload_raw(*, include_stale_quote: bool = True, confirmed_artwork_print: bool = False) -> dict:
    golden = _load_json(GOLDEN_ANALYSIS)
    raw: dict = {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": PILOT_V4_TEMPLATE_CODE},
        "svg_analysis_json": golden,
        "layer_role_setup": _pbl_layer_role_setup(),
        "finish_setup": (
            _pbl_finish_setup_with_confirmed_artwork_print()
            if confirmed_artwork_print
            else _pbl_finish_setup()
        ),
        "path_geometry_summary": {"parse_status": "parsed"},
        "svg_source": {
            "file_name": "pbl-layere.svg",
            "file_size_bytes": 5605,
            "file_hash": "golden-fixture",
            "upload_status": "analyzed",
        },
    }
    if include_stale_quote:
        raw["quote_geometry"] = {
            "real_letters_count": 10,
            "return_material_perimeter_ml": 11.6139,
            "artwork_piece_count": None,
            "volumetric_piece_count": None,
        }
    return raw


class TestPblQuoteGeometryCounters:
    def test_resolve_exposes_piece_counters_from_golden_analysis(self):
        payload = IntakeV4WorkspacePayload.model_validate(_pbl_payload_raw())
        quote = resolve_v4_quote_geometry(payload)
        assert quote.get("real_letters_count") == 10
        assert quote.get("inner_holes_count") == 5
        assert quote.get("artwork_piece_count") == 1
        assert quote.get("volumetric_piece_count") == 11

    def test_persist_sync_replaces_stale_null_counters(self):
        raw = _pbl_payload_raw(include_stale_quote=True)
        apply_v4_pricing_preview_derived_state(raw)
        quote = raw["quote_geometry"]
        assert quote["artwork_piece_count"] == 1
        assert quote["volumetric_piece_count"] == 11
        assert quote["return_material_perimeter_ml"] == pytest.approx(15.444, rel=0, abs=0.0002)
        assert raw["path_geometry_summary"]["volumetric_piece_count"] == 11


class TestPblReturnPerimeterCanonical:
    def test_golden_fixture_return_perimeter_stable(self):
        payload = IntakeV4WorkspacePayload.model_validate(_pbl_payload_raw())
        quote = resolve_v4_quote_geometry(payload)
        assert quote["return_material_perimeter_ml"] == pytest.approx(15.444, rel=0, abs=0.0002)
        assert quote["letter_return_perimeter_ml"] == pytest.approx(13.5979, rel=0, abs=0.0002)
        assert quote["artwork_return_perimeter_ml"] == pytest.approx(1.8461, rel=0, abs=0.0002)


class TestPblMaterialBreakdownCompleteness:
    def test_breakdown_plexiglas_nesting_no_full_sheet_fallback(self):
        raw = _pbl_payload_raw()
        apply_v4_pricing_preview_derived_state(raw)
        breakdown = build_intake_v4_material_breakdown("ws-pbl-pricing", raw)
        plexi = [r for r in breakdown.material_rows if r.material_key == "plexiglas_face"]
        assert plexi
        assert all(r.quantity is not None and r.quantity < 1.0 for r in plexi)
        assert all(r.quantity != 6.0 for r in plexi)
        assert breakdown.nesting_preview is not None
        assert breakdown.nesting_preview.summary.artwork_parts == 1

    def test_breakdown_no_vinyl_or_print_while_artwork_needs_decision(self):
        raw = _pbl_payload_raw()
        apply_v4_pricing_preview_derived_state(raw)
        breakdown = build_intake_v4_material_breakdown("ws-pbl-pricing", raw)
        keys = {row.material_key for row in breakdown.material_rows}
        assert "oracal_face_vinyl" not in keys
        assert not any("print" in key for key in keys)

    def test_breakdown_return_perimeter_matches_quote_geometry(self):
        raw = _pbl_payload_raw()
        apply_v4_pricing_preview_derived_state(raw)
        breakdown = build_intake_v4_material_breakdown("ws-pbl-pricing", raw)
        quote_return = raw["quote_geometry"]["return_material_perimeter_ml"]
        assert quote_return == pytest.approx(15.444, rel=0, abs=0.0002)
        return_rows = [r for r in breakdown.material_rows if "return" in r.material_key.lower()]
        assert return_rows, "expected return/cant material row"

    @pytest.mark.asyncio
    async def test_breakdown_print_service_priced_when_artwork_confirmed(self, db_session):
        await seed_intake_v6_unified_pricing()
        raw = _pbl_payload_raw(confirmed_artwork_print=True)
        apply_v4_pricing_preview_derived_state(raw)
        breakdown = await build_intake_v4_material_breakdown_with_registry(
            db_session,
            "ws-pbl-print-confirmed",
            raw,
        )
        print_ops = [
            row
            for row in breakdown.operation_rows
            if row.operation_type == "print_vinyl" and row.key.endswith("_print_service")
        ]
        assert len(print_ops) == 1
        print_service = print_ops[0]
        assert print_service.workcenter_code == "LARGE_FORMAT_PRINT"
        assert print_service.pricing_rate_key == "workcenter_rates:LARGE_FORMAT_PRINT:per_square_meter"
        assert print_service.pricing_status == "pricing_registry"
        assert print_service.unit_price == pytest.approx(8.5)
        assert print_service.estimated_cost is not None
        assert print_service.estimated_cost > 0
        print_material_keys = {
            row.material_key
            for row in breakdown.material_rows
            if "print" in row.material_key.lower() or "laminated" in row.material_key.lower()
        }
        assert any("print_vinyl" in key for key in print_material_keys)
        assert any("laminated_vinyl" in key for key in print_material_keys)
        missing_print_ops = [
            row
            for row in breakdown.operation_rows
            if row.operation_type == "print_vinyl" and row.pricing_status in {"missing_rate", "pending_mapping"}
        ]
        assert missing_print_ops == []
        assert breakdown.totals.contains_missing_prices is False


class TestPblLightingConsumables:
    def test_finish_sync_derives_psu_configuration_for_illuminated_job(self):
        raw = _pbl_payload_raw()
        apply_v4_pricing_preview_derived_state(raw)
        finish = raw["finish_setup"]
        assert finish.get("estimated_led_watts") == pytest.approx(67.68, rel=0, abs=0.05)
        assert finish.get("required_psu_watts") == pytest.approx(87.98, rel=0, abs=0.1)
        assert finish.get("psu_configuration")

    def test_material_breakdown_includes_led_and_psu_rows(self):
        raw = _pbl_payload_raw()
        apply_v4_pricing_preview_derived_state(raw)
        breakdown = build_intake_v4_material_breakdown("ws-pbl-pricing", raw)
        consumables = {row.material_key: row for row in breakdown.consumable_rows}
        assert consumables["led_modules"].quantity == 47
        assert "led_psu" in consumables
        assert consumables["led_psu"].quantity >= 1

    def test_pricing_input_preview_includes_psu_configuration(self):
        raw = _pbl_payload_raw()
        apply_v4_pricing_preview_derived_state(raw)
        payload = IntakeV4WorkspacePayload.model_validate(raw)
        preview = build_v4_pricing_input_preview(workspace_id="ws-pbl-pricing", payload=payload)
        assert preview.quote_input_payload.get("artwork_piece_count") == 1
        assert preview.quote_input_payload.get("volumetric_piece_count") == 11
        assert preview.quote_input_payload.get("psu_configuration")
        assert preview.production_counts.get("volumetric_piece_count") == 11

    def test_operator_psu_configuration_is_not_overwritten(self):
        setup = IntakeV4FinishSetup.model_validate(_pbl_finish_setup())
        setup = setup.model_copy(update={"psu_configuration": [200, 60], "required_psu_watts": 226.87})
        path_geometry = {
            "led_perimeter_ml": 11.6299,
            "outer_letter_perimeter_ml": 11.6299,
        }
        synced = sync_intake_v4_finish_lighting(setup, path_geometry=path_geometry)
        assert synced.psu_configuration == [200, 60]
        assert synced.required_psu_watts == 226.87


class TestPblProductionBoundaries:
    def test_no_execution_plan_or_tasks_in_material_breakdown(self):
        raw = _pbl_payload_raw()
        apply_v4_pricing_preview_derived_state(raw)
        breakdown = build_intake_v4_material_breakdown("ws-pbl-pricing", raw)
        dumped = breakdown.model_dump(mode="json")
        assert "execution_plan" not in dumped
        assert "tasks_json" not in dumped
