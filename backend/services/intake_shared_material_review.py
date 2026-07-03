"""Neutral helpers for material review display — no pricing or quote side effects."""

from __future__ import annotations

STALE_ORPHAN_TOKENS = frozenset(
    {
        "stale_orphan_defs_split_placement",
        "orphan_defs_parts_in_analysis",
    }
)


def filter_stale_orphan_manual_review_tokens(
    reason: str | None,
    *,
    orphan_defs_split_placement_sqm: float | None,
) -> str | None:
    """Drop stale orphan tokens when orphan defs area is absent after fresh re-analysis."""
    if not reason or not reason.strip():
        return reason
    orphan_sqm = orphan_defs_split_placement_sqm or 0.0
    if orphan_sqm > 0:
        return reason
    parts = [p.strip() for p in reason.split(";") if p.strip()]
    kept = [p for p in parts if p not in STALE_ORPHAN_TOKENS and "orphan_defs" not in p]
    return ";".join(kept) if kept else None


def is_stale_svg_snapshot_review(
    *,
    orphan_defs_split_placement_sqm: float | None,
    manual_review_reason: str | None,
) -> bool:
    if (orphan_defs_split_placement_sqm or 0) > 0:
        return True
    reason = manual_review_reason or ""
    return any(token in reason for token in STALE_ORPHAN_TOKENS)
