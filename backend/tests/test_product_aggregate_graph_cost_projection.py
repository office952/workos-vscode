"""Graph-to-cost projection — W3-T01 structural scope from composition_graph."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.aggregate_cost_bom_adapter import AggregateCostBomAdapter
from services.mounting_solution_service import (
    ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    METAL_PREMOUNT_TEMPLATE_CODE,
)
from services.product_aggregate_graph_cost_projection_service import (
    build_graph_cost_projection,
    resolve_cost_active_modules,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_definition_composition_contract import PRODUCT_DEFINITION_COMPOSITION_PILOT_KEY

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
VOLUM_AL = "TPL-VOLUM-ALUMINIU_v1"


def _mounting_payload_base() -> dict:
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
            "backing_mode": "closed_back",
            "mounting_scope": "preparation_only",
            "mounting_system": "direct_wall",
            "lighting_system_type": "front_lit",
            "illuminated": True,
            "selected_psu_watts": 100,
            "led_module_count": 180,
        },
    }


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


def _payload_with_volum() -> dict:
    payload = _payload_acm_only()
    payload["finish_setup"]["volum_aluminum_module_template_code"] = VOLUM_AL
    return payload


async def _workspace(session, payload: dict) -> str:
    workspace_id = str(uuid.uuid4())
    session.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-GCOST-{workspace_id[:8]}",
            title="Graph cost projection test",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await session.commit()
    return workspace_id


@pytest_asyncio.fixture
async def graph_cost_context(volumetric_v2_db):
    pd_builder = ProductDefinitionBuilderService(volumetric_v2_db)
    aggregate_svc = ProductAggregateService(volumetric_v2_db)
    adapter = AggregateCostBomAdapter()

    async def _build(payload: dict):
        ws = await _workspace(volumetric_v2_db, payload)
        pd = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
        aggregate = await aggregate_svc.build_for_workspace(TEMPLATE, ws)
        assert pd is not None and aggregate is not None
        bom = adapter.build(product_definition=pd, aggregate=aggregate)
        active, projection = resolve_cost_active_modules(pd=pd, aggregate=aggregate)
        return pd, aggregate, bom, projection, active

    yield _build


def _active_module_codes(bom) -> set[str]:
    return {m.module_code for m in bom.active_modules if m.included_in_cost_bom}


@pytest.mark.asyncio
async def test_case_a_root_only_no_structural_children(graph_cost_context):
    _, _, bom, projection, active = await graph_cost_context(_payload_direct_mounting())
    assert projection is not None
    assert projection.structural_authority == "composition_graph"
    assert "structura_suport" not in active
    assert "modelare_cant" not in active
    assert "structura_suport" not in _active_module_codes(bom)
    assert bom.graph_cost_projection is not None


@pytest.mark.asyncio
async def test_case_b_acm_mounting_panel_in_scope(graph_cost_context):
    _, aggregate, bom, projection, active = await graph_cost_context(_payload_acm_only())
    assert projection is not None
    assert "structura_suport" in active
    assert "modelare_cant" not in active
    assert ACM_BOXED_MOUNTING_TEMPLATE_CODE in projection.active_child_template_codes
    assert "structura_suport" in _active_module_codes(bom)
    premount_mats = [
        m for m in bom.costable_materials if "PREMOUNT" in (m.source_template_code or "")
    ]
    assert not premount_mats
    assert not any(n.node_role == "volum_aluminum" for n in aggregate.composition_graph.nodes)


@pytest.mark.asyncio
async def test_case_c_premount_only_in_scope(graph_cost_context):
    _, _, bom, projection, active = await graph_cost_context(_payload_premount_only())
    assert "structura_suport" in active
    assert METAL_PREMOUNT_TEMPLATE_CODE in projection.active_child_template_codes
    premount_mats = [
        m for m in bom.costable_materials if "PREMOUNT" in (m.source_template_code or "")
    ]
    assert premount_mats


@pytest.mark.asyncio
async def test_case_d_acm_plus_premount_chain(graph_cost_context):
    _, _, bom, projection, active = await graph_cost_context(_payload_acm_premount_chain())
    assert "structura_suport" in active
    assert ACM_BOXED_MOUNTING_TEMPLATE_CODE in projection.active_child_template_codes
    assert METAL_PREMOUNT_TEMPLATE_CODE in projection.active_child_template_codes
    assert len(projection.edges) >= 1


@pytest.mark.asyncio
async def test_steel_bars_without_graph_child_does_not_activate_structura(graph_cost_context):
    payload = _mounting_payload_base()
    payload["finish_setup"]["mounting_scope"] = "none"
    payload["finish_setup"]["mounting_system"] = "steel_bars"
    _, _, bom, projection, active = await graph_cost_context(payload)
    assert projection is not None
    assert "structura_suport" not in active
    assert "structura_suport" not in _active_module_codes(bom)


@pytest.mark.asyncio
async def test_repeated_projection_is_stable(graph_cost_context):
    _, _, _, proj1, active1 = await graph_cost_context(_payload_acm_only())
    _, _, _, proj2, active2 = await graph_cost_context(_payload_acm_only())
    assert active1 == active2
    assert proj1.active_mini_module_codes == proj2.active_mini_module_codes
    assert proj1.root_template_code == proj2.root_template_code


@pytest.mark.asyncio
async def test_graph_projection_preserves_roles_and_edges(graph_cost_context):
    _, _, _, projection, _ = await graph_cost_context(_payload_acm_premount_chain())
    roles = {n.node_role for n in projection.nodes}
    assert "mounting_panel" in roles
    assert "premount_structure" in roles
    assert any(e.relation_type for e in projection.edges)


@pytest.mark.asyncio
async def test_missing_volum_truth_explicit_blocker(graph_cost_context):
    pd, aggregate, bom, projection, active = await graph_cost_context(_payload_acm_only())
    assert "modelare_cant" not in active
    assert any(
        b.startswith("UPSTREAM_TRUTH_MISSING:volum_aluminum_module_template_code")
        for b in projection.blockers
    ) or "volum_aluminum_module_template_code" in pd.validation.missing_required_fields


@pytest.mark.asyncio
async def test_volum_in_graph_when_truth_present(graph_cost_context):
    _, _, bom, projection, active = await graph_cost_context(_payload_with_volum())
    assert "modelare_cant" in active
    assert VOLUM_AL in projection.active_child_template_codes
    assert "modelare_cant" in _active_module_codes(bom)


@pytest.mark.asyncio
async def test_projection_nodes_carry_finish_inputs(graph_cost_context):
    _, aggregate, _, projection, _ = await graph_cost_context(_payload_acm_only())
    root_nodes = [n for n in projection.nodes if n.node_role == "root"]
    assert root_nodes or projection.root_template_code == TEMPLATE
    mounting = next(n for n in projection.nodes if n.node_role == "mounting_panel")
    assert mounting.template_code == ACM_BOXED_MOUNTING_TEMPLATE_CODE
    assert mounting.module_code == "structura_suport"


@pytest.mark.asyncio
async def test_build_graph_cost_projection_deterministic_modules(graph_cost_context):
    pd, aggregate, _, _, _ = await graph_cost_context(_payload_acm_only())
    p1 = build_graph_cost_projection(pd=pd, aggregate=aggregate)
    p2 = build_graph_cost_projection(pd=pd, aggregate=aggregate)
    assert p1.active_mini_module_codes == p2.active_mini_module_codes
