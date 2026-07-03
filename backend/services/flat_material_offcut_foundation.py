"""Offcut measurement + inventory intake foundation for sheet nesting.

Inventory write is deferred: ``StockMovement`` currently supports only
``consumption`` / ``reversal`` tied to ``ExecutionReality`` — no
``offcut_created`` movement type yet.
"""

from __future__ import annotations

from typing import Any, Mapping, MutableMapping, Sequence

OFFCUT_MEASUREMENT_TASK_PROCESS_ID = "post_cut_offcut_measurement"
OFFCUT_MEASUREMENT_TASK_DISPLAY_NAME = "Măsurare rest placă"
OFFCUT_MEASUREMENT_TASK_INSTRUCTIONS = (
    "Măsoară resturile reutilizabile rămase după debitarea plăcii.\n\n"
    "Introdu fiecare rest care poate fi refolosit:\n"
    "- material\n"
    "- grosime\n"
    "- lățime mm\n"
    "- înălțime mm\n"
    "- stare\n"
    "- locație\n"
    "- observații\n\n"
    "Nu introduce bucățile foarte mici sau deteriorate dacă nu pot fi folosite."
)

INVENTORY_INTAKE_STATUS = "deferred"
INVENTORY_INTAKE_REASON = (
    "StockMovement supports consumption/reversal only; offcut intake requires "
    "movement_type extension and dimensional inventory item model."
)


def sheet_nesting_requires_offcut_measurement(handoff_block: Mapping[str, Any] | None) -> bool:
    if not isinstance(handoff_block, dict):
        return False
    if not handoff_block.get("enabled"):
        return False
    nesting = handoff_block.get("nesting")
    if not isinstance(nesting, dict):
        return False
    sheets_used = nesting.get("sheets_used")
    try:
        return int(sheets_used) > 0
    except (TypeError, ValueError):
        return False


def build_offcut_measurement_task_metadata(
    *,
    order_id: int | None = None,
    material_code: str,
    source_nesting_role: str,
    sheets_used: int = 1,
) -> dict[str, Any]:
    return {
        "process_id": OFFCUT_MEASUREMENT_TASK_PROCESS_ID,
        "display_name": OFFCUT_MEASUREMENT_TASK_DISPLAY_NAME,
        "instructions": OFFCUT_MEASUREMENT_TASK_INSTRUCTIONS,
        "material_code": material_code,
        "source_nesting_role": source_nesting_role,
        "sheets_used": sheets_used,
        "order_id": order_id,
        "inventory_intake_status": INVENTORY_INTAKE_STATUS,
        "inventory_intake_reason": INVENTORY_INTAKE_REASON,
    }


def validate_offcut_measurement_payload(payload: Mapping[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    offcuts = payload.get("offcuts")
    if not isinstance(offcuts, list) or len(offcuts) == 0:
        errors.append("offcuts_required")
        return False, errors

    for index, item in enumerate(offcuts):
        if not isinstance(item, dict):
            errors.append(f"offcut_{index}_invalid")
            continue
        for field in ("width_mm", "height_mm"):
            try:
                val = float(item[field])
                if val <= 0:
                    errors.append(f"offcut_{index}_{field}_non_positive")
            except (KeyError, TypeError, ValueError):
                errors.append(f"offcut_{index}_{field}_missing")

    return len(errors) == 0, errors


def normalize_offcut_measurement_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize operator payload; compute ``area_m2`` per offcut."""
    offcuts_out: list[dict[str, Any]] = []
    for raw in payload.get("offcuts") or []:
        if not isinstance(raw, dict):
            continue
        width = float(raw["width_mm"])
        height = float(raw["height_mm"])
        quantity = int(raw.get("quantity") or 1)
        offcuts_out.append(
            {
                "width_mm": width,
                "height_mm": height,
                "quantity": quantity,
                "area_m2": round(width * height / 1_000_000.0 * quantity, 6),
                "condition": raw.get("condition") or "usable",
                "location": raw.get("location"),
                "notes": raw.get("notes"),
            }
        )
    return {
        "order_id": payload.get("order_id"),
        "task_id": payload.get("task_id"),
        "material_code": payload.get("material_code"),
        "source_nesting_role": payload.get("source_nesting_role"),
        "source_sheet_index": payload.get("source_sheet_index"),
        "offcuts": offcuts_out,
    }


def enrich_handoff_with_offcut_foundation(
    handoff: MutableMapping[str, Any],
    *,
    plexiglass_face_nesting: Mapping[str, Any] | None = None,
    forex_backing_nesting: Mapping[str, Any] | None = None,
) -> None:
    """Attach offcut measurement flags without modifying execution plans."""
    required = (
        sheet_nesting_requires_offcut_measurement(plexiglass_face_nesting)
        or sheet_nesting_requires_offcut_measurement(forex_backing_nesting)
    )
    handoff["real_offcut_measurement_required"] = required
    if not required:
        return

    tasks_meta: list[dict[str, Any]] = []
    for role, block in (
        ("plexiglass_face", plexiglass_face_nesting),
        ("forex_backing", forex_backing_nesting),
    ):
        if not sheet_nesting_requires_offcut_measurement(block):
            continue
        material = (block or {}).get("material") or {}
        nesting = (block or {}).get("nesting") or {}
        tasks_meta.append(
            build_offcut_measurement_task_metadata(
                material_code=str(material.get("material_code") or ""),
                source_nesting_role=role,
                sheets_used=int(nesting.get("sheets_used") or 1),
            )
        )
    handoff["post_cut_offcut_measurement_tasks"] = tasks_meta
    handoff["offcut_inventory_intake"] = {
        "status": INVENTORY_INTAKE_STATUS,
        "reason": INVENTORY_INTAKE_REASON,
    }
