"""TPL-VOLUMETRIC-LETTERS — final commercial quote readiness gate.

Separates:
- simulate_ready: CostEngine can calculate with provided quote_input
- ready_for_quote: ProductReadinessService dossier/template gates
- can_create_commercial_quote: all final quote blockers cleared
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Optional

from services.mounting_scope_service import is_mounting_preparation_active
from services.volumetric_quote_input_policy import (
    WARNING_ACM_SEPARATE_TEMPLATE,
    WARNING_MOUNTING_BAR_PROFILE_PRICE_MISSING,
    WARNING_PRODUCTION_METADATA_MISSING,
    collect_volumetric_captured_unpriced_warnings,
    is_cant_ral_paint_enabled,
    is_illumination_enabled,
    normalize_mounting_system,
    normalize_mounting_template_enabled,
)
from services.volumetric_vector_readiness_policy import (
    WARN_LETTERS_VECTOR_FILE_REQUIRED,
    WARN_VECTOR_ANALYSIS_FAILED,
    WARN_VECTOR_ANALYSIS_PENDING,
    WARN_VECTOR_LAYER_MAPPING_PENDING,
    WARN_VECTOR_MANUAL_REVIEW_REQUIRED,
    evaluate_volumetric_vector_readiness,
)
from services.volumetric_material_rate_resolver import is_volumetric_template_code

FINAL_QUOTE_METADATA_BLOCKERS = frozenset(
    {
        f"{WARNING_PRODUCTION_METADATA_MISSING}:face_vinyl_color_code",
        f"{WARNING_PRODUCTION_METADATA_MISSING}:face_vinyl_roll_width_mm",
        f"{WARNING_PRODUCTION_METADATA_MISSING}:paint_ral_code",
    }
)


_READINESS_SECTION_KEYS = (
    "technical_readiness",
    "costengine_readiness",
    "document_output_readiness",
    "visual_prompt_readiness",
    "execution_preparation_readiness",
)

# Warning-only codes for TPL-VOLUMETRIC-LETTERS — never hard block final quote.
_ACKNOWLEDGEABLE_WARNING_PREFIXES = (
    WARN_VECTOR_ANALYSIS_PENDING,
    "volumetric_profile_depth_variant_pricing:",
    "volumetric_psu_wattage_variant_pricing:",
    "volumetric_profile_return_depth_required_at_quote:",
    "volumetric_psu_wattage_required_at_quote:",
    "operations_missing",
    "components_missing",
    "output_blocks_missing",
    "visual_prompt_blocks_missing",
    "task_rules_missing",
)


@dataclass(frozen=True)
class VolumetricQuoteReadyResult:
    simulate_ready: bool = False
    ready_for_quote: bool = False
    can_create_commercial_quote: bool = False
    requires_acknowledgement: bool = False
    blockers: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    classified: dict[str, list[str]] = field(default_factory=dict)
    reason_codes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "simulate_ready": self.simulate_ready,
            "ready_for_quote": self.ready_for_quote,
            "can_create_commercial_quote": self.can_create_commercial_quote,
            "requires_acknowledgement": self.requires_acknowledgement,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "notes": list(self.notes),
            "classified": {k: list(v) for k, v in self.classified.items()},
            "reason_codes": list(self.reason_codes),
        }


def _positive_number(value: Any) -> bool:
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False


def _has_valid_psu_selection(
    qi: Mapping[str, Any],
    product_spec: Mapping[str, Any] | None,
) -> bool:
    if _positive_number(qi.get("selected_psu_watts")):
        return True
    if not product_spec:
        return False
    status = str(product_spec.get("psu_allocation_status") or "").strip()
    cfg = product_spec.get("psu_configuration") or []
    return status == "ok" and isinstance(cfg, list) and len(cfg) > 0


def _collect_geometry_blockers(
    quote_input: Mapping[str, Any],
    *,
    product_spec: Mapping[str, Any] | None = None,
) -> list[str]:
    blockers: list[str] = []
    qi = quote_input or {}
    for key in ("width_mm", "height_mm", "letter_face_area_m2", "letter_perimeter_m", "letter_count"):
        if not _positive_number(qi.get(key)):
            blockers.append(f"quote_input_missing:{key}")
    depth_ok = _positive_number(qi.get("depth_mm")) or _positive_number(qi.get("return_depth_mm"))
    if not depth_ok:
        blockers.append("quote_input_missing:depth_mm_or_return_depth_mm")
    if is_illumination_enabled(qi) and not _has_valid_psu_selection(qi, product_spec):
        blockers.append("quote_input_missing:selected_psu_watts")
    try:
        tubes = float(qi.get("paint_tube_count") or 0)
    except (TypeError, ValueError):
        tubes = 0
    if (
        is_cant_ral_paint_enabled(qi, product_spec=product_spec)
        and tubes > 0
        and not str(qi.get("paint_ral_code") or "").strip()
    ):
        blockers.append(f"{WARNING_PRODUCTION_METADATA_MISSING}:paint_ral_code")
    if normalize_mounting_template_enabled(
        qi.get("mounting_template_enabled"),
        mounting_system=qi.get("mounting_system"),
        mounting_scope=qi.get("mounting_scope"),
        quote_input=qi,
    ):
        if not _positive_number(qi.get("mounting_template_area_m2")):
            blockers.append("quote_input_missing:mounting_template_area_m2")
    mount = normalize_mounting_system(qi.get("mounting_system"))
    if is_mounting_preparation_active(qi) and mount in ("steel_bars", "aluminum_bars"):
        if not str(qi.get("mounting_bar_profile") or "").strip():
            blockers.append("quote_input_missing:mounting_bar_profile")
        if not _positive_number(qi.get("mounting_bar_count")):
            blockers.append("quote_input_missing:mounting_bar_count")
    return blockers


def _classify_capture_warnings(capture_warnings: list[str]) -> tuple[list[str], list[str], list[str]]:
    blockers: list[str] = []
    metadata_blockers: list[str] = []
    warnings: list[str] = []
    for code in capture_warnings:
        if code.startswith(f"{WARNING_ACM_SEPARATE_TEMPLATE}:"):
            blockers.append(code)
        elif code.startswith(f"{WARNING_MOUNTING_BAR_PROFILE_PRICE_MISSING}:"):
            blockers.append(code)
        elif code in FINAL_QUOTE_METADATA_BLOCKERS or code.startswith(
            f"{WARNING_PRODUCTION_METADATA_MISSING}:"
        ):
            metadata_blockers.append(code)
        else:
            warnings.append(code)
    return blockers, metadata_blockers, warnings


def _vector_final_blockers(product_spec: Optional[dict[str, Any]]) -> list[str]:
    if not product_spec:
        return [WARN_LETTERS_VECTOR_FILE_REQUIRED]
    vector = evaluate_volumetric_vector_readiness(product_spec, template_level=False)
    if vector.vector_gate_satisfied:
        return []
    blockers: list[str] = []
    for code in vector.warnings:
        if code in {
            WARN_LETTERS_VECTOR_FILE_REQUIRED,
            WARN_VECTOR_LAYER_MAPPING_PENDING,
            WARN_VECTOR_MANUAL_REVIEW_REQUIRED,
            WARN_VECTOR_ANALYSIS_FAILED,
        }:
            blockers.append(code)
    if not blockers:
        blockers.append("vector_gate_not_satisfied")
    return blockers


def _readiness_section_blockers(readiness_dict: Mapping[str, Any]) -> list[str]:
    """Hard blockers only — section warnings / needs_review status are not blockers."""
    codes: list[str] = []
    for section_key in _READINESS_SECTION_KEYS:
        section = readiness_dict.get(section_key)
        if not isinstance(section, dict):
            continue
        for item in section.get("blockers") or []:
            if item:
                codes.append(str(item))
    top_level = readiness_dict.get("blockers")
    if isinstance(top_level, list):
        for item in top_level:
            if item:
                codes.append(str(item))
    return list(dict.fromkeys(codes))


def _readiness_section_warnings(readiness_dict: Mapping[str, Any]) -> list[str]:
    codes: list[str] = []
    for section_key in _READINESS_SECTION_KEYS:
        section = readiness_dict.get(section_key)
        if not isinstance(section, dict):
            continue
        for item in section.get("warnings") or []:
            if item:
                codes.append(str(item))
    top_level = readiness_dict.get("warnings")
    if isinstance(top_level, list):
        for item in top_level:
            if item:
                codes.append(str(item))
    return list(dict.fromkeys(codes))


def _is_acknowledgeable_warning(code: str) -> bool:
    return any(code == prefix or code.startswith(prefix) for prefix in _ACKNOWLEDGEABLE_WARNING_PREFIXES)


def _warning_satisfied_at_quote(
    code: str,
    *,
    quote_input: Mapping[str, Any],
    product_spec: Optional[Mapping[str, Any]],
) -> bool:
    """Quote-time reminders that are already satisfied do not require acknowledgement."""
    if code == WARN_VECTOR_ANALYSIS_PENDING and product_spec:
        vector = evaluate_volumetric_vector_readiness(dict(product_spec), template_level=False)
        if vector.vector_gate_satisfied:
            return True
    if code.startswith("volumetric_profile_return_depth_required_at_quote:"):
        return _positive_number(quote_input.get("return_depth_mm")) or _positive_number(
            quote_input.get("depth_mm")
        )
    if code.startswith("volumetric_psu_wattage_required_at_quote:"):
        if not is_illumination_enabled(quote_input):
            return True
        return _positive_number(quote_input.get("selected_psu_watts")) or _positive_number(
            quote_input.get("psu_watts")
        )
    if code.startswith("volumetric_profile_depth_variant_pricing:"):
        return _positive_number(quote_input.get("return_depth_mm")) or _positive_number(
            quote_input.get("depth_mm")
        )
    if code.startswith("volumetric_psu_wattage_variant_pricing:"):
        if not is_illumination_enabled(quote_input):
            return True
        return _positive_number(quote_input.get("selected_psu_watts")) or _positive_number(
            quote_input.get("psu_watts")
        )
    return False


def _volumetric_commercial_ready(
    *,
    template_active: bool,
    readiness_dict: Mapping[str, Any],
    section_blockers: list[str],
) -> bool:
    if not template_active:
        return False
    overall = str(readiness_dict.get("overall_status") or "")
    if overall in {"blocked", "draft"}:
        return False
    return len(section_blockers) == 0


def _pending_acknowledgement_warnings(
    warnings: list[str],
    *,
    quote_input: Mapping[str, Any],
    product_spec: Optional[Mapping[str, Any]],
) -> list[str]:
    pending: list[str] = []
    for code in warnings:
        if not _is_acknowledgeable_warning(code):
            pending.append(code)
            continue
        if not _warning_satisfied_at_quote(code, quote_input=quote_input, product_spec=product_spec):
            pending.append(code)
    return list(dict.fromkeys(pending))


def evaluate_volumetric_quote_ready(
    *,
    template_code: str,
    template_active: bool,
    readiness_dict: Mapping[str, Any],
    cost_blockers: list[str] | None = None,
    cost_warnings: list[str] | None = None,
    quote_input: Mapping[str, Any] | None = None,
    product_spec: Mapping[str, Any] | None = None,
) -> VolumetricQuoteReadyResult:
    """Evaluate simulate vs final commercial quote readiness."""
    if not is_volumetric_template_code(template_code):
        return VolumetricQuoteReadyResult(
            notes=["not_volumetric_template"],
        )

    cost_blockers = list(cost_blockers or [])
    cost_warnings = list(cost_warnings or [])
    qi = dict(quote_input or {})
    spec = dict(product_spec) if product_spec else None

    simulate_ready = len(cost_blockers) == 0

    geometry_blockers = _collect_geometry_blockers(qi, product_spec=spec)
    vector_blockers = _vector_final_blockers(spec)
    capture_warnings = collect_volumetric_captured_unpriced_warnings(
        template_code, qi, product_spec=spec
    )
    capture_blockers, metadata_blockers, capture_soft_warnings = _classify_capture_warnings(
        capture_warnings
    )
    readiness_section_blockers = _readiness_section_blockers(readiness_dict)
    readiness_section_warnings = _readiness_section_warnings(readiness_dict)

    dossier_ready = _volumetric_commercial_ready(
        template_active=template_active,
        readiness_dict=readiness_dict,
        section_blockers=readiness_section_blockers,
    )

    all_warnings = list(
        dict.fromkeys(cost_warnings + capture_soft_warnings + readiness_section_warnings)
    )
    ack_pending = _pending_acknowledgement_warnings(
        all_warnings,
        quote_input=qi,
        product_spec=spec,
    )

    classified = {
        "cost_blockers": cost_blockers,
        "readiness_blockers": readiness_section_blockers,
        "geometry_blockers": geometry_blockers,
        "vector_blockers": vector_blockers,
        "production_metadata_blockers": metadata_blockers + [
            c for c in capture_blockers if c.startswith(WARNING_PRODUCTION_METADATA_MISSING)
        ],
        "capture_blockers": [c for c in capture_blockers if not c.startswith(WARNING_PRODUCTION_METADATA_MISSING)],
        "warnings": all_warnings,
        "acknowledgement_pending": ack_pending,
    }

    all_blockers = list(
        dict.fromkeys(
            cost_blockers
            + readiness_section_blockers
            + geometry_blockers
            + vector_blockers
            + metadata_blockers
            + [c for c in capture_blockers if c not in metadata_blockers]
        )
    )

    can_create = (
        simulate_ready
        and dossier_ready
        and len(geometry_blockers) == 0
        and len(vector_blockers) == 0
        and len(metadata_blockers) == 0
        and len([c for c in capture_blockers if c not in metadata_blockers]) == 0
    )
    ready_for_quote = can_create

    reason_codes: list[str] = []
    if not can_create:
        reason_codes.extend(all_blockers)
    elif ack_pending:
        reason_codes.extend([f"acknowledgement_required:{c}" for c in ack_pending])

    notes: list[str] = []
    if simulate_ready and not can_create:
        notes.append("Simulare preliminară permisă; oferta comercială finală rămâne blocată.")
    if can_create and ack_pending:
        notes.append(
            "Oferta comercială poate fi creată; confirmă avertismentele înainte de conversie în comandă."
        )
    if spec and vector_blockers:
        notes.append("Vector verificat parțial — gate final necesită fișier + layer litere + review manual sau geometrie validă.")

    return VolumetricQuoteReadyResult(
        simulate_ready=simulate_ready,
        ready_for_quote=ready_for_quote,
        can_create_commercial_quote=can_create,
        requires_acknowledgement=bool(can_create and ack_pending),
        blockers=all_blockers,
        warnings=all_warnings,
        notes=notes,
        classified=classified,
        reason_codes=reason_codes,
    )
