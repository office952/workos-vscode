from __future__ import annotations

from seeds.seed_active_template_scope import validate_active_template_scope_postcondition


def test_postcondition_accepts_letters_offerable_and_logo_candidate() -> None:
    result = validate_active_template_scope_postcondition(
        [
            {
                "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
                "db_active": True,
                "quote_offerable": True,
                "product_system_role": "offerable_product",
                "display_group": "active_products",
            },
            {
                "template_code": "TPL-VOLUMETRIC-LOGO_v1",
                "db_active": True,
                "quote_offerable": False,
                "product_system_role": "candidate_product",
                "display_group": "candidate_products",
            },
        ]
    )

    assert result["ok"] is True
    assert result["blockers"] == ()
    assert result["work_intake_offerable_roots"] == ("TPL-VOLUMETRIC-LETTERS_V2",)


def test_postcondition_blocks_logo_root_offerability() -> None:
    result = validate_active_template_scope_postcondition(
        [
            {
                "template_code": "TPL-VOLUMETRIC-LETTERS_v2",
                "db_active": True,
                "quote_offerable": True,
                "product_system_role": "offerable_product",
                "display_group": "active_products",
            },
            {
                "template_code": "TPL-VOLUMETRIC-LOGO_v1",
                "db_active": True,
                "quote_offerable": True,
                "product_system_role": "offerable_product",
                "display_group": "active_products",
            },
        ]
    )

    assert result["ok"] is False
    assert "logo_root_offerability_enabled" in result["blockers"]
    assert "work_intake_offerable_roots_mismatch" in result["blockers"]