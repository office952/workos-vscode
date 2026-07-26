"""Cost BOM wiring for workspace-composed ProductAggregate with linked logo segments."""

from __future__ import annotations

import inspect
import json
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
from services.aggregate_cost_bom_adapter import (
    AggregateCostBomAdapter,
    AggregateCostBomBuilderService,
    WARNING_LINKED_SEGMENT_FINISH_PARTIAL,
)
from services.intake_v6_layer_binding_persistence_service import (
    persist_logo_layer_bindings_from_composition_confirmation,
)
from services.intake_v6_product_composition_recommendation_service import (
    LOGO_TEMPLATE_CODE,
    apply_product_composition_recommendation,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_aggregate_workspace_composition_service import (
    WARNING_COMPOSITION_APPLIED,
    WARNING_FINISH_PARTIAL,
)
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.template_architecture_scope import VOLUMETRIC_LOGO_TEMPLATE_CODE
from tests.test_aggregate_cost_bom_adapter import INVENTORY_CATALOG, SAMPLE_RATES, SAMPLE_WC_RATES
from tests.test_product_aggregate_volumetric_v2 import _seed_volumetric_v2_fixture

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = LOGO_TEMPLATE_CODE


def _layer(key: str, name: str, role: str) -> dict:
    return {
        "layer_key": key,
        "layer_id": key,
        "layer_name": name,
        "auto_role": role,
        "confirmed_role": role,
        "confirmation_state": "confirmed",
        "auto_confidence": "high",
    }


def _gradi_payload(*, finish_confirmed: bool = True) -> dict:
    payload = {
        "analysis_ready": True,
        "product_binding": {"template_code": ROOT},
        "svg_source": {"file_name": "gradi-curat.svg", "file_size_bytes": 27173, "upload_status": "analyzed"},
        "quote_geometry": {"letter_count": 19, "letter_perimeter_m": 31.638, "letter_face_area_m2": 3.05},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                _layer("letters", "Litere GRADI", "face"),
                _layer("logo_instance_001", "Logo 1", "printed_artwork"),
                _layer("logo_instance_002", "Logo 2", "printed_artwork"),
            ],
            "layer_bindings": [],
            "warnings": [],
        },
        "finish_setup": {
            "confirmed": True,
            "face_finish_type": "oracal_651",
            "return_depth_mm": 60,
            "return_finish_type": "white_aluminum",
            "artwork_finishes": [
                {
                    "layer_key": "logo_instance_001",
                    "layer_name": "Logo 1",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "return_depth_mm": 60,
                    "confirmed": finish_confirmed,
                },
                {
                    "layer_key": "logo_instance_002",
                    "layer_name": "Logo 2",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "return_depth_mm": 60,
                    "confirmed": finish_confirmed,
                },
            ],
        },
    }
    apply_product_composition_recommendation(payload)
    return payload


def _confirmed_bindings_payload() -> dict:
    payload = _gradi_payload()
    items = payload["product_composition_recommendation"]["composition_items"]
    persist_logo_layer_bindings_from_composition_confirmation(payload, confirmed=True, confirmed_items=items)
    payload["product_composition_confirmed"] = {"confirmed": True, "items": items}
    return payload


def _letters_only_payload() -> dict:
    payload = {
        "analysis_ready": True,
        "product_binding": {"template_code": ROOT},
        "svg_source": {"file_name": "letters.svg", "file_size_bytes": 1000, "upload_status": "analyzed"},
        "quote_geometry": {"letter_count": 5, "letter_perimeter_m": 2.0, "letter_face_area_m2": 0.5},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [_layer("letters", "Litere", "face")],
            "layer_bindings": [],
            "warnings": [],
        },
        "finish_setup": {
            "confirmed": True,
            "face_finish_type": "oracal_651",
            "return_depth_mm": 60,
            "return_finish_type": "white_aluminum",
            "artwork_finishes": [],
        },
    }
    apply_product_composition_recommendation(payload)
    return payload


async def _seed_logo_template(session) -> None:
    await seed_tpl_volumetric_logo_v1()


