"""Production-release guard for frozen owner decisions (Wave 5 / W5-T01).

Evaluates OrderSnapshotV2 owner_decisions_snapshot against operational resolution
state stored separately in orders.readiness_snapshot — never mutates frozen snapshots.
"""

from __future__ import annotations

import json
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from models.orders import Orders
from schemas.auth import UserResponse
from schemas.execution_owner_decision_release import (
    PRODUCTION_RELEASE_POLICY,
    FrozenDecisionClassification,
    OwnerDecisionOperationalStatus,
    OwnerDecisionReleaseBlocker,
    OwnerDecisionResolutionResult,
    ProductionReleaseEvaluation,
    ReleaseStatus,
)
from schemas.order_snapshot_v2 import OrderSnapshotV2
from schemas.quote_snapshot_v2 import QuoteSnapshotOwnerDecision
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

OWNER_DECISION_RESOLUTIONS_KEY = "owner_decision_resolutions_v1"

PRODUCTION_BLOCKING_OWNER_DECISION_CODES = frozenset(
    {
        "INTERNAL_SABLON_FOREX_COST",
        "INTERNAL_MONTAJ_RULE",
        "INTERNAL_CONSUMABLES_RULE",
    }
)

NONBLOCKING_INTERNAL_ANALYSIS_CODES = frozenset(
    {
        "INTERNAL_AMBALARE_RULE",
        "OVERHEAD_ALLOCATION_PENDING",
    }
)

RESOLVE_ALLOWED_ROLES = frozenset({"admin", "manager"})

OPERATOR_LABELS: dict[str, str] = {
    "INTERNAL_SABLON_FOREX_COST": "Cost șablon Forex — decizie owner necesară înainte de producție",
    "INTERNAL_MONTAJ_RULE": "Regulă montaj — decizie owner necesară înainte de producție",
    "INTERNAL_CONSUMABLES_RULE": "Regulă consumabile — decizie owner necesară înainte de producție",
    "INTERNAL_AMBALARE_RULE": "Regulă ambalare — analiză internă (nu blochează producția)",
    "OVERHEAD_ALLOCATION_PENDING": "Alocare overhead — analiză internă (nu blochează producția)",
}

