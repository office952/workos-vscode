"""Conditional task filtering for TPL-VOLUMETRIC-LETTERS execution plans."""

from __future__ import annotations

import json
from typing import Any, Dict, List, Mapping, MutableMapping, Tuple

from services.task_preparation_readiness_service import extract_quote_input_from_snapshot
from services.volumetric_face_vinyl_service import (
    FACE_VINYL_DISPLAY_NAME,
    apply_face_vinyl_taxonomy_to_plan_tasks,
    build_return_vinyl_task_instructions,
    extract_product_spec_from_snapshot,
    has_face_vinyl_application,
    recalculate_plan_total_minutes,
)
from services.volumetric_finish_assignment_service import (
    RETURN_VINYL_DISPLAY_NAME,
    RETURN_VINYL_PROCESS_ID,
    has_return_vinyl_application,
    resolve_volumetric_operational_quote_input,
)
from services.volumetric_material_rate_resolver import is_volumetric_template_code
from services.volumetric_quote_input_policy import (
    ILLUMINATION_DISABLED_TYPES,
    ILLUMINATION_ENABLED_TYPES,
    LIGHTING_SYSTEM_ENABLED_TYPES,
    is_cant_ral_paint_enabled,
    normalize_mounting_template_material_type,
    normalize_mounting_template_enabled,
)

ILLUMINATION_PROCESS_IDS = frozenset({"led_install_letters", "electrical_letters"})
MOUNTING_TEMPLATE_CNC_PROCESS_ID = "mounting_template_cnc_cut"
PAINTING_PROCESS_ID = "painting"
FACE_VINYL_PROCESS_ID = "vinyl_application"
ASSEMBLY_PROCESS_ID = "assembly_letters"
QC_PROCESS_ID = "qc_letters"
PACKAGING_PROCESS_ID = "packaging_letters"

QC_DISPLAY_NAME = "Verificare finală lucrare"
QC_INSTRUCTIONS = (
    "Verifică lucrarea înainte de predare sau montaj: finisaj, asamblare, "
    "iluminare dacă există și conformitate cu comanda."
)

PACKAGING_DISPLAY_NAME = (
    "Infoliere cu folie stretch și pregătire colet pentru livrare / montaj"
)
PACKAGING_INSTRUCTIONS_BASE = (
    "Infoliere cu folie stretch; pregătire colet pentru livrare sau montaj."
)
PAINTING_DISPLAY_NAME = (
    "Protejare față, vopsire cant litere și îndepărtare protecție după uscare"
)

DIRECT_MOUNT_DELIVERY_TYPES = frozenset({"delivery_install"})
DIRECT_MOUNT_INSTALLATION_MODES = frozenset(
    {
        "direct",
        "direct_mount",
        "field_installation",
        "field_install",
        "onsite",
        "on_site",
        "montaj_direct",
    }
)
DIRECT_MOUNT_BOOLEAN_KEYS = (
    "requires_installation",
    "field_installation",
    "requires_field_installation",
    "is_direct_mount",
    "direct_mount",
)

ALWAYS_INCLUDED_PROCESS_IDS = frozenset(
    {
        "vector_prep",
        "face_cnc_cut",
        "side_forming",
        "return_face_bonding",
        "back_cut",
        "assembly_letters",
        "qc_letters",
    }
)


def _normalize_process_id(task: Mapping[str, Any]) -> str:
    return str(task.get("process_id") or "").strip().lower()


def _snapshot_product_id(snapshot: Mapping[str, Any] | None) -> str:
    if not isinstance(snapshot, dict):
        return ""
    pd = snapshot.get("product_definition")
    if isinstance(pd, dict):
        return str(pd.get("product_id") or "").strip()
    return ""


def _merged_context(
    quote_input: Mapping[str, Any] | None,
    product_spec: Mapping[str, Any] | None,
) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(product_spec, dict):
        merged.update(product_spec)
    if isinstance(quote_input, dict):
        merged.update(quote_input)
    return merged


