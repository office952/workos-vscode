from __future__ import annotations

from copy import deepcopy
from typing import Any

from services.form_system_contract_backbone_service import build_form_system_contract_map


CONTRACT_VERSION = "form_system_contract_mapping_adapter_v1"

FieldSpec = dict[str, Any]


FIELD_SPECS: list[FieldSpec] = [
    {
        "field_key": "finish.print_required",
        "owner": "finish_artwork",
        "source": "artwork_execution_type_evidence",
        "state": "draft",
        "product_truth_path": "components.finish.printRequired",
        "confirmation_required": True,
        "blockers": ["PRINT_REQUIRED_UNKNOWN"],
        "notes": "Current Review/artwork flow can imply print intent from execution_type, but the canonical field remains a separate explicit boolean.",
    },
    {
        "field_key": "finish.lamination_required",
        "owner": "finish_artwork",
        "source": "artwork_execution_type_evidence",
        "state": "draft",
        "product_truth_path": "components.finish.laminationRequired",
        "confirmation_required": True,
        "blockers": ["LAMINATION_REQUIRED_UNKNOWN"],
        "notes": "Lamination remains distinct from print; current execution_type evidence does not make it confirmed truth.",
    },
    {
        "field_key": "finish.finish_target",
        "owner": "finish_artwork",
        "source": "ui_zone_implied_target",
        "state": "blocked",
        "product_truth_path": "components.finish.target",
        "confirmation_required": True,
        "blockers": ["FINISH_TARGET_MISSING"],
        "notes": "Existing UI zones imply target by area, but the canonical finish target is not a first-class confirmed field yet.",
    },
    {
        "field_key": "support.support_type",
        "owner": "mounting_support",
        "source": "mounting_bridge_or_operator_input",
        "state": "blocked",
        "product_truth_path": "components.support.supportType",
        "confirmation_required": True,
        "blockers": ["SUPPORT_TYPE_MISSING"],
        "notes": "Support type is a separate support truth field and must not be silently inferred from mounting_system.",
    },
    {
        "field_key": "mounting.mounting_scope",
        "owner": "mounting_support",
        "source": "operator_mounting_scope_decision",
        "state": "blocked",
        "product_truth_path": "components.mounting.mountingScope",
        "confirmation_required": True,
        "blockers": ["MOUNTING_SCOPE_MISSING"],
        "notes": "Commercial mounting scope is documented but not a first-class runtime field in current Intake V6 Review.",
    },
    {
        "field_key": "svg.selected_layer_group",
        "owner": "svg_layer_roles",
        "source": "operator_layer_selection_evidence",
        "state": "suggested",
        "product_truth_path": "svg.selected_layer_refs[]",
        "confirmation_required": True,
        "blockers": ["SELECTED_FACE_LAYER_MISSING"],
        "notes": "Selected layer/group remains evidence and a gate until explicit operator confirmation anchors it to canonical truth.",
    },
]


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


def _field_entry(spec: FieldSpec) -> dict[str, Any]:
    owner = spec.get("owner")
    source = spec.get("source")
    path = spec.get("product_truth_path")
    requested_state = str(spec.get("state") or "blocked")

    blockers = list(spec.get("blockers") or [])
    state = requested_state
    if not owner:
        blockers = [*blockers, "FIELD_OWNER_MISSING"]
        state = "blocked"
    if not source:
        blockers = [*blockers, "FIELD_SOURCE_MISSING"]
        state = "blocked"
    if not path:
        blockers = [*blockers, "PRODUCT_TRUTH_PATH_MISSING"]
        state = "blocked"
    if requested_state == "confirmed" and spec.get("confirmation_required") is True:
        blockers = [*blockers, "CONFIRMATION_REQUIRED"]
        state = "blocked"

    deduped_blockers: list[str] = []
    for blocker in blockers:
        if blocker and blocker not in deduped_blockers:
            deduped_blockers.append(blocker)

    return {
        "field_key": spec["field_key"],
        "owner": owner,
        "source": source,
        "state": state,
        "product_truth_path": path,
        "confirmation_required": bool(spec.get("confirmation_required", False)),
        "blockers": deduped_blockers,
        "notes": spec.get("notes"),
    }


def build_form_system_contract_readonly_mapping(
    template_code: str,
    *,
    field_specs: list[FieldSpec] | None = None,
    root_type: str = "product_template",
    quote_mode: str = "product_total",
    payload_raw: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a narrow read-only mapping from the active product root to explicit field contract metadata."""
    backbone = build_form_system_contract_map(
        template_code,
        root_type=root_type,
        quote_mode=quote_mode,
        payload_raw=payload_raw,
    )
    root = deepcopy(backbone["root"])
    if not root.get("allowed"):
        return {
            "contract_version": CONTRACT_VERSION,
            "read_only": True,
            "root": root,
            "fields": [],
            "blockers": list(backbone.get("blockers") or []),
            "downstream_write_intent": _downstream_write_intent(),
            "notes": [
                "Fail-closed narrow mapping adapter response.",
                "No Product Truth, Pricing, Quote, Order, Execution, or DB write behavior is invoked.",
            ],
        }

    entries = [_field_entry(spec) for spec in (field_specs or FIELD_SPECS)]
    backbone_fields = {field["field_key"]: field for field in backbone.get("fields") or []}
    selected_layer_runtime = backbone_fields.get("svg.selected_layer_group")
    if payload_raw is not None and selected_layer_runtime is not None:
        for entry in entries:
            if entry["field_key"] != "svg.selected_layer_group":
                continue
            entry["source"] = selected_layer_runtime.get("source_type") or entry["source"]
            entry["state"] = selected_layer_runtime.get("state") or entry["state"]
            blocker_code = selected_layer_runtime.get("blocker_code")
            entry["blockers"] = [blocker_code] if blocker_code else []
            break
    if payload_raw is not None:
        finish_setup = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else None
        finish_target = str(finish_setup.get("finish_target") or "").strip() if finish_setup else ""
        finish_confirmed = bool(finish_setup.get("confirmed") is True) if finish_setup else False
        for entry in entries:
            if entry["field_key"] != "finish.finish_target":
                continue
            if finish_target and finish_confirmed:
                entry["source"] = "payload_persisted"
                entry["state"] = "confirmed"
                entry["blockers"] = []
            break
    blockers = [
        {
            "field_key": field["field_key"],
            "blockers": field["blockers"],
            "state": field["state"],
        }
        for field in entries
        if field["blockers"]
    ]
    return {
        "contract_version": CONTRACT_VERSION,
        "read_only": True,
        "root": root,
        "fields": entries,
        "blockers": blockers,
        "downstream_write_intent": _downstream_write_intent(),
        "notes": [
            "Narrow read-only mapping adapter only.",
            "Product Template declares intent; Component Templates own fields; Intake V6 may display or persist draft input but does not invent ownership.",
            "Suggested or draft fields are not confirmed Product Truth.",
        ],
    }