async def _add_workspace(session, payload: dict) -> str:
    workspace_id = str(uuid.uuid4())
    session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-CBOM-{workspace_id[:8]}",
            title="Cost BOM workspace linked logo",
            template_code=ROOT,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await session.commit()
    return workspace_id


@pytest_asyncio.fixture
async def cost_bom_workspace_db(volumetric_v2_db):
    await _seed_logo_template(volumetric_v2_db)
    return volumetric_v2_db


@pytest_asyncio.fixture
async def workspace_bom_builder(cost_bom_workspace_db):
    service = AggregateCostBomBuilderService(cost_bom_workspace_db)

    async def _build(*, workspace_id: str | None = None):
        return await service.build_preview(ROOT, workspace_id=workspace_id)

    return _build


def _logo_materials(bom, *, segment: str | None = None):
    rows = [
        m
        for m in bom.costable_materials
        if m.source_template_code == VOLUMETRIC_LOGO_TEMPLATE_CODE
    ]
    if segment:
        rows = [m for m in rows if m.component_ref and segment in m.component_ref]
    return rows


def _logo_components(bom):
    return [c for c in bom.costable_components if "::" in c.component_id]


@pytest.mark.asyncio
async def test_builder_uses_build_for_workspace_when_workspace_id_present(cost_bom_workspace_db) -> None:
    workspace_id = await _add_workspace(cost_bom_workspace_db, _confirmed_bindings_payload())
    service = AggregateCostBomBuilderService(cost_bom_workspace_db)
    real_svc = ProductAggregateService(cost_bom_workspace_db)
    with patch.object(
        ProductAggregateService,
        "build_for_workspace",
        new_callable=AsyncMock,
        side_effect=real_svc.build_for_workspace,
    ) as build_for_workspace:
        bom = await service.build_preview(ROOT, workspace_id=workspace_id)
        assert bom is not None
        build_for_workspace.assert_awaited_once_with(ROOT, workspace_id)


@pytest.mark.asyncio
async def test_builder_uses_template_build_without_workspace_id(cost_bom_workspace_db) -> None:
    service = AggregateCostBomBuilderService(cost_bom_workspace_db)
    with patch.object(ProductAggregateService, "build_for_workspace", new_callable=AsyncMock) as build_for_workspace:
        bom = await service.build_preview(ROOT)
        assert bom is not None
        build_for_workspace.assert_not_awaited()


@pytest.mark.asyncio
async def test_adapter_consumes_built_aggregate_not_recompiled(cost_bom_workspace_db) -> None:
    workspace_id = await _add_workspace(cost_bom_workspace_db, _confirmed_bindings_payload())
    pd_builder = ProductDefinitionBuilderService(cost_bom_workspace_db)
    aggregate_svc = ProductAggregateService(cost_bom_workspace_db)
    pd = await pd_builder.build_preview(ROOT, workspace_id=workspace_id)
    aggregate = await aggregate_svc.build_for_workspace(ROOT, workspace_id)
    assert pd is not None and aggregate is not None

    adapter = AggregateCostBomAdapter()
    with patch.object(ProductDefinitionBuilderService, "build_preview", new_callable=AsyncMock) as pd_mock:
        bom = adapter.build(
            product_definition=pd,
            aggregate=aggregate,
            material_rates=SAMPLE_RATES,
            workcenter_rates=SAMPLE_WC_RATES,
            inventory_catalog=INVENTORY_CATALOG,
        )
        pd_mock.assert_not_awaited()
    assert _logo_components(bom)


def test_adapter_module_has_no_binding_or_recommendation_imports() -> None:
    from services import aggregate_cost_bom_adapter as module

    source = inspect.getsource(module)
    forbidden = (
        "intake_v6_layer_binding_persistence",
        "product_composition_recommendation",
        "persist_logo_layer_bindings",
        "apply_product_composition_recommendation",
    )
    for token in forbidden:
        assert token not in source


