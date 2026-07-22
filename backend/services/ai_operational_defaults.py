"""Resolve and apply AI operational defaults to template pricing read model."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

from data.ai_operational_defaults_v1 import (
    AI_ACM_PANEL_LABOR,
    AI_ELEC_MIN,
    AI_ELEC_PER_PSU,
    AI_LED_PER_MODULE,
    AI_OPERATIONAL_DEFAULTS,
    AiOperationalDefault,
    PACKAGING_RESOLVER_ID,
    SOURCE_PRECEDENCE,
    defaults_for_template,
    resolve_packaging_band,
)

_OVERRIDES_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "ai_operational_defaults_overrides_v1.json"
)


def load_overrides() -> dict[str, float]:
    if not _OVERRIDES_PATH.exists():
        return {}
    try:
        raw = json.loads(_OVERRIDES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    values = raw.get("values") if isinstance(raw, dict) else None
    if not isinstance(values, dict):
        return {}
    out: dict[str, float] = {}
    for k, v in values.items():
        try:
            out[str(k)] = float(v)
        except (TypeError, ValueError):
            continue
    return out


def save_override(decision_id: str, value: float) -> dict[str, float]:
    """Persist a configurable override (no DB migration)."""
    current = load_overrides()
    # Validate against known defaults
    known = {d.decision_id: d for d in AI_OPERATIONAL_DEFAULTS}
    if decision_id not in known and decision_id != PACKAGING_RESOLVER_ID:
        raise ValueError(f"Unknown decision_id: {decision_id}")
    if decision_id == PACKAGING_RESOLVER_ID:
        # Band resolver is computed — allow override of medium as proxy primary
        decision_id = "AI_PACK_MEDIUM"
    spec = known[decision_id]
    v = float(value)
    if v < spec.minimum:
        raise ValueError(f"Value below minimum {spec.minimum}")
    if spec.maximum is not None and v > spec.maximum:
        raise ValueError(f"Value above maximum {spec.maximum}")
    current[decision_id] = v
    payload = {
        "schema_version": "1.0.0",
        "values": current,
        "note": "AI operational default overrides — does not write catalog rates.",
    }
    _OVERRIDES_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return current


def disable_override(decision_id: str) -> dict[str, float]:
    current = load_overrides()
    current.pop(decision_id, None)
    if decision_id == PACKAGING_RESOLVER_ID:
        current.pop("AI_PACK_MEDIUM", None)
    payload = {"schema_version": "1.0.0", "values": current}
    _OVERRIDES_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return current


def _effective_value(spec: AiOperationalDefault, overrides: dict[str, float]) -> float:
    return float(overrides.get(spec.decision_id, spec.default_value))


def _decision_row(
    *,
    spec: AiOperationalDefault,
    resolved_value: float,
    overrides: dict[str, float],
    template_code: str,
    resolved_from: str,
    readiness_effect: str,
    formula_display: Optional[str] = None,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    overridden = spec.decision_id in overrides
    row = {
        "decision_id": spec.decision_id,
        "domain": spec.domain,
        "target_type": spec.target_type,
        "target_code": spec.target_code,
        "display_name_ro": spec.display_name_ro,
        "formula": formula_display or spec.formula,
        "unit": spec.unit,
        "default_value": spec.default_value,
        "resolved_value": resolved_value,
        "minimum": spec.minimum,
        "maximum": spec.maximum,
        "currency": spec.currency,
        "quantity_key": spec.quantity_key,
        "confidence": spec.confidence,
        "rationale_ro": spec.rationale_ro,
        "decision_source": "AI_DECISION",
        "resolved_from": resolved_from,
        "configurable": spec.configurable,
        "has_override": overridden,
        "review_trigger": spec.review_trigger,
        "status": "active" if spec.status == "active" else spec.status,
        "readiness_effect": readiness_effect,
        "affected_templates": list(spec.applies_to_templates),
        "template_code": template_code,
        "precedence_order": list(SOURCE_PRECEDENCE),
        "calibration_hooks": list(spec.calibration_hooks),
        "demotes_blockers": list(spec.demotes_blockers),
        "owner_confirmation_required": False,
        "superseded_by": None,
    }
    if extra:
        row.update(extra)
    return row


def build_ai_decisions_for_template(
    template_code: str,
    *,
    overrides: Optional[dict[str, float]] = None,
    face_area_m2: Optional[float] = None,
    illuminated: bool = True,
    psu_count: Optional[int] = None,
) -> list[dict[str, Any]]:
    """Build visible AI decision rows for a template (no catalog writes)."""
    overrides = overrides if overrides is not None else load_overrides()
    code_u = str(template_code or "").strip().upper()
    rows: list[dict[str, Any]] = []
    applicable = defaults_for_template(template_code)
    domains = {d.domain for d in applicable}

    if "packaging" in domains:
        band = resolve_packaging_band(
            face_area_m2=face_area_m2,
            illuminated=illuminated and code_u in {
                "TPL-VOLUMETRIC-LETTERS_V2",
                "TPL-VOLUMETRIC-LOGO_V1",
            },
            overrides=overrides,
        )
        rows.append(
            {
                "decision_id": PACKAGING_RESOLVER_ID,
                "domain": "packaging",
                "target_type": "catalog_code",
                "target_code": "PACKAGING",
                "display_name_ro": f"Ambalare — bandă {band.band}",
                "formula": (
                    f"max(min, band_{band.band.lower()}) "
                    f"+ fragile_addon({band.fragile_addon})"
                ),
                "unit": "EUR/produs",
                "default_value": band.value - band.fragile_addon,
                "resolved_value": band.value,
                "minimum": band.minimum,
                "maximum": 200.0,
                "currency": "EUR",
                "quantity_key": "letter_face_area_m2",
                "confidence": "MEDIUM",
                "rationale_ro": (
                    "Ambalare pe categorie de mărime + supliment fragil dacă iluminat. "
                    "Nu depinde de timp."
                ),
                "decision_source": "AI_DECISION",
                "resolved_from": "AI_DECISION",
                "configurable": True,
                "has_override": any(
                    k.startswith("AI_PACK_") for k in overrides
                ),
                "review_trigger": "observed_packaging_cost_sample_count>=20",
                "status": "active",
                "readiness_effect": "ACTIVE_WITH_AI_DEFAULTS",
                "affected_templates": [
                    d.applies_to_templates[0]
                    for d in applicable
                    if d.domain == "packaging"
                ][:4]
                or [template_code],
                "template_code": template_code,
                "precedence_order": list(SOURCE_PRECEDENCE),
                "calibration_hooks": [
                    "observed_actual_cost",
                    "actual_operation_count",
                    "observed_time",
                    "variance",
                    "sample_count",
                ],
                "demotes_blockers": [
                    "AMBALARE_COMMERCIAL_RULE",
                    "MISSING_OWNER_FORMULA",
                ],
                "owner_confirmation_required": False,
                "superseded_by": None,
                "packaging_band": band.band,
                "fragile_addon": band.fragile_addon,
            }
        )

    if any(d.decision_id == AI_ELEC_MIN.decision_id for d in applicable):
        psu = int(psu_count or 0)
        elec_min = _effective_value(AI_ELEC_MIN, overrides)
        per_psu = _effective_value(AI_ELEC_PER_PSU, overrides)
        resolved = max(AI_ELEC_MIN.minimum, elec_min + per_psu * psu)
        rows.append(
            _decision_row(
                spec=AI_ELEC_MIN,
                resolved_value=resolved,
                overrides=overrides,
                template_code=template_code,
                resolved_from="AI_DECISION",
                readiness_effect="ACTIVE_WITH_AI_DEFAULTS",
                formula_display=(
                    f"max({AI_ELEC_MIN.minimum}, {elec_min} + {per_psu}×{psu} PSU)"
                ),
                extra={"psu_count": psu, "per_psu_rate": per_psu},
            )
        )
        rows.append(
            _decision_row(
                spec=AI_ELEC_PER_PSU,
                resolved_value=per_psu,
                overrides=overrides,
                template_code=template_code,
                resolved_from="AI_DECISION",
                readiness_effect="ACTIVE_WITH_AI_DEFAULTS",
            )
        )

    if any(d.decision_id == AI_LED_PER_MODULE.decision_id for d in applicable):
        rate = _effective_value(AI_LED_PER_MODULE, overrides)
        rows.append(
            _decision_row(
                spec=AI_LED_PER_MODULE,
                resolved_value=rate,
                overrides=overrides,
                template_code=template_code,
                resolved_from="AI_DECISION",
                readiness_effect="ACTIVE_WITH_AI_DEFAULTS",
            )
        )

    if any(d.decision_id == AI_ACM_PANEL_LABOR.decision_id for d in applicable):
        rate = _effective_value(AI_ACM_PANEL_LABOR, overrides)
        rows.append(
            _decision_row(
                spec=AI_ACM_PANEL_LABOR,
                resolved_value=rate,
                overrides=overrides,
                template_code=template_code,
                resolved_from="AI_DECISION",
                readiness_effect="ACTIVE_WITH_AI_DEFAULTS",
                extra={"also_applies_to_operations": ["MOUNT_ACM_PANEL"]},
            )
        )

    return rows


def apply_ai_defaults_to_labor_recipes(
    *,
    template_code: str,
    labor_recipes: list[dict[str, Any]],
    ai_decisions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Enrich labor recipes with AI defaults; return (recipes, demoted_blocker_codes)."""
    by_target: dict[str, dict[str, Any]] = {}
    for d in ai_decisions:
        target = str(d.get("target_code") or "").upper()
        if not target:
            continue
        # Prefer composite product-level decisions over per-unit fragments
        # when multiple AI rows share a catalog target (e.g. electrical min vs per-PSU).
        existing = by_target.get(target)
        if existing is None:
            by_target[target] = d
            continue
        prefer_ids = {
            "AI_PACK_PRODUCT_BAND",
            "AI_ELEC_MIN_PRODUCT",
            "AI_LED_PER_MODULE",
            "AI_ACM_PANEL_LABOR_M2",
        }
        if str(d.get("decision_id")) in prefer_ids:
            by_target[target] = d
        elif str(existing.get("decision_id")) not in prefer_ids:
            by_target[target] = d

    demoted: list[str] = []
    out: list[dict[str, Any]] = []
    for recipe in labor_recipes:
        r = dict(recipe)
        catalog = str(r.get("catalog_code") or "").upper()
        op = str(r.get("operation_code") or "").upper()
        decision = by_target.get(catalog) or by_target.get(op)
        # ACM fold/mount share panel labor default
        if not decision and op in {"FOLD_CASSETTE", "MOUNT_ACM_PANEL"}:
            decision = by_target.get("FOLD_CASSETTE")

        if not decision:
            out.append(r)
            continue

        # Precedence: catalog value wins over AI when present & active
        catalog_value = r.get("internal_cost_rate")
        catalog_ok = (
            catalog_value is not None
            and r.get("status") in {"active", "warning"}
            and r.get("base_rate_source") == "pricing_registry"
        )
        ai_val = decision.get("resolved_value")
        r["ai_decision_id"] = decision.get("decision_id")
        r["ai_default_value"] = ai_val
        r["ai_confidence"] = decision.get("confidence")
        r["is_configurable"] = True
        r["review_trigger"] = decision.get("review_trigger")

        if catalog_ok:
            r["decision_source"] = "CATALOG"
            r["resolved_from"] = "CATALOG"
            r["rationale_ro"] = (
                "Tarif catalog preferat față de AI (precedență CATALOG > AI_DECISION). "
                "Default AI rămâne vizibil și configurabil pentru calibrare."
            )
            if r.get("formula_status") in {
                "OPERATION_ONLY",
                "MISSING_OWNER_FORMULA",
            }:
                if decision.get("quantity_key") and not r.get("quantity_keys"):
                    r["quantity_keys"] = [str(decision["quantity_key"])]
                r["formula_status"] = "QUANTITY_KEY_CONFIRMED"
                r["formula_status_label_ro"] = "Cantitate preluată din Product Truth"
                r["formula_source"] = (
                    f"ai_operational_default:{decision.get('decision_id')}"
                )
                r["technical_ready"] = True
                demoted.extend(["OPERATION_ONLY", "MISSING_OWNER_FORMULA"])
                demoted.extend(decision.get("demotes_blockers") or [])
            out.append(r)
            continue

        # Apply AI as commercial/operational fallback (no catalog write)
        r["decision_source"] = "AI_DECISION"
        r["resolved_from"] = "AI_DECISION"
        r["rationale_ro"] = decision.get("rationale_ro")
        r["owner_confirmation_required"] = False

        if r.get("internal_cost_rate") is None or r.get("status") == "missing":
            r["internal_cost_rate"] = ai_val
            r["commercial_rate"] = ai_val
            r["commercial_rate_status"] = "available"
            r["currency"] = decision.get("currency") or r.get("currency") or "EUR"
            r["unit"] = decision.get("unit") or r.get("unit")
            r["status"] = "warning"  # AI active — not owner-confirmed
            r["base_rate_source"] = "ai_operational_default"
            if "MISSING_CATALOG_RATE" in (r.get("blockers") or []):
                r["blockers"] = [
                    b for b in r["blockers"] if b != "MISSING_CATALOG_RATE"
                ]
            warnings = list(r.get("warnings") or [])
            warnings.append("AI_DEFAULT_ACTIVE")
            r["warnings"] = warnings
            r["commercial_ready"] = True
            demoted.extend(decision.get("demotes_blockers") or [])

        if r.get("formula_status") in {"OPERATION_ONLY", "MISSING_OWNER_FORMULA"}:
            if decision.get("quantity_key") and not r.get("quantity_keys"):
                r["quantity_keys"] = [str(decision["quantity_key"])]
            r["formula_status"] = "QUANTITY_KEY_CONFIRMED"
            r["formula_status_label_ro"] = "Cantitate preluată din Product Truth"
            r["formula_source"] = f"ai_operational_default:{decision.get('decision_id')}"
            r["technical_ready"] = True
            demoted.extend(["OPERATION_ONLY", "MISSING_OWNER_FORMULA"])

        out.append(r)

    # Deduplicate demoted codes
    return out, sorted(set(str(x) for x in demoted if x))


