"""Capacity Batch 17 Track B / Batch 18 OR-09 — display-only ops-graph read clarity.

Enriches operational task payloads with honesty metadata for operator/admin RO
review. NEVER invents minutes, workcenter, machine_code, unit, deps, sessions,
or actuals. NEVER mutates persisted tasks_json. NEVER computes Pricing/CostEngine
values; OR-09 only softens commercial unit phrasing embedded in template labels.
"""

from __future__ import annotations

import re
from typing import Any, Literal

NullClassification = Literal[
    "present",
    "unknown",
    "not_required",
    "owner_accepted_risk",
    "blocked_pending_owner_truth",
]

FIELD_HONESTY_VERSION = "ops_graph_read_clarity/v1"

# Owner-locked residuals (Batch 12 / CAP-004 / CAP-012 / OD1) — classify only.
_OWNER_ACCEPTED_MACHINE_CODE = "CAP-012"
_OWNER_ACCEPTED_WORKCENTER = "F7_OD1"
_OWNER_ACCEPTED_MINUTES = "CAP-004"
_OWNER_ACCEPTED_EMPLOYEE = "HR_OUT_OF_STAGE"
_OWNER_UPSTREAM_TEMPLATE_LABEL = "PRODUCT_SYSTEM_TEMPLATE_LABEL"

# Commercial unit parentheticals leaked into Product System template display_name
# values (e.g. "(EUR/ml serviciu)"). Strip for Capacity/ops-graph display only —
# do not invent rates, units, or hide the process name.
_COMMERCIAL_EUR_ML_PAREN = re.compile(
    r"\s*\([^)]*EUR\s*/\s*ml[^)]*\)",
    re.IGNORECASE,
)


