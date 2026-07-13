from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from seeds.seed_build4_templates import seed_build4_templates
from seeds.seed_tpl_volumetric_letters_dossier import seed_tpl_volumetric_letters_dossier
from seeds.seed_tpl_volumetric_letters_v2 import seed_tpl_volumetric_letters_v2

FIXTURE_SVG = Path(__file__).parent / "fixtures" / "intake_v3" / "multi_layer_ten_layers.svg"


@pytest.fixture(scope="module")
def seeded_db(db_fixture):
    asyncio.get_event_loop().run_until_complete(seed_build4_templates())
    asyncio.get_event_loop().run_until_complete(seed_tpl_volumetric_letters_dossier())
    asyncio.get_event_loop().run_until_complete(seed_tpl_volumetric_letters_v2())
    return db_fixture


@pytest.fixture
def v4_client(seeded_db):
    from core.database import get_db
    from dependencies.auth import get_current_user
    from fastapi.testclient import TestClient
    from main import app
    from schemas.auth import UserResponse

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


def _create_workspace(v4_client) -> str:
    create = v4_client.post(
        "/api/v1/intake-v4/workspaces",
        json={"title": "Finish target runtime", "template_code": "TPL-VOLUMETRIC-LETTERS_v2"},
    )
    assert create.status_code == 201, create.text
    return create.json()["id"]


def _put_analysis_bundle(v4_client, workspace_id: str) -> None:
    svg_text = FIXTURE_SVG.read_text(encoding="utf-8")
    layer_role_setup = {
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
    }
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
                    for layer in layer_role_setup["layers"]
                ],
                "parts": {"count": 10, "nestableCount": 8},
                "geometry": {"perimeterMl": 10.0},
            },
            "layer_role_setup": layer_role_setup,
        },
    )
    assert saved.status_code == 200, saved.text


def test_save_finish_setup_persists_finish_target_runtime_field(v4_client):
    workspace_id = _create_workspace(v4_client)
    _put_analysis_bundle(v4_client, workspace_id)

    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json={
            "face_finish_type": "oracal_8500",
            "finish_target": "face",
            "confirmed": True,
        },
    )
    assert saved.status_code == 200, saved.text
    finish = saved.json()["payload"]["finish_setup"]
    assert finish["finish_target"] == "face"
    assert "finishTarget" not in finish


def test_save_finish_setup_without_finish_target_keeps_field_absent(v4_client):
    workspace_id = _create_workspace(v4_client)
    _put_analysis_bundle(v4_client, workspace_id)

    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json={
            "face_finish_type": "oracal_8500",
            "confirmed": True,
        },
    )
    assert saved.status_code == 200, saved.text
    finish = saved.json()["payload"]["finish_setup"]
    assert finish.get("finish_target") is None


def test_save_finish_setup_persists_print_required_row_level(v4_client):
    workspace_id = _create_workspace(v4_client)
    _put_analysis_bundle(v4_client, workspace_id)

    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json={
            "confirmed": True,
            "artwork_finishes": [
                {
                    "layer_key": "face-1",
                    "execution_type": "print_laminate",
                    "print_required": True,
                    "lamination_required": False,
                },
                {
                    "layer_key": "face-2",
                    "execution_type": "vinyl_cut",
                    "print_required": False,
                    "lamination_required": False,
                },
            ],
        },
    )
    assert saved.status_code == 200, saved.text
    finish = saved.json()["payload"]["finish_setup"]
    artwork = finish["artwork_finishes"]

    assert artwork[0]["print_required"] is True
    assert artwork[1]["print_required"] is False
    assert "print_required" not in finish


def test_save_finish_setup_persists_lamination_required_row_level(v4_client):
    workspace_id = _create_workspace(v4_client)
    _put_analysis_bundle(v4_client, workspace_id)

    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json={
            "confirmed": True,
            "artwork_finishes": [
                {
                    "layer_key": "face-1",
                    "execution_type": "print_laminate",
                    "print_required": True,
                    "lamination_required": True,
                },
                {
                    "layer_key": "face-2",
                    "execution_type": "print",
                    "print_required": True,
                    "lamination_required": False,
                },
            ],
        },
    )
    assert saved.status_code == 200, saved.text
    finish = saved.json()["payload"]["finish_setup"]
    artwork = finish["artwork_finishes"]

    assert artwork[0]["lamination_required"] is True
    assert artwork[1]["lamination_required"] is False
    assert "lamination_required" not in finish


def test_save_finish_setup_persists_mounting_scope_runtime_field(v4_client):
    workspace_id = _create_workspace(v4_client)
    _put_analysis_bundle(v4_client, workspace_id)

    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json={
            "mounting_scope": "mounting_included",
            "mounting_system": "steel_bars",
            "support_type": "steel_frame",
            "confirmed": True,
        },
    )
    assert saved.status_code == 200, saved.text
    finish = saved.json()["payload"]["finish_setup"]

    assert finish["mounting_scope"] == "preparation_and_site_installation"
    assert finish["site_installation_included"] is True


def test_save_finish_setup_without_mounting_scope_keeps_field_absent_even_with_mounting_system_and_support_type(v4_client):
    workspace_id = _create_workspace(v4_client)
    _put_analysis_bundle(v4_client, workspace_id)

    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json={
            "mounting_system": "steel_bars",
            "support_type": "steel_frame",
            "confirmed": True,
        },
    )
    assert saved.status_code == 200, saved.text
    finish = saved.json()["payload"]["finish_setup"]

    assert finish.get("mounting_scope") == "none"


def test_save_finish_setup_persists_support_type_runtime_field(v4_client):
    workspace_id = _create_workspace(v4_client)
    _put_analysis_bundle(v4_client, workspace_id)

    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json={
            "support_type": "steel_frame",
            "support_required": "yes",
            "mounting_system": "steel_bars",
            "mounting_scope": "mounting_included",
            "confirmed": True,
        },
    )
    assert saved.status_code == 200, saved.text
    finish = saved.json()["payload"]["finish_setup"]

    assert finish["support_type"] == "steel_frame"


def test_save_finish_setup_without_support_type_keeps_field_absent_even_with_support_required_mounting_system_and_scope(v4_client):
    workspace_id = _create_workspace(v4_client)
    _put_analysis_bundle(v4_client, workspace_id)

    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/finish-setup",
        json={
            "support_required": "yes",
            "mounting_system": "steel_bars",
            "mounting_scope": "mounting_included",
            "support_source": "detected_svg",
            "confirmed": True,
        },
    )
    assert saved.status_code == 200, saved.text
    finish = saved.json()["payload"]["finish_setup"]

    assert finish.get("support_type") is None