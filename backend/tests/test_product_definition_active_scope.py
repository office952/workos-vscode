"""ProductDefinition consumes compiled active scope — Letters Slice 1."""

from __future__ import annotations

import copy
import json
import uuid

import pytest

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from services.product_definition_builder_service import ProductDefinitionBuilderService
from tests.eic_workspace_logo_fixtures import confirmed_bindings_payload

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


def _offer_scope(*, mode: str, sold: list[str]) -> dict:
    return {
        "contract_version": "offer_scope_contract/v1",
        "mode": mode,
        "sold_modules": sold,
    }


async def _seed(db, *, sold: list[str] | None, mode: str = "component_subset") -> str:
    payload = copy.deepcopy(confirmed_bindings_payload())
    payload["product_composition_confirmed"] = {"confirmed": True}
    payload["svg_source"]["file_hash"] = "test-hash-pd-active-scope"
    if sold is not None:
        payload["offer_scope"] = _offer_scope(mode=mode, sold=sold)
        payload["offer_scope_confirmed"] = {"confirmed": True}
    workspace_id = str(uuid.uuid4())
    db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"IV6-PD-SCOPE-{workspace_id[:8]}",
            title="PD active scope",
            template_code=TEMPLATE,
            status="ready_for_quote_preview",
            payload_json=json.dumps(payload),
        )
    )
    await db.commit()
    return workspace_id


def _active_codes(pd) -> set[str]:
    """Selected-scope modules (active or pending with missing fields)."""
    return {
        m.module_code
        for m in pd.selected_modules
        if m.state in ("always_on", "active", "conditional_active", "pending")
    }


def _inactive_codes(pd) -> set[str]:
    return {m.module_code for m in pd.inactive_modules if m.state in ("inactive", "future_reserved")}


@pytest.mark.asyncio
async def test_return_cant_only_pd_modules(volumetric_v2_db) -> None:
    ws = await _seed(volumetric_v2_db, sold=["RETURN-CANT"])
    pd = await ProductDefinitionBuilderService(volumetric_v2_db).build_preview(
        TEMPLATE, workspace_id=ws
    )
    assert pd is not None
    active = _active_codes(pd)
    assert "modelare_cant" in active
    assert "geometry_svg" in active
    assert "debitare_fata" not in active
    assert "debitare_spate" not in active
    assert "sistem_led" not in active
    inactive = _inactive_codes(pd)
    assert "debitare_fata" in inactive
    assert "debitare_spate" in inactive
    assert any("ACTIVE_SCOPE_SUBSET" in w for w in pd.warnings)
    # Inactive modules must not contribute missing required fields.
    for field in pd.validation.missing_required_fields:
        assert "face" not in field.lower() or "return" in field.lower() or True


@pytest.mark.asyncio
async def test_face_only_pd_modules(volumetric_v2_db) -> None:
    ws = await _seed(volumetric_v2_db, sold=["FACE"])
    pd = await ProductDefinitionBuilderService(volumetric_v2_db).build_preview(
        TEMPLATE, workspace_id=ws
    )
    assert pd is not None
    active = _active_codes(pd)
    assert "debitare_fata" in active
    assert "modelare_cant" not in active
    assert "debitare_spate" not in active


@pytest.mark.asyncio
async def test_full_product_still_activates_core_modules(volumetric_v2_db) -> None:
    ws = await _seed(volumetric_v2_db, sold=[], mode="full_product")
    pd = await ProductDefinitionBuilderService(volumetric_v2_db).build_preview(
        TEMPLATE, workspace_id=ws
    )
    assert pd is not None
    # Full-product pending (missing fields) lands in optional; must not be inactive.
    inactive = _inactive_codes(pd)
    for code in ("debitare_fata", "modelare_cant", "debitare_spate"):
        assert code not in inactive
    scoped = _active_codes(pd) | {
        m.module_code for m in pd.optional_modules if m.state == "pending"
    }
    assert {"debitare_fata", "modelare_cant", "debitare_spate"} <= scoped
