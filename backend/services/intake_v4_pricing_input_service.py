"""Intake V4 → V3 pricing_input adapter (Sprint 2)."""

from __future__ import annotations

from typing import Any

from schemas.intake_v4 import (
    IntakeV4FinishSetup,
    IntakeV4LetterGroupFinish,
    IntakeV4PricingInputPreviewResponse,
    IntakeV4WorkspacePayload,
)
from services.intake_v3_pricing_input_adapter import build_pricing_input_candidate
from services.intake_v4_finish_adapter import (
    build_path_geometry_summary_from_v4_payload,
    build_v3_workspace_from_v4_payload,
    derive_operation_flags_from_v4_finish,
    finish_assignment_from_v4_setup,
)
from services.intake_v4_led_lighting_service import (
    normalize_led_module_power_w,
    normalize_led_strip_power_w_per_ml,
)
from services.intake_v4_ral_paint_rules_service import (
    RAL_PAINT_SPRAY_COVERAGE_M_PER_TUBE,
    VOLUME_FINISH_PAINT_RAL,
    estimate_intake_v4_ral_paint_spray,
)
from services.intake_v4_volumetric_return_metrics_service import return_finish_active

DEFAULT_FOREX_BACKING_THICKNESS_MM = 10.0
DEFAULT_FOREX_BEVEL_DEPTH_MM = 7.0
RAW_VECTOR_TOTAL_MIN_DELTA_M = 0.05

FACE_VINYL_FINISH_TYPES = frozenset(
    {
        "oracal",
        "oracal_651",
        "oracal_641",
        "oracal_8500",
        "651",
        "641",
        "8500",
        "vinyl",
        "translucent_film",
        "print_laminate",
        "printed_vinyl",
        "printed_laminated_vinyl",
    }
)
FACE_FINISH_NONE_TYPES = frozenset({"none", "raw", "no_finish", "colored_plexiglas"})
RETURN_VINYL_FINISH_TYPES = frozenset({"oracal_wrapped", "oracal_651", "oracal", "vinyl"})
RETURN_PAINT_FINISH_TYPES = frozenset({"ral_paint", "painted", "paint"})
RETURN_RAW_FINISH_TYPES = frozenset(
    {
        "none",
        "white_aluminum",
        "black_aluminum",
        "gold_aluminum",
        "mirror_silver",
        "standard_aluminum",
        "raw_material",
        "raw",
        "prefinished",
    }
)
ORACAL_SERIES_LABELS = {
    "641": "Oracal 641",
    "651": "Oracal 651",
    "8500": "Oracal 8500",
}


def _optional_string(raw: Any) -> str:
    return str(raw or "").strip()


def _token(raw: Any, *, default: str = "") -> str:
    value = _optional_string(raw).lower()
    return value or default


def _positive_number(raw: Any) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def _raw_vector_total_perimeter_m(path_geometry: dict[str, Any]) -> float | None:
    candidates: list[float] = []
    contour_split = path_geometry.get("contour_split")
    if isinstance(contour_split, dict):
        total_mm = _positive_number(contour_split.get("total_cutting_perimeter_mm"))
        if total_mm is not None:
            candidates.append(total_mm / 1000.0)
    perimeter_mm = _positive_number(path_geometry.get("perimeter_mm_approx"))
    if perimeter_mm is not None:
        candidates.append(perimeter_mm / 1000.0)
    if not candidates:
        return None
    return round(max(candidates), 4)


def _raw_vector_total_should_override(raw_total_m: float | None, current_m: float | None) -> bool:
    if raw_total_m is None:
        return False
    if current_m is None:
        return True
    return raw_total_m > current_m + RAW_VECTOR_TOTAL_MIN_DELTA_M


def _compact_number(raw: Any) -> float | int | None:
    value = _positive_number(raw)
    if value is None:
        return None
    if value.is_integer():
        return int(value)
    return value


def _format_color_line(color_code: str | None, color_name: str | None) -> str | None:
    code = _optional_string(color_code)
    name = _optional_string(color_name)
    if code and name:
        return f"{code} {name}"
    if code:
        return code
    if name:
        return name
    return None


