"""Shared template architecture scope and alias resolution for WorkOS realignment flows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import FrozenSet, Iterable, Literal

VOLUMETRIC_V2_TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"
VOLUMETRIC_LOGO_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO_v1"
STRUCTURE_PREMOUNT_TEMPLATE_CODE = "TPL-METAL-PREMOUNT-STRUCTURE_v1"
ACM_BOXED_MOUNTING_TEMPLATE_CODE = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
VOLUM_ALUMINUM_TEMPLATE_CODE = "TPL-VOLUM-ALUMINIU_v1"
VOLUMETRIC_FACE_TEMPLATE_CODE = "TPL-VOLUMETRIC-FACE_v1"
VOLUMETRIC_BACK_TEMPLATE_CODE = "TPL-VOLUMETRIC-BACK_v1"
VOLUMETRIC_LED_TEMPLATE_CODE = "TPL-VOLUMETRIC-LED_v1"
VOLUMETRIC_FINISH_TEMPLATE_CODE = "TPL-VOLUMETRIC-FINISH_v1"
VOLUMETRIC_LOGO_FACE_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO-FACE_v1"
VOLUMETRIC_LOGO_RETURN_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO-RETURN_v1"
VOLUMETRIC_LOGO_BACK_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO-BACK_v1"
VOLUMETRIC_LOGO_LIGHTING_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO-LIGHTING_v1"
VOLUMETRIC_LOGO_FINISH_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO-FINISH_v1"
VOLUMETRIC_LOGO_MOUNTING_TEMPLATE_CODE = "TPL-VOLUMETRIC-LOGO-MOUNTING_v1"

VOLUMETRIC_TEMPLATE_ALIASES: FrozenSet[str] = frozenset(
    {"TPL-VOLUMETRIC-LETTERS", "TPL-VOLUMETRIC-LETTERS_V2"}
)

RUNTIME_TEMPLATE_CODE_BY_ALIAS: dict[str, str] = {
    "TPL-VOLUMETRIC-LETTERS": VOLUMETRIC_V2_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-LETTERS_V2": VOLUMETRIC_V2_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-LOGO": VOLUMETRIC_LOGO_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-LOGO_V1": VOLUMETRIC_LOGO_TEMPLATE_CODE,
    "TPL-METAL-PREMOUNT-STRUCTURE_V1": STRUCTURE_PREMOUNT_TEMPLATE_CODE,
    "TPL-ACM-BOXED-MOUNTING-SUPPORT_V1": ACM_BOXED_MOUNTING_TEMPLATE_CODE,
    "TPL-VOLUM-ALUMINIU_V1": VOLUM_ALUMINUM_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-FACE_V1": VOLUMETRIC_FACE_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-BACK_V1": VOLUMETRIC_BACK_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-LED_V1": VOLUMETRIC_LED_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-FINISH_V1": VOLUMETRIC_FINISH_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-LOGO-FACE_V1": VOLUMETRIC_LOGO_FACE_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-LOGO-RETURN_V1": VOLUMETRIC_LOGO_RETURN_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-LOGO-BACK_V1": VOLUMETRIC_LOGO_BACK_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-LOGO-LIGHTING_V1": VOLUMETRIC_LOGO_LIGHTING_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-LOGO-FINISH_V1": VOLUMETRIC_LOGO_FINISH_TEMPLATE_CODE,
    "TPL-VOLUMETRIC-LOGO-MOUNTING_V1": VOLUMETRIC_LOGO_MOUNTING_TEMPLATE_CODE,
}

OWNER_VALID_QUOTE_RUNTIME_TEMPLATE_CODES: FrozenSet[str] = frozenset(
    {
        VOLUMETRIC_V2_TEMPLATE_CODE.upper(),
        VOLUMETRIC_LOGO_TEMPLATE_CODE.upper(),
        VOLUM_ALUMINUM_TEMPLATE_CODE.upper(),
        VOLUMETRIC_FACE_TEMPLATE_CODE.upper(),
        VOLUMETRIC_BACK_TEMPLATE_CODE.upper(),
        VOLUMETRIC_LED_TEMPLATE_CODE.upper(),
        VOLUMETRIC_FINISH_TEMPLATE_CODE.upper(),
        STRUCTURE_PREMOUNT_TEMPLATE_CODE.upper(),
        ACM_BOXED_MOUNTING_TEMPLATE_CODE.upper(),
        VOLUMETRIC_LOGO_FACE_TEMPLATE_CODE.upper(),
        VOLUMETRIC_LOGO_RETURN_TEMPLATE_CODE.upper(),
        VOLUMETRIC_LOGO_BACK_TEMPLATE_CODE.upper(),
        VOLUMETRIC_LOGO_LIGHTING_TEMPLATE_CODE.upper(),
        VOLUMETRIC_LOGO_FINISH_TEMPLATE_CODE.upper(),
        VOLUMETRIC_LOGO_MOUNTING_TEMPLATE_CODE.upper(),
    }
)

OWNER_VALID_EXECUTION_RUNTIME_TEMPLATE_CODES: FrozenSet[str] = frozenset(
    OWNER_VALID_QUOTE_RUNTIME_TEMPLATE_CODES
)


def normalize_template_code(template_code: str | None) -> str:
    return str(template_code or "").strip().upper()


ResolutionType = Literal["canonical", "legacy_read_bridge", "rejected_alias"]


@dataclass(frozen=True)
class TemplateIdentityResolution:
    requested_template_code: str
    canonical_template_code: str
    resolution_type: ResolutionType
    legacy_alias_used: bool
    resolution_source: str


def resolve_template_identity(template_code: str | None) -> TemplateIdentityResolution:
    """
    Resolve a template identity with explicit trace metadata.

    Contract:
    - Harmless normalization: trim + uppercase.
    - Canonical template codes return resolution_type="canonical".
    - Known aliases resolve exactly once to a canonical code with resolution_type="legacy_read_bridge".
    - Unknown/unsupported alias-like inputs are classified as resolution_type="rejected_alias"
      *without* chained or recursive resolution.
    """
    requested_raw = str(template_code or "")
    normalized = normalize_template_code(requested_raw)
    if not normalized:
        return TemplateIdentityResolution(
            requested_template_code=requested_raw,
            canonical_template_code="",
            resolution_type="rejected_alias",
            legacy_alias_used=False,
            resolution_source="template_architecture_scope:empty",
        )

    resolved = RUNTIME_TEMPLATE_CODE_BY_ALIAS.get(normalized)
    if resolved and normalize_template_code(resolved) != normalized:
        return TemplateIdentityResolution(
            requested_template_code=requested_raw,
            canonical_template_code=normalize_template_code(resolved),
            resolution_type="legacy_read_bridge",
            legacy_alias_used=True,
            resolution_source="template_architecture_scope.RUNTIME_TEMPLATE_CODE_BY_ALIAS",
        )

    # Canonical identity (including harmless formatting differences).
    return TemplateIdentityResolution(
        requested_template_code=requested_raw,
        canonical_template_code=normalized,
        resolution_type="canonical",
        legacy_alias_used=False,
        resolution_source="template_architecture_scope:canonical",
    )


def require_canonical_template_code(template_code: str | None) -> TemplateIdentityResolution:
    """
    Strict identity gate for active compilation / write-like flows.

    - Allows harmless formatting normalization (trim/case) but rejects legacy alias resolution.
    - Returns the canonical resolution when accepted; callers should then use
      resolution.canonical_template_code as the only active identity.
    """
    resolution = resolve_template_identity(template_code)
    if resolution.resolution_type != "canonical" or resolution.legacy_alias_used:
        return TemplateIdentityResolution(
            requested_template_code=resolution.requested_template_code,
            canonical_template_code=resolution.canonical_template_code,
            resolution_type="rejected_alias",
            legacy_alias_used=resolution.legacy_alias_used,
            resolution_source=resolution.resolution_source,
        )
    return resolution


def resolve_runtime_template_code(template_code: str | None) -> str:
    normalized = normalize_template_code(template_code)
    if not normalized:
        return ""
    resolved = RUNTIME_TEMPLATE_CODE_BY_ALIAS.get(normalized)
    if resolved:
        return resolved.upper()
    return normalized


def template_matches_runtime_scope(
    template_code: str | None,
    allowed_runtime_codes: Iterable[str],
) -> bool:
    resolved = resolve_runtime_template_code(template_code)
    if not resolved:
        return False
    normalized_allowed = {normalize_template_code(code) for code in allowed_runtime_codes}
    return resolved in normalized_allowed