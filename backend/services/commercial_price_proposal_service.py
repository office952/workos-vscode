"""Read-only CommercialPriceProposal preview builder (Step 7G).

Answers: "What commercial price do we propose for the product on commercial rules?"
Does NOT use CostEngine, QuoteOrchestrator, or hourly basis.
Linked-logo finish lines may map to existing Pricing Registry operation rates
(workcenter_rates) plus company EUR→RON settings — never invent finish tariffs.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from data.commercial_rules_volumetric_v2 import (
    ACM_BOXED_ASSEMBLY_MIN_EUR,
    ACM_SHEET_ENVIRONMENT_EXTERIOR,
    ACM_SHEET_MATERIAL_EUR_M2_BY_VARIANT,
    ACM_SHEET_MIRROR_VARIANTS,
    ACM_SHEET_VARIANT_WHEN_ABSENT,
    CANT_ORACAL_MATERIAL_EUR_M2_BY_SERIES,
    CANT_ORACAL_WRAP_SERIES_BY_RETURN_FINISH_TYPE,
    CANT_RAL_PAINT_GATE_VALUES,
    CANT_RAL_PAINT_MATERIAL_EUR_ML_BY_DEPTH_MM,
    CANT_RAL_PAINT_MINIMUM_EUR_PER_COLOR,
    COMMERCIAL_PRODUCT_LABELS,
    CRITICAL_MODULE_CODES,
    FACE_FINISH_NONE_VALUES,
    FACE_FINISH_ORACAL_TOKENS,
    FACE_FINISH_PRINT_LAMINATE_TOKENS,
    FACE_FINISH_UNPRICED_COMMERCIAL_TOKENS,
    FORBIDDEN_HOURLY_TOKENS,
    LETTERS_ACM_PACK_MIN_EUR,
    ORACAL_8500_MATERIAL_EUR_M2_BY_ROLL_WIDTH_MM,
    ORACAL_8500_SUPPORTED_ROLL_WIDTH_MM,
    RAL_MINIMUM_TOP_UP_LINE_CODE,
    RAL_MINIMUM_TOP_UP_RULE_CODE,
    RULES_BY_TEMPLATE,
    CommercialRuleDefinition,
    volumetric_presentation_currency,
)
from schemas.commercial_price_proposal import (
    COMMERCIAL_PRICE_PROPOSAL_SOURCE,
    CommercialBlocker,
    CommercialCurrencyBucket,
    CommercialOwnerDecision,
    CommercialPriceLine,
    CommercialPriceProposalPreview,
    CommercialProductBreakdown,
    CommercialProductSubtotal,
    CommercialProposalStatus,
    CommercialProvenanceEntry,
)
from schemas.product_definition import ProductDefinitionPreview
from services.acm_quote_input_helpers import (
    ACM_BOXED_MOUNTING_STANDALONE_REQUIRED_KEYS,
    is_acm_boxed_mounting_payload,
    is_acm_boxed_mounting_standalone_root_template,
)
from services.intake_v6_modular_form_contract_service import IntakeV6ModularFormContractService
from services.linked_logo_commercial_price_service import build_linked_logo_commercial_lines
from services.product_definition_builder_service import (
    ProductDefinitionBuilderService,
    _classify_modules,
    _has_geometry_basics,
    _read_bool,
    _read_string,
)

BAR_MOUNTING = frozenset({"steel_bars", "aluminum_bars"})
GATE_ONLY_MODULES = frozenset({"geometry_svg"})
FUTURE_MODULES = frozenset({"electrica_logo"})
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
SUPPORTED_TEMPLATES = frozenset(RULES_BY_TEMPLATE.keys())


def _rules_template_key(template_code: str) -> str | None:
    """Map canonical/uppercased codes to RULES_BY_TEMPLATE keys (preserve declared casing)."""
    if template_code in RULES_BY_TEMPLATE:
        return template_code
    needle = str(template_code or "").strip().upper()
    if not needle:
        return None
    for key in RULES_BY_TEMPLATE:
        if key.upper() == needle:
            return key
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


def _lower_str(value: Any) -> str:
    return str(value or "").strip().lower()


# Face selections that carry an Owner-priced vinyl material rule and therefore also carry the
# single Owner vinyl-application line. "none" and stock cant never appear here.
FACE_FINISH_VINYL_APPLIED_TOKENS = FACE_FINISH_ORACAL_TOKENS | FACE_FINISH_PRINT_LAMINATE_TOKENS
# Canonical root key first (services/volumetric_face_vinyl_service.resolve_face_vinyl_roll_width_mm),
# then the finish_setup aliases the Intake V6 artwork-finish rows persist.
ORACAL_8500_ROLL_WIDTH_PATHS = (
    "face_vinyl_roll_width_mm",
    "finish_setup.face_vinyl_roll_width_mm",
    "finish_setup.face_roll_width_mm",
    "face_roll_width_mm",
)
# Canonical operator capture (F7F): acm_sheet_material_v1. Read from the ACM panel instance
# (letters + ACM composition) and from the standalone ACM root payload / mounting configuration.
ACM_SHEET_MATERIAL_PATHS = (
    "finish_setup.acm_panel_instance.sheet_material",
    "acm_panel_instance.sheet_material",
    "finish_setup.mounting_solution.configuration.acm_panel_instance.sheet_material",
    "finish_setup.mounting_solution.configuration.acm_sheet_material",
    "finish_setup.acm_sheet_material",
    "acm_sheet_material",
)


def _face_finish_token(payload: dict[str, Any]) -> str:
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    return _lower_str(finish.get("face_finish_type") or payload.get("face_finish_type"))


def _letter_group_finishes(payload: dict[str, Any]) -> list[dict[str, Any]]:
    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    groups = finish.get("letter_group_finishes") or payload.get("letter_group_finishes")
    if not isinstance(groups, list):
        return []
    return [group for group in groups if isinstance(group, dict)]


def _supported_8500_width(raw: Any) -> int | None:
    width = _positive_number(raw)
    if width is None:
        return None
    candidate = int(round(width))
    return candidate if candidate in ORACAL_8500_MATERIAL_EUR_M2_BY_ROLL_WIDTH_MM else None


def _confirmed_oracal_8500_roll_width_mm(payload: dict[str, Any]) -> int | None:
    """Owner F7F: rate by SKU + CONFIRMED roll width. Never guess, never default a tier.

    The job-level `face_vinyl_roll_width_mm` is a *derived dominant-value projection* of the
    per-group captures, so on a mixed-face job it can go null (or carry a width belonging to a
    different face) while an 8500 group really exists. The per-group capture is the operator's
    actual selection, so it wins whenever any group carries the 8500 face; groups that disagree,
    or that are not operator-confirmed, resolve to nothing and the caller fails closed.
    """
    oracal_8500_groups = [
        group
        for group in _letter_group_finishes(payload)
        if _lower_str(group.get("face_finish_type")) == "oracal_8500"
    ]
    if oracal_8500_groups:
        widths = {
            _supported_8500_width(group.get("face_vinyl_roll_width_mm"))
            for group in oracal_8500_groups
            if group.get("confirmed") is True
        }
        if len(widths) == 1 and None not in widths:
            return widths.pop()
        return None

    for path in ORACAL_8500_ROLL_WIDTH_PATHS:
        raw = _get_by_path(payload, path)
        if raw is None and "." not in path:
            raw = payload.get(path)
        width = _positive_number(raw)
        if width is None:
            continue
        candidate = int(round(width))
        if candidate in ORACAL_8500_MATERIAL_EUR_M2_BY_ROLL_WIDTH_MM:
            return candidate
    return None


def _acm_sheet_material(payload: dict[str, Any]) -> dict[str, Any]:
    for path in ACM_SHEET_MATERIAL_PATHS:
        raw = _get_by_path(payload, path)
        if isinstance(raw, dict):
            return raw
    return {}


def _acm_sheet_variant_token(payload: dict[str, Any]) -> str:
    """Absent variant keeps the owner-confirmed standard bond sheet; unknown fails closed."""
    token = _lower_str(_acm_sheet_material(payload).get("variant"))
    return token or ACM_SHEET_VARIANT_WHEN_ABSENT


def _acm_sheet_variant_is_known(payload: dict[str, Any]) -> bool:
    return _acm_sheet_variant_token(payload) in ACM_SHEET_MATERIAL_EUR_M2_BY_VARIANT


def _acm_mirror_exterior_unproven(payload: dict[str, Any]) -> bool:
    material = _acm_sheet_material(payload)
    variant = _lower_str(material.get("variant"))
    if variant not in ACM_SHEET_MIRROR_VARIANTS:
        return False
    if _lower_str(material.get("environment")) != ACM_SHEET_ENVIRONMENT_EXTERIOR:
        return False
    return not _read_string(material.get("exterior_sku"))


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
        "return_finish_type",
        "selected_psu_watts",
        "required_psu_watts",
        "led_module_count",
        "letter_led_module_count",
        "emblem_led_module_count",
        "emblem_lighting_mode",
        "face_finish_type",
        "backing_mode",
        "letter_group_finishes",
        "artwork_finishes",
        "mounting_solution",
        "mounting_scope",
        "site_installation_included",
        "applied_content",
        "letters_layer_outbox_m2",
        "letters_layer_outbox_source",
    ):
        if key in out and key not in merged_finish:
            merged_finish[key] = out[key]
    if merged_finish:
        out["finish_setup"] = merged_finish
    # Lift composition markers for CPP gate when only nested on finish_setup.
    if out.get("applied_content") in (None, "") and merged_finish.get("applied_content") not in (
        None,
        "",
    ):
        out["applied_content"] = merged_finish.get("applied_content")
    if out.get("letters_layer_outbox_m2") in (None, "", 0, 0.0) and merged_finish.get(
        "letters_layer_outbox_m2"
    ) not in (None, "", 0, 0.0):
        out["letters_layer_outbox_m2"] = merged_finish.get("letters_layer_outbox_m2")

    geometry = out.get("quote_geometry") if isinstance(out.get("quote_geometry"), dict) else {}
    merged_geometry = dict(geometry)
    for key in ("letter_count", "letter_face_area_m2", "letter_perimeter_m", "depth_mm", "artwork_boxes", "artwork_return_layers", "artwork_area_m2", "artwork_piece_count"):
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
    payload: dict[str, Any] = {}
    if quote_input:
        payload = _coalesce_quote_input(quote_input)
    elif pd.source_context.source_payload_type == "workspace_payload":
        payload = {
            "finish_setup": {},
            "quote_geometry": dict(pd.geometry_inputs),
            "client": {},
            "svg_source": {},
        }
        for key, value in pd.canonical_values.items():
            if key.startswith("finish_setup."):
                payload.setdefault("finish_setup", {})[key.split(".", 1)[1]] = value
            elif key in CRITICAL_GEOMETRY_KEYS or key in ("vector_file", "analysis_ready"):
                if key in ("width_mm", "height_mm", "depth_mm"):
                    payload.setdefault("client", {})[key] = value
                elif key in ("letter_count", "letter_face_area_m2", "letter_perimeter_m"):
                    payload.setdefault("quote_geometry", {})[key] = value
                elif key == "vector_file":
                    payload.setdefault("svg_source", {})["file_name"] = value
                else:
                    payload[key] = value

    # Enrich geometry/finish from ProductDefinition workspace projection when quote_input
    # adapter omitted linked-logo fields (artwork boxes, letter/emblem LED splits).
    geometry = payload.setdefault("quote_geometry", {})
    if isinstance(geometry, dict) and isinstance(pd.geometry_inputs, dict):
        for key, value in pd.geometry_inputs.items():
            if key not in geometry or geometry.get(key) in (None, [], {}):
                geometry[key] = value
    finish = payload.setdefault("finish_setup", {})
    if isinstance(finish, dict) and isinstance(pd.canonical_values, dict):
        for key, value in pd.canonical_values.items():
            if key.startswith("finish_setup."):
                short = key.split(".", 1)[1]
                if short not in finish or finish.get(short) in (None, [], {}):
                    finish[short] = value
            elif key in (
                "letter_led_module_count",
                "emblem_led_module_count",
                "emblem_lighting_mode",
                "artwork_finishes",
                "mounting_solution",
                "mounting_scope",
                "site_installation_included",
                "led_module_count",
                "light_color",
            ):
                if key not in finish or finish.get(key) in (None, [], {}):
                    finish[key] = value

    if isinstance(finish, dict):
        letter_led = _positive_number(finish.get("letter_led_module_count"))
        emblem_led = _positive_number(finish.get("emblem_led_module_count"))
        total_led = _positive_number(finish.get("led_module_count") or finish.get("total_led_module_count"))
        if letter_led is None and total_led is not None and emblem_led is not None and total_led >= emblem_led:
            finish["letter_led_module_count"] = round(total_led - emblem_led, 4)

    return payload


def _module_is_commercial_active(state: str) -> bool:
    return state in ("always_on", "active", "conditional_active")


def _legacy_resolve_active_commercial_modules(
    pd: ProductDefinitionPreview,
    payload: dict[str, Any],
) -> set[str]:
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
        from services.letters_finish_mounting_runtime_decoupling import (
            apply_decoupled_module_activation,
        )

        if apply_decoupled_module_activation(
            code=code,
            state=mod.state,
            activation_kind=mod.activation_kind or "",
            active=active,
        ):
            continue
        if code == "sistem_led":
            if mod.state in ("active", "conditional_active"):
                active.add(code)
            continue
        if mod.activation_kind in ("always_on", "required_module"):
            active.add(code)
            continue
        if _module_is_commercial_active(mod.state):
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


def _resolve_active_commercial_modules(
    pd: ProductDefinitionPreview,
    payload: dict[str, Any],
) -> set[str]:
    from services.offer_scope_resolver_service import resolve_pricing_active_modules

    return resolve_pricing_active_modules(
        pd=pd,
        payload=payload,
        quote_input=payload,
        legacy_fn=lambda p, qi: _legacy_resolve_active_commercial_modules(p, qi or {}),
    )


async def _resolve_commercial_modules_for_preview(
    *,
    db: AsyncSession,
    pd: ProductDefinitionPreview,
    payload: dict[str, Any],
    template_code: str,
    workspace_id: str | None,
    quote_input: dict[str, Any] | None,
) -> set[str]:
    if workspace_id and pd.source_context.source_payload_type == "workspace_payload":
        from services.product_aggregate_graph_cost_projection_service import resolve_cost_active_modules
        from services.product_aggregate_service import ProductAggregateService

        aggregate = await ProductAggregateService(db).build_for_workspace(template_code, workspace_id)
        if aggregate and aggregate.composition_graph is not None:
            active, _ = resolve_cost_active_modules(
                pd=pd,
                aggregate=aggregate,
                quote_input=quote_input or payload,
            )
            return active
    return _resolve_active_commercial_modules(pd, payload)


def _extract_quantity(payload: dict[str, Any], paths: tuple[str, ...]) -> float | int | None:
    for path in paths:
        value = _get_by_path(payload, path)
        if value is None and "." not in path:
            value = payload.get(path)
        number = _positive_number(value)
        if number is not None:
            if number.is_integer():
                return int(number)
            return round(number, 6)
    return None


def _material_gate_matches(payload: dict[str, Any], rule: CommercialRuleDefinition) -> bool:
    if not rule.material_gate_path:
        return True
    raw = _get_by_path(payload, rule.material_gate_path)
    if raw is None:
        alt_key = rule.material_gate_path.split(".")[-1]
        raw = _get_by_path(payload, f"finish_setup.{alt_key}")
    return _read_string(raw) == rule.material_gate_value


def _sablon_enabled(payload: dict[str, Any]) -> bool:
    from services.mounting_scope_service import is_mounting_preparation_active

    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    if not is_mounting_preparation_active(finish):
        return False
    enabled = _read_bool(finish.get("mounting_template_enabled"))
    if enabled is None:
        enabled = _read_bool(payload.get("mounting_template_enabled"))
    return enabled is not False


def _sablon_material(payload: dict[str, Any]) -> str | None:
    return _read_string(
        _get_by_path(payload, "finish_setup.mounting_template_material_type")
        or payload.get("mounting_template_material_type")
    )


def _site_install_commercially_required(payload: dict[str, Any]) -> bool:
    """True when commercial montaj must be present (G5 / installation_template)."""
    from services.mounting_scope_service import is_site_installation_active
    from services.mounting_solution_service import is_installation_template_solution

    finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
    if is_site_installation_active(finish):
        return True
    if is_site_installation_active(payload):
        return True
    solution = finish.get("mounting_solution")
    if solution is None:
        solution = payload.get("mounting_solution")
    return is_installation_template_solution(solution)


def _rule_applies(rule: CommercialRuleDefinition, active_modules: set[str], payload: dict[str, Any]) -> bool:
    from services.letters_acm_composition_commercial_v1 import (
        COMPOSITION_LINE_PREFIX,
        is_letters_acm_composition_active,
    )
    from services.lighting_mount_consumer_service import resolve_lighting_mount_consumers
    from services.offer_scope_led_subscope_service import (
        commercial_line_led_subscope,
        led_consumer_row_allowed,
        partial_led_subscope_filter,
    )

    # Site installation commercial marker — not surface finish; may fire without support module.
    if rule.line_code == "montaj" and _site_install_commercially_required(payload):
        return True

    # Letters↔ACM composition connection sheet — independent of active_modules set.
    if rule.line_code.startswith(COMPOSITION_LINE_PREFIX):
        return is_letters_acm_composition_active(payload)

    module_key = rule.module_gate or rule.module_code
    if rule.always_include and rule.criticality == "optional":
        return module_key in active_modules or rule.module_code in active_modules

    if module_key not in active_modules and rule.module_code not in active_modules:
        return False

    scope = payload.get("offer_scope") if isinstance(payload.get("offer_scope"), dict) else {}
    sold_led = partial_led_subscope_filter(frozenset(scope.get("sold_modules") or []))
    mount_decision = resolve_lighting_mount_consumers(payload, payload)
    if sold_led is not None and rule.module_code == "sistem_led":
        sub = commercial_line_led_subscope(rule.line_code)
        if not led_consumer_row_allowed(
            row_subscope=sub,
            sold_led_subscopes=sold_led,
            commercial_line_code=rule.line_code,
            mount_decision=mount_decision,
        ):
            return False

    if rule.line_code == "finisaje_colantare_vopsire":
        face_token = _face_finish_token(payload)
        if (
            face_token in FACE_FINISH_NONE_VALUES
            or face_token in FACE_FINISH_VINYL_APPLIED_TOKENS
            or face_token in FACE_FINISH_UNPRICED_COMMERCIAL_TOKENS
        ):
            return False

    if rule.line_code == "finisaje_print_laminate_material":
        return _face_finish_token(payload) in FACE_FINISH_PRINT_LAMINATE_TOKENS

    if rule.line_code == "finisaje_aplicare_autocolant_fata":
        # Charged once, only when a priced vinyl/print material actually covers the face.
        return _face_finish_token(payload) in FACE_FINISH_VINYL_APPLIED_TOKENS

    if rule.line_code.startswith("finisaje_cant_oracal_"):
        finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
        cant_token = _lower_str(finish.get("return_finish_type") or payload.get("return_finish_type"))
        return cant_token in CANT_ORACAL_WRAP_SERIES_BY_RETURN_FINISH_TYPE

    if rule.line_code.startswith("finisaje_cant_ral_"):
        finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
        cant_token = _lower_str(finish.get("return_finish_type") or payload.get("return_finish_type"))
        return cant_token in CANT_RAL_PAINT_GATE_VALUES

    if rule.line_code.startswith("sablon_montaj"):
        # ACM composition uses bundled letters_acm_conn_sablon_process @ 20 EUR/mp.
        if is_letters_acm_composition_active(payload):
            return False
        if not _sablon_enabled(payload):
            return False
        material = _sablon_material(payload)
        if rule.line_code == "sablon_montaj_hartie":
            return material == "paper"
        if rule.line_code == "sablon_montaj_forex":
            return material == "forex"
        if rule.line_code == "sablon_montaj":
            return material not in ("paper", "forex")
        return True

    if rule.material_gate_path and not _material_gate_matches(payload, rule):
        return False

    if rule.line_code.startswith("acm_"):
        from services.acm_quote_input_helpers import is_acm_boxed_mounting_payload

        if not is_acm_boxed_mounting_payload(payload):
            return False

    return True


async def _build_line(
    db: AsyncSession,
    rule: CommercialRuleDefinition,
    payload: dict[str, Any],
    *,
    measurement_qty: float | None = None,
    measurement_source: str | None = None,
    presentation_currency: str | None = None,
) -> CommercialPriceLine:
    from services.linked_logo_commercial_price_service import (
        _load_registry_operation_rate,
        _normalize_unit_price_to_cpp_ron,
    )

    warnings = list(rule.warnings)
    presentation = (presentation_currency or "").strip().upper() or None
    # LETTERS_CANONICAL_PRODUCT_SLICE_V1: prefer Aggregate commercial measurements.
    if measurement_qty is not None:
        quantity = float(measurement_qty)
        source_prefix = measurement_source or "product_aggregate.commercial_measurements"
        warnings.append(f"quantity_source={source_prefix}")
    else:
        quantity = _extract_quantity(payload, rule.quantity_paths) if rule.quantity_paths else None
        if quantity is not None:
            warnings.append("quantity_source=COMPATIBILITY_WORKSPACE_PATH")

    # Letters↔ACM composition mp lines — outbox / mounting_template_area honesty path.
    if rule.line_code.startswith("letters_acm_conn_") and rule.basis_type == "m2":
        from services.letters_acm_composition_commercial_v1 import (
            resolve_letters_layer_outbox_m2,
        )

        outbox_qty, outbox_src = resolve_letters_layer_outbox_m2(payload)
        if outbox_qty is not None:
            quantity = float(outbox_qty)
            warnings.append(f"quantity_source=letters_acm_outbox:{outbox_src}")
            if outbox_src not in (
                "letters_layer_outbox_m2",
                "finish_setup.letters_layer_outbox_m2",
            ):
                warnings.append(
                    "outbox_qty_fallback_not_canonical_letters_layer_outbox_m2"
                )
        elif quantity is None:
            warnings.append("missing_letters_layer_outbox_m2")

    owner_required = rule.owner_decision_required
    basis_type = rule.basis_type
    source = rule.source
    registry_pricing_code = (rule.registry_pricing_code or "").strip().upper() or None
    source_currency = rule.documented_unit_price_currency
    cpp_currency: str | None = None
    fx_rate: float | None = None
    fx_source: str | None = None

    if rule.line_code == "finisaje_colantare_vopsire":
        groups = _get_by_path(payload, "finish_setup.letter_group_finishes")
        if groups is None:
            warnings.append("Finish groups not confirmed — numeric commercial price deferred.")
        elif isinstance(groups, list) and not groups:
            warnings.append("Finish groups empty — owner review recommended.")

    dynamic_unit_price: float | None = None
    dynamic_unit_price_currency: str | None = None
    # When a dynamic rate is required but unresolvable, the documented rate must not silently
    # stand in for it (fail closed instead of quietly pricing the wrong material).
    suppress_documented_fallback = False

    if rule.line_code.startswith("finisaje_cant_oracal_"):
        finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
        if rule.line_code == "finisaje_cant_oracal_material":
            cant_token = _lower_str(
                finish.get("return_finish_type") or payload.get("return_finish_type")
            )
            series = CANT_ORACAL_WRAP_SERIES_BY_RETURN_FINISH_TYPE.get(cant_token)
            dynamic_unit_price = CANT_ORACAL_MATERIAL_EUR_M2_BY_SERIES.get(series) if series else None
            if dynamic_unit_price is not None:
                dynamic_unit_price_currency = "EUR"
                warnings.append(f"cant_oracal_series_resolved={series}")
        # Material and application share the same proven applied surface: the developed wrap area.
        perimeter = _extract_quantity(payload, ("quote_geometry.letter_perimeter_m", "letter_perimeter_m"))
        depth_mm = _positive_number(finish.get("return_depth_mm", payload.get("return_depth_mm")))
        if perimeter is not None and depth_mm is not None:
            quantity = round(float(perimeter) * (float(depth_mm) / 1000.0), 6)
            warnings.append("quantity_source=perimeter_m_x_return_depth_mm_to_m2")
        else:
            quantity = None

    if rule.line_code == "finisaje_oracal_8500_material":
        roll_width_mm = _confirmed_oracal_8500_roll_width_mm(payload)
        dynamic_unit_price = (
            ORACAL_8500_MATERIAL_EUR_M2_BY_ROLL_WIDTH_MM.get(roll_width_mm) if roll_width_mm else None
        )
        if dynamic_unit_price is not None:
            dynamic_unit_price_currency = "EUR"
            warnings.append(f"oracal_8500_roll_width_confirmed={roll_width_mm}mm")
        else:
            owner_required = True
            warnings.append(
                "COMMERCIAL_CONFIGURATION_INCOMPLETE:face_vinyl_roll_width_mm_not_confirmed;"
                f"supported={'/'.join(str(w) for w in ORACAL_8500_SUPPORTED_ROLL_WIDTH_MM)}"
            )

    if rule.line_code in ("acm_panel_face_material", "acm_return_strip_material"):
        variant = _acm_sheet_variant_token(payload)
        dynamic_unit_price = ACM_SHEET_MATERIAL_EUR_M2_BY_VARIANT.get(variant)
        if dynamic_unit_price is not None:
            dynamic_unit_price_currency = "EUR"
            warnings.append(f"acm_sheet_variant_resolved={variant}")
            if variant in ACM_SHEET_MIRROR_VARIANTS:
                # Replacement rate — never the standard rate plus a mirror surcharge.
                warnings.append("acm_mirror_rate_is_replacement_not_surcharge")
        else:
            owner_required = True
            suppress_documented_fallback = True
            warnings.append(f"COMMERCIAL_RULE_MISSING:acm_sheet_variant={variant}")

    if rule.line_code == "finisaje_cant_ral_material":
        finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
        depth_raw = _positive_number(finish.get("return_depth_mm", payload.get("return_depth_mm")))
        depth_tier = int(depth_raw) if depth_raw is not None and float(depth_raw).is_integer() else None
        dynamic_unit_price = (
            CANT_RAL_PAINT_MATERIAL_EUR_ML_BY_DEPTH_MM.get(depth_tier) if depth_tier else None
        )
        if dynamic_unit_price is not None:
            dynamic_unit_price_currency = "EUR"
            warnings.append(f"cant_ral_depth_tier_resolved={depth_tier}mm")

    if rule.line_code in ("finisaje_cant_oracal_material", "finisaje_cant_ral_material") and (
        dynamic_unit_price is None
    ):
        owner_required = True
        warnings.append(f"{rule.pricing_rule_code}:unresolved_dynamic_unit_price")

    if dynamic_unit_price is not None:
        unit_price = dynamic_unit_price
    elif suppress_documented_fallback:
        unit_price = None
    else:
        unit_price = rule.documented_unit_price
    if dynamic_unit_price_currency is not None:
        source_currency = dynamic_unit_price_currency
    if unit_price is not None and source_currency:
        cpp_currency = "RON" if str(source_currency).upper() == "RON" else None

    if registry_pricing_code:
        resolved = await _load_registry_operation_rate(db, registry_pricing_code)
        if resolved is None:
            # Fall back to documented EUR catalog rate when registry row is absent
            # (keeps Owner-documented CNC/forming usable in tests without inventing FX).
            if unit_price is not None and str(source_currency or "").upper() == "EUR":
                owner_required = False
                cpp_currency = "EUR" if presentation == "EUR" else None
                warnings.append(
                    f"registry_lookup_missed:{registry_pricing_code};"
                    "using_documented_eur_catalog_fallback;configure_at=/inventory/pricing"
                )
                source = f"{rule.source}:documented_eur_fallback"
            else:
                unit_price = None
                owner_required = True
                warnings.append(
                    f"registry_lookup_missed:{registry_pricing_code};configure_at=/inventory/pricing"
                )
                source = f"{rule.source}:registry_unresolved"
        else:
            resolved_currency = str(resolved.source_currency or "").upper()
            # F7H: volumetric/ACM presentation EUR keeps registry EUR natively — no company FX.
            if presentation == "EUR" and resolved_currency == "EUR":
                unit_price = float(resolved.unit_price_source)
                owner_required = False
                source_currency = "EUR"
                cpp_currency = "EUR"
                fx_rate = None
                fx_source = None
                source = f"pricing_registry:operation:{resolved.pricing_code}:EUR"
                warnings.append(
                    f"registry_bound={resolved.pricing_code};"
                    f"source_unit_price={resolved.unit_price_source};"
                    f"rate_basis={resolved.rate_basis};"
                    "presentation_currency=EUR;no_fx_normalization"
                )
            else:
                ron_price, fx_rate, fx_source, fx_error = await _normalize_unit_price_to_cpp_ron(
                    db,
                    unit_price=resolved.unit_price_source,
                    source_currency=resolved.source_currency,
                )
                if ron_price is None:
                    unit_price = None
                    owner_required = True
                    warnings.append(
                        f"BLOCKED_BY_CANONICAL_CURRENCY_CONVERSION:{fx_error or 'unknown'}"
                    )
                    source = f"{rule.source}:currency_gate_blocked"
                    source_currency = resolved.source_currency
                    cpp_currency = None
                else:
                    unit_price = ron_price
                    owner_required = False
                    source_currency = resolved.source_currency
                    cpp_currency = "RON"
                    source = (
                        f"pricing_registry:operation:{resolved.pricing_code}"
                        f":{resolved.source_currency}->{cpp_currency}"
                    )
                    warnings.append(
                        f"registry_bound={resolved.pricing_code};"
                        f"source_unit_price={resolved.unit_price_source};"
                        f"rate_basis={resolved.rate_basis}"
                    )

    if quantity is None and unit_price is not None:
        if basis_type in ("piece", "fixed", "set"):
            quantity = 1.0

    subtotal = None
    if unit_price is not None and quantity is not None and basis_type not in ("unknown",):
        subtotal = round(float(quantity) * float(unit_price), 4)

    if rule.pricing_rule_code == "ACM_BOXED_ASSEMBLY_M2_MIN" and unit_price is not None and quantity is not None:
        subtotal = round(max(float(quantity) * float(unit_price), ACM_BOXED_ASSEMBLY_MIN_EUR), 4)
        warnings.append(f"minimum_charge_applied={ACM_BOXED_ASSEMBLY_MIN_EUR}EUR")

    if rule.pricing_rule_code == "LETTERS_ACM_PACK_M2_MIN" and unit_price is not None and quantity is not None:
        subtotal = round(max(float(quantity) * float(unit_price), LETTERS_ACM_PACK_MIN_EUR), 4)
        warnings.append(f"minimum_charge_applied={LETTERS_ACM_PACK_MIN_EUR}EUR")

    if basis_type == "unknown":
        owner_required = True

    # F7H publication honesty — never label an unpublished gap as Owner-final.
    rate_status: str | None = None
    if unit_price is None and owner_required:
        rate_status = "unpublished"
    elif "owner_commercial_decision:f7f" in (source or "") or "owner_commercial_decision:f7h" in (
        source or ""
    ):
        rate_status = "owner_confirmed"
    elif "pricing_registry:operation:" in (source or ""):
        rate_status = "owner_confirmed"
    elif unit_price is not None:
        rate_status = "provisional"

    # When presentation currency is EUR, keep native EUR lines labeled as EUR.
    if presentation == "EUR" and str(source_currency or "").upper() == "EUR" and cpp_currency is None:
        cpp_currency = "EUR"

    return CommercialPriceLine(
        code=rule.line_code,
        label=rule.label,
        module_code=rule.module_code,
        component_code=rule.component_code,
        basis_type=basis_type,
        quantity=quantity,
        unit=rule.unit,
        commercial_unit_price=unit_price,
        subtotal=subtotal,
        pricing_rule_code=rule.pricing_rule_code,
        source=source,
        owner_decision_required=owner_required,
        warnings=warnings,
        registry_pricing_code=registry_pricing_code,
        source_currency=source_currency,
        cpp_currency=cpp_currency,
        currency_conversion_rate=fx_rate,
        currency_conversion_source=fx_source,
        commercial_product_key=rule.commercial_product_key,
        rate_publication_status=rate_status,  # type: ignore[arg-type]
    )


def scan_forbidden_hourly_usage(lines: list[CommercialPriceLine]) -> list[str]:
    import re

    hits: list[str] = []
    for line in lines:
        haystack = " ".join(
            [
                line.code,
                line.source,
                line.pricing_rule_code,
                line.basis_type,
                line.unit or "",
            ]
        ).lower()
        for token in FORBIDDEN_HOURLY_TOKENS:
            # Word-boundary match so "workcenter_rates" does not trip "workcenter_rate".
            if re.search(rf"(?<![a-z0-9_]){re.escape(token)}(?![a-z0-9_])", haystack):
                hits.append(f"{line.code}:{token}")
    return hits


def _missing_critical_geometry(
    payload: dict[str, Any],
    active_modules: set[str],
    rules_key: str | None = None,
) -> list[str]:
    # AGENT-B-F003: TPL-ACM-BOXED-MOUNTING-SUPPORT_v1 standalone root has ACM-shaped geometry
    # (panel_width_mm/panel_height_mm/acm_thickness_mm/return_depth_mm/fold_sides) — never
    # letter-shaped (letter_count/letter_face_area_m2/.../vector_file). Do not invent ACM shell
    # finish prices here; this only validates presence of the required geometry inputs.
    if rules_key is not None and is_acm_boxed_mounting_standalone_root_template(rules_key):
        missing: list[str] = []
        for key in ACM_BOXED_MOUNTING_STANDALONE_REQUIRED_KEYS:
            if key == "fold_sides":
                if not _read_string(payload.get(key)):
                    missing.append(key)
            elif _positive_number(payload.get(key)) is None:
                missing.append(key)
        return missing

    missing = []
    geometry = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
    client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
    merged = {**client, **geometry, **{k: payload[k] for k in payload if k in CRITICAL_GEOMETRY_KEYS}}

    for key in ("letter_count", "letter_face_area_m2", "letter_perimeter_m", "width_mm", "height_mm"):
        if _positive_number(merged.get(key)) is None and _positive_number(payload.get(key)) is None:
            missing.append(key)

    if "modelare_cant" in active_modules:
        finish = payload.get("finish_setup") if isinstance(payload.get("finish_setup"), dict) else {}
        depth = finish.get("return_depth_mm", payload.get("return_depth_mm"))
        if _positive_number(depth) is None:
            missing.append("return_depth_mm")

    svg = payload.get("svg_source") if isinstance(payload.get("svg_source"), dict) else {}
    if not _read_string(svg.get("file_name")) and not _read_string(payload.get("vector_file")):
        missing.append("vector_file")

    return missing


_RAL_MINIMUM_EUR_UNSET = object()


def _apply_cant_ral_paint_minimum_eur(
    lines: list[CommercialPriceLine],
    *,
    blockers: list[CommercialBlocker],
    minimum_eur_per_color: float | None | object = _RAL_MINIMUM_EUR_UNSET,
) -> None:
    """F7H: RAL commercial minimum as EUR-only explicit top-up (never mutates other lines).

    Legacy Owner text documented 100 RON/color — that RON figure is not converted to EUR and
    is not applied here. When the catalog EUR floor is unpublished (None), no top-up is
    invented. Eligible lines must share currency EUR; otherwise fail-closed.
    Scope: per RAL color (canonicalFinishEnumMap cant_ral_minimum_policy) — one color scope
    per return-cant RAL selection in this CPP slice.
    """
    # Read catalog live so test monkeypatches and config updates are honored (do not bind
    # the default argument at import time).
    floor = (
        CANT_RAL_PAINT_MINIMUM_EUR_PER_COLOR
        if minimum_eur_per_color is _RAL_MINIMUM_EUR_UNSET
        else minimum_eur_per_color
    )
    material = next(
        (line for line in lines if line.pricing_rule_code == "VOL_V2_CANT_RAL_MATERIAL_ML"),
        None,
    )
    if material is None or material.subtotal is None:
        return
    labor = next(
        (line for line in lines if line.pricing_rule_code == "VOL_V2_CANT_RAL_LABOR_ML"),
        None,
    )
    eligible = [material]
    if labor is not None and labor.subtotal is not None:
        eligible.append(labor)

    currencies = {_line_currency(line) for line in eligible}
    if None in currencies or len(currencies) != 1:
        blockers.append(
            CommercialBlocker(
                code="COMMERCIAL_MINIMUM_CURRENCY_MISMATCH",
                message=(
                    "RAL minimum/top-up refused: eligible RAL material/labor lines do not share "
                    "a single currency. Cross-currency numeric floors are forbidden."
                ),
                module_code="finisaje",
            )
        )
        return
    currency = next(iter(currencies))
    if currency != "EUR":
        blockers.append(
            CommercialBlocker(
                code="COMMERCIAL_MINIMUM_CURRENCY_MISMATCH",
                message=(
                    f"RAL minimum/top-up refused: expected EUR eligible lines, got {currency}."
                ),
                module_code="finisaje",
            )
        )
        return

    if floor is None:
        material.warnings.append(
            "ral_minimum_eur_unpublished;no_top_up_invented;legacy_100_RON_not_applied"
        )
        return

    if float(floor) <= 0:
        return

    eligible_subtotal = round(sum(float(line.subtotal or 0.0) for line in eligible), 4)
    top_up = round(max(0.0, float(floor) - eligible_subtotal), 4)
    if top_up <= 0:
        material.warnings.append(
            f"ral_minimum_cleared minimum_eur={floor};"
            f"eligible_subtotal_eur={eligible_subtotal}"
        )
        return

    lines.append(
        CommercialPriceLine(
            code=RAL_MINIMUM_TOP_UP_LINE_CODE,
            label="Finisaje — minim comercial RAL (top-up)",
            module_code="finisaje",
            component_code="comp_finisaj_litere",
            basis_type="minimum",
            quantity=1.0,
            unit="culoare",
            commercial_unit_price=top_up,
            subtotal=top_up,
            pricing_rule_code=RAL_MINIMUM_TOP_UP_RULE_CODE,
            source="owner_commercial_policy:f7h_ral_minimum_top_up_eur",
            owner_decision_required=False,
            warnings=[
                f"ral_minimum_top_up_eur={top_up};"
                f"minimum_eur_per_color={floor};"
                f"eligible_subtotal_eur={eligible_subtotal};scope=per_ral_color"
            ],
            source_currency="EUR",
            cpp_currency="EUR",
            commercial_product_key=material.commercial_product_key or "letters",
            rate_publication_status="owner_confirmed",
        )
    )


def _line_currency(line: CommercialPriceLine) -> str | None:
    """The currency a line's subtotal is actually expressed in — never assumed."""
    resolved = line.cpp_currency or line.source_currency
    return str(resolved).upper() if resolved else None