def _normalize_oracal_material_label(series: str | None) -> str:
    code = _optional_string(series).lower().replace("oracal", "").replace("_", " ").strip()
    if code in ORACAL_SERIES_LABELS:
        return ORACAL_SERIES_LABELS[code]
    if code.isdigit():
        return f"Oracal {code}"
    return "Oracal 651"


def _group_label(group: IntakeV4LetterGroupFinish) -> str:
    return _optional_string(group.layer_name) or group.group_key


def _face_oracal_series(raw_finish: str) -> str:
    if raw_finish in {"oracal_8500", "8500", "translucent_film"}:
        return "8500"
    if raw_finish in {"oracal_641", "641"}:
        return "641"
    return "651"


def _template_face_finish_type(raw_finish: str) -> str:
    if raw_finish in FACE_FINISH_NONE_TYPES:
        return "none"
    if raw_finish in {"print_laminate", "printed_laminated_vinyl"}:
        return "printed_laminated_vinyl"
    if raw_finish == "printed_vinyl":
        return "printed_vinyl"
    if raw_finish in FACE_VINYL_FINISH_TYPES:
        return "oracal_651"
    return raw_finish or "none"


def _template_return_finish_type(raw_finish: str) -> str:
    if raw_finish in RETURN_VINYL_FINISH_TYPES:
        return "oracal_651"
    if raw_finish in RETURN_PAINT_FINISH_TYPES:
        return "paint_after_face_miter_bond"
    if raw_finish in RETURN_RAW_FINISH_TYPES:
        return "none"
    return raw_finish or "none"


def _add_group_metrics(target: dict[str, Any], group: IntakeV4LetterGroupFinish) -> None:
    if group.face_area_m2 is not None:
        target["face_area_m2"] = group.face_area_m2
    if group.perimeter_m is not None:
        target["perimeter_m"] = group.perimeter_m
    if group.element_count is not None:
        target["element_count"] = group.element_count
    if group.source_fill_color:
        target["source_fill_color"] = group.source_fill_color


def _letter_group_return_perimeter_m(setup: IntakeV4FinishSetup) -> float | None:
    total = 0.0
    found = False
    default_return_finish = setup.return_finish_type
    for group in setup.letter_group_finishes:
        finish = group.return_finish_type or default_return_finish
        if not return_finish_active(finish):
            continue
        perimeter = _positive_number(group.perimeter_m)
        if perimeter is None:
            continue
        total += perimeter
        found = True
    return round(total, 4) if found else None


def _normalize_face_group(
    group: IntakeV4LetterGroupFinish,
    *,
    setup_roll_width_mm: float | None,
) -> dict[str, Any] | None:
    raw = _token(group.face_finish_type, default="none")
    if raw in FACE_FINISH_NONE_TYPES or raw not in FACE_VINYL_FINISH_TYPES:
        return None

    face_finish_type = _template_face_finish_type(raw)
    face_finish_subtype: str | None = None
    material = "Autocolant fata litere"
    if raw in {"print_laminate", "printed_laminated_vinyl"}:
        material = "Autocolant print + laminare"
    elif raw == "printed_vinyl":
        material = "Autocolant print"
    else:
        series = _face_oracal_series(raw)
        material = _normalize_oracal_material_label(series)
        if series == "8500":
            face_finish_subtype = "oracal_8500"

    roll_width = _compact_number(group.face_vinyl_roll_width_mm) or _compact_number(
        setup_roll_width_mm
    )
    normalized: dict[str, Any] = {
        "group_id": group.group_key,
        "group_label": _group_label(group),
        "face_finish_raw": raw,
        "face_finish_type": face_finish_type,
        "face_finish_subtype": face_finish_subtype,
        "face_vinyl_enabled": True,
        "face_vinyl_material": material,
        "face_vinyl_color_code": _optional_string(group.face_oracal_code) or None,
        "face_vinyl_color_name": _optional_string(group.face_oracal_name) or None,
        "face_vinyl_color": _format_color_line(group.face_oracal_code, group.face_oracal_name),
    }
    if raw not in {"print_laminate", "printed_vinyl", "printed_laminated_vinyl"}:
        normalized["face_oracal_series"] = _face_oracal_series(raw)
    if roll_width is not None:
        normalized["face_vinyl_roll_width_mm"] = roll_width
    _add_group_metrics(normalized, group)
    return normalized


