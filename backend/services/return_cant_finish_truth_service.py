"""Canonical cant/return finish normalization at persist — per-layer truth owner."""

from __future__ import annotations

from typing import Any

from schemas.intake_v4 import IntakeV4ArtworkFinish, IntakeV4FinishSetup, IntakeV4LetterGroupFinish

STOCK_RETURN_FINISH_TYPES = frozenset(
    {
        "white_aluminum",
        "black_aluminum",
        "gold_aluminum",
        "mirror_silver",
        "standard_aluminum",
    }
)
VINYL_RETURN_FINISH_TYPES = frozenset(
    {
        "oracal_wrapped",
        "oracal_651",
        "oracal_641",
        "oracal",
        "vinyl",
        "colantat",
    }
)
PAINT_RETURN_FINISH_TYPES = frozenset(
    {
        "ral_paint",
        "vopsit_ral",
        "painted",
        "paint",
        "ral",
    }
)
INACTIVE_RETURN_FINISH_TYPES = frozenset(
    {
        "none",
        "no_return",
        "without_return",
        "unspecified",
        "same_as_face",
    }
)


def return_finish_method_for_type(finish_type: str | None) -> str | None:
    token = str(finish_type or "").strip().lower()
    if not token or token in INACTIVE_RETURN_FINISH_TYPES:
        return None
    if token in STOCK_RETURN_FINISH_TYPES:
        return "stock_color"
    if token in VINYL_RETURN_FINISH_TYPES:
        return "vinyl_application"
    if token in PAINT_RETURN_FINISH_TYPES:
        return "paint_application"
    return None


def return_finish_requires_color_fields(finish_type: str | None) -> bool:
    method = return_finish_method_for_type(finish_type)
    return method in {"vinyl_application", "paint_application"}


def _hydrate_return_row(
    row: IntakeV4LetterGroupFinish | IntakeV4ArtworkFinish,
    *,
    global_finish_type: str | None,
    global_depth: float | int | None,
    global_color_code: str | None,
    global_color_name: str | None,
) -> IntakeV4LetterGroupFinish | IntakeV4ArtworkFinish:
    finish_type = row.return_finish_type or global_finish_type
    depth = row.return_depth_mm if row.return_depth_mm is not None else global_depth
    updates: dict[str, Any] = {
        "return_finish_type": finish_type,
        "return_depth_mm": depth,
    }
    if return_finish_requires_color_fields(finish_type):
        updates["return_oracal_code"] = row.return_oracal_code or global_color_code
        updates["return_oracal_name"] = row.return_oracal_name or global_color_name
    else:
        updates["return_oracal_code"] = None
        updates["return_oracal_name"] = None
    return row.model_copy(update=updates)


def normalize_return_cant_finish_setup(setup: IntakeV4FinishSetup) -> IntakeV4FinishSetup:
    """Hydrate per-layer cant truth and clear stale dependent color fields at save."""
    groups = list(setup.letter_group_finishes or [])
    artwork = list(setup.artwork_finishes or [])
    if not groups and not artwork:
        method = return_finish_method_for_type(setup.return_finish_type)
        updates: dict[str, Any] = {}
        if method in {None} and setup.return_finish_type in INACTIVE_RETURN_FINISH_TYPES:
            updates["return_oracal_code"] = None
            updates["return_oracal_name"] = None
        elif not return_finish_requires_color_fields(setup.return_finish_type):
            updates["return_oracal_code"] = None
            updates["return_oracal_name"] = None
        return setup.model_copy(update=updates) if updates else setup

    global_finish = setup.return_finish_type
    global_depth = setup.return_depth_mm
    global_code = setup.return_oracal_code
    global_name = setup.return_oracal_name

    hydrated_groups = [
        _hydrate_return_row(
            group,
            global_finish_type=global_finish,
            global_depth=global_depth,
            global_color_code=global_code,
            global_color_name=global_name,
        )
        for group in groups
    ]
    hydrated_artwork = [
        _hydrate_return_row(
            row,
            global_finish_type=global_finish,
            global_depth=global_depth,
            global_color_code=global_code,
            global_color_name=global_name,
        )
        for row in artwork
    ]

    dominant_finish = _dominant_return_finish_type(
        [g.return_finish_type for g in hydrated_groups]
        + [a.return_finish_type for a in hydrated_artwork]
        + [global_finish],
    )
    depths = [
        float(d)
        for d in (
            [g.return_depth_mm for g in hydrated_groups if g.return_depth_mm is not None]
            + [a.return_depth_mm for a in hydrated_artwork if a.return_depth_mm is not None]
            + ([global_depth] if global_depth is not None else [])
        )
        if d is not None
    ]
    updates: dict[str, Any] = {
        "letter_group_finishes": hydrated_groups,
        "artwork_finishes": hydrated_artwork,
    }
    if dominant_finish:
        updates["return_finish_type"] = dominant_finish
    if depths:
        updates["return_depth_mm"] = max(depths)
    if return_finish_requires_color_fields(dominant_finish or global_finish):
        codes = [
            c
            for c in (
                [g.return_oracal_code for g in hydrated_groups]
                + [a.return_oracal_code for a in hydrated_artwork]
                + [global_code]
            )
            if c
        ]
        names = [
            n
            for n in (
                [g.return_oracal_name for g in hydrated_groups]
                + [a.return_oracal_name for a in hydrated_artwork]
                + [global_name]
            )
            if n
        ]
        if codes:
            updates["return_oracal_code"] = codes[0]
        if names:
            updates["return_oracal_name"] = names[0]
    else:
        updates["return_oracal_code"] = None
        updates["return_oracal_name"] = None

    return setup.model_copy(update=updates)


def _dominant_return_finish_type(values: list[str | None]) -> str | None:
    from collections import Counter

    cleaned = [str(v).strip() for v in values if v and str(v).strip()]
    if not cleaned:
        return None
    return Counter(cleaned).most_common(1)[0][0]