def _currency_buckets(pairs: list[tuple[str, float]]) -> list[CommercialCurrencyBucket]:
    totals: dict[str, float] = {}
    for currency, amount in pairs:
        totals[currency] = round(totals.get(currency, 0.0) + amount, 4)
    return [
        CommercialCurrencyBucket(currency=currency, subtotal=totals[currency])
        for currency in sorted(totals)
    ]


def _build_commercial_product_breakdown(
    *,
    lines: list[CommercialPriceLine],
    blockers: list[CommercialBlocker],
    vat_rate_percent: float | None,
    vat_policy_source: str | None,
    presentation_currency: str | None = None,
) -> CommercialProductBreakdown:
    """F7F/F7H: per-product subtotals plus one complete offer total, or an honest refusal.

    Mixed currencies are never fused. Without an explicit provenance-bearing exchange rate this
    engine has no authority to convert, so it reports the mix instead of inventing a total.
    When ``presentation_currency`` is set (EUR for volumetric+ACM pilot), the complete total is
    emitted only if every summable line matches that currency.
    """
    ordered_keys: list[str] = []
    per_product: dict[str, list[CommercialPriceLine]] = {}
    for line in lines:
        key = line.commercial_product_key or "letters"
        if key not in per_product:
            per_product[key] = []
            ordered_keys.append(key)
        per_product[key].append(line)

    # Blockers are offer-wide today, so every product inherits them. Owner-pending lines are a
    # different, softer state: the total still stands, but it is explicitly partial.
    global_blocker_codes = sorted({blocker.code for blocker in blockers})
    presentation = (presentation_currency or "").strip().upper() or None

    products: list[CommercialProductSubtotal] = []
    all_pairs: list[tuple[str, float]] = []
    all_pending: list[str] = []
    for key in ordered_keys:
        product_lines = per_product[key]
        pairs: list[tuple[str, float]] = []
        pending: list[str] = []
        unknown_currency = False
        presentation_mismatch = False
        for line in product_lines:
            if line.subtotal is None:
                if line.owner_decision_required:
                    pending.append(line.code)
                continue
            currency = _line_currency(line)
            if currency is None:
                unknown_currency = True
                continue
            if presentation and currency != presentation:
                presentation_mismatch = True
            pairs.append((currency, float(line.subtotal)))
        all_pairs.extend(pairs)
        all_pending.extend(pending)

        blocker_codes = list(global_blocker_codes)
        if unknown_currency:
            blocker_codes.append("COMMERCIAL_LINE_CURRENCY_UNKNOWN")
        if presentation_mismatch:
            blocker_codes.append("COMMERCIAL_RULE_CURRENCY_MISMATCH")
        products.append(
            CommercialProductSubtotal(
                product_key=key,
                label=COMMERCIAL_PRODUCT_LABELS.get(key, key),
                line_codes=[line.code for line in product_lines],
                subtotals_by_currency=_currency_buckets(pairs),
                blocked=bool(blocker_codes),
                blocker_codes=sorted(set(blocker_codes)),
                pending_line_codes=pending,
            )
        )

    buckets = _currency_buckets(all_pairs)
    currency_mix = len(buckets) > 1
    total: float | None = None
    total_currency: str | None = None
    unavailable_reason: str | None = None
    if any(product.blocked for product in products):
        unavailable_reason = "COMMERCIAL_PRODUCT_BLOCKED"
        if currency_mix:
            unavailable_reason = "COMMERCIAL_CURRENCY_MIX_UNRESOLVED"
        elif presentation and any(
            "COMMERCIAL_RULE_CURRENCY_MISMATCH" in product.blocker_codes for product in products
        ):
            unavailable_reason = "COMMERCIAL_PRESENTATION_CURRENCY_UNAVAILABLE"
    elif currency_mix:
        unavailable_reason = "COMMERCIAL_CURRENCY_MIX_UNRESOLVED"
    elif not buckets:
        unavailable_reason = "COMMERCIAL_TOTAL_NOT_PRICED"
    elif presentation and buckets[0].currency != presentation:
        unavailable_reason = "COMMERCIAL_PRESENTATION_CURRENCY_UNAVAILABLE"
    else:
        total = buckets[0].subtotal
        total_currency = buckets[0].currency

    return CommercialProductBreakdown(
        products=products,
        subtotals_by_currency=buckets,
        currency_mix_detected=currency_mix,
        presentation_currency=presentation,
        complete_offer_total=total,
        complete_offer_total_currency=total_currency,
        complete_offer_total_unavailable_reason=unavailable_reason,
        complete_offer_total_is_partial=total is not None and bool(all_pending),
        pending_line_codes=sorted(set(all_pending)),
        vat_policy_source=vat_policy_source,
        vat_rate_percent=vat_rate_percent,
    )


