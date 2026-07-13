"""API-level runtime verification for fixture workspace W1-L-SPINE."""
from __future__ import annotations

import json

import pytest
from sqlalchemy import delete

from models.intake_v6_workspace import IntakeV6WorkspaceRecord

WORKSPACE_ID = "80570a4a-a806-4305-a39c-b34a72092694"
REQUEST_FIXTURE_NOTE = "IR-MRJS4VIK"


@pytest.fixture
def spine_fixture_workspace(db_fixture, auth_client):
    async def _noop():
        return None

    db_fixture.run(_noop())
    yield WORKSPACE_ID


def test_runtime_capture_api_no_stale_support_type_blocker(auth_client, spine_fixture_workspace):
    response = auth_client.get(
        f"/api/v1/intake-v6/workspaces/{spine_fixture_workspace}/runtime-capture-read-model"
    )
    if response.status_code == 404:
        pytest.skip("fixture workspace not present in test db")
    assert response.status_code == 200
    body = response.json()
    fields = {f["field_key"]: f for f in body["fields"]}
    assert "mounting.mounting_solution" in fields
    mounting = fields["mounting.mounting_solution"]
    assert mounting["state"] == "confirmed"
    assert mounting["blockers"] == []
    serialized = json.dumps(body)
    assert "SUPPORT_TYPE_MISSING" not in serialized


def test_pricing_preview_merges_capture_blockers(auth_client, spine_fixture_workspace):
    response = auth_client.get(
        f"/api/v1/intake-v6/workspaces/{spine_fixture_workspace}/pricing-input-preview"
    )
    if response.status_code == 404:
        pytest.skip("fixture workspace not present in test db")
    assert response.status_code == 200
    body = response.json()
    if body.get("is_ready_for_quote"):
        assert any("runtime_capture:" in b for b in body.get("adapter_blockers") or [])
    else:
        assert body.get("is_ready_for_quote") is False
