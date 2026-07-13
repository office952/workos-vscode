"""Shared LED mount consumer decision — adhesive / install gating for LIGHTING sold scope."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from data.product_dependency_bindings_volumetric_letters_v2 import PRODUCT_DEPENDENCY_BINDINGS
from services.offer_scope_resolver_service import extract_offer_scope, resolve_offer_scope
from services.sold_scope_dependency_validator_service import (
    CODE_LED_INSTALLATION_BY_US,
    CODE_LED_MOUNT_SURFACE_NOT_SOLD,
    _binding_for_template,
    _capability_satisfied,
    _read_dependency_confirmations,
)
from data.component_dependency_contract_v1 import LED_MOUNT_SURFACE

REASON_LIGHTING_NOT_SOLD = "lighting_not_sold"
REASON_LEGACY_FULL_PRODUCT = "legacy_full_product"
REASON_SOLD_MOUNT_PROVIDER = "sold_mount_provider"
REASON_EXTERNAL_MOUNT_CONFIRMED = "external_mount_confirmed"
REASON_INSTALLATION_BY_US_CONFIRMED = "installation_by_us_confirmed"
REASON_MOUNT_UNSATISFIED = "mount_surface_unsatisfied"
REASON_INSTALLATION_NOT_BY_US = "installation_not_by_us"


@dataclass(frozen=True)
class LightingMountConsumerDecision:
    lighting_sold: bool
    mount_surface_satisfied: bool
    sold_mount_provider: bool
    external_mount_confirmed: bool
    installation_by_us: bool
    include_led_modules: bool
    include_led_adhesive: bool
    include_led_install_operation: bool
    include_led_install_task: bool
    reason_codes: tuple[str, ...]
    use_legacy: bool = False


def _sold_mount_provider(sold: set[str], template_code: str | None) -> bool:
    binding = _binding_for_template(template_code)
    if binding is None:
        return False
    return _capability_satisfied(LED_MOUNT_SURFACE, sold, binding)


def _resolve_template_code(payload_raw: dict[str, Any] | None) -> str | None:
    if not isinstance(payload_raw, dict):
        return None
    binding = payload_raw.get("product_binding")
    if isinstance(binding, dict):
        code = binding.get("template_code")
        return str(code).strip() if code else None
    return None


def resolve_lighting_mount_consumers(
    payload_raw: dict[str, Any] | None,
    quote_input: dict[str, Any] | None = None,
    *,
    template_code: str | None = None,
    dependency_confirmations: set[str] | None = None,
) -> LightingMountConsumerDecision | None:
    """Deterministic consumer flags from sold scope + dependency validation + confirmations.

    Returns None for legacy full_product (all consumers allowed when illuminated).
    """
    scope = extract_offer_scope(payload_raw if isinstance(payload_raw, dict) else None, quote_input)
    resolved = resolve_offer_scope(scope)
    if resolved.use_legacy:
        return LightingMountConsumerDecision(
            lighting_sold=True,
            mount_surface_satisfied=True,
            sold_mount_provider=True,
            external_mount_confirmed=False,
            installation_by_us=True,
            include_led_modules=True,
            include_led_adhesive=True,
            include_led_install_operation=True,
            include_led_install_task=True,
            reason_codes=(REASON_LEGACY_FULL_PRODUCT,),
            use_legacy=True,
        )

    sold = {str(code).strip() for code in resolved.canonical_sold_modules if str(code).strip()}
    if "LIGHTING" not in sold:
        return LightingMountConsumerDecision(
            lighting_sold=False,
            mount_surface_satisfied=False,
            sold_mount_provider=False,
            external_mount_confirmed=False,
            installation_by_us=False,
            include_led_modules=False,
            include_led_adhesive=False,
            include_led_install_operation=False,
            include_led_install_task=False,
            reason_codes=(REASON_LIGHTING_NOT_SOLD,),
            use_legacy=False,
        )

    tpl = template_code or _resolve_template_code(payload_raw if isinstance(payload_raw, dict) else None)
    if tpl is None:
        tpl = "TPL-VOLUMETRIC-LETTERS_v2"
    confirmations = (
        set(dependency_confirmations)
        if dependency_confirmations is not None
        else _read_dependency_confirmations(payload_raw if isinstance(payload_raw, dict) else None)
    )

    sold_provider = _sold_mount_provider(sold, tpl)
    external_confirmed = CODE_LED_MOUNT_SURFACE_NOT_SOLD in confirmations
    install_confirmed = CODE_LED_INSTALLATION_BY_US in confirmations
    mount_satisfied = sold_provider or external_confirmed
    installation_by_us = sold_provider or install_confirmed

    reasons: list[str] = []
    if sold_provider:
        reasons.append(REASON_SOLD_MOUNT_PROVIDER)
    if external_confirmed:
        reasons.append(REASON_EXTERNAL_MOUNT_CONFIRMED)
    if install_confirmed:
        reasons.append(REASON_INSTALLATION_BY_US_CONFIRMED)
    if not mount_satisfied:
        reasons.append(REASON_MOUNT_UNSATISFIED)
    if mount_satisfied and not installation_by_us:
        reasons.append(REASON_INSTALLATION_NOT_BY_US)

    include_modules = True
    include_adhesive = installation_by_us
    include_install = installation_by_us

    return LightingMountConsumerDecision(
        lighting_sold=True,
        mount_surface_satisfied=mount_satisfied,
        sold_mount_provider=sold_provider,
        external_mount_confirmed=external_confirmed,
        installation_by_us=installation_by_us,
        include_led_modules=include_modules,
        include_led_adhesive=include_adhesive,
        include_led_install_operation=include_install,
        include_led_install_task=include_install,
        reason_codes=tuple(reasons),
        use_legacy=False,
    )


def resolve_lighting_mount_consumers_from_snapshot(
    *,
    mode: str,
    canonical_sold_modules: frozenset[str] | set[str],
    dependency_confirmations: frozenset[str] | set[str] | None = None,
    template_code: str | None = "TPL-VOLUMETRIC-LETTERS_v2",
) -> LightingMountConsumerDecision | None:
    """Execution/quote snapshot path — no resolver rerun."""
    if mode == "full_product":
        return LightingMountConsumerDecision(
            lighting_sold=True,
            mount_surface_satisfied=True,
            sold_mount_provider=True,
            external_mount_confirmed=False,
            installation_by_us=True,
            include_led_modules=True,
            include_led_adhesive=True,
            include_led_install_operation=True,
            include_led_install_task=True,
            reason_codes=(REASON_LEGACY_FULL_PRODUCT,),
            use_legacy=True,
        )

    sold = {str(code).strip() for code in canonical_sold_modules if str(code).strip()}
    confirmations = set(dependency_confirmations or ())
    payload_stub = {
        "offer_scope": {"mode": mode, "sold_modules": sorted(sold)},
        "offer_scope_confirmed": {"dependency_confirmations": sorted(confirmations)},
    }
    return resolve_lighting_mount_consumers(
        payload_stub,
        None,
        template_code=template_code,
        dependency_confirmations=confirmations,
    )


def lighting_mount_material_allowed(
    material_key: str | None,
    *,
    decision: LightingMountConsumerDecision | None,
) -> bool:
    if decision is None or decision.use_legacy:
        return True
    key = str(material_key or "").strip().lower()
    if key == "adhesive_led_modules":
        return decision.include_led_adhesive
    if key == "led_modules":
        return decision.include_led_modules
    return True


def lighting_mount_operation_allowed(
    operation_code: str | None,
    *,
    decision: LightingMountConsumerDecision | None,
) -> bool:
    if decision is None or decision.use_legacy:
        return True
    code = str(operation_code or "").strip().lower()
    if code == "led_install_letters":
        return decision.include_led_install_operation
    return True


def lighting_mount_task_allowed(
    *,
    priced_operation: str | None = None,
    task_name: str | None = None,
    decision: LightingMountConsumerDecision | None,
) -> bool:
    if decision is None or decision.use_legacy:
        return True
    op = str(priced_operation or "").strip().lower()
    name = str(task_name or "").strip().lower()
    if op == "led_install_letters" or name == "led_installation":
        return decision.include_led_install_task
    return True


def lighting_mount_logical_line_allowed(
    line_id: str | None,
    *,
    decision: LightingMountConsumerDecision | None,
) -> bool:
    if decision is None or decision.use_legacy:
        return True
    token = str(line_id or "").strip()
    if token == "material.adhesive_led":
        return decision.include_led_adhesive
    return True


def lighting_mount_eic_line_allowed(
    line_code: str | None,
    *,
    decision: LightingMountConsumerDecision | None,
) -> bool:
    if decision is None or decision.use_legacy:
        return True
    code = str(line_code or "").strip()
    if code == "sistem_led_install":
        return decision.include_led_install_operation
    return True


def lighting_mount_commercial_line_allowed(
    line_code: str | None,
    *,
    decision: LightingMountConsumerDecision | None,
) -> bool:
    if decision is None or decision.use_legacy:
        return True
    code = str(line_code or "").strip()
    if code == "sistem_led_module":
        return decision.include_led_modules
    return True