def compute_activation_status(
    *,
    technical_ready: bool,
    commercial_ready: bool,
    has_ai_decisions: bool,
    ai_covers_gaps: bool,
    has_real_blockers: bool,
    has_warnings: bool,
) -> str:
    # Real blockers (e.g. ACM treatments) never disappear behind AI activation.
    if has_real_blockers:
        if has_ai_decisions and technical_ready:
            return "ACTIVE_WITH_WARNINGS"
        return "BLOCKED"
    if commercial_ready and not has_ai_decisions:
        return "ACTIVE_WITH_CONFIRMED_TRUTH"
    if has_ai_decisions and (commercial_ready or ai_covers_gaps) and technical_ready:
        return "ACTIVE_WITH_AI_DEFAULTS"
    if technical_ready and has_warnings:
        return "ACTIVE_WITH_WARNINGS"
    if technical_ready:
        return "ACTIVE_WITH_WARNINGS"
    return "BLOCKED"


def demote_recipe_blockers(
    recipe_items: list[Any],
    demoted_codes: list[str],
) -> list[str]:
    """Return blocker codes that were demoted on commercial lines (for reporting)."""
    demoted_found: list[str] = []
    code_set = set(demoted_codes)
    for item in recipe_items:
        blockers = list(getattr(item, "blockers", None) or [])
        if not blockers:
            continue
        new_blockers = []
        for b in blockers:
            if b in code_set or (
                "AMBALARE" in b and "AMBALARE_COMMERCIAL_RULE" in code_set
            ):
                demoted_found.append(b)
                # move to warnings
                warnings = list(getattr(item, "warnings", None) or [])
                warnings.append(f"AI_DEFAULT_DEMOTES:{b}")
                try:
                    item.warnings = warnings
                    item.status = "warning" if item.status == "blocked" else item.status
                    item.commercial_ready = True
                    item.blockers = [x for x in blockers if x != b]
                except Exception:
                    new_blockers.append(b)
            else:
                new_blockers.append(b)
        if hasattr(item, "blockers"):
            try:
                item.blockers = [
                    x for x in (getattr(item, "blockers", None) or []) if x not in code_set
                ]
            except Exception:
                pass
    return sorted(set(demoted_found))
