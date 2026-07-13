"""Workspace save integration for sold-scope dependency validation."""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from schemas.auth import UserResponse
from services.intake_v6_workspace_service import (
    get_intake_v6_workspace,
    save_offer_scope_for_intake_v6_workspace,
)
from services.sold_scope_dependency_validator_service import (
    CODE_ELECTRICAL_LOAD_NOT_SOLD,
    CODE_LED_MOUNT_SURFACE_NOT_SOLD,
)
from tests.test_quote_snapshot_v2 import TEMPLATE, _seed_workspace

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]


def _user() -> UserResponse:
    return UserResponse(id="test-user", email="test@example.com", name="Test User", role="admin", last_login=None)


async def _seed_dependency_workspace(db) -> str:
    payload = {
        "product_binding": {"template_code": TEMPLATE},
        "svg_source": {"file_name": "test.svg", "file_size_bytes": 100, "upload_status": "analyzed"},
        "layer_role_setup": {"confirmation_status": "complete", "layers": []},
        "product_composition_confirmed": {"confirmed": True},
    }
    return await _seed_workspace(db, payload=payload)


@pytest.mark.asyncio
async def test_permissive_lighting_only_save_succeeds_with_pending_confirmation(volumetric_v2_db) -> None:
    workspace_id = await _seed_dependency_workspace(volumetric_v2_db)

    response = await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        workspace_id,
        mode="component_subset",
        sold_modules=["LIGHTING"],
        confirmed=True,
        current_user=_user(),
    )

    validation = response.payload.get("offer_scope_dependency_validation") or {}
    assert validation.get("valid_for_save") is True
    assert validation.get("valid_for_confirmation") is False
    assert any(
        issue.get("code") == CODE_LED_MOUNT_SURFACE_NOT_SOLD
        for issue in validation.get("confirmations_required", [])
    )


@pytest.mark.asyncio
async def test_strict_lighting_only_save_blocked(volumetric_v2_db, monkeypatch) -> None:
    monkeypatch.setenv("OFFER_SCOPE_DEPENDENCY_STRICT", "1")
    workspace_id = await _seed_dependency_workspace(volumetric_v2_db)

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
    detail = exc.value.detail
    assert isinstance(detail, dict)
    assert detail.get("error") == "offer_scope_dependency_invalid"


@pytest.mark.asyncio
async def test_dependency_confirmation_clears_mount_requirement(volumetric_v2_db) -> None:
    workspace_id = await _seed_dependency_workspace(volumetric_v2_db)

    await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        workspace_id,
        mode="component_subset",
        sold_modules=["LIGHTING"],
        confirmed=True,
        current_user=_user(),
    )

    response = await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        workspace_id,
        mode="component_subset",
        sold_modules=["LIGHTING"],
        confirmed=True,
        dependency_confirmation_codes=[CODE_LED_MOUNT_SURFACE_NOT_SOLD],
        current_user=_user(),
    )

    validation = response.payload.get("offer_scope_dependency_validation") or {}
    assert validation.get("valid_for_confirmation") is True
    confirmations = response.payload.get("offer_scope_confirmed", {}).get("dependency_confirmations", [])
    assert CODE_LED_MOUNT_SURFACE_NOT_SOLD in confirmations


@pytest.mark.asyncio
async def test_electrical_without_lighting_requires_confirmation(volumetric_v2_db) -> None:
    workspace_id = await _seed_dependency_workspace(volumetric_v2_db)

    response = await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        workspace_id,
        mode="component_subset",
        sold_modules=["ELECTRICAL"],
        confirmed=True,
        current_user=_user(),
    )

    validation = response.payload.get("offer_scope_dependency_validation") or {}
    assert validation.get("valid_for_confirmation") is False
    assert any(
        issue.get("code") == CODE_ELECTRICAL_LOAD_NOT_SOLD
        for issue in validation.get("confirmations_required", [])
    )

    confirmed = await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        workspace_id,
        mode="component_subset",
        sold_modules=["ELECTRICAL"],
        confirmed=True,
        dependency_confirmation_codes=[CODE_ELECTRICAL_LOAD_NOT_SOLD],
        current_user=_user(),
    )
    reloaded = await get_intake_v6_workspace(volumetric_v2_db, workspace_id)
    assert reloaded.payload["offer_scope_dependency_validation"]["valid_for_confirmation"] is True
    assert confirmed.payload["offer_scope_confirmed"]["confirmed"] is True


@pytest.mark.asyncio
async def test_back_plus_lighting_skips_mount_confirmation(volumetric_v2_db) -> None:
    workspace_id = await _seed_dependency_workspace(volumetric_v2_db)

    response = await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        workspace_id,
        mode="component_subset",
        sold_modules=["BACK", "LIGHTING"],
        confirmed=True,
        current_user=_user(),
    )

    validation = response.payload.get("offer_scope_dependency_validation") or {}
    assert validation.get("valid_for_confirmation") is True
    assert "LED_MOUNT_SURFACE" in validation.get("satisfied_capabilities", [])
