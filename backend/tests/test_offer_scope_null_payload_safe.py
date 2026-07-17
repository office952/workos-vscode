"""Offer-scope save must tolerate payload offer_scope=null (Build 3 scope switching)."""

from __future__ import annotations

import json
import uuid

import pytest
import pytest_asyncio

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from schemas.auth import UserResponse
from services.intake_v6_workspace_service import save_offer_scope_for_intake_v6_workspace

pytest_plugins = ["tests.test_product_aggregate_volumetric_v2"]

TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"


@pytest_asyncio.fixture
async def null_scope_workspace(volumetric_v2_db):
    workspace_id = str(uuid.uuid4())
    payload = {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": TEMPLATE},
        "offer_scope": None,
        "finish_setup": {"confirmed": True},
    }
    volumetric_v2_db.add(
        IntakeV6WorkspaceRecord(
            id=workspace_id,
            workspace_code=f"IV6-NULL-SCOPE-{workspace_id[:8]}",
            title="null offer_scope",
            template_code=TEMPLATE,
            status="collecting_data",
            payload_json=json.dumps(payload),
        )
    )
    await volumetric_v2_db.commit()
    return workspace_id


@pytest.mark.asyncio
async def test_full_product_save_with_null_offer_scope(volumetric_v2_db, null_scope_workspace):
    user = UserResponse(id="test-user", email="t@example.com", name="t", role="admin")
    result = await save_offer_scope_for_intake_v6_workspace(
        volumetric_v2_db,
        null_scope_workspace,
        mode="full_product",
        sold_modules=[],
        confirmed=True,
        current_user=user,
    )
    payload = result.payload if isinstance(result.payload, dict) else result.payload.model_dump()
    assert payload.get("offer_scope") is not None
    assert payload["offer_scope"]["mode"] == "full_product"
