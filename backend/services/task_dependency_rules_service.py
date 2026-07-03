"""Task dependency rules for execution plans — MVP volumetric letter pipeline."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple

DEPENDENCY_MODE_ALL_FINISHED = "all_finished"

# process_id → dependency rule (resolved to task_ids at plan generation time).
PROCESS_DEPENDENCY_RULES: Dict[str, Dict[str, Any]] = {
    "return_face_bonding": {
        "depends_on_process_ids": ["face_cnc_cut", "side_forming"],
        "dependency_mode": DEPENDENCY_MODE_ALL_FINISHED,
        "dependency_reason": (
            "Fețele debitate și canturile modelate sunt necesare pentru lipirea canturilor."
        ),
    },
    "led_install_letters": {
        "depends_on_process_ids": ["back_cut"],
        "dependency_mode": DEPENDENCY_MODE_ALL_FINISHED,
        "dependency_reason": "Spatele Forex trebuie debitat înainte de montajul LED.",
    },
    "electrical_letters": {
        "depends_on_process_ids": ["led_install_letters"],
        "dependency_mode": DEPENDENCY_MODE_ALL_FINISHED,
        "dependency_reason": "Cablarea depinde de LED-urile montate.",
    },
    "assembly_letters": {
        "depends_on_process_ids": [
            "return_face_bonding",
            "back_cut",
            "led_install_letters",
            "electrical_letters",
        ],
        "dependency_mode": DEPENDENCY_MODE_ALL_FINISHED,
        "dependency_reason": (
            "Asamblarea depinde de subansamblele pregătite (canturi, spate, LED, cablare)."
        ),
    },
    "qc_letters": {
        "depends_on_process_ids": ["assembly_letters"],
        "dependency_mode": DEPENDENCY_MODE_ALL_FINISHED,
        "dependency_reason": "Verificarea finală se face după asamblare.",
    },
    "packaging_letters": {
        "depends_on_process_ids": ["qc_letters"],
        "dependency_mode": DEPENDENCY_MODE_ALL_FINISHED,
        "dependency_reason": "Ambalarea se face după QC.",
    },
}

# Preparation → execution: vector/file prep before CNC debitare.
PREPARATION_DEPENDENCY_RULES: Dict[str, Dict[str, Any]] = {
    "face_cnc_cut": {
        "depends_on_process_ids": ["vector_prep"],
        "dependency_mode": DEPENDENCY_MODE_ALL_FINISHED,
        "dependency_reason": "Fișierele/vectorii trebuie pregătiți înainte de debitare CNC față.",
    },
    "back_cut": {
        "depends_on_process_ids": ["vector_prep"],
        "dependency_mode": DEPENDENCY_MODE_ALL_FINISHED,
        "dependency_reason": "Fișierele/vectorii trebuie pregătiți înainte de debitare CNC spate.",
    },
    "mounting_template_cnc_cut": {
        "depends_on_process_ids": ["vector_prep"],
        "dependency_mode": DEPENDENCY_MODE_ALL_FINISHED,
        "dependency_reason": "Vector prep necesar înainte de CNC șablon Forex.",
    },
}

CNC_MACHINE_TYPES_FOR_VECTOR_PREP = frozenset({"CNC_ROUTER", "CNC"})


def _normalize_process_id(task: dict) -> str:
    return str(task.get("process_id") or "").strip().lower()


def _build_process_id_index(tasks: List[Any]) -> Dict[str, str]:
    index: Dict[str, str] = {}
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        process_id = _normalize_process_id(entry)
        task_id = str(entry.get("task_id") or "").strip()
        if process_id and task_id and process_id not in index:
            index[process_id] = task_id
    return index


def _resolve_depends_on_task_ids(
    rule: Dict[str, Any],
    process_index: Dict[str, str],
) -> Tuple[List[str], List[str]]:
    depends_on: List[str] = []
    warnings: List[str] = []
    for process_id in rule.get("depends_on_process_ids") or []:
        key = str(process_id or "").strip().lower()
        if not key:
            continue
        task_id = process_index.get(key)
        if task_id:
            depends_on.append(task_id)
        else:
            warnings.append(f"missing_predecessor_process:{key}")
    return depends_on, warnings


def _merge_dependency_rule(
    row: dict,
    rule: Dict[str, Any],
    process_index: Dict[str, str],
    warnings: List[str],
) -> None:
    dep_ids, rule_warnings = _resolve_depends_on_task_ids(rule, process_index)
    warnings.extend(rule_warnings)
    existing = [str(x).strip() for x in (row.get("depends_on_task_ids") or []) if str(x).strip()]
    merged: List[str] = list(existing)
    for dep_id in dep_ids:
        if dep_id not in merged:
            merged.append(dep_id)
    row["depends_on_task_ids"] = merged
    if dep_ids:
        row["dependency_mode"] = str(rule.get("dependency_mode") or DEPENDENCY_MODE_ALL_FINISHED)
        prior_reason = str(row.get("dependency_reason") or "").strip()
        new_reason = str(rule.get("dependency_reason") or "").strip()
        if new_reason and new_reason not in prior_reason:
            row["dependency_reason"] = (
                f"{prior_reason}; {new_reason}" if prior_reason else new_reason
            )


def apply_task_dependency_rules_to_plan_tasks(
    tasks: List[Any],
) -> Tuple[List[Any], List[str], str]:
    """Attach depends_on_task_ids to plan tasks. Idempotent when unchanged."""
    if not isinstance(tasks, list):
        return tasks, [], "invalid_tasks"

    before = json.dumps(tasks, sort_keys=True, ensure_ascii=False)
    process_index = _build_process_id_index(tasks)
    warnings: List[str] = []
    updated: List[Any] = []

    for entry in tasks:
        if not isinstance(entry, dict):
            updated.append(entry)
            continue
        row = dict(entry)
        process_id = _normalize_process_id(row)

        physical_rule = PROCESS_DEPENDENCY_RULES.get(process_id)
        if physical_rule:
            _merge_dependency_rule(row, physical_rule, process_index, warnings)

        prep_rule = PREPARATION_DEPENDENCY_RULES.get(process_id)
        if prep_rule:
            _merge_dependency_rule(row, prep_rule, process_index, warnings)

        machine_type = str(row.get("machine_type") or "").strip().upper()
        if (
            machine_type in CNC_MACHINE_TYPES_FOR_VECTOR_PREP
            and process_id not in PREPARATION_DEPENDENCY_RULES
            and process_id not in PROCESS_DEPENDENCY_RULES
        ):
            vector_rule = {
                "depends_on_process_ids": ["vector_prep"],
                "dependency_mode": DEPENDENCY_MODE_ALL_FINISHED,
                "dependency_reason": "Pregătire vector necesară înainte de CNC.",
            }
            _merge_dependency_rule(row, vector_rule, process_index, warnings)

        updated.append(row)

    after = json.dumps(updated, sort_keys=True, ensure_ascii=False)
    action = "unchanged" if before == after else "updated"
    return updated, warnings, action


def backfill_plan_task_dependencies(tasks: List[Any]) -> Tuple[List[Any], str]:
    """Dev/fixture helper — same as apply, returns (tasks, action)."""
    updated, _warnings, action = apply_task_dependency_rules_to_plan_tasks(tasks)
    return updated, action
