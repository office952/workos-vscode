"""Layer role confirmation invalidation when SVG path geometry layer set changes."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.intake_v3_layer_role_confirmation_service import (
    WARN_LAYER_ROLE_CONFIRMATION_RESET_AFTER_SVG_REUPLOAD,
    layer_keys_from_path_geometry_summary,
)
from tests.test_intake_v3_svg_upload_analysis import _create_workspace, _upload_svg

SVG_A_LAYER_LITERE = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" width="300mm" height="120mm" viewBox="0 0 300 120">
  <g id="layer-litere"><path d="M40 90 L60 30 L80 90"/></g>
</svg>
"""

SVG_B_COREL_PATHS = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24.79463 23.5359">
  <g id="fata_x0020_plexiglas">
    <path d="M16.2246 6.56824l-2.56225 -1.47929 4.80996 -1.32351"/>
  </g>
  <g id="autocolant">
    <path d="M16.23122 6.31015l-2.56225 -1.47929"/>
  </g>
</svg>
"""

from tests.test_intake_v3_svg_layer_path_geometry import FLAT_PBL_SVG

SVG_PBL_SAME_KEYS_ALT = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="205cm" height="35cm" viewBox="0 0 198.61594 33.91004">
  <g id="Publi">
    <path fill="#009846" d="M12 12 L48 12 L48 28 L12 28 Z"/>
  </g>
  <g id="Media">
    <path fill="#66C3D0" d="M62 12 L98 12 L98 28 L62 28 Z"/>
  </g>
</svg>
"""

OWNER_SVG = (
    Path(__file__).resolve().parents[2]
    / "blueprints"
    / "volumetric-letter-svg-test"
    / "litere-volumetrice.svg"
)


def _layer_keys_from_workspace_payload(payload: dict) -> set[str]:
    summary = payload.get("path_geometry_summary") or {}
    return set(layer_keys_from_path_geometry_summary(summary))


def _confirmation_layer_keys(payload: dict) -> set[str]:
    snapshot = payload.get("layer_role_confirmation_snapshot") or {}
    layers = snapshot.get("layers") or []
    return {layer["layer_key"] for layer in layers if isinstance(layer, dict) and layer.get("layer_key")}


def _confirm_layer(auth_client, workspace_id: str, layer_key: str, role: str = "face") -> None:
    response = auth_client.put(
        f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
        json={
            "layers": [
                {"layer_key": layer_key, "confirmed_role": role, "confirmation_state": "confirmed"},
            ]
        },
    )
    assert response.status_code == 200, response.text


