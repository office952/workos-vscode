"""ProductSystem registry — TPL-VOLUMETRIC-FACE-BACK-PREP partial template."""

from __future__ import annotations

import asyncio
import json

import pytest

from schemas.intake_v4 import (
    TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE,
    TPL_VOLUMETRIC_FACE_BACK_PREP_V1_VERSION,
)
from seeds.seed_tpl_volumetric_face_back_prep_template import (
    seed_tpl_volumetric_face_back_prep_template,
    volumetric_face_back_prep_components,
)
from services.tpl_volumetric_face_back_prep_cost_draft_service import (
    build_tpl_volumetric_face_back_prep_cost_draft_v1,
)
from services.tpl_volumetric_face_back_prep_productsystem_contract import (
    CNC_RATE_EUR_PER_ML,
    FULL_VOLUMETRIC_TEMPLATE_CODE,
    MATERIAL_REGISTRY_BY_LOGICAL_KEY,
    OPERATION_BY_KEY,
    PRODUCTSYSTEM_COMPONENTS,
    PRODUCTSYSTEM_OPERATIONS,
    REGISTRY_FOREX_BACK_CODE,
    REGISTRY_PLEXI_FACE_CODE,
    TEMPLATE_EXCLUDES,
    TEMPLATE_INCLUDES,
    TEMPLATE_METADATA,
    task_draft_order,
)


class TestFaceBackPrepProductSystemContract:
    def test_template_key_and_scope(self):
        assert TEMPLATE_METADATA["key"] == TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE
        assert TEMPLATE_METADATA["scope"] == "partial_template"
        assert TEMPLATE_METADATA["version"] == TPL_VOLUMETRIC_FACE_BACK_PREP_V1_VERSION
        assert TEMPLATE_METADATA["status"] == "draft_internal"
        assert TEMPLATE_METADATA["active_for_commercial_quote"] is False
        assert TEMPLATE_METADATA["reusable_module_of"] == FULL_VOLUMETRIC_TEMPLATE_CODE

    def test_includes_face_and_back_components(self):
        assert "FACE_PLEXI" in TEMPLATE_INCLUDES
        assert "BACK_FOREX" in TEMPLATE_INCLUDES
        assert "FACE_PLEXI" in PRODUCTSYSTEM_COMPONENTS
        assert "BACK_FOREX" in PRODUCTSYSTEM_COMPONENTS

    def test_excludes_cant_led_support_mounting(self):
        for token in (
            "EDGE_CANT",
            "LIGHTING",
            "SUPPORT",
            "MOUNTING",
            "FINAL_ASSEMBLY",
            "STOCK_CONSUMPTION",
            "REAL_TASK_CREATION",
            "FINAL_QUOTE",
        ):
            assert token in TEMPLATE_EXCLUDES

    def test_material_mappings_use_historic_registry_codes(self):
        assert MATERIAL_REGISTRY_BY_LOGICAL_KEY["plexiglas_3mm"] == REGISTRY_PLEXI_FACE_CODE
        assert MATERIAL_REGISTRY_BY_LOGICAL_KEY["forex_10mm"] == REGISTRY_FOREX_BACK_CODE
        assert REGISTRY_PLEXI_FACE_CODE == "MAT-ACP-FATA-LITERE"
        assert REGISTRY_FOREX_BACK_CODE == "MAT-SPATE-PVC-LITERE"

    def test_cnc_operations_priced_at_150_eur_per_ml(self):
        for key in ("CUT_FACE_PLEXI", "SHANFREN_FACE_PLEXI", "CUT_BACK_FOREX", "SHANFREN_BACK_FOREX"):
            op = OPERATION_BY_KEY[key]
            assert op["unit"] == "ml"
            assert op["unitPrice"] == pytest.approx(CNC_RATE_EUR_PER_ML)
            assert op["currency"] == "EUR"
            assert op["priceSource"] == "fixed_rule"
            assert op["createsRealTask"] is False

    def test_face_shanfren_required_back_optional(self):
        assert OPERATION_BY_KEY["SHANFREN_FACE_PLEXI"]["required"] is True
        back = OPERATION_BY_KEY["SHANFREN_BACK_FOREX"]
        assert back["required"] is False
        assert back["appearsWhen"] == "shanfren_forex=true"

    def test_task_draft_order_without_forex_shanfren(self):
        assert task_draft_order(shanfren_forex_enabled=False) == [
            "PREPARE_CNC_FILES",
            "CUT_FACE_PLEXI",
            "SHANFREN_FACE_PLEXI",
            "CUT_BACK_FOREX",
            "CLEAN_AND_CHECK_PARTS",
            "PACKAGE_FACE_BACK_PARTS",
        ]

    def test_task_draft_order_with_forex_shanfren(self):
        assert task_draft_order(shanfren_forex_enabled=True) == [
            "PREPARE_CNC_FILES",
            "CUT_FACE_PLEXI",
            "SHANFREN_FACE_PLEXI",
            "CUT_BACK_FOREX",
            "SHANFREN_BACK_FOREX",
            "CLEAN_AND_CHECK_PARTS",
            "PACKAGE_FACE_BACK_PARTS",
        ]

    def test_cost_draft_service_uses_same_template_key(self):
        draft = build_tpl_volumetric_face_back_prep_cost_draft_v1(
            {
                "quote_geometry": {"face_area_m2": 1.0, "cutting_perimeter_ml": 5.0},
                "finish_setup": {"backing_mode": "forex_10_no_bevel"},
            },
            plexi_unit_price=10.0,
            forex_unit_price=10.0,
        )
        assert draft.template_key == TEMPLATE_METADATA["key"]
        assert draft.version == TEMPLATE_METADATA["version"]
        assert draft.creates_real_tasks is False
        assert draft.consumes_stock is False
        assert draft.creates_quote is False

    def test_seed_components_shape(self):
        components = volumetric_face_back_prep_components()
        codes = {c["component_id"] for c in components}
        assert codes == {"FACE_PLEXI", "BACK_FOREX"}
        ops = {op["code"] for comp in components for op in comp.get("operations", [])}
        assert "CUT_FACE_PLEXI" in ops
        assert "SHANFREN_BACK_FOREX" in ops
        assert len(PRODUCTSYSTEM_OPERATIONS) == 7


