"""Logo artwork BOM ownership dedupe — cardinality and canonical owner contract."""

from __future__ import annotations

import pytest
import pytest_asyncio

from seeds.seed_tpl_volumetric_logo_v1 import CHILD_SPECS, _component_from_spec
from services.aggregate_cost_bom_adapter import AggregateCostBomBuilderService
from services.estimated_internal_cost_service import EstimatedInternalCostService
from services.logo_artwork_cost_ownership import (
    CANONICAL_ARTWORK_COMPONENT,
    LOGO_ARTWORK_MATERIAL_CODES,
    LOGO_ARTWORK_OPERATION_CODES,
)
from services.product_aggregate_service import ProductAggregateService
from services.template_architecture_scope import (
    VOLUMETRIC_LOGO_FACE_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_FINISH_TEMPLATE_CODE,
    VOLUMETRIC_LOGO_TEMPLATE_CODE,
)
from tests.eic_patched_bom_builder import PatchedAggregateCostBomBuilder
from tests.eic_workspace_logo_fixtures import (
    LOGO_INVENTORY,
    LOGO_MATERIAL_RATES,
    ROOT,
    add_workspace as _add_workspace,
    confirmed_bindings_payload as _confirmed_bindings_payload,
    gradi_payload as _gradi_payload,
    letters_only_payload as _letters_only_payload,
    quote_input_overlay as _quote_input_overlay,
    seed_logo_inventory_materials as _seed_logo_inventory_materials,
    seed_logo_template,
)
from tests.test_product_aggregate_volumetric_v2 import _seed_volumetric_v2_fixture

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

ARTWORK_OPS = LOGO_ARTWORK_OPERATION_CODES
ARTWORK_MATS = LOGO_ARTWORK_MATERIAL_CODES


def _child_spec(template_code: str) -> dict:
    for spec in CHILD_SPECS:
        if spec["template_code"] == template_code:
            return spec
    raise KeyError(template_code)


def test_seed_face_child_excludes_artwork_materials_and_operations() -> None:
    component = _component_from_spec(_child_spec(VOLUMETRIC_LOGO_FACE_TEMPLATE_CODE))
    material_codes = {row["material_code"] for row in component["materials"]}
    operation_codes = {row["code"] for row in component["operations"]}
    assert "logo_face_material" in material_codes
    assert "print_media" not in material_codes
    assert "laminate_media" not in material_codes
    assert "logo_face_cnc_cut" in operation_codes
    assert "logo_face_print" not in operation_codes
    assert "logo_face_laminate" not in operation_codes


def test_seed_finish_child_includes_artwork_materials_and_operations() -> None:
    component = _component_from_spec(_child_spec(VOLUMETRIC_LOGO_FINISH_TEMPLATE_CODE))
    material_codes = {row["material_code"] for row in component["materials"]}
    operation_codes = {row["code"] for row in component["operations"]}
    assert material_codes == {"print_media", "laminate_media"}
    assert operation_codes == {
        "logo_face_print",
        "logo_face_laminate",
        "logo_finish_application",
    }


@pytest_asyncio.fixture
async def ownership_db(volumetric_v2_db):
    await seed_logo_template(volumetric_v2_db)
    await _seed_logo_inventory_materials(volumetric_v2_db)
    return volumetric_v2_db


@pytest_asyncio.fixture
async def ownership_bom_builder(ownership_db):
    service = AggregateCostBomBuilderService(ownership_db)

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


def _logo_operations(bom, *, segment: str | None = None):
    rows = [
        o
        for o in bom.costable_operations
        if o.source_template_code == VOLUMETRIC_LOGO_TEMPLATE_CODE
    ]
    if segment:
        rows = [o for o in rows if o.component_ref and segment in o.component_ref]
    return rows


def _artwork_materials(bom, *, segment: str):
    return [
        m
        for m in _logo_materials(bom, segment=segment)
        if m.material_code in ARTWORK_MATS
    ]


def _artwork_operations(bom, *, segment: str):
    return [
        o
        for o in _logo_operations(bom, segment=segment)
        if o.operation_code in ARTWORK_OPS
    ]


