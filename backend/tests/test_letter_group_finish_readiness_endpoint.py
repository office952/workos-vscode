from __future__ import annotations

import json

import pytest
from sqlalchemy import delete

from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from tests.test_letter_group_finish_readiness import ROOT, _payload


WORKSPACE_ID = "letter-group-readiness-workspace"
WORKSPACE_CODE = "IV6-LETTER-GROUP-READY"


@pytest.fixture
def letter_group_workspace(db_fixture):
    async def _seed():
        async with db_fixture.session_maker() as session:
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == WORKSPACE_ID))
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.workspace_code == WORKSPACE_CODE))
            session.add(
                IntakeV6WorkspaceRecord(
                    id=WORKSPACE_ID,
                    workspace_code=WORKSPACE_CODE,
                    title="Letter group readiness workspace",
                    template_code=ROOT,
                    status="ready_for_quote_preview",
                    payload_json=json.dumps(_payload()),
                    readiness_status="ready_for_quote_preview",
                    created_by_user_id="test-user-id",
                    updated_by_user_id="test-user-id",
                )
            )
            await session.commit()

    db_fixture.run(_seed())
    return WORKSPACE_ID


def _get(auth_client, workspace_id: str = WORKSPACE_ID):
    return auth_client.get(f"/api/v1/intake-v6/workspaces/{workspace_id}/letter-group-finish-readiness")


def test_endpoint_returns_read_only_letter_group_readiness(auth_client, letter_group_workspace):
    response = _get(auth_client, letter_group_workspace)

    assert response.status_code == 200
    body = response.json()
    assert body["read_only"] is True
    assert body["root_template_code"] == ROOT
    assert body["product_binding_template_code"] == ROOT
    assert body["section"] == "Vector Litere"
    assert body["letter_group_finish_readiness_summary"]["groups_count"] == 4
    assert {row["group_key"] for row in body["letter_group_finish_rows"]} == {
        "pseudo:maria",
        "pseudo:soare",
        "pseudo:ana",
        "pseudo:gradinita",
    }


def test_endpoint_summary_is_partial_and_downstream_safe(auth_client, letter_group_workspace):
    body = _get(auth_client, letter_group_workspace).json()
    summary = body["letter_group_finish_readiness_summary"]

    assert summary["status"] == "partial"
    assert summary["ready_groups_count"] == 0
    assert summary["partial_groups_count"] == 4
    assert summary["pricing_ready"] is False
    assert summary["quote_ready"] is False
    assert summary["order_ready"] is False
    assert summary["execution_ready"] is False
    assert all(value is False for value in body["downstream_write_intent"].values())


def test_endpoint_rows_include_source_state_and_warnings(auth_client, letter_group_workspace):
    body = _get(auth_client, letter_group_workspace).json()

    for row in body["letter_group_finish_rows"]:
        assert row["role"] == "letter_group_finish"
        assert row["svg_evidence"]["analyzer_detected_color"] is True
        assert row["svg_evidence"]["analyzer_detected_oracal"] is False
        assert row["svg_evidence"]["analyzer_detected_cant"] is False
        assert row["face_finish"]["source_type"] == "svg_nearest_color_mapping"
        assert row["face_finish"]["state"] == "suggested"
        assert row["return_cant"]["source_type"] == "payload_hydrated_or_prior_state"
        assert row["return_cant"]["state"] == "hydrated"
        assert row["product_truth_readiness"]["status"] == "partial"


def test_endpoint_has_no_commercial_or_execution_write_fields(auth_client, letter_group_workspace):
    body = _get(auth_client, letter_group_workspace).text.lower()

    assert "pricing_total" not in body
    assert "final_price" not in body
    assert "commercial_total" not in body
    assert "quote_write" not in body
    assert "order_write" not in body
    assert "execution_plan_write" not in body


def test_endpoint_missing_workspace_returns_404(auth_client):
    response = _get(auth_client, "missing-letter-group-readiness-workspace")

    assert response.status_code == 404


def test_endpoint_empty_payload_returns_empty_summary(auth_client, db_fixture):
    workspace_id = "letter-group-readiness-empty"
    workspace_code = "IV6-LETTER-GROUP-EMPTY"

    async def _seed():
        async with db_fixture.session_maker() as session:
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id))
            await session.execute(delete(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.workspace_code == workspace_code))
            session.add(
                IntakeV6WorkspaceRecord(
                    id=workspace_id,
                    workspace_code=workspace_code,
                    title="Letter group readiness empty workspace",
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
    assert body["letter_group_finish_rows"] == []
    assert body["letter_group_finish_readiness_summary"]["status"] == "empty"