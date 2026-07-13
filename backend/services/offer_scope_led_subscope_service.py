"""LIGHTING / ELECTRICAL sold-scope split within comp_led_litere / sistem_led."""

from __future__ import annotations

from typing import Any, Literal

from services.offer_scope_resolver_service import extract_offer_scope, resolve_offer_scope

LedSubscope = Literal["LIGHTING", "ELECTRICAL"]

LIGHTING_MATERIAL_KEYS: frozenset[str] = frozenset(
    {
        "led_modules",
        "adhesive_led_modules",
    }
)
ELECTRICAL_MATERIAL_KEYS: frozenset[str] = frozenset(
    {
        "wire_letters_myyup_2x075",
        "wire_supply_myyup_2x15",
    }
)

LIGHTING_OPERATIONS: frozenset[str] = frozenset({"led_install_letters"})
ELECTRICAL_OPERATIONS: frozenset[str] = frozenset({"electrical_letters"})

LIGHTING_TASK_NAMES: frozenset[str] = frozenset({"led_installation"})
ELECTRICAL_TASK_NAMES: frozenset[str] = frozenset({"electrical_wiring"})

LIGHTING_LOGICAL_LINE_IDS: frozenset[str] = frozenset(
    {"material.led_modules", "material.adhesive_led"}
)
ELECTRICAL_LOGICAL_LINE_IDS: frozenset[str] = frozenset(
    {"material.led_psu", "material.wire_letters", "material.wire_supply"}
)

# Runtime mini_module_code alias — electrical assembly lives under electrica_litere in dossier.
LED_RUNTIME_MODULE_ALIASES: dict[str, str] = {
    "electrica_litere": "sistem_led",
}

LIGHTING_COMMERCIAL_LINE_CODES: frozenset[str] = frozenset({"sistem_led_module"})
ELECTRICAL_COMMERCIAL_LINE_CODES: frozenset[str] = frozenset({"sursa_led"})
LIGHTING_EIC_LINE_CODES: frozenset[str] = frozenset({"sistem_led_install"})
ELECTRICAL_EIC_LINE_CODES: frozenset[str] = frozenset({"sursa_led"})


def sold_led_subscopes_from_canonical(canonical_sold: set[str] | frozenset[str]) -> frozenset[LedSubscope]:
    return frozenset(code for code in ("LIGHTING", "ELECTRICAL") if code in canonical_sold)


def resolve_sold_led_subscopes(
    payload_raw: dict,
    quote_input: dict | None = None,
) -> frozenset[LedSubscope] | None:
    """None when legacy full product or no LED canonical scopes in subset."""
    scope = extract_offer_scope(payload_raw, quote_input)
    resolved = resolve_offer_scope(scope)
    if resolved.use_legacy or resolved.validation_errors:
        return None
    led = sold_led_subscopes_from_canonical(resolved.canonical_sold_modules)
    return led if led else None


def material_led_subscope(material_key: str | None) -> LedSubscope | None:
    key = str(material_key or "").strip().lower()
    if not key:
        return None
    if key in LIGHTING_MATERIAL_KEYS:
        return "LIGHTING"
    if key.startswith("led_psu") or key in ELECTRICAL_MATERIAL_KEYS:
        return "ELECTRICAL"
    if key == "led_total_watts":
        return None
    return None


def led_runtime_module_bucket(mini_module_code: str | None) -> str | None:
    code = str(mini_module_code or "").strip()
    if not code:
        return None
    return LED_RUNTIME_MODULE_ALIASES.get(code, code)


def partial_led_subscope_filter(
    canonical_sold: set[str] | frozenset[str],
) -> frozenset[LedSubscope] | None:
    """Return active LED subscopes when subset filtering applies; None for full union/legacy."""
    led = sold_led_subscopes_from_canonical(canonical_sold)
    if not led or len(led) >= 2:
        return None
    return led


def aggregate_material_led_subscope(material_code: str | None) -> LedSubscope | None:
    code = str(material_code or "").strip().upper()
    if not code:
        return None
    if code == "MAT-LED-MODULE":
        return "LIGHTING"
    if code.startswith("MAT-LED-PSU"):
        return "ELECTRICAL"
    if code.startswith("MAT-CABLU-MYYUP") or code == "MAT-CABLU-ELECTRIC":
        return "ELECTRICAL"
    return None


