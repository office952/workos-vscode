"""ACM boxed support composition — applied_content XOR + optional metal frame.

Decision A: extend TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 without new panel SKU.
No schema migration — XOR uses trigger_field=applied_content on module links
and finish_setup / quote_input payload fields.
"""

from __future__ import annotations

from typing import Any, Literal, Mapping

from services.template_usage_mode_policy import (
    TPL_ACM_BOXED_MOUNTING_SUPPORT_V1,
    TPL_VOLUMETRIC_LOGO_V1,
    is_candidate_only_template,
)

ACM_BOXED_ROOT = TPL_ACM_BOXED_MOUNTING_SUPPORT_V1
LETTERS_ROOT_REFERENCE = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO_ROOT = TPL_VOLUMETRIC_LOGO_V1

APPLIED_CONTENT_TRIGGER_FIELD = "applied_content"
APPLIED_CONTENT_LETTERS = "letters"
APPLIED_CONTENT_LOGO = "logo"
APPLIED_CONTENT_NONE = "none"

AppliedContent = Literal["none", "letters", "logo"]

BLOCKER_APPLIED_CONTENT_XOR = "APPLIED_CONTENT_XOR_VIOLATION"
BLOCKER_LOGO_BRANCH_CANDIDATE = "LOGO_BRANCH_CANDIDATE_BLOCKED"
BLOCKER_UNKNOWN_APPLIED_CONTENT = "UNKNOWN_APPLIED_CONTENT"
WARN_PANEL_ONLY_NO_CONTENT = "ACM_PANEL_ONLY_NO_APPLIED_CONTENT"
WARN_UNPUBLISHED_LETTERS_CHILD = "UNPUBLISHED_LETTERS_CHILD_REUSE"

LETTERS_PACK_TEMPLATE_CODES: tuple[str, ...] = (
    "TPL-VOLUMETRIC-FACE_v1",
    "TPL-VOLUMETRIC-BACK_v1",
    "TPL-VOLUM-ALUMINIU_v1",
    "TPL-VOLUMETRIC-LED_v1",
    "TPL-VOLUMETRIC-FINISH_v1",
)

LOGO_PACK_TEMPLATE_CODES: tuple[str, ...] = (LOGO_ROOT,)

FRAME_DOMAIN_KIND = "acp_internal_frame"

# Quantity ownership — panel vs content never share commercial keys.
PANEL_QUANTITY_KEYS = frozenset(
    {
        "panel_width_mm",
        "panel_height_mm",
        "panel_area_m2",
        "panel_perimeter_m",
        "fold_length_m",
        "acm_thickness_mm",
        "return_depth_mm",
    }
)
CONTENT_QUANTITY_OWNERSHIP = "child_separate_quote_line"
ANTI_HOURLY_POLICY = "no_root_hourly_for_content_children"


def normalize_applied_content(value: Any) -> AppliedContent | None:
    if value is None:
        return APPLIED_CONTENT_NONE
    text = str(value).strip().lower()
    if not text or text in {"none", "null", "panel_only"}:
        return APPLIED_CONTENT_NONE
    if text == APPLIED_CONTENT_LETTERS:
        return APPLIED_CONTENT_LETTERS
    if text == APPLIED_CONTENT_LOGO:
        return APPLIED_CONTENT_LOGO
    return None


def _has_meaningful_applied_content_value(raw: Any) -> bool:
    """True when a source explicitly set applied_content (including explicit none)."""
    if raw is None:
        return False
    return bool(str(raw).strip())


def read_applied_content(payload: Mapping[str, Any] | None) -> AppliedContent | None:
    """Read applied_content from quote_input / finish_setup / composition confirm / top-level.

    Empty/null bags (common after partial finish writes) must not shadow
    product_composition_confirmed.applied_content — otherwise Letters↔ACM
    connection commercial lines never fire on VL+ACM workspaces.
    """
    if not isinstance(payload, Mapping):
        return APPLIED_CONTENT_NONE
    sources: list[Any] = []
    if "applied_content" in payload:
        sources.append(payload.get("applied_content"))
    finish = payload.get("finish_setup")
    if isinstance(finish, Mapping) and "applied_content" in finish:
        sources.append(finish.get("applied_content"))
    quote = payload.get("quote_input")
    if isinstance(quote, Mapping) and "applied_content" in quote:
        sources.append(quote.get("applied_content"))
    confirmed = payload.get("product_composition_confirmed")
    if isinstance(confirmed, Mapping) and "applied_content" in confirmed:
        sources.append(confirmed.get("applied_content"))

    # Prefer an explicit letters/logo decision from any source before treating
    # an empty finish bag as "none".
    normalized_meaningful: list[AppliedContent | None] = []
    for raw in sources:
        if not _has_meaningful_applied_content_value(raw):
            continue
        normalized_meaningful.append(normalize_applied_content(raw))
    for value in normalized_meaningful:
        if value in {APPLIED_CONTENT_LETTERS, APPLIED_CONTENT_LOGO}:
            return value
    if normalized_meaningful:
        return normalized_meaningful[0]
    return APPLIED_CONTENT_NONE


