from __future__ import annotations

import json

import pytest
from sqlalchemy import delete

from models.intake_v6_workspace import IntakeV6WorkspaceRecord


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
WORKSPACE_ID = "runtime-capture-read-model-workspace"
WORKSPACE_CODE = "IV6-RUNTIME-CAPTURE-READ-MODEL"


def _canonical_mounting_solution() -> dict:
    return {
        "template_code": "TPL-METAL-PREMOUNT-STRUCTURE_v1",
        "configuration": {
            "bar_count": 2,
            "mounting_bar_profile": "30x30x1.5",
            "bar_material": "steel",
        },
    }


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
            "mounting_solution": _canonical_mounting_solution(),
            "support_type": "steel_frame",
            "support_required": "yes",
        },
    }


@pytest.fixture
def runtime_capture_workspace(db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == WORKSPACE_ID))
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.workspace_code == WORKSPACE_CODE))
            session.add(
                IntakeV6WorkspaceRecord(
                    id=WORKSPACE_ID,
                    workspace_code=WORKSPACE_CODE,
                    title="Runtime capture read model workspace",
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
    return auth_client.get(f"/api/v1/intake-v6/workspaces/{workspace_id}/runtime-capture-read-model")


def _fields_by_key(body: dict) -> dict[str, dict]:
    return {field["field_key"]: field for field in body["fields"]}


def test_endpoint_returns_read_only_runtime_capture_read_model(auth_client, runtime_capture_workspace):
    response = _get(auth_client, runtime_capture_workspace)

    assert response.status_code == 200
    body = response.json()
    assert body["read_only"] is True
    assert body["workspace_id"] == WORKSPACE_ID
    assert body["workspace_code"] == WORKSPACE_CODE
    assert body["root_template_code"] == ROOT
    assert body["product_binding_template_code"] == ROOT
    assert body["read_model_version"] == "v1"
    assert {field["field_key"] for field in body["fields"]} == {
        "svg.selected_layer_refs[]",
        "finish.finish_target",
        "finish.print_required",
        "finish.lamination_required",
        "mounting.mounting_scope",
        "mounting.mounting_solution",
    }


def test_endpoint_returns_confirmed_fields_for_complete_payload(auth_client, runtime_capture_workspace):
    body = _get(auth_client, runtime_capture_workspace).json()

    assert body["blockers"] == []
    assert all(field["state"] == "confirmed" for field in body["fields"])
    assert all(field["ready_for_product_truth"] is True for field in body["fields"])


def test_endpoint_missing_fields_remain_blocked_without_fallback(auth_client, db_fixture):
    workspace_id = "runtime-capture-read-model-blocked"
    workspace_code = "IV6-RUNTIME-CAPTURE-BLOCKED"
    payload = _complete_payload()
    payload.pop("svg")
    payload["finish_setup"].pop("finish_target")
    payload["finish_setup"]["artwork_finishes"] = [{"layer_key": "logo-left"}]
    payload["finish_setup"].pop("mounting_solution")
    payload["finish_setup"]["support_type"] = "steel_frame"
    payload["finish_setup"]["support_source"] = "detected_svg"

    async def _seed():
        async with db_fixture.session_maker() as session:
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id))
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.workspace_code == workspace_code))
            session.add(
                IntakeV6WorkspaceRecord(
                    id=workspace_id,
                    workspace_code=workspace_code,
                    title="Runtime capture blocked workspace",
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
    fields = _fields_by_key(body)

    assert fields["svg.selected_layer_refs[]"]["blockers"] == ["SELECTED_LAYER_REFS_MISSING"]
    assert fields["finish.finish_target"]["blockers"] == ["FINISH_TARGET_MISSING"]
    assert fields["finish.print_required"]["blockers"] == ["PRINT_REQUIRED_UNKNOWN"]
    assert fields["finish.lamination_required"]["blockers"] == ["LAMINATION_REQUIRED_UNKNOWN"]
    assert fields["mounting.mounting_solution"]["blockers"] == ["MOUNTING_SOLUTION_MISSING"]
    assert fields["mounting.mounting_solution"]["ready_for_product_truth"] is False


def test_endpoint_is_read_only_and_has_no_pricing_quote_or_execution_coupling(auth_client, runtime_capture_workspace):
    body = _get(auth_client, runtime_capture_workspace).json()
    serialized = json.dumps(body, sort_keys=True).lower()

    assert all(value is False for value in body["downstream_write_intent"].values())
    assert "commercial_total" not in serialized
    assert "quote_write\": true" not in serialized
    assert "order_write\": true" not in serialized
    assert "execution_runtime_write\": true" not in serialized


def test_endpoint_missing_workspace_returns_404(auth_client):
    response = _get(auth_client, "missing-runtime-capture-read-model-workspace")

    assert response.status_code == 404


def test_endpoint_logo_fail_closed_uses_normalized_blockers_contract(auth_client, db_fixture):
    workspace_id = "runtime-capture-logo-fail-closed"
    workspace_code = "IV6-RUNTIME-CAPTURE-LOGO-FC"
    logo = "TPL-VOLUMETRIC-LOGO_v1"
    payload = {
        "product_binding": {
            "template_code": logo,
            "template_label": "Logo volumetric",
            "product_family": "litere_volumetrice",
        },
        "svg_source": {
            "file_name": "logo.svg",
            "file_hash": "d" * 64,
            "file_size_bytes": 100,
            "upload_status": "analyzed",
        },
    }

    async def _seed():
        async with db_fixture.session_maker() as session:
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id))
            await session.execute(
                delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.workspace_code == workspace_code)
            )
            session.add(
                IntakeV6WorkspaceRecord(
                    id=workspace_id,
                    workspace_code=workspace_code,
                    title="Runtime capture Logo fail-closed",
                    template_code=logo,
                    status="collecting_data",
                    payload_json=json.dumps(payload),
                    readiness_status="logo_only_candidate_not_offerable",
                    created_by_user_id="test-user-id",
                    updated_by_user_id="test-user-id",
                )
            )
            await session.commit()

    db_fixture.run(_seed())

    # HTTP CONTRACT PROOF — runtime-capture normalized blockers[]
    response = _get(auth_client, workspace_id)
    assert response.status_code == 200, response.text
    body = response.json()

    assert body["root_template_code"] == logo
    assert body["fields"] == []
    assert len(body["blockers"]) == 1
    row = body["blockers"][0]
    assert row["field_key"] == "root"
    assert row["blockers"] == ["LOGO_NOT_OFFERABLE"]
    assert row["blockers"].count("LOGO_NOT_OFFERABLE") == 1
    assert row["state"] == "blocked"
    assert row["blocker_code"] == "LOGO_NOT_OFFERABLE"
    assert row["severity"] == "blocked"
    assert isinstance(row.get("message"), str) and row["message"]
    assert "quote_preview" in (row.get("blocks") or [])

    # Readiness / handoff unchanged by blocker-shape normalization
    workspace = auth_client.get(f"/api/v1/intake-v6/workspaces/{workspace_id}")
    assert workspace.status_code == 200, workspace.text
    assert workspace.json()["readiness_status"] == "logo_only_candidate_not_offerable"

    handoff = auth_client.get(f"/api/v1/intake-v6/workspaces/{workspace_id}/quote-handoff-preview")
    assert handoff.status_code == 200, handoff.text
    handoff_body = handoff.json()
    assert handoff_body["workspace_readiness_status"] == "logo_only_candidate_not_offerable"
    assert handoff_body["handoff_allowed"] is False
    assert handoff_body["can_create_internal_draft_quote"] is False