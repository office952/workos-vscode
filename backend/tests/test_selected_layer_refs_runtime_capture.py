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
    from core.database import db_manager

    db_manager.engine = getattr(db_fixture, "_engine", None)
    db_manager.async_session_maker = db_fixture.session_maker
    db_manager._initialized = True

    db_fixture.run(seed_build4_templates())
    db_fixture.run(seed_tpl_volumetric_letters_dossier())
    db_fixture.run(seed_tpl_volumetric_letters_v2())
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


def _create_workspace(v4_client):
    create = v4_client.post(
        "/api/v1/intake-v4/workspaces",
        json={"title": "Selected layer refs", "template_code": "TPL-VOLUMETRIC-LETTERS_v2"},
    )
    assert create.status_code == 201, create.text
    return create.json()["id"]


def test_analysis_bundle_persists_mixed_letter_and_logo_selected_layer_refs(v4_client):
    workspace_id = _create_workspace(v4_client)
    svg_text = FIXTURE_SVG.read_text(encoding="utf-8")
    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
        json={
            "file_name": FIXTURE_SVG.name,
            "file_size_bytes": len(svg_text.encode("utf-8")),
            "svg_text": svg_text,
            "svg_analysis_json": {"schemaVersion": "1.10.0", "layers": []},
            "layer_role_setup": {
                "confirmation_status": "complete",
                "layers": [
                    {
                        "layer_key": "letter-1",
                        "layer_id": "letter-1",
                        "layer_name": "letter 1",
                        "auto_role": "face",
                        "auto_confidence": "high",
                        "confirmed_role": "face",
                        "confirmation_state": "confirmed",
                    },
                    {
                        "layer_key": "logo-1",
                        "layer_id": "logo-1",
                        "layer_name": "logo 1",
                        "auto_role": "printed_artwork",
                        "auto_confidence": "high",
                        "confirmed_role": "printed_artwork",
                        "confirmation_state": "confirmed",
                    },
                ],
                "warnings": [],
            },
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["payload"]["svg"]["selected_layer_refs"] == [
        {
            "layer_id": "letter-1",
            "role": "vector_litere",
            "source": "operator_confirmed_layer_role",
            "confirmed": True,
        },
        {
            "layer_id": "logo-1",
            "role": "vector_logo",
            "source": "operator_confirmed_layer_role",
            "confirmed": True,
        },
    ]


def test_analysis_bundle_persists_selected_layer_refs_from_confirmed_layer_role_setup(v4_client):
    workspace_id = _create_workspace(v4_client)
    svg_text = FIXTURE_SVG.read_text(encoding="utf-8")
    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
        json={
            "file_name": FIXTURE_SVG.name,
            "file_size_bytes": len(svg_text.encode("utf-8")),
            "svg_text": svg_text,
            "svg_analysis_json": {"schemaVersion": "1.10.0", "layers": []},
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
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["payload"]["svg"]["selected_layer_refs"] == [
        {
            "layer_id": "face-1",
            "role": "vector_litere",
            "source": "operator_confirmed_layer_role",
            "confirmed": True,
        }
    ]


def test_save_layer_roles_does_not_persist_selected_layer_refs_from_unconfirmed_roles(v4_client):
    workspace_id = _create_workspace(v4_client)
    upload = v4_client.post(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/svg",
        files={"file": (FIXTURE_SVG.name, FIXTURE_SVG.read_bytes(), "image/svg+xml")},
    )
    assert upload.status_code == 200, upload.text
    layers = upload.json()["layer_role_setup"]["layers"]
    updates = [
        {
            "layer_key": layers[0]["layer_key"],
            "confirmed_role": "face",
            "confirmation_state": "pending",
        }
    ]
    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/layer-roles",
        json={"layers": updates},
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["payload"].get("svg") is None or saved.json()["payload"]["svg"].get("selected_layer_refs") in {None, []}


def test_svg_replacement_clears_selected_layer_refs_when_source_changes(v4_client):
    workspace_id = _create_workspace(v4_client)
    svg_text = FIXTURE_SVG.read_text(encoding="utf-8")
    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
        json={
            "file_name": FIXTURE_SVG.name,
            "file_size_bytes": len(svg_text.encode("utf-8")),
            "svg_text": svg_text,
            "svg_analysis_json": {"schemaVersion": "1.10.0", "layers": []},
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
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["payload"]["svg"]["selected_layer_refs"]

    replacement = v4_client.post(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/svg",
        files={"file": ("replacement.svg", b"<svg xmlns='http://www.w3.org/2000/svg'><path d='M0 0'/></svg>", "image/svg+xml")},
    )
    assert replacement.status_code == 200, replacement.text
    payload = replacement.json()["workspace"]["payload"]
    assert payload.get("svg") is None or payload["svg"].get("selected_layer_refs") in {None, []}


def test_analysis_bundle_does_not_invent_selected_layer_refs_from_layer_name_only(v4_client):
    workspace_id = _create_workspace(v4_client)
    svg_text = FIXTURE_SVG.read_text(encoding="utf-8")
    saved = v4_client.put(
        f"/api/v1/intake-v4/workspaces/{workspace_id}/analysis-bundle",
        json={
            "file_name": FIXTURE_SVG.name,
            "file_size_bytes": len(svg_text.encode("utf-8")),
            "svg_text": svg_text,
            "svg_analysis_json": {"schemaVersion": "1.10.0", "layers": []},
            "layer_role_setup": {
                "confirmation_status": "complete",
                "layers": [
                    {
                        "layer_key": "face-1",
                        "layer_name": "face 1",
                        "auto_role": "face",
                        "auto_confidence": "high",
                        "confirmed_role": "face",
                        "confirmation_state": "confirmed",
                    }
                ],
                "warnings": [],
            },
        },
    )
    assert saved.status_code == 200, saved.text
    assert saved.json()["payload"].get("svg") is None or saved.json()["payload"]["svg"].get("selected_layer_refs") in {None, []}