"""Persistence and preview integration for Intake V6 offer_scope."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy import select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.auth import UserResponse
from services.aggregate_cost_bom_adapter import AggregateCostBomAdapter
from services.intake_v6_workspace_service import (
    get_intake_v6_workspace,
    save_offer_scope_for_intake_v6_workspace,
)
from services.product_aggregate_service import ProductAggregateService
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.quote_snapshot_component_scope_service import build_frozen_component_scope
from tests.test_aggregate_cost_bom_adapter import (
    INVENTORY_CATALOG,
    SAMPLE_RATES,
    SAMPLE_WC_RATES,
    _full_payload,
)
from tests.test_quote_snapshot_v2 import TEMPLATE, _seed_workspace

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def _user() -> UserResponse:
    return UserResponse(id="test-user", email="test@example.com", name="Test User", role="admin", last_login=None)


def _modules_in_bom(bom) -> set[str]:
    mods: set[str] = set()
    for item in bom.costable_components + bom.costable_materials + bom.costable_operations:
        if item.mini_module_code:
            mods.add(item.mini_module_code)
    return mods


async def _seed_scope_workspace(db) -> str:
    payload = {
        "product_binding": {"template_code": TEMPLATE},
        "svg_source": {"file_name": "test.svg", "file_size_bytes": 100, "upload_status": "analyzed"},
        "layer_role_setup": {"confirmation_status": "complete", "layers": []},
        "product_composition_confirmed": {"confirmed": True},
    }
    return await _seed_workspace(db, payload=payload)


@pytest_asyncio.fixture
async def bom_context(volumetric_v2_db):
    pd_builder = ProductDefinitionBuilderService(volumetric_v2_db)
    aggregate_svc = ProductAggregateService(volumetric_v2_db)
    adapter = AggregateCostBomAdapter()

    async def _build(*, workspace_id: str | None = None, quote_input=None):
        pd = await pd_builder.build_preview(TEMPLATE)
        if workspace_id:
            aggregate = await aggregate_svc.build_for_workspace(TEMPLATE, workspace_id)
        else:
            aggregate = await aggregate_svc.build(TEMPLATE)
        assert pd is not None and aggregate is not None
        return adapter.build(
            product_definition=pd,
            aggregate=aggregate,
            quote_input=quote_input,
            material_rates=SAMPLE_RATES,
            workcenter_rates=SAMPLE_WC_RATES,
            inventory_catalog=INVENTORY_CATALOG,
        )

    return _build


@pytest.mark.asyncio
async def test_full_product_persists_and_reloads(volumetric_v2_db) -> None:
    workspace_id = await _seed_scope_workspace(volumetric_v2_db)

    response = await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        workspace_id,
        mode="full_product",
        sold_modules=[],
        confirmed=True,
        current_user=_user(),
    )

    scope = response.payload.get("offer_scope") or {}
    assert scope.get("mode") == "full_product"
    assert scope.get("sold_modules") == []
    assert response.payload["offer_scope_confirmed"]["confirmed"] is True

    reloaded = await get_intake_v6_workspace(volumetric_v2_db, workspace_id)
    assert reloaded.payload["offer_scope"]["mode"] == "full_product"
    assert reloaded.payload["offer_scope_confirmed"]["confirmed"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("sold", "expected_runtime"),
    [
        (["FACE"], ["debitare_fata"]),
        (["RETURN-CANT"], ["modelare_cant"]),
        (["BACK"], ["debitare_spate"]),
        (["FACE", "RETURN-CANT"], ["debitare_fata", "modelare_cant"]),
    ],
)
async def test_component_subset_persists_canonical_scope(
    volumetric_v2_db,
    sold: list[str],
    expected_runtime: list[str],
) -> None:
    workspace_id = await _seed_scope_workspace(volumetric_v2_db)

    await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        workspace_id,
        mode="component_subset",
        sold_modules=sold,
        confirmed=True,
        current_user=_user(),
    )

    reloaded = await get_intake_v6_workspace(volumetric_v2_db, workspace_id)
    assert reloaded.payload["offer_scope"]["mode"] == "component_subset"
    assert reloaded.payload["offer_scope"]["sold_modules"] == sold

    scope = await build_frozen_component_scope(
        volumetric_v2_db,
        template_code=TEMPLATE,
        workspace_id=workspace_id,
    )
    assert scope is not None
    assert scope.offer_scope_snapshot.sold_modules == sold
    assert scope.offer_scope_snapshot.resolved_runtime_sold_modules == expected_runtime


@pytest.mark.asyncio
async def test_empty_subset_blocks_persist(volumetric_v2_db) -> None:
    workspace_id = await _seed_scope_workspace(volumetric_v2_db)

    with pytest.raises(HTTPException) as exc:
        await save_offer_scope_for_intake_v6_workspace(
            volumetric_v2_db,
            workspace_id,
            mode="component_subset",
            sold_modules=[],
            confirmed=True,
            current_user=_user(),
        )

    assert exc.value.status_code == 422
    detail = exc.value.detail
    assert detail["error"] == "offer_scope_invalid"
    assert "SOLD_MODULES_EMPTY" in detail["blockers"]


@pytest.mark.asyncio
async def test_deferred_module_blocks_persist(volumetric_v2_db) -> None:
    workspace_id = await _seed_scope_workspace(volumetric_v2_db)

    with pytest.raises(HTTPException) as exc:
        await save_offer_scope_for_intake_v6_workspace(
            volumetric_v2_db,
            workspace_id,
            mode="component_subset",
            sold_modules=["LIGHTING"],
            confirmed=True,
            current_user=_user(),
        )

    assert exc.value.status_code == 422
    blockers = exc.value.detail["blockers"]
    assert any("DEFERRED_SOLD_MODULE_NOT_SUPPORTED_IN_V1" in code for code in blockers)


@pytest.mark.asyncio
async def test_workspace_payload_preview_reflects_face_subset(volumetric_v2_db, bom_context) -> None:
    workspace_id = await _seed_scope_workspace(volumetric_v2_db)
    await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        workspace_id,
        mode="component_subset",
        sold_modules=["FACE"],
        confirmed=True,
        current_user=_user(),
    )

    reloaded = await get_intake_v6_workspace(volumetric_v2_db, workspace_id)
    bom = await bom_context(
        workspace_id=workspace_id,
        quote_input={"offer_scope": reloaded.payload["offer_scope"]},
    )
    mods = _modules_in_bom(bom)
    assert "debitare_fata" in mods
    assert "modelare_cant" not in mods
    assert "debitare_spate" not in mods


@pytest.mark.asyncio
async def test_legacy_workspace_without_offer_scope_unchanged(volumetric_v2_db, bom_context) -> None:
    workspace_id = str(uuid.uuid4())
    payload = _full_payload()
    payload["product_binding"] = {"template_code": TEMPLATE}
    payload["svg_source"] = {"file_name": "test.svg", "file_size_bytes": 100, "upload_status": "analyzed"}
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"WS-LEG-{workspace_id[:8]}",
            title="legacy",
            template_code=TEMPLATE,
            status="draft",
            payload_json=json.dumps(payload),
        )
    )
    await volumetric_v2_db.commit()

    baseline = await bom_context(workspace_id=workspace_id, quote_input=_full_payload())
    assert _modules_in_bom(baseline)

    reloaded = await get_intake_v6_workspace(volumetric_v2_db, workspace_id)
    assert reloaded.payload.get("offer_scope") is None
