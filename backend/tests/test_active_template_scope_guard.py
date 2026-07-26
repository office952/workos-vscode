from __future__ import annotations

from seeds.seed_active_template_scope import validate_active_template_scope_postcondition


LETTERS = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = "TPL-VOLUMETRIC-LOGO_v1"
SHARED_COMPONENTS = [
    "TPL-VOLUMETRIC-FACE_v1",
    "TPL-VOLUMETRIC-BACK_v1",
    "TPL-VOLUM-ALUMINIU_v1",
    "TPL-VOLUMETRIC-FINISH_v1",
    "TPL-VOLUMETRIC-MOUNTING-STRUCTURE_v1",
    "TPL-VOLUMETRIC-LED_v1",
]
LEGACY_LOGO_COMPONENTS = [
    "TPL-VOLUMETRIC-LOGO-FACE_v1",
    "TPL-VOLUMETRIC-LOGO-BACK_v1",
    "TPL-VOLUMETRIC-LOGO-RETURN_v1",
    "TPL-VOLUMETRIC-LOGO-FINISH_v1",
    "TPL-VOLUMETRIC-LOGO-MOUNTING_v1",
]


def _offerable_letters() -> dict[str, object]:
    return {
        "template_code": LETTERS,
        "db_active": True,
        "quote_offerable": True,
        "product_system_role": "offerable_product",
        "display_group": "active_products",
    }


def _candidate_logo() -> dict[str, object]:
    return {
        "template_code": LOGO,
        "db_active": True,
        "quote_offerable": False,
        "product_system_role": "candidate_product",
        "display_group": "candidate_products",
    }


def _shared_component(code: str) -> dict[str, object]:
    return {
        "template_code": code,
        "db_active": True,
        "quote_offerable": False,
        "runtime_module": True,
        "product_system_role": "internal_module",
        "display_group": "internal_modules",
    }


def _hidden_legacy_logo(code: str) -> dict[str, object]:
    return {
        "template_code": code,
        "db_active": False,
        "quote_offerable": False,
        "product_system_role": "archived_experimental",
        "display_group": "archived_experimental",
    }


def test_valid_scope_allows_letters_root_and_logo_candidate_product() -> None:
    rows = [
        _offerable_letters(),
        _candidate_logo(),
        *( _shared_component(code) for code in SHARED_COMPONENTS ),
        {"template_code": "TPL-VOLUMETRIC-LOGO-LIGHTING_v1", "db_active": True, "quote_offerable": False, "display_group": "internal_modules"},
        *( _hidden_legacy_logo(code) for code in LEGACY_LOGO_COMPONENTS ),
    ]

    result = validate_active_template_scope_postcondition(rows)

    assert result["ok"] is True
    assert result["blockers"] == ()
    assert result["work_intake_offerable_roots"] == ("TPL-VOLUMETRIC-LETTERS_V2",)


def test_legacy_letters_alias_is_canonicalized_to_v2_offerable_root() -> None:
    result = validate_active_template_scope_postcondition([
        {**_offerable_letters(), "template_code": "TPL-VOLUMETRIC-LETTERS"},
        _candidate_logo(),
    ])

    assert result["ok"] is True
    assert result["blockers"] == ()
    assert result["work_intake_offerable_roots"] == ("TPL-VOLUMETRIC-LETTERS_V2",)


def test_scope_fails_closed_for_unknown_offerable_template() -> None:
    result = validate_active_template_scope_postcondition([
        _offerable_letters(),
        {"template_code": "TPL-UNKNOWN", "db_active": True, "quote_offerable": True},
    ])

    assert result["ok"] is False
    assert "unexpected_work_intake_offerable:TPL-UNKNOWN" in result["blockers"]
    assert "work_intake_offerable_roots_mismatch" in result["blockers"]


def test_scope_accepts_logo_candidate_status() -> None:
    result = validate_active_template_scope_postcondition([
        _offerable_letters(),
        _candidate_logo(),
    ])

    assert result["ok"] is True
    assert result["blockers"] == ()


def test_scope_fails_closed_for_component_root_or_component_quote() -> None:
    result = validate_active_template_scope_postcondition([
        _offerable_letters(),
        {**_shared_component("TPL-VOLUMETRIC-FACE_v1"), "root_type": "component_template", "quote_mode": "component_only"},
    ])

    assert result["ok"] is False
    assert "component_template_root_or_quote_enabled:TPL-VOLUMETRIC-FACE_V1" in result["blockers"]
    assert "component_quote_enabled:TPL-VOLUMETRIC-FACE_V1" in result["blockers"]


def test_scope_fails_closed_for_legacy_logo_owner_facing_active() -> None:
    result = validate_active_template_scope_postcondition([
        _offerable_letters(),
        {**_hidden_legacy_logo("TPL-VOLUMETRIC-LOGO-FACE_v1"), "db_active": True, "display_group": "internal_modules", "product_system_role": "internal_module"},
    ])

    assert result["ok"] is False
    assert "legacy_logo_component_owner_facing_active:TPL-VOLUMETRIC-LOGO-FACE_V1" in result["blockers"]