def _normalize_return_group(
    group: IntakeV4LetterGroupFinish,
    *,
    setup_return_depth_mm: float | None,
) -> dict[str, Any] | None:
    raw = _token(group.return_finish_type, default="none")
    if raw not in RETURN_VINYL_FINISH_TYPES:
        return None

    depth = _compact_number(group.return_depth_mm) or _compact_number(setup_return_depth_mm)
    normalized: dict[str, Any] = {
        "group_id": group.group_key,
        "group_label": _group_label(group),
        "return_finish_raw": raw,
        "return_finish_type": "oracal_wrapped",
        "return_vinyl_enabled": True,
        "return_vinyl_material": "Oracal 651",
        "return_vinyl_color_code": _optional_string(group.return_oracal_code) or None,
        "return_vinyl_color_name": _optional_string(group.return_oracal_name) or None,
        "return_vinyl_color": _format_color_line(
            group.return_oracal_code,
            group.return_oracal_name,
        ),
    }
    if depth is not None:
        normalized["return_depth_mm"] = depth
    _add_group_metrics(normalized, group)
    return normalized


def _groups_are_uniform(groups: list[dict[str, Any]], keys: tuple[str, ...]) -> bool:
    if len(groups) <= 1:
        return True
    signatures = {tuple(group.get(key) for key in keys) for group in groups}
    return len(signatures) == 1


def _letter_group_finish_matrix(setup: IntakeV4FinishSetup) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    for group in setup.letter_group_finishes:
        face_raw = _token(group.face_finish_type, default="none")
        return_raw = _token(group.return_finish_type, default="none")
        row: dict[str, Any] = {
            "group_id": group.group_key,
            "group_label": _group_label(group),
            "face_finish_type": face_raw,
            "face_finish_template_type": _template_face_finish_type(face_raw),
            "face_oracal_code": _optional_string(group.face_oracal_code) or None,
            "face_oracal_name": _optional_string(group.face_oracal_name) or None,
            "return_finish_type": return_raw,
            "return_finish_template_type": _template_return_finish_type(return_raw),
            "return_oracal_code": _optional_string(group.return_oracal_code) or None,
            "return_oracal_name": _optional_string(group.return_oracal_name) or None,
            "return_depth_mm": _compact_number(group.return_depth_mm)
            or _compact_number(setup.return_depth_mm),
            "confirmed": group.confirmed is True or setup.confirmed is True,
        }
        _add_group_metrics(row, group)
        matrix.append(row)
    return matrix


