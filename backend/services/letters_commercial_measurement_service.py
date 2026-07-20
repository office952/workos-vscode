"""Build Letters commercial measurements from ProductDefinition / workspace facts.

Non-monetary. Mirrors quantity_paths of commercial_rules_volumetric_v2 for
TPL-VOLUMETRIC-LETTERS_v2 so CPP 7G can consume Aggregate as measurement SoT.
"""

from __future__ import annotations

from typing import Any, Mapping

from data.commercial_rules_volumetric_v2 import (
    PILOT_TEMPLATE,
    RULES_BY_TEMPLATE,
    CommercialRuleDefinition,
)
from schemas.commercial_measurement_contract import (
    COMMERCIAL_MEASUREMENT_CONTRACT_VERSION,
    CommercialMeasurement,
    CommercialMeasurementBundle,
)
from schemas.product_definition import ProductDefinitionPreview
from services.active_template_scope import normalize_template_code

_LETTERS = frozenset({"TPL-VOLUMETRIC-LETTERS", "TPL-VOLUMETRIC-LETTERS_V2"})


def is_letters_commercial_measurement_template(template_code: str | None) -> bool:
    return normalize_template_code(template_code) in _LETTERS


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


def collect_measurement_facts(
    *,
    pd: ProductDefinitionPreview | None,
    quote_input: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Merge PD geometry/canonical + quote_input into a flat-ish fact map."""
    out: dict[str, Any] = {}
    if isinstance(quote_input, dict):
        out.update(dict(quote_input))
        finish = quote_input.get("finish_setup")
        if isinstance(finish, dict):
            out.setdefault("finish_setup", dict(finish))
            for key, value in finish.items():
                out.setdefault(key, value)
        geom = quote_input.get("quote_geometry")
        if isinstance(geom, dict):
            out.setdefault("quote_geometry", dict(geom))
            for key, value in geom.items():
                out.setdefault(key, value)
    if pd is not None:
        if isinstance(pd.geometry_inputs, dict):
            geom = out.setdefault("quote_geometry", {})
            if isinstance(geom, dict):
                for key, value in pd.geometry_inputs.items():
                    if value is not None and geom.get(key) in (None, "", [], {}):
                        geom[key] = value
                    out.setdefault(key, value)
        if isinstance(pd.canonical_values, dict):
            for key, value in pd.canonical_values.items():
                if value is not None:
                    out.setdefault(key, value)
    return out


def _extract_quantity(facts: Mapping[str, Any], paths: tuple[str, ...]) -> float | None:
    for path in paths:
        value = _get_by_path(facts, path)
        if value is None and "." not in path:
            value = facts.get(path)
        number = _positive_number(value)
        if number is not None:
            return float(number) if not number.is_integer() else float(int(number))
    return None


def _source_keys(paths: tuple[str, ...]) -> list[str]:
    keys: list[str] = []
    for path in paths:
        key = path.split(".")[-1] if path else ""
        if key and key not in keys:
            keys.append(key)
    return keys


def build_letters_commercial_measurements(
    *,
    template_code: str,
    pd: ProductDefinitionPreview | None,
    quote_input: Mapping[str, Any] | None,
    active_modules: set[str] | None = None,
) -> CommercialMeasurementBundle | None:
    if not is_letters_commercial_measurement_template(template_code):
        return None

    rules = RULES_BY_TEMPLATE.get(PILOT_TEMPLATE) or ()
    facts = collect_measurement_facts(pd=pd, quote_input=quote_input)
    # Sole V6 commercial quantity resolver — prefer instance authority over raw bags.
    from services.letter_group_instance_authority import build_volumetric_letters_commercial_quantities

    finish = facts.get("finish_setup") if isinstance(facts.get("finish_setup"), dict) else {}
    if not finish and isinstance(quote_input, dict):
        finish = quote_input.get("finish_setup") if isinstance(quote_input.get("finish_setup"), dict) else {}
    geom = facts.get("quote_geometry") if isinstance(facts.get("quote_geometry"), dict) else {}
    qty = build_volumetric_letters_commercial_quantities(quote_geometry=geom, finish_setup=finish)
    if qty.get("letter_face_area_m2") is not None:
        facts["letter_face_area_m2"] = qty["letter_face_area_m2"]
        facts.setdefault("face_area_m2", qty["letter_face_area_m2"])
        if isinstance(facts.get("quote_geometry"), dict):
            facts["quote_geometry"]["letter_face_area_m2"] = qty["letter_face_area_m2"]
    if qty.get("letter_perimeter_m") is not None:
        facts["letter_perimeter_m"] = qty["letter_perimeter_m"]
        if isinstance(facts.get("quote_geometry"), dict):
            facts["quote_geometry"]["letter_perimeter_m"] = qty["letter_perimeter_m"]
    if qty.get("led_module_count") is not None:
        facts["letter_led_module_count"] = qty["led_module_count"]
        facts["led_module_count"] = qty["led_module_count"]
    facts["volumetric_letters_commercial_quantities"] = qty

    modules = active_modules or set()
    measurements: list[CommercialMeasurement] = []
    diagnostics: list[str] = []

    for rule in rules:
        if not isinstance(rule, CommercialRuleDefinition):
            continue
        gate = rule.module_gate or rule.module_code
        if modules and gate and gate not in modules:
            measurements.append(
                CommercialMeasurement(
                    measurement_key=f"cm.{rule.line_code}",
                    line_code=rule.line_code,
                    quantity=None,
                    unit=rule.unit,
                    module_code=rule.module_code,
                    component_code=rule.component_code,
                    source_fact_keys=_source_keys(rule.quantity_paths),
                    resolution_status="not_applicable",
                    pricing_rule_code=rule.pricing_rule_code,
                    selector={
                        "module_gate": gate,
                        "material_gate_path": rule.material_gate_path,
                        "material_gate_value": rule.material_gate_value,
                    },
                    notes=["module_gate inactive"],
                )
            )
            continue

        if rule.material_gate_path and rule.material_gate_value:
            raw = _get_by_path(facts, rule.material_gate_path)
            if raw is None:
                alt = rule.material_gate_path.split(".")[-1]
                raw = _get_by_path(facts, f"finish_setup.{alt}") or facts.get(alt)
            if str(raw or "").strip() != rule.material_gate_value:
                measurements.append(
                    CommercialMeasurement(
                        measurement_key=f"cm.{rule.line_code}",
                        line_code=rule.line_code,
                        quantity=None,
                        unit=rule.unit,
                        module_code=rule.module_code,
                        component_code=rule.component_code,
                        source_fact_keys=_source_keys(rule.quantity_paths),
                        resolution_status="not_applicable",
                        pricing_rule_code=rule.pricing_rule_code,
                        selector={
                            "material_gate_path": rule.material_gate_path,
                            "material_gate_value": rule.material_gate_value,
                        },
                        notes=["material_gate mismatch"],
                    )
                )
                continue

        if rule.quantity_paths:
            qty = _extract_quantity(facts, rule.quantity_paths)
            status = "resolved" if qty is not None else "missing_input"
            if qty is None:
                diagnostics.append(f"missing_qty:{rule.line_code}")
        else:
            # Fixed / piece-without-path lines (PSU, packaging, site install):
            # emit quantity=1 when module applicable; CPP retains monetary rules.
            qty = 1.0 if rule.basis_type in {"fixed", "piece", "unknown"} or rule.always_include else None
            if rule.owner_decision_required and rule.line_code == "ambalare":
                qty = None
                status = "pending_owner"
            else:
                status = "resolved" if qty is not None else "missing_input"

        measurements.append(
            CommercialMeasurement(
                measurement_key=f"cm.{rule.line_code}",
                line_code=rule.line_code,
                quantity=qty,
                unit=rule.unit,
                module_code=rule.module_code,
                component_code=rule.component_code,
                source_fact_keys=_source_keys(rule.quantity_paths),
                resolution_status=status,  # type: ignore[arg-type]
                pricing_rule_code=rule.pricing_rule_code,
                selector={
                    "basis_type": rule.basis_type,
                    "registry_pricing_code": rule.registry_pricing_code,
                },
            )
        )

    return CommercialMeasurementBundle(
        contract_version=COMMERCIAL_MEASUREMENT_CONTRACT_VERSION,
        template_code="TPL-VOLUMETRIC-LETTERS_v2",
        measurements=measurements,
        diagnostics=diagnostics,
    )


def measurement_quantity_by_line_code(
    bundle: CommercialMeasurementBundle | None,
    line_code: str,
) -> tuple[float | None, str | None]:
    """Return (quantity, source_tag) when measurement is resolved."""
    if bundle is None:
        return None, None
    for item in bundle.measurements:
        if item.line_code != line_code:
            continue
        if item.resolution_status != "resolved" or item.quantity is None:
            return None, f"measurement_unresolved:{item.resolution_status}"
        return float(item.quantity), item.provenance
    return None, None
