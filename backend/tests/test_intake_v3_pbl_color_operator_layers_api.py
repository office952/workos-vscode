"""API integration — pbl-color.svg layer/color evidence on upload."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.test_intake_v3_svg_upload_analysis import _create_workspace, _upload_svg

REPO_ROOT = Path(__file__).resolve().parents[2]
PBL_COLOR_SVG = REPO_ROOT / "tmp" / "atoms-export" / "uploads" / "pbl-color.svg"

pytestmark = pytest.mark.skipif(not PBL_COLOR_SVG.is_file(), reason="pbl-color.svg fixture missing")


class TestIntakeV3PblColorOperatorLayersApi:
    def test_upload_pbl_color_builds_three_layers_with_color_evidence(self, auth_client):
        workspace_id = _create_workspace(auth_client)
        svg_text = PBL_COLOR_SVG.read_text(encoding="utf-8", errors="replace")
        upload = _upload_svg(auth_client, workspace_id, "pbl-color.svg", svg_text)
        assert upload.status_code == 200

        payload = upload.json()["workspace"]["payload"]
        path_summary = payload.get("path_geometry_summary") or {}
        layer_ids = {layer.get("layer_id") for layer in path_summary.get("layers") or []}
        assert layer_ids == {"Cadru", "Litere_x0020_volumetrice", "Emblema"}

        font = path_summary.get("font_evidence") or {}
        assert font.get("converted_to_paths") is True

        layer_response = auth_client.get(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/layer-role-confirmation",
        )
        assert layer_response.status_code == 200
        snapshot = layer_response.json()["layer_role_confirmation_snapshot"]
        assert snapshot is not None
        keys = {layer["layer_key"] for layer in snapshot["layers"]}
        assert keys == {"Cadru", "Litere_x0020_volumetrice", "Emblema"}

        litere = next(layer for layer in snapshot["layers"] if layer["layer_key"] == "Litere_x0020_volumetrice")
        fills = (litere.get("color_evidence") or {}).get("fills") or []
        assert "#E31E24" in fills
        assert "#393185" in fills
        assert litere["auto_role"] == "face"

        emblema = next(layer for layer in snapshot["layers"] if layer["layer_key"] == "Emblema")
        assert emblema["metrics"]["polygon_count"] == 510
        assert emblema["auto_role"] == "printed_artwork"
        assert (emblema.get("color_evidence") or {}).get("is_multicolor") is True

        cadru = next(layer for layer in snapshot["layers"] if layer["layer_key"] == "Cadru")
        assert cadru["metrics"]["rect_count"] == 10
        assert cadru["auto_role"] == "reference"
