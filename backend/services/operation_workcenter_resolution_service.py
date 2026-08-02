"""Canonical operation → workcenter resolution (DEC-010).

Source of truth: ``operation_resource_requirements`` (+ product_system_aliases).
Not Pricing / workcenter_rates / UI labels / materializer invention.

Resolution (owner-correct):
  operation identity
  → ORR direct code or explicit alias
  → exactly one allowed_workcenter_code → resolved
  → multiple allowed → ambiguous (fail-closed null)
  → none / missing mapping → source_missing null
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Literal, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.operational_registry import OperationResourceRequirement
from schemas.product_aggregate import ProductAggregate, ProductAggregateOperation

WorkcenterResolutionStatus = Literal[
    "resolved",
    "source_missing",
    "ambiguous",
    "not_required",
    "inactive",
]

MAPPING_REGISTRY = "operation_resource_requirements"
MAPPING_VERSION = "orr/v1"


@dataclass(frozen=True)
class WorkcenterResolution:
    workcenter_code: str | None
    status: WorkcenterResolutionStatus
    mapping_source: str | None
    registry_operation_code: str | None
    matched_alias: str | None
    warning: str | None = None


def _parse_json_list(raw: Any) -> list[str]:
    if raw is None:
        return []
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            return []
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return [text] if text else []
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    return []


def normalize_orr_mapping_row(row: Any) -> dict[str, Any]:
    """Normalize ORM row or dict into a stable mapping record."""
    if isinstance(row, dict):
        op = str(row.get("operation_code") or "").strip()
        return {
            "operation_code": op,
            "allowed_workcenter_codes": _parse_json_list(
                row.get("allowed_workcenter_codes")
            ),
            "product_system_aliases": _parse_json_list(
                row.get("product_system_aliases")
            ),
            "updated_at": str(row.get("updated_at") or "") or None,
        }
    return {
        "operation_code": str(getattr(row, "operation_code", "") or "").strip(),
        "allowed_workcenter_codes": _parse_json_list(
            getattr(row, "allowed_workcenter_codes", None)
        ),
        "product_system_aliases": _parse_json_list(
            getattr(row, "product_system_aliases", None)
        ),
        "updated_at": str(getattr(row, "updated_at", "") or "") or None,
    }


def find_orr_mapping(
    operation_code: str,
    mappings: Sequence[dict[str, Any]],
) -> tuple[dict[str, Any] | None, str | None, str]:
    """Return (mapping, matched_alias, resolution_kind)."""
    code = (operation_code or "").strip()
    if not code:
        return None, None, "missing"
    code_lower = code.lower()
    for m in mappings:
        if str(m.get("operation_code") or "").strip().lower() == code_lower:
            return m, None, "direct"
    for m in mappings:
        for alias in m.get("product_system_aliases") or []:
            if str(alias).strip().lower() == code_lower:
                return m, str(alias).strip(), "alias"
    return None, None, "missing"


def resolve_workcenter_for_operation(
    operation_code: str,
    mappings: Sequence[dict[str, Any]],
    *,
    active_workcenter_codes: set[str] | None = None,
) -> WorkcenterResolution:
    """Deterministic fail-closed workcenter resolution for one operation code."""
    mapping, matched_alias, kind = find_orr_mapping(operation_code, mappings)
    if mapping is None:
        return WorkcenterResolution(
            workcenter_code=None,
            status="source_missing",
            mapping_source=None,
            registry_operation_code=None,
            matched_alias=None,
            warning="WORKCENTER_MAPPING_SOURCE_MISSING",
        )

    reg_op = str(mapping.get("operation_code") or "").strip()
    allowed = [
        str(c).strip()
        for c in (mapping.get("allowed_workcenter_codes") or [])
        if str(c).strip()
    ]
    # Explicit empty allow-list with a registered operation → not required.
    if not allowed:
        return WorkcenterResolution(
            workcenter_code=None,
            status="not_required",
            mapping_source=f"{MAPPING_REGISTRY}:{kind}:{reg_op}",
            registry_operation_code=reg_op,
            matched_alias=matched_alias,
            warning="WORKCENTER_NOT_REQUIRED",
        )

    unique = sorted(set(allowed))
    if len(unique) > 1:
        return WorkcenterResolution(
            workcenter_code=None,
            status="ambiguous",
            mapping_source=f"{MAPPING_REGISTRY}:{kind}:{reg_op}",
            registry_operation_code=reg_op,
            matched_alias=matched_alias,
            warning=f"WORKCENTER_MAPPING_AMBIGUOUS:{','.join(unique)}",
        )

    wc = unique[0]
    source = f"{MAPPING_REGISTRY}:{kind}:{reg_op}->{wc}"
    if matched_alias:
        source = f"{source}|alias={matched_alias}"
    source = f"{source}|{MAPPING_VERSION}"

    if active_workcenter_codes is not None and wc not in active_workcenter_codes:
        # Still stamp the canonical WC — capacity/machine gap is informative.
        return WorkcenterResolution(
            workcenter_code=wc,
            status="resolved",
            mapping_source=source,
            registry_operation_code=reg_op,
            matched_alias=matched_alias,
            warning="WORKCENTER_NO_ACTIVE_MACHINE",
        )

    return WorkcenterResolution(
        workcenter_code=wc,
        status="resolved",
        mapping_source=source,
        registry_operation_code=reg_op,
        matched_alias=matched_alias,
        warning=None,
    )


async def load_orr_mappings(db: AsyncSession) -> list[dict[str, Any]]:
    rows = (
        await db.execute(
            select(OperationResourceRequirement).order_by(
                OperationResourceRequirement.operation_code.asc()
            )
        )
    ).scalars().all()
    return [normalize_orr_mapping_row(r) for r in rows]


async def load_active_workcenter_codes(db: AsyncSession) -> set[str]:
    """Workcenter codes that have at least one active/available machine (informational)."""
    from models.operational_registry import MachineRegistry

    rows = (
        await db.execute(
            select(MachineRegistry.workcenter_code).where(
                MachineRegistry.workcenter_code.is_not(None),
                MachineRegistry.is_active.is_(True),
            )
        )
    ).scalars().all()
    return {str(c).strip() for c in rows if str(c).strip()}


def apply_workcenter_resolution_to_aggregate(
    aggregate: ProductAggregate,
    mappings: Sequence[dict[str, Any]],
    *,
    active_workcenter_codes: set[str] | None = None,
) -> ProductAggregate:
    """Stamp ORR-resolved workcenter onto Aggregate operations (freeze-time).

    Does not invent workcenters. Does not read Pricing. Idempotent when unchanged.
    """
    # Ensure task-rule priced ops exist as operations so EP can bind WC.
    op_by_code = {
        str(op.operation_code or "").strip().lower(): op for op in aggregate.operations
    }
    extra: list[ProductAggregateOperation] = []
    for rule in aggregate.task_contract.task_rules or []:
        priced = str(rule.priced_operation or "").strip()
        if not priced:
            continue
        key = priced.lower()
        if key in op_by_code:
            continue
        extra.append(
            ProductAggregateOperation(
                operation_code=priced,
                label=rule.task_name,
                workcenter=None,
                priced=True,
                provenance="derived",
                source_template_code=aggregate.template_code,
                mini_module_code=rule.mini_module_code,
                status="present",
            )
        )
        op_by_code[key] = extra[-1]

    ops = list(aggregate.operations) + extra
    patched: list[ProductAggregateOperation] = []
    notes = list(aggregate.task_contract.notes or [])
    note_prefix = "workcenter_resolution=operation_resource_requirements"

    for op in ops:
        code = str(op.operation_code or "").strip()
        resolution = resolve_workcenter_for_operation(
            code,
            mappings,
            active_workcenter_codes=active_workcenter_codes,
        )
        update: dict[str, Any] = {
            "workcenter": resolution.workcenter_code,
            "workcenter_resolution_status": resolution.status,
            "workcenter_mapping_source": resolution.mapping_source,
        }
        # Preserve explicit freeze-time WC only when ORR has no mapping and op already set.
        if (
            resolution.status == "source_missing"
            and op.workcenter
            and str(op.workcenter).strip()
        ):
            # Template-stamped WC without ORR proof → clear (fail-closed; no invent/legacy label).
            update["workcenter"] = None
            update["workcenter_resolution_status"] = "source_missing"
            update["workcenter_mapping_source"] = None

        patched.append(op.model_copy(update=update))
        if resolution.warning and resolution.warning not in notes:
            notes.append(f"{note_prefix}:{code}:{resolution.warning}")

    if note_prefix not in "".join(notes):
        notes.append(f"{note_prefix}|{MAPPING_VERSION}")

    return aggregate.model_copy(
        update={
            "operations": patched,
            "task_contract": aggregate.task_contract.model_copy(update={"notes": notes}),
        }
    )
