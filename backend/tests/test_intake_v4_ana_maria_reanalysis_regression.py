"""Regression: Ana Maria post re-analysis material review truth."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.intake_shared_material_review import (
    filter_stale_orphan_manual_review_tokens,
    is_stale_svg_snapshot_review,
)
from services.intake_v4_reanalyze_preview_service import (
    build_reanalyze_preview_snapshot,
    compare_reanalyze_preview,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "intake_v4"
ANA_FRESH = FIXTURES / "ana_maria_fresh_analysis.json"
ANA_POST = FIXTURES / "ana_maria_post_reanalysis_metrics.json"
PBL_DEGRADED = FIXTURES / "pbl_layere_degraded_analysis.json"
PBL_GOLDEN = FIXTURES / "pbl_layere_golden_analysis.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _ana_maria_layer_roles() -> dict:
    return {
        "confirmation_status": "complete",
        "layers": [
            {"layer_key": "pseudo gradinita", "confirmed_role": "face", "confirmation_state": "confirmed"},
            {"layer_key": "pseudo ana", "confirmed_role": "face", "confirmation_state": "confirmed"},
            {"layer_key": "pseudo maria", "confirmed_role": "face", "confirmation_state": "confirmed"},
            {"layer_key": "pseudo soare", "confirmed_role": "face", "confirmation_state": "confirmed"},
            {"layer_key": "logo stanga", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
            {"layer_key": "logo dreapta", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
        ],
        "warnings": [],
    }


def _pbl_layer_roles() -> dict:
    return {
        "layers": [
            {"layer_key": "Layer_x0020_1", "confirmed_role": "printed_artwork", "confirmation_state": "confirmed"},
            {"layer_key": "Layer_x0020_2", "confirmed_role": "face", "confirmation_state": "confirmed"},
            {"layer_key": "Layer_x0020_3", "confirmed_role": "face", "confirmation_state": "confirmed"},
        ]
    }


def test_fresh_ana_maria_analysis_has_no_orphan_splits():
    analysis = _load(ANA_FRESH)
    parts = (analysis.get("parts") or {}).get("items") or []
    split_count = sum(
        1 for p in parts if isinstance(p, dict) and str(p.get("id", "")).startswith("split_layer_")
    )
    assert split_count == 0


def test_fresh_ana_maria_reanalysis_preview_metrics():
    analysis = _load(ANA_FRESH)
    roles = _ana_maria_layer_roles()
    snapshot = build_reanalyze_preview_snapshot(analysis, roles)
    assert snapshot is not None
    assert snapshot.orphan_defs_split_placement_sqm in (None, 0)
    assert snapshot.layout_occupied_sqm == pytest.approx(2.5238, abs=0.02)
    assert snapshot.requires_manual_review is True


def test_ana_maria_post_reanalysis_policy_floor_documented():
    """Guards controlled execution metrics (see BUILD_INTAKE_V4_ANA_MARIA_CONTROLLED_REANALYZE_EXECUTION.md)."""
    expected = _load(ANA_POST)
    analysis = _load(ANA_FRESH)
    roles = _ana_maria_layer_roles()
    snapshot = build_reanalyze_preview_snapshot(analysis, roles)
    assert snapshot is not None
    assert snapshot.orphan_defs_split_placement_sqm in (None, 0)
    assert snapshot.layout_occupied_sqm == pytest.approx(expected["layout_occupied_area_sqm"], abs=0.02)
    diff = compare_reanalyze_preview(
        persisted_analysis=analysis,
        fresh_analysis=analysis,
        layer_role_setup=roles,
    )
    assert diff["persists_changes"] is False
    assert diff["selected_quantity_unchanged"] is True
    assert expected["is_applied_to_quote"] is False
    assert expected["selected_quote_sheet_area_sqm"] == pytest.approx(1.2638, abs=0.0002)


def test_reanalyze_preview_does_not_persist_or_create_quote_side_effects():
    diff = compare_reanalyze_preview(
        persisted_analysis=_load(PBL_DEGRADED),
        fresh_analysis=_load(PBL_GOLDEN),
        layer_role_setup=_pbl_layer_roles(),
    )
    assert diff["persists_changes"] is False
    assert diff["preview_available"] is True
    assert diff["selected_quantity_unchanged"] is True


def test_filter_stale_orphan_tokens_after_fresh_analysis():
    reason = (
        "stale_orphan_defs_split_placement;orphan_defs_parts_in_analysis;"
        "pseudo_layer_or_unlayered_complexity"
    )
    filtered = filter_stale_orphan_manual_review_tokens(
        reason,
        orphan_defs_split_placement_sqm=None,
    )
    assert filtered == "pseudo_layer_or_unlayered_complexity"
    assert is_stale_svg_snapshot_review(
        orphan_defs_split_placement_sqm=None,
        manual_review_reason=filtered,
    ) is False
