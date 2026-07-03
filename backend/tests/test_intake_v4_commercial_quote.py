"""Intake V4 commercial quote handoff (Sprint 3 + boundary-aligned seed)."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import pytest

from schemas.intake_v4 import PILOT_V4_TEMPLATE_CODE
from seeds.seed_build4_templates import seed_build4_templates
from services.intake_v4_commercial_quote_service import INTAKE_V4_LINKAGE_JSON_KEY

FIXTURE_SVG = Path(__file__).parent / "fixtures" / "intake_v3" / "multi_layer_ten_layers.svg"

DRAFT_QUOTE_BODY = {
    "confirm_create_draft_only": True,
    "confirm_no_order": True,
    "confirm_no_execution": True,
    "confirm_no_inventory": True,
    "confirm_internal_draft_quote": True,
    "decision_reason": "pytest handoff",
}

FINISH_WITH_ORACAL = {
    "face_finish_type": "oracal_651",
    "return_finish_type": "oracal_wrapped",
    "return_depth_mm": 60,
    "illuminated": True,
    "return_oracal_code": "ORACAL651-WHITE",
    "return_oracal_name": "Oracal 651 White",
    "lighting_system_type": "led_modules",
    "led_module_power_w": 1.44,
    "led_module_count": 10,
    "psu_configuration": [100],
    "letter_group_finishes": [
        {
            "group_key": "group-1",
            "face_finish_type": "oracal_651",
            "face_oracal_code": "ORACAL651-WHITE",
            "face_oracal_name": "Oracal 651 White",
            "return_finish_type": "oracal_wrapped",
            "return_oracal_code": "ORACAL651-WHITE",
            "return_depth_mm": 60,
            "confirmed": True,
        }
    ],
    "confirmed": True,
}


def _get_persisted_file_hash(v4_client, workspace_id: str) -> str:
    ws = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}")
    assert ws.status_code == 200, ws.text
    svg_source = ws.json()["payload"]["svg_source"]
    file_hash = svg_source["file_hash"]
    assert isinstance(file_hash, str) and len(file_hash) == 64
    return file_hash


def _draft_quote_body(v4_client, workspace_id: str, **overrides) -> dict:
    return {
        **DRAFT_QUOTE_BODY,
        "client_analysis_hash": _get_persisted_file_hash(v4_client, workspace_id),
        **overrides,
    }


def _confirm_layer_roles(v4_client, workspace_id: str, svg_path: Path = FIXTURE_SVG) -> dict:
    svg_bytes = svg_path.read_bytes()
    upload = v4_client.post(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/svg",
        files={"file": ("multi_layer.svg", svg_bytes, "image/svg+xml")},
    )
    assert upload.status_code == 200, upload.text
    layers = upload.json()["layer_role_setup"]["layers"]
    updates = [
        {
            "layer_key": layer["layer_key"],
            "confirmed_role": layer["auto_role"] if layer["auto_role"] != "unknown" else "face",
            "confirmation_state": "confirmed",
        }
        for layer in layers
    ]
    confirmed = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/layer-roles",
        json={"layers": updates},
    )
    assert confirmed.status_code == 200, confirmed.text
    return confirmed.json()["payload"]["layer_role_setup"]


def _put_analysis_bundle(v4_client, workspace_id: str, layer_role_setup: dict | None = None) -> None:
    svg_text = FIXTURE_SVG.read_text(encoding="utf-8")
    if layer_role_setup is None:
        layer_role_setup = _confirm_layer_roles(v4_client, workspace_id)
    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
        json={
            "file_name": FIXTURE_SVG.name,
            "file_size_bytes": len(svg_text.encode("utf-8")),
            "svg_text": svg_text,
            "svg_analysis_json": {
                "schemaVersion": "1.10.0",
                "layers": [
                    {
                        "id": layer["layer_key"],
                        "name": layer.get("layer_name") or layer["layer_key"],
                        "perimeterMl": 10.0,
                        "filledAreaSqm": 1.2,
                    }
                    for layer in layer_role_setup.get("layers", [])
                    if layer.get("confirmation_state") != "ignored"
                ],
                "parts": {"count": 10, "nestableCount": 8},
                "geometry": {"perimeterMl": 10.0},
            },
            "layer_role_setup": layer_role_setup,
        },
    )
    assert saved.status_code == 200, saved.text


def _confirm_internal_draft(v4_client, workspace_id: str) -> None:
    response = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/internal-draft-quote-confirmation",
        json={"confirmed": True},
    )
    assert response.status_code == 200, response.text


def _seed_ready_workspace(v4_client):
    create = v4_client.post(
        "/api/v1/intake-v4/workspaces",
        json={"title": "Quote handoff", "template_code": PILOT_V4_TEMPLATE_CODE, "client_name": "HUB TEST"},
    )
    assert create.status_code == 201, create.text
    workspace_id = create.json()["id"]
    _put_analysis_bundle(v4_client, workspace_id)
    finish = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json=FINISH_WITH_ORACAL,
    )
    assert finish.status_code == 200, finish.text
    _confirm_internal_draft(v4_client, workspace_id)
    ws = v4_client.get(f"/api/v1/intake-v4/workspaces/{workspace_id}")
    assert ws.status_code == 200
    assert ws.json()["readiness_status"] == "ready_for_quote_preview"
    return workspace_id


@pytest.fixture(scope="module")
def seeded_db(db_fixture):
    asyncio.get_event_loop().run_until_complete(seed_build4_templates())
    return db_fixture


@pytest.fixture
def v4_client(seeded_db):
    from main import app
    from core.database import get_db
    from dependencies.auth import get_current_user
    from schemas.auth import UserResponse
    from fastapi.testclient import TestClient

    async def _override_get_db():
        async with seeded_db.session_maker() as session:
            yield session

    async def _override_get_current_user():
        return UserResponse(
            id="test-user-id",
            email="test@example.com",
            name="Test Admin",
            role="admin",
            last_login=None,
        )

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client
    app.dependency_overrides.clear()


class TestIntakeV4CommercialQuoteHandoff:
    def test_create_draft_quote_endpoint(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        response = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert response.status_code == 201, response.text
        body = response.json()
        assert body["quote_created"] is True
        assert body["quote_id"] > 0
        assert body["source_module"] == "intake_v4"
        assert body["source_workspace_id"] == workspace_id
        assert body["requires_pricing_review"] is True
        assert body["snapshot_attached"] is True
        assert body["quote_input_payload"].get("intake_source") == "intake_v4"
        assert body["order_created"] is False
        assert body["execution_plan_created"] is False
        assert body["inventory_mutated"] is False

        quote_input = body["quote_input_payload"]
        for forbidden in ("unit_price", "grand_total", "subtotal", "owner_fallback"):
            assert forbidden not in quote_input

        quote_row = v4_client.get(f"/api/v1/entities/quotes/{body['quote_id']}")
        assert quote_row.status_code == 200
        quote = quote_row.json()
        assert quote["status"] == "draft"
        assert float(quote["grand_total"] or 0) == 0.0
        assert quote["intake_code"] == f"IV4-{workspace_id}"

        notes = json.loads(quote["notes"])
        linkage = notes[INTAKE_V4_LINKAGE_JSON_KEY]
        assert linkage["requires_pricing_review"] is True
        assert linkage["source_workspace_id"] == workspace_id
        snapshot = linkage["snapshot"]
        assert snapshot["quote_input_payload"]
        assert snapshot["workspace_payload_snapshot"]
        assert snapshot["operation_flags"]
        assert "DRAFT_QUOTE_REQUIRES_PRICING_REVIEW" in snapshot["integrity_rules"]
        assert "CLIENT_ANALYSIS_HASH_SYNCED" in snapshot["integrity_rules"]

        line_items = json.loads(quote["line_items"])
        assert line_items[0]["unit_price"] == 0
        assert line_items[0]["total"] == 0

    def test_duplicate_quote_blocked(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        first = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert first.status_code == 201
        second = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert second.status_code == 422
        assert second.json()["detail"]["error"] == "DUPLICATE_QUOTE_FOR_WORKSPACE"

    def test_handoff_blocked_without_analysis_bundle(self, v4_client):
        create = v4_client.post(
            "/api/v1/intake-v4/workspaces",
            json={"title": "Blocked handoff", "template_code": PILOT_V4_TEMPLATE_CODE},
        )
        workspace_id = create.json()["id"]
        layer_role_setup = _confirm_layer_roles(v4_client, workspace_id)
        v4_client.put(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
            json={**FINISH_WITH_ORACAL},
        )
        assert layer_role_setup["confirmation_status"] == "complete"

        response = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(v4_client, workspace_id),
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] in {"INTERNAL_DRAFT_QUOTE_BLOCKED", "INTERNAL_DRAFT_CONFIRMATION_REQUIRED"}
        blockers = detail.get("blockers") or detail.get("fatal_blockers") or []
        assert "missing_svg_analysis_json" in blockers

    def test_handoff_blocked_without_client_analysis_hash(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        response = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=DRAFT_QUOTE_BODY,
        )
        assert response.status_code == 422

    def test_handoff_blocked_on_analysis_hash_mismatch(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        response = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=_draft_quote_body(
                v4_client,
                workspace_id,
                client_analysis_hash="f" * 64,
            ),
        )
        assert response.status_code == 422
        detail = response.json()["detail"]
        assert detail["error"] == "INTERNAL_DRAFT_QUOTE_BLOCKED"
        assert "analysis_hash_mismatch" in (detail.get("blockers") or detail.get("fatal_blockers") or [])

    def test_quote_handoff_preview_mirrors_create_blockers(self, v4_client):
        workspace_id = _seed_ready_workspace(v4_client)
        file_hash = _get_persisted_file_hash(v4_client, workspace_id)

        allowed = v4_client.get(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/quote-handoff-preview",
            params={"client_analysis_hash": file_hash},
        )
        assert allowed.status_code == 200, allowed.text
        body = allowed.json()
        assert body["handoff_allowed"] is True
        assert body["status_label"] == "HANDOFF_ALLOWED"
        assert body["blockers"] == []

        blocked = v4_client.post(
            f"/api/v1/intake-v4/workspaces/{workspace_id}/create-draft-quote",
            json=DRAFT_QUOTE_BODY,
        )
        assert blocked.status_code == 422
        blocked_detail = blocked.json()["detail"]
        assert blocked_detail["error"] in {
            "INTERNAL_DRAFT_QUOTE_BLOCKED",
            "INTERNAL_DRAFT_CONFIRMATION_REQUIRED",
        }
        assert "missing_client_analysis_hash" in (
            blocked_detail.get("blockers") or blocked_detail.get("fatal_blockers") or []
        )
