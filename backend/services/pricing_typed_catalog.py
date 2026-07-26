"""Typed pricing catalog classification — application contract (no schema migration).

Additive metadata for Pricing Registry aggregation:
- typed_catalog: material | machine_operation | labor | service | unknown | markup_rule
- machine_family: cnc_mechanical | cnc_laser | other_machine | null
- data_quality_flags: rate_basis_column_mismatch, …
- cost_meaning: purchase_cost | reusable_rate | markup

Does not rewrite stored rates or commercial values.
"""

from __future__ import annotations

from typing import Any, Iterable, Optional

# Explicit code maps — preferred over display-name matching.
MACHINE_OPERATION_CODES: frozenset[str] = frozenset(
    {
        "CNC_ROUTER",
        "ACM_PANEL_CUTTING",
        "ACM_V_GROOVE",
        "LASER_CUTTING",
        "CONTOUR_CUTTING",
        "PANEL_CUTTING",
        "WC_METAL_FAB",
        "METAL_FAB",
        "RETURN_PROFILE_MACHINE_FORMING",
        "WELDING_BANNER",
    }
)

CNC_LASER_CODES: frozenset[str] = frozenset({"LASER_CUTTING"})

LABOR_CODES: frozenset[str] = frozenset(
    {
        "ACM_BOXED_ASSEMBLY",
        "ASSEMBLY",
        "CAPSARE",
        "ELECTRICAL_WIRING",
        "FACE_VINYL_APPLICATION_LABOR",
        "FINISHING",
        "INSTALL_PREP",
        "LED_ASSEMBLY",
        "PACKAGING",
        "PREPRESS",
        "QC_INSPECTION",
        "RETURN_CANT_RAL_PAINT_LABOR",
        "RETURN_CANT_VINYL_APPLICATION_LABOR",
        "RETURN_PROFILE_FACE_BONDING",
    }
)

SERVICE_CODES: frozenset[str] = frozenset(
    {
        "EXTERNAL_SUBCONTRACT",
        "LAMINATION",
        "LARGE_FORMAT_PRINT",
        "PAINTING",
        "SITE_INSTALLATION_STANDARD",
        "VINYL_APPLICATION",
    }
)

RATE_BASIS_MISMATCH_FLAG = "rate_basis_column_mismatch"
RATE_BASIS_MISMATCH_MESSAGE_RO = (
    "Valoarea ratei necesită verificare: unitatea declarată nu corespunde câmpului completat."
)


def classify_workcenter_typed_catalog(code: str) -> str:
    """Deterministic typed_catalog for a workcenter/operation code."""
    c = str(code or "").strip().upper()
    if not c:
        return "unknown"
    if c in MACHINE_OPERATION_CODES:
        return "machine_operation"
    if c in LABOR_CODES:
        return "labor"
    if c in SERVICE_CODES:
        return "service"
    if c.endswith("_LABOR") or "LABOR" in c:
        return "labor"
    if c.startswith("CNC_") or c.startswith("ACM_") and any(
        x in c for x in ("CUT", "GROOVE", "ROUTER", "LASER")
    ):
        return "machine_operation"
    return "unknown"


def machine_family_for_code(code: str) -> Optional[str]:
    c = str(code or "").strip().upper()
    if c in CNC_LASER_CODES or "LASER" in c:
        return "cnc_laser"
    typed = classify_workcenter_typed_catalog(c)
    if typed != "machine_operation":
        return None
    if any(x in c for x in ("CNC", "CUT", "GROOVE", "ROUTER", "PANEL_CUTTING", "CONTOUR")):
        return "cnc_mechanical"
    if c in {"WC_METAL_FAB", "METAL_FAB", "WELDING_BANNER"}:
        return "other_machine"
    return "other_machine"


def detect_rate_basis_mismatch(
    *,
    rate_basis: str | None,
    rate_per_hour: float | None,
    rate_per_linear_meter: float | None,
) -> list[str]:
    """Flag when declared basis does not match the populated storage column.

    Schema only has rate_per_hour and rate_per_linear_meter.
    per_square_meter / per_piece therefore always mismatch when a value exists.
    """
    basis = str(rate_basis or "per_hour").strip().lower()
    hour = rate_per_hour
    linear = rate_per_linear_meter
    hour_set = hour is not None
    linear_set = linear is not None

    if basis == "per_hour":
        if not hour_set and linear_set:
            return [RATE_BASIS_MISMATCH_FLAG]
        return []
    if basis == "per_linear_meter":
        if not linear_set and hour_set:
            return [RATE_BASIS_MISMATCH_FLAG]
        return []
    # Bases without a dedicated column — any stored value is a structural mismatch.
    if basis in {"per_square_meter", "per_piece", "per_set", "per_job"}:
        if hour_set or linear_set:
            return [RATE_BASIS_MISMATCH_FLAG]
        return []
    # Unknown basis with any value.
    if hour_set or linear_set:
        return [RATE_BASIS_MISMATCH_FLAG]
    return []


def cost_meaning_for_typed_catalog(typed_catalog: str) -> str:
    if typed_catalog == "material":
        return "purchase_cost"
    if typed_catalog == "markup_rule":
        return "markup"
    return "reusable_rate"


def enrich_material_item(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    out["typed_catalog"] = "material"
    out["machine_family"] = None
    out["data_quality_flags"] = list(out.get("data_quality_flags") or [])
    out["cost_meaning"] = "purchase_cost"
    out["cost_label_ro"] = "Cost achiziție"
    return out


def enrich_workcenter_item(
    item: dict[str, Any],
    *,
    rate_basis: str | None,
    rate_per_hour: float | None,
    rate_per_linear_meter: float | None,
) -> dict[str, Any]:
    out = dict(item)
    code = str(out.get("pricing_code") or "")
    typed = classify_workcenter_typed_catalog(code)
    flags = detect_rate_basis_mismatch(
        rate_basis=rate_basis,
        rate_per_hour=rate_per_hour,
        rate_per_linear_meter=rate_per_linear_meter,
    )
    out["typed_catalog"] = typed
    out["machine_family"] = machine_family_for_code(code)
    out["data_quality_flags"] = flags
    out["cost_meaning"] = cost_meaning_for_typed_catalog(typed)
    out["cost_label_ro"] = "Rată calcul"
    if RATE_BASIS_MISMATCH_FLAG in flags:
        out["data_quality_message_ro"] = RATE_BASIS_MISMATCH_MESSAGE_RO
    return out


def enrich_markup_item(item: dict[str, Any]) -> dict[str, Any]:
    out = dict(item)
    out["typed_catalog"] = "markup_rule"
    out["machine_family"] = None
    out["data_quality_flags"] = []
    out["cost_meaning"] = "markup"
    out["cost_label_ro"] = "Adaos comercial"
    return out


def count_by_typed_catalog(items: Iterable[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        key = str(item.get("typed_catalog") or "unknown")
        counts[key] = counts.get(key, 0) + 1
    return counts
