from __future__ import annotations

from seeds.seed_active_template_scope import validate_active_template_scope_postcondition
from seeds.seed_tpl_volumetric_logo_v1 import (
    CHILD_SPECS,
    FALLBACK_FAMILY_ID,
    FALLBACK_FAMILY_NAME,
    PARENT_TEMPLATE_CODE,
    _child_template_payload,
    _parent_template_payload,
)


LETTERS = "TPL-VOLUMETRIC-LETTERS_v2"


def _letters_offerable_row() -> dict[str, object]:
    return {
        "template_code": LETTERS,
        "db_active": True,
        "quote_offerable": True,
        "product_system_role": "offerable_product",
        "display_group": "active_products",
    }


def test_logo_seed_payload_is_valid_candidate_authority_when_scope_blocks_logo_root() -> None:
    parent = _parent_template_payload(FALLBACK_FAMILY_ID, FALLBACK_FAMILY_NAME)
    children = [
        _child_template_payload(spec, FALLBACK_FAMILY_ID, FALLBACK_FAMILY_NAME)
        for spec in CHILD_SPECS
    ]

    assert parent["template_code"] == PARENT_TEMPLATE_CODE
    assert parent["active"] is True
    assert all(child["active"] is True for child in children)

    result = validate_active_template_scope_postcondition([
        _letters_offerable_row(),
        {
            "template_code": parent["template_code"],
            "db_active": parent["active"],
            "quote_offerable": False,
            "product_system_role": "candidate_product",
            "display_group": "candidate_products",
        },
    ])

    assert result["ok"] is True
    assert result["blockers"] == ()


def test_active_scope_postcondition_blocks_logo_seed_children_from_owner_facing_active() -> None:
    children = [
        _child_template_payload(spec, FALLBACK_FAMILY_ID, FALLBACK_FAMILY_NAME)
        for spec in CHILD_SPECS
    ]
    legacy_rows = [
        {
            "template_code": child["template_code"],
            "db_active": child["active"],
            "quote_offerable": False,
            "product_system_role": "internal_module",
            "display_group": "internal_modules",
        }
        for child in children
        if str(child["template_code"]) != "TPL-VOLUMETRIC-LOGO-LIGHTING_v1"
    ]

    result = validate_active_template_scope_postcondition([
        _letters_offerable_row(),
        *legacy_rows,
    ])

    assert result["ok"] is False
    assert any(
        str(blocker).startswith("legacy_logo_component_owner_facing_active:")
        for blocker in result["blockers"]
    )


def test_active_scope_postcondition_accepts_logo_after_scope_deactivation() -> None:
    parent = _parent_template_payload(FALLBACK_FAMILY_ID, FALLBACK_FAMILY_NAME)
    children = [
        _child_template_payload(spec, FALLBACK_FAMILY_ID, FALLBACK_FAMILY_NAME)
        for spec in CHILD_SPECS
    ]
    scoped_rows = [
        _letters_offerable_row(),
        {
            "template_code": parent["template_code"],
            "db_active": False,
            "quote_offerable": False,
            "product_system_role": "candidate_product",
            "display_group": "candidate_products",
        },
        *[
            {
                "template_code": child["template_code"],
                "db_active": False,
                "quote_offerable": False,
                "product_system_role": "archived_experimental",
                "display_group": "archived_experimental",
            }
            for child in children
        ],
    ]

    result = validate_active_template_scope_postcondition(scoped_rows)

    assert result["ok"] is True
    assert result["blockers"] == ()