RESOLUTION_ALLOWED_STATUSES = frozenset({"acknowledged", "resolved"})


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_readiness_snapshot(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return dict(raw)
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def classify_frozen_decision_code(code: str) -> FrozenDecisionClassification:
    normalized = str(code or "").strip()
    if not normalized:
        return "unclassified"
    if normalized in PRODUCTION_BLOCKING_OWNER_DECISION_CODES:
        if normalized in NONBLOCKING_INTERNAL_ANALYSIS_CODES:
            return "unclassified"
        return "production_blocking"
    if normalized in NONBLOCKING_INTERNAL_ANALYSIS_CODES:
        return "nonblocking_internal_analysis"
    return "unclassified"


def _operator_label(decision: QuoteSnapshotOwnerDecision) -> str:
    code = str(decision.code or "").strip()
    if code in OPERATOR_LABELS:
        return OPERATOR_LABELS[code]
    label = str(decision.label or "").strip()
    return label or f"Decizie owner: {code}"


def load_frozen_owner_decisions(order: Orders) -> list[QuoteSnapshotOwnerDecision]:
    raw = getattr(order, "snapshot_v2_json", None)
    if not raw or not str(raw).strip():
        return []
    try:
        snapshot = OrderSnapshotV2.model_validate_json(str(raw))
    except Exception:
        return []
    return list(snapshot.owner_decisions_snapshot or [])


def _default_decision_runtime_entry(
    decision: QuoteSnapshotOwnerDecision,
    *,
    classification: FrozenDecisionClassification,
) -> dict[str, Any]:
    code = str(decision.code or "").strip()
    is_production_blocking = classification == "production_blocking"
    return {
        "code": code,
        "label": _operator_label(decision),
        "frozen_classification": classification,
        "operational_status": "unresolved",
        "required_role": "admin",
        "requires_resolution": is_production_blocking,
        "acknowledgement_sufficient": False,
        "scope": "order",
        "source": str(decision.source or ""),
        "module_code": decision.module_code,
        "resolved_at": None,
        "resolved_by_user_id": None,
        "resolved_by_user_name": None,
        "resolution_note": None,
    }


def _ensure_resolution_state(
    readiness_snapshot: dict[str, Any],
    frozen_decisions: list[QuoteSnapshotOwnerDecision],
) -> dict[str, Any]:
    patched = deepcopy(readiness_snapshot)
    existing = patched.get(OWNER_DECISION_RESOLUTIONS_KEY)
    if not isinstance(existing, dict):
        existing = {}

    decisions_map = existing.get("decisions")
    if not isinstance(decisions_map, dict):
        decisions_map = {}

    audit_history = existing.get("audit_history")
    if not isinstance(audit_history, list):
        audit_history = []

    for decision in frozen_decisions:
        code = str(decision.code or "").strip()
        if not code:
            continue
        classification = classify_frozen_decision_code(code)
        if code not in decisions_map:
            decisions_map[code] = _default_decision_runtime_entry(
                decision,
                classification=classification,
            )
            continue
        entry = decisions_map[code]
        if not isinstance(entry, dict):
            entry = _default_decision_runtime_entry(decision, classification=classification)
            decisions_map[code] = entry
        entry.setdefault("code", code)
        entry.setdefault("label", _operator_label(decision))
        entry.setdefault("frozen_classification", classification)
        entry.setdefault("operational_status", "unresolved")
        entry.setdefault("required_role", "admin")
        entry.setdefault(
            "requires_resolution",
            classification == "production_blocking",
        )
        entry.setdefault("acknowledgement_sufficient", False)
        entry.setdefault("scope", "order")
        entry.setdefault("source", str(decision.source or ""))
        entry.setdefault("module_code", decision.module_code)

    patched[OWNER_DECISION_RESOLUTIONS_KEY] = {
        "policy": PRODUCTION_RELEASE_POLICY,
        "decisions": decisions_map,
        "audit_history": audit_history,
        "last_initialized_at": existing.get("last_initialized_at") or _utc_now_iso(),
    }
    return patched


def _operational_status_allows_release(
    entry: dict[str, Any],
    *,
    classification: FrozenDecisionClassification,
) -> bool:
    if classification != "production_blocking":
        return True
    status = str(entry.get("operational_status") or "unresolved").strip().lower()
    if status == "resolved":
        return True
    if status == "waived":
        return True
    if status == "acknowledged" and bool(entry.get("acknowledgement_sufficient")):
        return True
    return False


def evaluate_production_release(order: Orders) -> ProductionReleaseEvaluation:
    frozen_decisions = load_frozen_owner_decisions(order)
    if not frozen_decisions:
        return ProductionReleaseEvaluation(
            release_status="RELEASE_ALLOWED",
            policy=PRODUCTION_RELEASE_POLICY,
            order_id=getattr(order, "id", None),
            message="No frozen owner decisions on order.",
        )

    readiness = _parse_readiness_snapshot(getattr(order, "readiness_snapshot", None))
    resolution_state = _ensure_resolution_state(readiness, frozen_decisions)
    decisions_map = resolution_state[OWNER_DECISION_RESOLUTIONS_KEY]["decisions"]

    if (
        PRODUCTION_BLOCKING_OWNER_DECISION_CODES
        & NONBLOCKING_INTERNAL_ANALYSIS_CODES
    ):
        return ProductionReleaseEvaluation(
            release_status="RELEASE_BLOCKED_POLICY_ERROR",
            policy=PRODUCTION_RELEASE_POLICY,
            order_id=getattr(order, "id", None),
            message="Owner-decision policy sets overlap — owner policy blocker.",
        )

    blockers: list[OwnerDecisionReleaseBlocker] = []
    nonblocking_codes: list[str] = []
    frozen_codes: list[str] = []
    policy_errors: list[str] = []

    for decision in frozen_decisions:
        code = str(decision.code or "").strip()
        if not code:
            continue
        frozen_codes.append(code)
        classification = classify_frozen_decision_code(code)
        if classification == "nonblocking_internal_analysis":
            nonblocking_codes.append(code)
            continue
        if classification != "production_blocking":
            continue

        entry = decisions_map.get(code)
        if not isinstance(entry, dict):
            policy_errors.append(code)
            continue

        operational_status = str(
            entry.get("operational_status") or "unresolved"
        ).strip().lower()
        if operational_status not in {
            "unresolved",
            "acknowledged",
            "resolved",
            "waived",
        }:
            policy_errors.append(code)
            continue

        if _operational_status_allows_release(entry, classification=classification):
            continue

        blockers.append(
            OwnerDecisionReleaseBlocker(
                code=code,
                label=_operator_label(decision),
                scope=str(entry.get("scope") or "order"),
                required_action="resolve_owner_decision",
                acknowledgement_sufficient=bool(
                    entry.get("acknowledgement_sufficient", False)
                ),
                requires_resolution=bool(entry.get("requires_resolution", True)),
                operational_status=operational_status,  # type: ignore[arg-type]
                frozen_classification=classification,
            )
        )

    if policy_errors:
        return ProductionReleaseEvaluation(
            release_status="RELEASE_BLOCKED_POLICY_ERROR",
            policy=PRODUCTION_RELEASE_POLICY,
            order_id=getattr(order, "id", None),
            frozen_decision_codes=frozen_codes,
            nonblocking_decision_codes=nonblocking_codes,
            message="Missing or invalid runtime resolution state for production blockers.",
            blockers=blockers,
        )

    if blockers:
        return ProductionReleaseEvaluation(
            release_status="RELEASE_BLOCKED_OWNER_DECISIONS",
            policy=PRODUCTION_RELEASE_POLICY,
            order_id=getattr(order, "id", None),
            frozen_decision_codes=frozen_codes,
            nonblocking_decision_codes=nonblocking_codes,
            blockers=blockers,
            message="Producția este blocată de decizii owner nerezolvate.",
        )

    return ProductionReleaseEvaluation(
        release_status="RELEASE_ALLOWED",
        policy=PRODUCTION_RELEASE_POLICY,
        order_id=getattr(order, "id", None),
        frozen_decision_codes=frozen_codes,
        nonblocking_decision_codes=nonblocking_codes,
        message="Production release allowed.",
    )


def production_release_http_exception(
    evaluation: ProductionReleaseEvaluation,
) -> HTTPException:
    return HTTPException(
        status_code=409,
        detail={
            "code": "production_release_blocked",
            "error": "production_release_blocked",
            "message": evaluation.message
            or "Producția este blocată de decizii owner nerezolvate.",
            "release_status": evaluation.release_status,
            "policy": evaluation.policy,
            "blockers": [item.model_dump() for item in evaluation.blockers],
            "frozen_decision_codes": evaluation.frozen_decision_codes,
            "nonblocking_decision_codes": evaluation.nonblocking_decision_codes,
        },
    )


async def load_order_for_release_gate(
    db: AsyncSession,
    order_id: int,
) -> Orders | None:
    return (
        await db.execute(select(Orders).where(Orders.id == order_id))
    ).scalar_one_or_none()


async def assert_production_release_allowed(
    db: AsyncSession,
    order_id: int,
) -> ProductionReleaseEvaluation:
    order = await load_order_for_release_gate(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})

    evaluation = evaluate_production_release(order)
    if evaluation.release_status == "RELEASE_ALLOWED":
        return evaluation
    raise production_release_http_exception(evaluation)


