"""Map Intake V4 finish_setup → Intake V3 FinishAssignment (Sprint 1 alignment)."""

from __future__ import annotations

import math
from typing import Any

from schemas.intake_v3 import (
    ConfirmedProductionModel,
    CutContourItem,
    CutContourModel,
    FaceFinishSpec,
    FinishAssignment,
    FinishGroupAssignment,
    FinishType,
    IntakeV3LightingPlan,
    IntakeV3PsuPlanUnit,
    IntakeV3Workspace,
    LetterModel,
    OperationFlags,
    ProductSelection,
    RawSvgAnalysis,
    ReturnFinishSpec,
    SupportContext,
    VectorAsset,
)
from schemas.intake_v4 import (
    IntakeV4ArtworkFinish,
    IntakeV4FinishSetup,
    IntakeV4LetterGroupFinish,
    IntakeV4WorkspacePayload,
)
from services.intake_v3_finish_material_service import derive_operation_flags_from_finishes
from services.intake_v3_lighting_plan_service import sync_lighting_plan
from services.intake_v4_quote_geometry_service import resolve_v4_quote_geometry

DEFAULT_LED_MODULE_POWER_W = 0.75
VOLUMETRIC_LED_PITCH_MM = 100.0  # 75 mm module + 25 mm gap — matches frontend V2 rule

_LIGHT_COLOR_MAP = {
    "warm": "warm_white",
    "warm_white": "warm_white",
    "neutral": "neutral_white",
    "neutral_white": "neutral_white",
    "cold": "cold_white",
    "cold_white": "cold_white",
    "rgb": "rgb",
    "custom": "custom",
}


def _positive(value: float | int | None) -> bool:
    try:
        return value is not None and float(value) > 0
    except (TypeError, ValueError):
        return False


def _resolve_v4_quote_geometry(payload: IntakeV4WorkspacePayload) -> dict[str, Any]:
    """Canonical geometry — delegates to ``resolve_v4_quote_geometry``."""
    return resolve_v4_quote_geometry(payload)


def _compute_led_module_count_from_perimeter(perimeter_m: float | None) -> int | None:
    if perimeter_m is None or perimeter_m <= 0:
        return None
    return int(math.ceil((float(perimeter_m) * 1000.0) / VOLUMETRIC_LED_PITCH_MM))


def _map_v4_light_color(raw: str | None) -> str | None:
    if not raw:
        return None
    token = raw.strip().lower()
    return _LIGHT_COLOR_MAP.get(token, token)


def _map_v4_led_system(raw: str | None) -> str:
    token = (raw or "led_modules").strip().lower()
    if token in {"led_modules", "led_module", "modules"}:
        return "modules"
    if token in {"led_strip", "strip"}:
        return "strip"
    return token or "modules"


def _resolve_face_roll_width_mm(
    *,
    group_roll_width: float | None,
    setup_roll_width: float | None,
) -> float | None:
    if _positive(group_roll_width):
        return float(group_roll_width)
    if _positive(setup_roll_width):
        return float(setup_roll_width)
    return None

_RETURN_PAINTED = frozenset({"ral_paint", "painted", "paint"})
_RETURN_WRAPPED = frozenset({"oracal_wrapped", "oracal_651", "vinyl"})
_RETURN_RAW = frozenset(
    {
        "white_aluminum",
        "black_aluminum",
        "gold_aluminum",
        "standard_aluminum",
        "mirror_silver",
        "raw_material",
        "raw",
        "prefinished",
    }
)