def _has_mounting_template_signal(
    quote_input: Mapping[str, Any] | None,
    product_spec: Mapping[str, Any] | None,
) -> bool:
    for source in (quote_input, product_spec):
        if not isinstance(source, dict):
            continue
        for key in (
            "mounting_template_enabled",
            "mounting_template_material_type",
            "mounting_template_area_m2",
            "mounting_system",
        ):
            if source.get(key) is not None:
                return True
    return False


def should_include_illumination_in_plan(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> bool:
    """Plan generation policy — omit LED/cabling unless illumination is explicitly enabled."""
    ctx = _merged_context(quote_input, product_spec)
    illum = str(ctx.get("illumination_type") or "").strip().lower()
    lighting = str(ctx.get("lighting_system_type") or "").strip().lower()

    if illum in ILLUMINATION_DISABLED_TYPES:
        return False
    if lighting == "none":
        return False
    if illum in ILLUMINATION_ENABLED_TYPES:
        return True
    if lighting in LIGHTING_SYSTEM_ENABLED_TYPES:
        return True
    return False


def _truthy_flag(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) != 0.0
    text = str(value or "").strip().lower()
    return text in {"true", "1", "yes", "on"}


def _extract_plan_delivery_context(snapshot: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(snapshot, dict):
        return {}
    ctx: dict[str, Any] = {}
    for key in (
        "delivery_type",
        "delivery_mode",
        "installation_mode",
        "mounting_mode",
        *DIRECT_MOUNT_BOOLEAN_KEYS,
    ):
        if snapshot.get(key) is not None:
            ctx[key] = snapshot.get(key)
    quote_snapshot = snapshot.get("quote_snapshot")
    if isinstance(quote_snapshot, dict):
        for key in ("delivery_type", "delivery_mode"):
            if quote_snapshot.get(key) is not None:
                ctx[key] = quote_snapshot.get(key)
    return ctx


def is_direct_mounting_in_plan(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
    snapshot: Mapping[str, Any] | None = None,
) -> bool:
    """True when the order goes to on-site direct mounting — packaging is omitted."""
    ctx = _merged_context(quote_input, product_spec)
    ctx.update(_extract_plan_delivery_context(snapshot))

    delivery = str(ctx.get("delivery_type") or ctx.get("delivery_mode") or "").strip().lower()
    if delivery in DIRECT_MOUNT_DELIVERY_TYPES:
        return True

    install_mode = str(
        ctx.get("installation_mode") or ctx.get("mounting_mode") or ""
    ).strip().lower()
    if install_mode in DIRECT_MOUNT_INSTALLATION_MODES:
        return True

    for key in DIRECT_MOUNT_BOOLEAN_KEYS:
        if _truthy_flag(ctx.get(key)):
            return True

    return False


def should_include_packaging_in_plan(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
    snapshot: Mapping[str, Any] | None = None,
) -> bool:
    """Packaging omitted for direct on-site mounting; default include for compatibility."""
    if is_direct_mounting_in_plan(quote_input, product_spec=product_spec, snapshot=snapshot):
        return False
    return True


def apply_volumetric_qc_taxonomy_to_plan_tasks(tasks: List[Any]) -> List[Any]:
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        if _normalize_process_id(entry) != QC_PROCESS_ID:
            continue
        entry["display_name"] = QC_DISPLAY_NAME
        entry["name"] = QC_DISPLAY_NAME
        entry["internal_only"] = True
        entry["instructions"] = QC_INSTRUCTIONS
    return tasks


def should_include_mounting_template_cnc_in_plan(
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> bool:
    if not _has_mounting_template_signal(quote_input, product_spec):
        return False
    ctx = _merged_context(quote_input, product_spec)
    if not normalize_mounting_template_enabled(
        ctx.get("mounting_template_enabled"),
        mounting_system=ctx.get("mounting_system"),
    ):
        return False
    return normalize_mounting_template_material_type(ctx) == "forex"


def should_include_volumetric_plan_task(
    process_id: str,
    quote_input: Mapping[str, Any] | None,
    *,
    product_spec: Mapping[str, Any] | None = None,
    snapshot: Mapping[str, Any] | None = None,
) -> bool:
    pid = str(process_id or "").strip().lower()
    if pid in ALWAYS_INCLUDED_PROCESS_IDS:
        return True
    if pid == PACKAGING_PROCESS_ID:
        return should_include_packaging_in_plan(
            quote_input,
            product_spec=product_spec,
            snapshot=snapshot,
        )
    if pid == FACE_VINYL_PROCESS_ID:
        return has_face_vinyl_application(quote_input, product_spec=product_spec)
    if pid == RETURN_VINYL_PROCESS_ID:
        return has_return_vinyl_application(quote_input, product_spec=product_spec)
    if pid in ILLUMINATION_PROCESS_IDS:
        return should_include_illumination_in_plan(quote_input, product_spec=product_spec)
    if pid == MOUNTING_TEMPLATE_CNC_PROCESS_ID:
        return should_include_mounting_template_cnc_in_plan(quote_input, product_spec=product_spec)
    if pid == PAINTING_PROCESS_ID:
        return is_cant_ral_paint_enabled(quote_input or {}, product_spec=product_spec)
    return True


def filter_volumetric_conditional_plan_tasks(
    tasks: List[Any],
    *,
    quote_input: Mapping[str, Any] | None,
    product_spec: Mapping[str, Any] | None = None,
    snapshot: Mapping[str, Any] | None = None,
) -> Tuple[List[Any], List[str]]:
    if not isinstance(tasks, list):
        return tasks, []

    removed: List[str] = []
    kept: List[Any] = []
    for entry in tasks:
        if not isinstance(entry, dict):
            kept.append(entry)
            continue
        pid = _normalize_process_id(entry)
        if pid and not should_include_volumetric_plan_task(
            pid,
            quote_input,
            product_spec=product_spec,
            snapshot=snapshot,
        ):
            removed.append(pid)
            continue
        kept.append(entry)
    return kept, removed


def resequence_plan_task_ids(tasks: List[Any]) -> Tuple[List[Any], Dict[str, str]]:
    id_map: Dict[str, str] = {}
    seq = 0
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        old_id = str(entry.get("task_id") or "").strip()
        seq += 1
        new_id = f"T-{seq:03d}"
        if old_id:
            id_map[old_id] = new_id
        entry["task_id"] = new_id

    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        raw_deps = entry.get("depends_on_task_ids")
        if not isinstance(raw_deps, list):
            continue
        remapped: List[str] = []
        for dep in raw_deps:
            dep_id = str(dep or "").strip()
            if not dep_id:
                continue
            mapped = id_map.get(dep_id, dep_id)
            if mapped not in remapped:
                remapped.append(mapped)
        entry["depends_on_task_ids"] = remapped
    return tasks, id_map


def prune_orphan_plan_dependencies(tasks: List[Any]) -> List[Any]:
    valid_ids = {
        str(entry.get("task_id") or "").strip()
        for entry in tasks
        if isinstance(entry, dict) and str(entry.get("task_id") or "").strip()
    }
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        raw_deps = entry.get("depends_on_task_ids")
        if not isinstance(raw_deps, list):
            continue
        entry["depends_on_task_ids"] = [
            dep_id
            for dep in raw_deps
            if (dep_id := str(dep or "").strip()) and dep_id in valid_ids
        ]
    return tasks


def apply_dynamic_volumetric_assembly_dependencies(tasks: List[Any]) -> List[Any]:
    process_index: Dict[str, str] = {}
    assembly_row: MutableMapping[str, Any] | None = None
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        pid = _normalize_process_id(entry)
        task_id = str(entry.get("task_id") or "").strip()
        if pid and task_id and pid not in process_index:
            process_index[pid] = task_id
        if pid == ASSEMBLY_PROCESS_ID:
            assembly_row = entry

    if assembly_row is None:
        return tasks

    deps: List[str] = []
    for pid in ("return_face_bonding", "back_cut"):
        task_id = process_index.get(pid)
        if task_id and task_id not in deps:
            deps.append(task_id)
    for pid in ("led_install_letters", "electrical_letters"):
        task_id = process_index.get(pid)
        if task_id and task_id not in deps:
            deps.append(task_id)

    assembly_row["depends_on_task_ids"] = deps
    assembly_row["dependency_mode"] = "all_finished"
    assembly_row["dependency_reason"] = (
        "Asamblarea depinde de subansamblele pregătite disponibile în plan."
    )
    return tasks


def ensure_face_vinyl_plan_task_when_required(
    tasks: List[Any],
    *,
    quote_input: Mapping[str, Any] | None,
    product_spec: Mapping[str, Any] | None = None,
    snapshot: Mapping[str, Any] | None = None,
) -> Tuple[List[Any], str]:
    """Inject vinyl_application when face vinyl is explicit but plan skipped 0-min process."""
    if not has_face_vinyl_application(quote_input, product_spec=product_spec):
        return tasks, "not_applicable"

    for entry in tasks:
        if isinstance(entry, dict) and _normalize_process_id(entry) == FACE_VINYL_PROCESS_ID:
            return tasks, "present"

    from services.volumetric_execution_dispatch import VOLUMETRIC_PRICED_OP_SCHEDULING_MINUTES

    minutes = float(VOLUMETRIC_PRICED_OP_SCHEDULING_MINUTES.get(FACE_VINYL_PROCESS_ID, 20.0))
    handoff: dict[str, Any] = {}
    if isinstance(snapshot, dict):
        raw = snapshot.get("face_vinyl_handoff")
        if isinstance(raw, dict):
            handoff = raw

    injected: dict[str, Any] = {
        "task_id": "T-INJ",
        "process_id": FACE_VINYL_PROCESS_ID,
        "process_type": "vinyl_application",
        "display_name": FACE_VINYL_DISPLAY_NAME,
        "name": FACE_VINYL_DISPLAY_NAME,
        "estimated_time_minutes": minutes,
        "quantity": 1,
        "machine_type": "",
        "layer_id": "layer_1",
        "face_vinyl_injected": True,
    }
    metadata = handoff.get("face_vinyl_metadata")
    if isinstance(metadata, dict):
        injected["face_vinyl_metadata"] = metadata

    insert_idx = _face_vinyl_insert_index(tasks)

    updated = list(tasks)
    updated.insert(insert_idx, injected)
    return updated, "injected"


def _face_vinyl_insert_index(tasks: List[Any]) -> int:
    """Place face vinyl after assembly and optional return painting — not after CNC face cut."""
    anchor_pid = PAINTING_PROCESS_ID
    for entry in tasks:
        if isinstance(entry, dict) and _normalize_process_id(entry) == PAINTING_PROCESS_ID:
            anchor_pid = PAINTING_PROCESS_ID
            break
    else:
        anchor_pid = ASSEMBLY_PROCESS_ID

    insert_idx = len(tasks)
    for idx, entry in enumerate(tasks):
        if isinstance(entry, dict) and _normalize_process_id(entry) == anchor_pid:
            insert_idx = idx + 1
            break
    return insert_idx


def reposition_face_vinyl_after_assembly(tasks: List[Any]) -> List[Any]:
    """Move vinyl_application row to post-assembly slot when plan order is stale."""
    return _reposition_process_after_anchor(
        tasks,
        process_id=FACE_VINYL_PROCESS_ID,
        anchor_pid=PAINTING_PROCESS_ID,
        fallback_anchor_pid=ASSEMBLY_PROCESS_ID,
    )


def reposition_painting_after_assembly(tasks: List[Any]) -> List[Any]:
    """Move painting row after assembly when template seed kept pre-assembly order."""
    return _reposition_process_after_anchor(
        tasks,
        process_id=PAINTING_PROCESS_ID,
        anchor_pid=ASSEMBLY_PROCESS_ID,
        fallback_anchor_pid=ASSEMBLY_PROCESS_ID,
    )


def _reposition_process_after_anchor(
    tasks: List[Any],
    *,
    process_id: str,
    anchor_pid: str,
    fallback_anchor_pid: str,
) -> List[Any]:
    row_idx = -1
    row: dict[str, Any] | None = None
    for idx, entry in enumerate(tasks):
        if isinstance(entry, dict) and _normalize_process_id(entry) == process_id:
            row_idx = idx
            row = dict(entry)
            break
    if row is None or row_idx < 0:
        return tasks

    without = [entry for idx, entry in enumerate(tasks) if idx != row_idx]
    insert_anchor = fallback_anchor_pid
    for entry in without:
        if isinstance(entry, dict) and _normalize_process_id(entry) == anchor_pid:
            insert_anchor = anchor_pid
            break

    insert_idx = len(without)
    for idx, entry in enumerate(without):
        if isinstance(entry, dict) and _normalize_process_id(entry) == insert_anchor:
            insert_idx = idx + 1
            break

    updated = list(without)
    updated.insert(insert_idx, row)
    return updated


def ensure_return_vinyl_plan_task_when_required(
    tasks: List[Any],
    *,
    quote_input: Mapping[str, Any] | None,
    product_spec: Mapping[str, Any] | None = None,
) -> Tuple[List[Any], str]:
    """Inject return_vinyl_application before side_forming when cant vinyl is selected."""
    if not has_return_vinyl_application(quote_input, product_spec=product_spec):
        return tasks, "not_applicable"

    for entry in tasks:
        if isinstance(entry, dict) and _normalize_process_id(entry) == RETURN_VINYL_PROCESS_ID:
            return tasks, "present"

    from services.volumetric_execution_dispatch import VOLUMETRIC_PRICED_OP_SCHEDULING_MINUTES

    minutes = float(VOLUMETRIC_PRICED_OP_SCHEDULING_MINUTES.get(RETURN_VINYL_PROCESS_ID, 20.0))
    injected: dict[str, Any] = {
        "task_id": "T-INJ-RV",
        "process_id": RETURN_VINYL_PROCESS_ID,
        "process_type": "vinyl_application",
        "display_name": RETURN_VINYL_DISPLAY_NAME,
        "name": RETURN_VINYL_DISPLAY_NAME,
        "estimated_time_minutes": minutes,
        "quantity": 1,
        "machine_type": "",
        "layer_id": "layer_1",
        "return_vinyl_injected": True,
    }

    insert_idx = len(tasks)
    for idx, entry in enumerate(tasks):
        if isinstance(entry, dict) and _normalize_process_id(entry) == "side_forming":
            insert_idx = idx
            break

    updated = list(tasks)
    updated.insert(insert_idx, injected)
    return updated, "injected"


def apply_return_vinyl_taxonomy_to_plan_tasks(
    tasks: List[Any],
    *,
    quote_input: Mapping[str, Any] | None,
    product_spec: Mapping[str, Any] | None = None,
    set_owner_instructions: bool = False,
) -> Tuple[List[Any], str]:
    if not isinstance(tasks, list):
        return tasks, "invalid_tasks"

    applicable = has_return_vinyl_application(quote_input, product_spec=product_spec)
    before = json.dumps(tasks, sort_keys=True, ensure_ascii=False)

    if not applicable:
        filtered = [
            entry
            for entry in tasks
            if not (isinstance(entry, dict) and _normalize_process_id(entry) == RETURN_VINYL_PROCESS_ID)
        ]
        after = json.dumps(filtered, sort_keys=True, ensure_ascii=False)
        if before == after:
            return filtered, "unchanged"
        return filtered, "filtered_no_return_vinyl"

    updated: List[Any] = []
    for entry in tasks:
        if not isinstance(entry, dict):
            updated.append(entry)
            continue
        row = dict(entry)
        if _normalize_process_id(row) != RETURN_VINYL_PROCESS_ID:
            updated.append(row)
            continue
        row["display_name"] = RETURN_VINYL_DISPLAY_NAME
        row["name"] = RETURN_VINYL_DISPLAY_NAME
        if set_owner_instructions:
            instructions = build_return_vinyl_task_instructions(
                quote_input,
                product_spec=product_spec,
            )
            if instructions:
                row["instructions"] = instructions
        updated.append(row)

    after = json.dumps(updated, sort_keys=True, ensure_ascii=False)
    if before == after:
        return updated, "unchanged"
    return updated, "updated"


def apply_dynamic_volumetric_vinyl_plan_dependencies(tasks: List[Any]) -> List[Any]:
    process_index: Dict[str, str] = {}
    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        pid = _normalize_process_id(entry)
        task_id = str(entry.get("task_id") or "").strip()
        if pid and task_id and pid not in process_index:
            process_index[pid] = task_id

    def _append_dep(row: MutableMapping[str, Any], process_id: str) -> None:
        dep_task = process_index.get(process_id)
        if not dep_task:
            return
        deps = [str(x).strip() for x in (row.get("depends_on_task_ids") or []) if str(x).strip()]
        if dep_task not in deps:
            deps.append(dep_task)
        row["depends_on_task_ids"] = deps

    def _strip_dep(row: MutableMapping[str, Any], process_id: str) -> None:
        dep_task = process_index.get(process_id)
        if not dep_task:
            return
        deps = [str(x).strip() for x in (row.get("depends_on_task_ids") or []) if str(x).strip()]
        row["depends_on_task_ids"] = [dep for dep in deps if dep != dep_task]

    face_vinyl_anchor = (
        PAINTING_PROCESS_ID
        if PAINTING_PROCESS_ID in process_index
        else ASSEMBLY_PROCESS_ID
    )

    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        pid = _normalize_process_id(entry)
        if pid == RETURN_VINYL_PROCESS_ID:
            _append_dep(entry, "vector_prep")
        elif pid == "side_forming":
            if RETURN_VINYL_PROCESS_ID in process_index:
                _append_dep(entry, RETURN_VINYL_PROCESS_ID)
        elif pid == PAINTING_PROCESS_ID:
            _append_dep(entry, ASSEMBLY_PROCESS_ID)
            entry["display_name"] = PAINTING_DISPLAY_NAME
            entry["name"] = PAINTING_DISPLAY_NAME
        elif pid == FACE_VINYL_PROCESS_ID:
            _strip_dep(entry, "face_cnc_cut")
            _append_dep(entry, face_vinyl_anchor)
            entry["dependency_reason"] = (
                "Colantarea finală a fețelor se face după asamblare"
                + (" și finisajul cantului vopsit." if face_vinyl_anchor == PAINTING_PROCESS_ID else ".")
            )
        elif pid == "return_face_bonding":
            _strip_dep(entry, FACE_VINYL_PROCESS_ID)
            if "side_forming" in process_index:
                _append_dep(entry, "side_forming")
            if "face_cnc_cut" in process_index:
                _append_dep(entry, "face_cnc_cut")
        elif pid == QC_PROCESS_ID and FACE_VINYL_PROCESS_ID in process_index:
            _append_dep(entry, FACE_VINYL_PROCESS_ID)
        elif pid == QC_PROCESS_ID and PAINTING_PROCESS_ID in process_index:
            _append_dep(entry, PAINTING_PROCESS_ID)

    return tasks


def apply_volumetric_packaging_taxonomy_to_plan_tasks(
    tasks: List[Any],
    *,
    quote_input: Mapping[str, Any] | None,
    product_spec: Mapping[str, Any] | None = None,
) -> List[Any]:
    """Align final packaging label/instructions; mention PSU in colet when illuminated."""
    if not isinstance(tasks, list):
        return tasks

    illuminated = should_include_illumination_in_plan(quote_input, product_spec=product_spec)
    psu_watts = None
    if isinstance(quote_input, dict):
        raw_psu = quote_input.get("selected_psu_watts") or quote_input.get("psu_watts")
        try:
            if raw_psu is not None:
                psu_watts = int(float(raw_psu))
        except (TypeError, ValueError):
            psu_watts = None

    instructions = PACKAGING_INSTRUCTIONS_BASE
    if illuminated:
        if psu_watts:
            instructions += f" Include sursele calculate ({psu_watts} W) în colet."
        else:
            instructions += " Include sursele calculate în colet."

    for entry in tasks:
        if not isinstance(entry, dict):
            continue
        if _normalize_process_id(entry) != PACKAGING_PROCESS_ID:
            continue
        entry["display_name"] = PACKAGING_DISPLAY_NAME
        entry["name"] = PACKAGING_DISPLAY_NAME
        entry["instructions"] = instructions
    return tasks


def apply_volumetric_conditional_plan_from_snapshot(
    tasks: List[Any],
    snapshot: Mapping[str, Any] | None,
    *,
    set_face_vinyl_instructions: bool = False,
) -> Tuple[List[Any], dict[str, Any]]:
    """Filter/enrich volumetric plan tasks; resequence IDs; return summary metadata."""
    summary: dict[str, Any] = {
        "applied": False,
        "removed_process_ids": [],
        "face_vinyl_action": "unchanged",
        "return_vinyl_action": "unchanged",
        "resequenced": False,
    }

    product_id = _snapshot_product_id(snapshot)
    if not is_volumetric_template_code(product_id):
        return tasks, summary

    quote_input = resolve_volumetric_operational_quote_input(
        extract_quote_input_from_snapshot(snapshot or {}),
        product_spec=extract_product_spec_from_snapshot(snapshot or {}),
    )
    product_spec = extract_product_spec_from_snapshot(snapshot or {})

    before = json.dumps(tasks, sort_keys=True, ensure_ascii=False)
    filtered, removed = filter_volumetric_conditional_plan_tasks(
        tasks,
        quote_input=quote_input,
        product_spec=product_spec,
        snapshot=snapshot,
    )
    summary["removed_process_ids"] = removed

    if FACE_VINYL_PROCESS_ID in removed:
        summary["face_vinyl_action"] = "filtered_no_face_vinyl"
    if RETURN_VINYL_PROCESS_ID in removed:
        summary["return_vinyl_action"] = "filtered_no_return_vinyl"

    filtered, return_inject_action = ensure_return_vinyl_plan_task_when_required(
        filtered,
        quote_input=quote_input,
        product_spec=product_spec,
    )
    if return_inject_action == "injected":
        summary["return_vinyl_action"] = "injected_missing_task"

    filtered, inject_action = ensure_face_vinyl_plan_task_when_required(
        filtered,
        quote_input=quote_input,
        product_spec=product_spec,
        snapshot=snapshot,
    )
    if inject_action == "injected":
        summary["face_vinyl_action"] = "injected_missing_task"

    filtered, face_action = apply_face_vinyl_taxonomy_to_plan_tasks(
        filtered,
        quote_input=quote_input,
        product_spec=product_spec,
        set_owner_instructions=set_face_vinyl_instructions,
    )
    if face_action != "unchanged":
        summary["face_vinyl_action"] = face_action

    filtered, return_action = apply_return_vinyl_taxonomy_to_plan_tasks(
        filtered,
        quote_input=quote_input,
        product_spec=product_spec,
        set_owner_instructions=set_face_vinyl_instructions,
    )
    if return_action != "unchanged":
        summary["return_vinyl_action"] = return_action

    filtered = apply_volumetric_qc_taxonomy_to_plan_tasks(filtered)
    filtered = reposition_painting_after_assembly(filtered)
    filtered = reposition_face_vinyl_after_assembly(filtered)
    filtered = apply_volumetric_packaging_taxonomy_to_plan_tasks(
        filtered,
        quote_input=quote_input,
        product_spec=product_spec,
    )

    filtered, _id_map = resequence_plan_task_ids(filtered)
    summary["resequenced"] = True

    after = json.dumps(filtered, sort_keys=True, ensure_ascii=False)
    summary["applied"] = before != after
    summary["total_estimated_time_minutes"] = recalculate_plan_total_minutes(filtered)
    return filtered, summary


def finalize_volumetric_plan_dependencies(tasks: List[Any]) -> List[Any]:
    from services.task_dependency_rules_service import apply_task_dependency_rules_to_plan_tasks

    updated = reposition_painting_after_assembly(tasks)
    updated = reposition_face_vinyl_after_assembly(updated)
    updated, _warnings, _action = apply_task_dependency_rules_to_plan_tasks(updated)
    updated = apply_dynamic_volumetric_vinyl_plan_dependencies(updated)
    updated = apply_dynamic_volumetric_assembly_dependencies(updated)
    updated = prune_orphan_plan_dependencies(updated)
    return updated
