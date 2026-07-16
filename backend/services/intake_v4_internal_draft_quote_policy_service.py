"""Intake V4 internal draft quote policy — fatal blockers vs review-only warnings."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from models.intake_v4_workspace import IntakeV4WorkspaceRecord
from schemas.intake_v4 import IntakeV4WorkspacePayload
from services.intake_v4_analysis_boundary_service import (
    list_v4_analysis_boundary_blockers,
    list_v4_analysis_hash_sync_blockers,
)
from services.intake_v4_analysis_bundle_guard_service import analysis_bundle_has_degraded_child_parts
from services.intake_v4_finish_truth_service import list_finish_setup_color_fatal_blockers
from services.active_template_scope import is_owner_valid_active_template


REVIEW_WARNING_PREFIXES = ("artwork_execution_undecided:", "pricing_warning:", "material_availability:")
REVIEW_WARNING_EXACT = frozenset(
    {
        "requires_pricing_review",
        "manual_pricing_review_required",
        "material_availability_warning",
        "template_pricing_code_missing",
        "artwork_execution_pending",
        "unclassified_vector_artwork_requires_decision",
    }
)
HASH_SYNC_BLOCKERS = frozenset(
    {"missing_client_analysis_hash", "missing_svg_source_hash", "analysis_hash_mismatch"}
)
RAW_VECTOR_TOTAL_MIN_DELTA_M = 0.05


def _positive_float(raw: Any) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    return value if value > 0 else None


def _raw_vector_total_perimeter_m(payload: IntakeV4WorkspacePayload) -> float | None:
    path_geom = payload.path_geometry_summary if isinstance(payload.path_geometry_summary, dict) else {}
    candidates: list[float] = []
    contour_split = path_geom.get("contour_split")
    if isinstance(contour_split, dict):
        total_mm = _positive_float(contour_split.get("total_cutting_perimeter_mm"))
        if total_mm is not None:
            candidates.append(total_mm / 1000.0)
    perimeter_mm = _positive_float(path_geom.get("perimeter_mm_approx"))
    if perimeter_mm is not None:
        candidates.append(perimeter_mm / 1000.0)
    return round(max(candidates), 4) if candidates else None


def _is_artwork_row_perimeter_eligible(row: Any) -> bool:
    """True when a Vector Logo row may contribute perimeter like a letter group.

    Product-configured logos (execution decided) count even when legacy finish
    ``confirmed=false``. Incomplete rows (needs_decision / blank) are excluded
    individually so one incomplete logo does not drop all others.
    """
    execution = str(getattr(row, "execution_type", None) or "needs_decision").strip().lower()
    return bool(execution) and execution != "needs_decision"


def _artwork_row_perimeter_m(row: Any, analysis: dict[str, Any]) -> float | None:
    layer_key = str(getattr(row, "layer_key", None) or "")
    layer_name = str(getattr(row, "layer_name", None) or layer_key)
    if not layer_key and not layer_name:
        return None
    lookup = {value for value in (layer_key, layer_name) if value}
    layers = analysis.get("layers")
    if not isinstance(layers, list):
        return None
    for layer in layers:
        if not isinstance(layer, dict):
            continue
        layer_id = str(layer.get("id") or "")
        name = str(layer.get("name") or layer_id)
        if not lookup.intersection({layer_id, name}):
            continue
        perimeter_m = _positive_float(layer.get("perimeterMl")) or _positive_float(layer.get("perimeter_ml"))
        if perimeter_m is not None:
            return perimeter_m
        perimeter_mm = _positive_float(layer.get("perimeterMm")) or _positive_float(layer.get("perimeter_mm"))
        if perimeter_mm is not None:
            return perimeter_mm / 1000.0
    return None


def _operator_confirmed_artwork_perimeter_m(payload: IntakeV4WorkspacePayload) -> float | None:
    setup = payload.finish_setup
    if setup is None or not setup.artwork_finishes:
        return None

    artwork_rows = list(setup.artwork_finishes)
    eligible_rows = [row for row in artwork_rows if _is_artwork_row_perimeter_eligible(row)]
    if not eligible_rows:
        return None

    analysis = payload.svg_analysis_json if isinstance(payload.svg_analysis_json, dict) else {}
    row_perimeters: list[float] = []
    for row in eligible_rows:
        perimeter = _artwork_row_perimeter_m(row, analysis)
        if perimeter is None:
            row_perimeters = []
            break
        row_perimeters.append(perimeter)
    if row_perimeters:
        return round(sum(row_perimeters), 4)

    # Aggregate fallback only when every Vector Logo row is eligible (none incomplete).
    if len(eligible_rows) == len(artwork_rows):
        quote_geom = payload.quote_geometry if isinstance(payload.quote_geometry, dict) else {}
        aggregate = _positive_float(quote_geom.get("artwork_return_perimeter_ml"))
        if aggregate is not None:
            return round(aggregate, 4)
    return None


def _operator_confirmed_letter_perimeter_m(payload: IntakeV4WorkspacePayload) -> float | None:
    setup = payload.finish_setup
    if setup and setup.letter_group_finishes:
        total = 0.0
        found = False
        for group in setup.letter_group_finishes:
            value = _positive_float(group.perimeter_m)
            if value is None:
                continue
            total += value
            found = True
        if found:
            return round(total, 4)

    quote_geom = payload.quote_geometry if isinstance(payload.quote_geometry, dict) else {}
    path_geom = payload.path_geometry_summary if isinstance(payload.path_geometry_summary, dict) else {}
    for source in (quote_geom, path_geom):
        for key in (
            "letter_return_perimeter_ml",
            "letter_perimeter_m",
            "total_letter_perimeter_ml",
        ):
            value = _positive_float(source.get(key))
            if value is not None:
                return value
    return None


def _operator_confirmed_vector_perimeter_m(payload: IntakeV4WorkspacePayload) -> float | None:
    letter_total = _operator_confirmed_letter_perimeter_m(payload)
    if letter_total is None:
        return None
    artwork_total = _operator_confirmed_artwork_perimeter_m(payload)
    if artwork_total is not None:
        return round(letter_total + artwork_total, 4)
    return letter_total


def has_unclassified_vector_artwork(payload: IntakeV4WorkspacePayload) -> bool:
    raw_total = _raw_vector_total_perimeter_m(payload)
    confirmed_total = _operator_confirmed_vector_perimeter_m(payload)
    if raw_total is None or confirmed_total is None:
        return False
    return raw_total > confirmed_total + RAW_VECTOR_TOTAL_MIN_DELTA_M


def is_review_warning_code(code: str) -> bool:
    if code in REVIEW_WARNING_EXACT:
        return True
    return any(code.startswith(prefix) for prefix in REVIEW_WARNING_PREFIXES)


def classify_handoff_issue_codes(codes: list[str]) -> tuple[list[str], list[str]]:
    fatal: list[str] = []
    warnings: list[str] = []
    for code in codes:
        if is_review_warning_code(code):
            warnings.append(code)
        else:
            fatal.append(code)
    return fatal, warnings


def list_lighting_fatal_blockers(payload: IntakeV4WorkspacePayload) -> list[str]:
    setup = payload.finish_setup
    if setup is None or setup.illuminated is False:
        return []
    blockers: list[str] = []
    if not (setup.lighting_system_type or "").strip():
        blockers.append("lighting_config_invalid:missing_system_type")
    lighting_system = (setup.lighting_system_type or "").strip().lower()
    if lighting_system == "led_strip":
        if setup.estimated_led_watts is None or float(setup.estimated_led_watts) <= 0:
            blockers.append("lighting_config_invalid:missing_led_strip_load")
    else:
        module_count = setup.led_module_count
        if module_count is None or int(module_count) <= 0:
            blockers.append("lighting_config_invalid:missing_led_module_count")
    if not setup.psu_configuration:
        blockers.append("lighting_config_invalid:missing_psu_configuration")
    return blockers


def list_v4_handoff_issue_codes(
    record: IntakeV4WorkspaceRecord,
    payload: IntakeV4WorkspacePayload,
    *,
    pricing_preview: Any | None = None,
    client_analysis_hash: str | None = None,
    include_hash_sync: bool = True,
) -> list[str]:
    """Collect all handoff issue codes before fatal vs review classification."""
    issues: list[str] = []

    if record.archived_at is not None:
        issues.append("workspace_archived")

    if record.readiness_status != "ready_for_quote_preview":
        issues.append(f"readiness_not_ready:{record.readiness_status or 'unknown'}")

    setup = payload.finish_setup
    if setup is None or not setup.confirmed:
        issues.append("finish_setup_not_confirmed")

    layer_setup = payload.layer_role_setup
    if layer_setup is None or layer_setup.confirmation_status != "complete":
        issues.append("layer_roles_incomplete")

    if not payload.svg_analysis_json:
        path = payload.path_geometry_summary if isinstance(payload.path_geometry_summary, dict) else {}
        svg_source = payload.svg_source
        analyzed_upload = (
            svg_source is not None
            and svg_source.upload_status == "analyzed"
            and path.get("parse_status") == "parsed"
        )
        if not analyzed_upload:
            issues.append("missing_svg_analysis")

    if payload.svg_analysis_json and analysis_bundle_has_degraded_child_parts(payload.svg_analysis_json):
        issues.append("degraded_child_parts_analysis")

    for code in list_v4_analysis_boundary_blockers(payload):
        if code not in issues:
            issues.append(code)

    if include_hash_sync:
        for code in list_v4_analysis_hash_sync_blockers(payload, client_analysis_hash):
            if code not in issues:
                issues.append(code)

    if not is_owner_valid_active_template(payload.product_binding.template_code):
        issues.append("template_out_of_scope")

    quote_geom = payload.quote_geometry if isinstance(payload.quote_geometry, dict) else {}
    path_geom = payload.path_geometry_summary if isinstance(payload.path_geometry_summary, dict) else {}
    letter_count = quote_geom.get("letter_count") or path_geom.get("letter_count") or path_geom.get(
        "real_letters_count"
    )
    perimeter = (
        quote_geom.get("letter_perimeter_m")
        or quote_geom.get("total_letter_perimeter_ml")
        or path_geom.get("letter_perimeter_m")
        or path_geom.get("total_letter_perimeter_ml")
    )
    if not perimeter:
        approx_mm = path_geom.get("perimeter_mm_approx")
        try:
            if approx_mm is not None and float(approx_mm) > 0:
                perimeter = float(approx_mm) / 1000.0
        except (TypeError, ValueError):
            perimeter = None
    if not letter_count and not perimeter:
        issues.append("missing_quote_geometry")

    for code in list_finish_setup_color_fatal_blockers(setup):
        if code not in issues:
            issues.append(code)

    for code in list_lighting_fatal_blockers(payload):
        if code not in issues:
            issues.append(code)

    if setup and setup.artwork_finishes:
        for row in setup.artwork_finishes:
            if (row.execution_type or "needs_decision") == "needs_decision":
                code = f"artwork_execution_undecided:{row.layer_key}"
                if code not in issues:
                    issues.append(code)

    if has_unclassified_vector_artwork(payload):
        code = "unclassified_vector_artwork_requires_decision"
        if code not in issues:
            issues.append(code)

    if pricing_preview is not None:
        quote_input = dict(getattr(pricing_preview, "quote_input_payload", None) or {})
        has_baseline = bool(quote_input) and (
            quote_input.get("letter_count")
            or quote_input.get("real_letters_count")
            or quote_input.get("letter_perimeter_m")
            or quote_input.get("total_letter_perimeter_ml")
        )
        if not has_baseline:
            if "pricing_baseline_unavailable" not in issues:
                issues.append("pricing_baseline_unavailable")
        for warning in list(getattr(pricing_preview, "adapter_warnings", []) or []):
            token = str(warning).strip()
            if not token:
                continue
            if "pricing review" in token.lower() or "manual pricing" in token.lower():
                code = "manual_pricing_review_required"
                if code not in issues:
                    issues.append(code)

    if setup is None or not setup.internal_draft_quote_confirmed:
        issues.append("operator_confirmation_missing")

    from services.intake_v6_canonical_readiness_service import list_runtime_capture_fatal_blocker_codes

    template_code = (
        payload.product_binding.template_code
        if payload.product_binding and payload.product_binding.template_code
        else "TPL-VOLUMETRIC-LETTERS_v2"
    )
    for code in list_runtime_capture_fatal_blocker_codes(payload.model_dump(mode="json"), template_code=template_code):
        token = f"runtime_capture:{code}"
        if token not in issues:
            issues.append(token)

    if pricing_preview is not None:
        if not getattr(pricing_preview, "is_ready_for_quote", True):
            if "pricing_adapter_not_ready" not in issues:
                issues.append("pricing_adapter_not_ready")
        for code in list(getattr(pricing_preview, "adapter_blockers", []) or []):
            token = str(code).strip()
            if not token:
                continue
            prefixed = token if token.startswith(("runtime_capture:", "canonical_")) else f"pricing_adapter:{token}"
            if prefixed not in issues:
                issues.append(prefixed)

    return issues


@dataclass(frozen=True)
class InternalDraftQuotePolicyResult:
    fatal_blockers: list[str]
    review_warnings: list[str]
    operator_confirmation_complete: bool
    requires_operator_confirmation: bool
    can_create_internal_draft_quote: bool
    client_send_allowed: bool
    accept_allowed: bool
    convert_to_order_allowed: bool
    production_allowed: bool
    status_label: str
    all_issue_codes: list[str]


def resolve_internal_draft_quote_status_label(
    fatal_blockers: list[str],
    review_warnings: list[str],
) -> str:
    if any(code in HASH_SYNC_BLOCKERS for code in fatal_blockers):
        return "ACTION_NEEDED"
    if fatal_blockers:
        return "QUOTE_HANDOFF_BLOCKED"
    if review_warnings:
        return "READY_FOR_INTERNAL_DRAFT_REVIEW"
    return "HANDOFF_ALLOWED"


def evaluate_internal_draft_quote_policy(
    record: IntakeV4WorkspaceRecord,
    payload: IntakeV4WorkspacePayload,
    *,
    pricing_preview: Any | None = None,
    client_analysis_hash: str | None = None,
    include_hash_sync: bool = True,
) -> InternalDraftQuotePolicyResult:
    all_codes = list_v4_handoff_issue_codes(
        record,
        payload,
        pricing_preview=pricing_preview,
        client_analysis_hash=client_analysis_hash,
        include_hash_sync=include_hash_sync,
    )
    fatal_blockers, review_warnings = classify_handoff_issue_codes(all_codes)
    operator_confirmation_complete = bool(
        payload.finish_setup is not None and payload.finish_setup.internal_draft_quote_confirmed
    )
    requires_operator_confirmation = True
    can_create = not fatal_blockers
    has_review_only_warnings = bool(review_warnings)

    status_label = resolve_internal_draft_quote_status_label(fatal_blockers, review_warnings)

    return InternalDraftQuotePolicyResult(
        fatal_blockers=fatal_blockers,
        review_warnings=review_warnings,
        operator_confirmation_complete=operator_confirmation_complete,
        requires_operator_confirmation=requires_operator_confirmation,
        can_create_internal_draft_quote=can_create,
        client_send_allowed=not has_review_only_warnings and can_create,
        accept_allowed=not has_review_only_warnings and can_create,
        convert_to_order_allowed=not has_review_only_warnings and can_create,
        production_allowed=not has_review_only_warnings and can_create,
        status_label=status_label,
        all_issue_codes=all_codes,
    )


def client_order_production_flags_for_quote(*, review_warnings: list[str]) -> dict[str, bool]:
    """Persisted on draft quote snapshot — artwork/review warnings block downstream client actions."""
    blocked = bool(review_warnings)
    return {
        "client_send_allowed": not blocked,
        "accept_allowed": not blocked,
        "convert_to_order_allowed": not blocked,
        "production_allowed": not blocked,
        "client_ready": not blocked,
        "send_allowed": not blocked,
        "internal_draft_review_only": blocked,
    }