def _map_v4_face_finish(
    group: IntakeV4LetterGroupFinish,
    *,
    setup_confirmed: bool = False,
    setup_roll_width_mm: float | None = None,
) -> FaceFinishSpec:
    raw = (group.face_finish_type or "oracal_651").strip().lower()
    confirmed = group.confirmed is True or setup_confirmed
    roll_width_mm = _resolve_face_roll_width_mm(
        group_roll_width=group.face_vinyl_roll_width_mm,
        setup_roll_width=setup_roll_width_mm,
    )

    if raw == "none":
        return FaceFinishSpec(finish_type="none", enabled=True, confirmed=confirmed)

    if raw == "oracal_8500":
        return FaceFinishSpec(
            finish_type="oracal_8500",
            material_code="8500",
            color_code=group.face_oracal_code,
            color_name=group.face_oracal_name,
            face_vinyl_roll_width_mm=roll_width_mm,
            confirmed=confirmed,
        )

    if raw == "oracal_641":
        return FaceFinishSpec(
            finish_type="vinyl",
            material_code="641",
            color_code=group.face_oracal_code,
            color_name=group.face_oracal_name,
            face_vinyl_roll_width_mm=roll_width_mm,
            confirmed=confirmed,
        )

    if raw == "print_laminate":
        return FaceFinishSpec(
            finish_type="printed_vinyl",
            face_vinyl_roll_width_mm=roll_width_mm,
            confirmed=confirmed,
        )

    # oracal_651 and legacy aliases → vinyl gate for operation catalog
    return FaceFinishSpec(
        finish_type="vinyl",
        material_code="651",
        color_code=group.face_oracal_code,
        color_name=group.face_oracal_name,
        face_vinyl_roll_width_mm=roll_width_mm,
        confirmed=confirmed,
    )


def _map_v4_return_finish(
    *,
    return_finish_type: str | None,
    return_oracal_code: str | None,
    return_depth_mm: float | None,
    confirmed: bool,
) -> ReturnFinishSpec:
    raw = (return_finish_type or "oracal_wrapped").strip().lower()

    if raw in _RETURN_PAINTED:
        return ReturnFinishSpec(
            finish_type="painted",
            material_code="RAL",
            color_code=return_oracal_code,
            return_depth_mm=return_depth_mm,
            confirmed=confirmed,
        )

    if raw in _RETURN_WRAPPED:
        finish_type: FinishType = "oracal_wrapped" if raw == "oracal_wrapped" else "oracal_651"
        return ReturnFinishSpec(
            finish_type=finish_type,
            material_code="651",
            color_code=return_oracal_code,
            return_depth_mm=return_depth_mm,
            confirmed=confirmed,
        )

    if raw in _RETURN_RAW:
        return ReturnFinishSpec(
            finish_type="raw_material",
            material_code=raw,
            return_depth_mm=return_depth_mm,
            confirmed=confirmed,
        )

    return ReturnFinishSpec(
        finish_type="other",
        material_code=raw or None,
        return_depth_mm=return_depth_mm,
        confirmed=confirmed,
    )


def _letter_group_to_v3(
    group: IntakeV4LetterGroupFinish,
    *,
    setup_confirmed: bool = False,
    default_return_depth_mm: float | None = None,
    setup_roll_width_mm: float | None = None,
) -> FinishGroupAssignment:
    group_confirmed = group.confirmed is True or setup_confirmed
    return_depth_mm = group.return_depth_mm if _positive(group.return_depth_mm) else default_return_depth_mm
    return FinishGroupAssignment(
        group_id=group.group_key,
        group_label=group.layer_name or group.group_key,
        face_finish=_map_v4_face_finish(
            group,
            setup_confirmed=setup_confirmed,
            setup_roll_width_mm=setup_roll_width_mm,
        ),
        return_finish=_map_v4_return_finish(
            return_finish_type=group.return_finish_type,
            return_oracal_code=group.return_oracal_code,
            return_depth_mm=return_depth_mm,
            confirmed=group_confirmed,
        ),
        confirmed_by_operator=group_confirmed,
    )


def _pseudo_group_from_global(setup: IntakeV4FinishSetup) -> IntakeV4LetterGroupFinish:
    return IntakeV4LetterGroupFinish(
        group_key="__all__",
        layer_name="Toate literele",
        face_finish_type=setup.face_finish_type,
        return_finish_type=setup.return_finish_type,
        return_depth_mm=setup.return_depth_mm,
        confirmed=setup.confirmed is True,
    )