def commercial_line_led_subscope(line_code: str | None) -> LedSubscope | None:
    code = str(line_code or "").strip()
    if code in LIGHTING_COMMERCIAL_LINE_CODES:
        return "LIGHTING"
    if code in ELECTRICAL_COMMERCIAL_LINE_CODES:
        return "ELECTRICAL"
    return None


def eic_line_led_subscope(line_code: str | None) -> LedSubscope | None:
    code = str(line_code or "").strip()
    if code in LIGHTING_EIC_LINE_CODES:
        return "LIGHTING"
    if code in ELECTRICAL_EIC_LINE_CODES:
        return "ELECTRICAL"
    return None


def operation_led_subscope(operation_code: str | None) -> LedSubscope | None:
    code = str(operation_code or "").strip().lower()
    if code in LIGHTING_OPERATIONS:
        return "LIGHTING"
    if code in ELECTRICAL_OPERATIONS:
        return "ELECTRICAL"
    return None


def task_rule_led_subscope(*, priced_operation: str | None, task_name: str | None) -> LedSubscope | None:
    op_scope = operation_led_subscope(priced_operation)
    if op_scope:
        return op_scope
    name = str(task_name or "").strip().lower()
    if name in LIGHTING_TASK_NAMES:
        return "LIGHTING"
    if name in ELECTRICAL_TASK_NAMES:
        return "ELECTRICAL"
    return None


def logical_list_line_led_subscope(line_id: str | None) -> LedSubscope | None:
    token = str(line_id or "").strip()
    if token in LIGHTING_LOGICAL_LINE_IDS:
        return "LIGHTING"
    if token in ELECTRICAL_LOGICAL_LINE_IDS:
        return "ELECTRICAL"
    return None


def led_subscope_row_allowed(
    row_subscope: LedSubscope | None,
    *,
    sold_led_subscopes: frozenset[LedSubscope] | None,
) -> bool:
    if sold_led_subscopes is None:
        return True
    if row_subscope is None:
        return True
    return row_subscope in sold_led_subscopes


def led_consumer_row_allowed(
    *,
    row_subscope: LedSubscope | None,
    sold_led_subscopes: frozenset[LedSubscope] | None,
    material_key: str | None = None,
    operation_code: str | None = None,
    line_id: str | None = None,
    eic_line_code: str | None = None,
    commercial_line_code: str | None = None,
    priced_operation: str | None = None,
    task_name: str | None = None,
    mount_decision: Any | None = None,
) -> bool:
    """Combine LIGHTING/ELECTRICAL subscope filter with mount consumer gating."""
    from services.lighting_mount_consumer_service import (
        LightingMountConsumerDecision,
        lighting_mount_commercial_line_allowed,
        lighting_mount_eic_line_allowed,
        lighting_mount_logical_line_allowed,
        lighting_mount_material_allowed,
        lighting_mount_operation_allowed,
        lighting_mount_task_allowed,
    )

    if not led_subscope_row_allowed(row_subscope, sold_led_subscopes=sold_led_subscopes):
        return False
    if mount_decision is None or (
        isinstance(mount_decision, LightingMountConsumerDecision) and mount_decision.use_legacy
    ):
        return True
    if material_key is not None and not lighting_mount_material_allowed(material_key, decision=mount_decision):
        return False
    if operation_code is not None and not lighting_mount_operation_allowed(operation_code, decision=mount_decision):
        return False
    if line_id is not None and not lighting_mount_logical_line_allowed(line_id, decision=mount_decision):
        return False
    if eic_line_code is not None and not lighting_mount_eic_line_allowed(eic_line_code, decision=mount_decision):
        return False
    if commercial_line_code is not None and not lighting_mount_commercial_line_allowed(
        commercial_line_code, decision=mount_decision
    ):
        return False
    if (priced_operation is not None or task_name is not None) and not lighting_mount_task_allowed(
        priced_operation=priced_operation,
        task_name=task_name,
        decision=mount_decision,
    ):
        return False
    return True
