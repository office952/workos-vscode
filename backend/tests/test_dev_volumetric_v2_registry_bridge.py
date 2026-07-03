"""Tests for Step 8 dev volumetric v2 registry bridge."""

from __future__ import annotations

import pytest

from data.dev_volumetric_v2_registry_bridge import DEV_BRIDGE_MATERIAL_RATES
from services.estimated_internal_cost_service import EstimatedInternalCostService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _full_quote_input() -> dict:
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "test.svg"},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
        },
        "finish_setup": {
            "face_finish_type": "plexiglas_clear",
            "return_depth_mm": 60,
            "return_finish_type": "ral",
            "mounting_system": "direct_wall",
            "lighting_system_type": "front_lit",
            "illuminated": True,
            "led_module_count": 24,
            "selected_psu_watts": 100,
            "mounting_template_enabled": True,
            "mounting_template_area_m2": 2.5,
            "mounting_template_material_type": "paper",
            "letter_group_finishes": [{"group_key": "default", "confirmed": True}],
        },
    }


def test_merge_dev_registry_bridge_fills_missing_rates():
    rates: dict[str, float] = {}
    currencies: dict[str, str] = {}
    catalog: dict[str, dict] = {}
    EstimatedInternalCostService._merge_dev_registry_bridge(rates, currencies, catalog)
    assert rates["MAT-ACP-FATA-LITERE"] == DEV_BRIDGE_MATERIAL_RATES["MAT-ACP-FATA-LITERE"]
    assert catalog["MAT-ACP-FATA-LITERE"]["unit_cost"] == DEV_BRIDGE_MATERIAL_RATES["MAT-ACP-FATA-LITERE"]


def test_merge_dev_registry_bridge_does_not_override_db_rates():
    rates = {"MAT-ACP-FATA-LITERE": 99.0}
    currencies = {"MAT-ACP-FATA-LITERE": "RON"}
    catalog = {"MAT-ACP-FATA-LITERE": {"status": "active", "unit_cost": 99.0}}
    EstimatedInternalCostService._merge_dev_registry_bridge(rates, currencies, catalog)
    assert rates["MAT-ACP-FATA-LITERE"] == 99.0


@pytest.mark.asyncio
async def test_unpatched_eic_partial_with_dev_bridge(volumetric_v2_db):
    service = EstimatedInternalCostService(volumetric_v2_db)
    preview = await service.build_preview(TEMPLATE, quote_input=_full_quote_input())
    assert preview is not None
    assert preview.status in ("partial", "ready")
    assert not any(b.code == "INTERNAL_MATERIAL_COST_MISSING" for b in preview.internal_blockers)
