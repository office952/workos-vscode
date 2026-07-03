"""Intake V4 analysis boundary gates."""

from __future__ import annotations

from schemas.intake_v4 import IntakeV4WorkspacePayload
from services.intake_v4_analysis_boundary_service import (
    list_v4_analysis_boundary_blockers,
    list_v4_analysis_hash_sync_blockers,
)
from services.intake_v4_quote_geometry_service import resolve_v4_quote_geometry


def _minimal_payload(**overrides) -> IntakeV4WorkspacePayload:
    base = {
        "schema_version": "1.0.0",
        "product_binding": {"template_code": "TPL-VOLUMETRIC-LETTERS"},
        "svg_source": {
            "file_name": "test.svg",
            "file_hash": "abc123",
            "file_size_bytes": 100,
            "upload_status": "analyzed",
        },
        "svg_analysis_json": {
            "layers": [
                {"id": "l1", "name": "litere", "perimeterMl": 10.0, "filledAreaSqm": 1.5},
            ],
            "parts": {"nestableCount": 10},
        },
        "layer_role_setup": {
            "confirmation_status": "complete",
            "layers": [
                {
                    "layer_key": "l1",
                    "confirmed_role": "face",
                    "confirmation_state": "confirmed",
                }
            ],
        },
        "quote_geometry": {
            "letter_count": 1,
            "letter_perimeter_m": 999.0,
            "face_area_m2": 0.01,
            "confirmed": True,
        },
    }
    base.update(overrides)
    return IntakeV4WorkspacePayload.model_validate(base)


class TestIntakeV4AnalysisBoundary:
    def test_boundary_passes_with_persisted_analysis(self):
        blockers = list_v4_analysis_boundary_blockers(_minimal_payload())
        assert blockers == []

    def test_boundary_blocks_missing_analysis(self):
        payload = _minimal_payload()
        payload = payload.model_copy(update={"svg_analysis_json": None})
        blockers = list_v4_analysis_boundary_blockers(payload)
        assert "missing_svg_analysis_json" in blockers


class TestIntakeV4AnalysisHashSync:
    def test_hash_sync_passes_when_client_matches_persisted(self):
        payload = _minimal_payload()
        blockers = list_v4_analysis_hash_sync_blockers(payload, "abc123")
        assert blockers == []

    def test_hash_sync_blocks_missing_client_hash(self):
        payload = _minimal_payload()
        blockers = list_v4_analysis_hash_sync_blockers(payload, None)
        assert blockers == ["missing_client_analysis_hash"]

    def test_hash_sync_blocks_mismatch(self):
        payload = _minimal_payload()
        blockers = list_v4_analysis_hash_sync_blockers(payload, "deadbeef" * 8)
        assert blockers == ["analysis_hash_mismatch"]


class TestResolveV4QuoteGeometryCanonical:
    def test_derives_from_analysis_not_stale_persisted_metrics(self):
        payload = _minimal_payload()
        quote = resolve_v4_quote_geometry(payload)
        assert quote["letter_perimeter_m"] == 10.0
        assert quote["face_area_m2"] == 1.5
        assert quote["letter_count"] == 10
