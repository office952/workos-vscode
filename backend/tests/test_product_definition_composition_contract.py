"""Product Definition composed-graph contract V1 — Cases A–D, blockers, legacy."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_templates import Product_templates
from schemas.product_definition import ProductDefinitionComposition
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.product_definition_composition_contract import (
    BLOCKER_AMBIGUOUS_STRUCTURA_SUPORT,
    BLOCKER_AMBIGUOUS_SUPPORT_HIERARCHY,
    BLOCKER_DUPLICATE_ROLE_ASSIGNMENT,
    BLOCKER_MISSING_ACM_TO_PREMOUNT_EDGE,
    BLOCKER_MOUNTING_SCOPE_INACTIVE,
    BLOCKER_UNKNOWN_CHILD_TEMPLATE,
    METAL_PREMOUNT_TEMPLATE_CODE,
    PRODUCT_DEFINITION_COMPOSITION_PILOT_KEY,
    WARN_INTAKE_COMPOSITION_MODE_LIMITED,
    WARN_LEGACY_MOUNTING_SYSTEM_FALLBACK,
    build_product_definition_composition,
    freeze_mounting_resolution,
)
from services.mounting_solution_service import ACM_BOXED_MOUNTING_TEMPLATE_CODE

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
VOLUM_AL = "TPL-VOLUM-ALUMINIU_v1"


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


def _payload_direct_mounting() -> dict:
    payload = _base_payload()
    payload["finish_setup"]["mounting_scope"] = "none"
    payload["finish_setup"]["mounting_system"] = "direct_wall"
    return payload


def _payload_acm_only() -> dict:
    payload = _base_payload()
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
    payload = _base_payload()
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
            workspace_code=f"WS-COMP-{workspace_id[:8]}",
            title="Composition contract test",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await session.commit()
    return workspace_id


def _child_nodes(composition: ProductDefinitionComposition, role: str):
    return [n for n in composition.nodes if n.node_role == role and n.included_in_graph]


def _edge_between(composition: ProductDefinitionComposition, parent: str, child: str, relation: str | None = None):
    for edge in composition.edges:
        if edge.parent_template_code == parent and edge.child_template_code == child:
            if relation is None or edge.relation_type == relation:
                return edge
    return None


@pytest.mark.asyncio
async def test_case_a_direct_mounting_no_support_children(pd_builder, volumetric_v2_db):
    ws = await _workspace(volumetric_v2_db, _payload_direct_mounting())
    preview = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    assert preview and preview.composition
    comp = preview.composition
    assert _child_nodes(comp, "mounting_panel") == []
    assert _child_nodes(comp, "premount_structure") == []
    assert _child_nodes(comp, "volum_aluminum")
    assert comp.solution_status == "confirmed"
    structura_states = [
        m.state
        for m in preview.selected_modules + preview.optional_modules + preview.inactive_modules
        if m.module_code == "structura_suport"
    ]
    assert structura_states and "active" not in structura_states


@pytest.mark.asyncio
async def test_case_b_acm_only_mounting_panel(pd_builder, volumetric_v2_db):
    await _seed_acm_child(volumetric_v2_db)
    ws = await _workspace(volumetric_v2_db, _payload_acm_only())
    preview = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    assert preview and preview.composition
    comp = preview.composition
    acm_nodes = _child_nodes(comp, "mounting_panel")
    assert len(acm_nodes) == 1
    assert acm_nodes[0].template_code == ACM_BOXED_MOUNTING_TEMPLATE_CODE
    assert acm_nodes[0].module_role == "mounting_support"
    assert _child_nodes(comp, "premount_structure") == []
    edge = _edge_between(comp, TEMPLATE, ACM_BOXED_MOUNTING_TEMPLATE_CODE, "visual_mounting_support")
    assert edge is not None
    assert edge.child_role == "mounting_panel"
    assert "panel_width_mm" in edge.locally_owned_inputs or "panel_width_mm" in edge.inherited_inputs


@pytest.mark.asyncio
async def test_case_c_premount_only_structural_dependency(pd_builder, volumetric_v2_db):
    ws = await _workspace(volumetric_v2_db, _payload_premount_only())
    preview = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    assert preview and preview.composition
    comp = preview.composition
    premount_nodes = _child_nodes(comp, "premount_structure")
    assert len(premount_nodes) == 1
    assert premount_nodes[0].template_code == METAL_PREMOUNT_TEMPLATE_CODE
    assert _child_nodes(comp, "mounting_panel") == []
    edge = _edge_between(comp, TEMPLATE, METAL_PREMOUNT_TEMPLATE_CODE, "structural_dependency")
    assert edge is not None
    assert premount_nodes[0].unresolved_inputs or premount_nodes[0].locally_owned_inputs


@pytest.mark.asyncio
async def test_case_d_acm_premount_chain(pd_builder, volumetric_v2_db):
    await _seed_acm_child(volumetric_v2_db)
    ws = await _workspace(volumetric_v2_db, _payload_acm_premount_chain())
    preview = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    assert preview and preview.composition
    comp = preview.composition
    assert comp.composition_mode == "mounting_chain"
    assert len(_child_nodes(comp, "mounting_panel")) == 1
    assert len(_child_nodes(comp, "premount_structure")) == 1
    letters_acm = _edge_between(comp, TEMPLATE, ACM_BOXED_MOUNTING_TEMPLATE_CODE, "visual_mounting_support")
    acm_premount = _edge_between(comp, ACM_BOXED_MOUNTING_TEMPLATE_CODE, METAL_PREMOUNT_TEMPLATE_CODE, "structural_dependency")
    assert letters_acm is not None
    assert acm_premount is not None
    assert acm_premount.dependency_role == "supports_acm_assembly"
    assert BLOCKER_DUPLICATE_ROLE_ASSIGNMENT not in comp.blockers
    assert "CONFLICTING_MOUNTING_SOLUTIONS" not in comp.blockers


@pytest.mark.asyncio
async def test_invalid_chain_missing_acm_to_premount_edge():
    payload = _payload_acm_only()
    payload[PRODUCT_DEFINITION_COMPOSITION_PILOT_KEY] = {
        "composition_mode": "mounting_chain",
        "supporting_template_codes": [],
    }
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=payload,
        source_payload_type="workspace_payload",
    )
    assert BLOCKER_MISSING_ACM_TO_PREMOUNT_EDGE in comp.blockers


@pytest.mark.asyncio
async def test_invalid_chain_duplicate_role_assignment():
    payload = _payload_premount_only()
    payload[PRODUCT_DEFINITION_COMPOSITION_PILOT_KEY] = {"_force_duplicate_role": True}
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=payload,
        source_payload_type="workspace_payload",
    )
    assert BLOCKER_DUPLICATE_ROLE_ASSIGNMENT in comp.blockers


@pytest.mark.asyncio
async def test_invalid_chain_ambiguous_support_hierarchy():
    payload = _payload_premount_only()
    payload[PRODUCT_DEFINITION_COMPOSITION_PILOT_KEY] = {
        "composition_mode": "mounting_chain",
        "supporting_template_codes": [ACM_BOXED_MOUNTING_TEMPLATE_CODE],
    }
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=payload,
        source_payload_type="workspace_payload",
    )
    assert BLOCKER_AMBIGUOUS_SUPPORT_HIERARCHY in comp.blockers


@pytest.mark.asyncio
async def test_legacy_mounting_system_hydrates_acm(pd_builder, volumetric_v2_db):
    await _seed_acm_child(volumetric_v2_db)
    payload = _base_payload()
    payload["finish_setup"]["mounting_system"] = "acm_panel"
    payload["finish_setup"].pop("mounting_solution", None)
    ws = await _workspace(volumetric_v2_db, payload)
    preview = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    assert preview and preview.composition
    assert WARN_LEGACY_MOUNTING_SYSTEM_FALLBACK in preview.composition.warnings
    assert _child_nodes(preview.composition, "mounting_panel")


@pytest.mark.asyncio
async def test_canonical_solution_precedence_over_legacy(pd_builder, volumetric_v2_db):
    payload = _payload_premount_only()
    payload["finish_setup"]["mounting_system"] = "acm_panel"
    ws = await _workspace(volumetric_v2_db, payload)
    preview = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    assert preview and preview.composition
    assert _child_nodes(preview.composition, "premount_structure")
    assert _child_nodes(preview.composition, "mounting_panel") == []


@pytest.mark.asyncio
async def test_unknown_child_template_blocker():
    payload = _base_payload()
    payload["finish_setup"]["mounting_solution"] = {
        "template_code": "TPL-UNKNOWN-CHILD_v9",
        "configuration": {},
    }
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=payload,
        source_payload_type="workspace_payload",
    )
    assert BLOCKER_UNKNOWN_CHILD_TEMPLATE in comp.blockers


@pytest.mark.asyncio
async def test_acm_product_support_valid_with_mounting_scope_none():
    """D1/D2: ACM product support remains active when commercial mounting is none."""
    payload = _payload_acm_only()
    payload["finish_setup"]["mounting_scope"] = "none"
    payload["finish_setup"].pop("volum_aluminum_module_template_code", None)
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=payload,
        source_payload_type="workspace_payload",
    )
    assert BLOCKER_MOUNTING_SCOPE_INACTIVE not in comp.blockers
    assert any(
        n.template_code == ACM_BOXED_MOUNTING_TEMPLATE_CODE and n.included_in_graph
        for n in comp.nodes
    )


@pytest.mark.asyncio
async def test_metal_premount_not_in_graph_when_mounting_scope_none():
    payload = _base_payload()
    payload["finish_setup"]["mounting_scope"] = "none"
    payload["finish_setup"]["mounting_solution"] = {
        "template_code": METAL_PREMOUNT_TEMPLATE_CODE,
        "configuration": {
            "bar_count": 2,
            "mounting_bar_profile": "30x30x1.5",
            "bar_material": "steel",
        },
    }
    payload["finish_setup"].pop("volum_aluminum_module_template_code", None)
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=payload,
        source_payload_type="workspace_payload",
    )
    assert BLOCKER_MOUNTING_SCOPE_INACTIVE not in comp.blockers
    assert not any(
        n.template_code == METAL_PREMOUNT_TEMPLATE_CODE and n.included_in_graph
        for n in comp.nodes
    )


@pytest.mark.asyncio
async def test_ambiguous_structura_without_child_identity():
    payload = _base_payload()
    payload["finish_setup"]["mounting_system"] = "steel_bars"
    payload["finish_setup"].pop("mounting_solution", None)
    payload["finish_setup"]["mounting_scope"] = "none"
    payload["finish_setup"].pop("volum_aluminum_module_template_code", None)
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=payload,
        source_payload_type="workspace_payload",
    )
    assert BLOCKER_AMBIGUOUS_STRUCTURA_SUPORT in comp.blockers


def test_schema_round_trip():
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=_payload_acm_premount_chain(),
        source_payload_type="workspace_payload",
    )
    restored = ProductDefinitionComposition.model_validate(comp.model_dump())
    assert restored.model_dump() == comp.model_dump()


def test_reason_code_stability():
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=_payload_acm_only(),
        source_payload_type="workspace_payload",
    )
    assert all(isinstance(code, str) and code.isupper() or ":" in code for code in comp.blockers + comp.warnings)


def test_edge_deterministic_order():
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=_payload_acm_premount_chain(),
        source_payload_type="workspace_payload",
    )
    keys = [(e.parent_template_code, e.child_template_code, e.relation_type) for e in comp.edges]
    assert keys == sorted(keys)


def test_node_and_edge_id_deterministic():
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=_payload_acm_premount_chain(),
        source_payload_type="workspace_payload",
    )
    again = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=_payload_acm_premount_chain(),
        source_payload_type="workspace_payload",
    )
    assert [n.node_id for n in comp.nodes] == [n.node_id for n in again.nodes]
    assert [e.edge_id for e in comp.edges] == [e.edge_id for e in again.edges]


@pytest.mark.asyncio
async def test_backward_compatible_preview_fields(pd_builder, volumetric_v2_db):
    ws = await _workspace(volumetric_v2_db, _payload_direct_mounting())
    preview = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    assert preview is not None
    dumped = preview.model_dump()
    for key in (
        "preview_version",
        "template_code",
        "selected_modules",
        "components",
        "canonical_values",
        "validation",
        "warnings",
    ):
        assert key in dumped
    assert "composition" in dumped


@pytest.mark.asyncio
async def test_intake_composition_mode_limited_warning():
    payload = _payload_acm_only()
    payload[PRODUCT_DEFINITION_COMPOSITION_PILOT_KEY] = {"composition_mode": "mounting_chain"}
    comp = build_product_definition_composition(
        root_template_code=TEMPLATE,
        payload=payload,
        source_payload_type="workspace_payload",
    )
    assert WARN_INTAKE_COMPOSITION_MODE_LIMITED in comp.warnings


def test_freeze_mounting_resolution_single_path():
    finish = _payload_acm_only()["finish_setup"]
    frozen = freeze_mounting_resolution(finish=finish, payload=_payload_acm_only())
    assert frozen.resolved_solution is not None
    assert frozen.selected_solution_id == ACM_BOXED_MOUNTING_TEMPLATE_CODE
    assert frozen.activation_source == "canonical_mounting_solution"


@pytest.mark.asyncio
async def test_quote_geometry_resolves_dimensions_without_client(pd_builder, volumetric_v2_db):
    payload = _payload_acm_only()
    payload["client"] = {}
    payload["quote_geometry"]["width_mm"] = 1180
    payload["quote_geometry"]["height_mm"] = 390
    payload["quote_geometry"].pop("letter_face_area_m2", None)
    payload["quote_geometry"]["face_area_m2"] = 2.95
    ws = await _workspace(volumetric_v2_db, payload)
    preview = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    assert preview is not None
    assert preview.canonical_values.get("width_mm") == 1180
    assert preview.canonical_values.get("height_mm") == 390
    assert preview.canonical_values.get("letter_face_area_m2") == 2.95
    assert "width_mm" not in preview.validation.missing_required_fields
    assert "height_mm" not in preview.validation.missing_required_fields
    assert "letter_face_area_m2" not in preview.validation.missing_required_fields


@pytest.mark.asyncio
async def test_mounting_system_projected_from_canonical_solution(pd_builder, volumetric_v2_db):
    await _seed_acm_child(volumetric_v2_db)
    payload = _payload_acm_only()
    payload["finish_setup"].pop("mounting_system", None)
    ws = await _workspace(volumetric_v2_db, payload)
    preview = await pd_builder.build_preview(TEMPLATE, workspace_id=ws)
    assert preview is not None
    assert preview.canonical_values.get("mounting_system") == "acm_panel"
    assert "mounting_system" not in preview.validation.missing_required_fields
