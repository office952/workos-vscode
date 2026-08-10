"""WORKOS Intake V6 exhaustive price-input audit V1 — read-only CPP OFAT.

Owner GO: AUTHORIZE_WORKOS_INTAKE_V6_EXHAUSTIVE_PRICE_INPUT_AUDIT_V1

- No quote/order writes, no pricing/product-truth mutations, no push.
- Dependency-aware one-factor-at-a-time against frozen baseline variants.
- Authority: POST commercial-price-preview (EUR). Optional dry-run if workspace id set.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
EVIDENCE = ROOT / "docs" / "qa" / "workos-intake-v6-exhaustive-price-input-audit-v1"
BASELINES = EVIDENCE / "baselines"
CAPTURES = EVIDENCE / "captures"
GOLDEN = BACKEND / "tests" / "fixtures" / "intake_v6_golden_gradi"

BASE_URL = os.environ.get("WORKOS_AUDIT_BASE_URL", "http://127.0.0.1:8000").rstrip("/")
PREVIEW = f"{BASE_URL}/api/v1/product-system/commercial-price-preview"
HEADERS = {
    "Authorization": "Bearer __DEV_BYPASS_TOKEN__",
    "Content-Type": "application/json",
}
TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"
CURRENCY = "EUR"


def _sha(obj: Any) -> str:
    raw = json.dumps(obj, sort_keys=True, ensure_ascii=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _preview_body(quote_input: dict) -> dict:
    return {"template_code": TEMPLATE, "quote_input": quote_input, "currency": CURRENCY}


def call_preview(quote_input: dict) -> dict:
    resp = requests.post(
        f"{PREVIEW}/{TEMPLATE}",
        headers=HEADERS,
        data=json.dumps(_preview_body(quote_input)),
        timeout=90,
    )
    try:
        data = resp.json()
    except Exception:
        data = {"raw": resp.text}
    if resp.status_code >= 400:
        return {
            "_http_status": resp.status_code,
            "_error": True,
            "preview": data if isinstance(data, dict) else {"raw": data},
        }
    if isinstance(data, dict) and "preview" in data:
        data["_http_status"] = resp.status_code
        return data
    return {"_http_status": resp.status_code, "preview": data if isinstance(data, dict) else {}}


def unwrap(resp: dict) -> dict:
    prev = resp.get("preview")
    return prev if isinstance(prev, dict) else {}


def line_map(preview: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for line in preview.get("commercial_price_lines") or []:
        code = str(line.get("code") or "")
        if not code:
            continue
        out[code] = line
    return out


def money(preview: dict) -> tuple[float | None, str | None]:
    total = preview.get("subtotal_commercial")
    if total is None:
        total = preview.get("commercial_total")
    curr = preview.get("currency")
    bd = preview.get("commercial_product_breakdown") or {}
    if isinstance(bd, dict):
        if bd.get("complete_offer_total") is not None and total is None:
            total = bd.get("complete_offer_total")
        if bd.get("complete_offer_total_currency"):
            curr = bd.get("complete_offer_total_currency") or curr
        if total is None:
            for bucket in bd.get("subtotals_by_currency") or []:
                if isinstance(bucket, dict) and str(bucket.get("currency") or "").upper() == "EUR":
                    total = bucket.get("subtotal")
                    curr = "EUR"
                    break
    try:
        total_f = float(total) if total is not None else None
    except (TypeError, ValueError):
        total_f = None
    return total_f, curr if isinstance(curr, str) else None


def complete_offer(preview: dict) -> dict:
    bd = preview.get("commercial_product_breakdown") or {}
    if not isinstance(bd, dict):
        bd = {}
    return {
        "complete_offer_total": bd.get("complete_offer_total"),
        "complete_offer_total_currency": bd.get("complete_offer_total_currency"),
        "complete_offer_total_unavailable_reason": bd.get(
            "complete_offer_total_unavailable_reason"
        ),
        "complete_offer_total_is_partial": bd.get("complete_offer_total_is_partial"),
        "subtotals_by_currency": bd.get("subtotals_by_currency"),
    }


def blockers(preview: dict) -> list[dict]:
    out = []
    for b in preview.get("commercial_blockers") or []:
        if isinstance(b, dict):
            out.append({"code": b.get("code"), "message": b.get("message")})
        else:
            out.append({"code": str(b), "message": None})
    return out


def gradi_baseline_quote_input() -> dict:
    """EUR-safe Letters baseline: golden geometry, Oracal 8500@1260, mounting template OFF."""
    payload = json.loads((GOLDEN / "workspace_payload.golden.json").read_text(encoding="utf-8"))
    geom = copy.deepcopy(payload.get("quote_geometry") or {})
    # CPP critical path uses letter_face_area_m2; golden pack historically stores face_area_m2.
    if geom.get("letter_face_area_m2") is None and geom.get("face_area_m2") is not None:
        geom["letter_face_area_m2"] = geom["face_area_m2"]
    if geom.get("letter_perimeter_m") is None and geom.get("total_letter_perimeter_ml") is not None:
        geom["letter_perimeter_m"] = geom["total_letter_perimeter_ml"]
    finish = copy.deepcopy(payload.get("finish_setup") or {})
    # Force EUR-safe commercial hygiene for OFAT (Owner lock: template on causes RON mix historically).
    finish["mounting_template_enabled"] = False
    finish["mounting_scope"] = "none"
    finish["site_installation_included"] = False
    finish["face_finish_type"] = "oracal_8500"
    finish["face_vinyl_roll_width_mm"] = 1260
    finish["face_oracal_code"] = finish.get("face_oracal_code") or "021"
    finish["return_finish_type"] = "white_aluminum"
    finish["return_depth_mm"] = finish.get("return_depth_mm") or 60
    finish["illuminated"] = True
    finish["lighting_system_type"] = finish.get("lighting_system_type") or "led_modules"
    finish["led_module_power_w"] = finish.get("led_module_power_w") or 0.75
    finish["selected_psu_watts"] = finish.get("selected_psu_watts") or 60
    finish["confirmed"] = True
    groups = finish.get("letter_group_finishes") or []
    if not groups:
        groups = [{"group_key": "grp-A"}]
    for g in groups:
        g["face_finish_type"] = "oracal_8500"
        g["face_vinyl_roll_width_mm"] = 1260
        g["face_oracal_code"] = g.get("face_oracal_code") or "021"
        g["return_finish_type"] = "white_aluminum"
        g["confirmed"] = True
    finish["letter_group_finishes"] = groups
    return {
        "quote_geometry": geom,
        "client": payload.get("client") or {"width_mm": 2000, "height_mm": 500},
        "vector_file": "gradi-curat.svg",
        "finish_setup": finish,
        "product_binding": payload.get("product_binding"),
    }


def bond_baseline_quote_input(*, acm_included: bool) -> dict:
    """Remus Letters(+ACM) synthetic geometry baseline."""
    finish: dict[str, Any] = {
        "return_depth_mm": 100,
        "face_finish_type": "oracal_651",
        "face_oracal_code": "021",
        "face_vinyl_roll_width_mm": 1260,
        "return_finish_type": "white_aluminum",
        "backing_mode": "forex_10_no_bevel",
        "illuminated": True,
        "lighting_system_type": "led_modules",
        "led_module_power_w": 0.75,
        "selected_psu_watts": 60,
        "mounting_template_enabled": False,
        "mounting_scope": "none",
        "site_installation_included": False,
        "confirmed": True,
        "letter_group_finishes": [
            {
                "group_key": "grp-A",
                "face_finish_type": "oracal_651",
                "face_oracal_code": "021",
                "face_vinyl_roll_width_mm": 1260,
                "return_finish_type": "white_aluminum",
                "confirmed": True,
            }
        ],
    }
    if acm_included:
        finish["acm_panel_domain_action"] = "upsert"
        finish["applied_content"] = "letters"
        finish["mounting_solution"] = {
            "template_code": "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1",
            "configuration": {
                "acm_panel_instance": {
                    "geometry": {"width_mm": 2000, "height_mm": 500},
                    "configuration": {
                        "fold_count": 2,
                        "acm_thickness_mm": 3,
                        "l1_mm": 60,
                        "l2_mm": 25,
                        "internal_frame_enabled": True,
                    },
                    "sheet_material": {"variant": "standard", "environment": "interior"},
                    "shell_finish": {"apply_after_frame": False},
                    "composition_status": "confirmed",
                    "technical_configuration_status": "confirmed",
                }
            },
        }
        # Mirror common Intake path used by finish-setup upserts.
        finish["acm_panel_instance"] = finish["mounting_solution"]["configuration"][
            "acm_panel_instance"
        ]
    return {
        "quote_geometry": {
            "letter_count": 5,
            "letter_face_area_m2": 0.8,
            "letter_perimeter_m": 6.0,
            "width_mm": 2000,
            "height_mm": 500,
            "depth_mm": 100,
        },
        "client": {"width_mm": 2000, "height_mm": 500},
        "vector_file": "test-bond-litere.svg",
        "finish_setup": finish,
        "applied_content": "letters" if acm_included else None,
        "product_composition_confirmed": (
            {"applied_content": "letters", "status": "confirmed"} if acm_included else None
        ),
        "product_composition": {
            "items": (
                [
                    {"key": "letters", "status": "applied_content"},
                    {"key": "support", "status": "included"},
                ]
                if acm_included
                else [
                    {"key": "letters", "status": "applied_content"},
                    {"key": "support", "status": "available_optional"},
                ]
            )
        },
    }


def set_finish(qi: dict, **kwargs: Any) -> dict:
    out = copy.deepcopy(qi)
    fs = out.setdefault("finish_setup", {})
    for k, v in kwargs.items():
        fs[k] = v
    # Keep letter groups aligned for face/return mutations when present.
    groups = fs.get("letter_group_finishes") or []
    for g in groups:
        for key in (
            "face_finish_type",
            "face_vinyl_roll_width_mm",
            "face_oracal_code",
            "return_finish_type",
            "return_oracal_code",
            "return_depth_mm",
            "backing_mode",
            "confirmed",
        ):
            if key in kwargs:
                g[key] = kwargs[key]
    fs["letter_group_finishes"] = groups
    return out


def set_nested(qi: dict, path: str, value: Any) -> dict:
    out = copy.deepcopy(qi)
    cur: Any = out
    parts = path.split(".")
    for p in parts[:-1]:
        if p not in cur or not isinstance(cur[p], dict):
            cur[p] = {}
        cur = cur[p]
    cur[parts[-1]] = value
    return out


def set_commercial(qi: dict, **kwargs: Any) -> dict:
    out = copy.deepcopy(qi)
    ci = out.setdefault("commercial_inputs", {})
    ci.update(kwargs)
    # Also mirror on finish_setup if some paths expect it.
    fs = out.setdefault("finish_setup", {})
    fs.setdefault("commercial_inputs", {}).update(kwargs)
    return out


def classify(
    *,
    expected: str,
    base_prev: dict,
    new_prev: dict,
    http_error: bool,
) -> tuple[str, bool, str, str]:
    """Return OBSERVED_CLASS, DEFECT, RATIONALE, FIRST_BROKEN_BOUNDARY."""
    if http_error:
        return "ERROR", True, "HTTP/preview error on valid probe", "PRICING_AUTHORITY"

    co = complete_offer(new_prev)
    bl = blockers(new_prev)
    codes = {str(b.get("code") or "") for b in bl}
    reason = str(co.get("complete_offer_total_unavailable_reason") or "")

    if any("CURRENCY_MIX" in c or "CURRENCY" in c for c in codes) or "CURRENCY" in reason:
        defect = expected == "YES"
        return (
            "CURRENCY_MIX",
            True,
            f"currency mix/unavailable: {reason or sorted(codes)}",
            "CURRENCY_COMPOSITION",
        )

    if any("MISSING" in c or "RULE" in c or "UNPUBLISHED" in c for c in codes) or "MISSING" in reason:
        return (
            "MISSING_RULE",
            expected == "YES",
            f"missing/unpublished rule: {sorted(codes) or reason}",
            "CPP_RULE_SELECTION",
        )

    if bl and co.get("complete_offer_total") is None and money(new_prev)[0] is None:
        # hard block
        return (
            "BLOCKER",
            expected == "YES",
            f"blocked: {sorted(codes)}",
            "CPP_RULE_SELECTION",
        )

    base_lines = line_map(base_prev)
    new_lines = line_map(new_prev)
    base_total, _ = money(base_prev)
    new_total, _ = money(new_prev)

    added = [c for c in new_lines if c not in base_lines]
    removed = [c for c in base_lines if c not in new_lines]
    changed = []
    for c, line in new_lines.items():
        if c not in base_lines:
            continue
        try:
            a = float(base_lines[c].get("subtotal") or 0)
            b = float(line.get("subtotal") or 0)
        except (TypeError, ValueError):
            continue
        if abs(a - b) > 1e-6:
            changed.append(c)

    total_delta = None
    if base_total is not None and new_total is not None:
        total_delta = round(new_total - base_total, 4)

    priced = bool(added or removed or changed or (total_delta is not None and abs(total_delta) > 1e-6))

    if priced:
        # complete offer may still be broken
        if co.get("complete_offer_total") is None and (co.get("complete_offer_total_unavailable_reason") or bl):
            return (
                "PRICED_LINE",
                True,
                "line pricing changed but complete_offer invalid",
                "TOTAL_COMPOSITION",
            )
        return "PRICED_LINE", False, "attributable commercial delta observed", "NONE"

    # no money/line delta
    if expected == "NO":
        return "ZERO_DELTA_INTENTIONAL", False, "no commercial effect expected", "NONE"
    if expected == "UNKNOWN":
        return "NO_EFFECT", False, "no delta; expectation unknown — not auto-defect", "NONE"
    # expected YES
    if bl:
        return "BLOCKER", True, f"expected price; blocked {sorted(codes)}", "CPP_RULE_SELECTION"
    return "NO_EFFECT", True, "expected commercial effect but no line/total delta", "CPP_RULE_SELECTION"


def attribution(base_prev: dict, new_prev: dict) -> dict:
    base_lines = line_map(base_prev)
    new_lines = line_map(new_prev)
    base_total, curr = money(base_prev)
    new_total, curr2 = money(new_prev)
    added = sorted(c for c in new_lines if c not in base_lines)
    removed = sorted(c for c in base_lines if c not in new_lines)
    changed = []
    line_amounts = []
    for c in sorted(set(base_lines) | set(new_lines)):
        before = base_lines.get(c, {}).get("subtotal")
        after = new_lines.get(c, {}).get("subtotal")
        try:
            bf = float(before) if before is not None else None
            af = float(after) if after is not None else None
        except (TypeError, ValueError):
            bf, af = before, after
        if c in added or c in removed or (bf is not None and af is not None and abs(bf - af) > 1e-6):
            if c not in added and c not in removed:
                changed.append(c)
            line_amounts.append(
                {
                    "code": c,
                    "LINE_AMOUNT_BEFORE": bf,
                    "LINE_AMOUNT_AFTER": af,
                    "currency": (new_lines.get(c) or base_lines.get(c) or {}).get("source_currency")
                    or (new_lines.get(c) or base_lines.get(c) or {}).get("cpp_currency"),
                }
            )
    delta = None
    if base_total is not None and new_total is not None:
        delta = round(new_total - base_total, 4)
    return {
        "BASE_TOTAL": base_total,
        "NEW_TOTAL": new_total,
        "TOTAL_DELTA": delta,
        "LINE_CODES_ADDED": added,
        "LINE_CODES_REMOVED": removed,
        "LINE_CODES_CHANGED": changed,
        "LINE_AMOUNTS": line_amounts,
        "CURRENCY": curr2 or curr,
    }


def build_catalog() -> list[dict]:
    """Operator-selectable OFAT scenarios (UI-authoritative tokens)."""
    rows: list[dict] = []

    def add(**kwargs: Any) -> None:
        rows.append(kwargs)

    # --- Lane A GRADI: face ---
    for tok, exp in [
        ("none", "NO"),
        ("oracal_641", "YES"),
        ("oracal_651", "YES"),
        # Baseline is already oracal_8500@1260 — identity OFAT expects no delta.
        ("oracal_8500", "NO"),
        ("print_laminate", "YES"),
    ]:
        add(
            scenario_id=f"A_FACE_{tok}",
            lane="gradi",
            baseline_variant_id="GRADI_EUR_SAFE",
            field="finish_setup.face_finish_type",
            value=tok,
            EXPECTED_COMMERCIAL_EFFECT=exp,
            ledger_ref=f"A1/{tok}",
            apply={"kind": "face", "face_finish_type": tok},
        )
    add(
        scenario_id="A_FACE_8500_W1000",
        lane="gradi",
        baseline_variant_id="GRADI_EUR_SAFE",
        field="finish_setup.face_vinyl_roll_width_mm",
        value=1000,
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="A2/1000",
        apply={"kind": "face", "face_finish_type": "oracal_8500", "face_vinyl_roll_width_mm": 1000},
    )
    add(
        scenario_id="A_FACE_COLOR_032",
        lane="gradi",
        baseline_variant_id="GRADI_EUR_SAFE",
        field="finish_setup.face_oracal_code",
        value="032",
        EXPECTED_COMMERCIAL_EFFECT="NO",
        ledger_ref="A3/color",
        apply={"kind": "finish", "face_oracal_code": "032"},
    )

    # return finishes
    for tok, exp in [
        ("white_aluminum", "NO"),
        ("black_aluminum", "NO"),
        ("gold_aluminum", "NO"),
        ("mirror_silver", "NO"),
        ("ral_paint", "YES"),
        ("oracal_wrapped", "YES"),
    ]:
        add(
            scenario_id=f"A_RETURN_{tok}",
            lane="gradi",
            baseline_variant_id="GRADI_EUR_SAFE",
            field="finish_setup.return_finish_type",
            value=tok,
            EXPECTED_COMMERCIAL_EFFECT=exp,
            ledger_ref=f"A4/{tok}",
            apply={"kind": "finish", "return_finish_type": tok, "return_depth_mm": 60},
        )

    for depth in (30, 80, 100):
        add(
            scenario_id=f"A_DEPTH_{depth}",
            lane="gradi",
            baseline_variant_id="GRADI_EUR_SAFE",
            field="finish_setup.return_depth_mm",
            value=depth,
            EXPECTED_COMMERCIAL_EFFECT="YES",
            ledger_ref=f"A5/{depth}",
            apply={"kind": "finish", "return_depth_mm": depth},
        )

    for bm, exp in [
        ("forex_10_no_bevel", "YES"),
        ("forex_10_with_bevel", "YES"),
    ]:
        add(
            scenario_id=f"A_BACK_{bm}",
            lane="gradi",
            baseline_variant_id="GRADI_EUR_SAFE",
            field="finish_setup.backing_mode",
            value=bm,
            EXPECTED_COMMERCIAL_EFFECT=exp,
            ledger_ref=f"A7/{bm}",
            apply={"kind": "finish", "backing_mode": bm},
        )

    # lighting
    add(
        scenario_id="A_LED_OFF",
        lane="gradi",
        baseline_variant_id="GRADI_EUR_SAFE",
        field="finish_setup.illuminated",
        value=False,
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="B1/false",
        apply={"kind": "finish", "illuminated": False},
    )
    add(
        scenario_id="A_LED_STRIP",
        lane="gradi",
        baseline_variant_id="GRADI_EUR_SAFE",
        field="finish_setup.lighting_system_type",
        value="led_strip",
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="B2/led_strip",
        apply={"kind": "finish", "illuminated": True, "lighting_system_type": "led_strip"},
    )
    for color in ("warm", "cool"):
        add(
            scenario_id=f"A_LIGHT_COLOR_{color}",
            lane="gradi",
            baseline_variant_id="GRADI_EUR_SAFE",
            field="finish_setup.light_color",
            value=color,
            EXPECTED_COMMERCIAL_EFFECT="NO",
            ledger_ref=f"B3/{color}",
            apply={"kind": "finish", "illuminated": True, "light_color": color},
        )
    for w in (1.0, 1.44):
        add(
            scenario_id=f"A_LED_POWER_{w}",
            lane="gradi",
            baseline_variant_id="GRADI_EUR_SAFE",
            field="finish_setup.led_module_power_w",
            value=w,
            EXPECTED_COMMERCIAL_EFFECT="YES",
            ledger_ref=f"B4/{w}",
            apply={
                "kind": "finish",
                "illuminated": True,
                "lighting_system_type": "led_modules",
                "led_module_power_w": w,
            },
        )
    for psu in (100, 160, 200):
        add(
            scenario_id=f"A_PSU_{psu}",
            lane="gradi",
            baseline_variant_id="GRADI_EUR_SAFE",
            field="finish_setup.selected_psu_watts",
            value=psu,
            EXPECTED_COMMERCIAL_EFFECT="YES",
            ledger_ref=f"B6/{psu}",
            apply={"kind": "finish", "illuminated": True, "selected_psu_watts": psu},
        )

    # mounting
    add(
        scenario_id="A_MOUNT_TMPL_FOREX_ON",
        lane="gradi",
        baseline_variant_id="GRADI_EUR_SAFE",
        field="finish_setup.mounting_template_enabled",
        value=True,
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="D2/true+forex",
        apply={
            "kind": "finish",
            "mounting_template_enabled": True,
            "mounting_template_material_type": "forex",
            "mounting_template_area_m2": 1.5,
            "mounting_scope": "preparation_only",
        },
    )
    add(
        scenario_id="A_MOUNT_TMPL_PAPER",
        lane="gradi",
        baseline_variant_id="GRADI_EUR_SAFE",
        field="finish_setup.mounting_template_material_type",
        value="paper",
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="D4/paper",
        apply={
            "kind": "finish",
            "mounting_template_enabled": True,
            "mounting_template_material_type": "paper",
            "mounting_template_area_m2": 1.5,
            "mounting_scope": "preparation_only",
        },
    )
    add(
        scenario_id="A_MOUNT_SITE_ON",
        lane="gradi",
        baseline_variant_id="GRADI_EUR_SAFE",
        field="finish_setup.site_installation_included",
        value=True,
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="D6/true",
        apply={
            "kind": "finish",
            "mounting_scope": "preparation_and_site_installation",
            "site_installation_included": True,
            "mounting_template_enabled": False,
        },
    )

    # commercial adjustments
    add(
        scenario_id="A_MARKUP_10",
        lane="gradi",
        baseline_variant_id="GRADI_EUR_SAFE",
        field="commercial_inputs.markup_percent",
        value=10,
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="E1/10",
        apply={"kind": "commercial", "markup_percent": 10},
    )
    add(
        scenario_id="A_DISCOUNT_5",
        lane="gradi",
        baseline_variant_id="GRADI_EUR_SAFE",
        field="commercial_inputs.discount_percent",
        value=5,
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="E2/5",
        apply={"kind": "commercial", "discount_percent": 5},
    )
    add(
        scenario_id="A_MANUAL_RON_100",
        lane="gradi",
        baseline_variant_id="GRADI_EUR_SAFE",
        field="commercial_inputs.manual_adjustment_ron",
        value=100,
        EXPECTED_COMMERCIAL_EFFECT="UNKNOWN",
        ledger_ref="E4/100",
        apply={"kind": "commercial", "manual_adjustment_ron": 100},
        special="manual_ron",
    )

    # confirmed gate
    add(
        scenario_id="A_CONFIRMED_FALSE",
        lane="gradi",
        baseline_variant_id="GRADI_EUR_SAFE",
        field="finish_setup.confirmed / letter_group confirmed",
        value=False,
        EXPECTED_COMMERCIAL_EFFECT="UNKNOWN",
        ledger_ref="gate/confirmed",
        apply={"kind": "finish", "confirmed": False},
    )

    # --- Lane B BOND letters (ACM optional baseline) ---
    for tok, exp in [
        ("none", "NO"),
        ("oracal_641", "YES"),
        ("oracal_8500", "YES"),
        ("print_laminate", "YES"),
    ]:
        add(
            scenario_id=f"B_FACE_{tok}",
            lane="bond",
            baseline_variant_id="BOND_LETTERS_ACM_OPTIONAL",
            field="finish_setup.face_finish_type",
            value=tok,
            EXPECTED_COMMERCIAL_EFFECT=exp,
            ledger_ref=f"A1/{tok}",
            apply={"kind": "face", "face_finish_type": tok, "face_vinyl_roll_width_mm": 1260},
        )
    add(
        scenario_id="B_RETURN_RAL",
        lane="bond",
        baseline_variant_id="BOND_LETTERS_ACM_OPTIONAL",
        field="finish_setup.return_finish_type",
        value="ral_paint",
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="A4/ral_paint",
        apply={"kind": "finish", "return_finish_type": "ral_paint", "return_depth_mm": 100},
    )

    # ACM sold-scope transition + construction (included baseline)
    add(
        scenario_id="B_ACM_INCLUDE_SOLD",
        lane="bond",
        baseline_variant_id="BOND_LETTERS_ACM_OPTIONAL",
        field="acm sold composition",
        value="included",
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="ACM/sold-scope",
        apply={"kind": "baseline_switch", "to": "BOND_ACM_INCLUDED"},
        acm_flags_probe=True,
    )
    add(
        scenario_id="B_ACM_FOLD_1",
        lane="bond",
        baseline_variant_id="BOND_ACM_INCLUDED",
        field="acm_panel_instance.configuration.fold_count",
        value=1,
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="C11/1",
        apply={"kind": "nested", "path": "finish_setup.acm_panel_instance.configuration.fold_count", "value": 1},
        acm_flags_probe=True,
    )
    add(
        scenario_id="B_ACM_THICKNESS_4",
        lane="bond",
        baseline_variant_id="BOND_ACM_INCLUDED",
        field="acm_panel_instance.configuration.acm_thickness_mm",
        value=4,
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="C12/4",
        apply={
            "kind": "nested",
            "path": "finish_setup.acm_panel_instance.configuration.acm_thickness_mm",
            "value": 4,
        },
        acm_flags_probe=True,
    )
    add(
        scenario_id="B_ACM_L1_80",
        lane="bond",
        baseline_variant_id="BOND_ACM_INCLUDED",
        field="acm_panel_instance.configuration.l1_mm",
        value=80,
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="C12/l1_80",
        apply={"kind": "nested", "path": "finish_setup.acm_panel_instance.configuration.l1_mm", "value": 80},
        acm_flags_probe=True,
    )
    add(
        scenario_id="B_ACM_FOIL_AFTER_FRAME",
        lane="bond",
        baseline_variant_id="BOND_ACM_INCLUDED",
        field="shell_finish.apply_after_frame",
        value=True,
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="C4/after_frame",
        apply={
            "kind": "nested",
            "path": "finish_setup.acm_panel_instance.shell_finish.apply_after_frame",
            "value": True,
        },
        acm_flags_probe=True,
    )
    add(
        scenario_id="B_ACM_SHEET_COLORAT",
        lane="bond",
        baseline_variant_id="BOND_ACM_INCLUDED",
        field="sheet_material.variant",
        value="colorat",
        EXPECTED_COMMERCIAL_EFFECT="YES",
        ledger_ref="C1/colorat",
        apply={
            "kind": "nested",
            "path": "finish_setup.acm_panel_instance.sheet_material.variant",
            "value": "colorat",
        },
        acm_flags_probe=True,
    )
    add(
        scenario_id="B_MANUAL_RON_100",
        lane="bond",
        baseline_variant_id="BOND_ACM_INCLUDED",
        field="commercial_inputs.manual_adjustment_ron",
        value=100,
        EXPECTED_COMMERCIAL_EFFECT="UNKNOWN",
        ledger_ref="E4/100",
        apply={"kind": "commercial", "manual_adjustment_ron": 100},
        special="manual_ron",
        acm_flags_probe=True,
    )

    return rows


def apply_scenario(qi: dict, apply: dict, baselines: dict[str, dict]) -> dict:
    kind = apply.get("kind")
    if kind == "baseline_switch":
        return copy.deepcopy(baselines[apply["to"]]["quote_input"])
    if kind == "commercial":
        kw = {k: v for k, v in apply.items() if k != "kind"}
        return set_commercial(qi, **kw)
    if kind == "nested":
        out = set_nested(qi, apply["path"], apply["value"])
        # Keep mounting_solution ACM mirror in sync when mutating finish_setup.acm_panel_instance.*
        path = str(apply["path"])
        prefix = "finish_setup.acm_panel_instance."
        if path.startswith(prefix):
            mirror = "finish_setup.mounting_solution.configuration.acm_panel_instance." + path[
                len(prefix) :
            ]
            out = set_nested(out, mirror, apply["value"])
        return out
    if kind == "face":
        kw = {k: v for k, v in apply.items() if k != "kind"}
        if kw.get("face_finish_type") == "oracal_8500" and "face_vinyl_roll_width_mm" not in kw:
            kw["face_vinyl_roll_width_mm"] = 1260
        if kw.get("face_finish_type") in {"oracal_641", "oracal_651", "oracal_8500"}:
            kw.setdefault("face_oracal_code", "021")
        return set_finish(qi, **kw)
    if kind == "finish":
        kw = {k: v for k, v in apply.items() if k != "kind"}
        return set_finish(qi, **kw)
    raise ValueError(f"unknown apply kind {kind}")


def acm_scope_flags(qi: dict) -> dict:
    fs = qi.get("finish_setup") or {}
    inst = fs.get("acm_panel_instance")
    present = inst is not None
    included = False
    confirmed = False
    optional = False
    if present and isinstance(inst, dict):
        confirmed = str(inst.get("composition_status") or "") == "confirmed"
        # product_composition items
    pc = qi.get("product_composition") or {}
    items = pc.get("items") or []
    for it in items:
        if it.get("key") in {"support", "acm"}:
            st = str(it.get("status") or "")
            if st in {"included", "applied_content"}:
                included = True
            if st == "available_optional":
                optional = True
    if present and not included and not optional:
        optional = not confirmed
    return {
        "ACM_PRESENT_IN_PRODUCT_TRUTH": present,
        "ACM_AVAILABLE_OPTIONAL": optional and not included,
        "ACM_CONFIRMED": confirmed,
        "ACM_INCLUDED_IN_SOLD_COMPOSITION": included or (present and confirmed),
        "ACM_PRICED": None,  # filled after preview
    }


def main() -> None:
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    BASELINES.mkdir(parents=True, exist_ok=True)
    CAPTURES.mkdir(parents=True, exist_ok=True)

    catalog = build_catalog()
    (EVIDENCE / "scenario_catalog_v1.json").write_text(
        json.dumps(
            {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "template": TEMPLATE,
                "currency": CURRENCY,
                "scenarios": catalog,
            },
            indent=2,
            ensure_ascii=True,
        )
        + "\n",
        encoding="utf-8",
    )

    baselines: dict[str, dict] = {}
    for vid, builder in [
        ("GRADI_EUR_SAFE", lambda: gradi_baseline_quote_input()),
        ("BOND_LETTERS_ACM_OPTIONAL", lambda: bond_baseline_quote_input(acm_included=False)),
        ("BOND_ACM_INCLUDED", lambda: bond_baseline_quote_input(acm_included=True)),
    ]:
        qi = builder()
        resp = call_preview(qi)
        prev = unwrap(resp)
        snap = {
            "baseline_variant_id": vid,
            "quote_input_sha256": _sha(qi),
            "cpp_sha256": _sha(prev),
            "money": {"total": money(prev)[0], "currency": money(prev)[1]},
            "complete_offer": complete_offer(prev),
            "blockers": blockers(prev),
            "line_codes": sorted(line_map(prev).keys()),
            "http_status": resp.get("_http_status"),
        }
        baselines[vid] = {"quote_input": qi, "preview": prev, "resp": resp, "snap": snap}
        (BASELINES / f"{vid}.json").write_text(
            json.dumps({"snap": snap, "quote_input": qi, "preview": prev}, indent=2, default=str)
            + "\n",
            encoding="utf-8",
        )

    results: list[dict] = []
    manual_ron_report: dict[str, Any] = {}

    for sc in catalog:
        vid = sc["baseline_variant_id"]
        base = baselines[vid]
        base_qi = base["quote_input"]
        base_prev = base["preview"]
        qi = apply_scenario(base_qi, sc["apply"], baselines)
        # Ensure no leakage: always from frozen baseline variant, not prior mutation.
        assert _sha(base_qi) == baselines[vid]["snap"]["quote_input_sha256"]

        resp = call_preview(qi)
        prev = unwrap(resp)
        http_err = bool(resp.get("_error")) or int(resp.get("_http_status") or 200) >= 400
        expected = sc["EXPECTED_COMMERCIAL_EFFECT"]
        observed, defect, rationale, first_broken = classify(
            expected=expected, base_prev=base_prev, new_prev=prev, http_error=http_err
        )
        attr = attribution(base_prev, prev)
        co = complete_offer(prev)
        line_status = "priced_delta" if observed == "PRICED_LINE" else (
            "error" if observed == "ERROR" else "no_line_delta"
        )
        if co.get("complete_offer_total") is not None:
            offer_status = "total_valid"
        elif "CURRENCY" in str(co.get("complete_offer_total_unavailable_reason") or ""):
            offer_status = "currency_mix_or_null"
        elif blockers(prev):
            offer_status = "blocked_or_null"
        else:
            offer_status = "total_null"

        acm_flags = None
        if sc.get("acm_flags_probe") or sc["lane"] == "bond":
            acm_flags = acm_scope_flags(qi)
            acm_lines = [c for c in line_map(prev) if c.startswith("acm_")]
            acm_flags["ACM_PRICED"] = bool(acm_lines)

        row = {
            "scenario_id": sc["scenario_id"],
            "lane": sc["lane"],
            "BASELINE_VARIANT_ID": vid,
            "field": sc["field"],
            "value": sc["value"],
            "ledger_ref": sc.get("ledger_ref"),
            "EXPECTED_COMMERCIAL_EFFECT": expected,
            "OBSERVED_CLASS": observed,
            "DEFECT": defect,
            "RATIONALE": rationale,
            "FIRST_BROKEN_BOUNDARY": first_broken if defect else "NONE",
            "LINE_PRICING_STATUS": line_status,
            "COMPLETE_OFFER_STATUS": offer_status,
            "attribution": attr,
            "complete_offer": co,
            "blockers": blockers(prev),
            "acm_scope": acm_flags,
            "http_status": resp.get("_http_status"),
            "quote_input_sha256": _sha(qi),
            "cpp_sha256": _sha(prev),
        }

        if sc.get("special") == "manual_ron":
            # Special currency audit — do not repair.
            accepted = not http_err
            conversion = None
            fx = None
            # Heuristic observation only
            if attr["TOTAL_DELTA"] not in (None, 0) and attr.get("CURRENCY") == "EUR":
                conversion = "UNKNOWN_OR_IMPLICIT"
            elif attr["TOTAL_DELTA"] in (None, 0):
                conversion = "NO_OR_IGNORED"
            manual_ron_report[sc["scenario_id"]] = {
                "MANUAL_RON_INPUT_ACCEPTED": accepted,
                "CONTRACT_SOURCE": "commercial_inputs.manual_adjustment_ron / finish_setup.commercial_inputs",
                "CONVERSION_USED": conversion not in (None, "NO_OR_IGNORED"),
                "FX_SOURCE": fx or "NONE",
                "CPP_RESULT": {
                    "status": prev.get("status"),
                    "subtotal": attr["NEW_TOTAL"],
                    "currency": attr["CURRENCY"],
                    "TOTAL_DELTA": attr["TOTAL_DELTA"],
                },
                "COMPLETE_OFFER_TOTAL": co.get("complete_offer_total"),
                "OBSERVED_CLASS": observed,
                "P0_CURRENCY_POLICY": bool(
                    accepted
                    and attr.get("CURRENCY") == "EUR"
                    and (attr["TOTAL_DELTA"] not in (None, 0))
                    and conversion == "UNKNOWN_OR_IMPLICIT"
                ),
            }
            if manual_ron_report[sc["scenario_id"]]["P0_CURRENCY_POLICY"]:
                row["DEFECT"] = True
                row["OBSERVED_CLASS"] = "CURRENCY_MIX"
                row["FIRST_BROKEN_BOUNDARY"] = "CURRENCY_COMPOSITION"
                row["RATIONALE"] = (
                    "manual RON adjustment appears to affect EUR commercial total "
                    "without explicit canonical FX conversion contract"
                )
                row["severity"] = "P0"

        results.append(row)
        (CAPTURES / f"{sc['scenario_id']}.json").write_text(
            json.dumps({"scenario": sc, "result": row, "preview": prev}, indent=2, default=str)
            + "\n",
            encoding="utf-8",
        )

    # severity assignment for remaining defects
    for row in results:
        if row.get("severity"):
            continue
        if not row["DEFECT"]:
            row["severity"] = None
            continue
        oc = row["OBSERVED_CLASS"]
        if oc in {"CURRENCY_MIX", "ERROR"} or (
            oc == "PRICED_LINE" and row["COMPLETE_OFFER_STATUS"] != "total_valid"
        ):
            row["severity"] = "P0"
        elif oc in {"NO_EFFECT", "MISSING_RULE", "BLOCKER"} and row["EXPECTED_COMMERCIAL_EFFECT"] == "YES":
            row["severity"] = "P1"
        else:
            row["severity"] = "P2"

    results_path = EVIDENCE / "results.jsonl"
    with results_path.open("w", encoding="utf-8") as f:
        for row in results:
            f.write(json.dumps(row, ensure_ascii=True, default=str) + "\n")

    (EVIDENCE / "manual_ron_audit.json").write_text(
        json.dumps(manual_ron_report, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    (EVIDENCE / "baseline_index.json").write_text(
        json.dumps({k: v["snap"] for k, v in baselines.items()}, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"scenarios={len(results)} evidence={EVIDENCE}")
    print("baseline_totals=")
    for k, v in baselines.items():
        print(" ", k, v["snap"]["money"], "complete=", v["snap"]["complete_offer"].get("complete_offer_total"))


if __name__ == "__main__":
    main()