def read_metal_frame_optional(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Operator-explicit optional frame — never inferred from thresholds."""
    empty = {
        "kind": FRAME_DOMAIN_KIND,
        "enabled": False,
        "selection_source": "operator_explicit",
        "automatic_threshold_applied": False,
    }
    if not isinstance(payload, Mapping):
        return empty
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), Mapping) else {}
    solution = finish.get("mounting_solution") if isinstance(finish.get("mounting_solution"), Mapping) else {}
    config = solution.get("configuration") if isinstance(solution.get("configuration"), Mapping) else {}
    selection = payload.get("acm_panel_selection") if isinstance(payload.get("acm_panel_selection"), Mapping) else {}

    enabled = False
    if isinstance(config.get("internal_frame"), Mapping):
        enabled = bool(config["internal_frame"].get("enabled"))
    elif "internal_frame_enabled" in config:
        enabled = bool(config.get("internal_frame_enabled"))
    elif "internal_frame_enabled" in selection:
        enabled = bool(selection.get("internal_frame_enabled"))
    elif "internal_frame_enabled" in payload:
        enabled = bool(payload.get("internal_frame_enabled"))
    elif "metal_frame_enabled" in payload:
        enabled = bool(payload.get("metal_frame_enabled"))

    return {
        "kind": FRAME_DOMAIN_KIND,
        "enabled": enabled,
        "selection_source": "operator_explicit",
        "automatic_threshold_applied": False,
        "product_template": None,
    }


def content_pack_template_codes(applied: AppliedContent) -> tuple[str, ...]:
    if applied == APPLIED_CONTENT_LETTERS:
        return LETTERS_PACK_TEMPLATE_CODES
    if applied == APPLIED_CONTENT_LOGO:
        return LOGO_PACK_TEMPLATE_CODES
    return ()


def validate_applied_content_xor(
    *,
    applied_content: AppliedContent | None,
    letters_active: bool = False,
    logo_active: bool = False,
) -> dict[str, Any]:
    """Validate XOR: letters and logo cannot both be active."""
    blockers: list[str] = []
    warnings: list[str] = []

    if applied_content is None:
        blockers.append(BLOCKER_UNKNOWN_APPLIED_CONTENT)
        return {
            "ok": False,
            "applied_content": None,
            "blockers": blockers,
            "warnings": warnings,
            "active_pack_codes": [],
            "logo_branch_status": "n/a",
            "letters_branch_status": "n/a",
        }

    if letters_active and logo_active:
        blockers.append(BLOCKER_APPLIED_CONTENT_XOR)

    if applied_content == APPLIED_CONTENT_LETTERS and logo_active:
        blockers.append(BLOCKER_APPLIED_CONTENT_XOR)
    if applied_content == APPLIED_CONTENT_LOGO and letters_active:
        blockers.append(BLOCKER_APPLIED_CONTENT_XOR)

    logo_branch_status = "inactive"
    letters_branch_status = "inactive"

    if applied_content == APPLIED_CONTENT_LOGO or logo_active:
        if is_candidate_only_template(LOGO_ROOT):
            blockers.append(BLOCKER_LOGO_BRANCH_CANDIDATE)
            logo_branch_status = "honestly_blocked_candidate"
        else:
            logo_branch_status = "active"
    if applied_content == APPLIED_CONTENT_LETTERS or letters_active:
        letters_branch_status = "active_reuse"
        warnings.append(WARN_UNPUBLISHED_LETTERS_CHILD)

    if applied_content == APPLIED_CONTENT_NONE and not letters_active and not logo_active:
        warnings.append(WARN_PANEL_ONLY_NO_CONTENT)

    active_codes = list(content_pack_template_codes(applied_content))
    return {
        "ok": len(blockers) == 0,
        "applied_content": applied_content,
        "blockers": blockers,
        "warnings": warnings,
        "active_pack_codes": active_codes,
        "logo_branch_status": logo_branch_status,
        "letters_branch_status": letters_branch_status,
        "quantity_policy": {
            "panel_keys": sorted(PANEL_QUANTITY_KEYS),
            "content_ownership": CONTENT_QUANTITY_OWNERSHIP,
            "anti_hourly": ANTI_HOURLY_POLICY,
            "double_count_guard": "panel_and_content_separate_quote_lines",
        },
    }


def resolve_acm_boxed_composition(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Full composition resolution for ACM boxed root (Decision A)."""
    applied = read_applied_content(payload)
    frame = read_metal_frame_optional(payload)

    letters_active = applied == APPLIED_CONTENT_LETTERS
    logo_active = applied == APPLIED_CONTENT_LOGO
    # Explicit dual flags (tests / hostile payloads)
    if isinstance(payload, Mapping):
        if payload.get("force_letters_and_logo"):
            letters_active = True
            logo_active = True

    xor = validate_applied_content_xor(
        applied_content=applied,
        letters_active=letters_active,
        logo_active=logo_active,
    )
    return {
        "root_template_code": ACM_BOXED_ROOT,
        "letters_root_reference": LETTERS_ROOT_REFERENCE,
        "logo_root": LOGO_ROOT,
        "applied_content": xor["applied_content"],
        "metal_frame": frame,
        "xor": xor,
        "composition_mode": "acm_boxed_support_composition_v1",
        "decision": "A",
    }


def module_link_trigger_value_for_pack(pack: AppliedContent) -> str | None:
    if pack in (APPLIED_CONTENT_LETTERS, APPLIED_CONTENT_LOGO):
        return pack
    return None
