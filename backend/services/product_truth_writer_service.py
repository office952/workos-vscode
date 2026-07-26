from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from services.product_truth_writer_dry_run_service import (
    TARGET_CONTRACT_VERSION,
    TARGET_PATH,
    WRITER_CONTRACT_VERSION,
    compute_payload_hash,
    get_confirmed_snapshot_target_path,
    normalize_downstream_write_intent,
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    return {}


def _copy_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return copy.deepcopy(value)
    return {}


def _confirmed_snapshot(payload_raw: dict[str, Any]) -> dict[str, Any] | None:
    product_truth = payload_raw.get("product_truth")
    if not isinstance(product_truth, dict):
        return None
    snapshot = product_truth.get("confirmed_snapshot_v1")
    if not isinstance(snapshot, dict):
        return None
    return snapshot


def _confirmed_snapshot_hash(payload_raw: dict[str, Any]) -> str:
    return compute_payload_hash(_confirmed_snapshot(payload_raw) or {})


def _return_cant_bridge_hash(payload_raw: dict[str, Any]) -> str:
    product_truth = _dict(payload_raw.get("product_truth"))
    components = _dict(product_truth.get("components"))
    return compute_payload_hash(_dict(components.get("return_cant")))


def _current_entry_value(payload_raw: dict[str, Any], field_key: str, identity_key: str | None) -> Any:
    snapshot = _confirmed_snapshot(payload_raw) or {}
    entries = _dict(snapshot.get("entries"))
    current: Any = entries
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


def _ensure_snapshot(payload_raw: dict[str, Any]) -> dict[str, Any]:
    product_truth = payload_raw.setdefault("product_truth", {})
    if not isinstance(product_truth, dict):
        product_truth = {}
        payload_raw["product_truth"] = product_truth
    snapshot = product_truth.setdefault("confirmed_snapshot_v1", {})
    if not isinstance(snapshot, dict):
        snapshot = {}
        product_truth["confirmed_snapshot_v1"] = snapshot
    snapshot.setdefault("metadata", {})
    snapshot.setdefault("planner_basis", {})
    snapshot.setdefault("entries", {})
    snapshot.setdefault("audit_trail", [])
    if not isinstance(snapshot["metadata"], dict):
        snapshot["metadata"] = {}
    if not isinstance(snapshot["planner_basis"], dict):
        snapshot["planner_basis"] = {}
    if not isinstance(snapshot["entries"], dict):
        snapshot["entries"] = {}
    if not isinstance(snapshot["audit_trail"], list):
        snapshot["audit_trail"] = []
    return snapshot


def _write_entry_record(snapshot_entries: dict[str, Any], mutation: dict[str, Any]) -> None:
    field_key = str(mutation.get("field_key") or "")
    identity_key = mutation.get("identity_key")
    current = snapshot_entries
    segments = field_key.split(".")
    for segment in segments[:-1]:
        nested = current.setdefault(segment, {})
        if not isinstance(nested, dict):
            nested = {}
            current[segment] = nested
        current = nested
    leaf = segments[-1]
    record = {
        "entry_key": mutation.get("entry_key"),
        "field_key": field_key,
        "source_path": mutation.get("source_path"),
        "target_path": mutation.get("target_path"),
        "value": copy.deepcopy(mutation.get("value")),
        "value_state": mutation.get("value_state"),
        "source_state": mutation.get("source_state"),
        "source_type": mutation.get("source_type"),
        "identity_key": identity_key,
        "planner_entry_hash": mutation.get("planner_entry_hash"),
        "promotion_hash": mutation.get("promotion_hash"),
        "provenance": copy.deepcopy(mutation.get("provenance") or {}),
        "conflict_status": mutation.get("conflict_status"),
        "stored_at": _utcnow_iso(),
    }
    if identity_key is None:
        current[leaf] = record
        return
    leaf_node = current.setdefault(leaf, {})
    if not isinstance(leaf_node, dict):
        leaf_node = {}
        current[leaf] = leaf_node
    leaf_node[identity_key] = record


def _existing_entries_match(payload_raw: dict[str, Any], proposed_mutations: list[dict[str, Any]]) -> bool:
    if not proposed_mutations:
        return False
    for mutation in proposed_mutations:
        if _current_entry_value(
            payload_raw,
            str(mutation.get("field_key") or ""),
            mutation.get("identity_key"),
        ) != mutation.get("value"):
            return False
    return True


def proposed_mutations_match_confirmed_snapshot(
    payload_raw: dict[str, Any],
    proposed_mutations: list[dict[str, Any]],
) -> bool:
    return _existing_entries_match(payload_raw, proposed_mutations)


def _refusal_detail(
    *,
    error: str,
    workspace_id: str,
    workspace_code: str | None,
    dry_run_response: dict[str, Any],
    payload_raw: dict[str, Any],
) -> dict[str, Any]:
    return {
        "error": error,
        "write_performed": False,
        "idempotent_replay": False,
        "workspace_id": workspace_id,
        "workspace_code": workspace_code,
        "target_path": dry_run_response.get("target_path") or get_confirmed_snapshot_target_path(),
        "promoted_entries": [],
        "refused_entries": copy.deepcopy(dry_run_response.get("refused_entries") or []),
        "blockers": copy.deepcopy(dry_run_response.get("blockers") or []),
        "payload_hash_before": compute_payload_hash(payload_raw),
        "payload_hash_after": compute_payload_hash(payload_raw),
        "confirmed_snapshot_hash_before": _confirmed_snapshot_hash(payload_raw),
        "confirmed_snapshot_hash_after": _confirmed_snapshot_hash(payload_raw),
        "return_cant_bridge_hash_before": _return_cant_bridge_hash(payload_raw),
        "return_cant_bridge_hash_after": _return_cant_bridge_hash(payload_raw),
        "downstream_write_intent": normalize_downstream_write_intent(
            dry_run_response.get("downstream_write_intent") or {}
        ),
        "notes": [
            "Atomic Product Truth writer refusal.",
            "No payload mutation was committed.",
            "payload.product_truth.components.return_cant remains untouched.",
        ],
    }


def build_product_truth_writer_response(
    *,
    workspace_id: str,
    workspace_code: str | None,
    payload_before: dict[str, Any],
    payload_after: dict[str, Any],
    dry_run_response: dict[str, Any],
    promoted_entries: list[dict[str, Any]],
    write_performed: bool,
    idempotent_replay: bool,
) -> dict[str, Any]:
    return {
        "write_performed": write_performed,
        "idempotent_replay": idempotent_replay,
        "workspace_id": workspace_id,
        "workspace_code": workspace_code,
        "target_path": get_confirmed_snapshot_target_path(),
        "promoted_entries": copy.deepcopy(promoted_entries),
        "refused_entries": [],
        "blockers": copy.deepcopy(dry_run_response.get("blockers") or []),
        "payload_hash_before": compute_payload_hash(payload_before),
        "payload_hash_after": compute_payload_hash(payload_after),
        "confirmed_snapshot_hash_before": _confirmed_snapshot_hash(payload_before),
        "confirmed_snapshot_hash_after": _confirmed_snapshot_hash(payload_after),
        "return_cant_bridge_hash_before": _return_cant_bridge_hash(payload_before),
        "return_cant_bridge_hash_after": _return_cant_bridge_hash(payload_after),
        "downstream_write_intent": normalize_downstream_write_intent(
            dry_run_response.get("downstream_write_intent") or {}
        ),
        "notes": [
            f"Mutation target limited to {TARGET_PATH}.",
            "No ProductDefinition, Pricing, Quote, Order, Execution, ProductAggregate, or TaskGraph write was triggered.",
            "payload.product_truth.components.return_cant remains untouched.",
        ],
    }


def promote_product_truth_snapshot(
    *,
    workspace_id: str,
    workspace_code: str | None,
    payload_raw: dict[str, Any],
    dry_run_response: dict[str, Any],
    actor: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if dry_run_response.get("target_path") != get_confirmed_snapshot_target_path():
        raise HTTPException(
            status_code=422,
            detail=_refusal_detail(
                error="writer_target_path_mismatch",
                workspace_id=workspace_id,
                workspace_code=workspace_code,
                dry_run_response=dry_run_response,
                payload_raw=payload_raw,
            ),
        )

    proposed_mutations = [copy.deepcopy(item) for item in (dry_run_response.get("proposed_mutations") or [])]
    refused_entries = [copy.deepcopy(item) for item in (dry_run_response.get("refused_entries") or [])]
    if refused_entries:
        raise HTTPException(
            status_code=422,
            detail=_refusal_detail(
                error="product_truth_promotion_refused",
                workspace_id=workspace_id,
                workspace_code=workspace_code,
                dry_run_response=dry_run_response,
                payload_raw=payload_raw,
            ),
        )

    payload_before = copy.deepcopy(payload_raw)
    if _existing_entries_match(payload_raw, proposed_mutations):
        return payload_before, build_product_truth_writer_response(
            workspace_id=workspace_id,
            workspace_code=workspace_code,
            payload_before=payload_before,
            payload_after=payload_raw,
            dry_run_response=dry_run_response,
            promoted_entries=proposed_mutations,
            write_performed=False,
            idempotent_replay=True,
        )

    snapshot = _ensure_snapshot(payload_raw)
    snapshot["metadata"] = {
        "workspace_id": workspace_id,
        "workspace_code": workspace_code,
        "target_path": TARGET_PATH,
        "target_contract_version": TARGET_CONTRACT_VERSION,
        "writer_contract_version": WRITER_CONTRACT_VERSION,
        "last_promotion_hash": dry_run_response.get("promotion_hash"),
        "last_promoted_at": _utcnow_iso(),
        "last_actor": copy.deepcopy(actor),
    }
    snapshot["planner_basis"] = copy.deepcopy(dry_run_response.get("idempotency_basis") or {})
    snapshot["planner_basis"]["planner_version"] = dry_run_response.get("planner_version")
    snapshot["planner_basis"]["target_path"] = TARGET_PATH
    snapshot_entries = _dict(snapshot.get("entries"))
    snapshot["entries"] = snapshot_entries
    for mutation in proposed_mutations:
        _write_entry_record(snapshot_entries, mutation)
    snapshot_audit = snapshot.get("audit_trail")
    if not isinstance(snapshot_audit, list):
        snapshot_audit = []
        snapshot["audit_trail"] = snapshot_audit
    snapshot_audit.append(
        {
            "promotion_hash": dry_run_response.get("promotion_hash"),
            "workspace_id": workspace_id,
            "workspace_code": workspace_code,
            "target_path": TARGET_PATH,
            "promoted_entry_keys": [item.get("entry_key") for item in proposed_mutations],
            "idempotency_basis": copy.deepcopy(dry_run_response.get("idempotency_basis") or {}),
            "actor": copy.deepcopy(actor),
            "promoted_at": _utcnow_iso(),
        }
    )

    return payload_before, build_product_truth_writer_response(
        workspace_id=workspace_id,
        workspace_code=workspace_code,
        payload_before=payload_before,
        payload_after=payload_raw,
        dry_run_response=dry_run_response,
        promoted_entries=proposed_mutations,
        write_performed=True,
        idempotent_replay=False,
    )