@pytest.mark.asyncio
async def test_letters_only_workspace_matches_template_bom(workspace_bom_builder, cost_bom_workspace_db) -> None:
    workspace_id = await _add_workspace(cost_bom_workspace_db, _letters_only_payload())
    template_bom = await workspace_bom_builder()
    workspace_bom = await workspace_bom_builder(workspace_id=workspace_id)

    template_component_ids = {c.component_id for c in template_bom.costable_components}
    workspace_component_ids = {c.component_id for c in workspace_bom.costable_components}
    assert workspace_component_ids == template_component_ids
    assert not _logo_components(workspace_bom)
    template_material_keys = {
        (m.material_code, m.component_ref) for m in template_bom.costable_materials
    }
    workspace_material_keys = {
        (m.material_code, m.component_ref) for m in workspace_bom.costable_materials
    }
    assert workspace_material_keys == template_material_keys


@pytest.mark.asyncio
async def test_two_logo_segments_produce_distinct_bom_rows(workspace_bom_builder, cost_bom_workspace_db) -> None:
    workspace_id = await _add_workspace(cost_bom_workspace_db, _confirmed_bindings_payload())
    bom = await workspace_bom_builder(workspace_id=workspace_id)

    logo_ids = {c.component_id for c in _logo_components(bom)}
    assert "comp_logo_face::logo_instance_001" in logo_ids
    assert "comp_logo_face::logo_instance_002" in logo_ids

    stanga = _logo_materials(bom, segment="logo_instance_001")
    dreapta = _logo_materials(bom, segment="logo_instance_002")
    assert stanga
    assert dreapta
    stanga_refs = {m.component_ref for m in stanga}
    dreapta_refs = {m.component_ref for m in dreapta}
    assert stanga_refs.isdisjoint(dreapta_refs)


@pytest.mark.asyncio
async def test_logo_rows_use_same_linked_template_twice(workspace_bom_builder, cost_bom_workspace_db) -> None:
    workspace_id = await _add_workspace(cost_bom_workspace_db, _confirmed_bindings_payload())
    bom = await workspace_bom_builder(workspace_id=workspace_id)

    logo_materials = _logo_materials(bom)
    assert len(logo_materials) >= 2
    assert all(m.source_template_code == VOLUMETRIC_LOGO_TEMPLATE_CODE for m in logo_materials)


@pytest.mark.asyncio
async def test_missing_binding_creates_no_logo_bom_rows(workspace_bom_builder, cost_bom_workspace_db) -> None:
    workspace_id = await _add_workspace(cost_bom_workspace_db, _gradi_payload())
    template_bom = await workspace_bom_builder()
    workspace_bom = await workspace_bom_builder(workspace_id=workspace_id)

    assert not _logo_components(workspace_bom)
    assert {c.component_id for c in workspace_bom.costable_components} == {
        c.component_id for c in template_bom.costable_components
    }


@pytest.mark.asyncio
async def test_missing_finish_partial_bom_without_fabricated_logo_materials(
    workspace_bom_builder, cost_bom_workspace_db
) -> None:
    payload = _confirmed_bindings_payload()
    payload["finish_setup"]["artwork_finishes"][0]["confirmed"] = False
    payload["finish_setup"]["artwork_finishes"][1]["confirmed"] = False
    workspace_id = await _add_workspace(cost_bom_workspace_db, payload)
    bom = await workspace_bom_builder(workspace_id=workspace_id)

    assert _logo_components(bom)
    assert _logo_materials(bom) == []
    assert bom.bom_status == "partial"
    assert any(WARNING_FINISH_PARTIAL in w or WARNING_LINKED_SEGMENT_FINISH_PARTIAL in w for w in bom.warnings)
    assert bom.costable_materials


@pytest.mark.asyncio
async def test_print_and_laminate_map_when_finish_complete(workspace_bom_builder, cost_bom_workspace_db) -> None:
    workspace_id = await _add_workspace(cost_bom_workspace_db, _confirmed_bindings_payload())
    bom = await workspace_bom_builder(workspace_id=workspace_id)

    material_codes = {m.material_code for m in _logo_materials(bom)}
    assert "print_media" in material_codes
    assert "laminate_media" in material_codes


@pytest.mark.asyncio
async def test_logo_provenance_preserved_on_bom_rows(workspace_bom_builder, cost_bom_workspace_db) -> None:
    workspace_id = await _add_workspace(cost_bom_workspace_db, _confirmed_bindings_payload())
    bom = await workspace_bom_builder(workspace_id=workspace_id)

    for row in _logo_materials(bom):
        assert row.source_template_code == VOLUMETRIC_LOGO_TEMPLATE_CODE
        assert row.component_ref and "::" in row.component_ref

    letter_rows = [c for c in bom.costable_components if "::" not in c.component_id]
    assert letter_rows
    assert all(c.source_template_code == ROOT for c in letter_rows)


