"""Read-only EstimatedInternalCost preview builder (Step 7H).

Answers: "What do we estimate this product costs internally before production?"
Does NOT use CostEngine, QuoteOrchestrator, price bridge, or hourly totals.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from data.internal_cost_rules_volumetric_v2 import (
    CRITICAL_MODULE_CODES,
    FORBIDDEN_HOURLY_TOKENS,
    INTERNAL_QC_OPERATION_CODES,
    RULES_BY_TEMPLATE,
    CapacityHintRule,
    InternalConsumableRule,
    InternalOperationRule,
    InternalOverheadRule,
)
from schemas.aggregate_cost_bom import (
    AggregateExpandedCostBom,
    CostBomCostableMaterial,
    CostBomCostableOperation,
)
from schemas.estimated_internal_cost import (
    ESTIMATED_INTERNAL_COST_SOURCE,
    CapacityHint,
    EstimatedInternalCostLine,
    EstimatedInternalCostPreview,
    InternalBlocker,
    InternalOwnerDecision,
    InternalProvenanceEntry,
)
from schemas.product_definition import ProductDefinitionPreview
from services.aggregate_cost_bom_adapter import AggregateCostBomBuilderService
from services.formula_handlers import resolve_formula
from services.intake_v6_modular_form_contract_service import IntakeV6ModularFormContractService
from services.product_definition_builder_service import (
    ProductDefinitionBuilderService,
    _classify_modules,
    _has_geometry_basics,
    _read_bool,
    _read_string,
)
from services.template_architecture_scope import VOLUMETRIC_LOGO_TEMPLATE_CODE

BAR_MOUNTING = frozenset({"steel_bars", "aluminum_bars"})
GATE_ONLY_MODULES = frozenset({"geometry_svg"})
FUTURE_MODULES = frozenset({"electrica_logo"})
SKIP_INVENTORY_CLASSIFICATIONS = frozenset()  # reserved for future inventory classification filters
SUPPORTED_TEMPLATES = frozenset(RULES_BY_TEMPLATE.keys())
CRITICAL_GEOMETRY_KEYS = frozenset(
    {
        "letter_count",
        "letter_face_area_m2",
        "letter_perimeter_m",
        "width_mm",
        "height_mm",
        "return_depth_mm",
    }
)

SEGMENT_NAMESPACE_SEP = "::"
WARNING_LINKED_SEGMENT_FINISH_PARTIAL = "LINKED_SEGMENT_FINISH_PARTIAL"
ARTWORK_OWNED_LOGO_MATERIAL_CODES = frozenset(
    {
        "print_media",
        "laminate_media",
    }
)
ARTWORK_OWNED_LOGO_OPERATION_CODES = frozenset(
    {
        "logo_face_print",
        "logo_face_laminate",
        "logo_finish_application",
    }
)
LOGO_OPERATION_FORMULA_BASIS = {
    "logo_area": "m2",
    "logo_perimeter": "ml",
    "logo_led_modules": "piece",
    "logo_psu_count": "piece",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _is_linked_logo_bom_material(mat: CostBomCostableMaterial) -> bool:
    if _text(mat.source_template_code) != VOLUMETRIC_LOGO_TEMPLATE_CODE:
        return False
    return SEGMENT_NAMESPACE_SEP in _text(mat.component_ref)


def _is_linked_logo_bom_operation(op: CostBomCostableOperation) -> bool:
    if _text(op.source_template_code) != VOLUMETRIC_LOGO_TEMPLATE_CODE:
        return False
    return SEGMENT_NAMESPACE_SEP in _text(op.component_ref)


def _linked_logo_segment_key(component_ref: str | None) -> str | None:
    ref = _text(component_ref)
    if SEGMENT_NAMESPACE_SEP not in ref:
        return None
    return ref.split(SEGMENT_NAMESPACE_SEP, 1)[1]


def _artwork_finish_area_for_segment(payload: dict[str, Any], segment_key: str) -> float | None:
    from services.intake_v6_layer_identity import artwork_finish_for_segment

    row = artwork_finish_for_segment(payload, segment_key)
    if not row:
        return None
    for field in ("estimated_area_m2", "face_area_m2", "area_m2", "artwork_area_m2"):
        qty = _positive_number(row.get(field))
        if qty is not None:
            return qty
    geometry = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
    for box in geometry.get("artwork_boxes") or []:
        if not isinstance(box, dict):
            continue
        if _text(box.get("layer_key")) == segment_key:
            qty = _positive_number(box.get("area_m2"))
            if qty is not None:
                return qty
    return None


def _enrich_payload_artwork_finishes_from_pd(pd: ProductDefinitionPreview, payload: dict[str, Any]) -> None:
    linked = pd.linked_template_runtime_segments
    if not isinstance(linked, dict):
        return
    segments = linked.get("segments")
    if not isinstance(segments, list) or not segments:
        return
    finish_setup = payload.setdefault("finish_setup", {})
    artwork_finishes = list(finish_setup.get("artwork_finishes") or [])
    by_key = {_text(row.get("layer_key")): dict(row) for row in artwork_finishes if isinstance(row, dict)}
    for segment in segments:
        if not isinstance(segment, dict):
            continue
        segment_key = _text(segment.get("segment_key"))
        if not segment_key:
            continue
        row = by_key.setdefault(segment_key, {"layer_key": segment_key})
        finish = segment.get("finish") if isinstance(segment.get("finish"), dict) else {}
        for key, value in finish.items():
            if key not in row:
                row[key] = value
    finish_setup["artwork_finishes"] = list(by_key.values())


def _segment_finish_row(payload: dict[str, Any], segment_key: str) -> dict[str, Any]:
    finish_setup = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    for row in finish_setup.get("artwork_finishes") or []:
        if isinstance(row, dict) and _text(row.get("layer_key")) == segment_key:
            return dict(row)
    return {}


def _segment_geometry_area_for_segment(payload: dict[str, Any], segment_key: str) -> float | None:
    row = _segment_finish_row(payload, segment_key)
    for field in ("svg_area_m2", "face_area_m2", "bounding_area_m2"):
        qty = _positive_number(row.get(field))
        if qty is not None:
            return qty
    return None


def _segment_geometry_perimeter_for_segment(payload: dict[str, Any], segment_key: str) -> float | None:
    row = _segment_finish_row(payload, segment_key)
    for field in ("svg_perimeter_ml", "perimeter_ml", "perimeter_m"):
        qty = _positive_number(row.get(field))
        if qty is not None:
            return qty
    return None


def _segment_led_module_count_for_segment(payload: dict[str, Any], segment_key: str) -> float | None:
    row = _segment_finish_row(payload, segment_key)
    for field in ("emblem_led_module_count", "led_module_count"):
        qty = _positive_number(row.get(field))
        if qty is not None:
            return qty
    return None


def _get_by_path(root: Any, path: str) -> Any:
    if not path:
        return None
    cur = root
    for part in path.split("."):
        if not isinstance(cur, dict):
            return None
        cur = cur.get(part)
    return cur


def _positive_number(raw: Any) -> float | None:
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value <= 0:
        return None
    return value


def _coalesce_quote_input(quote_input: dict[str, Any] | None) -> dict[str, Any]:
    if not quote_input:
        return {}
    out = dict(quote_input)
    finish = out.get("finish_setup") if isinstance(out.get("finish_setup"), dict) else {}
    merged_finish = dict(finish)
    for key in (
        "mounting_system",
        "mounting_template_enabled",
        "mounting_template_area_m2",
        "mounting_template_material_type",
        "lighting_system_type",
        "illuminated",
        "return_depth_mm",
        "selected_psu_watts",
        "led_module_count",
        "face_finish_type",
        "backing_mode",
    ):
        if key in out and key not in merged_finish:
            merged_finish[key] = out[key]
    if merged_finish:
        out["finish_setup"] = merged_finish
    geometry = out.get("quote_geometry") if isinstance(out.get("quote_geometry"), dict) else {}
    merged_geometry = dict(geometry)
    for key in ("letter_count", "letter_face_area_m2", "letter_perimeter_m", "depth_mm"):
        if key in out and key not in merged_geometry:
            merged_geometry[key] = out[key]
    if merged_geometry:
        out["quote_geometry"] = merged_geometry
    client = out.get("client") if isinstance(out.get("client"), dict) else {}
    merged_client = dict(client)
    for key in ("width_mm", "height_mm", "depth_mm"):
        if key in out and key not in merged_client:
            merged_client[key] = out[key]
    if merged_client:
        out["client"] = merged_client
    if "svg_source" not in out and _read_string(out.get("vector_file")):
        out["svg_source"] = {"file_name": out.get("vector_file")}
    from services.acm_quote_input_helpers import merge_acm_boxed_mounting_derived_fields

    return merge_acm_boxed_mounting_derived_fields(out)


def _payload_from_sources(
    *,
    pd: ProductDefinitionPreview,
    quote_input: dict[str, Any] | None,
) -> dict[str, Any]:
    if quote_input:
        return _coalesce_quote_input(quote_input)
    if pd.source_context.source_payload_type == "workspace_payload":
        payload: dict[str, Any] = {
            "finish_setup": {},
            "quote_geometry": dict(pd.geometry_inputs),
            "client": {},
            "svg_source": {},
        }
        for key, value in pd.canonical_values.items():
            if key.startswith("finish_setup."):
                payload.setdefault("finish_setup", {})[key.split(".", 1)[1]] = value
            elif key in CRITICAL_GEOMETRY_KEYS:
                if key in ("width_mm", "height_mm", "depth_mm"):
                    payload.setdefault("client", {})[key] = value
                else:
                    payload.setdefault("quote_geometry", {})[key] = value
        _enrich_payload_artwork_finishes_from_pd(pd, payload)
        return payload
    return {}


def _merged_values(pd: ProductDefinitionPreview, payload: dict[str, Any]) -> dict[str, Any]:
    merged = dict(pd.canonical_values)
    merged.update({k: v for k, v in payload.items() if v is not None and v != ""})
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    for key, value in finish.items():
        merged[key] = value
        merged[f"finish_setup.{key}"] = value
    geometry = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
    for key, value in geometry.items():
        merged[key] = value
    return merged


def _module_is_active(state: str) -> bool:
    return state in ("always_on", "active", "conditional_active")


def _legacy_resolve_active_modules(pd: ProductDefinitionPreview, payload: dict[str, Any]) -> set[str]:
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    quote_geometry = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
    svg_source = payload.get("svg_source") if isinstance(payload.get("svg_source"), dict) else {}
    client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
    analysis_ready = bool(payload.get("analysis_ready")) or _has_geometry_basics(payload)

    form = IntakeV6ModularFormContractService().get_for_template(pd.template_code)
    if form is not None and payload:
        selected, optional, inactive = _classify_modules(
            form.modules,
            finish=finish,
            quote_geometry=quote_geometry,
            svg_source=svg_source,
            client=client,
            analysis_ready=analysis_ready,
        )
        all_mods = selected + optional + inactive
    else:
        all_mods = pd.selected_modules + pd.optional_modules + pd.inactive_modules

    active: set[str] = set()
    seen: set[str] = set()
    for mod in all_mods:
        if mod.module_code in seen:
            continue
        seen.add(mod.module_code)
        code = mod.module_code
        if code in FUTURE_MODULES or code in GATE_ONLY_MODULES:
            continue
        if code == "structura_suport":
            if mod.state == "active":
                active.add(code)
            continue
        if code == "finisaje":
            active.add(code)
            continue
        if code == "sistem_led":
            if mod.state in ("active", "conditional_active"):
                active.add(code)
            continue
        if mod.activation_kind in ("always_on", "required_module"):
            active.add(code)
            continue
        if _module_is_active(mod.state):
            active.add(code)

    from services.acm_quote_input_helpers import is_acm_boxed_mounting_standalone_root_template

    if is_acm_boxed_mounting_standalone_root_template(pd.template_code):
        active.add("structura_suport")
        return active

    mounting = _read_string(finish.get("mounting_system") or payload.get("mounting_system"))
    from services.mounting_solution_service import is_structura_suport_active

    if is_structura_suport_active(finish if isinstance(finish, dict) else {}):
        active.add("structura_suport")
    elif mounting:
        if mounting in BAR_MOUNTING:
            active.add("structura_suport")
        else:
            active.discard("structura_suport")
    illuminated = finish.get("illuminated")
    is_lit = illuminated is True or str(illuminated).lower() in ("true", "1", "yes")
    lighting = _read_string(finish.get("lighting_system_type") or payload.get("lighting_system_type"))
    if is_lit and lighting and lighting.lower() not in ("", "none"):
        active.add("sistem_led")
    elif illuminated is False or (lighting and lighting.lower() == "none"):
        active.discard("sistem_led")
    return active


def _resolve_active_modules(pd: ProductDefinitionPreview, payload: dict[str, Any]) -> set[str]:
    from services.offer_scope_resolver_service import resolve_pricing_active_modules

    return resolve_pricing_active_modules(
        pd=pd,
        payload=payload,
        quote_input=payload,
        legacy_fn=lambda p, qi: _legacy_resolve_active_modules(p, qi or {}),
    )


def _extract_quantity(payload: dict[str, Any], values: dict[str, Any], paths: tuple[str, ...]) -> float | int | None:
    for path in paths:
        raw = _get_by_path(payload, path)
        if raw is None:
            raw = values.get(path.split(".")[-1]) if path else None
        if raw is None and "." in path:
            raw = values.get(path)
        number = _positive_number(raw)
        if number is not None:
            return int(number) if number.is_integer() else round(number, 6)
    return None


def _sablon_enabled(payload: dict[str, Any]) -> bool:
    from services.mounting_scope_service import is_mounting_preparation_active

    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    if not is_mounting_preparation_active(finish):
        return False
    enabled = _read_bool(finish.get("mounting_template_enabled"))
    if enabled is None:
        enabled = _read_bool(payload.get("mounting_template_enabled"))
    return enabled is not False


def _material_gate_matches(payload: dict[str, Any], path: str | None, expected: str | None) -> bool:
    if not path:
        return True
    raw = _get_by_path(payload, path) or _get_by_path(payload, f"finish_setup.{path.split('.')[-1]}")
    return _read_string(raw) == expected


def _estimate_material_quantity(
    mat: CostBomCostableMaterial,
    payload: dict[str, Any],
    values: dict[str, Any],
) -> tuple[float | int | None, list[str]]:
    code = (mat.resolved_material_code or mat.material_code or "").upper()
    material_code = _text(mat.material_code).lower()
    unit = (mat.unit or "").lower()
    warnings: list[str] = []

    if _is_linked_logo_bom_material(mat):
        segment_key = _linked_logo_segment_key(mat.component_ref)
        if material_code in ARTWORK_OWNED_LOGO_MATERIAL_CODES:
            if segment_key:
                area = _artwork_finish_area_for_segment(payload, segment_key)
                if area is not None:
                    return area, warnings
            return None, warnings
        return None, warnings

    if "LED-MODULE" in code:
        qty = _extract_quantity(payload, values, ("finish_setup.led_module_count", "led_module_count"))
        return qty, warnings
    if "PSU" in code:
        return 1, warnings
    if "SABLON" in code:
        if not _sablon_enabled(payload):
            return None, ["Sablon disabled — quantity excluded."]
        return _extract_quantity(
            payload,
            values,
            ("finish_setup.mounting_template_area_m2", "mounting_template_area_m2"),
        ), warnings
    if mat.source_template_code == "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1" and "ACM-BOND" in code:
        component_ref = _text(mat.component_ref)
        if component_ref == "comp_casetted_returns":
            qty = _extract_quantity(payload, values, ("return_strip_area_m2",))
            return qty, warnings
        qty = _extract_quantity(payload, values, ("panel_area_m2",))
        return qty, warnings
    if "SURUBURI" in code and mat.source_template_code == "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1":
        return 1, warnings
    if "PROFIL-LATERAL" in code or unit == "ml":
        return _extract_quantity(
            payload,
            values,
            ("quote_geometry.letter_perimeter_m", "letter_perimeter_m"),
        ), warnings
    if unit in ("mp", "m2", "m²"):
        area = _extract_quantity(
            payload,
            values,
            ("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
        )
        if area is not None:
            return area, warnings
        return _extract_quantity(
            payload,
            values,
            ("finish_setup.mounting_template_area_m2", "mounting_template_area_m2"),
        ), warnings
    if unit in ("buc", "piece", "pcs"):
        qty = _extract_quantity(payload, values, ("quote_geometry.letter_count", "letter_count"))
        return qty if qty is not None else 1, warnings
    return None, warnings


def _resolve_logo_operation_internal_rate(
    operation_code: str,
    *,
    op: CostBomCostableOperation | None = None,
) -> tuple[float | None, str, str]:
    """Return owner-approved logo artwork internal rate from canonical catalog only."""
    from data.internal_cost_rules_volumetric_v2 import LOGO_ARTWORK_INTERNAL_OPERATION_RATE_BY_CODE
    from services.logo_artwork_cost_ownership import is_canonical_logo_artwork_operation_row

    if op is not None and operation_code in ARTWORK_OWNED_LOGO_OPERATION_CODES:
        if not is_canonical_logo_artwork_operation_row(
            operation_code=operation_code,
            component_ref=op.component_ref,
            provenance=op.provenance,
            status=getattr(op, "status", None),
            source_template_code=op.source_template_code,
        ):
            return (
                None,
                "INT_LOGO_OP_RATE_MISSING",
                "internal_cost_rules_volumetric_v2:non_canonical_logo_owner",
            )

    rate_entry = LOGO_ARTWORK_INTERNAL_OPERATION_RATE_BY_CODE.get(operation_code)
    if rate_entry is not None and rate_entry.status == "active":
        return float(rate_entry.internal_unit_cost), rate_entry.rule_code, rate_entry.source
    return None, "INT_LOGO_OP_RATE_MISSING", "internal_cost_rules_volumetric_v2:logo_operation_rate_missing"


def _logo_operation_basis_type(op: CostBomCostableOperation) -> str:
    formula_id = _text(op.formula_id)
    return LOGO_OPERATION_FORMULA_BASIS.get(formula_id, "unknown")


def _logo_operation_unit(op: CostBomCostableOperation) -> str | None:
    basis = _logo_operation_basis_type(op)
    if basis == "m2":
        return "m2"
    if basis == "ml":
        return "ml"
    if basis == "piece":
        return "buc"
    return None


def _estimate_logo_operation_quantity(
    op: CostBomCostableOperation,
    payload: dict[str, Any],
    values: dict[str, Any],
) -> tuple[float | int | None, list[str]]:
    segment_key = _linked_logo_segment_key(op.component_ref)
    if not segment_key:
        return None, []

    operation_code = _text(op.operation_code)
    formula_id = _text(op.formula_id)
    warnings: list[str] = []

    if operation_code in ARTWORK_OWNED_LOGO_OPERATION_CODES:
        area = _artwork_finish_area_for_segment(payload, segment_key)
        if area is not None:
            warnings.append(f"quantity_source=artwork_finish:{segment_key}")
        return area, warnings

    if formula_id == "logo_area":
        area = _segment_geometry_area_for_segment(payload, segment_key)
        if area is not None:
            warnings.append(f"quantity_source=segment_geometry_area:{segment_key}")
        return area, warnings

    if formula_id == "logo_perimeter":
        perimeter = _segment_geometry_perimeter_for_segment(payload, segment_key)
        if perimeter is not None:
            warnings.append(f"quantity_source=segment_geometry_perimeter:{segment_key}")
        return perimeter, warnings

    if formula_id == "logo_led_modules":
        count = _segment_led_module_count_for_segment(payload, segment_key)
        if count is not None:
            warnings.append(f"quantity_source=segment_led_module_count:{segment_key}")
        return count, warnings

    return None, warnings


def _build_logo_operation_line_from_bom(
    op: CostBomCostableOperation,
    *,
    quantity: float | int | None,
    unit_cost: float | None,
    rule_code: str,
    source: str,
    warnings: list[str],
) -> EstimatedInternalCostLine:
    basis_type = _logo_operation_basis_type(op)
    subtotal = None
    if unit_cost is not None and quantity is not None and basis_type != "unknown":
        subtotal = round(float(quantity) * float(unit_cost), 4)
    line_warnings = list(warnings)
    if op.workcenter:
        line_warnings.append(f"workcenter_reference={op.workcenter}")
    if op.provenance:
        line_warnings.append(f"bom_provenance={op.provenance}")
    if op.source_template_code:
        line_warnings.append(f"source_template_code={op.source_template_code}")
    return EstimatedInternalCostLine(
        code=f"operation_{op.operation_code}",
        label=op.label or op.operation_code,
        module_code=op.mini_module_code,
        component_code=op.component_ref,
        line_type="operation",
        basis_type=basis_type,  # type: ignore[arg-type]
        quantity=quantity,
        unit=_logo_operation_unit(op),
        internal_unit_cost=unit_cost,
        subtotal=subtotal,
        rule_code=rule_code,
        source=source,
        owner_decision_required=unit_cost is None,
        warnings=line_warnings,
    )


def _operation_rule_applies(rule: InternalOperationRule, active_modules: set[str], payload: dict[str, Any]) -> bool:
    from services.lighting_mount_consumer_service import resolve_lighting_mount_consumers
    from services.offer_scope_led_subscope_service import (
        eic_line_led_subscope,
        led_consumer_row_allowed,
        partial_led_subscope_filter,
    )

    module_key = rule.module_gate or rule.module_code
    if rule.always_include and rule.criticality == "optional":
        return module_key in active_modules or rule.module_code in active_modules
    if module_key not in active_modules and rule.module_code not in active_modules:
        return False

    scope = payload.get("offer_scope") if isinstance(payload.get("offer_scope"), dict) else {}
    sold_led = partial_led_subscope_filter(frozenset(scope.get("sold_modules") or []))
    mount_decision = resolve_lighting_mount_consumers(payload, payload)
    if sold_led is not None and rule.module_code == "sistem_led":
        sub = eic_line_led_subscope(rule.line_code)
        if not led_consumer_row_allowed(
            row_subscope=sub,
            sold_led_subscopes=sold_led,
            eic_line_code=rule.line_code,
            mount_decision=mount_decision,
        ):
            return False

    if rule.line_code.startswith("sablon_montaj"):
        if not _sablon_enabled(payload):
            return False
    if rule.material_gate_path and not _material_gate_matches(payload, rule.material_gate_path, rule.material_gate_value):
        return False
    if rule.line_code == "sablon_montaj_cnc":
        material = _read_string(
            _get_by_path(payload, "finish_setup.mounting_template_material_type")
            or payload.get("mounting_template_material_type")
        )
        if material in ("paper", "forex"):
            return False
    return True


def scan_hourly_contamination(*lines: EstimatedInternalCostLine) -> list[str]:
    hits: list[str] = []
    for line in lines:
        if line.line_type == "capacity_hint":
            continue
        haystack = " ".join(
            [line.code, line.source, line.rule_code, line.basis_type, line.unit or ""]
        ).lower()
        for token in FORBIDDEN_HOURLY_TOKENS:
            if token in haystack:
                hits.append(f"{line.code}:{token}")
    return hits


def _build_operation_line(
    rule: InternalOperationRule,
    payload: dict[str, Any],
    values: dict[str, Any],
) -> EstimatedInternalCostLine:
    quantity = _extract_quantity(payload, values, rule.quantity_paths) if rule.quantity_paths else None
    unit_cost = rule.internal_unit_cost
    subtotal = None
    if unit_cost is not None and quantity is not None and rule.basis_type != "unknown":
        subtotal = round(float(quantity) * float(unit_cost), 4)
    return EstimatedInternalCostLine(
        code=rule.line_code,
        label=rule.label,
        module_code=rule.module_code,
        component_code=rule.component_code,
        line_type="operation",
        basis_type=rule.basis_type,
        quantity=quantity,
        unit=rule.unit,
        internal_unit_cost=unit_cost,
        subtotal=subtotal,
        rule_code=rule.rule_code,
        source=rule.source,
        owner_decision_required=rule.owner_decision_required or rule.basis_type == "unknown",
        warnings=list(rule.warnings),
    )


class EstimatedInternalCostService:
    """Build read-only EstimatedInternalCost preview — no DB writes, no /price."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        pd_builder: ProductDefinitionBuilderService | None = None,
        bom_builder: AggregateCostBomBuilderService | None = None,
    ) -> None:
        self._db = db
        self._pd_builder = pd_builder or ProductDefinitionBuilderService(db)
        self._bom_builder = bom_builder or AggregateCostBomBuilderService(db)

    async def _load_pricing_context(
        self,
    ) -> tuple[dict[str, float], dict[str, str], dict[str, float], dict[str, dict]]:
        material_rates: dict[str, float] = {}
        material_currencies: dict[str, str] = {}
        workcenter_rates: dict[str, float] = {}
        inventory_catalog: dict[str, dict] = {}
        try:
            from sqlalchemy import select

            from models.inventory_materials import Inventory_materials
            from services.inventory_materials_admin_service import load_material_cost_dict, load_material_pricing_dict
            from services.workcenter_rates_service import load_workcenter_rate_dict

            material_rates = await load_material_cost_dict(self._db)
            pricing_dict = await load_material_pricing_dict(self._db)
            material_currencies = {
                code: str(row.get("currency") or "RON").strip().upper()
                for code, row in pricing_dict.items()
            }
            wc_raw = await load_workcenter_rate_dict(self._db)
            for code, val in wc_raw.items():
                if isinstance(val, (int, float)):
                    workcenter_rates[code] = float(val)
            inv_rows = (await self._db.execute(select(Inventory_materials))).scalars().all()
            for row in inv_rows:
                inventory_catalog[row.code] = {
                    "status": row.status,
                    "unit_cost": float(row.unit_cost) if row.unit_cost is not None else None,
                }
        except Exception:
            pass

        self._merge_dev_registry_bridge(material_rates, material_currencies, inventory_catalog)
        return material_rates, material_currencies, workcenter_rates, inventory_catalog

    @staticmethod
    def _merge_dev_registry_bridge(
        material_rates: dict[str, float],
        material_currencies: dict[str, str],
        inventory_catalog: dict[str, dict],
    ) -> None:
        """Fill missing volumetric v2 material costs from Step 8 dev bridge (local/dev/test only)."""
        from core.environment import get_runtime_environment
        from data.dev_volumetric_v2_registry_bridge import DEV_BRIDGE_MATERIAL_RATES, DEV_BRIDGE_SOURCE

        if get_runtime_environment() not in ("local", "development", "test"):
            return

        for code, rate in DEV_BRIDGE_MATERIAL_RATES.items():
            existing_rate = material_rates.get(code)
            if existing_rate is None or existing_rate <= 0:
                material_rates[code] = float(rate)
            material_currencies.setdefault(code, "RON")
            catalog_row = inventory_catalog.get(code) or {}
            catalog_cost = catalog_row.get("unit_cost")
            if catalog_cost is None or (isinstance(catalog_cost, (int, float)) and catalog_cost <= 0):
                inventory_catalog[code] = {
                    "status": catalog_row.get("status") or "active",
                    "unit_cost": float(rate),
                    "source": DEV_BRIDGE_SOURCE,
                }

    async def build_preview(
        self,
        template_code: str,
        *,
        workspace_id: str | None = None,
        quote_input: dict[str, Any] | None = None,
        currency: str = "RON",
    ) -> EstimatedInternalCostPreview | None:
        if template_code not in SUPPORTED_TEMPLATES:
            return None

        pd = await self._pd_builder.build_preview(template_code, workspace_id=workspace_id)
        if pd is None:
            return None

        payload = _payload_from_sources(pd=pd, quote_input=quote_input)
        values = _merged_values(pd, payload)
        has_payload = bool(payload) or pd.source_context.source_payload_type == "workspace_payload"

        bom = await self._bom_builder.build_preview(
            template_code,
            workspace_id=workspace_id,
            quote_input=quote_input or payload or None,
        )
        if bom is None:
            return None

        if bom.graph_cost_projection is not None:
            active_modules = {
                m.module_code for m in bom.active_modules if m.included_in_cost_bom
            }
        else:
            active_modules = _resolve_active_modules(pd, payload)

        rules = RULES_BY_TEMPLATE[template_code]
        material_lines: list[EstimatedInternalCostLine] = []
        operation_lines: list[EstimatedInternalCostLine] = []
        consumable_lines: list[EstimatedInternalCostLine] = []
        overhead_lines: list[EstimatedInternalCostLine] = []
        blockers: list[InternalBlocker] = []
        owner_decisions: list[InternalOwnerDecision] = []
        warnings: list[str] = list(bom.warnings)

        material_rates, material_currencies, workcenter_rates, inventory_catalog = await self._load_pricing_context()
        if workcenter_rates:
            warnings.append(
                "Workcenter hourly rates present in registry — excluded from EstimatedInternalCost totals."
            )

        for mat in bom.costable_materials:
            is_logo = _is_linked_logo_bom_material(mat)
            if not is_logo and mat.mini_module_code and mat.mini_module_code not in active_modules:
                continue
            resolved = mat.resolved_material_code or mat.material_code

            if mat.pricing_availability != "available" or not mat.unit_cost:
                if is_logo or (mat.mini_module_code in active_modules):
                    blockers.append(
                        InternalBlocker(
                            code="INTERNAL_MATERIAL_COST_MISSING",
                            message=f"Missing inventory unit_cost for {resolved}.",
                            module_code=mat.mini_module_code,
                            material_code=resolved,
                        )
                    )
                continue

            quantity, mat_warnings = _estimate_material_quantity(mat, payload, values)
            if quantity is None and (is_logo or mat.mini_module_code in active_modules):
                blockers.append(
                    InternalBlocker(
                        code="INTERNAL_GEOMETRY_MISSING",
                        message=f"Missing quantity geometry for material {resolved}.",
                        module_code=mat.mini_module_code,
                        material_code=resolved,
                    )
                )
                continue

            unit_cost = mat.unit_cost
            subtotal = round(float(quantity) * float(unit_cost), 4) if quantity is not None else None
            line_code = f"material_{resolved}"
            if mat.component_ref:
                line_code = f"{line_code}_{mat.component_ref}"
            material_lines.append(
                EstimatedInternalCostLine(
                    code=line_code,
                    label=mat.label or resolved,
                    module_code=mat.mini_module_code,
                    component_code=mat.component_ref,
                    line_type="material",
                    basis_type="inventory_unit_cost",
                    quantity=quantity,
                    unit=mat.unit,
                    internal_unit_cost=unit_cost,
                    subtotal=subtotal,
                    rule_code="INT_MAT_INVENTORY_UNIT_COST",
                    source="inventory_materials.unit_cost",
                    warnings=mat_warnings,
                )
            )

        logo_operation_count = 0
        for op in bom.costable_operations:
            if op.operation_code in INTERNAL_QC_OPERATION_CODES:
                continue
            if op.operation_code.lower().startswith("qc_"):
                continue
            if not _is_linked_logo_bom_operation(op):
                continue

            unit_cost, rule_code, source = _resolve_logo_operation_internal_rate(op.operation_code, op=op)
            quantity, op_warnings = _estimate_logo_operation_quantity(op, payload, values)
            operation_lines.append(
                _build_logo_operation_line_from_bom(
                    op,
                    quantity=quantity,
                    unit_cost=unit_cost,
                    rule_code=rule_code,
                    source=source,
                    warnings=op_warnings,
                )
            )
            logo_operation_count += 1

            if quantity is None:
                blockers.append(
                    InternalBlocker(
                        code="INTERNAL_GEOMETRY_MISSING",
                        message=f"Missing quantity geometry for logo operation {op.operation_code}.",
                        module_code=op.mini_module_code,
                    )
                )
            if unit_cost is None:
                blockers.append(
                    InternalBlocker(
                        code="INTERNAL_OPERATION_RULE_MISSING",
                        message=f"Missing internal operation unit cost rule for {op.operation_code}.",
                        module_code=op.mini_module_code,
                    )
                )

        for rule in rules["operations"]:
            if not _operation_rule_applies(rule, active_modules, payload):
                continue
            line = _build_operation_line(rule, payload, values)
            operation_lines.append(line)
            if line.owner_decision_required and rule.owner_decision_code:
                owner_decisions.append(
                    InternalOwnerDecision(
                        code=rule.owner_decision_code,
                        label=rule.label,
                        module_code=rule.module_code,
                        detail=rule.owner_decision_detail,
                    )
                )
            if line.basis_type == "unknown" and rule.criticality == "critical":
                blockers.append(
                    InternalBlocker(
                        code="INTERNAL_OPERATION_BASIS_UNKNOWN",
                        message=f"Internal operation basis unknown for {line.code}.",
                        module_code=line.module_code,
                    )
                )
            elif line.internal_unit_cost is None and rule.criticality == "critical" and not line.owner_decision_required:
                blockers.append(
                    InternalBlocker(
                        code="INTERNAL_OPERATION_RULE_MISSING",
                        message=f"Missing internal operation unit cost rule for {line.code}.",
                        module_code=line.module_code,
                    )
                )

        for rule in rules["consumables"]:
            if rule.module_code not in active_modules:
                continue
            qty = _extract_quantity(payload, values, rule.quantity_paths)
            consumable_lines.append(
                EstimatedInternalCostLine(
                    code=rule.line_code,
                    label=rule.label,
                    module_code=rule.module_code,
                    line_type="consumable",
                    basis_type=rule.basis_type,
                    quantity=qty,
                    unit=rule.unit,
                    internal_unit_cost=rule.internal_unit_cost,
                    subtotal=None,
                    rule_code=rule.rule_code,
                    source=rule.source,
                    owner_decision_required=rule.owner_decision_required,
                )
            )
            if rule.owner_decision_code:
                owner_decisions.append(
                    InternalOwnerDecision(
                        code=rule.owner_decision_code,
                        label=rule.label,
                        module_code=rule.module_code,
                        detail=rule.owner_decision_detail,
                    )
                )

        for rule in rules["overhead"]:
            overhead_lines.append(
                EstimatedInternalCostLine(
                    code=rule.line_code,
                    label=rule.label,
                    line_type="overhead",
                    basis_type=rule.basis_type,
                    quantity=rule.placeholder_percent,
                    unit="%",
                    rule_code=rule.rule_code,
                    source=rule.source,
                    owner_decision_required=rule.owner_decision_required,
                )
            )
            owner_decisions.append(
                InternalOwnerDecision(
                    code=rule.owner_decision_code,
                    label=rule.label,
                    detail=rule.owner_decision_detail,
                )
            )

        capacity_hints: list[CapacityHint] = []
        if has_payload:
            for hint_rule in rules["capacity"]:
                if hint_rule.module_code and hint_rule.module_code not in active_modules:
                    continue
                if hint_rule.code.startswith("acm_"):
                    from services.acm_quote_input_helpers import is_acm_boxed_mounting_payload

                    if not is_acm_boxed_mounting_payload(payload):
                        continue
                capacity_values = dict(values)
                capacity_values.setdefault("quantity", payload.get("quantity") or 1)
                if hint_rule.code.startswith("acm_"):
                    capacity_values["letter_count"] = int(payload.get("quantity") or 1)
                result = resolve_formula(hint_rule.formula_id, hint_rule.formula_params, capacity_values)
                if result.resolved and result.value is not None:
                    capacity_hints.append(
                        CapacityHint(
                            code=hint_rule.code,
                            label=hint_rule.label,
                            estimated_minutes=float(result.value),
                            source=hint_rule.source,
                            purpose=hint_rule.purpose,  # type: ignore[arg-type]
                            excluded_from_total=True,
                        )
                    )

        missing_critical_geometry = self._missing_critical_geometry(payload, active_modules) if has_payload else []
        if missing_critical_geometry:
            blockers.append(
                InternalBlocker(
                    code="INTERNAL_GEOMETRY_MISSING",
                    message=f"Missing critical geometry: {', '.join(sorted(set(missing_critical_geometry)))}.",
                )
            )

        contamination = scan_hourly_contamination(
            *material_lines,
            *operation_lines,
            *consumable_lines,
            *overhead_lines,
        )

        material_total = round(sum(l.subtotal for l in material_lines if l.subtotal is not None), 4)
        operation_total = round(sum(l.subtotal for l in operation_lines if l.subtotal is not None), 4)
        consumables_total = round(sum(l.subtotal for l in consumable_lines if l.subtotal is not None), 4) or None
        overhead_total = round(sum(l.subtotal for l in overhead_lines if l.subtotal is not None), 4) or None
        estimated_total = round(material_total + operation_total + (consumables_total or 0) + (overhead_total or 0), 4)

        status, ready, confidence, completeness = self._compute_status(
            blockers=blockers,
            owner_decisions=owner_decisions,
            contamination=contamination,
            has_payload=has_payload,
            material_lines=material_lines,
            operation_lines=operation_lines,
            missing_geometry=missing_critical_geometry,
        )
        if not contamination:
            if bom.bom_status == "partial" or any(
                WARNING_LINKED_SEGMENT_FINISH_PARTIAL in w for w in warnings
            ):
                status = "partial"
                ready = False

        provenance = [
            InternalProvenanceEntry(
                key="aggregate_cost_bom",
                source="aggregate_cost_bom_builder_service",
                detail=(
                    f"workspace={bool(workspace_id)} bom_status={bom.bom_status} "
                    f"materials={len(material_lines)} operations={len(operation_lines)} "
                    f"logo_operations={logo_operation_count}"
                ),
            ),
            InternalProvenanceEntry(
                key="internal_rules",
                source="internal_cost_rules_volumetric_v2",
                detail="temporary_local_catalog_until_step_7i",
            ),
            InternalProvenanceEntry(
                key="inventory",
                source="inventory_materials.unit_cost",
                detail="acquisition_cost_not_commercial_price",
            ),
            InternalProvenanceEntry(
                key="active_modules",
                source="estimated_internal_cost_service",
                detail=f"modules={','.join(sorted(active_modules))}",
            ),
        ]

        notes = [
            "Read-only EstimatedInternalCost preview — Step 7H.",
            "Does not call /price, CostEngine, QuoteOrchestrator, or aggregate_cost_bom_price_bridge.",
            "Time estimates appear only in capacity_hints — excluded from totals.",
        ]

        return EstimatedInternalCostPreview(
            template_code=template_code,
            source=ESTIMATED_INTERNAL_COST_SOURCE,
            status=status,
            estimated_material_lines=material_lines,
            estimated_operation_lines=operation_lines,
            estimated_consumable_lines=consumable_lines,
            estimated_overhead_lines=overhead_lines,
            capacity_hints=capacity_hints,
            estimated_material_cost=material_total if material_lines else None,
            estimated_operation_cost=operation_total if operation_total else None,
            estimated_consumables_cost=consumables_total,
            estimated_overhead_cost=overhead_total,
            estimated_total_internal_cost=estimated_total if material_lines or operation_total else None,
            currency=currency,
            internal_blockers=blockers,
            warnings=warnings,
            unknown_owner_decisions=owner_decisions,
            hourly_contamination_detected=contamination,
            provenance=provenance,
            completeness=completeness,
            confidence=confidence,  # type: ignore[arg-type]
            ready_for_quote_snapshot=ready,
            notes=notes,
            input_summary={
                "has_payload": has_payload,
                "active_modules": sorted(active_modules),
                "workspace_id": workspace_id,
            },
        )

    @staticmethod
    def _missing_critical_geometry(payload: dict[str, Any], active_modules: set[str]) -> list[str]:
        missing: list[str] = []
        geometry = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
        client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
        merged = {**client, **geometry}
        for key in ("letter_count", "letter_face_area_m2", "letter_perimeter_m", "width_mm", "height_mm"):
            if _positive_number(merged.get(key)) is None and _positive_number(payload.get(key)) is None:
                missing.append(key)
        if "modelare_cant" in active_modules:
            finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
            if _positive_number(finish.get("return_depth_mm") or payload.get("return_depth_mm")) is None:
                missing.append("return_depth_mm")
        return missing

    @staticmethod
    def _compute_status(
        *,
        blockers: list[InternalBlocker],
        owner_decisions: list[InternalOwnerDecision],
        contamination: list[str],
        has_payload: bool,
        material_lines: list[EstimatedInternalCostLine],
        operation_lines: list[EstimatedInternalCostLine],
        missing_geometry: list[str],
    ) -> tuple[str, bool, str, float]:
        if contamination:
            return "blocked", False, "low", 0.0
        critical_codes = frozenset(
            {
                "INTERNAL_GEOMETRY_MISSING",
                "INTERNAL_MATERIAL_COST_MISSING",
                "INTERNAL_OPERATION_BASIS_UNKNOWN",
                "INTERNAL_OPERATION_RULE_MISSING",
            }
        )
        critical_owner = frozenset({"INTERNAL_DEBITARE_SPATE_ML_VS_M2", "INTERNAL_SABLON_FOREX_COST"})
        if missing_geometry or any(b.code in critical_codes for b in blockers):
            return "blocked", False, "low", 0.3
        if any(d.code in critical_owner for d in owner_decisions):
            return "blocked", False, "low", 0.4

        optional_owner = [d for d in owner_decisions if d.code not in critical_owner]
        total_slots = max(len(material_lines) + len(operation_lines), 1)
        filled = sum(1 for l in material_lines + operation_lines if l.subtotal is not None)
        completeness = round(filled / total_slots, 4)

        if optional_owner or not has_payload or completeness < 0.5:
            return "partial", False, "medium", completeness
        if completeness >= 0.8:
            return "ready", True, "high", completeness
        return "partial", False, "medium", completeness