@pytest.mark.asyncio
async def test_per_segment_artwork_material_cardinality(ownership_bom_builder, ownership_db) -> None:
    workspace_id = await _add_workspace(ownership_db, _confirmed_bindings_payload())
    bom = await ownership_bom_builder(workspace_id=workspace_id)
    for segment in ("logo-stanga", "logo-dreapta"):
        mats = _artwork_materials(bom, segment=segment)
        assert len(mats) == 2
        assert {m.material_code for m in mats} == ARTWORK_MATS
        assert {m.component_ref for m in mats} == {f"{CANONICAL_ARTWORK_COMPONENT}::{segment}"}


@pytest.mark.asyncio
async def test_per_segment_artwork_operation_cardinality(ownership_bom_builder, ownership_db) -> None:
    workspace_id = await _add_workspace(ownership_db, _confirmed_bindings_payload())
    bom = await ownership_bom_builder(workspace_id=workspace_id)
    for segment in ("logo-stanga", "logo-dreapta"):
        ops = _artwork_operations(bom, segment=segment)
        assert len(ops) == 3
        assert {o.operation_code for o in ops} == ARTWORK_OPS
        assert {o.component_ref for o in ops} == {f"{CANONICAL_ARTWORK_COMPONENT}::{segment}"}


@pytest.mark.asyncio
async def test_face_component_does_not_emit_artwork_rows(ownership_bom_builder, ownership_db) -> None:
    workspace_id = await _add_workspace(ownership_db, _confirmed_bindings_payload())
    bom = await ownership_bom_builder(workspace_id=workspace_id)
    for segment in ("logo-stanga", "logo-dreapta"):
        face_artwork_mats = [
            m
            for m in _logo_materials(bom, segment=segment)
            if m.material_code in ARTWORK_MATS and m.component_ref.startswith("comp_logo_face::")
        ]
        face_artwork_ops = [
            o
            for o in _logo_operations(bom, segment=segment)
            if o.operation_code in ARTWORK_OPS and o.component_ref.startswith("comp_logo_face::")
        ]
        assert face_artwork_mats == []
        assert face_artwork_ops == []


@pytest.mark.asyncio
async def test_mapping_only_linked_segment_not_costable(ownership_bom_builder, ownership_db) -> None:
    workspace_id = await _add_workspace(ownership_db, _confirmed_bindings_payload())
    bom = await ownership_bom_builder(workspace_id=workspace_id)
    linked_segment_rows = [
        row
        for row in list(bom.costable_materials) + list(bom.costable_operations)
        if row.component_ref and row.component_ref.startswith("linked_segment::")
    ]
    assert linked_segment_rows == []


@pytest.mark.asyncio
async def test_two_segments_remain_independent(ownership_bom_builder, ownership_db) -> None:
    workspace_id = await _add_workspace(ownership_db, _confirmed_bindings_payload())
    bom = await ownership_bom_builder(workspace_id=workspace_id)
    stanga_print = [
        m for m in _artwork_materials(bom, segment="logo-stanga") if m.material_code == "print_media"
    ]
    dreapta_print = [
        m for m in _artwork_materials(bom, segment="logo-dreapta") if m.material_code == "print_media"
    ]
    assert len(stanga_print) == 1
    assert len(dreapta_print) == 1
    assert stanga_print[0].component_ref != dreapta_print[0].component_ref


@pytest.mark.asyncio
async def test_partial_finish_emits_zero_artwork_rows(ownership_bom_builder, ownership_db) -> None:
    payload = _confirmed_bindings_payload()
    payload["finish_setup"]["artwork_finishes"][0]["confirmed"] = False
    payload["finish_setup"]["artwork_finishes"][1]["confirmed"] = False
    workspace_id = await _add_workspace(ownership_db, payload)
    bom = await ownership_bom_builder(workspace_id=workspace_id)
    assert _artwork_materials(bom, segment="logo-stanga") == []
    assert _artwork_operations(bom, segment="logo-stanga") == []


@pytest.mark.asyncio
async def test_missing_binding_emits_zero_logo_artwork_rows(ownership_bom_builder, ownership_db) -> None:
    workspace_id = await _add_workspace(ownership_db, _gradi_payload())
    bom = await ownership_bom_builder(workspace_id=workspace_id)
    assert _logo_materials(bom) == []
    assert _logo_operations(bom) == []