class TestReuploadLayerRoleSnapshotInvalidation:
    def test_first_upload_builds_layer_role_draft(self, auth_client) -> None:
        workspace_id = _create_workspace(auth_client)
        upload = _upload_svg(auth_client, workspace_id, "a.svg", SVG_A_LAYER_LITERE)
        assert upload.status_code == 200, upload.text
        payload = upload.json()["workspace"]["payload"]
        assert _layer_keys_from_workspace_payload(payload) == {"layer-litere"}
        assert _confirmation_layer_keys(payload) == {"layer-litere"}

        get_resp = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
        )
        assert get_resp.status_code == 200
        keys = {layer["layer_key"] for layer in get_resp.json()["layer_role_confirmation_snapshot"]["layers"]}
        assert keys == {"layer-litere"}

    def test_reupload_different_svg_rebuilds_layer_roles(self, auth_client) -> None:
        workspace_id = _create_workspace(auth_client)
        first = _upload_svg(auth_client, workspace_id, "a.svg", SVG_A_LAYER_LITERE)
        assert first.status_code == 200, first.text
        _confirm_layer(auth_client, workspace_id, "layer-litere", "face")

        second = _upload_svg(auth_client, workspace_id, "b.svg", SVG_B_COREL_PATHS)
        assert second.status_code == 200, second.text
        payload = second.json()["workspace"]["payload"]
        assert _layer_keys_from_workspace_payload(payload) == {"fata_x0020_plexiglas", "autocolant"}
        confirm_keys = _confirmation_layer_keys(payload)
        assert "layer-litere" not in confirm_keys
        assert confirm_keys == {"fata_x0020_plexiglas", "autocolant"}

        get_resp = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
        )
        assert get_resp.status_code == 200
        body = get_resp.json()
        keys = {layer["layer_key"] for layer in body["layer_role_confirmation_snapshot"]["layers"]}
        assert keys == {"fata_x0020_plexiglas", "autocolant"}
        assert body["layer_role_confirmation_snapshot"]["layers"][0]["confirmed_role"] is None
        warning_codes = {item["code"] for item in body["layer_role_confirmation_snapshot"].get("warnings", [])}
        assert WARN_LAYER_ROLE_CONFIRMATION_RESET_AFTER_SVG_REUPLOAD in warning_codes

    def test_reupload_same_svg_preserves_confirmed_roles(self, auth_client) -> None:
        workspace_id = _create_workspace(auth_client)
        first = _upload_svg(auth_client, workspace_id, "a.svg", SVG_A_LAYER_LITERE)
        assert first.status_code == 200, first.text
        _confirm_layer(auth_client, workspace_id, "layer-litere", "face")

        second = _upload_svg(auth_client, workspace_id, "a-again.svg", SVG_A_LAYER_LITERE)
        assert second.status_code == 200, second.text
        payload = second.json()["workspace"]["payload"]
        snapshot = payload["layer_role_confirmation_snapshot"]
        by_key = {layer["layer_key"]: layer for layer in snapshot["layers"]}
        assert by_key["layer-litere"]["confirmed_role"] == "face"
        assert by_key["layer-litere"]["confirmation_state"] == "confirmed"

    def test_reupload_same_layer_keys_different_content_resets_confirmation(self, auth_client) -> None:
        workspace_id = _create_workspace(auth_client)
        first = _upload_svg(auth_client, workspace_id, "pbl.svg", FLAT_PBL_SVG)
        assert first.status_code == 200, first.text
        _confirm_layer(auth_client, workspace_id, "Publi", "face")
        _confirm_layer(auth_client, workspace_id, "Media", "face")

        second = _upload_svg(auth_client, workspace_id, "pbl-alt.svg", SVG_PBL_SAME_KEYS_ALT)
        assert second.status_code == 200, second.text
        payload = second.json()["workspace"]["payload"]
        assert _confirmation_layer_keys(payload) == {"Publi", "Media"}
        snapshot = payload["layer_role_confirmation_snapshot"]
        by_key = {layer["layer_key"]: layer for layer in snapshot["layers"]}
        assert by_key["Publi"]["confirmation_state"] != "confirmed"
        assert by_key["Media"]["confirmation_state"] != "confirmed"
        warning_codes = {item["code"] for item in snapshot.get("warnings", [])}
        assert WARN_LAYER_ROLE_CONFIRMATION_RESET_AFTER_SVG_REUPLOAD in warning_codes

    @pytest.mark.skipif(not OWNER_SVG.is_file(), reason="owner SVG missing locally")
    def test_reupload_corel_owner_svg_layer_roles_match_path_geometry(self, auth_client) -> None:
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id, "a.svg", SVG_A_LAYER_LITERE)
        _confirm_layer(auth_client, workspace_id, "layer-litere", "face")

        owner_text = OWNER_SVG.read_text(encoding="utf-8")
        upload = _upload_svg(auth_client, workspace_id, "litere-volumetrice.svg", owner_text)
        assert upload.status_code == 200, upload.text
        payload = upload.json()["workspace"]["payload"]
        path_keys = _layer_keys_from_workspace_payload(payload)
        confirm_keys = _confirmation_layer_keys(payload)
        assert "layer-litere" not in confirm_keys
        assert confirm_keys == path_keys
        assert payload["path_geometry_summary"]["parse_status"] == "parsed"

    def test_path_geometry_and_confirmation_keys_aligned_after_reupload(self, auth_client) -> None:
        workspace_id = _create_workspace(auth_client)
        _upload_svg(auth_client, workspace_id, "a.svg", SVG_A_LAYER_LITERE)
        _upload_svg(auth_client, workspace_id, "b.svg", SVG_B_COREL_PATHS)
        workspace = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}").json()
        payload = workspace["payload"]
        assert _confirmation_layer_keys(payload) == _layer_keys_from_workspace_payload(payload)

        auth_client.put(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
            json={
                "layers": [
                    {
                        "layer_key": "fata_x0020_plexiglas",
                        "confirmed_role": "face",
                        "confirmation_state": "confirmed",
                    },
                    {
                        "layer_key": "autocolant",
                        "confirmed_role": "vinyl",
                        "confirmation_state": "confirmed",
                    },
                ]
            },
        )
        classification = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/geometry-path-perimeter-classification",
        ).json()
        assert classification["classification_available"] is True
        face_ml = classification["path_perimeter_classification"]["perimeters"]["face_cutting_perimeter_ml"]["value"]
        assert face_ml is not None and face_ml > 0
