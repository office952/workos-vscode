"""Project SVG-bindable components for Product System read models.

Pure projection from the code-owned binding contract. No Intake dependency.
"""

from __future__ import annotations

from typing import Any

from data.product_system.svg_component_binding_contract import (
    SVG_BINDABLE_BY_PRODUCT_TEMPLATE,
    list_geometry_roles,
    stale_bond_casetat_status,
)


def get_svg_bindable_components(template_code: str | None) -> list[dict[str, Any]]:
    code = str(template_code or "").strip()
    if not code:
        return []
    return [dict(item) for item in SVG_BINDABLE_BY_PRODUCT_TEMPLATE.get(code, [])]


def get_svg_binding_catalog_summary(template_code: str | None) -> dict[str, Any]:
    """Runtime proof payload for letters / ACM / stale containment."""
    code = str(template_code or "").strip()
    components = get_svg_bindable_components(code)
    return {
        "template_code": code,
        "geometry_roles": list_geometry_roles(),
        "svg_bindable_components": components,
        "stale_support_template": stale_bond_casetat_status(),
        "authority": "product_system_svg_component_binding_contract_v1",
        "intake_hardcoded_roles": "LEGACY_INTAKE_SVG_ROLE_ADAPTER",
    }


def assert_inactive_isolation(component: dict[str, Any]) -> list[str]:
    """Return blockers if inactive component incorrectly requires SVG/config."""
    blockers: list[str] = []
    if component.get("active_by_default"):
        return blockers
    if component.get("required"):
        blockers.append("optional_component_marked_required")
    if component.get("active") is True and not component.get("active_by_default"):
        blockers.append("inactive_default_but_active_true")
    return blockers
