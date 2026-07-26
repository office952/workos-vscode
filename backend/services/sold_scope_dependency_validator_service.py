"""Validate sold component graphs using declarative contracts and product bindings."""

from __future__ import annotations

import os
from typing import Any

from data.component_dependency_contract_v1 import (
    LED_MOUNT_SURFACE,
    SLICE1_COMPONENT_REQUIREMENTS,
)
from data.offer_scope_canonical_map import derive_calc_modules
from data.product_dependency_bindings_volumetric_letters_v2 import (
    PRODUCT_DEPENDENCY_BINDINGS,
    CapabilityProvider,
    ProductDependencyBinding,
)
from schemas.offer_scope import OfferScopeInput
from schemas.sold_scope_dependency import (
    SoldScopeDependencyIssue,
    SoldScopeDependencyValidationResult,
)
from services.offer_scope_resolver_service import resolve_offer_scope

CODE_SOLD_MODULES_EMPTY = "SOLD_MODULES_EMPTY"
CODE_LED_MOUNT_SURFACE_NOT_SOLD = "LED_MOUNT_SURFACE_NOT_SOLD"
CODE_LED_INSTALLATION_BY_US = "LED_INSTALLATION_BY_US"
CODE_ELECTRICAL_LOAD_NOT_SOLD = "ELECTRICAL_LOAD_NOT_SOLD"

MSG_LED_MOUNT = (
    "Iluminarea necesita o suprafata de montaj. "
    "Confirma ca suportul este existent sau furnizat de client."
)
MSG_ELECTRICAL_LOAD = (
    "Electrica este selectata fara Iluminare. "
    "Confirma ca sarcina LED este existenta sau furnizata separat."
)


def is_offer_scope_dependency_strict() -> bool:
    try:
        from core.config import settings

        if getattr(settings, "offer_scope_dependency_strict", False):
            return True
    except Exception:
        pass
    raw = os.environ.get("OFFER_SCOPE_DEPENDENCY_STRICT", "0").strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _binding_for_template(template_code: str | None) -> ProductDependencyBinding | None:
    if not template_code:
        return None
    return PRODUCT_DEPENDENCY_BINDINGS.get(template_code)


def _capability_satisfied(capability: str, sold: set[str], binding: ProductDependencyBinding | None) -> bool:
    if binding is None:
        return True
    providers = binding.capability_providers.get(capability, ())
    return any(provider.satisfied_by(sold) for provider in providers)


def _read_dependency_confirmations(payload_raw: dict[str, Any] | None) -> set[str]:
    if not isinstance(payload_raw, dict):
        return set()
    confirmed = payload_raw.get("offer_scope_confirmed")
    if not isinstance(confirmed, dict):
        return set()
    codes = confirmed.get("dependency_confirmations")
    if isinstance(codes, list):
        return {str(code).strip() for code in codes if str(code).strip()}
    if isinstance(codes, dict):
        return {str(key).strip() for key, value in codes.items() if value}
    return set()


def _issue_confirmed(code: str, confirmations: set[str]) -> bool:
    return code in confirmations