async def get_production_release_status(
    db: AsyncSession,
    order_id: int,
) -> ProductionReleaseEvaluation:
    order = await load_order_for_release_gate(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})
    return evaluate_production_release(order)


def _assert_resolve_role(user: UserResponse) -> None:
    role = str(getattr(user, "role", None) or "").strip().lower()
    if role not in RESOLVE_ALLOWED_ROLES:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "owner_decision_resolve_forbidden",
                "message": "Nu ai permisiunea de a rezolva decizii owner de producție.",
                "required_roles": sorted(RESOLVE_ALLOWED_ROLES),
            },
        )


async def resolve_owner_decision_for_order(
    db: AsyncSession,
    *,
    order_id: int,
    code: str,
    status: OwnerDecisionOperationalStatus,
    note: str,
    current_user: UserResponse,
) -> OwnerDecisionResolutionResult:
    _assert_resolve_role(current_user)

    normalized_code = str(code or "").strip()
    normalized_status = str(status or "").strip().lower()
    normalized_note = str(note or "").strip()

    if normalized_status not in RESOLUTION_ALLOWED_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "owner_decision_status_invalid",
                "message": "Statusul operațional nu este permis pentru rezolvare.",
                "allowed_statuses": sorted(RESOLUTION_ALLOWED_STATUSES),
            },
        )
    if len(normalized_note) < 3:
        raise HTTPException(
            status_code=422,
            detail={"error": "owner_decision_note_required"},
        )

    order = await load_order_for_release_gate(db, order_id)
    if order is None:
        raise HTTPException(status_code=404, detail={"error": "order_not_found"})

    frozen_decisions = load_frozen_owner_decisions(order)
    frozen_by_code = {
        str(item.code or "").strip(): item for item in frozen_decisions if item.code
    }
    if normalized_code not in frozen_by_code:
        raise HTTPException(
            status_code=404,
            detail={"error": "owner_decision_not_in_frozen_snapshot"},
        )

    classification = classify_frozen_decision_code(normalized_code)
    if classification == "nonblocking_internal_analysis":
        raise HTTPException(
            status_code=422,
            detail={
                "error": "owner_decision_nonblocking",
                "message": "Această decizie este doar pentru analiză internă și nu necesită rezolvare operațională.",
            },
        )
    if classification != "production_blocking":
        raise HTTPException(
            status_code=422,
            detail={
                "error": "owner_decision_not_production_blocking",
                "message": "Decizia nu este clasificată ca blocantă de producție.",
            },
        )

    readiness = _parse_readiness_snapshot(getattr(order, "readiness_snapshot", None))
    resolution_state = _ensure_resolution_state(readiness, frozen_decisions)
    container = resolution_state[OWNER_DECISION_RESOLUTIONS_KEY]
    decisions_map: dict[str, Any] = container["decisions"]
    entry = decisions_map[normalized_code]
    if not isinstance(entry, dict):
        raise HTTPException(
            status_code=409,
            detail={"error": "owner_decision_runtime_state_missing"},
        )

    previous_status = str(entry.get("operational_status") or "unresolved").strip().lower()
    idempotent = (
        previous_status == normalized_status
        and str(entry.get("resolution_note") or "").strip() == normalized_note
        and str(entry.get("resolved_by_user_id") or "") == str(current_user.id or "")
    )

    audit_event_id: str | None = None
    if not idempotent:
        audit_event_id = f"odr-{uuid.uuid4().hex[:12]}"
        now = _utc_now_iso()
        entry["operational_status"] = normalized_status
        entry["resolved_at"] = now
        entry["resolved_by_user_id"] = str(current_user.id or "")
        entry["resolved_by_user_name"] = str(current_user.name or "")
        entry["resolution_note"] = normalized_note
        container["audit_history"].append(
            {
                "event_id": audit_event_id,
                "event": "owner_decision_resolution",
                "code": normalized_code,
                "from_status": previous_status,
                "to_status": normalized_status,
                "note": normalized_note,
                "by_user_id": str(current_user.id or ""),
                "by_user_name": str(current_user.name or ""),
                "by_user_role": str(current_user.role or ""),
                "at": now,
            }
        )
        container["last_resolution_at"] = now
        order.readiness_snapshot = resolution_state
        await db.commit()
        await db.refresh(order)
    else:
        await db.refresh(order)

    release_eval = evaluate_production_release(order)
    return OwnerDecisionResolutionResult(
        order_id=order_id,
        code=normalized_code,
        operational_status=normalized_status,  # type: ignore[arg-type]
        release_status=release_eval.release_status,  # type: ignore[arg-type]
        idempotent=idempotent,
        audit_event_id=audit_event_id,
    )
