from __future__ import annotations

import json

import pytest
from sqlalchemy import delete

from models.intake_v6_workspace import IntakeV6WorkspaceRecord


ROOT = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = "TPL-VOLUMETRIC-LOGO_v1"
WORKSPACE_ID = "linked-segments-workspace"
WORKSPACE_CODE = "IV6-LINKED-SEGMENTS"
INTAKE_CODE = "IR-LINKED-SEGMENTS"


def _payload() -> dict:
    return {
        "product_binding": {"template_code": ROOT},
        "intake_request_code": INTAKE_CODE,
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "logo-stanga",
                    "layer_id": "logo-stanga",
                    "layer_name": "logo stanga",
                    "auto_role": "printed_artwork",
                    "confirmed_role": "printed_artwork",
                    "confirmation_state": "confirmed",
                },
                {
                    "layer_key": "logo-dreapta",
                    "layer_id": "logo-dreapta",
                    "layer_name": "logo dreapta",
                    "auto_role": "printed_artwork",
                    "confirmed_role": "printed_artwork",
                    "confirmation_state": "confirmed",
                },
            ],
            "layer_bindings": [
                {
                    "layer_key": "logo-stanga",
                    "source_layer_name": "logo stanga",
                    "suggested_semantic_role": "printed_artwork",
                    "confirmed_semantic_role": "printed_artwork",
                    "target_template_code": LOGO,
                    "target_module_code": "logo_finish",
                    "binding_status": "suggested",
                    "binding_reason": "additional_template_suggestion_requires_binding_confirmation",
                },
                {
                    "layer_key": "logo-dreapta",
                    "source_layer_name": "logo dreapta",
                    "suggested_semantic_role": "printed_artwork",
                    "confirmed_semantic_role": "printed_artwork",
                    "target_template_code": LOGO,
                    "target_module_code": "logo_finish",
                    "binding_status": "suggested",
                    "binding_reason": "additional_template_suggestion_requires_binding_confirmation",
                },
            ],
        },
        "finish_setup": {
            "confirmed": True,
            "artwork_finishes": [
                {
                    "layer_key": "logo-stanga",
                    "layer_name": "logo stanga",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "print_transparency": "translucent",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                    "confirmed": True,
                },
                {
                    "layer_key": "logo-dreapta",
                    "layer_name": "logo dreapta",
                    "execution_type": "print_laminate",
                    "color_mode": "polychrome",
                    "print_transparency": "translucent",
                    "return_finish_type": "white_aluminum",
                    "return_depth_mm": 60,
                    "confirmed": True,
                },
            ],
        },
    }