def _is_blank(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def _short_task_code(task: dict[str, Any]) -> str:
    for key in ("technical_name", "source_task_rule_code", "source_operation_code"):
        raw = task.get(key)
        if not _is_blank(raw):
            return str(raw).strip()
    task_id = str(task.get("task_id") or "").strip()
    if ":" in task_id:
        return task_id.rsplit(":", 1)[-1]
    return task_id or "—"


def _deterministic_task_key(task: dict[str, Any]) -> Any:
    key = task.get("deterministic_task_key")
    if not _is_blank(key):
        return key
    frozen = task.get("frozen_identity")
    if isinstance(frozen, dict):
        frozen_key = frozen.get("deterministic_task_key")
        if not _is_blank(frozen_key):
            return frozen_key
    return None


def _field(
    *,
    value: Any,
    classification: NullClassification,
    role: str,
    note: str | None = None,
    owner_lock: str | None = None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "value": value,
        "classification": classification,
        "role": role,
    }
    if note is not None:
        out["note"] = note
    if owner_lock is not None:
        out["owner_lock"] = owner_lock
    return out


def _classify_machine_code(task: dict[str, Any]) -> dict[str, Any]:
    raw = task.get("machine_code")
    if not _is_blank(raw):
        return _field(
            value=str(raw).strip(),
            classification="present",
            role="assigned_machine_instance",
            note="Concrete machine_code assignment is present.",
        )
    return _field(
        value=None,
        classification="owner_accepted_risk",
        role="assigned_machine_instance",
        note=(
            "machine_code absent — not an assigned utilaj. "
            "Do not treat machine_type as machine_code."
        ),
        owner_lock=_OWNER_ACCEPTED_MACHINE_CODE,
    )


def _classify_machine_type(task: dict[str, Any]) -> dict[str, Any]:
    raw = task.get("machine_type")
    if _is_blank(raw):
        return _field(
            value=None,
            classification="unknown",
            role="planning_requirement_class",
            note="machine_type/capability class absent on operational_task.",
        )
    return _field(
        value=str(raw).strip(),
        classification="present",
        role="planning_requirement_class",
        note=(
            "Planning capability / requirement class from materialize "
            "(often workcenter-class code). NOT an assigned machine_code."
        ),
    )


def _classify_workcenter(task: dict[str, Any]) -> dict[str, Any]:
    raw = task.get("workcenter")
    if not _is_blank(raw):
        return _field(
            value=str(raw).strip(),
            classification="present",
            role="workcenter",
            note="Explicit workcenter field on operational_task.",
        )
    # Field absent/null — OD1. machine_type may still hold a WC-class hint but
    # must not be copied into workcenter (no invent).
    machine_type = task.get("machine_type")
    note = "workcenter field null (OD1 owner-accepted)."
    if not _is_blank(machine_type):
        note += (
            f" Planning requirement class is separately present as machine_type="
            f"{str(machine_type).strip()} — not promoted to workcenter."
        )
    return _field(
        value=None,
        classification="owner_accepted_risk",
        role="workcenter",
        note=note,
        owner_lock=_OWNER_ACCEPTED_WORKCENTER,
    )


def _classify_estimated_minutes(task: dict[str, Any]) -> dict[str, Any]:
    raw = task.get("estimated_time_minutes")
    warnings = [str(w) for w in (task.get("warnings") or []) if w]
    source = task.get("planning_minutes_source")
    if raw is not None:
        return _field(
            value=raw,
            classification="present",
            role="estimated_time_minutes",
            note=(
                "Planning minutes present from source "
                f"{source or 'unspecified'} — not ExecutionActuals."
            ),
        )
    if any("PLANNING_MINUTES" in w for w in warnings) or _is_blank(source):
        return _field(
            value=None,
            classification="owner_accepted_risk",
            role="estimated_time_minutes",
            note=(
                "estimated_time_minutes null with planning-source gap; "
                "do not invent 0. Not blocked for graph structure."
            ),
            owner_lock=_OWNER_ACCEPTED_MINUTES,
        )
    return _field(
        value=None,
        classification="unknown",
        role="estimated_time_minutes",
        note="estimated_time_minutes null without classified planning warning.",
    )


def _classify_planning_minutes_source(task: dict[str, Any]) -> dict[str, Any]:
    raw = task.get("planning_minutes_source")
    if not _is_blank(raw):
        return _field(
            value=str(raw).strip(),
            classification="present",
            role="planning_minutes_source",
        )
    return _field(
        value=None,
        classification="owner_accepted_risk",
        role="planning_minutes_source",
        note="planning_minutes_source null (paired with CAP-004 minutes honesty).",
        owner_lock=_OWNER_ACCEPTED_MINUTES,
    )


def _classify_quantity(task: dict[str, Any]) -> dict[str, Any]:
    if "quantity" not in task:
        return _field(
            value=None,
            classification="unknown",
            role="quantity",
            note="quantity key absent on operational_task.",
        )
    return _field(
        value=task.get("quantity"),
        classification="present",
        role="quantity",
        note="Plan-task quantity count only — not inventable commercial qty.",
    )


def _classify_unit(task: dict[str, Any]) -> dict[str, Any]:
    if "unit" not in task or _is_blank(task.get("unit")):
        return _field(
            value=None,
            classification="unknown",
            role="unit",
            note=(
                "unit absent on operational_task (V-13). "
                "Do not invent piece/ml/m2; quantity is dimensionless plan count."
            ),
        )
    return _field(
        value=str(task.get("unit")).strip(),
        classification="present",
        role="unit",
    )


def _classify_employee(task: dict[str, Any]) -> dict[str, Any]:
    raw = task.get("assigned_employee_id")
    if raw is not None and raw != "":
        return _field(
            value=raw,
            classification="present",
            role="assigned_employee_id",
        )
    return _field(
        value=None,
        classification="owner_accepted_risk",
        role="assigned_employee_id",
        note="No employee assignment at this stage (not Employee Mobile).",
        owner_lock=_OWNER_ACCEPTED_EMPLOYEE,
    )


def _classify_lifecycle(task: dict[str, Any]) -> dict[str, Any]:
    """Surface operational_status honestly — plan lifecycle, not reality actuals."""
    raw = task.get("operational_status")
    if _is_blank(raw):
        return {
            "value": None,
            "classification": "unknown",
            "role": "plan_lifecycle_status",
            "display_label": "status_unknown",
            "note": (
                "operational_status absent. Do not invent not_started/done "
                "from missing ExecutionActuals."
            ),
            "source_field": "operational_status",
        }
    status = str(raw).strip()
    if status == "pending":
        display = "materialized_pending_execution"
        note = (
            "Plan operational_status=pending — task is materialized in envelope; "
            "not an ExecutionActuals / session state. No start/stop observed."
        )
    else:
        display = status
        note = (
            f"Plan operational_status={status} from envelope — "
            "not inferred from reality/sessions."
        )
    return {
        "value": status,
        "classification": "present",
        "role": "plan_lifecycle_status",
        "display_label": display,
        "note": note,
        "source_field": "operational_status",
    }


def _warning_buckets(task: dict[str, Any]) -> dict[str, list[str]]:
    """Split raw warnings vs accepted-gap codes for quieter UI (OR-04)."""
    raw_warnings = [str(w) for w in (task.get("warnings") or []) if w]
    accepted_gap_codes: list[str] = []
    active_warnings: list[str] = []

    for w in raw_warnings:
        if "PLANNING_MINUTES" in w:
            if _OWNER_ACCEPTED_MINUTES not in accepted_gap_codes:
                accepted_gap_codes.append(_OWNER_ACCEPTED_MINUTES)
            # Keep code once under accepted; omit from noisy active list.
            continue
        active_warnings.append(w)

    if _is_blank(task.get("machine_code")):
        accepted_gap_codes.append(_OWNER_ACCEPTED_MACHINE_CODE)
    if _is_blank(task.get("workcenter")):
        accepted_gap_codes.append(_OWNER_ACCEPTED_WORKCENTER)
    if task.get("assigned_employee_id") is None or task.get("assigned_employee_id") == "":
        accepted_gap_codes.append(_OWNER_ACCEPTED_EMPLOYEE)

    # Dedupe preserving order
    seen: set[str] = set()
    accepted_deduped: list[str] = []
    for code in accepted_gap_codes:
        if code not in seen:
            seen.add(code)
            accepted_deduped.append(code)

    return {
        "raw_warnings": raw_warnings,
        "accepted_gap_codes": accepted_deduped,
        "active_warnings": active_warnings,
    }


def _sequence_plan_note(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    indices: list[int] = []
    for t in tasks:
        raw = t.get("sequence_index")
        if isinstance(raw, bool):
            continue
        if isinstance(raw, int):
            indices.append(raw)
        elif isinstance(raw, float) and raw.is_integer():
            indices.append(int(raw))
    indices = sorted(set(indices))
    gaps: list[int] = []
    if indices:
        for n in range(indices[0], indices[-1] + 1):
            if n not in indices:
                gaps.append(n)
    return {
        "observed_indices": indices,
        "gaps": gaps,
        "classification": "unknown" if gaps else "present",
        "note": (
            "sequence_index preserved from template/planning source; "
            "not remapped to dense 1..N. Gaps are display clarity only "
            "(V-07 / OR-03) — technical order + deps remain authoritative."
            if gaps
            else "sequence_index contiguous in observed range."
        ),
        "display_order_basis": "sequence_index then task_id; no invent densify",
    }


def _raw_task_label(task: dict[str, Any]) -> str | None:
    raw = task.get("display_name") or task.get("name")
    if _is_blank(raw):
        return None
    return str(raw).strip()


def _soften_commercial_eur_ml_label(raw_label: str) -> str:
    """Remove EUR/ml parentheticals from a template label for ops-graph display."""
    softened = _COMMERCIAL_EUR_ML_PAREN.sub("", raw_label)
    softened = re.sub(r"\s{2,}", " ", softened).strip(" -—\t")
    return softened or raw_label


def classify_ops_graph_label(raw_label: str | None) -> dict[str, Any]:
    """Classify template display_name for Capacity/ops-graph (OR-09 / V-15).

    Categories (exactly one primary artifact_kind):
    - process_label — ordinary process wording
    - misleading_commercial_unit_phrasing — EUR/ml (or similar) embedded in
      free-text template label; NOT pricing display, NOT capacity metadata,
      NOT the task catalog ``unit`` field (which remains independently classified)

    Softening strips commercial parentheticals for ops display only. Upstream
    Product System / seed rename remains an Owner decision.
    """
    if raw_label is None:
        return {
            "classification": "unknown",
            "artifact_kind": "missing_label",
            "role": "template_provenance_not_client_price_not_capacity_unit",
            "commercial_unit_phrasing_present": False,
            "softened_for_ops_graph": False,
            "ops_display_label": None,
            "note": "display_name/name absent — show —; do not invent a process title.",
        }

    has_commercial = bool(_COMMERCIAL_EUR_ML_PAREN.search(raw_label))
    if not has_commercial:
        return {
            "classification": "present",
            "artifact_kind": "process_label",
            "role": "template_provenance_not_client_price_not_capacity_unit",
            "commercial_unit_phrasing_present": False,
            "softened_for_ops_graph": False,
            "ops_display_label": raw_label,
            "note": "Process label from template/envelope provenance.",
        }

    ops_label = _soften_commercial_eur_ml_label(raw_label)
    return {
        "classification": "owner_accepted_risk",
        "artifact_kind": "misleading_commercial_unit_phrasing",
        "role": "template_provenance_not_client_price_not_capacity_unit",
        "commercial_unit_phrasing_present": True,
        "softened_for_ops_graph": ops_label != raw_label,
        "ops_display_label": ops_label,
        "owner_lock": _OWNER_UPSTREAM_TEMPLATE_LABEL,
        "note": (
            "OR-09: template display_name embeds commercial unit phrasing "
            "(EUR/ml). Not a Pricing surface, not Capacity metadata, not task.unit. "
            "Ops-graph shows process wording only; raw provenance retained in "
            "identity.label. Upstream Product System rename = Owner decision."
        ),
    }


def build_task_read_clarity(
    task: dict[str, Any],
    *,
    task_id_to_short: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build per-task honesty / identity clarity block (display-only)."""
    short = _short_task_code(task)
    dep_ids = [
        str(d).strip()
        for d in (task.get("depends_on_task_ids") or [])
        if str(d).strip()
    ]
    lookup = task_id_to_short or {}
    dep_shorts = [lookup.get(d, d.rsplit(":", 1)[-1] if ":" in d else d) for d in dep_ids]
    buckets = _warning_buckets(task)
    lifecycle = _classify_lifecycle(task)
    raw_label = _raw_task_label(task)
    label_clarity = classify_ops_graph_label(raw_label)

    return {
        "version": FIELD_HONESTY_VERSION,
        "identity": {
            "task_id": task.get("task_id"),
            "short_code": short,
            "label": raw_label,
            "ops_display_label": label_clarity.get("ops_display_label"),
            "label_clarity": {
                "classification": label_clarity["classification"],
                "artifact_kind": label_clarity["artifact_kind"],
                "role": label_clarity["role"],
                "commercial_unit_phrasing_present": label_clarity[
                    "commercial_unit_phrasing_present"
                ],
                "softened_for_ops_graph": label_clarity["softened_for_ops_graph"],
                "note": label_clarity.get("note"),
                **(
                    {"owner_lock": label_clarity["owner_lock"]}
                    if label_clarity.get("owner_lock")
                    else {}
                ),
            },
            "technical_name": task.get("technical_name"),
            "source_operation_code": task.get("source_operation_code"),
            "source_task_rule_code": task.get("source_task_rule_code"),
            "process_type": task.get("process_type"),
            "sequence_index": task.get("sequence_index"),
            "deterministic_task_key": _deterministic_task_key(task),
        },
        "lifecycle": lifecycle,
        "quantity": _classify_quantity(task),
        "unit": _classify_unit(task),
        "depends_on": {
            "task_ids": dep_ids,
            "short_codes": dep_shorts,
            "classification": "present" if dep_ids else "not_required",
            "note": (
                "Root task — empty depends_on is valid."
                if not dep_ids
                else "Dependency ids from envelope; short_codes use technical_name map."
            ),
        },
        "machine_code": _classify_machine_code(task),
        "machine_type": _classify_machine_type(task),
        "workcenter": _classify_workcenter(task),
        "estimated_time_minutes": _classify_estimated_minutes(task),
        "planning_minutes_source": _classify_planning_minutes_source(task),
        "assigned_employee_id": _classify_employee(task),
        "warnings": buckets,
        "display_hints": {
            "machine_column": "machine_type_as_requirement_class",
            "machine_code_column": "null_means_unassigned",
            "status_column": "lifecycle.display_label",
            "collapse_accepted_gaps": True,
            "do_not_coalesce_machine_code_from_machine_type": True,
            "prefer_ops_display_label": True,
            "label_column": (
                "ops_display_label_with_provenance_tooltip"
                if label_clarity["commercial_unit_phrasing_present"]
                else "template_provenance_label"
            ),
        },
    }


def enrich_operational_tasks_for_ops_graph(
    tasks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return shallow-copied tasks with read_clarity + plan-level summary.

    Original task fields are preserved unchanged (no invent / no overwrite).
    """
    short_map = {
        str(t.get("task_id")): _short_task_code(t)
        for t in tasks
        if t.get("task_id")
    }
    enriched: list[dict[str, Any]] = []
    for task in tasks:
        copy = dict(task)
        copy["read_clarity"] = build_task_read_clarity(task, task_id_to_short=short_map)
        enriched.append(copy)

    commercial_label_count = sum(
        1
        for row in enriched
        if (row.get("read_clarity") or {})
        .get("identity", {})
        .get("label_clarity", {})
        .get("commercial_unit_phrasing_present")
    )
    summary = {
        "version": FIELD_HONESTY_VERSION,
        "operational_tasks_count": len(enriched),
        "sequence": _sequence_plan_note(tasks),
        "null_policy": {
            "unknown": "Field absent or unclassified — show —; do not invent.",
            "not_required": "Empty is valid for this stage (e.g. root deps).",
            "owner_accepted_risk": "Locked Owner residual — warn, do not fill.",
            "blocked_pending_owner_truth": "Must not invent; wait for Owner truth.",
            "present": "Value from persisted operational_task / envelope.",
        },
        "identity_rules": {
            "machine_code": "Assigned utilaj instance only — never coalesce from machine_type.",
            "machine_type": "Planning requirement / capability class — not assignment.",
            "workcenter": "Only explicit workcenter field; OD1 null is owner-accepted.",
            "lifecycle": "Use operational_status via read_clarity.lifecycle — not reality.",
            "unit": "Absent → unknown; quantity alone is not a unit claim.",
            "label": (
                "Prefer identity.ops_display_label on Capacity/ops-graph. "
                "EUR/ml in template display_name is misleading commercial phrasing "
                "(OR-09) — not Pricing display, not Capacity metadata, not task.unit. "
                "Raw identity.label retained; upstream rename = Product System Owner."
            ),
        },
        "label_policy": {
            "commercial_unit_phrasing_task_count": commercial_label_count,
            "note": (
                "OR-09 display soften only — no Pricing/CostEngine, no invent unit, "
                "no hide of process name, no persist rewrite of display_name."
            ),
        },
        "counts_guard": {
            "note": "Enrichment is display-only; task count must equal input length.",
            "input_count": len(tasks),
            "output_count": len(enriched),
        },
    }
    return enriched, summary


def apply_ops_graph_read_clarity_to_plan_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Mutate a plan API payload dict in place with read-clarity enrichment."""
    tasks = payload.get("tasks")
    if not isinstance(tasks, list):
        payload["ops_graph_read_clarity"] = {
            "version": FIELD_HONESTY_VERSION,
            "operational_tasks_count": 0,
            "sequence": _sequence_plan_note([]),
            "counts_guard": {"input_count": 0, "output_count": 0},
        }
        return payload
    dict_tasks = [t for t in tasks if isinstance(t, dict)]
    enriched, summary = enrich_operational_tasks_for_ops_graph(dict_tasks)
    payload["tasks"] = enriched
    payload["ops_graph_read_clarity"] = summary
    return payload
