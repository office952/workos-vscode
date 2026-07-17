"""
Letters FINISH / MOUNTING settings ownership + runtime decoupling contract.

Ownership V1 + runtime decoupling V1 metadata.
Sold FINISH/MOUNTING chips remain deferred.
"""

from __future__ import annotations

from typing import Any

from data.offer_scope_canonical_map import CANONICAL_TO_RUNTIME
from services.letters_finish_mounting_runtime_decoupling import (
    FINISH_RUNTIME_MAP_DECOUPLED,
    LEGACY_FINISAJE_AGGREGATE_ALIAS,
    MOUNTING_RUNTIME_MAP_DECOUPLED,
    OWNER_GATES,
    RUNTIME_INSTALLATION_TEMPLATE,
    RUNTIME_PACKAGING_LOGISTICS,
    RUNTIME_STRUCTURE_SUPPORT,
    RUNTIME_SURFACE_FINISH,
    expand_legacy_finisaje_runtime_modules,
    mounting_template_enabled,
    responsibility_summary,
)

FINISH_FACE_VINYL_PRINT_OWNER = "MODULE_FINISH"
RETURN_ORACAL_RAL_OWNER = "RETURN_CANT_COMPONENT"
MOUNTING_TEMPLATE_OWNER = "MOUNTING_PREP_INSTALLATION_TEMPLATE"

MOUNTING_SCOPE_ROLE = "canonical_commercial_prep_intent"
MOUNTING_SYSTEM_ROLE = "canonical_mounting_method_v1"
MOUNTING_SOLUTION_ROLE = "canonical_support_composition"
METAL_SUPPORT_REQUIRED_ROLE = "derived_compatibility_alias"
MOUNTING_METHOD_TARGET_NAME_ONLY = "target_future_name_only"

OWNER_GATES_NOT_APPROVED = frozenset(
    {
        gate
        for gate, status in OWNER_GATES.items()
        if status in {"NOT_APPROVED", "NOT_PLANNED"}
    }
)

# Post-decoupling canonical maps (asserted against offer_scope_canonical_map).
MOUNTING_RUNTIME_MAP = MOUNTING_RUNTIME_MAP_DECOUPLED
FINISH_RUNTIME_MAP = FINISH_RUNTIME_MAP_DECOUPLED
# Back-compat names used by older ownership tests.
MOUNTING_RUNTIME_MAP_UNCHANGED = MOUNTING_RUNTIME_MAP_DECOUPLED
FINISH_RUNTIME_MAP_UNCHANGED = FINISH_RUNTIME_MAP_DECOUPLED

BAR_MOUNTING_METHODS = frozenset({"steel_bars", "aluminum_bars"})


def _has_support_solution(mounting_solution: Any) -> bool:
    if not isinstance(mounting_solution, dict) or not mounting_solution:
        return False
    template_code = mounting_solution.get("template_code") or mounting_solution.get(
        "product_system_template"
    )
    if isinstance(template_code, str) and template_code.strip():
        return True
    kind = mounting_solution.get("kind")
    if kind in {"product_system_template", "installation_template"}:
        return True
    return len(mounting_solution) > 0


def derive_metal_support_required_alias(
    *,
    mounting_system: str | None = None,
    mounting_solution: Any = None,
) -> bool | None:
    if _has_support_solution(mounting_solution):
        return True
    if mounting_system in BAR_MOUNTING_METHODS:
        return True
    if mounting_system == "direct_wall":
        return False
    if not mounting_system and not _has_support_solution(mounting_solution):
        return None
    return False


def diagnose_mounting_ownership_conflicts(
    *,
    mounting_system: str | None = None,
    mounting_solution: Any = None,
    metal_support_required: bool | None = None,
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    solution_present = _has_support_solution(mounting_solution)
    bars = mounting_system in BAR_MOUNTING_METHODS

    if (
        metal_support_required is True
        and not solution_present
        and not bars
        and mounting_system == "direct_wall"
    ):
        diagnostics.append(
            {
                "code": "MOUNTING_ALIAS_TRUE_WITHOUT_SUPPORT_INTENT",
                "severity": "compatibility_warning",
                "canonical_wins": True,
                "message": (
                    "metal_support_required=true while mounting_system=direct_wall "
                    "and no mounting_solution; alias is not authoritative."
                ),
            }
        )

    if metal_support_required is False and (solution_present or bars):
        diagnostics.append(
            {
                "code": "MOUNTING_ALIAS_FALSE_WITH_SUPPORT_INTENT",
                "severity": "compatibility_warning",
                "canonical_wins": True,
                "message": (
                    "metal_support_required=false while canonical support intent is present; "
                    "respect mounting_solution / mounting_system."
                ),
            }
        )

    if bars and solution_present and isinstance(mounting_solution, dict):
        if mounting_solution.get("kind") == "installation_template":
            diagnostics.append(
                {
                    "code": "MOUNTING_METHOD_BARS_VS_INSTALLATION_SOLUTION",
                    "severity": "compatibility_warning",
                    "canonical_wins": True,
                    "message": (
                        "mounting_system implies bars while mounting_solution is "
                        "installation_template; review operator intent."
                    ),
                }
            )

    return diagnostics


def ownership_contract_summary() -> dict[str, Any]:
    summary = responsibility_summary()
    summary.update(
        {
            "finish_face_vinyl_print_owner": FINISH_FACE_VINYL_PRINT_OWNER,
            "return_oracal_ral_owner": RETURN_ORACAL_RAL_OWNER,
            "mounting_template_owner": MOUNTING_TEMPLATE_OWNER,
            "mounting_fields": {
                "mounting_scope": MOUNTING_SCOPE_ROLE,
                "mounting_system": MOUNTING_SYSTEM_ROLE,
                "mounting_solution": MOUNTING_SOLUTION_ROLE,
                "metal_support_required": METAL_SUPPORT_REQUIRED_ROLE,
                "mounting_method": MOUNTING_METHOD_TARGET_NAME_ONLY,
            },
            "owner_gates_not_approved": sorted(OWNER_GATES_NOT_APPROVED),
            "mounting_runtime_map_unchanged": sorted(MOUNTING_RUNTIME_MAP),
            "finish_runtime_map_unchanged": sorted(FINISH_RUNTIME_MAP),
            "canonical_map_finish": sorted(CANONICAL_TO_RUNTIME["FINISH"]),
            "canonical_map_mounting": sorted(CANONICAL_TO_RUNTIME["MOUNTING"]),
            "legacy_finisaje_alias": sorted(LEGACY_FINISAJE_AGGREGATE_ALIAS),
            "sold_finish_status": "DEFERRED",
            "sold_mounting_status": "DEFERRED",
            "behavioral_change": True,
            "finisaje_module_removed": False,
            "runtime_codes": {
                "surface_finish": RUNTIME_SURFACE_FINISH,
                "installation_template": RUNTIME_INSTALLATION_TEMPLATE,
                "packaging": RUNTIME_PACKAGING_LOGISTICS,
                "support": RUNTIME_STRUCTURE_SUPPORT,
            },
        }
    )
    return summary


__all__ = [
    "BAR_MOUNTING_METHODS",
    "FINISH_RUNTIME_MAP",
    "FINISH_RUNTIME_MAP_UNCHANGED",
    "MOUNTING_RUNTIME_MAP",
    "MOUNTING_RUNTIME_MAP_UNCHANGED",
    "OWNER_GATES_NOT_APPROVED",
    "derive_metal_support_required_alias",
    "diagnose_mounting_ownership_conflicts",
    "expand_legacy_finisaje_runtime_modules",
    "mounting_template_enabled",
    "ownership_contract_summary",
]
