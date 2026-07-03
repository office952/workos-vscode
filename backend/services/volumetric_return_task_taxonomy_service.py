"""Volumetric return-profile task taxonomy — modelare cant vs lipire cant (execution plan)."""

from __future__ import annotations

import json
from typing import Any, List, Tuple

SIDE_FORMING_PROCESS_ID = "side_forming"
RETURN_BONDING_PROCESS_ID = "return_face_bonding"

MODELING_DISPLAY_NAME = "Modelare canturi litere volumetrice"
BONDING_DISPLAY_NAME = "Lipire canturi pe fețele literelor"

MODELING_PROCESS_TYPE = "edge_bending"
BONDING_PROCESS_TYPE = "volumetric_letter_assembly"

MODELING_MACHINE_TYPE = "RETURN_PROFILE_FORMING_MACHINE"
BONDING_MACHINE_TYPE = "ASSEMBLY_TABLE"

MODELING_INSTRUCTIONS = (
    "Modelează canturile conform schiței, numerotează segmentele "
    "și livrează-le la mesele de ansamblare."
)
BONDING_INSTRUCTIONS = (
    "Lipește canturile numerotate pe fețele literelor conform schiței "
    "și verifică alinierea înainte de fixare finală."
)

WRONG_BONDING_PROCESS_TYPES = frozenset({"welding"})
WRONG_BONDING_MACHINE_TYPES = frozenset({
    "RETURN_PROFILE_FACE_BONDING",
    "return_profile_face_bonding",
})


def _normalize_process_id(task: dict) -> str:
    return str(task.get("process_id") or "").strip().lower()


def is_legacy_wrong_return_bonding_task(task: dict) -> bool:
    if _normalize_process_id(task) != RETURN_BONDING_PROCESS_ID:
        return False
    process_type = str(task.get("process_type") or "").strip().lower()
    machine_type = str(task.get("machine_type") or "").strip().upper()
    display = str(task.get("display_name") or task.get("name") or "").strip().lower()
    if process_type in WRONG_BONDING_PROCESS_TYPES:
        return True
    if machine_type in {m.upper() for m in WRONG_BONDING_MACHINE_TYPES}:
        return True
    if display == "lipire cant pe față":
        return True
    return False


def apply_volumetric_return_taxonomy_to_task(
    task: dict,
    *,
    set_owner_instructions: bool = False,
) -> dict:
    updated = dict(task)
    process_id = _normalize_process_id(updated)
    if not process_id:
        return updated

    if process_id == SIDE_FORMING_PROCESS_ID:
        updated["display_name"] = MODELING_DISPLAY_NAME
        updated["name"] = MODELING_DISPLAY_NAME
        updated["process_type"] = MODELING_PROCESS_TYPE
        updated["machine_type"] = MODELING_MACHINE_TYPE
        if set_owner_instructions and not str(updated.get("instructions") or "").strip():
            updated["instructions"] = MODELING_INSTRUCTIONS
        return updated

    if process_id == RETURN_BONDING_PROCESS_ID:
        updated["display_name"] = BONDING_DISPLAY_NAME
        updated["name"] = BONDING_DISPLAY_NAME
        updated["process_type"] = BONDING_PROCESS_TYPE
        updated["machine_type"] = BONDING_MACHINE_TYPE
        if set_owner_instructions and not str(updated.get("instructions") or "").strip():
            updated["instructions"] = BONDING_INSTRUCTIONS
        return updated

    return updated


def apply_volumetric_return_taxonomy_to_plan_tasks(
    tasks: List[Any],
    *,
    set_owner_instructions: bool = False,
) -> Tuple[List[Any], str]:
    if not isinstance(tasks, list):
        return tasks, "invalid_tasks"

    before = json.dumps(tasks, sort_keys=True, ensure_ascii=False)
    updated: List[Any] = []
    for entry in tasks:
        if isinstance(entry, dict):
            updated.append(
                apply_volumetric_return_taxonomy_to_task(
                    entry,
                    set_owner_instructions=set_owner_instructions,
                )
            )
        else:
            updated.append(entry)

    after = json.dumps(updated, sort_keys=True, ensure_ascii=False)
    if before == after:
        return updated, "unchanged"
    return updated, "updated"


def find_task_by_process_id(tasks: List[dict], process_id: str) -> dict | None:
    key = (process_id or "").strip().lower()
    for task in tasks:
        if isinstance(task, dict) and _normalize_process_id(task) == key:
            return task
    return None