def _apply_letter_group_finish_handoff(
    patched: dict[str, Any],
    setup: IntakeV4FinishSetup,
) -> bool:
    if not setup.letter_group_finishes:
        return False

    face_groups = [
        normalized
        for group in setup.letter_group_finishes
        if (
            normalized := _normalize_face_group(
                group,
                setup_roll_width_mm=setup.face_vinyl_roll_width_mm,
            )
        )
    ]
    return_groups = [
        normalized
        for group in setup.letter_group_finishes
        if (
            normalized := _normalize_return_group(
                group,
                setup_return_depth_mm=setup.return_depth_mm,
            )
        )
    ]
    matrix = _letter_group_finish_matrix(setup)

    patched["letter_group_count"] = len(setup.letter_group_finishes)
    patched["letter_group_finish_source"] = "intake_v4_finish_setup"
    patched["letter_group_finish_matrix"] = matrix
    patched["grouped_finish_pricing_mode"] = "per_group_handoff"
    patched["requires_grouped_finish_review"] = False

    if face_groups:
        patched["letter_group_face_vinyl_handoff"] = {
            "groups": face_groups,
            "uniform_all_letters": _groups_are_uniform(
                face_groups,
                (
                    "face_finish_type",
                    "face_finish_subtype",
                    "face_oracal_series",
                    "face_vinyl_material",
                    "face_vinyl_color_code",
                    "face_vinyl_color_name",
                    "face_vinyl_roll_width_mm",
                ),
            ),
            "source": "intake_v4_finish_setup",
        }
        patched["face_vinyl_group_count"] = len(face_groups)
        patched["face_finish_variation_count"] = len(
            {
                (
                    group.get("face_finish_type"),
                    group.get("face_finish_subtype"),
                    group.get("face_oracal_series"),
                    group.get("face_vinyl_color_code"),
                    group.get("face_vinyl_color_name"),
                    group.get("face_vinyl_roll_width_mm"),
                )
                for group in face_groups
            }
        )

    if return_groups:
        patched["letter_group_return_vinyl_handoff"] = {
            "groups": return_groups,
            "uniform_all_letters": _groups_are_uniform(
                return_groups,
                (
                    "return_vinyl_material",
                    "return_vinyl_color_code",
                    "return_vinyl_color_name",
                    "return_depth_mm",
                ),
            ),
            "source": "intake_v4_finish_setup",
        }
        patched["return_vinyl_group_count"] = len(return_groups)
        patched["return_finish_variation_count"] = len(
            {
                (
                    group.get("return_vinyl_material"),
                    group.get("return_vinyl_color_code"),
                    group.get("return_vinyl_color_name"),
                    group.get("return_depth_mm"),
                )
                for group in return_groups
            }
        )

    return True


def _resolve_v4_backing_presence(payload: IntakeV4WorkspacePayload) -> dict[str, Any]:
    """Operator backing mode (finish_setup) with layer-role fallback."""
    finish_raw = payload.finish_setup.model_dump(mode="json") if payload.finish_setup else {}
    layer_setup_raw = (
        payload.layer_role_setup.model_dump(mode="json") if payload.layer_role_setup else None
    )
    quote_geom = payload.quote_geometry if isinstance(payload.quote_geometry, dict) else None
    from services.intake_v4_backing_mode_service import (
        apply_backing_state_to_geometry_patch,
        resolve_volumetric_backing_state,
    )

    mode, backing_present, back_bevel = resolve_volumetric_backing_state(
        finish_raw,
        layer_setup_raw,
        quote_geometry=quote_geom,
    )
    patch: dict[str, Any] = {
        "backing_present": backing_present,
        "backing_mode": mode,
    }
    if backing_present:
        patch["backing_material"] = "FOREX_10MM"
        patch["backing_thickness_mm"] = DEFAULT_FOREX_BACKING_THICKNESS_MM
        patch["back_material"] = "FOREX_10MM"
    else:
        patch["backing_material"] = None
    return apply_backing_state_to_geometry_patch(
        patch,
        backing_present=backing_present,
        back_bevel_enabled=back_bevel,
    )


