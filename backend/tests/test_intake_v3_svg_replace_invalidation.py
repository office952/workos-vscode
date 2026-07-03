"""SVG replace invalidates dependent operator state (model, finishes, lighting, quote readiness)."""

from __future__ import annotations

from tests.test_intake_v3_production_model_review import HUB_CONFIRM_PAYLOAD
from tests.test_intake_v3_svg_layer_path_geometry import FLAT_PBL_SVG
from tests.test_intake_v3_svg_upload_analysis import _create_workspace, _upload_svg

SVG_A = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="50mm" viewBox="0 0 100 50">
  <g id="Letters"><path d="M5 5 L95 5 L95 45 L5 45 Z"/></g>
</svg>"""


class TestSvgReplaceInvalidatesDependentState:
    def test_replace_clears_confirmed_model_and_quote_readiness(self, auth_client) -> None:
        workspace_id = _create_workspace(auth_client)
        first = _upload_svg(auth_client, workspace_id, "complex.svg", SVG_A)
        assert first.status_code == 200, first.text

        confirm = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/confirm",
            json=HUB_CONFIRM_PAYLOAD,
        )
        assert confirm.status_code == 200, confirm.text

        preview_before = auth_client.get(f"/api/v1/intake-v3/workspaces/{workspace_id}/preview")
        assert preview_before.status_code == 200
        assert preview_before.json()["preview"]["vector_summary"]["confirmed_letter_count"] == 18

        second = _upload_svg(auth_client, workspace_id, "pbl.svg", FLAT_PBL_SVG)
        assert second.status_code == 200, second.text
        body = second.json()
        next_payload = body["workspace"]["payload"]

        assert next_payload.get("confirmed_production_model") is None
        assert next_payload.get("production_model_status") == "pending"
        assert "svg_dependent_state_invalidated_after_svg_replace" in (
            next_payload.get("svg_dependent_state_warnings") or []
        )

        layer_keys = {
            layer["layer_key"]
            for layer in (next_payload.get("layer_role_confirmation_snapshot") or {}).get("layers") or []
        }
        assert layer_keys == {"Publi", "Media"}

        preview = body["preview"]["preview"]
        assert preview["vector_summary"]["confirmed_letter_count"] == 0
        assert preview["readiness_report"]["can_create_quote"] is False

    def test_same_file_reupload_preserves_confirmed_model(self, auth_client) -> None:
        workspace_id = _create_workspace(auth_client)
        first = _upload_svg(auth_client, workspace_id, "same.svg", SVG_A)
        assert first.status_code == 200

        confirm = auth_client.post(
            f"/api/v1/intake-v3/workspaces/{workspace_id}/production-model/confirm",
            json=HUB_CONFIRM_PAYLOAD,
        )
        assert confirm.status_code == 200

        second = _upload_svg(auth_client, workspace_id, "same.svg", SVG_A)
        assert second.status_code == 200
        next_payload = second.json()["workspace"]["payload"]
        assert next_payload.get("confirmed_production_model") is not None
        assert next_payload["confirmed_production_model"]["letter_count"] == 18
