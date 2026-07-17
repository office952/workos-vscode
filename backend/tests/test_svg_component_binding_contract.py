"""Product System SVG component-binding contract — unit proof."""

from __future__ import annotations

from data.product_system.svg_component_binding_contract import (
    ACM_BOXED_SUPPORT,
    FACE_COMPONENT,
    GEOMETRY_ROLE_LETTER_VECTOR_SET,
    GEOMETRY_ROLE_LOGO_VECTOR_SET,
    GEOMETRY_ROLE_SUPPORT_CONTOUR,
    LETTERS_PRODUCT,
    LOGO_PRODUCT,
    METAL_PREMOUNT,
    SELECTION_MODE_CLOSED_CONTOUR,
    SELECTION_MODE_LAYER_OR_GROUP,
    STALE_BOND_CASETAT,
    CARDINALITY_MAX_ONE,
    stale_bond_casetat_status,
)
from services.svg_component_binding_service import (
    assert_inactive_isolation,
    get_svg_bindable_components,
    get_svg_binding_catalog_summary,
)


def test_letters_product_exposes_svg_bindable_components() -> None:
    comps = get_svg_bindable_components(LETTERS_PRODUCT)
    by_code = {c["component_template_code"]: c for c in comps}

    assert FACE_COMPONENT in by_code
    face = by_code[FACE_COMPONENT]
    assert face["accepted_geometry_roles"] == [GEOMETRY_ROLE_LETTER_VECTOR_SET]
    assert face["selection_mode"] == SELECTION_MODE_LAYER_OR_GROUP
    assert face["required"] is True
    assert face["active_by_default"] is True

    logo = by_code[LOGO_PRODUCT]
    assert logo["accepted_geometry_roles"] == [GEOMETRY_ROLE_LOGO_VECTOR_SET]
    assert logo["required"] is False
    assert logo["active_by_default"] is False
    assert "candidate_only" in logo["guards"]

    acm = by_code[ACM_BOXED_SUPPORT]
    assert acm["accepted_geometry_roles"] == [GEOMETRY_ROLE_SUPPORT_CONTOUR]
    assert acm["selection_mode"] == SELECTION_MODE_CLOSED_CONTOUR
    assert acm["cardinality"] == CARDINALITY_MAX_ONE
    assert acm["required"] is False
    assert acm["available"] is True
    assert acm["active_by_default"] is False
    assert acm["owner_label"] == "Panou Alucobond casetat"
    assert acm["svg_binding"]["geometry_requirements"]["closed_required"] is True

    metal = by_code[METAL_PREMOUNT]
    assert metal["svg_binding"]["enabled"] is False


def test_acm_inactive_by_default_has_zero_required_leakage() -> None:
    acm = next(
        c
        for c in get_svg_bindable_components(LETTERS_PRODUCT)
        if c["component_template_code"] == ACM_BOXED_SUPPORT
    )
    assert assert_inactive_isolation(acm) == []
    assert acm["active"] is False


def test_stale_bond_casetat_not_new_selection_authority() -> None:
    status = stale_bond_casetat_status()
    assert status["code"] == STALE_BOND_CASETAT
    assert status["new_selection_authority"] is False
    assert status["live_authority"] == ACM_BOXED_SUPPORT
    assert status["seeded_product_template"] is False
    codes = {c["component_template_code"] for c in get_svg_bindable_components(LETTERS_PRODUCT)}
    assert STALE_BOND_CASETAT not in codes


def test_no_vector_acp_geometry_role() -> None:
    summary = get_svg_binding_catalog_summary(LETTERS_PRODUCT)
    role_codes = {r["code"] for r in summary["geometry_roles"]}
    assert "VECTOR_ACP" not in role_codes
    assert "ALUCOBOND" not in role_codes
    assert GEOMETRY_ROLE_SUPPORT_CONTOUR in role_codes
    labels = " ".join(r["owner_label"] for r in summary["geometry_roles"])
    assert "Vector ACP" not in labels


def test_acm_template_self_binding() -> None:
    comps = get_svg_bindable_components(ACM_BOXED_SUPPORT)
    assert len(comps) == 1
    assert comps[0]["selection_mode"] == SELECTION_MODE_CLOSED_CONTOUR
    assert comps[0]["cardinality"] == CARDINALITY_MAX_ONE
