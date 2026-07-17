"""Propagate workspace offer_scope into Intake V6 live calculation quote_input paths."""

from __future__ import annotations

from typing import Any

from schemas.intake_v4 import (
    IntakeV4CncOperationRow,
    IntakeV4EdgeCantOperationRow,
    IntakeV4MaterialBreakdownResponse,
    IntakeV4MaterialBreakdownTotals,
    IntakeV4MaterialBreakdownWarning,
    IntakeV4MaterialQuantityRow,
)
from services.offer_scope_led_subscope_service import (
    LedSubscope,
    commercial_line_led_subscope,
    led_consumer_row_allowed,
    logical_list_line_led_subscope,
    material_led_subscope,
    operation_led_subscope,
    resolve_sold_led_subscopes,
)
from services.lighting_mount_consumer_service import resolve_lighting_mount_consumers
from services.mounting_scope_service import is_mounting_preparation_active
from services.active_scope_resolver_service import compile_active_scope
from services.offer_scope_resolver_service import (
    _apply_conditional_gates,
    extract_offer_scope,
    resolve_offer_scope,
)


def coerce_payload_raw(payload: Any, payload_raw: dict[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(payload_raw, dict):
        return payload_raw
    if isinstance(payload, dict):
        return payload
    if hasattr(payload, "model_dump"):
        dumped = payload.model_dump(mode="json")
        return dumped if isinstance(dumped, dict) else {}
    return {}


def merge_workspace_offer_scope_into_quote_input(
    payload_raw: dict[str, Any],
    quote_input: dict[str, Any] | None,
) -> dict[str, Any]:
    """Attach persisted workspace offer_scope to quote_input when present."""
    merged = dict(quote_input or {})
    scope = payload_raw.get("offer_scope")
    if isinstance(scope, dict) and scope.get("contract_version"):
        merged["offer_scope"] = dict(scope)
    return merged


def resolve_live_calc_scope(
    payload_raw: dict[str, Any],
    quote_input: dict[str, Any] | None = None,
) -> tuple[bool, set[str]]:
    """Return (use_legacy_full_product, active_runtime_module_codes)."""
    scope = extract_offer_scope(payload_raw, quote_input)
    resolved = resolve_offer_scope(scope)
    if resolved.use_legacy:
        return True, set()
    if resolved.validation_errors:
        return False, set()
    active = _apply_conditional_gates(
        resolved.runtime_sold_modules,
        payload=payload_raw,
        quote_input=quote_input,
    )
    return False, active


def resolve_composition_excluded_materials(
    payload_raw: dict[str, Any],
    quote_input: dict[str, Any] | None = None,
) -> frozenset[str]:
    """FACE+CANT interface materials silenced when interface is inactive."""
    compiled = compile_active_scope(
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        payload=payload_raw,
        quote_input=quote_input,
    )
    if compiled.use_legacy_full_product or compiled.errors:
        return frozenset()
    return frozenset(
        str(code).strip().lower()
        for code in (compiled.composition_excluded_materials or [])
        if str(code).strip()
    )


def _merged_mounting_context(
    payload_raw: dict[str, Any],
    quote_input: dict[str, Any] | None,
) -> dict[str, Any]:
    ctx: dict[str, Any] = {}
    finish = payload_raw.get("finish_setup")
    if isinstance(finish, dict):
        ctx.update(finish)
    if isinstance(quote_input, dict):
        for key in ("mounting_scope", "site_installation_included", "mounting_template_enabled"):
            if quote_input.get(key) is not None:
                ctx[key] = quote_input.get(key)
    return ctx


def _is_mounting_prep_material_key(material_key: str) -> bool:
    key = str(material_key or "").strip().lower()
    if key == "mounting_accessories_percent":
        return True
    if "sablon" in key or key.startswith("mounting_template"):
        return True
    if key.startswith("premount_bar") or "premount" in key:
        return True
    return False


def _is_mounting_prep_operation_row(row: IntakeV4CncOperationRow | IntakeV4EdgeCantOperationRow) -> bool:
    if isinstance(row, IntakeV4EdgeCantOperationRow):
        return False
    for candidate in (
        getattr(row, "dossier_operation_key", None),
        getattr(row, "tpl_operation_key", None),
        getattr(row, "key", None),
    ):
        code = str(candidate or "").strip().lower()
        if "mounting_template" in code or code.startswith("sablon_montaj"):
            return True
    return False


def runtime_module_for_material_key(material_key: str) -> str | None:
    key = str(material_key or "").strip().lower()
    if not key:
        return None
    if key in {"plexiglas_face"}:
        return "debitare_fata"
    if key.startswith("face_vinyl_") or key.startswith("face_oracal"):
        return "debitare_fata"
    if key.startswith("artwork_plexiglas"):
        return "debitare_fata"
    if key in {"forex_backing"} or key.startswith("artwork_forex_backing"):
        return "debitare_spate"
    if key in {"return_material", "ral_paint_spray"}:
        return "modelare_cant"
    if key.startswith("led_") or key.startswith("wire_") or key in {"adhesive_led_modules"}:
        return "sistem_led"
    if key in {"adhesive_return_to_face"}:
        return "modelare_cant"
    if key in {
        "print_vinyl",
        "laminated_vinyl",
        "mounting_accessories_percent",
    } or key.startswith("artwork_") and (
        "print" in key or "laminated" in key or "vinyl" in key
    ):
        return "finisaje"
    if key.startswith("nesting_roll_") or key.startswith("nesting_sheet_"):
        return "finisaje"
    return None


def runtime_module_for_operation_row(row: IntakeV4CncOperationRow | IntakeV4EdgeCantOperationRow) -> str | None:
    if isinstance(row, IntakeV4EdgeCantOperationRow):
        return "modelare_cant"
    key = str(getattr(row, "key", "") or "").strip().lower()
    tpl = str(getattr(row, "tpl_operation_key", "") or "").strip().lower()
    dossier = str(getattr(row, "dossier_operation_key", "") or "").strip().lower()
    op_code = dossier or tpl or key
    if operation_led_subscope(op_code) is not None:
        return "sistem_led"
    if key.startswith("cnc_face") or tpl.startswith("cnc_face"):
        return "debitare_fata"
    if key.startswith("cnc_back") or tpl.startswith("cnc_back"):
        return "debitare_spate"
    if key in {"print_service", "lamination_service", "application_service"} or tpl in {
        "print_solvent",
        "lamination",
        "apply_vinyl",
    }:
        return "finisaje"
    if "cant" in key or "edge" in key:
        return "modelare_cant"
    return None


def _operation_led_subscope_for_row(row: IntakeV4CncOperationRow | IntakeV4EdgeCantOperationRow) -> str | None:
    if isinstance(row, IntakeV4EdgeCantOperationRow):
        return None
    for candidate in (
        getattr(row, "dossier_operation_key", None),
        getattr(row, "tpl_operation_key", None),
        getattr(row, "key", None),
    ):
        sub = operation_led_subscope(str(candidate or ""))
        if sub:
            return sub
    return None


def _row_allowed(
    *,
    runtime_module: str | None,
    use_legacy: bool,
    active_modules: set[str],
    sold_led_subscopes: frozenset[LedSubscope] | None = None,
    mount_decision: Any | None = None,
    material_key: str | None = None,
    operation_subscope: LedSubscope | None = None,
    operation_code: str | None = None,
    line_id: str | None = None,
    commercial_line_code: str | None = None,
) -> bool:
    if use_legacy:
        return True
    if runtime_module is None:
        return False
    if runtime_module not in active_modules:
        return False
    if runtime_module != "sistem_led" or sold_led_subscopes is None:
        return True
    row_subscope = None
    if material_key is not None:
        row_subscope = material_led_subscope(material_key)
    elif operation_subscope is not None:
        row_subscope = operation_subscope
    elif line_id is not None:
        row_subscope = logical_list_line_led_subscope(line_id)
    return led_consumer_row_allowed(
        row_subscope=row_subscope,
        sold_led_subscopes=sold_led_subscopes,
        material_key=material_key,
        operation_code=operation_code,
        line_id=line_id,
        commercial_line_code=commercial_line_code,
        mount_decision=mount_decision,
    )


def _material_cost(row: IntakeV4MaterialQuantityRow) -> float:
    if row.estimated_cost is not None:
        return float(row.estimated_cost)
    if row.material_cost is not None:
        return float(row.material_cost)
    return 0.0


def _operation_cost(row: IntakeV4CncOperationRow | IntakeV4EdgeCantOperationRow) -> float:
    if row.estimated_cost is not None:
        return float(row.estimated_cost)
    return 0.0


def _is_price_missing_material(row: IntakeV4MaterialQuantityRow) -> bool:
    # Informational-only rows (e.g. led_total_watts) are not priced tariffs.
    price_source = str(getattr(row, "price_source", "") or "").strip().lower()
    if price_source in {"informational_only", "informational", "info_only"}:
        return False
    if row.quantity and row.quantity > 0 and row.estimated_cost is None and row.material_cost is None:
        return True
    return False


def _is_price_missing_operation(row: IntakeV4CncOperationRow | IntakeV4EdgeCantOperationRow) -> bool:
    if row.quantity and row.quantity > 0 and row.estimated_cost is None:
        return True
    return False


def filter_material_breakdown_by_offer_scope(
    breakdown: IntakeV4MaterialBreakdownResponse,
    *,
    payload_raw: dict[str, Any],
    quote_input: dict[str, Any] | None = None,
) -> IntakeV4MaterialBreakdownResponse:
    use_legacy, active_modules = resolve_live_calc_scope(payload_raw, quote_input)
    excluded_materials = resolve_composition_excluded_materials(payload_raw, quote_input)
    mounting_ctx = _merged_mounting_context(payload_raw, quote_input)
    mounting_prep_active = is_mounting_preparation_active(mounting_ctx)

    sold_led_subscopes = resolve_sold_led_subscopes(payload_raw, quote_input)
    mount_decision = resolve_lighting_mount_consumers(payload_raw, quote_input)

    def _material_allowed(row: IntakeV4MaterialQuantityRow) -> bool:
        key = str(row.material_key or "").strip().lower()
        mat_code = str(getattr(row, "material_code", None) or "").strip().lower()
        if key in excluded_materials or mat_code in excluded_materials:
            return False
        if not mounting_prep_active and _is_mounting_prep_material_key(row.material_key):
            return False
        return _row_allowed(
            runtime_module=runtime_module_for_material_key(row.material_key),
            use_legacy=use_legacy,
            active_modules=active_modules,
            sold_led_subscopes=sold_led_subscopes,
            mount_decision=mount_decision,
            material_key=row.material_key,
        )

    def _operation_allowed(row: IntakeV4CncOperationRow | IntakeV4EdgeCantOperationRow) -> bool:
        if not mounting_prep_active and _is_mounting_prep_operation_row(row):
            return False
        op_code = str(
            getattr(row, "dossier_operation_key", None)
            or getattr(row, "tpl_operation_key", None)
            or getattr(row, "key", None)
            or ""
        )
        # FACE+CANT interface ops — silence when adhesive/bonding interface inactive.
        if not use_legacy and excluded_materials:
            lowered = op_code.lower()
            if "bonding" in lowered or "return_face_bonding" in lowered:
                return False
        return _row_allowed(
            runtime_module=runtime_module_for_operation_row(row),
            use_legacy=use_legacy,
            active_modules=active_modules,
            sold_led_subscopes=sold_led_subscopes,
            mount_decision=mount_decision,
            operation_subscope=_operation_led_subscope_for_row(row),
            operation_code=op_code,
        )

    material_rows = [row for row in breakdown.material_rows if _material_allowed(row)]
    consumable_rows = [row for row in breakdown.consumable_rows if _material_allowed(row)]
    operation_rows = [row for row in breakdown.operation_rows if _operation_allowed(row)]
    edge_cant_operation_rows = [
        row
        for row in breakdown.edge_cant_operation_rows
        if _row_allowed(
            runtime_module="modelare_cant",
            use_legacy=use_legacy,
            active_modules=active_modules,
            sold_led_subscopes=sold_led_subscopes,
        )
    ]

    total = 0.0
    contains_missing_prices = False
    for row in material_rows + consumable_rows:
        if _is_price_missing_material(row):
            contains_missing_prices = True
        total += _material_cost(row)
    for row in operation_rows + edge_cant_operation_rows:
        if _is_price_missing_operation(row):
            contains_missing_prices = True
        total += _operation_cost(row)

    warnings = list(breakdown.warnings)
    if not use_legacy:
        warnings.append(
            IntakeV4MaterialBreakdownWarning(
                code="offer_scope_material_breakdown_filtered",
                message="Material breakdown filtered by workspace offer_scope sold modules.",
                source="intake_v6_offer_scope_live_calc",
                severity="info",
            )
        )

    cost_total = round(total, 2)
    return breakdown.model_copy(
        update={
            "material_rows": material_rows,
            "consumable_rows": consumable_rows,
            "operation_rows": operation_rows,
            "edge_cant_operation_rows": edge_cant_operation_rows,
            "warnings": warnings,
            "totals": IntakeV4MaterialBreakdownTotals(
                material_cost_total=cost_total,
                estimated_cost_total=cost_total,
                currency=breakdown.totals.currency,
                contains_estimates=breakdown.totals.contains_estimates,
                contains_missing_prices=contains_missing_prices,
            ),
        }
    )


def filter_logical_list_rows_by_offer_scope(
    rows: list[dict[str, Any]],
    *,
    payload_raw: dict[str, Any],
    quote_input: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    use_legacy, active_modules = resolve_live_calc_scope(payload_raw, quote_input)
    if use_legacy:
        return rows
    sold_led_subscopes = resolve_sold_led_subscopes(payload_raw, quote_input)
    mount_decision = resolve_lighting_mount_consumers(payload_raw, quote_input)
    filtered: list[dict[str, Any]] = []
    for row in rows:
        module_code = row.get("module_code")
        if not isinstance(module_code, str) or module_code not in active_modules:
            continue
        if not _row_allowed(
            runtime_module=module_code,
            use_legacy=use_legacy,
            active_modules=active_modules,
            sold_led_subscopes=sold_led_subscopes,
            mount_decision=mount_decision,
            line_id=str(row.get("line_id") or ""),
        ):
            continue
        filtered.append(row)
    return filtered


def filter_commercial_line_items_by_offer_scope(
    line_items: list[dict[str, Any]],
    *,
    payload_raw: dict[str, Any],
    quote_input: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    use_legacy, active_modules = resolve_live_calc_scope(payload_raw, quote_input)
    if use_legacy:
        return line_items
    sold_led_subscopes = resolve_sold_led_subscopes(payload_raw, quote_input)
    mount_decision = resolve_lighting_mount_consumers(payload_raw, quote_input)
    filtered: list[dict[str, Any]] = []
    for line in line_items:
        module_code = line.get("module_code")
        if not isinstance(module_code, str) or module_code not in active_modules:
            continue
        if module_code == "sistem_led" and sold_led_subscopes is not None:
            sub = commercial_line_led_subscope(str(line.get("code") or ""))
            if not led_consumer_row_allowed(
                row_subscope=sub,
                sold_led_subscopes=sold_led_subscopes,
                commercial_line_code=str(line.get("code") or ""),
                mount_decision=mount_decision,
            ):
                continue
        filtered.append(line)
    return filtered