def _compute_status(
    *,
    lines: list[CommercialPriceLine],
    blockers: list[CommercialBlocker],
    owner_decisions: list[CommercialOwnerDecision],
    forbidden_hourly: list[str],
    missing_geometry: list[str],
    has_payload: bool,
    site_install_required: bool = False,
) -> tuple[CommercialProposalStatus, bool, str]:
    if forbidden_hourly:
        return "blocked", False, "low"
    if missing_geometry:
        return "blocked", False, "low"

    critical_blocker_codes = frozenset(
        {
            "CRITICAL_GEOMETRY_MISSING",
            "COMMERCIAL_RULE_MISSING",
            "COMMERCIAL_BASIS_UNKNOWN",
            "COMMERCIAL_CONFIGURATION_INCOMPLETE",
            "TECHNICAL_MATERIAL_COMPATIBILITY_REQUIRED",
        }
    )
    if any(b.code in critical_blocker_codes for b in blockers):
        return "blocked", False, "low"

    critical_owner_codes = frozenset({"DEBITARE_SPATE_BASIS_ML_VS_M2", "SABLON_FOREX_COMMERCIAL_PRICE"})
    if any(d.code in critical_owner_codes for d in owner_decisions):
        return "blocked", False, "low"

    if not has_payload:
        return "partial", False, "medium"

    optional_line_codes = {"ambalare"}
    if not site_install_required:
        optional_line_codes.add("montaj")

    # Linked-logo owner-pending tariffs keep proposal partial (fail closed).
    logo_pending = [
        line
        for line in lines
        if line.segment_key
        and line.owner_decision_required
        and line.commercial_unit_price is None
        and line.quantity is not None
    ]
    if logo_pending:
        return "partial", False, "medium"

    if site_install_required:
        montaj = next((line for line in lines if line.code == "montaj"), None)
        if montaj is None or montaj.commercial_unit_price is None:
            return "partial", False, "medium"

    critical_lines = [
        line
        for line in lines
        if line.module_code in CRITICAL_MODULE_CODES and line.code not in optional_line_codes
    ]
    if critical_lines and all(
        line.owner_decision_required is False and line.basis_type != "unknown" for line in critical_lines
    ):
        return "ready", True, "high"
    return "partial", False, "medium"