@pytest.mark.asyncio
async def test_aggregate_matches_bom_cardinality(ownership_db) -> None:
    workspace_id = await _add_workspace(ownership_db, _confirmed_bindings_payload())
    aggregate = await ProductAggregateService(ownership_db).build_for_workspace(ROOT, workspace_id)
    bom = await AggregateCostBomBuilderService(ownership_db).build_preview(ROOT, workspace_id=workspace_id)
    assert aggregate is not None
    assert bom is not None
    for segment in ("logo-stanga", "logo-dreapta"):
        agg_mats = [
            m
            for m in aggregate.materials
            if m.material_code in ARTWORK_MATS and segment in (m.component_ref or "")
        ]
        bom_mats = _artwork_materials(bom, segment=segment)
        assert len(agg_mats) == len(bom_mats) == 2


@pytest.mark.asyncio
async def test_eic_logo_operations_one_per_concept_and_rates_missing(ownership_db) -> None:
    service = EstimatedInternalCostService(
        ownership_db,
        bom_builder=PatchedAggregateCostBomBuilder(
            ownership_db,
            material_rates=LOGO_MATERIAL_RATES,
            inventory_catalog=LOGO_INVENTORY,
        ),
    )

    async def _patched_load():
        return LOGO_MATERIAL_RATES, {"RON": "RON"}, {"WC_CNC_ROUTING": 120.0}, LOGO_INVENTORY

    service._load_pricing_context = _patched_load  # type: ignore[method-assign]
    workspace_id = await _add_workspace(ownership_db, _confirmed_bindings_payload())
    preview = await service.build_preview(
        ROOT,
        workspace_id=workspace_id,
        quote_input=_quote_input_overlay(_confirmed_bindings_payload()),
    )
    assert preview is not None
    logo_ops = [
        line
        for line in preview.estimated_operation_lines
        if line.component_code and "::" in line.component_code and line.code.startswith("operation_logo_")
    ]
    print_ops = [line for line in logo_ops if line.code == "operation_logo_face_print"]
    assert len(print_ops) == 2
    assert all(line.component_code.startswith(f"{CANONICAL_ARTWORK_COMPONENT}::") for line in print_ops)
    assert all(line.subtotal is None for line in logo_ops)
    assert any(b.code == "INTERNAL_OPERATION_RULE_MISSING" for b in preview.internal_blockers)


@pytest.mark.asyncio
async def test_runtime_bom_inventory_probe_report(ownership_bom_builder, ownership_db, capsys) -> None:
    """Runtime probe — 1 row per concept per segment after ownership dedupe."""
    workspace_id = await _add_workspace(ownership_db, _confirmed_bindings_payload())
    bom = await ownership_bom_builder(workspace_id=workspace_id)
    report: list[str] = []
    for segment in ("logo-stanga", "logo-dreapta"):
        for concept in ("print_media", "laminate_media"):
            rows = [m for m in _artwork_materials(bom, segment=segment) if m.material_code == concept]
            report.append(f"segment={segment} concept={concept} count={len(rows)}")
            for row in rows:
                report.append(
                    f"  component_ref={row.component_ref} source_template={row.source_template_code} provenance={row.provenance}"
                )
        for concept in ARTWORK_OPS:
            rows = [o for o in _artwork_operations(bom, segment=segment) if o.operation_code == concept]
            report.append(f"segment={segment} concept={concept} count={len(rows)}")
            for row in rows:
                report.append(
                    f"  component_ref={row.component_ref} source_template={row.source_template_code} provenance={row.provenance}"
                )
    print("\n".join(report))
    for segment in ("logo-stanga", "logo-dreapta"):
        assert len([m for m in _artwork_materials(bom, segment=segment) if m.material_code == "print_media"]) == 1
        assert len([m for m in _artwork_materials(bom, segment=segment) if m.material_code == "laminate_media"]) == 1
        assert len([o for o in _artwork_operations(bom, segment=segment) if o.operation_code == "logo_face_print"]) == 1
        assert len([o for o in _artwork_operations(bom, segment=segment) if o.operation_code == "logo_face_laminate"]) == 1
        assert len([o for o in _artwork_operations(bom, segment=segment) if o.operation_code == "logo_finish_application"]) == 1


@pytest.mark.asyncio
async def test_letters_only_workspace_unchanged(ownership_bom_builder, ownership_db) -> None:
    letters_workspace = await _add_workspace(ownership_db, _letters_only_payload())
    template_bom = await ownership_bom_builder()
    letters_bom = await ownership_bom_builder(workspace_id=letters_workspace)
    assert _logo_materials(letters_bom) == []
    assert {c.component_id for c in letters_bom.costable_components} == {
        c.component_id for c in template_bom.costable_components
    }
