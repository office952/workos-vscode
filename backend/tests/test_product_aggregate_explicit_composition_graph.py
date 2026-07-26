"""Product Aggregate explicit composition graph consumption — W2-T02."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_templates import Product_templates
from services.mounting_solution_service import (
    ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    METAL_PREMOUNT_TEMPLATE_CODE,
)
from services.product_aggregate_explicit_composition_service import (
    CONFLICT_COMPOSITION_BLOCKED,
    WARNING_EXPLICIT_GRAPH_APPLIED,
    WARNING_UPSTREAM_TRUTH_MISSING,
    apply_explicit_composition_graph,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_definition_composition_contract import PRODUCT_DEFINITION_COMPOSITION_PILOT_KEY

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
VOLUM_AL = "TPL-VOLUM-ALUMINIU_v1"


@pytest_asyncio.fixture
async def aggregate_svc(volumetric_v2_db):
    yield ProductAggregateService(volumetric_v2_db)


@pytest_asyncio.fixture
async def pd_builder(volumetric_v2_db):
    yield ProductDefinitionBuilderService(volumetric_v2_db)


async def _seed_acm_child(session) -> None:
    from sqlalchemy import select

    existing = await session.execute(
        select(Product_templates).where(Product_templates.template_code == ACM_BOXED_MOUNTING_TEMPLATE_CODE).limit(1)
    )
    if existing.scalar_one_or_none() is not None:
        return
    session.add(
        Product_templates(
            template_code=ACM_BOXED_MOUNTING_TEMPLATE_CODE,
            family_id="acm_boxed_mounting",
            family_name="ACM boxed mounting",
            components_json=json.dumps([{"component_id": "comp_acm_panel"}]),
            operations_json=json.dumps([{"code": "acm_panel_fold", "workcenter": "WC_ACM"}]),
            required_materials_json=json.dumps([{"material_code": "MAT-ACM-PANEL"}]),
            active=True,
        )
    )
    await session.commit()


def _base_payload() -> dict:
    return {
        "analysis_ready": True,
        "svg_source": {"file_name": "letters.svg"},
        "client": {"width_mm": 1200, "height_mm": 400},
        "quote_geometry": {
            "letter_count": 5,
            "letter_perimeter_m": 12.5,
            "letter_face_area_m2": 1.2,
            "width_mm": 1200,
            "height_mm": 400,
        },
        "finish_setup": {
            "face_finish_type": "plexiglas_clear",
            "return_depth_mm": 60,
            "return_finish_type": "ral",
            "volum_aluminum_module_template_code": VOLUM_AL,
            "backing_mode": "closed_back",
            "mounting_scope": "preparation_only",
            "mounting_system": "direct_wall",
            "lighting_system_type": "front_lit",
            "illuminated": True,
        },
    }


def _mounting_payload_base() -> dict:
    """Base payload without volum child — isolates mounting composition cases."""
    payload = _base_payload()
    payload["finish_setup"].pop("volum_aluminum_module_template_code", None)
    return payload


def _payload_direct_mounting() -> dict:
    payload = _mounting_payload_base()
    payload["finish_setup"]["mounting_scope"] = "none"
    payload["finish_setup"]["mounting_system"] = "direct_wall"
    return payload


def _payload_acm_only() -> dict:
    payload = _mounting_payload_base()
    payload["finish_setup"]["mounting_solution"] = {
        "template_code": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
        "configuration": {
            "panel_width_mm": 1200,
            "panel_height_mm": 400,
            "acm_thickness_mm": 3,
            "return_depth_mm": 60,
        },
    }
    payload["finish_setup"]["mounting_system"] = None
    return payload


def _payload_premount_only() -> dict:
    payload = _mounting_payload_base()
    payload["finish_setup"]["mounting_solution"] = {
        "template_code": METAL_PREMOUNT_TEMPLATE_CODE,
        "configuration": {
            "bar_count": 2,
            "mounting_bar_profile": "30x30x1.5",
            "bar_material": "steel",
        },
    }
    payload["finish_setup"]["mounting_system"] = None
    return payload


def _payload_acm_premount_chain() -> dict:
    payload = _payload_acm_only()
    payload[PRODUCT_DEFINITION_COMPOSITION_PILOT_KEY] = {
        "composition_mode": "mounting_chain",
        "supporting_template_codes": [METAL_PREMOUNT_TEMPLATE_CODE],
        "premount_configuration": {
            "bar_count": 2,
            "mounting_bar_profile": "30x30x1.5",
            "bar_material": "steel",
        },
    }
    return payload


async def _workspace(session, payload: dict) -> str:
    workspace_id = str(uuid.uuid4())
    session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-AGG-{workspace_id[:8]}",
            title="Aggregate graph test",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await session.commit()
    return workspace_id


def _child_codes(aggregate) -> list[str]:
    graph = aggregate.composition_graph
    assert graph is not None
    return list(graph.active_child_template_codes)


def _module_codes(aggregate) -> list[str]:
    return sorted(
        {
            module.child_template_code
            for module in [*aggregate.modules.required, *aggregate.modules.optional]
        }
    )


@pytest.mark.asyncio
async def test_case_b_aggregate_consumes_explicit_acm_child(aggregate_svc, pd_builder, volumetric_v2_db):
    await _seed_acm_child(volumetric_v2_db)
    ws = await _workspace(volumetric_v2_db, _payload_acm_only())
    pd = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    assert pd and pd.composition
    aggregate = await aggregate_svc.build_for_workspace(TEMPLATE, ws)
    assert aggregate is not None
    assert aggregate.composition_graph is not None
    assert _child_codes(aggregate) == [ACM_BOXED_MOUNTING_TEMPLATE_CODE]
    assert VOLUM_AL not in _module_codes(aggregate)
    assert METAL_PREMOUNT_TEMPLATE_CODE not in _module_codes(aggregate)
    assert any(w.code == WARNING_EXPLICIT_GRAPH_APPLIED for w in aggregate.warnings)
    roles = {node.node_role for node in aggregate.composition_graph.nodes}
    assert "mounting_panel" in roles
    edge_roles = {edge.relation_type for edge in aggregate.composition_graph.edges}
    assert "visual_mounting_support" in edge_roles


@pytest.mark.asyncio
async def test_case_a_aggregate_root_only_children(aggregate_svc, pd_builder, volumetric_v2_db):
    ws = await _workspace(volumetric_v2_db, _payload_direct_mounting())
    aggregate = await aggregate_svc.build_for_workspace(TEMPLATE, ws)
    assert aggregate is not None
    assert aggregate.composition_graph is not None
    assert _child_codes(aggregate) == []
    assert ACM_BOXED_MOUNTING_TEMPLATE_CODE not in _module_codes(aggregate)
    assert METAL_PREMOUNT_TEMPLATE_CODE not in _module_codes(aggregate)


@pytest.mark.asyncio
async def test_case_c_aggregate_premount_only(aggregate_svc, pd_builder, volumetric_v2_db):
    ws = await _workspace(volumetric_v2_db, _payload_premount_only())
    aggregate = await aggregate_svc.build_for_workspace(TEMPLATE, ws)
    assert aggregate is not None
    assert _child_codes(aggregate) == [METAL_PREMOUNT_TEMPLATE_CODE]
    assert ACM_BOXED_MOUNTING_TEMPLATE_CODE not in _module_codes(aggregate)


@pytest.mark.asyncio
async def test_case_d_aggregate_acm_premount_chain(aggregate_svc, pd_builder, volumetric_v2_db):
    await _seed_acm_child(volumetric_v2_db)
    ws = await _workspace(volumetric_v2_db, _payload_acm_premount_chain())
    aggregate = await aggregate_svc.build_for_workspace(TEMPLATE, ws)
    assert aggregate is not None
    assert set(_child_codes(aggregate)) == {
        ACM_BOXED_MOUNTING_TEMPLATE_CODE,
        METAL_PREMOUNT_TEMPLATE_CODE,
    }
    assert aggregate.composition_graph.composition_mode == "mounting_chain"


@pytest.mark.asyncio
async def test_legacy_mounting_system_does_not_add_extra_children(aggregate_svc, pd_builder, volumetric_v2_db):
    payload = _payload_premount_only()
    payload["finish_setup"]["mounting_system"] = "acm_panel"
    ws = await _workspace(volumetric_v2_db, payload)
    aggregate = await aggregate_svc.build_for_workspace(TEMPLATE, ws)
    assert aggregate is not None
    assert _child_codes(aggregate) == [METAL_PREMOUNT_TEMPLATE_CODE]
    assert ACM_BOXED_MOUNTING_TEMPLATE_CODE not in _module_codes(aggregate)


@pytest.mark.asyncio
async def test_mounting_transition_removes_obsolete_child(aggregate_svc, pd_builder, volumetric_v2_db):
    await _seed_acm_child(volumetric_v2_db)
    ws_acm = await _workspace(volumetric_v2_db, _payload_acm_only())
    ws_direct = await _workspace(volumetric_v2_db, _payload_direct_mounting())
    agg_acm = await aggregate_svc.build_for_workspace(TEMPLATE, ws_acm)
    agg_direct = await aggregate_svc.build_for_workspace(TEMPLATE, ws_direct)
    assert ACM_BOXED_MOUNTING_TEMPLATE_CODE in _child_codes(agg_acm)
    assert _child_codes(agg_direct) == []


@pytest.mark.asyncio
async def test_graph_node_ids_stable_across_rebuild(aggregate_svc, pd_builder, volumetric_v2_db):
    await _seed_acm_child(volumetric_v2_db)
    ws = await _workspace(volumetric_v2_db, _payload_acm_only())
    first = await aggregate_svc.build_for_workspace(TEMPLATE, ws)
    second = await aggregate_svc.build_for_workspace(TEMPLATE, ws)
    assert [n.node_id for n in first.composition_graph.nodes] == [
        n.node_id for n in second.composition_graph.nodes
    ]
    assert [e.edge_id for e in first.composition_graph.edges] == [
        e.edge_id for e in second.composition_graph.edges
    ]


@pytest.mark.asyncio
async def test_finish_truth_preserved_on_graph_nodes(aggregate_svc, pd_builder, volumetric_v2_db):
    await _seed_acm_child(volumetric_v2_db)
    ws = await _workspace(volumetric_v2_db, _payload_acm_only())
    pd = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    aggregate = await aggregate_svc.build_for_workspace(TEMPLATE, ws)
    assert pd is not None
    assert pd.canonical_values.get("face_finish_type") == "plexiglas_clear"
    acm_nodes = [n for n in aggregate.composition_graph.nodes if n.node_role == "mounting_panel"]
    assert acm_nodes
    assert acm_nodes[0].locally_owned_inputs.get("panel_width_mm") == 1200


@pytest.mark.asyncio
async def test_volum_missing_is_nonblocking_upstream_warning(aggregate_svc, pd_builder, volumetric_v2_db):
    await _seed_acm_child(volumetric_v2_db)
    payload = _payload_acm_only()
    payload["finish_setup"].pop("volum_aluminum_module_template_code", None)
    ws = await _workspace(volumetric_v2_db, payload)
    pd = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    assert "volum_aluminum_module_template_code" in pd.validation.missing_required_fields
    aggregate = await aggregate_svc.build_for_workspace(TEMPLATE, ws)
    assert aggregate.composition_graph is not None
    assert VOLUM_AL not in _child_codes(aggregate)
    assert any(w.code == WARNING_UPSTREAM_TRUTH_MISSING for w in aggregate.conflicts + aggregate.warnings)


@pytest.mark.asyncio
async def test_blocked_composition_produces_aggregate_conflict(aggregate_svc, pd_builder, volumetric_v2_db):
    payload = _payload_acm_only()
    payload["finish_setup"]["mounting_scope"] = "none"
    ws = await _workspace(volumetric_v2_db, payload)
    aggregate = await aggregate_svc.build_for_workspace(TEMPLATE, ws)
    assert aggregate is not None
    assert any(c.code == CONFLICT_COMPOSITION_BLOCKED for c in aggregate.conflicts)


@pytest.mark.asyncio
async def test_apply_explicit_graph_unit_no_duplicate_children(aggregate_svc, pd_builder, volumetric_v2_db):
    await _seed_acm_child(volumetric_v2_db)
    ws = await _workspace(volumetric_v2_db, _payload_acm_only())
    pd = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    base = await aggregate_svc.build(TEMPLATE)
    child = await aggregate_svc.build(ACM_BOXED_MOUNTING_TEMPLATE_CODE)
    compiled = apply_explicit_composition_graph(
        pd=pd,
        base_aggregate=base,
        child_aggregates_by_template={ACM_BOXED_MOUNTING_TEMPLATE_CODE: child},
    )
    child_component_ids = [
        component.component_id
        for component in compiled.components
        if component.source_template_code == ACM_BOXED_MOUNTING_TEMPLATE_CODE
    ]
    assert len(child_component_ids) == len(set(child_component_ids))