@pytest.mark.asyncio
async def test_composition_applied_warning_propagates(workspace_bom_builder, cost_bom_workspace_db) -> None:
    workspace_id = await _add_workspace(cost_bom_workspace_db, _confirmed_bindings_payload())
    bom = await workspace_bom_builder(workspace_id=workspace_id)
    assert any(WARNING_COMPOSITION_APPLIED in w for w in bom.warnings)


@pytest.mark.asyncio
async def test_no_commercial_price_fields_on_bom(workspace_bom_builder, cost_bom_workspace_db) -> None:
    workspace_id = await _add_workspace(cost_bom_workspace_db, _confirmed_bindings_payload())
    bom = await workspace_bom_builder(workspace_id=workspace_id)
    dumped = bom.model_dump()
    forbidden_keys = ("commercial_price", "client_price", "offer_price", "markup", "margin", "vat")
    assert not any(key in dumped for key in forbidden_keys)


def test_cost_bom_preview_endpoint_without_workspace(volumetric_auth_client):
    response = volumetric_auth_client.get(f"/api/v1/product-system/cost-bom-preview/{ROOT}")
    assert response.status_code == 200
    body = response.json()
    assert body["template_code"] == ROOT
    assert not any("::" in c["component_id"] for c in body.get("costable_components", []))


def test_cost_bom_preview_endpoint_letters_only_workspace(volumetric_auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            await _seed_volumetric_v2_fixture(session)
            await _seed_logo_template(session)
            return await _add_workspace(session, _letters_only_payload())

    workspace_id = db_fixture.run(_seed())
    response = volumetric_auth_client.get(
        f"/api/v1/product-system/cost-bom-preview/{ROOT}",
        params={"workspace_id": workspace_id},
    )
    assert response.status_code == 200
    body = response.json()
    assert not any("::" in c["component_id"] for c in body.get("costable_components", []))


def test_cost_bom_preview_endpoint_two_logo_segments(volumetric_auth_client, db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            await _seed_volumetric_v2_fixture(session)
            await _seed_logo_template(session)
            return await _add_workspace(session, _confirmed_bindings_payload())

    workspace_id = db_fixture.run(_seed())
    response = volumetric_auth_client.get(
        f"/api/v1/product-system/cost-bom-preview/{ROOT}",
        params={"workspace_id": workspace_id},
    )
    assert response.status_code == 200
    body = response.json()
    component_ids = {c["component_id"] for c in body.get("costable_components", [])}
    assert "comp_logo_face::logo_instance_001" in component_ids
    assert "comp_logo_face::logo_instance_002" in component_ids
    logo_materials = [
        m for m in body.get("costable_materials", [])
        if m.get("source_template_code") == VOLUMETRIC_LOGO_TEMPLATE_CODE
    ]
    assert logo_materials
    assert "commercial_price" not in body


def test_cost_bom_preview_endpoint_partial_logo_finish(volumetric_auth_client, db_fixture):
    payload = _confirmed_bindings_payload()
    payload["finish_setup"]["artwork_finishes"][0]["confirmed"] = False
    payload["finish_setup"]["artwork_finishes"][1]["confirmed"] = False

    async def _seed():
        async with db_fixture.session_maker() as session:
            await _seed_volumetric_v2_fixture(session)
            await _seed_logo_template(session)
            return await _add_workspace(session, payload)

    workspace_id = db_fixture.run(_seed())
    response = volumetric_auth_client.get(
        f"/api/v1/product-system/cost-bom-preview/{ROOT}",
        params={"workspace_id": workspace_id},
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("bom_status") == "partial"
    logo_materials = [
        m for m in body.get("costable_materials", [])
        if m.get("source_template_code") == VOLUMETRIC_LOGO_TEMPLATE_CODE
    ]
    assert logo_materials == []
    assert any(WARNING_FINISH_PARTIAL in w for w in body.get("warnings", []))
