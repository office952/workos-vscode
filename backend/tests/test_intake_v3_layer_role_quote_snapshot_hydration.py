"""Layer role confirmation must use live workspace path geometry over stale quote snapshots."""

from __future__ import annotations

import pytest

from services.intake_v3_material_quantity_breakdown_service import hydrate_live_workspace_snapshot_sections
from services.intake_v3_workspace_service import sanitize_intake_v3_workspace_payload
from tests.test_intake_v3_svg_upload_analysis import _create_workspace, _upload_svg

SVG_PBL_FLAT = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="205cm" height="35cm" viewBox="0 0 198.61594 33.91004">
  <g id="Publi">
    <path fill="#009846" d="M10 10 L50 10 L50 30 L10 30 Z"/>
  </g>
  <g id="Media">
    <path fill="#66C3D0" d="M60 10 L100 10 L100 30 L60 30 Z"/>
  </g>
</svg>
"""

SVG_OLD_SINGLE_LAYER = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="50mm" viewBox="0 0 100 50">
  <g id="Litere_x0020_Volumetrice_x0020_Luminoase">
    <path d="M10 10 L40 10 L40 30 L10 30 Z"/>
  </g>
</svg>
"""


def _layer_ids_from_workspace(workspace) -> set[str]:
    summary = workspace.path_geometry_summary if workspace else None
    if not isinstance(summary, dict):
        return set()
    return {
        str(layer.get("layer_id"))
        for layer in summary.get("layers") or []
        if isinstance(layer, dict) and layer.get("layer_id")
    }


@pytest.mark.asyncio
async def test_hydrate_live_workspace_replaces_stale_quote_path_geometry(db_session, auth_client) -> None:
    workspace_id = _create_workspace(auth_client)
    upload = _upload_svg(auth_client, workspace_id, "pbl.svg", SVG_PBL_FLAT)
    assert upload.status_code == 200, upload.text

    stale_upload = _upload_svg(auth_client, workspace_id, "old.svg", SVG_OLD_SINGLE_LAYER)
    assert stale_upload.status_code == 200, stale_upload.text
    stale_workspace = sanitize_intake_v3_workspace_payload(stale_upload.json()["workspace"]["payload"])
    assert _layer_ids_from_workspace(stale_workspace) == {"Litere_x0020_Volumetrice_x0020_Luminoase"}

    fresh_upload = _upload_svg(auth_client, workspace_id, "pbl.svg", SVG_PBL_FLAT)
    assert fresh_upload.status_code == 200, fresh_upload.text

    sections = {
        "workspace_payload_snapshot": stale_workspace.model_dump(mode="json"),
    }
    quote_linkage = {"source_workspace_id": workspace_id}
    sections, hydrated_workspace = await hydrate_live_workspace_snapshot_sections(
        db_session,
        quote_linkage,
        sections,
        stale_workspace,
        workspace_id_override=workspace_id,
    )
    assert _layer_ids_from_workspace(hydrated_workspace) == {"Publi", "Media"}

    nested = sections.get("workspace_payload_snapshot") or {}
    nested_layers = {
        layer.get("layer_id")
        for layer in (nested.get("path_geometry_summary") or {}).get("layers") or []
        if isinstance(layer, dict)
    }
    assert nested_layers == {"Publi", "Media"}

