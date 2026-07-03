"""Intake V6 task generation dry-run namespace."""

from __future__ import annotations

from services.intake_v4_task_generation_dry_run_service import (
    build_intake_v4_task_generation_dry_run,
)
from services.intake_v6_response_normalization import normalize_intake_v6_model


async def build_intake_v6_task_generation_dry_run(*args, **kwargs):
    return normalize_intake_v6_model(await build_intake_v4_task_generation_dry_run(*args, **kwargs))
