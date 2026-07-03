"""Derive operational preparation domain for execution plan / blueprint tasks."""

from __future__ import annotations

from typing import Any, Mapping

CNC_MACHINE_TYPES = frozenset({"CNC_ROUTER", "CNC"})
CNC_PROCESS_IDS = frozenset(
    {
        "face_cnc_cut",
        "back_cut",
        "mounting_template_cnc_cut",
        "cnc_cut",
        "cnc_routing",
        "forex_back_cut",
        "volumetric_back_cut",
        "plexiglas_face_cut",
        "volumetric_face_cut",
    }
)
CNC_PROCESS_TYPES = frozenset({"cnc_routing"})

PRINT_PROCESS_TYPES = frozenset({"print", "vinyl", "laminating", "printing"})
PRINT_MACHINE_TYPES = frozenset({"PRINTER", "VINYL", "LAMINATOR", "PRINT"})
PRINT_PROCESS_ID_MARKERS = ("print", "vinyl", "laminat", "oracal", "colant")

INSTRUMENTATION_PROCESS_IDS = frozenset(
    {
        "document_handoff",
        "vector_prep",
        "vector_preparation",
        "production_document_handoff",
        "workshop_info",
        "instrumentation_prep",
    }
)
INSTRUMENTATION_PROCESS_TYPES = frozenset({"document", "prep", "handoff", "graphics"})
INSTRUMENTATION_MARKERS = ("document", "vector", "handoff", "schi", "sketch", "file_prep")

WORKSHOP_INFO_MARKERS = ("workshop_info", "workshop", "atelier_info")


def derive_preparation_domain(task: Mapping[str, Any]) -> str:
    """Classify a plan task into a preparation domain without DB migration."""
    process_id = str(task.get("process_id") or "").strip().lower()
    process_type = str(task.get("process_type") or "").strip().lower()
    machine_type = str(task.get("machine_type") or "").strip().upper()
    name = str(task.get("display_name") or task.get("name") or "").strip().lower()

    if (
        machine_type in CNC_MACHINE_TYPES
        or process_id in CNC_PROCESS_IDS
        or process_type in CNC_PROCESS_TYPES
        or "cnc" in process_id
    ):
        return "cnc"

    if any(marker in process_id for marker in WORKSHOP_INFO_MARKERS):
        return "workshop_info"

    if (
        process_type in PRINT_PROCESS_TYPES
        or machine_type in PRINT_MACHINE_TYPES
        or any(marker in process_id for marker in PRINT_PROCESS_ID_MARKERS)
        or any(marker in name for marker in ("print", "vinyl", "lamin"))
    ):
        return "print"

    if (
        process_id in INSTRUMENTATION_PROCESS_IDS
        or process_type in INSTRUMENTATION_PROCESS_TYPES
        or any(marker in process_id for marker in INSTRUMENTATION_MARKERS)
        or any(marker in name for marker in INSTRUMENTATION_MARKERS)
        or task.get("documents")
    ):
        return "instrumentation"

    return "other"


def group_tasks_by_preparation_domain(
    tasks: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {
        "cnc": [],
        "instrumentation": [],
        "print": [],
        "workshop_info": [],
        "other": [],
    }
    for task in tasks:
        if not isinstance(task, dict):
            continue
        domain = str(task.get("preparation_domain") or derive_preparation_domain(task))
        bucket = domain if domain in grouped else "other"
        grouped[bucket].append(task)
    return grouped
