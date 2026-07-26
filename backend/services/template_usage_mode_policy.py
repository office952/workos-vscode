from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet


@dataclass(frozen=True)
class TemplateUsageModePolicy:
    template_code: str
    root_offerable: bool
    linked_child_allowed: bool
    candidate_only: bool
    component_only: bool
    owner_go_required: bool
    reason: str


TPL_VOLUMETRIC_LETTERS_V2 = "TPL-VOLUMETRIC-LETTERS_v2"
TPL_VOLUMETRIC_LOGO_V1 = "TPL-VOLUMETRIC-LOGO_v1"
TPL_METAL_PREMOUNT_STRUCTURE_V1 = "TPL-METAL-PREMOUNT-STRUCTURE_v1"
TPL_VOLUM_ALUMINIU_V1 = "TPL-VOLUM-ALUMINIU_v1"
TPL_ACM_CASSETTED_PANEL = "TPL-ACM-CASSETTED-PANEL"
TPL_ACM_BOXED_MOUNTING_SUPPORT_V1 = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"

_LETTER_MODULE_CODES = (
    TPL_METAL_PREMOUNT_STRUCTURE_V1,
    TPL_VOLUM_ALUMINIU_V1,
    "TPL-VOLUMETRIC-FACE_v1",
    "TPL-VOLUMETRIC-BACK_v1",
    "TPL-VOLUMETRIC-LED_v1",
    "TPL-VOLUMETRIC-FINISH_v1",
)

_LOGO_MODULE_CODES = (
    "TPL-VOLUMETRIC-LOGO-FACE_v1",
    "TPL-VOLUMETRIC-LOGO-RETURN_v1",
    "TPL-VOLUMETRIC-LOGO-BACK_v1",
    "TPL-VOLUMETRIC-LOGO-LIGHTING_v1",
    "TPL-VOLUMETRIC-LOGO-FINISH_v1",
    "TPL-VOLUMETRIC-LOGO-MOUNTING_v1",
)


def normalize_template_code(template_code: str | None) -> str:
    return str(template_code or "").strip().upper()


def _component_policy(template_code: str, reason: str) -> TemplateUsageModePolicy:
    return TemplateUsageModePolicy(
        template_code=template_code,
        root_offerable=False,
        linked_child_allowed=True,
        candidate_only=False,
        component_only=True,
        owner_go_required=False,
        reason=reason,
    )


_RAW_POLICIES = {
    TPL_VOLUMETRIC_LETTERS_V2: TemplateUsageModePolicy(
        template_code=TPL_VOLUMETRIC_LETTERS_V2,
        root_offerable=True,
        linked_child_allowed=False,
        candidate_only=False,
        component_only=False,
        owner_go_required=False,
        reason="Current owner-approved Work Intake root offerable template.",
    ),
    TPL_VOLUMETRIC_LOGO_V1: TemplateUsageModePolicy(
        template_code=TPL_VOLUMETRIC_LOGO_V1,
        root_offerable=False,
        linked_child_allowed=True,
        candidate_only=True,
        component_only=False,
        owner_go_required=True,
        reason="Candidate/read-only logo product; child/composition intent allowed, root activation blocked pending owner GO.",
    ),
    TPL_ACM_CASSETTED_PANEL: TemplateUsageModePolicy(
        template_code=TPL_ACM_CASSETTED_PANEL,
        root_offerable=False,
        linked_child_allowed=False,
        candidate_only=True,
        component_only=False,
        owner_go_required=True,
        reason="Future ACP/ACM candidate template; not active as Work Intake root or linked child today.",
    ),
    TPL_ACM_BOXED_MOUNTING_SUPPORT_V1: TemplateUsageModePolicy(
        template_code=TPL_ACM_BOXED_MOUNTING_SUPPORT_V1,
        root_offerable=True,
        linked_child_allowed=True,
        candidate_only=False,
        component_only=False,
        owner_go_required=False,
        reason="Owner-approved offerable boxed ACM mounting support; standalone PS + Intake linked child.",
    ),
    TPL_METAL_PREMOUNT_STRUCTURE_V1: TemplateUsageModePolicy(
        template_code=TPL_METAL_PREMOUNT_STRUCTURE_V1,
        root_offerable=True,
        linked_child_allowed=True,
        candidate_only=False,
        component_only=False,
        owner_go_required=False,
        reason="Owner-approved offerable metal premount structure; standalone PS + linked child for mounting system.",
    ),
}

for code in _LETTER_MODULE_CODES:
    _RAW_POLICIES.setdefault(
        code,
        _component_policy(code, "Internal module used by volumetric letters; not root offerable."),
    )

for code in _LOGO_MODULE_CODES:
    _RAW_POLICIES.setdefault(
        code,
        _component_policy(code, "Internal module used by volumetric logo composition; not root offerable."),
    )


TEMPLATE_USAGE_MODE_POLICIES = {
    normalize_template_code(code): policy for code, policy in _RAW_POLICIES.items()
}

ROOT_OFFERABLE_TEMPLATE_CODES: FrozenSet[str] = frozenset(
    code for code, policy in TEMPLATE_USAGE_MODE_POLICIES.items() if policy.root_offerable
)


def get_template_usage_mode_policy(
    template_code: str | None,
) -> TemplateUsageModePolicy | None:
    return TEMPLATE_USAGE_MODE_POLICIES.get(normalize_template_code(template_code))


def is_root_offerable_template(template_code: str | None) -> bool:
    policy = get_template_usage_mode_policy(template_code)
    return bool(policy and policy.root_offerable)


def is_linked_child_allowed_template(template_code: str | None) -> bool:
    policy = get_template_usage_mode_policy(template_code)
    return bool(policy and policy.linked_child_allowed)


def is_candidate_only_template(template_code: str | None) -> bool:
    policy = get_template_usage_mode_policy(template_code)
    return bool(policy and policy.candidate_only)


def is_component_only_template(template_code: str | None) -> bool:
    policy = get_template_usage_mode_policy(template_code)
    return bool(policy and policy.component_only)


def requires_owner_go_for_root_offerability(template_code: str | None) -> bool:
    policy = get_template_usage_mode_policy(template_code)
    return bool(policy and policy.owner_go_required and not policy.root_offerable)