def finish_assignment_from_v4_setup(setup: IntakeV4FinishSetup | None) -> FinishAssignment | None:
    """Convert V4 finish_setup to V3 FinishAssignment."""
    if setup is None:
        return None

    setup_confirmed = setup.confirmed is True
    letter_groups = list(setup.letter_group_finishes or [])
    if letter_groups:
        groups = [
            _letter_group_to_v3(
                row,
                setup_confirmed=setup_confirmed,
                default_return_depth_mm=setup.return_depth_mm,
                setup_roll_width_mm=setup.face_vinyl_roll_width_mm,
            )
            for row in letter_groups
        ]
        return FinishAssignment(
            assignment_mode="group",
            groups=groups,
            confirmed_by_operator=setup_confirmed,
        )

    return FinishAssignment(
        assignment_mode="all",
        face_finish=_map_v4_face_finish(
            IntakeV4LetterGroupFinish(
                group_key="__all__",
                layer_name="Toate literele",
                face_finish_type=setup.face_finish_type,
                face_vinyl_roll_width_mm=setup.face_vinyl_roll_width_mm,
                return_finish_type=setup.return_finish_type,
                return_depth_mm=setup.return_depth_mm,
                confirmed=setup_confirmed,
            ),
            setup_confirmed=setup_confirmed,
            setup_roll_width_mm=setup.face_vinyl_roll_width_mm,
        ),
        return_finish=_map_v4_return_finish(
            return_finish_type=setup.return_finish_type,
            return_oracal_code=setup.return_oracal_code,
            return_depth_mm=setup.return_depth_mm,
            confirmed=setup_confirmed,
        ),
        confirmed_by_operator=setup_confirmed,
    )


def derive_operation_flags_from_v4_finish(
    finish: FinishAssignment | None,
    *,
    illuminated: bool = True,
    shared_support: bool = False,
) -> OperationFlags:
    """OR operation flags across all finish groups (V4 per-layer truth)."""
    ctx = SupportContext(shared_support=shared_support, illuminated=illuminated)
    if finish is None:
        return OperationFlags()

    groups = finish.active_groups()
    if not groups:
        return derive_operation_flags_from_finishes(finish, ctx)

    merged = OperationFlags()
    for group in groups:
        scoped = FinishAssignment(
            assignment_mode="all",
            face_finish=group.face_finish,
            return_finish=group.return_finish,
            backing_finish=group.backing_finish,
            confirmed_by_operator=group.confirmed_by_operator,
        )
        flags = derive_operation_flags_from_finishes(scoped, ctx)
        merged.return_vinyl_application_required |= flags.return_vinyl_application_required
        merged.return_painting_after_assembly_required |= flags.return_painting_after_assembly_required
        merged.face_vinyl_application_required |= flags.face_vinyl_application_required
        merged.face_vinyl_after_return_painting |= flags.face_vinyl_after_return_painting
        if flags.psu_packed_at_packaging:
            merged.psu_packed_at_packaging = True
        if flags.electrical_source_mounting_allowed:
            merged.electrical_source_mounting_allowed = True

    return merged


def _minimal_cut_contour_model(count: int) -> CutContourModel:
    contours = [
        CutContourItem(
            contour_id=f"letter-{index}",
            role="outer",
            include_in_cut=True,
            sequence_index=index,
        )
        for index in range(1, count + 1)
    ]
    return CutContourModel(
        contours=contours,
        outer_contour_count=count,
        cut_contour_count=count,
    )


def _confirmed_production_model_from_payload(payload: IntakeV4WorkspacePayload) -> ConfirmedProductionModel | None:
    quote = _resolve_v4_quote_geometry(payload)
    letter_count = quote.get("real_letters_count")
    if letter_count is None:
        letter_count = quote.get("letter_count")
    if letter_count is None:
        path = payload.path_geometry_summary if isinstance(payload.path_geometry_summary, dict) else {}
        letter_count = path.get("real_letters_count") or path.get("letter_count")
    try:
        count = int(letter_count) if letter_count is not None else 0
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return None

    inner_hole_count = quote.get("inner_holes_count")
    if inner_hole_count is None:
        path = payload.path_geometry_summary if isinstance(payload.path_geometry_summary, dict) else {}
        inner_hole_count = path.get("inner_holes_count")
    try:
        holes = int(inner_hole_count) if inner_hole_count is not None else 0
    except (TypeError, ValueError):
        holes = 0
    if holes < 0:
        holes = 0

    cut_contour_count = quote.get("cutting_contours_count")
    if cut_contour_count is None:
        cut_contour_count = count + holes
    try:
        cut_count = int(cut_contour_count) if cut_contour_count is not None else count + holes
    except (TypeError, ValueError):
        cut_count = count + holes

    layer_setup = payload.layer_role_setup
    finish = payload.finish_setup
    confirmed_layers = layer_setup is not None and layer_setup.confirmation_status == "complete"
    finish_confirmed = finish is not None and finish.confirmed is True
    status = "confirmed" if (confirmed_layers or finish_confirmed) else "pending"

    return ConfirmedProductionModel(
        letter_count=count,
        cut_contour_count=cut_count,
        inner_hole_count=holes,
        confirmation_status=status,
        letter_model=LetterModel(count_confirmed=status == "confirmed"),
        cut_contour_model=_minimal_cut_contour_model(cut_count),
    )


