from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.auth import UserResponse
from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
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
    compose_from_product_definition,
)
from services.product_definition_builder_service import ProductDefinitionBuilderService
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


def _gradi_payload(*, with_bindings: list[dict] | None = None, finish_confirmed: bool = True) -> dict:
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
            "layer_bindings": with_bindings or [],
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


@pytest_asyncio.fixture
async def aggregate_workspace_db(volumetric_v2_db):
    await _seed_logo_template(volumetric_v2_db)
    return volumetric_v2_db


async def _add_workspace(session, payload: dict) -> str:
    workspace_id = str(uuid.uuid4())
    session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-PA-{workspace_id[:8]}",
            title="ProductAggregate workspace composition",
            template_code=ROOT,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await session.commit()
    return workspace_id


@pytest.mark.asyncio
async def test_letters_only_workspace_matches_template_aggregate(aggregate_workspace_db) -> None:
    workspace_id = await _add_workspace(aggregate_workspace_db, _letters_only_payload())
    baseline = await ProductAggregateService(aggregate_workspace_db).build(ROOT)
    composed = await ProductAggregateService(aggregate_workspace_db).build_for_workspace(ROOT, workspace_id)

    assert baseline is not None
    assert composed is not None
    assert {component.component_id for component in composed.components} == {
        component.component_id for component in baseline.components
    }
    assert not any("::" in component.component_id for component in composed.components)
    assert not any(code == WARNING_COMPOSITION_APPLIED for code in {warning.code for warning in composed.warnings})


@pytest.mark.asyncio
async def test_two_confirmed_segments_produce_two_namespaced_logo_instances(aggregate_workspace_db) -> None:
    workspace_id = await _add_workspace(aggregate_workspace_db, _confirmed_bindings_payload())
    composed = await ProductAggregateService(aggregate_workspace_db).build_for_workspace(ROOT, workspace_id)

    assert composed is not None
    logo_component_ids = [component.component_id for component in composed.components if "::" in component.component_id]
    assert "comp_logo_face::logo_instance_001" in logo_component_ids
    assert "comp_logo_face::logo_instance_002" in logo_component_ids
    assert "comp_logo_finish::logo_instance_001" in logo_component_ids
    assert "comp_logo_finish::logo_instance_002" in logo_component_ids
    assert any(warning.code == WARNING_COMPOSITION_APPLIED for warning in composed.warnings)


@pytest.mark.asyncio
async def test_missing_binding_does_not_invent_logo_components(aggregate_workspace_db) -> None:
    workspace_id = await _add_workspace(aggregate_workspace_db, _gradi_payload())
    baseline = await ProductAggregateService(aggregate_workspace_db).build(ROOT)
    composed = await ProductAggregateService(aggregate_workspace_db).build_for_workspace(ROOT, workspace_id)

    assert baseline is not None
    assert composed is not None
    assert {component.component_id for component in composed.components} == {
        component.component_id for component in baseline.components
    }


@pytest.mark.asyncio
async def test_missing_finish_keeps_partial_logo_structure_without_materials(aggregate_workspace_db) -> None:
    payload = _confirmed_bindings_payload()
    payload["finish_setup"]["artwork_finishes"][0]["confirmed"] = False
    payload["finish_setup"]["artwork_finishes"][1]["confirmed"] = False
    workspace_id = await _add_workspace(aggregate_workspace_db, payload)
    composed = await ProductAggregateService(aggregate_workspace_db).build_for_workspace(ROOT, workspace_id)

    assert composed is not None
    partial_components = [
        component for component in composed.components if component.component_id.endswith("::logo_instance_001")
    ]
    assert partial_components
    assert all(component.status == "partial" for component in partial_components)
    logo_materials = [
        material
        for material in composed.materials
        if _text(material.source_template_code) == LOGO and "logo_instance_001" in _text(material.component_ref)
    ]
    assert logo_materials == []
    assert any(warning.code == WARNING_FINISH_PARTIAL for warning in composed.warnings)


def _text(value) -> str:
    return str(value or "").strip()


