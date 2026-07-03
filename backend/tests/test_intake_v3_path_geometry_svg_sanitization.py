"""Path geometry summary — safe DOCTYPE sanitization for owner SVG exports."""

from __future__ import annotations

from pathlib import Path

import pytest

from services.intake_v3_geometry_metrics_snapshot_service import build_path_geometry_summary_from_svg_text
from services.svg_metrics_service import SvgMetricsService
from services.svg_sanitization_service import (
    ERROR_SVG_UNSAFE_ENTITY_DECLARATION,
    OPERATOR_MESSAGE_SVG_UNSUPPORTED_XML,
    WARN_SVG_SANITIZED_DOCTYPE_REMOVED,
    prepare_svg_text_for_safe_geometry_parsing,
    sanitize_svg_for_analysis,
)
from tests.test_intake_v3_svg_upload_analysis import _create_workspace, _upload_svg
from tests.test_svg_sanitization import COREL_DOCTYPE_SVG

FIXTURE_MULTILAYER = (
    Path(__file__).resolve().parents[2]
    / "frontend"
    / "e2e"
    / "fixtures"
    / "volumetric-multilayer.svg"
)
OWNER_SVG = (
    Path(__file__).resolve().parents[2]
    / "blueprints"
    / "volumetric-letter-svg-test"
    / "litere-volumetrice.svg"
)

XXE_SVG = """<?xml version="1.0"?>
<!DOCTYPE svg [
  <!ENTITY xxe SYSTEM "file:///etc/passwd">
]>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
  <path d="M0 0 L10 10"/>
</svg>
"""

ENTITY_IN_DOCTYPE_SVG = """<?xml version="1.0"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd" [
  <!ENTITY foo "bar">
]>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
  <path d="M0 0 L10 10"/>
</svg>
"""

CLEAN_SVG = """<?xml version="1.0"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50" width="100mm" height="50mm">
  <g id="LITERE"><path d="M10 40 L20 10 L30 40 Z"/></g>
</svg>
"""

MULTILINE_DOCTYPE_SVG = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" width="100mm" height="50mm" viewBox="0 0 100 50">
  <g id="LITERE"><path d="M10 40 L20 10 L30 40 Z"/></g>
