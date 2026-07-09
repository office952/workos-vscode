from __future__ import annotations

import json

import pytest
from sqlalchemy import delete, select

from models.intake_v6_workspace import IntakeV6WorkspaceRecord


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
WORKSPACE_ID = "product-truth-promotion-planner-workspace"
WORKSPACE_CODE = "IV6-PRODUCT-TRUTH-PLANNER"


def _complete_payload() -> dict:
    return {
        "product_binding": {"template_code": ROOT},
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "face-1",
                    "layer_id": "face-1",
                    "layer_name": "face 1",
                    "auto_role": "face",
                    "auto_confidence": "high",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
            "warnings": [],
        },
        "svg": {
            "selected_layer_refs": [
                {
                    "layer_id": "face-1",
                    "role": "vector_litere",
                    "source": "operator_confirmed_layer_role",
                    "confirmed": True,
                }
            ]
        },
        "finish_setup": {
            "finish_target": "face",
            "confirmed": True,
            "artwork_finishes": [
                {
                    "layer_key": "logo-left",
                    "print_required": True,
                    "lamination_required": False,
                },
                {
                    "layer_key": "logo-right",
                    "print_required": False,
                    "lamination_required": True,
                },
            ],
            "mounting_scope": "mounting_included",
            "mounting_system": "steel_bars",
            "support_type": "steel_frame",
            "support_required": "yes",
        },
    }


@pytest.fixture
def planner_workspace(db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == WORKSPACE_ID))
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.workspace_code == WORKSPACE_CODE))
            session.add(
                IntakeV6WorkspaceRecord(
                    id=WORKSPACE_ID,
                    workspace_code=WORKSPACE_CODE,
                    title="Product truth planner workspace",
                    template_code=ROOT,
                    status="ready_for_quote_preview",
                    payload_json=json.dumps(_complete_payload()),
                    readiness_status="ready_for_quote_preview",
                    created_by_user_id="test-user-id",
                    updated_by_user_id="test-user-id",
                )
            )
            await session.commit()

    db_fixture.run(_seed())
    return WORKSPACE_ID


def _get(auth_client, workspace_id: str = WORKSPACE_ID):
    return auth_client.get(f"/api/v1/intake-v6/workspaces/{workspace_id}/product-truth-promotion-planner")


def _entries_by_key(entries: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for entry in entries:
        grouped.setdefault(entry["field_key"], []).append(entry)
    return grouped


def test_endpoint_returns_read_only_planner_output(auth_client, planner_workspace):
    response = _get(auth_client, planner_workspace)

    assert response.status_code == 200
    body = response.json()
    assert body["read_only"] is True
    assert body["workspace_id"] == WORKSPACE_ID
    assert body["workspace_record_id"] == WORKSPACE_ID
    assert body["workspace_code"] == WORKSPACE_CODE
    assert body["planner_version"] == "v1"
    assert set(_entries_by_key(body["eligible_entries"])) == {
        "svg.selected_layer_refs[]",
        "finish.finish_target",
        "finish.print_required",
        "finish.lamination_required",
        "mounting.mounting_scope",
        "support.support_type",
    }
    assert body["blocked_entries"] == []


def test_endpoint_returns_eligible_and_blocked_entries(auth_client, db_fixture):
    workspace_id = "product-truth-promotion-planner-blocked"
    workspace_code = "IV6-PRODUCT-TRUTH-PLANNER-BLOCKED"
    payload = _complete_payload()
    payload.pop("svg")
    payload["finish_setup"].pop("finish_target")
    payload["finish_setup"]["artwork_finishes"] = [{"layer_key": "logo-left", "execution_type": "print_laminate"}]
    payload["finish_setup"].pop("mounting_scope")
    payload["finish_setup"].pop("support_type")
    payload["finish_setup"]["support_source"] = "detected_svg"

    async def _seed():
        async with db_fixture.session_maker() as session:
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id))
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.workspace_code == workspace_code))
            session.add(
                IntakeV6WorkspaceRecord(
                    id=workspace_id,
                    workspace_code=workspace_code,
                    title="Product truth planner blocked workspace",
                    template_code=ROOT,
                    status="collecting_data",
                    payload_json=json.dumps(payload),
                    readiness_status="collecting_data",
                    created_by_user_id="test-user-id",
                    updated_by_user_id="test-user-id",
                )
            )
            await session.commit()

    db_fixture.run(_seed())
    body = _get(auth_client, workspace_id).json()
    blocked = _entries_by_key(body["blocked_entries"])

    assert body["eligible_entries"] == []
    assert blocked["svg.selected_layer_refs[]"][0]["blockers"] == ["SELECTED_LAYER_REFS_MISSING"]
    assert blocked["finish.finish_target"][0]["blockers"] == ["FINISH_TARGET_MISSING"]
    assert blocked["mounting.mounting_scope"][0]["blockers"] == ["MOUNTING_SCOPE_MISSING"]
    assert blocked["support.support_type"][0]["blockers"] == ["SUPPORT_TYPE_MISSING"]
    assert any("ARTWORK_BOOLEAN_EXPLICIT_VALUE_MISSING" in entry["blockers"] for entry in blocked["finish.print_required"])
    assert any("ARTWORK_BOOLEAN_EXPLICIT_VALUE_MISSING" in entry["blockers"] for entry in blocked["finish.lamination_required"])


def test_endpoint_has_all_write_flags_false(auth_client, planner_workspace):
    body = _get(auth_client, planner_workspace).json()
    serialized = json.dumps(body, sort_keys=True).lower()

    assert body["downstream_write_intent"]["product_truth_write"] is False
    assert all(value is False for value in body["downstream_write_intent"].values())
    assert '"product_truth_write": true' not in serialized
    assert '"quote_write": true' not in serialized
    assert '"order_write": true' not in serialized
    assert '"execution_runtime_write": true' not in serialized


def test_endpoint_does_not_write_workspace_payload(auth_client, planner_workspace, db_fixture):
    async def _read_payload() -> str | None:
        async with db_fixture.session_maker() as session:
            result = await session.execute(
                select(IntakeV6WorkspaceRecord.payload_json).where(IntakeV6WorkspaceRecord.id == WORKSPACE_ID)
            )
            return result.scalar_one_or_none()

    before = db_fixture.run(_read_payload())
    response = _get(auth_client, planner_workspace)
    after = db_fixture.run(_read_payload())

    assert response.status_code == 200
    assert before == after


def test_endpoint_missing_workspace_returns_404(auth_client):
    response = _get(auth_client, "missing-product-truth-promotion-planner-workspace")

    assert response.status_code == 404