def _patch_quote_input_from_v4_geometry(
    quote_input: dict[str, Any],
    path_geometry: dict[str, Any],
    payload: IntakeV4WorkspacePayload,
) -> dict[str, Any]:
    patched = dict(quote_input)
    for key in (
        "letter_perimeter_m",
        "total_letter_perimeter_ml",
        "return_material_perimeter_ml",
        "face_cutting_perimeter_ml",
        "cutting_perimeter_ml",
        "hole_perimeter_ml",
        "face_area_m2",
        "letter_face_area_m2",
        "artwork_area_m2",
        "letter_count",
        "real_letters_count",
        "inner_holes_count",
        "cutting_contours_count",
        "material_piece_count",
        "letter_return_perimeter_ml",
        "artwork_return_perimeter_ml",
        "led_perimeter_ml",
        "artwork_piece_count",
        "volumetric_piece_count",
        "cnc_cutting_perimeter_ml",
        "bevel_perimeter_ml",
    ):
        value = path_geometry.get(key)
        if value is not None:
            patched[key] = value

    cnc_perimeter = path_geometry.get("cnc_cutting_perimeter_ml")
    if cnc_perimeter is not None:
        patched.setdefault("cnc_cutting_perimeter_ml", cnc_perimeter)
        # Face bevel dry-run / geometry summary — same contour scope as CNC cutting when bevel active.
        patched.setdefault("bevel_perimeter_ml", cnc_perimeter)

    if "back_bevel_enabled" not in patched:
        patched["back_bevel_enabled"] = False

    svg_source = payload.svg_source
    if svg_source is not None:
        vector_file = (
            _optional_string(getattr(svg_source, "file_name", None))
            or _optional_string(getattr(svg_source, "file_hash", None))
            or _optional_string(getattr(svg_source, "upload_status", None))
        )
        if vector_file:
            patched["vector_file"] = vector_file

    backing_patch = _resolve_v4_backing_presence(payload)
    patched.update(backing_patch)
    if patched.get("backing_present") and patched.get("back_bevel_enabled"):
        patched.setdefault("back_bevel_depth_mm", DEFAULT_FOREX_BEVEL_DEPTH_MM)

    setup = payload.finish_setup
    if setup:
        patched["illuminated"] = setup.illuminated is not False
        patched["lighting_system_type"] = setup.lighting_system_type
        patched["light_color"] = setup.light_color
        module_power = normalize_led_module_power_w(setup.led_module_power_w)
        patched["led_module_power_w"] = module_power
        patched["module_wattage"] = module_power
        strip_power = normalize_led_strip_power_w_per_ml(setup.led_strip_power_w_per_ml)
        patched["led_strip_power_w_per_ml"] = strip_power
        lighting_system = str(setup.lighting_system_type or "").strip().lower()
        if lighting_system == "led_strip":
            if setup.total_led_strip_length_m is not None:
                patched["led_strip_length_m"] = setup.total_led_strip_length_m
            if setup.letter_led_strip_length_m is not None:
                patched["letter_led_strip_length_m"] = setup.letter_led_strip_length_m
            if setup.emblem_led_strip_length_m is not None:
                patched["emblem_led_strip_length_m"] = setup.emblem_led_strip_length_m
        elif setup.led_module_count is not None:
            patched["led_module_count"] = setup.led_module_count
        if setup.estimated_led_watts is not None:
            patched["estimated_led_watts"] = setup.estimated_led_watts
        if setup.required_psu_watts is not None:
            patched["required_psu_watts"] = setup.required_psu_watts
        if setup.selected_psu_watts is not None:
            patched["selected_psu_watts"] = int(setup.selected_psu_watts)
        if setup.psu_configuration:
            patched["psu_configuration"] = list(setup.psu_configuration)
            patched.setdefault("selected_psu_watts", max(int(w) for w in setup.psu_configuration))
        if setup.back_bevel_enabled is not None:
            patched["back_bevel_enabled"] = bool(setup.back_bevel_enabled)
        if setup.mounting_template_enabled is not None:
            patched["mounting_template_enabled"] = bool(setup.mounting_template_enabled)
        if setup.mounting_template_area_m2 is not None:
            patched["mounting_template_area_m2"] = setup.mounting_template_area_m2
        if setup.mounting_template_material_type:
            patched["mounting_template_material_type"] = setup.mounting_template_material_type
        if setup.mounting_solution is not None:
            patched["mounting_solution"] = setup.mounting_solution.model_dump(mode="json")
            solution = setup.mounting_solution
            config = solution.configuration if isinstance(solution.configuration, dict) else {}
            bar_material = str(config.get("bar_material") or "steel").strip().lower()
            patched["bar_material"] = bar_material
            if config.get("mounting_bar_profile"):
                patched["mounting_bar_profile"] = config["mounting_bar_profile"]
            if config.get("bar_count") is not None:
                patched["mounting_bar_count"] = config["bar_count"]
            patched["metal_support_required"] = True
            from services.mounting_solution_service import legacy_mounting_system_from_solution

            legacy_ms = legacy_mounting_system_from_solution(solution.model_dump(mode="json"))
            if legacy_ms:
                patched["mounting_system"] = legacy_ms
        elif setup.mounting_system:
            patched["mounting_system"] = setup.mounting_system
            if setup.mounting_bar_profile:
                patched["mounting_bar_profile"] = setup.mounting_bar_profile
        if setup.mounting_scope is not None:
            patched["mounting_scope"] = setup.mounting_scope
        if setup.site_installation_included is not None:
            patched["site_installation_included"] = bool(setup.site_installation_included)
        if setup.letter_group_finishes:
            _apply_letter_group_finish_handoff(patched, setup)
            group_return_perimeter = _letter_group_return_perimeter_m(setup)
            if group_return_perimeter is not None:
                patched["return_material_perimeter_ml"] = group_return_perimeter
                patched["letter_return_perimeter_ml"] = group_return_perimeter
        if setup.artwork_finishes:
            patched["artwork_layer_count"] = len(setup.artwork_finishes)

    raw_vector_total = _raw_vector_total_perimeter_m(path_geometry)
    current_vector_total = _positive_number(patched.get("return_material_perimeter_ml"))
    if _raw_vector_total_should_override(raw_vector_total, current_vector_total):
        letter_return = _positive_number(patched.get("letter_return_perimeter_ml"))
        residual = (
            round(raw_vector_total - letter_return, 4)
            if raw_vector_total is not None and letter_return is not None
            else None
        )
        patched["return_material_perimeter_ml"] = raw_vector_total
        patched["face_cutting_perimeter_ml"] = raw_vector_total
        patched["cutting_perimeter_ml"] = raw_vector_total
        patched["cnc_cutting_perimeter_ml"] = raw_vector_total
        patched["bevel_perimeter_ml"] = raw_vector_total
        patched["raw_vector_total_perimeter_ml"] = raw_vector_total
        patched["vector_total_perimeter_source"] = "path_geometry_summary.perimeter_mm_approx"
        if residual is not None and residual > RAW_VECTOR_TOTAL_MIN_DELTA_M:
            patched["artwork_return_perimeter_ml"] = residual

    if setup:
        setup_dict = setup.model_dump(mode="json")
        ral_estimate = estimate_intake_v4_ral_paint_spray(
            finish_setup=setup_dict,
            geometry=patched,
            analysis=payload.svg_analysis_json if isinstance(payload.svg_analysis_json, dict) else {},
            default_return_finish=setup.return_finish_type,
        )
        if ral_estimate is not None:
            patched["estimated_paint_tubes"] = ral_estimate.raw_tubes
            patched["paint_tube_count"] = ral_estimate.raw_tubes
            patched["painted_return_perimeter_m"] = ral_estimate.painted_return_m
            patched["painted_letter_return_perimeter_m"] = ral_estimate.letter_painted_return_m
            patched["painted_artwork_return_perimeter_m"] = ral_estimate.artwork_painted_return_m
            patched["paint_tube_coverage_m_per_tube"] = RAL_PAINT_SPRAY_COVERAGE_M_PER_TUBE
            if ral_estimate.paint_ral_code:
                patched["paint_ral_code"] = ral_estimate.paint_ral_code
            if ral_estimate.paint_ral_name:
                patched["paint_ral_name"] = ral_estimate.paint_ral_name
            if ral_estimate.all_letter_returns_painted:
                patched["volume_finish"] = VOLUME_FINISH_PAINT_RAL

    patched["intake_source"] = "intake_v4"
    patched["geometry_calculation_quality"] = path_geometry.get("calculation_quality")
    return patched


