"""TPL-VOLUMETRIC-FACE-BACK-PREP — V1 CNC-only internal production cost draft (read-only).

Scope: plexiglas 3 mm face + Forex 10 mm back, CNC cut + shanfren/channel operations.
No finishes, stock, real tasks, quotes, or CostEngine integration.
"""

from __future__ import annotations

from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from schemas.intake_v4 import (
    TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE,
    TPL_VOLUMETRIC_FACE_BACK_PREP_V1_VERSION,
    IntakeV4FaceBackPrepComponentSnapshot,
    IntakeV4FaceBackPrepComponents,
    IntakeV4FaceBackPrepCostDraftResponse,
    IntakeV4FaceBackPrepCostDraftTotals,
    IntakeV4FaceBackPrepCostDraftWarning,
    IntakeV4FaceBackPrepMaterialCostRow,
    IntakeV4FaceBackPrepOperationCostRow,
    IntakeV4FaceBackPrepTaskDraft,
)
from services.intake_v4_backing_mode_service import (
    resolve_backing_mode_from_finish,
    resolve_volumetric_backing_state,
)
from services.intake_v4_cnc_router_pass_policy_service import (
    DEFAULT_CNC_RATE_EUR_PER_ML_PASS,
    face_plexi_cnc_passes,
    forex_backing_cnc_passes,
)
from services.intake_v4_material_breakdown_service import resolve_v4_registry_material_price
from services.intake_v4_workspace_service import _get_record_or_404, _json_loads
from services.tpl_volumetric_face_back_prep_productsystem_contract import (
    CNC_RATE_EUR_PER_ML,
    MATERIAL_KEY_FOREX_10MM,
    MATERIAL_KEY_PLEXI_3MM,
    OP_CNC_CUT_BACK,
    OP_CNC_CUT_FACE,
    OP_CNC_SHANFREN_BACK,
    OP_CNC_SHANFREN_FACE,
    REGISTRY_FOREX_BACK_CODE,
    REGISTRY_PLEXI_FACE_CODE,
    TASK_CLEAN,
    TASK_CUT_BACK,
    TASK_CUT_FACE,
    TASK_PACKAGE,
    TASK_PREPARE_CNC,
    TASK_SHANFREN_BACK,
    TASK_SHANFREN_FACE,
    TEMPLATE_METADATA,
    VECTOR_BACK_PERIMETER_KEYS,
    VECTOR_FACE_PERIMETER_KEYS,
)

MountingContext = Literal["flat_support", "metal_bars", "raised_support", "manual"]
PerimeterConfidence = Literal["high", "derived_candidate", "manual_required"]


def _normalize_material_price_source(source: str) -> str:
    if source == "pricing_registry":
        return "prices_registry"
    return source


def _float_metric(sources: list[dict[str, Any] | None], *keys: str) -> float | None:
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in keys:
            raw = source.get(key)
            if raw is None:
                continue
            try:
                value = float(raw)
                if value > 0:
                    return value
            except (TypeError, ValueError):
                continue
    return None