</svg>
"""


class TestPrepareSvgTextForSafeGeometryParsing:
    def test_clean_svg_unchanged(self) -> None:
        prep = prepare_svg_text_for_safe_geometry_parsing(CLEAN_SVG)
        assert prep.ok is True
        assert prep.svg_text == CLEAN_SVG
        assert prep.sanitization is None

    def test_standard_doctype_sanitized(self) -> None:
        prep = prepare_svg_text_for_safe_geometry_parsing(COREL_DOCTYPE_SVG)
        assert prep.ok is True
        assert prep.svg_text is not None
        assert prep.sanitization is not None
        assert prep.sanitization.analysis_sanitized is True
        assert WARN_SVG_SANITIZED_DOCTYPE_REMOVED in prep.warnings
        assert SvgMetricsService.parse_svg_metrics(prep.svg_text).parse_status == "parsed"

    def test_multiline_doctype_sanitized(self) -> None:
        prep = prepare_svg_text_for_safe_geometry_parsing(MULTILINE_DOCTYPE_SVG)
        assert prep.ok is True
        assert prep.svg_text is not None
        assert SvgMetricsService.parse_svg_metrics(prep.svg_text).parse_status == "parsed"

    def test_entity_declaration_blocked(self) -> None:
        prep = prepare_svg_text_for_safe_geometry_parsing(ENTITY_IN_DOCTYPE_SVG)
        assert prep.ok is False
        assert prep.error_code == ERROR_SVG_UNSAFE_ENTITY_DECLARATION
        assert prep.operator_message == OPERATOR_MESSAGE_SVG_UNSUPPORTED_XML

    def test_xxe_pattern_blocked(self) -> None:
        prep = prepare_svg_text_for_safe_geometry_parsing(XXE_SVG)
        assert prep.ok is False
        assert prep.error_code in {
            ERROR_SVG_UNSAFE_ENTITY_DECLARATION,
            "svg_unsafe_dtd_declaration",
        }


class TestBuildPathGeometrySummaryFromSvgText:
    def test_clean_svg_parsed(self) -> None:
        summary = build_path_geometry_summary_from_svg_text(CLEAN_SVG)
        assert summary is not None
        assert summary["parse_status"] == "parsed"
        assert summary.get("doctype_removed_for_safe_parse") is not True

    def test_doctype_svg_parsed_with_metadata(self) -> None:
        summary = build_path_geometry_summary_from_svg_text(COREL_DOCTYPE_SVG)
        assert summary is not None
        assert summary["parse_status"] == "parsed"
        assert summary.get("doctype_removed_for_safe_parse") is True
        assert WARN_SVG_SANITIZED_DOCTYPE_REMOVED in summary.get("warnings", [])
        assert summary.get("layer_count", 0) >= 1

    def test_entity_svg_failed_with_clear_code(self) -> None:
        summary = build_path_geometry_summary_from_svg_text(ENTITY_IN_DOCTYPE_SVG)
        assert summary is not None
        assert summary["parse_status"] == "failed"
        assert summary["error_code"] == ERROR_SVG_UNSAFE_ENTITY_DECLARATION

    @pytest.mark.skipif(not FIXTURE_MULTILAYER.is_file(), reason="multilayer fixture missing")
    def test_multilayer_fixture_still_parsed(self) -> None:
        svg_text = FIXTURE_MULTILAYER.read_text(encoding="utf-8")
        summary = build_path_geometry_summary_from_svg_text(svg_text)
        assert summary is not None
        assert summary["parse_status"] == "parsed"

    @pytest.mark.skipif(not OWNER_SVG.is_file(), reason="owner SVG missing locally")
    def test_owner_svg_parsed_after_doctype_sanitization(self) -> None:
        svg_text = OWNER_SVG.read_text(encoding="utf-8")
        assert "<!DOCTYPE" in svg_text
        assert "<!ENTITY" not in svg_text.upper()

        before = build_path_geometry_summary_from_svg_text(svg_text)
        assert before is not None
        assert before["parse_status"] == "parsed"
        assert before.get("doctype_removed_for_safe_parse") is True
        assert before.get("error_code") != "xml_unsafe_construct"
        assert before.get("layer_count", 0) >= 1
        layers = before.get("layers") or []
        layer_ids = {layer.get("layer_id") for layer in layers if isinstance(layer, dict)}
        assert "fata_x0020_plexiglas" in layer_ids or "Spate" in layer_ids


class TestIntakeV3UploadPathGeometryDoctype:
    def test_upload_doctype_svg_sets_parsed_path_geometry(self, auth_client) -> None:
        workspace_id = _create_workspace(auth_client)
        response = _upload_svg(auth_client, workspace_id, "corel.svg", COREL_DOCTYPE_SVG)
        assert response.status_code == 200
        payload = response.json()["workspace"]["payload"]
        summary = payload.get("path_geometry_summary") or {}
        assert summary.get("parse_status") == "parsed"
        assert summary.get("doctype_removed_for_safe_parse") is True
        assert WARN_SVG_SANITIZED_DOCTYPE_REMOVED in summary.get("warnings", [])

    @pytest.mark.skipif(not OWNER_SVG.is_file(), reason="owner SVG missing locally")
    def test_upload_owner_svg_path_geometry_not_xml_unsafe(self, auth_client) -> None:
        workspace_id = _create_workspace(auth_client)
        svg_text = OWNER_SVG.read_text(encoding="utf-8")
        response = _upload_svg(auth_client, workspace_id, "litere-volumetrice.svg", svg_text)
        assert response.status_code == 200
        summary = response.json()["workspace"]["payload"].get("path_geometry_summary") or {}
        assert summary.get("parse_status") == "parsed"
        assert summary.get("error_code") != "xml_unsafe_construct"
        assert summary.get("layer_count", 0) >= 1
