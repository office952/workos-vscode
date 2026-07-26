"""Position-independent linked logo instance identity contract tests."""

from __future__ import annotations

import copy

import pytest

from services.intake_v6_layer_identity import (
    artwork_finish_for_segment,
    canonical_segment_key,
    is_positional_logo_identity,
)
from services.linked_template_runtime_segment_extraction_service import (
    extract_linked_template_segments_from_workspace_payload,
)
from services.form_system_contract_backbone_service import build_form_system_contract_map
from services.product_aggregate_workspace_composition_service import build_workspace_composed_aggregate
from services.aggregate_cost_bom_adapter import AggregateCostBomBuilderService
from tests.eic_workspace_logo_fixtures import (
    LOGO_INSTANCE_A,
    LOGO_INSTANCE_B,
    ROOT,
    confirmed_bindings_payload,
)
from tests.test_product_aggregate_volumetric_v2 import _seed_volumetric_v2_fixture

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def test_neutral_fixture_ids_are_not_positional() -> None:
    assert not is_positional_logo_identity(LOGO_INSTANCE_A)
    assert not is_positional_logo_identity(LOGO_INSTANCE_B)


def test_legacy_positional_layer_key_normalizes_to_neutral_layer_id() -> None:
    layer = {
        "layer_key": "logo-stanga",
        "layer_id": LOGO_INSTANCE_A,
        "layer_name": "Logo 1",
    }
    assert canonical_segment_key(layer_key="logo-stanga", layer=layer) == LOGO_INSTANCE_A


def _linked_template_composition() -> dict:
    return build_form_system_contract_map(ROOT)["linked_template_composition"]


def test_segment_extraction_uses_neutral_instance_ids() -> None:
    payload = confirmed_bindings_payload()
    segments = extract_linked_template_segments_from_workspace_payload(
        root_template_code=ROOT,
        workspace_payload=payload,
        linked_template_composition=_linked_template_composition(),
    )
    keys = {segment["segment_key"] for segment in segments["segments"]}
    assert keys == {LOGO_INSTANCE_A, LOGO_INSTANCE_B}
    assert all(not is_positional_logo_identity(key) for key in keys)


def test_geometry_swap_preserves_instance_identity() -> None:
    payload = confirmed_bindings_payload()
    swapped = copy.deepcopy(payload)
    finishes = swapped["finish_setup"]["artwork_finishes"]
    a = next(row for row in finishes if row["layer_key"] == LOGO_INSTANCE_A)
    b = next(row for row in finishes if row["layer_key"] == LOGO_INSTANCE_B)
    a["position_hint"] = "right"
    b["position_hint"] = "left"
    a["estimated_area_m2"] = 0.42
    b["estimated_area_m2"] = 0.38

    before = extract_linked_template_segments_from_workspace_payload(
        root_template_code=ROOT,
        workspace_payload=payload,
        linked_template_composition=_linked_template_composition(),
    )
    after = extract_linked_template_segments_from_workspace_payload(
        root_template_code=ROOT,
        workspace_payload=swapped,
        linked_template_composition=_linked_template_composition(),
    )
    assert {segment["segment_key"] for segment in before["segments"]} == {
        segment["segment_key"] for segment in after["segments"]
    }
    assert artwork_finish_for_segment(swapped, LOGO_INSTANCE_A)["estimated_area_m2"] == 0.42
    assert artwork_finish_for_segment(swapped, LOGO_INSTANCE_B)["estimated_area_m2"] == 0.38


@pytest.mark.asyncio
async def test_productaggregate_and_cost_bom_refs_preserved_after_geometry_swap(volumetric_v2_db) -> None:
    from seeds.seed_tpl_volumetric_logo_v1 import seed_tpl_volumetric_logo_v1
    from models.intake_v6_workspace import IntakeV6WorkspaceRecord
    import json
    import uuid

    await _seed_volumetric_v2_fixture(volumetric_v2_db)
    await seed_tpl_volumetric_logo_v1()

    payload = confirmed_bindings_payload()
    workspace_id = str(uuid.uuid4())
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code="WS-IDENTITY",
            title="identity",
            template_code=ROOT,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await volumetric_v2_db.commit()

    composed_before = await build_workspace_composed_aggregate(
        volumetric_v2_db, template_code=ROOT, workspace_id=workspace_id
    )
    bom_before = await AggregateCostBomBuilderService(volumetric_v2_db).build_preview(
        ROOT, workspace_id=workspace_id
    )
    refs_before = {
        component.component_id
        for component in composed_before.components
        if LOGO_INSTANCE_A in component.component_id or LOGO_INSTANCE_B in component.component_id
    }

    swapped_payload = copy.deepcopy(payload)
    for finish in swapped_payload["finish_setup"]["artwork_finishes"]:
        finish["position_hint"] = "left" if finish["layer_key"] == LOGO_INSTANCE_B else "right"

    record = await volumetric_v2_db.get(IntakeV6WorkspaceRecord, workspace_id)
    assert record is not None
    record.payload_json = json.dumps(swapped_payload)
    await volumetric_v2_db.commit()

    composed_after = await build_workspace_composed_aggregate(
        volumetric_v2_db, template_code=ROOT, workspace_id=workspace_id
    )
    bom_after = await AggregateCostBomBuilderService(volumetric_v2_db).build_preview(
        ROOT, workspace_id=workspace_id
    )
    refs_after = {
        component.component_id
        for component in composed_after.components
        if LOGO_INSTANCE_A in component.component_id or LOGO_INSTANCE_B in component.component_id
    }
    assert refs_before == refs_after
    assert refs_before
    assert all("logo-stanga" not in ref and "logo-dreapta" not in ref for ref in refs_before)
    assert len(bom_before.costable_materials) == len(bom_after.costable_materials)


def test_legacy_positional_fixture_normalization_compat() -> None:
    payload = confirmed_bindings_payload()
    layer = payload["layer_role_setup"]["layers"][1]
    layer["layer_key"] = "logo-stanga"
    layer["layer_id"] = LOGO_INSTANCE_A
    payload["finish_setup"]["artwork_finishes"][0]["layer_key"] = LOGO_INSTANCE_A
    payload["layer_role_setup"]["layer_bindings"][0]["layer_key"] = LOGO_INSTANCE_A
    segments = extract_linked_template_segments_from_workspace_payload(
        root_template_code=ROOT,
        workspace_payload=payload,
        linked_template_composition=_linked_template_composition(),
    )
    keys = {segment["segment_key"] for segment in segments["segments"]}
    assert LOGO_INSTANCE_A in keys
    assert "logo-stanga" not in keys
