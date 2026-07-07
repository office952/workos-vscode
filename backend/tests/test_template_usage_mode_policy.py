from __future__ import annotations

from services.template_usage_mode_policy import (
    TPL_ACM_CASSETTED_PANEL,
    TPL_METAL_PREMOUNT_STRUCTURE_V1,
    TPL_VOLUMETRIC_LETTERS_V2,
    TPL_VOLUMETRIC_LOGO_V1,
    TPL_VOLUM_ALUMINIU_V1,
    get_template_usage_mode_policy,
    is_candidate_only_template,
    is_component_only_template,
    is_linked_child_allowed_template,
    is_root_offerable_template,
    requires_owner_go_for_root_offerability,
)


def test_letters_template_is_root_offerable() -> None:
    policy = get_template_usage_mode_policy(TPL_VOLUMETRIC_LETTERS_V2)
    assert policy is not None
    assert policy.root_offerable is True
    assert policy.candidate_only is False
    assert policy.component_only is False
    assert policy.owner_go_required is False


def test_logo_template_is_not_root_offerable() -> None:
    policy = get_template_usage_mode_policy(TPL_VOLUMETRIC_LOGO_V1)
    assert policy is not None
    assert policy.root_offerable is False
    assert is_root_offerable_template(TPL_VOLUMETRIC_LOGO_V1) is False


def test_logo_template_is_candidate_and_linked_child_allowed() -> None:
    policy = get_template_usage_mode_policy(TPL_VOLUMETRIC_LOGO_V1)
    assert policy is not None
    assert policy.linked_child_allowed is True
    assert policy.candidate_only is True
    assert is_linked_child_allowed_template(TPL_VOLUMETRIC_LOGO_V1) is True
    assert is_candidate_only_template(TPL_VOLUMETRIC_LOGO_V1) is True


def test_logo_template_requires_owner_go_for_root_offerability() -> None:
    assert requires_owner_go_for_root_offerability(TPL_VOLUMETRIC_LOGO_V1) is True


def test_internal_modules_remain_component_only_non_root() -> None:
    for code in (TPL_METAL_PREMOUNT_STRUCTURE_V1, TPL_VOLUM_ALUMINIU_V1):
        policy = get_template_usage_mode_policy(code)
        assert policy is not None
        assert policy.root_offerable is False
        assert policy.component_only is True
        assert policy.linked_child_allowed is True
        assert is_component_only_template(code) is True


def test_acm_panel_stays_non_root_candidate_only() -> None:
    policy = get_template_usage_mode_policy(TPL_ACM_CASSETTED_PANEL)
    assert policy is not None
    assert policy.root_offerable is False
    assert policy.candidate_only is True
    assert policy.owner_go_required is True
