"""ConfirmJobProductTruth — job-level Product Truth revision with pinned typed bags.

Reuses payload_json.product_truth.confirmed_snapshot_v1 (no new table).
Catalog is never written here. Field-level promote remains a separate subordinate path.
"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException

from services.acm_panel_pd_projection import coalesce_acm_panel_instance_from_finish
from services.product_truth_writer_dry_run_service import TARGET_PATH, compute_payload_hash

JOB_REVISION_CONTRACT = "job_revision_v1"
PINNED_BAG_KEYS = (
    "letter_group_instances",
    "acm_panel_instance",
    "component_placements",
)


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def draft_hash_for_payload(payload_raw: MappingLike) -> str:
    """Hash of draft workspace excluding confirmed snapshot (edit surface)."""
    payload = copy.deepcopy(dict(payload_raw) if isinstance(payload_raw, dict) else {})
    pt = payload.get("product_truth")
    if isinstance(pt, dict):
        pt = copy.deepcopy(pt)
        pt.pop("confirmed_snapshot_v1", None)
        payload["product_truth"] = pt
    return compute_payload_hash(payload)


# typing alias without importing Mapping everywhere for py3.10+
MappingLike = Any


def extract_typed_bags_from_finish(payload_raw: dict[str, Any]) -> dict[str, Any]:
    finish = _dict(payload_raw.get("finish_setup"))
    letters = _list(finish.get("letter_group_instances"))
    placements = _list(finish.get("component_placements"))
    acm = coalesce_acm_panel_instance_from_finish(finish)
    return {
        "letter_group_instances": copy.deepcopy(letters),
        "acm_panel_instance": copy.deepcopy(acm) if isinstance(acm, dict) else None,
        "component_placements": copy.deepcopy(placements),
    }


def compute_pinned_content_hash(
    *,
    pinned_bags: dict[str, Any],
    root_template_code: str | None,
    root_template_version: str | None,
) -> str:
    return compute_payload_hash(
        {
            "contract_version": JOB_REVISION_CONTRACT,
            "root_template_code": root_template_code,
            "root_template_version": root_template_version,
            "pinned_typed_bags": pinned_bags,
        }
    )


def get_job_revision_metadata(payload_raw: dict[str, Any]) -> dict[str, Any] | None:
    snapshot = _dict(_dict(payload_raw.get("product_truth")).get("confirmed_snapshot_v1"))
    meta = _dict(snapshot.get("metadata"))
    if meta.get("contract_version") != JOB_REVISION_CONTRACT and meta.get("revision") is None:
        # Field-promote-only snapshot without job revision
        if "revision" not in meta:
            return None
    if meta.get("revision") is None:
        return None
    return meta


def is_job_revision_stale(payload_raw: dict[str, Any]) -> bool:
    meta = get_job_revision_metadata(payload_raw)
    if not meta:
        return False
    return str(meta.get("confirmation_state") or "") == "stale_after_edit"


def commercial_freeze_allowed(payload_raw: dict[str, Any]) -> bool:
    meta = get_job_revision_metadata(payload_raw)
    if not meta:
        return False
    if str(meta.get("confirmation_state") or "") != "confirmed":
        return False
    if not snapshot_has_pinned_bags(payload_raw):
        return False
    return True


def read_product_truth_provenance(
    payload_raw: dict[str, Any] | None,
    *,
    freeze_allowed: bool | None = None,
) -> dict[str, Any]:
    """Read-only job revision/hash surface for PD / Aggregate / Quantity / Snap.

    Does not invent authority — returns None fields when metadata absent.
    When freeze_allowed is True (or computed True), status is ``confirmed``.
    """
    if not isinstance(payload_raw, dict):
        return {
            "product_truth_status": "draft",
            "product_truth_job_revision": None,
            "product_truth_content_hash": None,
        }
    meta = get_job_revision_metadata(payload_raw)
    if not meta:
        return {
            "product_truth_status": "draft",
            "product_truth_job_revision": None,
            "product_truth_content_hash": None,
        }
    allowed = commercial_freeze_allowed(payload_raw) if freeze_allowed is None else bool(freeze_allowed)
    state = str(meta.get("confirmation_state") or "draft")
    if allowed:
        status = "confirmed"
    elif state == "stale_after_edit":
        status = "stale_after_edit"
    else:
        status = state or "draft"
    revision = meta.get("revision")
    try:
        revision_int = int(revision) if revision is not None else None
    except (TypeError, ValueError):
        revision_int = None
    content_hash = meta.get("content_hash")
    return {
        "product_truth_status": status,
        "product_truth_job_revision": revision_int,
        "product_truth_content_hash": str(content_hash) if content_hash else None,
    }


def assert_commercial_freeze_allowed(payload_raw: dict[str, Any]) -> dict[str, Any]:
    """Raise 422 if job Product Truth is missing/stale. Returns metadata when allowed."""
    meta = get_job_revision_metadata(payload_raw)
    if not commercial_freeze_allowed(payload_raw):
        state = str((meta or {}).get("confirmation_state") or "unconfirmed")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "product_truth_not_confirmed_or_stale",
                "confirmation_state": state,
                "has_job_revision": meta is not None,
                "message": (
                    "Quote Snapshot V2 freeze requires a non-stale ConfirmJobProductTruth revision "
                    "with pinned_typed_bags."
                ),
            },
        )
    return meta or {}


def apply_pinned_bags_onto_payload(payload_raw: dict[str, Any]) -> dict[str, Any]:
    """Return a copy of payload with finish_setup bags replaced by pinned_typed_bags.

    Used by compilers/freeze so live draft edits cannot race after confirm.
    """
    out = copy.deepcopy(payload_raw)
    bags = get_pinned_typed_bags(out)
    if not bags:
        return out
    finish = out.get("finish_setup")
    finish = dict(finish) if isinstance(finish, dict) else {}
    if "letter_group_instances" in bags:
        finish["letter_group_instances"] = copy.deepcopy(bags.get("letter_group_instances") or [])
    if "component_placements" in bags:
        finish["component_placements"] = copy.deepcopy(bags.get("component_placements") or [])
    if "acm_panel_instance" in bags:
        finish["acm_panel_instance"] = copy.deepcopy(bags.get("acm_panel_instance"))
    # Re-project ACM mirrors from canonical pin
    try:
        from services.acm_panel_domain_service import project_acm_mirrors_from_canonical

        finish = project_acm_mirrors_from_canonical(finish)
    except Exception:
        pass
    out["finish_setup"] = finish
    return out


def snapshot_has_pinned_bags(payload_raw: dict[str, Any]) -> bool:
    snapshot = _dict(_dict(payload_raw.get("product_truth")).get("confirmed_snapshot_v1"))
    bags = snapshot.get("pinned_typed_bags")
    return isinstance(bags, dict) and ("acm_panel_instance" in bags or "letter_group_instances" in bags)


def get_pinned_typed_bags(payload_raw: dict[str, Any]) -> dict[str, Any] | None:
    snapshot = _dict(_dict(payload_raw.get("product_truth")).get("confirmed_snapshot_v1"))
    bags = snapshot.get("pinned_typed_bags")
    return copy.deepcopy(bags) if isinstance(bags, dict) else None


def mark_job_revision_stale_if_confirmed(payload_raw: dict[str, Any]) -> bool:
    """Mark confirmed job revision stale after draft edit. Returns True if mutated."""
    snapshot = _dict(_dict(payload_raw.get("product_truth")).get("confirmed_snapshot_v1"))
    meta = _dict(snapshot.get("metadata"))
    if meta.get("revision") is None:
        return False
    if str(meta.get("confirmation_state") or "") != "confirmed":
        return False
    meta["confirmation_state"] = "stale_after_edit"
    meta["stale_marked_at"] = _utcnow_iso()
    snapshot["metadata"] = meta
    product_truth = payload_raw.setdefault("product_truth", {})
    if not isinstance(product_truth, dict):
        product_truth = {}
        payload_raw["product_truth"] = product_truth
    product_truth["confirmed_snapshot_v1"] = snapshot
    return True


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
    snapshot.setdefault("entries", {})
    snapshot.setdefault("audit_trail", [])
    snapshot.setdefault("planner_basis", {})
    if not isinstance(snapshot["metadata"], dict):
        snapshot["metadata"] = {}
    if not isinstance(snapshot["audit_trail"], list):
        snapshot["audit_trail"] = []
    return snapshot


def _conflict(detail: dict[str, Any]) -> HTTPException:
    return HTTPException(status_code=409, detail=detail)


def confirm_job_product_truth(
    *,
    workspace_id: str,
    workspace_code: str | None,
    payload_raw: dict[str, Any],
    expected_revision: int,
    expected_draft_hash: str | None,
    expected_content_hash: str | None,
    root_template_code: str | None,
    root_template_version: str | None,
    actor_id: str | None,
    correction_reason: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Mutates payload_raw in place on write.
    Returns (response_dict, payload_raw).
    """
    draft_hash = draft_hash_for_payload(payload_raw)
    if expected_draft_hash is not None and expected_draft_hash != draft_hash:
        raise _conflict(
            {
                "error": "draft_hash_mismatch",
                "workspace_id": workspace_id,
                "expected_draft_hash": expected_draft_hash,
                "actual_draft_hash": draft_hash,
            }
        )

    template_code = (
        (root_template_code or "").strip()
        or str(payload_raw.get("template_code") or "").strip()
        or None
    )
    pinned = extract_typed_bags_from_finish(payload_raw)
    content_hash = compute_pinned_content_hash(
        pinned_bags=pinned,
        root_template_code=template_code,
        root_template_version=root_template_version,
    )

    existing_meta = get_job_revision_metadata(payload_raw)
    current_revision = int(existing_meta["revision"]) if existing_meta else 0
    current_state = str(existing_meta.get("confirmation_state") or "") if existing_meta else "unconfirmed"
    current_hash = str(existing_meta.get("content_hash") or "") if existing_meta else ""

    if expected_revision != current_revision:
        raise _conflict(
            {
                "error": "revision_mismatch",
                "workspace_id": workspace_id,
                "expected_revision": expected_revision,
                "actual_revision": current_revision,
            }
        )

    if expected_content_hash is not None and current_revision > 0 and expected_content_hash != current_hash:
        raise _conflict(
            {
                "error": "content_hash_mismatch",
                "workspace_id": workspace_id,
                "expected_content_hash": expected_content_hash,
                "actual_content_hash": current_hash,
            }
        )

    # Idempotent: same pin hash while confirmed
    if (
        current_revision > 0
        and current_state == "confirmed"
        and current_hash == content_hash
    ):
        meta_view = _metadata_view(existing_meta or {})
        return {
            "workspace_id": workspace_id,
            "workspace_code": workspace_code,
            "write_performed": False,
            "idempotent_noop": True,
            "product_truth_path": TARGET_PATH,
            "metadata": meta_view,
            "pinned_bag_keys": list(PINNED_BAG_KEYS),
            "draft_hash": draft_hash,
            "previous_revision": current_revision,
            "audit_entry": None,
        }, payload_raw

    new_revision = 1 if current_revision == 0 else current_revision + 1
    confirmed_at = _utcnow_iso()
    snapshot = _ensure_snapshot(payload_raw)
    # Preserve existing field entries / planner_basis from field promote
    prev_meta = _dict(snapshot.get("metadata"))
    metadata = {
        **{k: v for k, v in prev_meta.items() if k not in {
            "revision", "content_hash", "confirmation_state", "confirmed_at",
            "confirmed_by", "expected_draft_hash", "contract_version", "source",
            "stale_marked_at",
        }},
        "revision": new_revision,
        "content_hash": content_hash,
        "confirmation_state": "confirmed",
        "confirmed_at": confirmed_at,
        "confirmed_by": actor_id,
        "expected_draft_hash": draft_hash,
        "root_template_code": template_code,
        "root_template_version": root_template_version,
        "contract_version": JOB_REVISION_CONTRACT,
        "source": "confirm_job_product_truth",
        "provenance": {
            "command": "ConfirmJobProductTruth",
            "pinned_bag_keys": list(PINNED_BAG_KEYS),
            "catalog_write": False,
        },
        "workspace_id": workspace_id,
        "workspace_code": workspace_code,
        "target_path": TARGET_PATH,
    }
    snapshot["metadata"] = metadata
    snapshot["pinned_typed_bags"] = pinned

    audit_entry = {
        "command": "ConfirmJobProductTruth",
        "previous_revision": current_revision if current_revision > 0 else None,
        "current_revision": new_revision,
        "content_hash": content_hash,
        "previous_content_hash": current_hash or None,
        "correction_reason": correction_reason,
        "actor": actor_id,
        "timestamp": confirmed_at,
        "draft_hash": draft_hash,
    }
    audit = snapshot.get("audit_trail")
    if not isinstance(audit, list):
        audit = []
        snapshot["audit_trail"] = audit
    audit.append(audit_entry)

    return {
        "workspace_id": workspace_id,
        "workspace_code": workspace_code,
        "write_performed": True,
        "idempotent_noop": False,
        "product_truth_path": TARGET_PATH,
        "metadata": _metadata_view(metadata),
        "pinned_bag_keys": list(PINNED_BAG_KEYS),
        "draft_hash": draft_hash,
        "previous_revision": current_revision if current_revision > 0 else None,
        "audit_entry": audit_entry,
    }, payload_raw