def build_v4_pricing_input_preview(
    *,
    workspace_id: str,
    payload: IntakeV4WorkspacePayload,
) -> IntakeV4PricingInputPreviewResponse:
    v3_workspace = build_v3_workspace_from_v4_payload(payload)
    result = build_pricing_input_candidate(v3_workspace)
    path_geometry = build_path_geometry_summary_from_v4_payload(payload)

    finish = finish_assignment_from_v4_setup(payload.finish_setup)
    illuminated = payload.finish_setup.illuminated is not False if payload.finish_setup else True
    flags = derive_operation_flags_from_v4_finish(finish, illuminated=illuminated)

    quote_input = _patch_quote_input_from_v4_geometry(
        result.quote_input_payload,
        path_geometry,
        payload,
    )
    quote_input["operation_flags"] = flags.model_dump()

    production = result.candidate.production_counts
    finish_summary = result.candidate.finish_summary

    letter_count = path_geometry.get("real_letters_count") or path_geometry.get("letter_count")
    if letter_count is None:
        letter_count = production.letter_count
    try:
        letter_count_int = int(letter_count) if letter_count is not None else production.letter_count
    except (TypeError, ValueError):
        letter_count_int = production.letter_count

    inner_hole_count = path_geometry.get("inner_holes_count")
    if inner_hole_count is None:
        inner_hole_count = production.inner_hole_count
    try:
        inner_hole_count_int = int(inner_hole_count) if inner_hole_count is not None else production.inner_hole_count
    except (TypeError, ValueError):
        inner_hole_count_int = production.inner_hole_count

    cut_contour_count = path_geometry.get("cutting_contours_count")
    if cut_contour_count is None:
        cut_contour_count = (letter_count_int or 0) + (inner_hole_count_int or 0)
    try:
        cut_contour_count_int = int(cut_contour_count) if cut_contour_count is not None else production.cut_contour_count
    except (TypeError, ValueError):
        cut_contour_count_int = production.cut_contour_count

    production_counts = {
        "letter_count": letter_count_int,
        "real_letters_count": letter_count_int,
        "cut_contour_count": cut_contour_count_int,
        "inner_hole_count": inner_hole_count_int,
        "cutting_contours_count": cut_contour_count_int,
        "material_piece_count": path_geometry.get("material_piece_count") or letter_count_int,
        "volumetric_piece_count": path_geometry.get("volumetric_piece_count"),
        "artwork_piece_count": path_geometry.get("artwork_piece_count"),
    }

    artwork_warnings: list[str] = []
    if payload.finish_setup and payload.finish_setup.artwork_finishes:
        for row in payload.finish_setup.artwork_finishes:
            if (row.execution_type or "needs_decision") == "needs_decision":
                artwork_warnings.append(
                    f"Artwork „{row.layer_name or row.layer_key}” — metodă execuție nedecisă."
                )

    adapter_warnings = list(result.adapter_warnings) + artwork_warnings
    grouped_finish_handoff = quote_input.get("grouped_finish_pricing_mode") == "per_group_handoff"
    requires_grouped_finish_review = result.candidate.requires_grouped_finish_review
    if grouped_finish_handoff:
        requires_grouped_finish_review = False
        quote_input["requires_grouped_finish_review"] = False

    finish_summary_payload: dict[str, Any] = {
        "face_finish_type": finish_summary.face_finish_type,
        "face_vinyl_enabled": finish_summary.face_vinyl_enabled,
        "return_finish_type": finish_summary.return_finish_type,
        "return_depth_mm": finish_summary.return_depth_mm,
        "return_wrapped": finish_summary.return_wrapped,
        "return_painted": finish_summary.return_painted,
    }
    for key in (
        "letter_group_count",
        "grouped_finish_pricing_mode",
        "face_vinyl_group_count",
        "return_vinyl_group_count",
        "face_finish_variation_count",
        "return_finish_variation_count",
        "letter_group_finish_matrix",
    ):
        if key in quote_input:
            finish_summary_payload[key] = quote_input[key]

    return IntakeV4PricingInputPreviewResponse(
        workspace_id=workspace_id,
        template_code=payload.product_binding.template_code,
        is_ready_for_quote=result.is_ready_for_quote,
        adapter_status=result.adapter_status,
        adapter_blockers=list(result.adapter_blockers),
        adapter_warnings=adapter_warnings,
        quote_input_payload=quote_input,
        operation_flags=flags.model_dump(),
        production_counts=production_counts,
        finish_summary=finish_summary_payload,
        readiness_status=result.candidate.readiness_summary.status,
        requires_grouped_finish_review=requires_grouped_finish_review,
        preview_only=True,
    )
