"""Commercial mounting scope — V1 canonical values with legacy hydration."""

from __future__ import annotations

from typing import Any, Literal, Mapping

MountingScopeV1 = Literal["none", "preparation_only", "preparation_and_site_installation"]
LegacyMountingScope = Literal[
    "no_mounting",
    "mounting_included",
    "mounting_external",
    "to_be_decided",
]

V1_MOUNTING_SCOPES = frozenset({"none", "preparation_only", "preparation_and_site_installation"})
LEGACY_MOUNTING_SCOPES = frozenset(
    {"no_mounting", "mounting_included", "mounting_external", "to_be_decided"}
)


def _truthy_bool(raw: Any) -> bool:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return False
    if isinstance(raw, (int, float)):
        return raw != 0
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def has_mounting_prep_signals(setup: Mapping[str, Any] | None) -> bool:
    """True when persisted prep fields indicate factory preparation intent."""
    if not isinstance(setup, Mapping):
        return False
    if _truthy_bool(setup.get("mounting_template_enabled")):
        return True
    area = setup.get("mounting_template_area_m2")
    try:
        if area is not None and float(area) > 0:
            return True
    except (TypeError, ValueError):
        pass
    if str(setup.get("volum_aluminum_module_template_code") or "").strip():
        return True
    return False


def map_legacy_mounting_scope(raw: str) -> MountingScopeV1:
    """Map legacy enum values to canonical V1 scope."""
    legacy = str(raw or "").strip()
    if legacy == "no_mounting":
        return "none"
    if legacy == "mounting_included":
        return "preparation_and_site_installation"
    if legacy == "mounting_external":
        # External install: factory prep may still apply; site install is not sold by us.
        return "preparation_only"
    if legacy == "to_be_decided":
        return "none"
    return "none"


def normalize_mounting_scope(
    raw: Any,
    *,
    setup: Mapping[str, Any] | None = None,
) -> MountingScopeV1:
    """Resolve canonical V1 mounting_scope from persisted or legacy values."""
    text = str(raw or "").strip()
    if text in V1_MOUNTING_SCOPES:
        return text  # type: ignore[return-value]
    if text in LEGACY_MOUNTING_SCOPES:
        return map_legacy_mounting_scope(text)
    if has_mounting_prep_signals(setup):
        return "preparation_only"
    return "none"


def default_site_installation_included(scope: MountingScopeV1) -> bool:
    return scope == "preparation_and_site_installation"


def normalize_site_installation_included(
    raw: Any,
    *,
    mounting_scope: MountingScopeV1,
) -> bool | None:
    if mounting_scope != "preparation_and_site_installation":
        return None if raw is None else _truthy_bool(raw)
    if raw is None:
        return True
    return _truthy_bool(raw)


def is_mounting_preparation_active(
    setup: Mapping[str, Any] | None,
    *,
    mounting_scope: Any = None,
) -> bool:
    scope = normalize_mounting_scope(
        mounting_scope if mounting_scope is not None else (setup or {}).get("mounting_scope"),
        setup=setup,
    )
    return scope in {"preparation_only", "preparation_and_site_installation"}


def is_site_installation_active(
    setup: Mapping[str, Any] | None,
    *,
    mounting_scope: Any = None,
    site_installation_included: Any = None,
) -> bool:
    scope = normalize_mounting_scope(
        mounting_scope if mounting_scope is not None else (setup or {}).get("mounting_scope"),
        setup=setup,
    )
    if scope != "preparation_and_site_installation":
        return False
    included = site_installation_included
    if included is None and isinstance(setup, Mapping):
        included = setup.get("site_installation_included")
    return normalize_site_installation_included(included, mounting_scope=scope) is True


def hydrate_mounting_scope_fields(setup: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize mounting_scope + site_installation_included for persist/load."""
    scope = normalize_mounting_scope(setup.get("mounting_scope"), setup=setup)
    site_raw = setup.get("site_installation_included")
    if scope == "preparation_and_site_installation":
        site = normalize_site_installation_included(site_raw, mounting_scope=scope)
        if str(setup.get("mounting_scope") or "").strip() == "mounting_included" and site_raw is None:
            site = True
        return {
            "mounting_scope": scope,
            "site_installation_included": site,
        }
    return {
        "mounting_scope": scope,
        "site_installation_included": None if site_raw is None else _truthy_bool(site_raw),
    }