def _metadata_view(meta: dict[str, Any]) -> dict[str, Any]:
    return {
        "revision": int(meta.get("revision") or 0),
        "content_hash": str(meta.get("content_hash") or ""),
        "confirmation_state": str(meta.get("confirmation_state") or "unconfirmed"),
        "confirmed_at": meta.get("confirmed_at"),
        "confirmed_by": meta.get("confirmed_by"),
        "expected_draft_hash": meta.get("expected_draft_hash"),
        "root_template_code": meta.get("root_template_code"),
        "root_template_version": meta.get("root_template_version"),
        "contract_version": str(meta.get("contract_version") or JOB_REVISION_CONTRACT),
        "source": str(meta.get("source") or "confirm_job_product_truth"),
        "provenance": copy.deepcopy(_dict(meta.get("provenance"))),
    }


def build_job_truth_status(
    *,
    workspace_id: str,
    payload_raw: dict[str, Any],
) -> dict[str, Any]:
    meta = get_job_revision_metadata(payload_raw)
    draft_hash = draft_hash_for_payload(payload_raw)
    stale = is_job_revision_stale(payload_raw)
    return {
        "workspace_id": workspace_id,
        "has_job_revision": meta is not None,
        "metadata": _metadata_view(meta) if meta else None,
        "draft_hash": draft_hash,
        "is_stale": stale,
        "commercial_freeze_allowed": commercial_freeze_allowed(payload_raw),
    }