def build_path_geometry_summary_from_v4_payload(payload: IntakeV4WorkspacePayload) -> dict[str, Any]:
    """Merge nest2 quote_geometry + finish lighting into path summary for V3 adapters."""
    merged: dict[str, Any] = {}
    if payload.path_geometry_summary:
        merged.update(payload.path_geometry_summary)
    quote = _resolve_v4_quote_geometry(payload)
    for key, value in quote.items():
        if value is not None:
            merged[key] = value

    perimeter = merged.get("letter_perimeter_m") or merged.get("total_letter_perimeter_ml")
    if perimeter:
        merged.setdefault("total_letter_perimeter_ml", perimeter)
        merged.setdefault("letter_perimeter_m", perimeter)
        merged.setdefault(
            "return_material_perimeter_ml",
            merged.get("return_material_perimeter_ml") or perimeter,
        )
    cutting = merged.get("face_cutting_perimeter_ml") or merged.get("cutting_perimeter_ml")
    if cutting:
        merged.setdefault("face_cutting_perimeter_ml", cutting)
        merged.setdefault("cutting_perimeter_ml", cutting)
    elif perimeter:
        merged.setdefault("face_cutting_perimeter_ml", perimeter)
        merged.setdefault("cutting_perimeter_ml", perimeter)

    cnc_cutting = merged.get("cnc_cutting_perimeter_ml")
    if cnc_cutting:
        merged.setdefault("cnc_cutting_perimeter_ml", cnc_cutting)
        merged.setdefault("bevel_perimeter_ml", cnc_cutting)

    face_area = merged.get("face_area_m2")
    if face_area:
        merged.setdefault("letter_face_area_m2", face_area)

    setup = payload.finish_setup
    if setup:
        if setup.return_depth_mm is not None:
            merged.setdefault("return_depth_mm", setup.return_depth_mm)
        if setup.estimated_led_watts is not None:
            merged["estimated_led_watts"] = setup.estimated_led_watts
        if setup.required_psu_watts is not None:
            merged["required_psu_watts"] = setup.required_psu_watts
        if setup.psu_configuration:
            merged["psu_configuration"] = list(setup.psu_configuration)

    if perimeter and face_area:
        merged["calculation_quality"] = "calculated"
    elif payload.svg_analysis_json:
        merged["calculation_quality"] = "estimated"
    else:
        merged["calculation_quality"] = "missing"

    layer_setup = payload.layer_role_setup
    if layer_setup and layer_setup.confirmation_status == "complete":
        merged["layer_role_confirmation_status"] = "complete"
        merged["operator_confirmed_layer_roles"] = True

    return merged


def _lighting_plan_from_v4(
    setup: IntakeV4FinishSetup | None,
    *,
    path_summary: dict[str, Any] | None = None,
) -> IntakeV3LightingPlan | None:
    if setup is None:
        return None

    path_summary = path_summary or {}
    setup_confirmed = setup.confirmed is True

    if setup.illuminated is False:
        return IntakeV3LightingPlan(
            enabled=False,
            illumination_mode="non_illuminated",
            psu_strategy="not_required",
            is_confirmed=setup_confirmed,
        )

    perimeter_m = path_summary.get("led_perimeter_ml") or path_summary.get("letter_perimeter_m") or path_summary.get("total_letter_perimeter_ml")
    try:
        perimeter_value = float(perimeter_m) if perimeter_m is not None else None
    except (TypeError, ValueError):
        perimeter_value = None

    module_power = setup.led_module_power_w if _positive(setup.led_module_power_w) else DEFAULT_LED_MODULE_POWER_W
    is_led_strip = (setup.lighting_system_type or "").strip().lower() == "led_strip"
    module_count: int | None = None
    if not is_led_strip and _positive(setup.estimated_led_watts) and _positive(module_power):
        module_count = max(1, int(round(float(setup.estimated_led_watts) / float(module_power))))
    elif not is_led_strip and perimeter_value and perimeter_value > 0:
        module_count = _compute_led_module_count_from_perimeter(perimeter_value)

    psu_units = [
        IntakeV3PsuPlanUnit(capacity_w=float(watts), quantity=1, label=f"{watts}W")
        for watts in (setup.psu_configuration or [])
        if watts is not None
    ]

    plan = IntakeV3LightingPlan(
        enabled=True,
        illumination_mode="frontlit",
        led_system=_map_v4_led_system(setup.lighting_system_type),
        light_color=_map_v4_light_color(setup.light_color) or "neutral_white",
        module_power_w=module_power,
        module_count=module_count,
        estimated_total_watts=setup.estimated_led_watts,
        required_watts_with_reserve=setup.required_psu_watts,
        psu_units=psu_units,
        psu_strategy="packed_at_packaging",
        psu_packed_at_packaging=True,
        is_confirmed=setup_confirmed,
    )
    if is_led_strip:
        return plan
    return sync_lighting_plan(plan)


