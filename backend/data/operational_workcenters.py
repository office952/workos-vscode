"""Canonical operational workcenter codes (workforce / Machines registry).

Source of truth for code *identity* (not rates, not Pricing):
- ``seeds/seed_operational_workforce_registry.py``
- ``services.shared_cnc_operation_model.REGISTRY_CNC_WORKCENTER_CODE``

``WC_CNC`` is a legacy/transitional conflict token (parity VALUE_CONFLICT vs
``WC_CNC_ROUTING``). It is NOT an accepted operational stamp.
"""

from __future__ import annotations

# Mirrors seed_operational_workforce_registry + REGISTRY_CNC_WORKCENTER_CODE.
CANONICAL_WORKCENTER_CODES: frozenset[str] = frozenset(
    {
        # CNC / letters / metal / assembly (volumetric pilot)
        "WC_CNC_ROUTING",
        "WC_LETTER_FORMING",
        "WC_METAL_FAB",
        "WC_ASSEMBLY",
        "WC_LED_ASSEMBLY",
        "WC_VINYL_APPLICATION",
        "WC_FIELD_INSTALLATION",
        # Print / prep (same workforce seed registry)
        "WC_PRINT",
        "WC_LAMINATE",
        "WC_CUT",
        "WC_LASER_CUTTING",
        "WC_PREPRESS",
    }
)

# Known non-canonical codes that must never be treated as registry-valid.
NON_CANONICAL_WORKCENTER_CODES: frozenset[str] = frozenset(
    {
        "WC_CNC",  # conflict with WC_CNC_ROUTING — do not alias silently
    }
)

CANONICAL_CNC_WORKCENTER = "WC_CNC_ROUTING"


def normalize_workcenter_code(code: str | None) -> str:
    return str(code or "").strip().upper()


def is_canonical_workcenter_code(code: str | None) -> bool:
    raw = str(code or "").strip()
    if not raw:
        return False
    return raw in CANONICAL_WORKCENTER_CODES


def workcenter_registry_status(code: str | None) -> str:
    """Return resolved | missing | non_canonical | empty."""
    raw = str(code or "").strip()
    if not raw:
        return "empty"
    if raw in NON_CANONICAL_WORKCENTER_CODES:
        return "non_canonical"
    if raw in CANONICAL_WORKCENTER_CODES:
        return "resolved"
    return "missing"
