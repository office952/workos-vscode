"""Read-only externalization / reseller readiness hooks for Step 7B.1.

Declarative metadata only — no suppliers, tasks, routing, or reseller pricing.
"""

from __future__ import annotations

from typing import Any

VOLUMETRIC_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"

# operation_code -> hook metadata
OPERATION_EXTERNALIZATION_HOOKS: dict[str, dict[str, Any]] = {
    "PAINTING": {
        "code": "EXT_POWDER_COATING_RAL",
        "label": "Vopsire electrostatică / RAL",
        "module_code": "modelare_cant",
        "reason": "RAL finish can be subcontracted to a powder-coating collaborator.",
        "default_mode": "external_service_possible",
        "fallback_mode": "internal_production",
        "supplier_type": "powder_coating_partner",
        "external_partner_fallback": "collaborator_powder_coating",
        "required_machine_type": None,
        "owner_step": 9,
    },
    "return_painting": {
        "code": "EXT_RETURN_PAINTING",
        "label": "Finisaj special cant — vopsire externă",
        "module_code": "modelare_cant",
        "reason": "Return-edge special finish may be sent to external finisher.",
        "default_mode": "external_service_possible",
        "fallback_mode": "internal_production",
        "supplier_type": "finishing_partner",
        "external_partner_fallback": "collaborator_special_finish",
        "required_machine_type": None,
        "owner_step": 9,
    },
    "RETURN_PROFILE_MACHINE_FORMING": {
        "code": "EXT_PROFILE_FORMING",
        "label": "Modelare profil lateral — colaborator fallback",
        "module_code": "modelare_cant",
        "reason": "Large-volume profile forming may use external CNC partner when internal WC unavailable.",
        "default_mode": "external_service_possible",
        "fallback_mode": "internal_production",
        "supplier_type": "cnc_partner",
        "external_partner_fallback": "collaborator_cnc",
        "required_machine_type": "CNC_ROUTER",
        "owner_step": 9,
    },
    "METAL_FAB": {
        "code": "EXT_METAL_FAB_SUBCONTRACT",
        "label": "Lăcătușerie / structură metalică subcontractată",
        "module_code": "structura_suport",
        "reason": "Premount structure fabrication can be sent to metalworking collaborator.",
        "default_mode": "external_service_possible",
        "fallback_mode": "internal_production",
        "supplier_type": "metalworking_partner",
        "external_partner_fallback": "collaborator_metal_fab",
        "required_machine_type": "WC_METAL_FAB",
        "owner_step": 9,
    },
    "WC_METAL_FAB": {
        "code": "EXT_METAL_FAB_SUBCONTRACT",
        "label": "Lăcătușerie / structură metalică subcontractată",
        "module_code": "structura_suport",
        "reason": "Premount structure fabrication can be sent to metalworking collaborator.",
        "default_mode": "external_service_possible",
        "fallback_mode": "internal_production",
        "supplier_type": "metalworking_partner",
        "external_partner_fallback": "collaborator_metal_fab",
        "required_machine_type": "WC_METAL_FAB",
        "owner_step": 9,
    },
    "packaging_letters": {
        "code": "EXT_MOUNTING_SUBCONTRACT",
        "label": "Montaj / instalare subcontractată",
        "module_code": "finisaje",
        "reason": "On-site mounting may be subcontracted to installation partner.",
        "default_mode": "external_service_possible",
        "fallback_mode": "internal_production",
        "supplier_type": "installation_partner",
        "external_partner_fallback": "collaborator_mounting",
        "required_machine_type": None,
        "owner_step": 9,
    },
}

MODULE_FUTURE_EXTERNALIZATION: dict[str, dict[str, Any]] = {
    "electrica_logo": {
        "code": "EXT_ELECTRICA_LOGO",
        "label": "Electrificare logo — viitor",
        "module_code": "electrica_logo",
        "reason": "Electrical logo module reserved for future Step 8+ wiring integration.",
        "default_mode": "future_reserved",
        "owner_step": 8,
    },
}

RESELLER_PRODUCT_FUTURE: list[dict[str, Any]] = [
    {
        "product_code": "RESELL-LED-MODULE-KIT",
        "label": "Kit module LED revanzare (viitor)",
        "purchase_price_required": True,
        "supplier_required": True,
        "margin_policy_required": True,
        "internal_operations_required": False,
        "status": "future_reserved",
        "owner_step": 8,
    },
    {
        "product_code": "RESELL-PSU-12V",
        "label": "Sursă LED 12V revanzare (viitor)",
        "purchase_price_required": True,
        "supplier_required": True,
        "margin_policy_required": True,
        "internal_operations_required": False,
        "status": "future_reserved",
        "owner_step": 8,
    },
]


def get_operation_hook(operation_code: str) -> dict[str, Any] | None:
    if not operation_code:
        return None
    direct = OPERATION_EXTERNALIZATION_HOOKS.get(operation_code)
    if direct:
        return direct
    upper = OPERATION_EXTERNALIZATION_HOOKS.get(operation_code.upper())
    if upper:
        return upper
    for key, hook in OPERATION_EXTERNALIZATION_HOOKS.items():
        if key.upper() == operation_code.upper():
            return hook
    return None


def is_external_service_possible(operation_code: str, workcenter: str | None = None) -> bool:
    hook = get_operation_hook(operation_code)
    if hook and hook.get("default_mode") == "external_service_possible":
        return True
    if workcenter:
        wc_hook = get_operation_hook(workcenter)
        if wc_hook and wc_hook.get("default_mode") == "external_service_possible":
            return True
    return False