def build_v3_workspace_from_v4_payload(payload: IntakeV4WorkspacePayload) -> IntakeV3Workspace:
    """Minimal Intake V3 workspace for production handoff / task seed preview."""
    finish = finish_assignment_from_v4_setup(payload.finish_setup)
    illuminated = payload.finish_setup.illuminated is not False if payload.finish_setup else True
    path_summary = build_path_geometry_summary_from_v4_payload(payload)
    confirmed_model = _confirmed_production_model_from_payload(payload)

    width_mm = payload.client.width_mm or path_summary.get("width_mm")
    height_mm = payload.client.height_mm or path_summary.get("height_mm")

    vector_asset: VectorAsset | None = None
    if payload.svg_source is not None:
        upload_status = payload.svg_source.upload_status
        if upload_status == "analyzed":
            upload_status = "parsed"
        vector_asset = VectorAsset(
            file_name=payload.svg_source.file_name,
            file_hash=payload.svg_source.file_hash,
            upload_status=upload_status,  # type: ignore[arg-type]
            declared_width_mm=width_mm,
            declared_height_mm=height_mm,
        )
    elif payload.svg_analysis_json:
        vector_asset = VectorAsset(
            file_name="svg",
            upload_status="parsed",
            declared_width_mm=width_mm,
            declared_height_mm=height_mm,
        )

    raw_svg: RawSvgAnalysis | None = None
    if vector_asset is not None:
        letter_count = confirmed_model.letter_count if confirmed_model else 0
        closed_contours = letter_count
        if confirmed_model and confirmed_model.cut_contour_count:
            closed_contours = confirmed_model.cut_contour_count
        raw_svg = RawSvgAnalysis(
            file_name=vector_asset.file_name,
            closed_contour_count=closed_contours,
            path_count=letter_count,
        )

    depth_mm = payload.finish_setup.return_depth_mm if payload.finish_setup else None

    return IntakeV3Workspace(
        client_request={
            "client_name": payload.client.client_name or "",
            "job_title": payload.client.job_title or "",
            "width_mm": width_mm,
            "height_mm": height_mm,
            "depth_mm": depth_mm,
        },
        product_selection=ProductSelection(
            template_code=payload.product_binding.template_code,
            template_id=payload.product_binding.template_id,
        ),
        vector_asset=vector_asset,
        raw_svg_analysis=raw_svg,
        confirmed_production_model=confirmed_model,
        finish_assignment=finish,
        lighting_plan=_lighting_plan_from_v4(payload.finish_setup, path_summary=path_summary),
        path_geometry_summary=path_summary or None,
        support_context=SupportContext(shared_support=False, illuminated=illuminated),
    )


def merge_finish_setup_override(
    setup: IntakeV4FinishSetup | None,
    override: dict[str, Any] | None,
) -> IntakeV4FinishSetup | None:
    if setup is None and not override:
        return None
    base = setup.model_dump(mode="json") if setup else {}
    if override:
        base.update({k: v for k, v in override.items() if v is not None})
    return IntakeV4FinishSetup.model_validate(base)


def artwork_finishes_present(finishes: list[IntakeV4ArtworkFinish] | None) -> bool:
    return bool(finishes)