class CommercialPriceProposalService:
    """Build read-only commercial price proposal preview — no DB writes, no /price."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        pd_builder: ProductDefinitionBuilderService | None = None,
    ) -> None:
        self._db = db
        self._pd_builder = pd_builder or ProductDefinitionBuilderService(db)

    async def build_preview(
        self,
        template_code: str,
        *,
        workspace_id: str | None = None,
        quote_input: dict[str, Any] | None = None,
        currency: str = "RON",
    ) -> CommercialPriceProposalPreview | None:
        rules_key = _rules_template_key(template_code)
        if rules_key is None:
            return None

        pd = await self._pd_builder.build_preview(rules_key, workspace_id=workspace_id)
        if pd is None:
            return None

        payload = _payload_from_sources(pd=pd, quote_input=quote_input)
        # Prefer confirmed return perimeter for VL product-total; control quote_geometry bridge.
        if str(rules_key or "").startswith("TPL-VOLUMETRIC-LETTERS"):
            from services.volum_aluminiu_quantity_ownership import (
                apply_confirmed_perimeter_quote_geometry_bridge,
            )

            payload, _perimeter_authority = apply_confirmed_perimeter_quote_geometry_bridge(payload)
        has_payload = bool(payload) or pd.source_context.source_payload_type == "workspace_payload"
        active_modules = await _resolve_commercial_modules_for_preview(
            db=self._db,
            pd=pd,
            payload=payload,
            template_code=rules_key,
            workspace_id=workspace_id,
            quote_input=quote_input,
        )
        rules = RULES_BY_TEMPLATE[rules_key]
        presentation_currency = volumetric_presentation_currency(rules_key)
        # Scoped presentation currency for the volumetric+ACM pilot — never a global default.
        if presentation_currency:
            currency = presentation_currency

        lines: list[CommercialPriceLine] = []
        blockers: list[CommercialBlocker] = []
        owner_decisions: list[CommercialOwnerDecision] = []
        warnings: list[str] = []
        covered_modules = {r.module_code for r in rules}

        for mod in active_modules:
            if mod in CRITICAL_MODULE_CODES and mod not in covered_modules:
                blockers.append(
                    CommercialBlocker(
                        code="COMMERCIAL_RULE_MISSING",
                        message=f"No commercial rule catalog entry for active module {mod}.",
                        module_code=mod,
                    )
                )

        # Canonical Letters measurements from ProductAggregate (non-monetary).
        measurement_by_line: dict[str, float] = {}
        measurement_diag: list[str] = []
        if workspace_id:
            from services.letters_commercial_measurement_service import (
                build_letters_commercial_measurements,
                measurement_quantity_by_line_code,
            )
            from services.product_aggregate_service import ProductAggregateService

            aggregate = await ProductAggregateService(self._db).build_for_workspace(
                template_code, workspace_id
            )
            bundle = getattr(aggregate, "commercial_measurements", None) if aggregate else None
            if bundle is None:
                bundle = build_letters_commercial_measurements(
                    template_code=template_code,
                    pd=pd,
                    quote_input=payload,
                    active_modules=active_modules,
                )
                measurement_diag.append("measurements_built_inline_for_cpp")
            if bundle is not None:
                for rule in rules:
                    qty, src = measurement_quantity_by_line_code(bundle, rule.line_code)
                    if qty is not None:
                        measurement_by_line[rule.line_code] = qty
                measurement_diag.extend(list(bundle.diagnostics or []))

        for rule in rules:
            if not _rule_applies(rule, active_modules, payload):
                continue
            m_qty = measurement_by_line.get(rule.line_code)
            m_src = (
                "product_aggregate.commercial_measurements"
                if m_qty is not None
                else None
            )
            line = await _build_line(
                self._db,
                rule,
                payload,
                measurement_qty=m_qty,
                measurement_source=m_src,
                presentation_currency=presentation_currency,
            )
            lines.append(line)
            if line.owner_decision_required and rule.owner_decision_code:
                owner_decisions.append(
                    CommercialOwnerDecision(
                        code=rule.owner_decision_code,
                        label=rule.label,
                        module_code=rule.module_code,
                        detail=rule.owner_decision_detail,
                    )
                )
            if line.basis_type == "unknown" and rule.criticality == "critical":
                blockers.append(
                    CommercialBlocker(
                        code="COMMERCIAL_BASIS_UNKNOWN",
                        message=f"Commercial basis unknown for {line.code}.",
                        module_code=line.module_code,
                    )
                )
            # Universal currency guard — priced line must declare a currency; presentation
            # mismatch is fail-closed (never rename RON as EUR).
            if line.subtotal is not None:
                line_ccy = _line_currency(line)
                if line_ccy is None:
                    blockers.append(
                        CommercialBlocker(
                            code="COMMERCIAL_LINE_CURRENCY_UNKNOWN",
                            message=(
                                f"Priced line {line.code} has no resolvable currency "
                                f"(rule={line.pricing_rule_code})."
                            ),
                            module_code=line.module_code,
                        )
                    )
                elif presentation_currency and line_ccy != presentation_currency:
                    blockers.append(
                        CommercialBlocker(
                            code="COMMERCIAL_RULE_CURRENCY_MISMATCH",
                            message=(
                                f"Line {line.code} currency {line_ccy} does not match "
                                f"presentation currency {presentation_currency} "
                                f"(rule={line.pricing_rule_code})."
                            ),
                            module_code=line.module_code,
                        )
                    )

        _apply_cant_ral_paint_minimum_eur(lines, blockers=blockers)

        # Selection-granularity fail-closed (F7E cross-cutting recommendation): a commercially
        # relevant face finish selection with no owner-priced CPP rule must block "ready" —
        # never silently fall back to the flat finisaje_colantare_vopsire rate.
        if str(rules_key or "").startswith("TPL-VOLUMETRIC-LETTERS") and "finisaje" in active_modules:
            face_token = _face_finish_token(payload)
            if face_token in FACE_FINISH_UNPRICED_COMMERCIAL_TOKENS:
                blockers.append(
                    CommercialBlocker(
                        code="COMMERCIAL_RULE_MISSING",
                        message=(
                            f"No commercial rule catalog entry for face_finish_type={face_token}."
                        ),
                        module_code="finisaje",
                    )
                )
            # Owner F7F: Oracal 8500 is priced by SKU + confirmed roll width. A missing or
            # unsupported width must block — never resolve to the cheaper or dearer tier.
            if (
                face_token == "oracal_8500"
                and _confirmed_oracal_8500_roll_width_mm(payload) is None
            ):
                blockers.append(
                    CommercialBlocker(
                        code="COMMERCIAL_CONFIGURATION_INCOMPLETE",
                        message=(
                            "Oracal 8500 requires one confirmed face_vinyl_roll_width_mm "
                            f"({' or '.join(str(w) for w in ORACAL_8500_SUPPORTED_ROLL_WIDTH_MM)} mm) "
                            "before a commercial rate can be resolved. Letter groups that carry the "
                            "8500 face must be confirmed and must agree on one width."
                        ),
                        module_code="finisaje",
                    )
                )

        # Owner F7F ACM sheet law: unknown variant fails closed; mirror on an exterior
        # installation needs a proven supplier SKU before any technical compatibility claim.
        if is_acm_boxed_mounting_payload(payload):
            if not _acm_sheet_variant_is_known(payload):
                blockers.append(
                    CommercialBlocker(
                        code="COMMERCIAL_RULE_MISSING",
                        message=(
                            "No commercial rule catalog entry for acm_sheet_variant="
                            f"{_acm_sheet_variant_token(payload)}."
                        ),
                        module_code="structura_suport",
                    )
                )
            if _acm_mirror_exterior_unproven(payload):
                blockers.append(
                    CommercialBlocker(
                        code="TECHNICAL_MATERIAL_COMPATIBILITY_REQUIRED",
                        message=(
                            "Mirror ACM is interior by default. An exterior installation requires "
                            "a proven supplier SKU before technical compatibility is claimed."
                        ),
                        module_code="structura_suport",
                    )
                )

        # Linked logo commercial is composition/full-product only — not part of
        # Letters Slice 1 component_subset (RETURN-CANT / FACE / BACK / LIGHTING).
        from services.active_scope_resolver_service import compile_active_scope

        _scope_for_logo = compile_active_scope(
            template_code=rules_key,
            payload=payload,
            quote_input=quote_input or payload,
        )
        logo_lines: list[CommercialPriceLine] = []
        logo_owner_decisions: list[CommercialOwnerDecision] = []
        if _scope_for_logo.use_legacy_full_product:
            logo_lines, logo_owner_decisions = await build_linked_logo_commercial_lines(
                db=self._db,
                payload=payload,
                pd_linked_segments=getattr(pd, "linked_template_runtime_segments", None),
                presentation_currency=presentation_currency,
            )
            for logo_line in logo_lines:
                # Linked logo segments are sold under the letters product, not the ACM panel.
                logo_line.commercial_product_key = "letters"
                if logo_line.subtotal is not None and presentation_currency:
                    logo_ccy = _line_currency(logo_line)
                    if logo_ccy is None:
                        blockers.append(
                            CommercialBlocker(
                                code="COMMERCIAL_LINE_CURRENCY_UNKNOWN",
                                message=(
                                    f"Priced logo line {logo_line.code} has no resolvable currency."
                                ),
                                module_code=logo_line.module_code,
                            )
                        )
                    elif logo_ccy != presentation_currency:
                        blockers.append(
                            CommercialBlocker(
                                code="COMMERCIAL_RULE_CURRENCY_MISMATCH",
                                message=(
                                    f"Logo line {logo_line.code} currency {logo_ccy} does not match "
                                    f"presentation currency {presentation_currency}."
                                ),
                                module_code=logo_line.module_code,
                            )
                        )
            lines.extend(logo_lines)
            owner_decisions.extend(logo_owner_decisions)
        elif getattr(pd, "linked_template_runtime_segments", None):
            warnings.append(
                "ACTIVE_SCOPE_SUBSET: linked logo commercial lines suppressed "
                "(Logo remains BLOCKED for standalone sold scope)."
            )

        missing_geometry = (
            _missing_critical_geometry(payload, active_modules, rules_key=rules_key) if has_payload else []
        )
        if missing_geometry:
            blockers.append(
                CommercialBlocker(
                    code="CRITICAL_GEOMETRY_MISSING",
                    message=f"Missing critical geometry: {', '.join(sorted(set(missing_geometry)))}.",
                )
            )

        if "structura_suport" not in active_modules:
            mounting = _read_string(
                _get_by_path(payload, "finish_setup.mounting_system") or payload.get("mounting_system")
            )
            if mounting == "direct_wall":
                warnings.append("structura_suport correctly inactive for direct_wall mounting.")

        site_install_required = _site_install_commercially_required(payload)
        forbidden_hourly = scan_forbidden_hourly_usage(lines)
        status, quote_ready, confidence = _compute_status(
            lines=lines,
            blockers=blockers,
            owner_decisions=owner_decisions,
            forbidden_hourly=forbidden_hourly,
            missing_geometry=missing_geometry,
            has_payload=has_payload,
            site_install_required=site_install_required,
        )

        # F7F/F7H: honest per-product / per-currency view. CPP stays tax-exclusive — the fiscal
        # policy (VAT) is a separate owner and is filled in downstream, never guessed here.
        # Never fuse mixed-currency line subtotals into a single legacy number.
        product_breakdown = _build_commercial_product_breakdown(
            lines=lines,
            blockers=blockers,
            vat_rate_percent=None,
            vat_policy_source=None,
            presentation_currency=presentation_currency,
        )
        subtotal_commercial = product_breakdown.complete_offer_total

        provenance = [
            CommercialProvenanceEntry(
                key="product_definition",
                source="product_definition_builder_service",
                detail=f"read_only=true workspace_id={workspace_id or 'none'}",
            ),
            CommercialProvenanceEntry(
                key="commercial_rules",
                source="commercial_rules_volumetric_v2",
                detail="temporary_local_catalog_until_step_7i",
            ),
            CommercialProvenanceEntry(
                key="active_modules",
                source="commercial_price_proposal_service",
                detail=f"modules={','.join(sorted(active_modules))}",
            ),
        ]
        if logo_lines:
            provenance.append(
                CommercialProvenanceEntry(
                    key="linked_logo_commercial",
                    source="linked_logo_commercial_price_service",
                    detail=f"segments={len({line.segment_key for line in logo_lines if line.segment_key})}",
                )
            )
        if quote_input:
            provenance.append(
                CommercialProvenanceEntry(
                    key="quote_input",
                    source="request_body",
                    detail="read_only_normalization_no_pricing_engine",
                )
            )

        notes = [
            "Read-only CommercialPriceProposal preview — Step 7G / F7H.",
            "Does not call /price, CostEngine, or QuoteOrchestrator.",
            "Does not consume EstimatedInternalCost, HR, machine hourly, or inventory unit_cost "
            "as client price.",
            (
                "Volumetric letters + ACM presentation currency is EUR (scoped). Registry EUR "
                "rates stay native EUR — no company FX, no live/online/inferred FX, no RON rename."
                if presentation_currency == "EUR"
                else "Registry EUR rates for non-pilot templates may normalize via company "
                "EUR→RON settings when presentation is not EUR."
            ),
            "Site installation (montaj) binds once per job to SITE_INSTALLATION_STANDARD "
            "(200 EUR fixed / locatie). Travel outside Bucharest is not auto-added. "
            "Fail closed if the rate is unavailable.",
            "Hourly commercial basis is forbidden.",
        ]

        return CommercialPriceProposalPreview(
            template_code=rules_key,
            source=COMMERCIAL_PRICE_PROPOSAL_SOURCE,
            status=status,
            commercial_price_lines=lines,
            subtotal_commercial=subtotal_commercial,
            commercial_total=subtotal_commercial,
            commercial_product_breakdown=product_breakdown,
            currency=currency,
            unknown_owner_decisions=owner_decisions,
            commercial_blockers=blockers,
            warnings=warnings,
            forbidden_hourly_usage_detected=forbidden_hourly,
            provenance=provenance,
            confidence=confidence,  # type: ignore[arg-type]
            quote_ready_for_commercial_review=quote_ready,
            notes=notes,
            input_summary={
                "has_payload": has_payload,
                "active_modules": sorted(active_modules),
                "workspace_id": workspace_id,
                "linked_logo_segments": sorted(
                    {line.segment_key for line in logo_lines if line.segment_key}
                ),
                "site_install_required": site_install_required,
            },
        )