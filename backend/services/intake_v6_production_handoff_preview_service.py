"""Intake V6 production handoff preview namespace."""

from __future__ import annotations

from services.intake_v4_production_handoff_preview_service import (
    build_intake_v4_production_handoff_preview,
)
from services.intake_v6_response_normalization import normalize_intake_v6_model


async def build_intake_v6_production_handoff_preview(*args, **kwargs):
    return normalize_intake_v6_model(await build_intake_v4_production_handoff_preview(*args, **kwargs))
