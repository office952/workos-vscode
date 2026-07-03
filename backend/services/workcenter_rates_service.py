"""Service layer for the `workcenter_rates` registry.

Sprint #20 — Product Registry Foundation.

This module owns:
  - status validation (canonical enum-in-code),
  - the `active` invariant (status=="active" requires a positive rate),
  - the canonical bridge `load_workcenter_rate_dict()` that the v2
    CostEngine / QuoteOrchestrator will eventually call instead of having
    rates injected at the caller boundary.

**Important:** Sprint #20 does NOT wire the orchestrator to call this
function. The bridge is shipped but not mounted, per spec §5.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import db_manager
from models.workcenter_rates import Workcenter_rates

logger = logging.getLogger(__name__)

VALID_STATUSES: frozenset[str] = frozenset(
    {"active", "missing_price", "needs_owner_input", "archived"}
)
VALID_RATE_BASES: frozenset[str] = frozenset(
    {"per_hour", "per_linear_meter", "per_piece", "per_square_meter"}
)
LINEAR_ONLY_CODES: frozenset[str] = frozenset(
    {
        "CNC",
        "LASER",
        "CNC_ROUTER",
        "LASER_CUTTING",
        "WC_METAL_FAB",
        "WC_CNC_ROUTING",
        "WC_LASER_CUTTING",
    }
)
_UNSET = object()


class WorkcenterRateValidationError(ValueError):
    """Raised when a workcenter rate row violates the canonical invariants."""


def _row_to_dict(row: Workcenter_rates) -> Dict[str, Any]:
    return {
        "id": row.id,
        "code": row.code,
        "label": row.label,
        "rate_per_hour": row.rate_per_hour,
        "rate_per_linear_meter": row.rate_per_linear_meter,
        "rate_basis": row.rate_basis,
        "currency": row.currency,
        "status": row.status,
        "is_active": bool(row.is_active),
        "approval_reference": row.approval_reference,
        "notes": row.notes,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def validate_status_and_rate(status: str, rate_per_hour: Optional[float]) -> None:
    """Enforce the canonical invariant.

    Rules:
      - `status` must be one of `VALID_STATUSES`.
      - If `status == "active"`, `rate_per_hour` must be a positive number.
      - For non-active statuses, `rate_per_hour` MAY be None or positive.
        Negative or zero rates are never allowed.
    """
    validate_rate_contract(
        code=None,
        status=status,
        is_active=(status == "active"),
        rate_basis="per_hour",
        rate_per_hour=rate_per_hour,
        rate_per_linear_meter=None,
    )


def validate_rate_contract(
    *,
    code: Optional[str],
    status: str,
    is_active: bool,
    rate_basis: str,
    rate_per_hour: Optional[float],
    rate_per_linear_meter: Optional[float],
) -> None:
    """Validate basis-aware rate contract with CNC/LASER guardrails."""
    if status not in VALID_STATUSES:
        raise WorkcenterRateValidationError(
            f"Invalid status '{status}'. Allowed: {sorted(VALID_STATUSES)}"
        )
    if rate_basis not in VALID_RATE_BASES:
        raise WorkcenterRateValidationError(
            f"Invalid rate_basis '{rate_basis}'. Allowed: {sorted(VALID_RATE_BASES)}"
        )
    if rate_per_hour is not None and rate_per_hour <= 0:
        raise WorkcenterRateValidationError(
            "rate_per_hour must be a positive number when provided"
        )
    if rate_per_linear_meter is not None and rate_per_linear_meter <= 0:
        raise WorkcenterRateValidationError(
            "rate_per_linear_meter must be a positive number when provided"
        )

    effective_active = bool(is_active or status == "active")
    normalized_code = (code or "").strip().upper()
    is_linear_only = normalized_code in LINEAR_ONLY_CODES

    if effective_active:
        if is_linear_only:
            if rate_basis != "per_linear_meter":
                raise WorkcenterRateValidationError(
                    "active CNC/LASER workcenters must use rate_basis='per_linear_meter'"
                )
            if rate_per_linear_meter is None:
                raise WorkcenterRateValidationError(
                    "active CNC/LASER workcenters require rate_per_linear_meter"
                )
            return

        if rate_basis == "per_hour" and rate_per_hour is None:
            raise WorkcenterRateValidationError(
                "active per_hour rows require a non-null, positive rate_per_hour"
            )
        if rate_basis in {"per_linear_meter", "per_piece", "per_square_meter"}:
            if rate_per_linear_meter is None:
                raise WorkcenterRateValidationError(
                    f"active {rate_basis} rows require a non-null, positive "
                    "rate_per_linear_meter (unit rate)"
                )


def _compute_is_active(status: str, is_active: Optional[bool]) -> bool:
    if is_active is None:
        return status == "active"
    return bool(is_active)


async def list_workcenter_rates(db: AsyncSession) -> List[Dict[str, Any]]:
    """Return every workcenter rate row as a serialized dict."""
    rows = (
        await db.execute(select(Workcenter_rates).order_by(Workcenter_rates.code))
    ).scalars().all()
    return [_row_to_dict(r) for r in rows]


async def get_workcenter_rate_by_code(
    db: AsyncSession, code: str
) -> Optional[Dict[str, Any]]:
    """Return a single workcenter rate by its canonical code, or None."""
    row = (
        await db.execute(select(Workcenter_rates).where(Workcenter_rates.code == code))
    ).scalar_one_or_none()
    return _row_to_dict(row) if row else None


async def create_workcenter_rate(
    db: AsyncSession,
    *,
    code: str,
    label: str,
    rate_per_hour: Optional[float] = None,
    rate_per_linear_meter: Optional[float] = None,
    rate_basis: str = "per_hour",
    status: str = "missing_price",
    is_active: Optional[bool] = None,
    approval_reference: Optional[str] = None,
    notes: Optional[str] = None,
    currency: str = "RON",
) -> Dict[str, Any]:
    """Insert a new workcenter rate row. Enforces code uniqueness + invariants."""
    if not code or not code.strip():
        raise WorkcenterRateValidationError("code is required")
    if not label or not label.strip():
        raise WorkcenterRateValidationError("label is required")
    effective_is_active = _compute_is_active(status, is_active)
    validate_rate_contract(
        code=code,
        status=status,
        is_active=effective_is_active,
        rate_basis=rate_basis,
        rate_per_hour=rate_per_hour,
        rate_per_linear_meter=rate_per_linear_meter,
    )

    existing = (
        await db.execute(select(Workcenter_rates).where(Workcenter_rates.code == code))
    ).scalar_one_or_none()
    if existing is not None:
        raise WorkcenterRateValidationError(
            f"workcenter_rate with code='{code}' already exists"
        )

    row = Workcenter_rates(
        code=code,
        label=label,
        rate_per_hour=rate_per_hour,
        rate_per_linear_meter=rate_per_linear_meter,
        rate_basis=rate_basis,
        currency=currency,
        status=status,
        is_active=effective_is_active,
        approval_reference=approval_reference,
        notes=notes,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    logger.info("workcenter_rate created: code=%s status=%s", code, status)
    return _row_to_dict(row)


async def update_workcenter_rate(
    db: AsyncSession,
    code: str,
    *,
    rate_per_hour: Optional[float] = _UNSET,
    rate_per_linear_meter: Optional[float] = _UNSET,
    rate_basis: Optional[str] = None,
    status: Optional[str] = None,
    is_active: Optional[bool] = None,
    approval_reference: Optional[str] = _UNSET,
    label: Optional[str] = None,
    notes: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """PATCH a workcenter rate row by code.

        Field semantics:
            - pass `_UNSET` (default) to keep existing value,
            - pass `None` to clear nullable fields,
            - pass scalar to set a new value.
    """
    row = (
        await db.execute(select(Workcenter_rates).where(Workcenter_rates.code == code))
    ).scalar_one_or_none()
    if row is None:
        return None

    new_status = status if status is not None else row.status
    new_rate_per_hour = (
        row.rate_per_hour if rate_per_hour is _UNSET else rate_per_hour
    )
    new_rate_per_linear_meter = (
        row.rate_per_linear_meter
        if rate_per_linear_meter is _UNSET
        else rate_per_linear_meter
    )
    new_rate_basis = rate_basis if rate_basis is not None else row.rate_basis
    new_is_active = _compute_is_active(new_status, is_active)

    validate_rate_contract(
        code=code,
        status=new_status,
        is_active=new_is_active,
        rate_basis=new_rate_basis,
        rate_per_hour=new_rate_per_hour,
        rate_per_linear_meter=new_rate_per_linear_meter,
    )

    if label is not None:
        row.label = label
    if notes is not None:
        row.notes = notes
    if approval_reference is not _UNSET:
        row.approval_reference = approval_reference
    row.status = new_status
    row.rate_per_hour = new_rate_per_hour
    row.rate_per_linear_meter = new_rate_per_linear_meter
    row.rate_basis = new_rate_basis
    row.is_active = new_is_active

    await db.commit()
    await db.refresh(row)
    logger.info(
        "workcenter_rate updated: code=%s status=%s rate=%s",
        code,
        row.status,
        row.rate_per_hour,
    )
    return _row_to_dict(row)


async def load_workcenter_rate_dict(
    db: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    """Canonical bridge for future orchestrator use.

        Returns a basis-aware dict containing ONLY active rows:
            - per_hour rows as `{code: <rate_per_hour_float>}`
            - per_linear_meter rows as
                `{code: {"rate_basis":"per_linear_meter","rate_per_linear_meter":<float>}}`

    Rows with missing prices are deliberately EXCLUDED so the v2 engine
    surfaces them as `WORKCENTER_RATE_MISSING` rather than silently
    defaulting to 0.

    Sprint #20 ships this function but does NOT call it from the
    orchestrator — that wiring is explicitly deferred.
    """
    owns_session = db is None
    if owns_session:
        session_ctx = db_manager.async_session_maker()
        session = await session_ctx.__aenter__()
    else:
        session = db  # type: ignore[assignment]
        session_ctx = None

    try:
        rows = (
            await session.execute(
                select(Workcenter_rates).where(
                    (Workcenter_rates.status == "active")
                    | (Workcenter_rates.is_active.is_(True))
                )
            )
        ).scalars().all()
        out: Dict[str, Any] = {}
        for r in rows:
            basis = getattr(r, "rate_basis", None) or "per_hour"
            rate_per_hour = getattr(r, "rate_per_hour", None)
            rate_per_linear_meter = getattr(r, "rate_per_linear_meter", None)
            if (
                basis == "per_hour"
                and rate_per_hour is not None
                and rate_per_hour > 0
            ):
                out[r.code] = float(rate_per_hour)
            elif (
                basis in {"per_linear_meter", "per_piece", "per_square_meter"}
                and rate_per_linear_meter is not None
                and rate_per_linear_meter > 0
            ):
                out[r.code] = {
                    "rate_basis": basis,
                    "rate_per_linear_meter": float(rate_per_linear_meter),
                    "rate_per_hour": (
                        float(rate_per_hour) if rate_per_hour is not None else None
                    ),
                }
        return out
    finally:
        if owns_session and session_ctx is not None:
            await session_ctx.__aexit__(None, None, None)


async def load_workcenter_rate_pricing_dict(
    db: Optional[AsyncSession] = None,
) -> Dict[str, Dict[str, Optional[float] | str]]:
    """Return basis-aware active pricing rows for v2 costing.

    Shape:
      {
        "CODE": {
          "rate_basis": "per_hour"|"per_linear_meter",
          "rate_per_hour": float|None,
          "rate_per_linear_meter": float|None,
        }
      }
    """
    owns_session = db is None
    if owns_session:
        session_ctx = db_manager.async_session_maker()
        session = await session_ctx.__aenter__()
    else:
        session = db  # type: ignore[assignment]
        session_ctx = None

    try:
        rows = (
            await session.execute(
                select(Workcenter_rates).where(
                    (Workcenter_rates.status == "active")
                    | (Workcenter_rates.is_active.is_(True))
                )
            )
        ).scalars().all()
        out: Dict[str, Dict[str, Optional[float] | str]] = {}
        for r in rows:
            basis = getattr(r, "rate_basis", None) or "per_hour"
            rate_per_hour = getattr(r, "rate_per_hour", None)
            rate_per_linear_meter = getattr(r, "rate_per_linear_meter", None)
            if basis == "per_hour":
                if rate_per_hour is None or rate_per_hour <= 0:
                    continue
            elif basis in {"per_linear_meter", "per_piece", "per_square_meter"}:
                if rate_per_linear_meter is None or rate_per_linear_meter <= 0:
                    continue
            else:
                continue

            out[r.code] = {
                "rate_basis": basis,
                "rate_per_hour": float(rate_per_hour) if rate_per_hour is not None else None,
                "rate_per_linear_meter": (
                    float(rate_per_linear_meter)
                    if rate_per_linear_meter is not None
                    else None
                ),
                "currency": str(getattr(r, "currency", "") or "RON").strip().upper(),
                "source": "workcenter_rates",
            }
        return out
    finally:
        if owns_session and session_ctx is not None:
            await session_ctx.__aexit__(None, None, None)