def _resolve_geometry_sources(payload_raw: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    quote_geometry = payload_raw.get("quote_geometry")
    path_geometry = payload_raw.get("path_geometry_summary")
    if not isinstance(quote_geometry, dict):
        quote_geometry = {}
    if not isinstance(path_geometry, dict):
        path_geometry = {}
    merged = {**path_geometry, **quote_geometry}
    return quote_geometry, path_geometry, merged


def _resolve_face_area_m2(sources: list[dict[str, Any] | None]) -> tuple[float | None, str | None]:
    value = _float_metric(sources, "face_area_m2", "letter_face_area_m2")
    if value is not None:
        return value, "quote_geometry|path_geometry_summary.face_area_m2"
    return None, None


def _resolve_back_area_m2(
    sources: list[dict[str, Any] | None],
    *,
    face_area: float | None,
) -> tuple[float | None, str | None, bool]:
    value = _float_metric(sources, "backing_area_m2", "back_area_m2")
    if value is not None:
        return value, "quote_geometry|path_geometry_summary.backing_area_m2", False
    if face_area is not None:
        return face_area, "face_area_fallback", True
    return None, None, False


def _resolve_vector_perimeter_ml(
    geometry: dict[str, Any],
    *,
    keys: tuple[str, ...],
) -> tuple[float | None, str | None]:
    """Resolve CNC vector perimeter from explicit geometry keys only (no bbox/nesting fallback)."""
    for key in keys:
        raw = geometry.get(key)
        if raw is None:
            continue
        try:
            value = float(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            return round(value, 6), key
    return None, None


def _resolve_vector_face_perimeter_ml(
    merged_geom: dict[str, Any],
) -> tuple[float | None, str | None, PerimeterConfidence]:
    value, source_key = _resolve_vector_perimeter_ml(
        merged_geom,
        keys=VECTOR_FACE_PERIMETER_KEYS,
    )
    if value is not None:
        return value, source_key, "high"
    return None, None, "manual_required"


def _resolve_vector_back_perimeter_ml(
    merged_geom: dict[str, Any],
) -> tuple[float | None, str | None, PerimeterConfidence]:
    value, source_key = _resolve_vector_perimeter_ml(
        merged_geom,
        keys=VECTOR_BACK_PERIMETER_KEYS,
    )
    if value is not None:
        return value, source_key, "high"
    return None, None, "manual_required"


def _resolve_shanfren_forex_enabled(
    *,
    finish: dict[str, Any],
    back_bevel_enabled: bool,
    shanfren_forex_override: bool | None,
    mounting_context: MountingContext | None,
) -> tuple[bool, list[str]]:
    manual: list[str] = []
    if shanfren_forex_override is not None:
        return shanfren_forex_override, manual
    if back_bevel_enabled:
        return True, manual
    if mounting_context in {"metal_bars", "raised_support"}:
        manual.append("shanfren_forex_mounting_context_recommended")
        return False, manual
    return False, manual


def _operation_row(
    *,
    operation_key: str,
    label: str,
    component: Literal["FACE_PLEXI", "BACK_FOREX"],
    task_key: str,
    quantity_ml: float | None,
    pass_count: int,
    active: bool,
    perimeter_source: str | None = None,
    perimeter_confidence: PerimeterConfidence = "high",
    is_vector_perimeter_source: bool = True,
    status_when_inactive: Literal["skipped", "optional"] = "skipped",
) -> IntakeV4FaceBackPrepOperationCostRow | None:
    if not active:
        return None
    if (
        quantity_ml is None
        or quantity_ml <= 0
        or perimeter_confidence == "manual_required"
        or pass_count <= 0
    ):
        return IntakeV4FaceBackPrepOperationCostRow(
            operation_key=operation_key,
            label=label,
            component=component,
            task_key=task_key,
            quantity=0.0,
            unit_price=DEFAULT_CNC_RATE_EUR_PER_ML_PASS,
            pass_count=pass_count,
            price_source="fixed_rule",
            cost=None,
            status="manual_required",
            perimeter_source=perimeter_source,
            perimeter_confidence="manual_required",
            is_vector_perimeter_source=is_vector_perimeter_source,
        )
    cost = round(quantity_ml * pass_count * DEFAULT_CNC_RATE_EUR_PER_ML_PASS, 4)
    op_status: Literal["calculated", "calculated_when_enabled"] = "calculated"
    if operation_key == OP_CNC_SHANFREN_BACK:
        op_status = "calculated_when_enabled"
    return IntakeV4FaceBackPrepOperationCostRow(
        operation_key=operation_key,
        label=label,
        component=component,
        task_key=task_key,
        quantity=round(quantity_ml, 4),
        unit_price=DEFAULT_CNC_RATE_EUR_PER_ML_PASS,
        pass_count=pass_count,
        price_source="fixed_rule",
        cost=cost,
        status=op_status,
        perimeter_source=perimeter_source,
        perimeter_confidence=perimeter_confidence,
        is_vector_perimeter_source=is_vector_perimeter_source,
    )


def _material_row(
    *,
    component: Literal["FACE_PLEXI", "BACK_FOREX"],
    material_key: str,
    material_label: str,
    registry_code: str,
    thickness_mm: float,
    area_sqm: float | None,
    unit_price: float | None,
    price_source: str,
    active: bool,
) -> IntakeV4FaceBackPrepMaterialCostRow | None:
    if not active:
        return None
    if area_sqm is None or area_sqm <= 0:
        return IntakeV4FaceBackPrepMaterialCostRow(
            component=component,
            material_key=material_key,
            material_label=material_label,
            registry_code=registry_code,
            thickness_mm=thickness_mm,
            quantity=0.0,
            unit_price=unit_price,
            price_source=price_source,  # type: ignore[arg-type]
            cost=None,
            status="manual_required",
        )
    cost = round(area_sqm * unit_price, 4) if unit_price is not None else None
    status: Literal["calculated", "missing_price"] = "calculated" if cost is not None else "missing_price"
    return IntakeV4FaceBackPrepMaterialCostRow(
        component=component,
        material_key=material_key,
        material_label=material_label,
        registry_code=registry_code,
        thickness_mm=thickness_mm,
        quantity=round(area_sqm, 4),
        unit_price=unit_price,
        price_source=price_source,  # type: ignore[arg-type]
        cost=cost,
        status=status,
    )


def _build_task_drafts(*, shanfren_forex_enabled: bool, back_forex_active: bool) -> list[IntakeV4FaceBackPrepTaskDraft]:
    tasks: list[IntakeV4FaceBackPrepTaskDraft] = [
        IntakeV4FaceBackPrepTaskDraft(
            task_key=TASK_PREPARE_CNC,
            label="Pregătire fișiere CNC",
            station="prepress",
            component="GENERAL",
            order_index=1,
            depends_on=[],
            cost_rows=[],
        ),
        IntakeV4FaceBackPrepTaskDraft(
            task_key=TASK_CUT_FACE,
            label="Debitare față plexiglas 3 mm",
            station="cnc",
            component="FACE_PLEXI",
            order_index=2,
            depends_on=[TASK_PREPARE_CNC],
            cost_rows=[OP_CNC_CUT_FACE],
        ),
        IntakeV4FaceBackPrepTaskDraft(
            task_key=TASK_SHANFREN_FACE,
            label="Șanfren/canal CNC față plexiglas",
            station="cnc",
            component="FACE_PLEXI",
            order_index=3,
            depends_on=[TASK_CUT_FACE],
            cost_rows=[OP_CNC_SHANFREN_FACE],
        ),
    ]
    order = 4
    if back_forex_active:
        tasks.append(
            IntakeV4FaceBackPrepTaskDraft(
                task_key=TASK_CUT_BACK,
                label="Debitare spate Forex 10 mm",
                station="cnc",
                component="BACK_FOREX",
                order_index=order,
                depends_on=[TASK_PREPARE_CNC],
                cost_rows=[OP_CNC_CUT_BACK],
            )
        )
        order += 1
        if shanfren_forex_enabled:
            tasks.append(
                IntakeV4FaceBackPrepTaskDraft(
                    task_key=TASK_SHANFREN_BACK,
                    label="Șanfren/canal CNC spate Forex",
                    station="cnc",
                    component="BACK_FOREX",
                    order_index=order,
                    depends_on=[TASK_CUT_BACK],
                    cost_rows=[OP_CNC_SHANFREN_BACK],
                )
            )
            order += 1
    tasks.extend(
        [
            IntakeV4FaceBackPrepTaskDraft(
                task_key=TASK_CLEAN,
                label="Curățare și verificare piese",
                station="finishing",
                component="GENERAL",
                order_index=order,
                depends_on=[TASK_SHANFREN_FACE] + ([TASK_CUT_BACK] if back_forex_active else []),
                cost_rows=[],
            ),
            IntakeV4FaceBackPrepTaskDraft(
                task_key=TASK_PACKAGE,
                label="Ambalare piese față + spate",
                station="packing",
                component="GENERAL",
                order_index=order + 1,
                depends_on=[TASK_CLEAN],
                cost_rows=[],
            ),
        ]
    )
    return tasks


def build_tpl_volumetric_face_back_prep_cost_draft_v1(
    payload_raw: dict[str, Any],
    *,
    workspace_id: str | None = None,
    shanfren_forex_override: bool | None = None,
    mounting_context: MountingContext | None = None,
    plexi_unit_price: float | None = None,
    plexi_price_source: str = "prices_registry",
    forex_unit_price: float | None = None,
    forex_price_source: str = "prices_registry",
) -> IntakeV4FaceBackPrepCostDraftResponse:
    """Pure builder — no DB writes, no side effects."""
    finish = payload_raw.get("finish_setup")
    if not isinstance(finish, dict):
        finish = {}
    layer_role_setup = payload_raw.get("layer_role_setup")
    if not isinstance(layer_role_setup, dict):
        layer_role_setup = {}

    quote_geometry, path_geometry, merged_geom = _resolve_geometry_sources(payload_raw)
    geom_sources = [path_geometry, quote_geometry, merged_geom]

    backing_mode, backing_present, back_bevel_enabled = resolve_volumetric_backing_state(
        finish,
        layer_role_setup,
        quote_geometry=quote_geometry,
    )
    explicit_mode = resolve_backing_mode_from_finish(finish)
    if explicit_mode == "none":
        back_forex_active = False
    elif explicit_mode is not None:
        back_forex_active = True
    else:
        # Partial template defaults to back prep unless layer setup denies backing.
        back_forex_active = backing_present if backing_present else True

    shanfren_forex_enabled, shanfren_manual = _resolve_shanfren_forex_enabled(
        finish=finish,
        back_bevel_enabled=back_bevel_enabled,
        shanfren_forex_override=shanfren_forex_override,
        mounting_context=mounting_context,
    )

    face_area, face_area_source = _resolve_face_area_m2(geom_sources)
    back_area, back_area_source, back_area_fallback = _resolve_back_area_m2(
        geom_sources,
        face_area=face_area,
    )
    face_cut_ml, face_cut_source, face_perimeter_confidence = _resolve_vector_face_perimeter_ml(
        merged_geom
    )
    back_cut_ml, back_cut_source, back_perimeter_confidence = _resolve_vector_back_perimeter_ml(
        merged_geom
    )

    face_passes = face_plexi_cnc_passes(face_bevel_enabled=True)
    forex_passes = forex_backing_cnc_passes(back_bevel_enabled=shanfren_forex_enabled)

    face_shanfren_ml = face_cut_ml
    back_shanfren_ml = back_cut_ml if shanfren_forex_enabled else None

    warnings: list[IntakeV4FaceBackPrepCostDraftWarning] = [
        IntakeV4FaceBackPrepCostDraftWarning(
            code="v1_cnc_only_scope",
            message="V1 — doar materiale față/spate și operații CNC; finisaje excluse.",
            severity="info",
            source="tpl_volumetric_face_back_prep_cost_draft_service",
        ),
        IntakeV4FaceBackPrepCostDraftWarning(
            code="task_order_logical_not_physical",
            message="Ordinea taskurilor draft este logică pentru cost/preview, nu neapărat secvența fizică pe utilaj.",
            severity="info",
        ),
    ]
    if back_area_fallback:
        warnings.append(
            IntakeV4FaceBackPrepCostDraftWarning(
                code="back_area_face_fallback",
                message="Arie spate Forex — fallback din arie față (doar material, nu CNC).",
                source=back_area_source,
            )
        )
    if face_perimeter_confidence == "manual_required":
        warnings.append(
            IntakeV4FaceBackPrepCostDraftWarning(
                code="vector_perimeter_missing_or_low_confidence",
                message="Perimetru vectorial CNC față lipsă — cost CNC manual_required; fără fallback bbox/nesting.",
                severity="warning",
                source="vector_geometry",
            )
        )
    if back_forex_active and back_perimeter_confidence == "manual_required":
        warnings.append(
            IntakeV4FaceBackPrepCostDraftWarning(
                code="vector_perimeter_missing_or_low_confidence",
                message="Perimetru vectorial CNC spate lipsă — cost CNC manual_required; fără fallback față/bbox/nesting.",
                severity="warning",
                source="vector_geometry",
            )
        )
    if not back_forex_active:
        warnings.append(
            IntakeV4FaceBackPrepCostDraftWarning(
                code="back_forex_inactive",
                message="Spate Forex inactiv (backing_mode=none) — doar față plexiglas în cost draft.",
            )
        )

    manual_inputs: list[str] = list(shanfren_manual)
    if face_area is None:
        manual_inputs.append("face_area_sqm")
    if face_cut_ml is None:
        manual_inputs.append("face_cut_length_ml")
    if back_forex_active and back_area is None:
        manual_inputs.append("back_area_sqm")
    if back_forex_active and back_cut_ml is None:
        manual_inputs.append("back_cut_length_ml")

    materials: list[IntakeV4FaceBackPrepMaterialCostRow] = []
    for row in (
        _material_row(
            component="FACE_PLEXI",
            material_key=MATERIAL_KEY_PLEXI_3MM,
            material_label="Plexiglas 3 mm — față litere",
            registry_code=REGISTRY_PLEXI_FACE_CODE,
            thickness_mm=3.0,
            area_sqm=face_area,
            unit_price=plexi_unit_price,
            price_source=plexi_price_source,
            active=True,
        ),
        _material_row(
            component="BACK_FOREX",
            material_key=MATERIAL_KEY_FOREX_10MM,
            material_label="Forex 10 mm — spate litere",
            registry_code=REGISTRY_FOREX_BACK_CODE,
            thickness_mm=10.0,
            area_sqm=back_area,
            unit_price=forex_unit_price,
            price_source=forex_price_source,
            active=back_forex_active,
        ),
    ):
        if row is not None:
            materials.append(row)

    operations: list[IntakeV4FaceBackPrepOperationCostRow] = []
    for row in (
        _operation_row(
            operation_key=OP_CNC_CUT_FACE,
            label="Debitare CNC față plexiglas 3 mm",
            component="FACE_PLEXI",
            task_key=TASK_CUT_FACE,
            quantity_ml=face_cut_ml,
            pass_count=face_passes["cut_passes"],
            active=True,
            perimeter_source=face_cut_source,
            perimeter_confidence=face_perimeter_confidence,
        ),
        _operation_row(
            operation_key=OP_CNC_SHANFREN_FACE,
            label="Șanfren/canal CNC față plexiglas",
            component="FACE_PLEXI",
            task_key=TASK_SHANFREN_FACE,
            quantity_ml=face_shanfren_ml,
            pass_count=face_passes["bevel_passes"],
            active=True,
            perimeter_source=face_cut_source,
            perimeter_confidence=face_perimeter_confidence,
        ),
        _operation_row(
            operation_key=OP_CNC_CUT_BACK,
            label="Debitare CNC spate Forex 10 mm",
            component="BACK_FOREX",
            task_key=TASK_CUT_BACK,
            quantity_ml=back_cut_ml,
            pass_count=forex_passes["cut_passes"],
            active=back_forex_active,
            perimeter_source=back_cut_source,
            perimeter_confidence=back_perimeter_confidence if back_forex_active else "manual_required",
        ),
        _operation_row(
            operation_key=OP_CNC_SHANFREN_BACK,
            label="Șanfren/canal CNC spate Forex",
            component="BACK_FOREX",
            task_key=TASK_SHANFREN_BACK,
            quantity_ml=back_shanfren_ml,
            pass_count=forex_passes["bevel_passes"],
            active=back_forex_active and shanfren_forex_enabled,
            perimeter_source=back_cut_source,
            perimeter_confidence=back_perimeter_confidence if back_forex_active else "manual_required",
            status_when_inactive="optional",
        ),
    ):
        if row is not None:
            operations.append(row)

    missing_prices: list[str] = []
    material_cost_parts: list[float] = []
    for row in materials:
        if row.status == "missing_price":
            missing_prices.append(row.registry_code or row.material_key)
        elif row.cost is not None:
            material_cost_parts.append(row.cost)

    operation_cost_parts: list[float] = []
    for row in operations:
        if row.cost is not None:
            operation_cost_parts.append(row.cost)
        elif row.status == "manual_required":
            manual_inputs.append(row.operation_key)

    material_cost = round(sum(material_cost_parts), 4) if material_cost_parts else None
    operation_cost = round(sum(operation_cost_parts), 4) if operation_cost_parts else None
    has_missing_price = bool(missing_prices)
    has_manual = any(
        row.status in {"manual_required", "missing_price"} for row in materials + operations
    )
    total_internal: float | None = None
    if not has_missing_price and not has_manual:
        if material_cost is not None or operation_cost is not None:
            total_internal = round((material_cost or 0.0) + (operation_cost or 0.0), 4)

    components = IntakeV4FaceBackPrepComponents(
        face_plexi=IntakeV4FaceBackPrepComponentSnapshot(
            material_key=MATERIAL_KEY_PLEXI_3MM,
            registry_code=REGISTRY_PLEXI_FACE_CODE,
            thickness_mm=3.0,
            area_sqm=face_area,
            cut_length_ml=face_cut_ml,
            shanfren_length_ml=face_shanfren_ml,
            shanfren_required=True,
            shanfren_enabled=True,
            area_source=face_area_source,
            cut_length_source=face_cut_source,
            shanfren_length_source=face_cut_source if face_shanfren_ml else None,
        ),
        back_forex=IntakeV4FaceBackPrepComponentSnapshot(
            material_key=MATERIAL_KEY_FOREX_10MM,
            registry_code=REGISTRY_FOREX_BACK_CODE,
            thickness_mm=10.0,
            area_sqm=back_area if back_forex_active else None,
            cut_length_ml=back_cut_ml if back_forex_active else None,
            shanfren_length_ml=back_shanfren_ml,
            shanfren_required=False,
            shanfren_enabled=shanfren_forex_enabled and back_forex_active,
            area_source=back_area_source,
            cut_length_source=back_cut_source,
            shanfren_length_source=back_cut_source if back_shanfren_ml else None,
        ),
    )

    return IntakeV4FaceBackPrepCostDraftResponse(
        workspace_id=workspace_id,
        template_key=TPL_VOLUMETRIC_FACE_BACK_PREP_TEMPLATE_CODE,
        version=TPL_VOLUMETRIC_FACE_BACK_PREP_V1_VERSION,
        components=components,
        materials=materials,
        operations=operations,
        task_drafts=_build_task_drafts(
            shanfren_forex_enabled=shanfren_forex_enabled and back_forex_active,
            back_forex_active=back_forex_active,
        ),
        totals=IntakeV4FaceBackPrepCostDraftTotals(
            material_cost=material_cost,
            operation_cost=operation_cost,
            total_internal_cost=total_internal,
        ),
        missing_prices=missing_prices,
        manual_inputs_required=sorted(set(manual_inputs)),
        warnings=warnings,
        cnc_rate_eur_per_ml=DEFAULT_CNC_RATE_EUR_PER_ML_PASS,
    )


async def get_tpl_volumetric_face_back_prep_cost_draft_for_workspace(
    db: AsyncSession,
    workspace_id: str,
    *,
    shanfren_forex_override: bool | None = None,
    mounting_context: MountingContext | None = None,
) -> IntakeV4FaceBackPrepCostDraftResponse:
    """Read-only workspace cost draft with registry material prices."""
    from services.inventory_materials_admin_service import load_material_pricing_dict

    record = await _get_record_or_404(db, workspace_id)
    payload_raw = _json_loads(record.payload_json, {})
    if not isinstance(payload_raw, dict):
        payload_raw = {}

    pricing_cache = await load_material_pricing_dict(db)
    plexi_price, _, plexi_source = await resolve_v4_registry_material_price(
        db,
        REGISTRY_PLEXI_FACE_CODE,
        pricing_cache=pricing_cache,
    )
    forex_price, _, forex_source = await resolve_v4_registry_material_price(
        db,
        REGISTRY_FOREX_BACK_CODE,
        pricing_cache=pricing_cache,
    )

    return build_tpl_volumetric_face_back_prep_cost_draft_v1(
        payload_raw,
        workspace_id=workspace_id,
        shanfren_forex_override=shanfren_forex_override,
        mounting_context=mounting_context,
        plexi_unit_price=plexi_price,
        plexi_price_source=_normalize_material_price_source(plexi_source),
        forex_unit_price=forex_price,
        forex_price_source=_normalize_material_price_source(forex_source),
    )
