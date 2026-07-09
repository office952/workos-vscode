from __future__ import annotations

import copy
import hashlib
import json
from typing import Any


TARGET_PATH = "payload_json.product_truth.confirmed_snapshot_v1"
WRITER_CONTRACT_VERSION = "dry_run_contract_v1"
TARGET_CONTRACT_VERSION = "confirmed_snapshot_v1"
WRITER_REAL_ATOMIC_POLICY = "fail_closed_if_request_contains_blocked"

_ALL_FALSE_DOWNSTREAM_WRITE_INTENT = {
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


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(value: Any) -> str:
    return f"sha256:{hashlib.sha256(_canonical_json(value).encode('utf-8')).hexdigest()}"


def _copy_dict(value: dict[str, Any] | None) -> dict[str, Any]:
    if isinstance(value, dict):
        return copy.deepcopy(value)
    return {}


def compute_payload_hash(payload_raw: dict[str, Any]) -> str:
    return _sha256(payload_raw)


def compute_planner_hash(planner_response: dict[str, Any]) -> str:
    basis = {
        "workspace_id": planner_response.get("workspace_id"),
        "workspace_code": planner_response.get("workspace_code"),
        "root_template_code": planner_response.get("root_template_code"),
        "product_binding_template_code": planner_response.get("product_binding_template_code"),
        "planner_version": planner_response.get("planner_version"),
        "eligible_entries": sorted(
            [copy.deepcopy(entry) for entry in (planner_response.get("eligible_entries") or [])],
            key=lambda entry: str(entry.get("entry_key") or ""),
        ),
        "blocked_entries": sorted(
            [copy.deepcopy(entry) for entry in (planner_response.get("blocked_entries") or [])],
            key=lambda entry: str(entry.get("entry_key") or ""),
        ),
        "blockers": sorted(
            [copy.deepcopy(blocker) for blocker in (planner_response.get("blockers") or [])],
            key=lambda blocker: (
                str(blocker.get("field_key") or ""),
                str(blocker.get("identity_key") or ""),
            ),
        ),
        "downstream_write_intent": normalize_downstream_write_intent(
            planner_response.get("downstream_write_intent") or {}
        ),
    }
    return _sha256(basis)


def compute_planner_entry_hash(*, entry: dict[str, Any], target_path: str, value: Any) -> str:
    basis = {
        "entry_key": entry.get("entry_key"),
        "field_key": entry.get("field_key"),
        "runtime_source": entry.get("runtime_source"),
        "product_truth_path": entry.get("product_truth_path"),
        "target_path": target_path,
        "state": entry.get("state"),
        "value_status": entry.get("value_status"),
        "identity_key": entry.get("identity_key"),
        "value": value,
        "blockers": sorted(str(value) for value in (entry.get("blockers") or [])),
    }
    return _sha256(basis)


def normalize_downstream_write_intent(value: dict[str, Any]) -> dict[str, bool]:
    normalized = dict(_ALL_FALSE_DOWNSTREAM_WRITE_INTENT)
    for key in list(normalized):
        normalized[key] = bool(value.get(key))
    return normalized


def downstream_write_intent_is_all_false(value: dict[str, Any]) -> bool:
    return all(flag is False for flag in normalize_downstream_write_intent(value).values())


def get_confirmed_snapshot_target_path() -> str:
    return TARGET_PATH


def _split_identity(identity_key: str | None) -> tuple[str | None, str | None]:
    if not identity_key or ":" not in identity_key:
        return None, None
    key, value = identity_key.split(":", 1)
    return key, value


def _target_path_for_entry(field_key: str, identity_key: str | None) -> str:
    path = f"{TARGET_PATH}.entries.{field_key}"
    if identity_key:
        return f"{path}[{identity_key}]"
    return path


def _source_type_for_field(field_key: str) -> str:
    if field_key == "svg.selected_layer_refs[]":
        return "selected_layer_ref"
    if field_key in {"finish.print_required", "finish.lamination_required"}:
        return "artwork_row_boolean"
    return "scalar"


def _source_path_for_entry(field_key: str, identity_key: str | None) -> str:
    _, identity_value = _split_identity(identity_key)
    if field_key == "svg.selected_layer_refs[]":
        if identity_value:
            return f"payload.svg.selected_layer_refs[layer_id={identity_value}]"
        return "payload.svg.selected_layer_refs"
    if field_key == "finish.finish_target":
        return "payload.finish_setup.finish_target"
    if field_key == "mounting.mounting_scope":
        return "payload.finish_setup.mounting_scope"
    if field_key == "support.support_type":
        return "payload.finish_setup.support_type"
    if field_key in {"finish.print_required", "finish.lamination_required"}:
        leaf = field_key.split(".", 1)[1]
        if identity_value:
            return f"payload.finish_setup.artwork_finishes[layer_key={identity_value}].{leaf}"
        return f"payload.finish_setup.artwork_finishes[].{leaf}"
    return f"payload.{field_key}"


def _find_selected_layer_ref(payload_raw: dict[str, Any], identity_key: str | None) -> dict[str, Any] | None:
    _, layer_id = _split_identity(identity_key)
    svg = payload_raw.get("svg") if isinstance(payload_raw.get("svg"), dict) else {}
    selected_refs = svg.get("selected_layer_refs") if isinstance(svg.get("selected_layer_refs"), list) else []
    for item in selected_refs:
        if isinstance(item, dict) and str(item.get("layer_id") or "").strip() == layer_id:
            return copy.deepcopy(item)
    return None


def _find_artwork_row(payload_raw: dict[str, Any], identity_key: str | None) -> dict[str, Any] | None:
    _, layer_key = _split_identity(identity_key)
    finish_setup = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else {}
    artwork_rows = finish_setup.get("artwork_finishes") if isinstance(finish_setup.get("artwork_finishes"), list) else []
    for item in artwork_rows:
        if isinstance(item, dict) and str(item.get("layer_key") or "").strip() == layer_key:
            return copy.deepcopy(item)
    return None


def _value_for_entry(payload_raw: dict[str, Any], entry: dict[str, Any]) -> Any:
    field_key = str(entry.get("field_key") or "")
    identity_key = entry.get("identity_key")
    if field_key == "svg.selected_layer_refs[]":
        return _find_selected_layer_ref(payload_raw, identity_key)
    finish_setup = payload_raw.get("finish_setup") if isinstance(payload_raw.get("finish_setup"), dict) else {}
    if field_key == "finish.finish_target":
        return finish_setup.get("finish_target")
    if field_key == "mounting.mounting_scope":
        return finish_setup.get("mounting_scope")
    if field_key == "support.support_type":
        return finish_setup.get("support_type")
    if field_key in {"finish.print_required", "finish.lamination_required"}:
        artwork_row = _find_artwork_row(payload_raw, identity_key)
        if artwork_row is None:
            return None
        return artwork_row.get(field_key.split(".", 1)[1])
    return None


def _snapshot_entries_root(payload_raw: dict[str, Any]) -> dict[str, Any]:
    product_truth = payload_raw.get("product_truth") if isinstance(payload_raw.get("product_truth"), dict) else {}
    confirmed = product_truth.get("confirmed_snapshot_v1") if isinstance(product_truth.get("confirmed_snapshot_v1"), dict) else {}
    entries = confirmed.get("entries") if isinstance(confirmed.get("entries"), dict) else {}
    return entries


def _existing_snapshot_value(payload_raw: dict[str, Any], field_key: str, identity_key: str | None) -> Any:
    current: Any = _snapshot_entries_root(payload_raw)
    for segment in field_key.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(segment)
    if identity_key is not None:
        if not isinstance(current, dict):
            return None
        current = current.get(identity_key)
    if isinstance(current, dict) and "value" in current:
        return copy.deepcopy(current.get("value"))
    return copy.deepcopy(current)


def _conflict_status(payload_raw: dict[str, Any], field_key: str, identity_key: str | None, value: Any) -> str:
    existing_value = _existing_snapshot_value(payload_raw, field_key, identity_key)
    if existing_value is None:
        return "no_conflict"
    if existing_value == value:
        return "would_overwrite_same_value"
    return "would_conflict_existing_snapshot"


def _provenance(
    *,
    workspace_id: str,
    workspace_code: str | None,
    root_template_code: str,
    product_binding_template_code: str | None,
    planner_version: str,
    planner_hash: str,
    payload_hash_basis: str,
    source_path: str,
    source_state: str,
    source_type: str,
    identity_key: str | None,
    actor: dict[str, Any],
) -> dict[str, Any]:
    return {
        "workspace_id": workspace_id,
        "workspace_code": workspace_code,
        "root_template_code": root_template_code,
        "product_binding_template_code": product_binding_template_code,
        "planner_version": planner_version,
        "planner_hash": planner_hash,
        "payload_hash_basis": payload_hash_basis,
        "source_path": source_path,
        "source_state": source_state,
        "source_type": source_type,
        "identity_key": identity_key,
        "actor": copy.deepcopy(actor),
        "writer_contract_version": WRITER_CONTRACT_VERSION,
        "target_contract_version": TARGET_CONTRACT_VERSION,
        "planner_read_only": True,
        "promotion_reason": "eligible_entry_would_be_promoted",
    }


def _requested_entry_keys(requested_entry_keys: list[str] | None) -> set[str] | None:
    if requested_entry_keys is None:
        return None
    requested = {str(entry_key).strip() for entry_key in requested_entry_keys if str(entry_key).strip()}
    return requested


def _requested_unknown_entry_keys(
    *,
    requested_entry_keys: set[str] | None,
    eligible_entries: list[dict[str, Any]],
    blocked_entries: list[dict[str, Any]],
) -> list[str]:
    if requested_entry_keys is None:
        return []
    known = {
        str(entry.get("entry_key") or "")
        for entry in [*eligible_entries, *blocked_entries]
        if str(entry.get("entry_key") or "")
    }
    return sorted(entry_key for entry_key in requested_entry_keys if entry_key not in known)


def build_product_truth_writer_dry_run_response(
    *,
    workspace_id: str,
    workspace_record_id: str,
    workspace_code: str | None,
    root_template_code: str,
    product_binding_template_code: str | None,
    payload_raw: dict[str, Any],
    planner_response: dict[str, Any],
    actor: dict[str, Any] | None = None,
    requested_entry_keys: list[str] | None = None,
) -> dict[str, Any]:
    actor_payload = _copy_dict(actor)
    requested_keys = _requested_entry_keys(requested_entry_keys)
    payload_hash_before = compute_payload_hash(payload_raw)
    planner_hash_before = compute_planner_hash(planner_response)
    eligible_entries = sorted(
        [copy.deepcopy(entry) for entry in (planner_response.get("eligible_entries") or [])],
        key=lambda entry: str(entry.get("entry_key") or ""),
    )
    blocked_entries = sorted(
        [copy.deepcopy(entry) for entry in (planner_response.get("blocked_entries") or [])],
        key=lambda entry: str(entry.get("entry_key") or ""),
    )

    proposed_mutations: list[dict[str, Any]] = []
    for entry in eligible_entries:
        entry_key = str(entry.get("entry_key") or "")
        if requested_keys is not None and entry_key not in requested_keys:
            continue
        field_key = str(entry.get("field_key") or "")
        identity_key = entry.get("identity_key")
        value = _value_for_entry(payload_raw, entry)
        target_path = _target_path_for_entry(field_key, identity_key)
        source_path = _source_path_for_entry(field_key, identity_key)
        source_type = _source_type_for_field(field_key)
        planner_entry_hash = compute_planner_entry_hash(entry=entry, target_path=target_path, value=value)
        proposed_mutations.append(
            {
                "entry_key": entry_key,
                "field_key": field_key,
                "source_path": source_path,
                "target_path": target_path,
                "value": copy.deepcopy(value),
                "value_state": "confirmed",
                "source_state": entry.get("state") or "confirmed",
                "source_type": source_type,
                "identity_key": identity_key,
                "planner_entry_hash": planner_entry_hash,
                "provenance": _provenance(
                    workspace_id=workspace_id,
                    workspace_code=workspace_code,
                    root_template_code=root_template_code,
                    product_binding_template_code=product_binding_template_code,
                    planner_version=str(planner_response.get("planner_version") or "v1"),
                    planner_hash=planner_hash_before,
                    payload_hash_basis=payload_hash_before,
                    source_path=source_path,
                    source_state=str(entry.get("state") or "confirmed"),
                    source_type=source_type,
                    identity_key=identity_key,
                    actor=actor_payload,
                ),
                "conflict_status": _conflict_status(payload_raw, field_key, identity_key, value),
                "action": "would_write",
            }
        )

    refused_entries: list[dict[str, Any]] = []
    for entry in blocked_entries:
        entry_key = str(entry.get("entry_key") or "")
        if requested_keys is not None and entry_key not in requested_keys:
            continue
        field_key = str(entry.get("field_key") or "")
        identity_key = entry.get("identity_key")
        target_path = _target_path_for_entry(field_key, identity_key)
        refused_entries.append(
            {
                "action": "refused",
                "refusal_is_blocking": True,
                "entry_key": entry_key,
                "field_key": field_key,
                "source_path": _source_path_for_entry(field_key, identity_key),
                "target_path": target_path,
                "reason": entry.get("reason") or "Blocked planner entry cannot be promoted during dry-run.",
                "blockers": copy.deepcopy(entry.get("blockers") or []),
            }
        )
        if identity_key is not None:
            refused_entries[-1]["identity_key"] = identity_key

    unknown_requested_entry_keys = _requested_unknown_entry_keys(
        requested_entry_keys=requested_keys,
        eligible_entries=eligible_entries,
        blocked_entries=blocked_entries,
    )
    for entry_key in unknown_requested_entry_keys:
        refused_entries.append(
            {
                "action": "refused",
                "refusal_is_blocking": True,
                "entry_key": entry_key,
                "field_key": entry_key,
                "source_path": "request.requested_entry_keys[]",
                "target_path": None,
                "reason": "Requested entry key does not exist in the current planner basis.",
                "blockers": ["REQUESTED_ENTRY_KEY_UNKNOWN"],
            }
        )

    idempotency_basis = {
        "workspace_id": workspace_id,
        "workspace_code": workspace_code,
        "root_template_code": root_template_code,
        "product_binding_template_code": product_binding_template_code,
        "planner_version": planner_response.get("planner_version") or "v1",
        "planner_hash": planner_hash_before,
        "payload_hash_basis": payload_hash_before,
        "normalized_entries": [
            {
                "entry_key": mutation["entry_key"],
                "field_key": mutation["field_key"],
                "target_path": mutation["target_path"],
                "identity_key": mutation.get("identity_key"),
                "value": copy.deepcopy(mutation["value"]),
            }
            for mutation in proposed_mutations
        ],
    }
    promotion_hash = _sha256(idempotency_basis) if proposed_mutations else None
    for mutation in proposed_mutations:
        mutation["promotion_hash"] = promotion_hash

    payload_hash_after = compute_payload_hash(payload_raw)
    planner_hash_after = compute_planner_hash(planner_response)
    downstream_write_intent = normalize_downstream_write_intent(
        planner_response.get("downstream_write_intent") or {}
    )
    response = {
        "read_only": True,
        "dry_run": True,
        "writer_real_atomic_policy": WRITER_REAL_ATOMIC_POLICY,
        "workspace_id": workspace_id,
        "workspace_record_id": workspace_record_id,
        "workspace_code": workspace_code,
        "root_template_code": root_template_code,
        "product_binding_template_code": product_binding_template_code,
        "planner_version": planner_response.get("planner_version") or "v1",
        "target_path": TARGET_PATH,
        "proposed_mutations": proposed_mutations,
        "refused_entries": refused_entries,
        "blockers": copy.deepcopy(planner_response.get("blockers") or []),
        "idempotency_basis": idempotency_basis,
        "promotion_hash": promotion_hash,
        "downstream_write_intent": downstream_write_intent,
        "no_mutation_proof": {
            "payload_hash_before": payload_hash_before,
            "payload_hash_after": payload_hash_after,
            "payload_hash_unchanged": payload_hash_before == payload_hash_after,
            "planner_hash_before": planner_hash_before,
            "planner_hash_after": planner_hash_after,
            "planner_hash_unchanged": planner_hash_before == planner_hash_after,
            "product_truth_target_hash_before": _sha256(
                _copy_dict(
                    (
                        payload_raw.get("product_truth") if isinstance(payload_raw.get("product_truth"), dict) else {}
                    ).get("confirmed_snapshot_v1")
                    if isinstance(payload_raw.get("product_truth"), dict)
                    else {}
                )
            ),
            "product_truth_target_hash_after": _sha256(
                _copy_dict(
                    (
                        payload_raw.get("product_truth") if isinstance(payload_raw.get("product_truth"), dict) else {}
                    ).get("confirmed_snapshot_v1")
                    if isinstance(payload_raw.get("product_truth"), dict)
                    else {}
                )
            ),
            "product_truth_target_mutated": False,
            "return_cant_bridge_hash_before": _sha256(
                _copy_dict(
                    (
                        (
                            payload_raw.get("product_truth")
                            if isinstance(payload_raw.get("product_truth"), dict)
                            else {}
                        ).get("components")
                        if isinstance(
                            (
                                payload_raw.get("product_truth")
                                if isinstance(payload_raw.get("product_truth"), dict)
                                else {}
                            ).get("components"),
                            dict,
                        )
                        else {}
                    ).get("return_cant")
                    if isinstance(
                        (
                            payload_raw.get("product_truth")
                            if isinstance(payload_raw.get("product_truth"), dict)
                            else {}
                        ).get("components"),
                        dict,
                    )
                    else {}
                )
            ),
            "return_cant_bridge_hash_after": _sha256(
                _copy_dict(
                    (
                        (
                            payload_raw.get("product_truth")
                            if isinstance(payload_raw.get("product_truth"), dict)
                            else {}
                        ).get("components")
                        if isinstance(
                            (
                                payload_raw.get("product_truth")
                                if isinstance(payload_raw.get("product_truth"), dict)
                                else {}
                            ).get("components"),
                            dict,
                        )
                        else {}
                    ).get("return_cant")
                    if isinstance(
                        (
                            payload_raw.get("product_truth")
                            if isinstance(payload_raw.get("product_truth"), dict)
                            else {}
                        ).get("components"),
                        dict,
                    )
                    else {}
                )
            ),
            "return_cant_bridge_mutated": False,
            "downstream_mutated": False,
            "db_write_performed": False,
        },
        "notes": [
            "Dry-run visibility only; no persistence performed.",
            f"Target path remains {TARGET_PATH}.",
            "payload.product_truth.components.return_cant is not used as a generic sink.",
            f"Real writer policy remains {WRITER_REAL_ATOMIC_POLICY}.",
        ],
    }
    return response