@pytest.mark.asyncio
async def test_confirmed_finish_includes_per_segment_logo_materials(aggregate_workspace_db) -> None:
    workspace_id = await _add_workspace(aggregate_workspace_db, _confirmed_bindings_payload())
    composed = await ProductAggregateService(aggregate_workspace_db).build_for_workspace(ROOT, workspace_id)

    assert composed is not None
    stanga_refs = {
        material.component_ref
        for material in composed.materials
        if material.source_template_code == LOGO and material.component_ref and "logo_instance_001" in material.component_ref
    }
    dreapta_refs = {
        material.component_ref
        for material in composed.materials
        if material.source_template_code == LOGO and material.component_ref and "logo_instance_002" in material.component_ref
    }
    assert stanga_refs
    assert dreapta_refs
    assert stanga_refs.isdisjoint(dreapta_refs)


@pytest.mark.asyncio
async def test_compose_uses_product_definition_not_direct_binding_reads(aggregate_workspace_db) -> None:
    workspace_id = await _add_workspace(aggregate_workspace_db, _confirmed_bindings_payload())
    pd = await ProductDefinitionBuilderService(aggregate_workspace_db).build_preview(ROOT, workspace_id=workspace_id)
    letters = await ProductAggregateService(aggregate_workspace_db).build(ROOT)
    logo = await ProductAggregateService(aggregate_workspace_db).build(LOGO)

    assert pd is not None
    assert letters is not None
    assert logo is not None
    composed = compose_from_product_definition(
        pd=pd,
        letters_aggregate=letters,
        logo_aggregates_by_segment={
            "logo_instance_001": logo,
            "logo_instance_002": logo,
        },
        workspace_id=workspace_id,
    )
    assert any(component.component_id == "comp_logo_face::logo_instance_001" for component in composed.components)
    assert any(component.component_id == "comp_logo_face::logo_instance_002" for component in composed.components)


@pytest.mark.asyncio
async def test_letters_rows_remain_traceable_to_letters_template(aggregate_workspace_db) -> None:
    workspace_id = await _add_workspace(aggregate_workspace_db, _confirmed_bindings_payload())
    composed = await ProductAggregateService(aggregate_workspace_db).build_for_workspace(ROOT, workspace_id)

    assert composed is not None
    letter_components = [component for component in composed.components if "::" not in component.component_id]
    assert letter_components
    assert all(component.source_template_code == ROOT for component in letter_components)


@pytest.mark.asyncio
async def test_task_rules_compose_per_segment(aggregate_workspace_db) -> None:
    workspace_id = await _add_workspace(aggregate_workspace_db, _confirmed_bindings_payload())
    composed = await ProductAggregateService(aggregate_workspace_db).build_for_workspace(ROOT, workspace_id)

    assert composed is not None
    logo_rules = [
        rule
        for rule in composed.task_contract.task_rules
        if rule.trigger_condition and rule.trigger_condition.startswith("linked_segment:")
    ]
    segment_keys = {rule.trigger_condition.split(":", 1)[1] for rule in logo_rules}
    assert "logo_instance_001" in segment_keys
    assert "logo_instance_002" in segment_keys


def test_get_endpoint_without_workspace_id_unchanged(volumetric_auth_client):
    response = volumetric_auth_client.get(f"/api/v1/product-system/aggregate/{ROOT}")
    assert response.status_code == 200
    body = response.json()
    assert body["template_code"] == ROOT
    assert len(body["components"]) == 5
    assert not any("::" in component["component_id"] for component in body["components"])


def test_get_endpoint_with_workspace_id_composes_logo_segments(volumetric_auth_client, db_fixture):
    payload = _confirmed_bindings_payload()

    async def _seed():
        async with db_fixture.session_maker() as session:
            await _seed_volumetric_v2_fixture(session)
            await _seed_logo_template(session)
            workspace_id = await _add_workspace(session, payload)
            return workspace_id

    workspace_id = db_fixture.run(_seed())
    response = volumetric_auth_client.get(
        f"/api/v1/product-system/aggregate/{ROOT}",
        params={"workspace_id": workspace_id},
    )
    assert response.status_code == 200
    body = response.json()
    component_ids = {component["component_id"] for component in body["components"]}
    assert "comp_logo_face::logo_instance_001" in component_ids
    assert "comp_logo_face::logo_instance_002" in component_ids
    assert any(warning["code"] == WARNING_COMPOSITION_APPLIED for warning in body.get("warnings", []))