def validate_sold_graph(
    *,
    mode: str,
    sold_modules: list[str],
    template_code: str | None = None,
    dependency_confirmations: set[str] | None = None,
    strict: bool | None = None,
) -> SoldScopeDependencyValidationResult:
    """Rule-driven sold graph validation — not a hardcoded 32-case map."""
    strict_mode = is_offer_scope_dependency_strict() if strict is None else strict
    sold = {str(code).strip() for code in sold_modules if str(code).strip()}
    confirmations = set(dependency_confirmations or [])
    binding = _binding_for_template(template_code)

    blockers: list[SoldScopeDependencyIssue] = []
    confirmations_required: list[SoldScopeDependencyIssue] = []
    warnings: list[SoldScopeDependencyIssue] = []
    satisfied_capabilities: list[str] = []
    missing_capabilities: list[str] = []

    if mode == "full_product":
        return SoldScopeDependencyValidationResult(
            valid=True,
            valid_for_save=True,
            valid_for_confirmation=True,
            resolved_calc_modules=[],
        )

    resolved = resolve_offer_scope(
        OfferScopeInput(
            contract_version="offer_scope_contract/v1",
            mode="component_subset",
            sold_modules=sorted(sold),
        )
    )
    for error in resolved.validation_errors:
        blockers.append(
            SoldScopeDependencyIssue(
                severity="blocker",
                code=str(error),
                message="Selecteaza cel putin o componenta pentru scope partial.",
            )
        )

    if not sold:
        result = SoldScopeDependencyValidationResult(
            valid=False,
            valid_for_save=False,
            valid_for_confirmation=False,
            blockers=blockers,
            resolved_calc_modules=[],
        )
        return result

    calc_modules = derive_calc_modules(sorted(sold))

    if "LIGHTING" in sold:
        if _capability_satisfied(LED_MOUNT_SURFACE, sold, binding):
            satisfied_capabilities.append(LED_MOUNT_SURFACE)
        else:
            missing_capabilities.append(LED_MOUNT_SURFACE)
            if not _issue_confirmed(CODE_LED_MOUNT_SURFACE_NOT_SOLD, confirmations):
                confirmations_required.append(
                    SoldScopeDependencyIssue(
                        severity="confirmation_required",
                        code=CODE_LED_MOUNT_SURFACE_NOT_SOLD,
                        message=MSG_LED_MOUNT,
                        capability=LED_MOUNT_SURFACE,
                    )
                )

    if "ELECTRICAL" in sold and "LIGHTING" not in sold:
        if not _issue_confirmed(CODE_ELECTRICAL_LOAD_NOT_SOLD, confirmations):
            confirmations_required.append(
                SoldScopeDependencyIssue(
                    severity="confirmation_required",
                    code=CODE_ELECTRICAL_LOAD_NOT_SOLD,
                    message=MSG_ELECTRICAL_LOAD,
                )
            )
            warnings.append(
                SoldScopeDependencyIssue(
                    severity="warning",
                    code=CODE_ELECTRICAL_LOAD_NOT_SOLD,
                    message=MSG_ELECTRICAL_LOAD,
                )
            )

    unresolved_confirmations = len(confirmations_required) > 0
    has_blockers = len(blockers) > 0

    valid_for_confirmation = not has_blockers and not unresolved_confirmations
    valid_for_save = valid_for_confirmation if strict_mode else not has_blockers

    return SoldScopeDependencyValidationResult(
        valid=not has_blockers and not unresolved_confirmations,
        valid_for_save=valid_for_save,
        valid_for_confirmation=valid_for_confirmation,
        blockers=blockers,
        confirmations_required=confirmations_required,
        warnings=warnings,
        satisfied_capabilities=satisfied_capabilities,
        missing_capabilities=missing_capabilities,
        resolved_calc_modules=calc_modules,
    )


def validate_sold_graph_from_payload(payload_raw: dict[str, Any] | None) -> SoldScopeDependencyValidationResult:
    if not isinstance(payload_raw, dict):
        return SoldScopeDependencyValidationResult(valid=True, valid_for_save=True, valid_for_confirmation=True)

    scope = payload_raw.get("offer_scope")
    if not isinstance(scope, dict):
        return SoldScopeDependencyValidationResult(valid=True, valid_for_save=True, valid_for_confirmation=True)

    mode = str(scope.get("mode") or "full_product")
    sold_modules = scope.get("sold_modules")
    if not isinstance(sold_modules, list):
        sold_modules = []

    template_code = None
    binding = payload_raw.get("product_binding")
    if isinstance(binding, dict):
        template_code = binding.get("template_code")

    confirmations = _read_dependency_confirmations(payload_raw)
    return validate_sold_graph(
        mode=mode,
        sold_modules=[str(code) for code in sold_modules],
        template_code=str(template_code) if template_code else None,
        dependency_confirmations=confirmations,
    )


def sync_offer_scope_dependency_validation(payload_raw: dict[str, Any]) -> SoldScopeDependencyValidationResult:
    """Compute validation and attach to workspace payload for UI consumption."""
    result = validate_sold_graph_from_payload(payload_raw)
    payload_raw["offer_scope_dependency_validation"] = result.model_dump(mode="json")
    return result


def merge_dependency_confirmations(
    payload_raw: dict[str, Any],
    *,
    new_codes: list[str] | None,
    sold_modules_changed: bool,
) -> None:
    confirmed = payload_raw.get("offer_scope_confirmed")
    if not isinstance(confirmed, dict):
        confirmed = {}
        payload_raw["offer_scope_confirmed"] = confirmed

    existing: set[str] = set() if sold_modules_changed else _read_dependency_confirmations(payload_raw)
    if new_codes:
        for code in new_codes:
            token = str(code).strip()
            if token:
                existing.add(token)
    confirmed["dependency_confirmations"] = sorted(existing)


def dependency_blocker_codes(payload_raw: dict[str, Any] | None) -> list[str]:
    result = validate_sold_graph_from_payload(payload_raw if isinstance(payload_raw, dict) else None)
    codes: list[str] = []
    for issue in result.blockers:
        codes.append(issue.code)
    for issue in result.confirmations_required:
        codes.append(f"offer_scope_dependency_unconfirmed:{issue.code}")
    return codes
