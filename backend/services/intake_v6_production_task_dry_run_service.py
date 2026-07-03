"""Intake V6 production task dry-run namespace."""

from __future__ import annotations

from services.intake_v4_production_task_dry_run_service import (
    build_v4_production_task_dry_run,
)
from services.intake_v6_response_normalization import normalize_intake_v6_model


def build_v6_production_task_dry_run(*args, **kwargs):
    return normalize_intake_v6_model(build_v4_production_task_dry_run(*args, **kwargs))
