"""Read-only Product Truth promotion planner for runtime capture fields.

This planner does not write Product Truth. It evaluates the existing runtime
capture read model and payload evidence to separate eligible promotion entries
from blocked entries while preserving stable identity requirements.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from schemas.intake_v4 import IntakeV4LayerRoleSetup
from services.form_system_runtime_capture_read_model_service import (
    DEFAULT_TEMPLATE_CODE,
    build_form_system_runtime_capture_read_model,
)
from services.intake_v4_layer_role_service import selected_layer_refs_runtime_state


PLANNER_VERSION = "v1"


def _payload_to_dict(payload: Any) -> dict[str, Any] | None:
    if payload is None:
        return None
    if isinstance(payload, dict):
        return payload
    model_dump = getattr(payload, "model_dump", None)
    if callable(model_dump):
        return model_dump(mode="json")
    return None


def _downstream_write_intent() -> dict[str, bool]:
    return {
        "product_truth_write": False,
        "pricing_write": False,
        "quote_write": False,
        "order_write": False,
        "product_definition_write": False,
        "product_aggregate_write": False,
        "task_graph_write": False,
        "execution_runtime_write": False,
        "inventory_movement": False,
        "db_write": False,
    }


def _string(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _bool_or_none(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def _dedupe(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        if value and value not in deduped:
            deduped.append(value)
    return deduped


def _entry(
    *,
    field_key: str,
    runtime_source: str,
    product_truth_path: str,
    state: str,
    value_status: str,
    promotion_allowed: bool,
    reason: str,
    blockers: list[str],
    identity_key: str | None = None,
) -> dict[str, Any]:
    entry_key = field_key if not identity_key else f"{field_key}:{identity_key}"
    entry = {
        "entry_key": entry_key,
        "field_key": field_key,
        "runtime_source": runtime_source,
        "product_truth_path": product_truth_path,
        "state": state,
        "value_status": value_status,
        "promotion_allowed": promotion_allowed,
        "reason": reason,
        "blockers": _dedupe(blockers),
    }
    if identity_key is not None:
        entry["identity_key"] = identity_key
    return entry


def _blocker_summary(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for entry in entries:
        blockers = entry.get("blockers") or []
        if not blockers:
            continue
        summary.append(
            {
                "field_key": entry["field_key"],
                "identity_key": entry.get("identity_key"),
                "blockers": blockers,
                "state": entry["state"],
            }
        )
    return summary


def _classify_selected_layer_entries(
    field: dict[str, Any],
    payload_raw: dict[str, Any] | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    eligible: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    layer_role_setup = payload_raw.get("layer_role_setup") if isinstance(payload_raw, dict) else None
    setup_layers = layer_role_setup.get("layers") if isinstance(layer_role_setup, dict) and isinstance(layer_role_setup.get("layers"), list) else []
    confirmation_status = _string(layer_role_setup.get("confirmation_status")) if isinstance(layer_role_setup, dict) else None
    svg = payload_raw.get("svg") if isinstance(payload_raw, dict) and isinstance(payload_raw.get("svg"), dict) else {}
    persisted_refs = svg.get("selected_layer_refs") if isinstance(svg.get("selected_layer_refs"), list) else []
    base_blockers = [str(value) for value in (field.get("blockers") or []) if str(value).strip()]

    if field.get("state") == "confirmed" and persisted_refs:
        seen_layer_ids: set[str] = set()
        for raw_ref in persisted_refs:
            if not isinstance(raw_ref, dict):
                blocked.append(
                    _entry(
                        field_key=field["field_key"],
                        runtime_source=field["runtime_source"],
                        product_truth_path=field["product_truth_path"],
                        state="blocked",
                        value_status="invalid_ref_shape",
                        promotion_allowed=False,
                        reason="Selected layer ref entry is not a valid object, so stable identity cannot be promoted.",
                        blockers=["SELECTED_LAYER_REF_INVALID"],
                    )
                )
                continue
            layer_id = _string(raw_ref.get("layer_id"))
            if not layer_id:
                blocked.append(
                    _entry(
                        field_key=field["field_key"],
                        runtime_source=field["runtime_source"],
                        product_truth_path=field["product_truth_path"],
                        state="blocked",
                        value_status="missing_identity",
                        promotion_allowed=False,
                        reason="Selected layer refs require a stable layer_id; array position or UI label is not canonical identity.",
                        blockers=["SELECTED_LAYER_ID_MISSING"],
                    )
                )
                continue
            if layer_id in seen_layer_ids:
                blocked.append(
                    _entry(
                        field_key=field["field_key"],
                        runtime_source=field["runtime_source"],
                        product_truth_path=field["product_truth_path"],
                        state="blocked",
                        value_status="ambiguous_identity",
                        promotion_allowed=False,
                        reason="Selected layer refs require unique stable layer_id values; duplicate identity is ambiguous.",
                        blockers=["SELECTED_LAYER_REFS_AMBIGUOUS"],
                        identity_key=f"layer_id:{layer_id}",
                    )
                )
                continue
            seen_layer_ids.add(layer_id)
            if raw_ref.get("confirmed") is not True:
                blocked.append(
                    _entry(
                        field_key=field["field_key"],
                        runtime_source=field["runtime_source"],
                        product_truth_path=field["product_truth_path"],
                        state="hydrated",
                        value_status="present_unconfirmed",
                        promotion_allowed=False,
                        reason="Selected layer ref exists but is not explicitly confirmed, so it cannot enter Product Truth.",
                        blockers=["SELECTED_LAYER_REFS_UNCONFIRMED"],
                        identity_key=f"layer_id:{layer_id}",
                    )
                )
                continue
            eligible.append(
                _entry(
                    field_key=field["field_key"],
                    runtime_source=field["runtime_source"],
                    product_truth_path=field["product_truth_path"],
                    state="confirmed",
                    value_status="explicit_confirmed",
                    promotion_allowed=True,
                    reason="Selected layer ref is confirmed and carries a stable layer_id, so it is eligible for Product Truth promotion.",
                    blockers=[],
                    identity_key=f"layer_id:{layer_id}",
                )
            )
        return eligible, blocked

    if not persisted_refs and isinstance(layer_role_setup, dict):
        try:
            setup = IntakeV4LayerRoleSetup.model_validate(layer_role_setup)
            runtime = selected_layer_refs_runtime_state(setup)
            if runtime["status"] == "confirmed" and runtime["refs"]:
                for ref in runtime["refs"]:
                    blocked.append(
                        _entry(
                            field_key=field["field_key"],
                            runtime_source=field["runtime_source"],
                            product_truth_path=field["product_truth_path"],
                            state="suggested",
                            value_status="derived_at_read_time",
                            promotion_allowed=False,
                            reason=(
                                "Layer-role setup derives selected layer refs at read time, "
                                "but the persisted projection is absent until the workspace is saved again."
                            ),
                            blockers=["SELECTED_LAYER_REFS_NOT_PERSISTED"],
                            identity_key=f"layer_id:{ref.layer_id}",
                        )
                    )
                return eligible, blocked
        except Exception:
            pass

    blocked_state = "missing"
    value_status = "missing"
    reason = "Selected layer refs are missing."
    blockers = base_blockers or ["SELECTED_LAYER_REFS_MISSING"]
    if persisted_refs and confirmation_status != "complete":
        blocked_state = "partial"
        value_status = "persisted_but_unconfirmed"
        reason = "Selected layer refs exist but layer-role confirmation is not complete, so they cannot be promoted."
        blockers = base_blockers or ["SELECTED_LAYER_REFS_UNCONFIRMED"]
    elif setup_layers:
        blocked_state = "suggested"
        value_status = "layer_role_evidence_only"
        reason = "Layer-role evidence exists, but persisted selected layer refs with stable confirmed identity are not available yet."
    blocked.append(
        _entry(
            field_key=field["field_key"],
            runtime_source=field["runtime_source"],
            product_truth_path=field["product_truth_path"],
            state=blocked_state,
            value_status=value_status,
            promotion_allowed=False,
            reason=reason,
            blockers=blockers,
        )
    )
    return eligible, blocked


def _classify_scalar_entry(
    field: dict[str, Any],
    *,
    raw_value: Any,
    explicit_confirmed: bool,
    suggested_state: str | None = None,
    suggested_reason: str | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    base_blockers = [str(value) for value in (field.get("blockers") or []) if str(value).strip()]
    value_present = raw_value is not None and raw_value != ""

    if field.get("state") == "confirmed" and explicit_confirmed and value_present:
        return [
            _entry(
                field_key=field["field_key"],
                runtime_source=field["runtime_source"],
                product_truth_path=field["product_truth_path"],
                state="confirmed",
                value_status="explicit_confirmed",
                promotion_allowed=True,
                reason="Field value is explicitly persisted and confirmed, so it is eligible for Product Truth promotion.",
                blockers=[],
            )
        ], []

    if value_present:
        state = suggested_state or "hydrated"
        reason = suggested_reason or "Field value exists but is not explicitly confirmed, so it remains draft evidence only."
        blockers = base_blockers or ["CONFIRMATION_REQUIRED"]
        return [], [
            _entry(
                field_key=field["field_key"],
                runtime_source=field["runtime_source"],
                product_truth_path=field["product_truth_path"],
                state=state,
                value_status="present_unconfirmed",
                promotion_allowed=False,
                reason=reason,
                blockers=blockers,
            )
        ]

    if suggested_state is not None and suggested_reason is not None:
        return [], [
            _entry(
                field_key=field["field_key"],
                runtime_source=field["runtime_source"],
                product_truth_path=field["product_truth_path"],
                state=suggested_state,
                value_status="evidence_only",
                promotion_allowed=False,
                reason=suggested_reason,
                blockers=base_blockers,
            )
        ]

    return [], [
        _entry(
            field_key=field["field_key"],
            runtime_source=field["runtime_source"],
            product_truth_path=field["product_truth_path"],
            state=str(field.get("state") or "blocked"),
            value_status="missing",
            promotion_allowed=False,
            reason="Field value is missing, so it cannot be promoted.",
            blockers=base_blockers,
        )
    ]


def _classify_artwork_boolean_entries(
    field: dict[str, Any],
    payload_raw: dict[str, Any] | None,
    *,
    value_name: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    eligible: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []
    finish_setup = payload_raw.get("finish_setup") if isinstance(payload_raw, dict) and isinstance(payload_raw.get("finish_setup"), dict) else {}
    artwork_rows = finish_setup.get("artwork_finishes") if isinstance(finish_setup.get("artwork_finishes"), list) else []
    setup_confirmed = finish_setup.get("confirmed") is True
    base_blockers = [str(value) for value in (field.get("blockers") or []) if str(value).strip()]

    if not artwork_rows:
        blocked.append(
            _entry(
                field_key=field["field_key"],
                runtime_source=field["runtime_source"],
                product_truth_path=field["product_truth_path"],
                state=str(field.get("state") or "missing"),
                value_status="missing_rows",
                promotion_allowed=False,
                reason="Artwork finish rows are missing, so row-level Product Truth entries cannot be planned.",
                blockers=base_blockers,
            )
        )
        return eligible, blocked

    for raw_row in artwork_rows:
        if not isinstance(raw_row, dict):
            blocked.append(
                _entry(
                    field_key=field["field_key"],
                    runtime_source=field["runtime_source"],
                    product_truth_path=field["product_truth_path"],
                    state="blocked",
                    value_status="invalid_row_shape",
                    promotion_allowed=False,
                    reason="Artwork finish row is not a valid object, so no canonical row-level entry can be planned.",
                    blockers=[*base_blockers, "ARTWORK_ROW_INVALID"],
                )
            )
            continue

        layer_key = _string(raw_row.get("layer_key"))
        identity_key = f"layer_key:{layer_key}" if layer_key else None
        explicit_value = _bool_or_none(raw_row.get(value_name))
        row_confirmed = raw_row.get("confirmed") is True or setup_confirmed
        execution_type = _string(raw_row.get("execution_type"))

        if explicit_value is not None and row_confirmed and layer_key and field.get("state") == "confirmed":
            eligible.append(
                _entry(
                    field_key=field["field_key"],
                    runtime_source=field["runtime_source"],
                    product_truth_path=field["product_truth_path"],
                    state="confirmed",
                    value_status="explicit_confirmed",
                    promotion_allowed=True,
                    reason="Artwork row carries an explicit confirmed boolean and stable layer_key identity, so it is eligible for Product Truth promotion.",
                    blockers=[],
                    identity_key=identity_key,
                )
            )
            continue

        row_blockers = list(base_blockers)
        state = str(field.get("state") or "blocked")
        value_status = "missing"
        reason = "Artwork row value is not eligible for Product Truth promotion."

        if not layer_key:
            row_blockers.append("ARTWORK_ROW_IDENTITY_MISSING")
            state = "blocked"
            value_status = "missing_identity"
            reason = "Artwork row requires a stable layer_key identity; UI label or array index is not canonical identity."
        elif explicit_value is None:
            row_blockers.append("ARTWORK_BOOLEAN_EXPLICIT_VALUE_MISSING")
            if execution_type:
                state = "suggested"
                value_status = "derived_evidence_only"
                reason = "Artwork boolean is missing and only encoded execution_type evidence exists; derived evidence is not canonical truth."
            else:
                state = "missing"
                value_status = "missing_boolean"
                reason = "Artwork row is missing an explicit boolean value, so it cannot be promoted."
        elif not row_confirmed:
            row_blockers.append("ARTWORK_ROW_CONFIRMATION_MISSING")
            state = "hydrated"
            value_status = "present_unconfirmed"
            reason = "Artwork row carries an explicit boolean but lacks row or setup confirmation, so it remains hydrated draft input only."

        blocked.append(
            _entry(
                field_key=field["field_key"],
                runtime_source=field["runtime_source"],
                product_truth_path=field["product_truth_path"],
                state=state,
                value_status=value_status,
                promotion_allowed=False,
                reason=reason,
                blockers=row_blockers,
                identity_key=identity_key,
            )
        )
    return eligible, blocked


def build_product_truth_promotion_plan(
    payload: dict[str, Any] | Any,
    *,
    template_code: str = DEFAULT_TEMPLATE_CODE,
) -> dict[str, Any]:
    payload_raw = _payload_to_dict(payload)
    read_model = build_form_system_runtime_capture_read_model(payload, template_code=template_code)
    root = deepcopy(read_model.get("root") or {})

    if not root.get("allowed"):
        return {
            "planner_version": PLANNER_VERSION,
            "read_only": True,
            "root": root,
            "eligible_entries": [],
            "blocked_entries": [],
            "blockers": list(read_model.get("blockers") or []),
            "downstream_write_intent": _downstream_write_intent(),
            "notes": [
                "Fail-closed Product Truth promotion planner response.",
                "No Product Truth, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, or DB write behavior is invoked.",
            ],
        }

    fields_by_key = {
        field["field_key"]: field
        for field in (read_model.get("fields") or [])
        if isinstance(field, dict) and field.get("field_key")
    }
    finish_setup = payload_raw.get("finish_setup") if isinstance(payload_raw, dict) and isinstance(payload_raw.get("finish_setup"), dict) else {}
    finish_confirmed = finish_setup.get("confirmed") is True
    eligible_entries: list[dict[str, Any]] = []
    blocked_entries: list[dict[str, Any]] = []

    field = fields_by_key.get("svg.selected_layer_refs[]")
    if field is not None:
        eligible, blocked = _classify_selected_layer_entries(field, payload_raw)
        eligible_entries.extend(eligible)
        blocked_entries.extend(blocked)

    field = fields_by_key.get("finish.finish_target")
    if field is not None:
        eligible, blocked = _classify_scalar_entry(
            field,
            raw_value=_string(finish_setup.get("finish_target")),
            explicit_confirmed=finish_confirmed,
        )
        eligible_entries.extend(eligible)
        blocked_entries.extend(blocked)

    field = fields_by_key.get("finish.print_required")
    if field is not None:
        eligible, blocked = _classify_artwork_boolean_entries(field, payload_raw, value_name="print_required")
        eligible_entries.extend(eligible)
        blocked_entries.extend(blocked)

    field = fields_by_key.get("finish.lamination_required")
    if field is not None:
        eligible, blocked = _classify_artwork_boolean_entries(field, payload_raw, value_name="lamination_required")
        eligible_entries.extend(eligible)
        blocked_entries.extend(blocked)

    field = fields_by_key.get("mounting.mounting_scope")
    if field is not None:
        eligible, blocked = _classify_scalar_entry(
            field,
            raw_value=_string(finish_setup.get("mounting_scope")),
            explicit_confirmed=finish_confirmed,
        )
        eligible_entries.extend(eligible)
        blocked_entries.extend(blocked)

    field = fields_by_key.get("mounting.mounting_solution")
    if field is not None:
        solution_raw = finish_setup.get("mounting_solution")
        solution_template = ""
        if isinstance(solution_raw, dict):
            solution_template = _string(solution_raw.get("template_code"))
        eligible, blocked = _classify_scalar_entry(
            field,
            raw_value=solution_template or None,
            explicit_confirmed=finish_confirmed,
        )
        eligible_entries.extend(eligible)
        blocked_entries.extend(blocked)

    return {
        "planner_version": PLANNER_VERSION,
        "read_only": True,
        "root": root,
        "eligible_entries": eligible_entries,
        "blocked_entries": blocked_entries,
        "blockers": _blocker_summary(blocked_entries),
        "downstream_write_intent": _downstream_write_intent(),
        "notes": [
            "Read-only Product Truth promotion planner only.",
            "Only confirmed runtime capture entries with stable canonical identity are eligible.",
            "No Product Truth, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, or DB write behavior is invoked.",
        ],
    }