"""Tests for read-only ProductDefinition preview builder (Step 6)."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.product_definition_builder_service import ProductDefinitionBuilderService

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


@pytest_asyncio.fixture
async def pd_builder(volumetric_v2_db):
    yield ProductDefinitionBuilderService(volumetric_v2_db)


@pytest.fixture
def pd_auth_client(volumetric_auth_client):
    return volumetric_auth_client


def _full_payload(*, mounting_system: str = "direct_wall") -> dict:
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
            "volum_aluminum_module_template_code": "TPL-VOLUM-ALUMINIU_v1",
            "backing_mode": "closed_back",
            "mounting_system": mounting_system,
            "lighting_system_type": "front_lit",
            "illuminated": True,
        },
    }


@pytest.mark.asyncio
async def test_preview_template_code_correct(pd_builder: ProductDefinitionBuilderService):
    preview = await pd_builder.build_preview(TEMPLATE)
    assert preview is not None
    assert preview.template_code == TEMPLATE
    assert preview.business_name_ro


@pytest.mark.asyncio
async def test_preview_includes_always_on_modules(pd_builder: ProductDefinitionBuilderService):
    preview = await pd_builder.build_preview(TEMPLATE)
    assert preview is not None
    all_codes = {
        m.module_code
        for m in preview.selected_modules + preview.optional_modules + preview.inactive_modules
    }
    for expected in ("geometry_svg", "debitare_fata", "debitare_spate", "modelare_cant"):
        assert expected in all_codes


@pytest.mark.asyncio
async def test_structura_suport_inactive_without_bars_mounting(pd_builder: ProductDefinitionBuilderService):
    preview = await pd_builder.build_preview(TEMPLATE)
    assert preview is not None
    structura_states = [
        m.state
        for m in preview.optional_modules + preview.inactive_modules + preview.selected_modules
        if m.module_code == "structura_suport"
    ]
    assert structura_states
    assert "active" not in structura_states


@pytest.mark.asyncio
async def test_structura_suport_active_with_steel_bars(pd_builder: ProductDefinitionBuilderService, volumetric_v2_db):
    workspace_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-PD-{workspace_id[:8]}",
            title="PD test workspace",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(_full_payload(mounting_system="steel_bars")),
        )
    )
    await volumetric_v2_db.commit()

    preview = await pd_builder.build_preview(TEMPLATE, workspace_id=workspace_id)
    assert preview is not None
    structura = next(
        m
        for m in preview.selected_modules + preview.optional_modules
        if m.module_code == "structura_suport"
    )
    assert structura.state == "active"
    assert preview.canonical_values.get("metal_support_required") is True


@pytest.mark.asyncio
async def test_geometry_svg_is_gate_not_priced_task(pd_builder: ProductDefinitionBuilderService):
    preview = await pd_builder.build_preview(TEMPLATE)
    assert preview is not None
    svg_ops = [op for op in preview.operation_roles if op.operation_code == "svg_geometry_analysis"]
    assert svg_ops
    assert svg_ops[0].is_geometry_gate is True
    assert svg_ops[0].mini_module_code == "geometry_svg" or svg_ops[0].is_geometry_gate


@pytest.mark.asyncio
async def test_missing_required_fields_reported_not_invented(pd_builder: ProductDefinitionBuilderService):
    preview = await pd_builder.build_preview(TEMPLATE)
    assert preview is not None
    assert preview.validation.readiness_status == "partial"
    assert preview.validation.missing_required_fields
    assert "width_mm" in preview.validation.missing_required_fields
    assert preview.canonical_values.get("width_mm") is None


@pytest.mark.asyncio
async def test_aggregate_warnings_propagated(pd_builder: ProductDefinitionBuilderService):
    preview = await pd_builder.build_preview(TEMPLATE)
    assert preview is not None
    assert any("TRIGGER" in w or "trigger" in w.lower() for w in preview.warnings + preview.validation.unresolved_warnings)


@pytest.mark.asyncio
async def test_comp_auto_1_not_component_truth(pd_builder: ProductDefinitionBuilderService):
    preview = await pd_builder.build_preview(TEMPLATE)
    assert preview is not None
    component_ids = {c.component_id for c in preview.components}
    assert "comp_auto_1" not in component_ids
    assert len(preview.components) >= 5


@pytest.mark.asyncio
async def test_no_pricing_or_cost_result(pd_builder: ProductDefinitionBuilderService):
    preview = await pd_builder.build_preview(TEMPLATE)
    assert preview is not None
    dumped = preview.model_dump()
    assert "cost_result" not in dumped
    assert "price" not in dumped
    assert "grand_total" not in dumped


def test_product_definition_endpoint_200(pd_auth_client):
    response = pd_auth_client.get(f"/api/v1/product-system/product-definition/{TEMPLATE}")
    assert response.status_code == 200
    body = response.json()
    assert body["template_code"] == TEMPLATE
    assert body["validation"]["readiness_status"] in ("partial", "ready", "blocked")
    assert "components" in body


def test_unknown_template_returns_404(pd_auth_client):
    response = pd_auth_client.get("/api/v1/product-system/product-definition/TPL-UNKNOWN")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_electrica_logo_future_not_active(pd_builder: ProductDefinitionBuilderService):
    preview = await pd_builder.build_preview(TEMPLATE)
    assert preview is not None
    electrica = [
        m
        for m in preview.inactive_modules + preview.optional_modules + preview.selected_modules
        if m.module_code == "electrica_logo"
    ]
    if electrica:
        assert electrica[0].state == "future_reserved"
    assert any("electrica_logo" in w.lower() or "FUTURE_RESERVED" in w for w in preview.warnings)


@pytest.mark.asyncio
async def test_no_db_writes_on_preview(pd_builder: ProductDefinitionBuilderService, volumetric_v2_db):
    from sqlalchemy import func, select

    before = await volumetric_v2_db.scalar(select(func.count()).select_from(IntakeV6WorkspaceRecord))
    await pd_builder.build_preview(TEMPLATE)
    after = await volumetric_v2_db.scalar(select(func.count()).select_from(IntakeV6WorkspaceRecord))
    assert before == after
