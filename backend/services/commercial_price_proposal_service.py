"""Read-only CommercialPriceProposal preview builder (Step 7G).

Answers: "What commercial price do we propose for the product on commercial rules?"
Does NOT use CostEngine, QuoteOrchestrator, workcenter_rates, or hourly basis.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from data.commercial_rules_volumetric_v2 import (
    CRITICAL_MODULE_CODES,
    FORBIDDEN_HOURLY_TOKENS,
    RULES_BY_TEMPLATE,
    CommercialRuleDefinition,
)
from schemas.commercial_price_proposal import (
    COMMERCIAL_PRICE_PROPOSAL_SOURCE,
    CommercialBlocker,
    CommercialOwnerDecision,
    CommercialPriceLine,
    CommercialPriceProposalPreview,
    CommercialProposalStatus,
    CommercialProvenanceEntry,
)
from schemas.product_definition import ProductDefinitionPreview
from services.intake_v6_modular_form_contract_service import IntakeV6ModularFormContractService
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
        "return_finish_type",
        "selected_psu_watts",
        "required_psu_watts",
        "led_module_count",
        "face_finish_type",
        "backing_mode",
        "letter_group_finishes",
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
        if _module_is_commercial_active(mod.state):
            active.add(code)

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


def _rule_applies(rule: CommercialRuleDefinition, active_modules: set[str], payload: dict[str, Any]) -> bool:
    from services.lighting_mount_consumer_service import resolve_lighting_mount_consumers
    from services.offer_scope_led_subscope_service import (
        commercial_line_led_subscope,
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
        sub = commercial_line_led_subscope(rule.line_code)
        if not led_consumer_row_allowed(
            row_subscope=sub,
            sold_led_subscopes=sold_led,
            commercial_line_code=rule.line_code,
            mount_decision=mount_decision,
        ):
            return False

    if rule.line_code.startswith("sablon_montaj"):
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


def _build_line(
    rule: CommercialRuleDefinition,
    payload: dict[str, Any],
) -> CommercialPriceLine:
    quantity = _extract_quantity(payload, rule.quantity_paths) if rule.quantity_paths else None
    warnings = list(rule.warnings)
    owner_required = rule.owner_decision_required
    basis_type = rule.basis_type

    if rule.line_code == "finisaje_colantare_vopsire":
        groups = _get_by_path(payload, "finish_setup.letter_group_finishes")
        if groups is None:
            warnings.append("Finish groups not confirmed — numeric commercial price deferred.")
        elif isinstance(groups, list) and not groups:
            warnings.append("Finish groups empty — owner review recommended.")

    unit_price = rule.documented_unit_price
    if quantity is None and unit_price is not None:
        if basis_type in ("piece", "fixed", "set"):
            quantity = 1.0

    subtotal = None
    if unit_price is not None and quantity is not None and basis_type not in ("unknown",):
        subtotal = round(float(quantity) * float(unit_price), 4)

    if rule.pricing_rule_code == "ACM_BOXED_ASSEMBLY_M2_MIN" and unit_price is not None and quantity is not None:
        from data.commercial_rules_volumetric_v2 import ACM_BOXED_ASSEMBLY_MIN_EUR

        subtotal = round(max(float(quantity) * float(unit_price), ACM_BOXED_ASSEMBLY_MIN_EUR), 4)
        warnings.append(f"minimum_charge_applied={ACM_BOXED_ASSEMBLY_MIN_EUR}EUR")

    if basis_type == "unknown":
        owner_required = True

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
        source=rule.source,
        owner_decision_required=owner_required,
        warnings=warnings,
    )


def scan_forbidden_hourly_usage(lines: list[CommercialPriceLine]) -> list[str]:
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
            if token in haystack:
                hits.append(f"{line.code}:{token}")
    return hits


def _missing_critical_geometry(payload: dict[str, Any], active_modules: set[str]) -> list[str]:
    missing: list[str] = []
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


def _compute_status(
    *,
    lines: list[CommercialPriceLine],
    blockers: list[CommercialBlocker],
    owner_decisions: list[CommercialOwnerDecision],
    forbidden_hourly: list[str],
    missing_geometry: list[str],
    has_payload: bool,
) -> tuple[CommercialProposalStatus, bool, str]:
    if forbidden_hourly:
        return "blocked", False, "low"
    if missing_geometry:
        return "blocked", False, "low"

    critical_blocker_codes = frozenset(
        {"CRITICAL_GEOMETRY_MISSING", "COMMERCIAL_RULE_MISSING", "COMMERCIAL_BASIS_UNKNOWN"}
    )
    if any(b.code in critical_blocker_codes for b in blockers):
        return "blocked", False, "low"

    critical_owner_codes = frozenset({"DEBITARE_SPATE_BASIS_ML_VS_M2", "SABLON_FOREX_COMMERCIAL_PRICE"})
    if any(d.code in critical_owner_codes for d in owner_decisions):
        return "blocked", False, "low"

    if not has_payload:
        return "partial", False, "medium"

    optional_line_codes = frozenset({"ambalare", "montaj"})
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
        if template_code not in SUPPORTED_TEMPLATES:
            return None

        pd = await self._pd_builder.build_preview(template_code, workspace_id=workspace_id)
        if pd is None:
            return None

        payload = _payload_from_sources(pd=pd, quote_input=quote_input)
        has_payload = bool(payload) or pd.source_context.source_payload_type == "workspace_payload"
        active_modules = _resolve_active_commercial_modules(pd, payload)
        rules = RULES_BY_TEMPLATE[template_code]

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

        for rule in rules:
            if not _rule_applies(rule, active_modules, payload):
                continue
            line = _build_line(rule, payload)
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

        missing_geometry = _missing_critical_geometry(payload, active_modules) if has_payload else []
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

        forbidden_hourly = scan_forbidden_hourly_usage(lines)
        status, quote_ready, confidence = _compute_status(
            lines=lines,
            blockers=blockers,
            owner_decisions=owner_decisions,
            forbidden_hourly=forbidden_hourly,
            missing_geometry=missing_geometry,
            has_payload=has_payload,
        )

        subtotals = [line.subtotal for line in lines if line.subtotal is not None]
        subtotal_commercial = round(sum(subtotals), 4) if subtotals else None

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
        if quote_input:
            provenance.append(
                CommercialProvenanceEntry(
                    key="quote_input",
                    source="request_body",
                    detail="read_only_normalization_no_pricing_engine",
                )
            )

        notes = [
            "Read-only CommercialPriceProposal preview — Step 7G.",
            "Does not call /price, CostEngine, QuoteOrchestrator, or workcenter_rates.",
            "Numeric RON totals deferred until owner commercial price registry (Step 7I).",
        ]

        return CommercialPriceProposalPreview(
            template_code=template_code,
            source=COMMERCIAL_PRICE_PROPOSAL_SOURCE,
            status=status,
            commercial_price_lines=lines,
            subtotal_commercial=subtotal_commercial,
            commercial_total=subtotal_commercial,
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
            },
        )