class TestFaceBackPrepProductSystemSeed:
    @pytest.fixture(scope="class")
    def seeded_row(self, db_fixture):
        import models  # noqa: F401
        from models.product_templates import Product_templates
        from sqlalchemy import select

        asyncio.get_event_loop().run_until_complete(seed_tpl_volumetric_face_back_prep_template())

        async def _fetch():
            async with db_fixture.session_maker() as session:
                result = await session.execute(
                    select(Product_templates).where(
                        Product_templates.template_code == TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE
                    )
                )
                return result.scalar_one_or_none()

        row = asyncio.get_event_loop().run_until_complete(_fetch())
        assert row is not None
        return row

    def test_template_row_inactive_draft_internal(self, seeded_row):
        assert seeded_row.active is False
        assert "partial_template" in (seeded_row.notes or "")
        assert "cost_draft_only=true" in (seeded_row.notes or "")

    def test_template_row_json_contains_components(self, seeded_row):
        components = json.loads(seeded_row.components_json)
        assert len(components) == 2
        ops = json.loads(seeded_row.operations_json)
        op_codes = {o["code"] for o in ops}
        assert "CUT_FACE_PLEXI" in op_codes
        mats = json.loads(seeded_row.required_materials_json)
        mat_codes = {m["material_code"] for m in mats}
        assert REGISTRY_PLEXI_FACE_CODE in mat_codes
        assert REGISTRY_FOREX_BACK_CODE in mat_codes


class TestFaceBackPrepEndpointReadOnly:
    def test_cost_draft_route_is_get_only(self):
        from main import app

        matches = [
            r
            for r in app.routes
            if getattr(r, "path", "").endswith("/volumetric-face-back-prep/cost-draft")
        ]
        assert len(matches) == 1
        route = matches[0]
        assert "GET" in getattr(route, "methods", set())
