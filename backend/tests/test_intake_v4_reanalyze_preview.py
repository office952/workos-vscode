"""Intake V4 re-analyze preview — read-only before/after diff."""

from __future__ import annotations

import json
from pathlib import Path

from services.intake_v4_reanalyze_preview_service import (
    build_reanalyze_preview_snapshot,
    compare_reanalyze_preview,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "intake_v4"
PBL_GOLDEN = FIXTURES / "pbl_layere_golden_analysis.json"
PBL_DEGRADED = FIXTURES / "pbl_layere_degraded_analysis.json"


def _pbl_layer_roles() -> dict:
    return {
        "layers": [
            {
                "layer_key": "Layer_x0020_1",
                "layer_name": "Layer_x0020_1",
                "confirmed_role": "printed_artwork",
                "confirmation_state": "confirmed",
            },
            {
                "layer_key": "Layer_x0020_2",
                "layer_name": "Layer_x0020_2",
                "confirmed_role": "face",
                "confirmation_state": "confirmed",
            },
            {
                "layer_key": "Layer_x0020_3",
                "layer_name": "Layer_x0020_3",
                "confirmed_role": "face",
                "confirmation_state": "confirmed",
            },
        ]
    }


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_build_reanalyze_preview_snapshot_pbl_golden():
    analysis = _load(PBL_GOLDEN)
    snapshot = build_reanalyze_preview_snapshot(analysis, _pbl_layer_roles())
    assert snapshot is not None
    assert snapshot.placements_count > 0
    assert snapshot.selected_quantity_sqm is not None


def test_compare_degraded_to_golden_preview_improves_granularity():
    persisted = _load(PBL_DEGRADED)
    fresh = _load(PBL_GOLDEN)
    roles = _pbl_layer_roles()

    before = build_reanalyze_preview_snapshot(persisted, roles)
    after = build_reanalyze_preview_snapshot(fresh, roles)
    assert before is not None
    assert after is not None
    assert after.placements_count >= before.placements_count

    diff = compare_reanalyze_preview(
        persisted_analysis=persisted,
        fresh_analysis=fresh,
        layer_role_setup=roles,
    )
    assert diff["preview_available"] is True
    assert diff["persists_changes"] is False
    assert diff["before"]["placements_count"] <= diff["after"]["placements_count"]
