"""Operator-facing production task labels for Intake V4 — catalog keys unchanged."""

from __future__ import annotations

_V4_OPERATOR_TASK_LABELS: dict[str, str] = {
    "return_vinyl_application_workbench": "Aplicare Oracal 651 pe cant / volum la banc de lucru",
    "face_vinyl_application_final": "Aplicare autocolant pe fețele literelor",
}


def operator_task_label_for_seed(seed_code: str, catalog_label: str) -> str:
    """Map V3 catalog display_name to Intake V4 operator wording when defined."""
    key = str(seed_code or "").strip()
    if not key:
        return catalog_label
    return _V4_OPERATOR_TASK_LABELS.get(key, catalog_label)


def operator_task_label_for_operation(operation_code: str, catalog_label: str) -> str:
    """Same mapping keyed by operation_code (matches seed_code for catalog entries)."""
    return operator_task_label_for_seed(operation_code, catalog_label)
