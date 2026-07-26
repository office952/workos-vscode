"""
Letters FINISH / MOUNTING / packaging runtime responsibility decoupling (V1).

Promotes phantom Aggregate codes to first-class runtime responsibilities.
Does NOT activate sold FINISH/MOUNTING/packaging chips.
Does NOT mutate historical snapshots.
"""

from __future__ import annotations

from typing import Any

# Canonical runtime responsibility codes (promote existing Aggregate phantoms).
RUNTIME_SURFACE_FINISH = "finisaje"
RUNTIME_INSTALLATION_TEMPLATE = "sablon_montaj"
RUNTIME_PACKAGING_LOGISTICS = "ambalare_livrare_montaj"
RUNTIME_STRUCTURE_SUPPORT = "structura_suport"

DECOUPLED_RUNTIME_MODULES: frozenset[str] = frozenset(
    {
        RUNTIME_SURFACE_FINISH,
        RUNTIME_INSTALLATION_TEMPLATE,
        RUNTIME_PACKAGING_LOGISTICS,
        RUNTIME_STRUCTURE_SUPPORT,
    }
)

# Old mixed finisaje bucket — expand when reading legacy snapshots (immutable JSON).
LEGACY_FINISAJE_AGGREGATE_ALIAS: frozenset[str] = frozenset(
    {
        RUNTIME_SURFACE_FINISH,
        RUNTIME_INSTALLATION_TEMPLATE,
        RUNTIME_PACKAGING_LOGISTICS,
    }
)

# Canonical sold maps after decoupling (FINISH/MOUNTING chips remain deferred).
FINISH_RUNTIME_MAP_DECOUPLED: frozenset[str] = frozenset({RUNTIME_SURFACE_FINISH})
MOUNTING_RUNTIME_MAP_DECOUPLED: frozenset[str] = frozenset(
    {RUNTIME_STRUCTURE_SUPPORT, RUNTIME_INSTALLATION_TEMPLATE}
)

# Full Letters composition — packaging is composition/conditional, not MOUNTING.
FULL_LETTERS_COMPOSITION_ALWAYS: frozenset[str] = frozenset(
    {
        RUNTIME_SURFACE_FINISH,
        RUNTIME_PACKAGING_LOGISTICS,
    }
)

ACTIVE_SCOPE_SNAPSHOT_VERSION_V1 = "active_scope_snapshot/v1"
ACTIVE_SCOPE_SNAPSHOT_VERSION_V2 = "active_scope_snapshot/v2"

OWNER_GATES = {
    "MOUNTING_MAP_NARROWING_OWNER_GATE": "APPROVED",
    "MINI_MODULE_SPLIT_OWNER_GATE": "APPROVED",
    "SOLD_CHIP_ACTIVATION_OWNER_GATE": "NOT_APPROVED",
    "PACKAGING_SOLD_CHIP": "NOT_PLANNED",
}


def _read_bool(value: Any) -> bool | None:
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "on"}:
        return True
    if text in {"false", "0", "no", "off"}:
        return False
    return None


def mounting_template_enabled(finish: dict[str, Any] | None) -> bool:
    if not isinstance(finish, dict):
        return False
    flag = _read_bool(finish.get("mounting_template_enabled"))
    return flag is True


def expand_legacy_finisaje_runtime_modules(runtime_modules: frozenset[str] | set[str]) -> frozenset[str]:
    """Legacy mixed finisaje → precise responsibility set (read path only)."""
    out = set(runtime_modules)
    if RUNTIME_SURFACE_FINISH in out:
        out |= LEGACY_FINISAJE_AGGREGATE_ALIAS
    return frozenset(out)


def full_letters_composition_modules(*, finish: dict[str, Any] | None) -> frozenset[str]:
    """Explicit composition activation replacing accidental mixed always-on bundling."""
    active = set(FULL_LETTERS_COMPOSITION_ALWAYS)
    if mounting_template_enabled(finish):
        active.add(RUNTIME_INSTALLATION_TEMPLATE)
    return frozenset(active)


def priced_op_to_runtime_module(priced_op: str | None) -> str | None:
    """Precise ownership for new snapshots / Aggregate task stamps."""
    if not priced_op:
        return None
    return {
        "painting": RUNTIME_SURFACE_FINISH,
        "vinyl_application": "colantare_fata",  # face path token (Aggregate legacy)
        "mounting_template_cnc_cut": RUNTIME_INSTALLATION_TEMPLATE,
        "packaging_letters": RUNTIME_PACKAGING_LOGISTICS,
        "return_face_bonding": "modelare_cant",
    }.get(str(priced_op))


def apply_decoupled_module_activation(
    *,
    code: str,
    state: str,
    activation_kind: str,
    active: set[str],
) -> bool:
    """
    Apply decoupled commercial/cost activation for known responsibility codes.
    Returns True if the code was handled (caller should continue).
    """
    if code == RUNTIME_SURFACE_FINISH:
        active.add(code)
        return True
    if code == RUNTIME_PACKAGING_LOGISTICS:
        if state in ("always_on", "active", "conditional_active") or activation_kind in (
            "always_on",
            "required_module",
        ):
            active.add(code)
        return True
    if code == RUNTIME_INSTALLATION_TEMPLATE:
        if state in ("active", "conditional_active"):
            active.add(code)
        return True
    return False


def responsibility_summary() -> dict[str, Any]:
    return {
        "surface_finish": RUNTIME_SURFACE_FINISH,
        "installation_template": RUNTIME_INSTALLATION_TEMPLATE,
        "packaging_logistics": RUNTIME_PACKAGING_LOGISTICS,
        "structure_support": RUNTIME_STRUCTURE_SUPPORT,
        "finish_sold_map": sorted(FINISH_RUNTIME_MAP_DECOUPLED),
        "mounting_sold_map": sorted(MOUNTING_RUNTIME_MAP_DECOUPLED),
        "legacy_finisaje_alias": sorted(LEGACY_FINISAJE_AGGREGATE_ALIAS),
        "snapshot_writer_version": ACTIVE_SCOPE_SNAPSHOT_VERSION_V2,
        "snapshot_legacy_version": ACTIVE_SCOPE_SNAPSHOT_VERSION_V1,
        "owner_gates": dict(OWNER_GATES),
        "sold_finish": "DEFERRED",
        "sold_mounting": "DEFERRED",
        "sold_packaging": "NOT_PLANNED",
        "finisaje_module_removed": False,
        "finisaje_responsibility_narrowed": True,
    }
