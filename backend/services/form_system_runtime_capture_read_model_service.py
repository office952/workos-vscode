"""Minimal read-only Form System runtime capture read model.

This service projects the already-confirmed runtime capture series into a stable
read-only shape without Product Truth writes, Pricing mutation, Quote/Order/
Execution mutation, DB writes, or new writer surfaces.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from services.form_system_contract_mapping_adapter_service import (
    build_form_system_contract_readonly_mapping,
)


READ_MODEL_VERSION = "form_system_runtime_capture_read_model_v1"
DEFAULT_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"


FIELD_SPECS: list[dict[str, str]] = [
    {
        "field_key": "svg.selected_layer_refs[]",
        "adapter_field_key": "svg.selected_layer_group",
        "runtime_source": "svg.selected_layer_refs[]",
        "product_truth_path": "svg.selected_layer_refs[]",
        "confirmation_rule": "Persisted selected layer refs require layer_role_setup.confirmation_status=complete plus stable layer_id and confirmation_state=confirmed.",
    },
    {
        "field_key": "finish.finish_target",
        "adapter_field_key": "finish.finish_target",
        "runtime_source": "finish_setup.finish_target",
        "product_truth_path": "components.finish.target",
        "confirmation_rule": "Explicit persisted finish_setup.finish_target and finish_setup.confirmed=true.",
    },
    {
        "field_key": "finish.print_required",
        "adapter_field_key": "finish.print_required",
        "runtime_source": "finish_setup.artwork_finishes[].print_required",
        "product_truth_path": "components.artwork.items[].printRequired",
        "confirmation_rule": "Every persisted artwork finish row must carry an explicit print_required value and row confirmation or finish_setup.confirmed=true.",
    },
    {
        "field_key": "finish.lamination_required",
        "adapter_field_key": "finish.lamination_required",
        "runtime_source": "finish_setup.artwork_finishes[].lamination_required",
        "product_truth_path": "components.artwork.items[].laminationRequired",
        "confirmation_rule": "Every persisted artwork finish row must carry an explicit lamination_required value and row confirmation or finish_setup.confirmed=true.",
    },
    {
        "field_key": "mounting.mounting_scope",
        "adapter_field_key": "mounting.mounting_scope",
        "runtime_source": "finish_setup.mounting_scope",
        "product_truth_path": "components.mounting.mountingScope",
        "confirmation_rule": "Explicit persisted finish_setup.mounting_scope and finish_setup.confirmed=true; no fallback from mounting_system or support_type.",
    },
    {
        "field_key": "mounting.mounting_solution",
        "adapter_field_key": "mounting.mounting_solution",
        "runtime_source": "finish_setup.mounting_solution",
        "product_truth_path": "components.mounting.solution",
        "confirmation_rule": "Explicit persisted finish_setup.mounting_solution when mounting preparation is active; legacy mounting_system and support_type do not satisfy this gate.",
    },
]


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


def _fail_closed_field(spec: dict[str, str], blocker: str) -> dict[str, Any]:
    return {
        "field_key": spec["field_key"],
        "runtime_source": spec["runtime_source"],
        "product_truth_path": spec["product_truth_path"],
        "state": "blocked",
        "confirmation_rule": spec["confirmation_rule"],
        "blockers": [blocker],
        "ready_for_product_truth": False,
    }


def _normalize_runtime_capture_blocker_rows(raw_blockers: Any) -> list[dict[str, Any]]:
    """Normalize fail-closed backbone rows into the field-level blocker contract.

    Canonical row shape:
      { "field_key": str, "blockers": [str, ...], "state": str }

    Backbone fail-closed rows historically used blocker_code / severity / blocks /
    message without nested blockers[]. Those fields are preserved additively so
    LOGO_NOT_OFFERABLE (and similar root blockers) keep their meaning while
    frontend collectors that read blockers[] stay consistent.
    """
    if not isinstance(raw_blockers, list):
        return []

    normalized: list[dict[str, Any]] = []
    for row in raw_blockers:
        if not isinstance(row, dict):
            continue

        codes: list[str] = []
        existing = row.get("blockers")
        if isinstance(existing, list):
            for item in existing:
                code = str(item or "").strip()
                if code and code not in codes:
                    codes.append(code)

        blocker_code = str(row.get("blocker_code") or "").strip()
        if blocker_code and blocker_code not in codes:
            codes.append(blocker_code)

        if not codes:
            continue

        state = str(row.get("state") or row.get("severity") or "blocked").strip() or "blocked"
        field_key = row.get("field_key")
        out: dict[str, Any] = {
            "field_key": str(field_key).strip() if field_key not in (None, "") else "root",
            "blockers": codes,
            "state": state,
        }

        # Additive compatibility — do not drop backbone semantics.
        if blocker_code:
            out["blocker_code"] = blocker_code
        if row.get("message") is not None:
            out["message"] = row.get("message")
        if row.get("severity") is not None:
            out["severity"] = row.get("severity")
        if isinstance(row.get("blocks"), list):
            out["blocks"] = list(row["blocks"])
        if row.get("owning_component") is not None:
            out["owning_component"] = row.get("owning_component")

        normalized.append(out)

    return normalized


def build_form_system_runtime_capture_read_model(
    payload: dict[str, Any] | Any,
    *,
    template_code: str = DEFAULT_TEMPLATE_CODE,
) -> dict[str, Any]:
    """Project the runtime capture series into a minimal read-only model."""
    payload_raw = _payload_to_dict(payload)
    mapping = build_form_system_contract_readonly_mapping(
        template_code,
        payload_raw=payload_raw,
    )
    root = deepcopy(mapping.get("root") or {})
    adapter_fields = {
        field["field_key"]: field
        for field in (mapping.get("fields") or [])
        if isinstance(field, dict) and field.get("field_key")
    }

    if not root.get("allowed"):
        return {
            "contract_version": READ_MODEL_VERSION,
            "read_only": True,
            "root": root,
            "fields": [],
            "blockers": _normalize_runtime_capture_blocker_rows(mapping.get("blockers") or []),
            "downstream_write_intent": _downstream_write_intent(),
            "notes": [
                "Fail-closed runtime capture read model response.",
                "No Product Truth, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, or DB write behavior is invoked.",
            ],
        }

    fields: list[dict[str, Any]] = []
    for spec in FIELD_SPECS:
        adapter_field = adapter_fields.get(spec["adapter_field_key"])
        if adapter_field is None:
            fields.append(_fail_closed_field(spec, "RUNTIME_CAPTURE_FIELD_NOT_EXPOSED"))
            continue

        blockers = [str(blocker) for blocker in (adapter_field.get("blockers") or []) if str(blocker).strip()]
        state = str(adapter_field.get("state") or "blocked")
        fields.append(
            {
                "field_key": spec["field_key"],
                "runtime_source": spec["runtime_source"],
                "product_truth_path": adapter_field.get("product_truth_path") or spec["product_truth_path"],
                "state": state,
                "confirmation_rule": spec["confirmation_rule"],
                "blockers": blockers,
                "ready_for_product_truth": state == "confirmed" and not blockers,
            }
        )

    blockers = [
        {
            "field_key": field["field_key"],
            "blockers": field["blockers"],
            "state": field["state"],
        }
        for field in fields
        if field["blockers"]
    ]
    return {
        "contract_version": READ_MODEL_VERSION,
        "read_only": True,
        "root": root,
        "fields": fields,
        "blockers": blockers,
        "downstream_write_intent": _downstream_write_intent(),
        "notes": [
            "Minimal runtime capture read model only.",
            "Fail-closed: missing or unconfirmed runtime inputs remain blocked.",
            "No Product Truth, Pricing, Quote, Order, Execution, ProductAggregate, TaskGraph, or DB write behavior is invoked.",
        ],
    }