@pytest.fixture
def linked_segments_workspace(db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            await session.execute(
                delete(IntakeV6WorkspaceRecord).where(
                    IntakeV6WorkspaceRecord.id.in_([WORKSPACE_ID]),
                )
            )
            await session.execute(
                delete(IntakeV6WorkspaceRecord).where(
                    IntakeV6WorkspaceRecord.workspace_code.in_([WORKSPACE_CODE]),
                )
            )
            record = IntakeV6WorkspaceRecord(
                id=WORKSPACE_ID,
                workspace_code=WORKSPACE_CODE,
                title="Linked segments workspace",
                template_code=ROOT,
                status="ready_for_quote_preview",
                payload_json=json.dumps(_payload()),
                readiness_status="ready_for_quote_preview",
                created_by_user_id="test-user-id",
                updated_by_user_id="test-user-id",
            )
            session.add(record)
            await session.commit()

    db_fixture.run(_seed())
    return WORKSPACE_ID


def _get(auth_client, workspace_id: str = WORKSPACE_ID):
    return auth_client.get(f"/api/v1/intake-v6/workspaces/{workspace_id}/linked-template-segments")


def test_endpoint_returns_linked_segments_for_letters_workspace(auth_client, linked_segments_workspace):
    response = _get(auth_client, linked_segments_workspace)

    assert response.status_code == 200
    body = response.json()
    segments = body["linked_template_runtime_segments"]["segments"]
    assert body["read_only"] is True
    assert body["root_template_code"] == ROOT
    assert body["product_binding_template_code"] == ROOT
    assert body["linked_template_composition"]["linked_templates"][0]["template_code"] == LOGO
    assert body["linked_template_composition"]["linked_templates"][0]["composition_role"] == "linked_logo_segment"
    assert body["linked_template_runtime_segments"]["summary"]["segments_count"] == 2
    assert {segment["segment_key"] for segment in segments} == {"logo-stanga", "logo-dreapta"}


def test_endpoint_preserves_suggested_binding(auth_client, linked_segments_workspace):
    body = _get(auth_client, linked_segments_workspace).json()
    segments = body["linked_template_runtime_segments"]["segments"]

    assert body["linked_template_runtime_segments"]["summary"]["suggested_binding_count"] == 2
    for segment in segments:
        assert segment["binding_status"] == "suggested"
        assert segment["owning_template_code"] == LOGO
        assert segment["parent_root_template_code"] == ROOT
        assert "binding_status_suggested_requires_product_truth_confirmation_boundary" in segment["warnings"]


def test_endpoint_includes_product_truth_readiness_per_segment(auth_client, linked_segments_workspace):
    body = _get(auth_client, linked_segments_workspace).json()
    segments = body["linked_template_runtime_segments"]["segments"]

    for segment in segments:
        readiness = segment["product_truth_readiness"]
        assert readiness["status"] == "partial"
        assert readiness["reason"] == "template_binding_suggested"
        assert readiness["finish_confirmed"] is True
        assert readiness["layer_role_confirmed"] is True
        assert readiness["template_binding_confirmed"] is False
        assert readiness["product_truth_path"] == segment["product_truth_path"]


def test_endpoint_includes_product_truth_readiness_summary(auth_client, linked_segments_workspace):
    body = _get(auth_client, linked_segments_workspace).json()
    summary = body["linked_template_runtime_segments"]["product_truth_readiness_summary"]

    assert summary["status"] == "partial"
    assert summary["ready_segments_count"] == 0
    assert summary["partial_segments_count"] == 2
    assert summary["blocked_segments_count"] == 0
    assert summary["reason"] == "linked_template_binding_suggested"


def test_endpoint_preserves_no_downstream_activation(auth_client, linked_segments_workspace):
    body = _get(auth_client, linked_segments_workspace).json()
    summary = body["linked_template_runtime_segments"]["summary"]
    readiness_summary = body["linked_template_runtime_segments"]["product_truth_readiness_summary"]

    assert summary["root_offerable_activation"] is False
    assert summary["separate_quote_activation"] is False
    assert summary["task_graph_activation"] is False
    assert all(value is False for value in body["downstream_write_intent"].values())
    assert readiness_summary["pricing_ready"] is False
    assert readiness_summary["quote_ready"] is False
    assert readiness_summary["order_ready"] is False
    assert readiness_summary["execution_ready"] is False


def test_endpoint_does_not_activate_logo_root(auth_client, linked_segments_workspace):
    response = auth_client.get("/api/v1/intake-v6/form-contract/TPL-VOLUMETRIC-LOGO_v1")

    assert response.status_code == 404


def test_endpoint_missing_workspace_returns_404(auth_client):
    response = _get(auth_client, "missing-linked-segments-workspace")

    assert response.status_code == 404


def test_endpoint_empty_payload_returns_safe_empty(auth_client, db_fixture):
    workspace_id = "linked-segments-empty"

    async def _seed():
        async with db_fixture.session_maker() as session:
            await session.execute(
                delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id)
            )
            await session.execute(
                delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.workspace_code == "IV6-LINKED-EMPTY")
            )
            session.add(
                IntakeV6WorkspaceRecord(
                    id=workspace_id,
                    workspace_code="IV6-LINKED-EMPTY",
                    title="Linked segments empty workspace",
                    template_code=ROOT,
                    status="draft",
                    payload_json=json.dumps({"product_binding": {"template_code": ROOT}}),
                    readiness_status="draft",
                    created_by_user_id="test-user-id",
                    updated_by_user_id="test-user-id",
                )
            )
            await session.commit()

    db_fixture.run(_seed())
    response = _get(auth_client, workspace_id)

    assert response.status_code == 200
    body = response.json()
    assert body["linked_template_runtime_segments"]["segments"] == []
    assert body["linked_template_runtime_segments"]["product_truth_readiness_summary"]["status"] == "not_applicable"
    assert body["linked_template_runtime_segments"]["summary"]["segments_count"] == 0
    assert body["linked_template_runtime_segments"]["summary"]["product_truth_readiness_status"] == "no_runtime_segments"