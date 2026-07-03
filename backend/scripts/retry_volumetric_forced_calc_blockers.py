"""Report CostEngine blockers for TPL-VOLUMETRIC-LETTERS preliminary costing (read-only)."""

from __future__ import annotations

import asyncio
import json
import os
import sys

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from core.database import db_manager  # noqa: E402
import models  # noqa: F401,E402

from seeds.seed_build4_templates import _volumetric_letters_components  # noqa: E402
from seeds.seed_volumetric_owner_confirmed_prices import (  # noqa: E402
    ESTIMATED_PRELIMINARY_ACTIVATED_CODES,
    OWNER_CONFIRMED_ACTIVATED_CODES,
    PRELIMINARY_BLOCKERS_DOCUMENTED,
    PRELIMINARY_COSTING_ALIAS_CODES,
)
from seeds.seed_volumetric_workcenter_rates import (  # noqa: E402
    RETURN_PROFILE_FACE_BONDING_CODE,
    RETURN_PROFILE_MACHINE_FORMING_CODE,
)
from services.cost_engine_service import (  # noqa: E402
    ERR_FORMULA_UNKNOWN,
    ERR_MATERIAL_RATE_MISSING,
    ERR_WORKCENTER_RATE_MISSING,
    ComponentCostContext,
    build_execution_layers_from_components,
)
from services.formula_handlers import resolve_formula  # noqa: E402
from services.inventory_materials_admin_service import (  # noqa: E402
    list_inventory_materials_admin,
)
from services.volumetric_material_rate_resolver import (  # noqa: E402
    resolve_volumetric_material_rates_with_trace,
)
from services.workcenter_rates_service import load_workcenter_rate_dict  # noqa: E402

FULL_QUOTE_INPUT = {
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "letter_count": 9,
    "return_depth_mm": 60,
    "selected_psu_watts": 100,
    "psu_watts": 100,
    "led_module_count": 180,
    "mounting_template_area_m2": 2.88,
}


def _rates_from_registry(rows: list[dict]) -> dict[str, float]:
    rates: dict[str, float] = {}
    for row in rows:
        code = str(row.get("code") or "").strip()
        cost = row.get("unit_cost")
        if not code or cost is None or float(cost) <= 0:
            continue
        if str(row.get("status") or "") != "active":
            continue
        rates[code] = float(cost)
    return rates


def _labor_ops_summary(out: dict) -> dict:
    labor_codes = {
        RETURN_PROFILE_MACHINE_FORMING_CODE,
        RETURN_PROFILE_FACE_BONDING_CODE,
        "mounting_template_cnc_cut",
    }
    lines: list[dict] = []
    labor_total = 0.0
    for comp in out.get("components") or []:
        for op in comp.get("operations_detail") or []:
            code = str(op.get("code") or "")
            wc = str(op.get("workcenter") or "")
            if code not in labor_codes and wc not in {
                RETURN_PROFILE_MACHINE_FORMING_CODE,
                RETURN_PROFILE_FACE_BONDING_CODE,
            }:
                continue
            line_total = float(op.get("line_total") or 0.0)
            labor_total += line_total
            lines.append(
                {
                    "code": code,
                    "workcenter": wc,
                    "rate_basis": op.get("rate_basis"),
                    "linear_meters": op.get("linear_meters"),
                    "hours": op.get("hours"),
                    "line_total": line_total,
                }
            )
    profile_material = 0.0
    for comp in out.get("components") or []:
        for mat in comp.get("materials_detail") or []:
            if str(mat.get("material_code") or "") == "MAT-PROFIL-LATERAL-LITERE":
                profile_material = float(mat.get("line_total") or 0.0)
    return {
        "lines": lines,
        "labor_service_total": round(labor_total, 2),
        "profile_material_only": profile_material,
    }


async def main() -> int:
    await db_manager.init_db()
    async with db_manager.async_session_maker() as session:
        registry = await list_inventory_materials_admin(session)
        workcenter_rates = await load_workcenter_rate_dict(session)
    rates = _rates_from_registry(registry)
    rates, resolution_trace = resolve_volumetric_material_rates_with_trace(
        rates,
        FULL_QUOTE_INPUT,
        template_code="TPL-VOLUMETRIC-LETTERS",
    )

    led_formula = resolve_formula(
        "led_per_letter",
        {"module_length_mm": 75, "module_gap_mm": 25},
        FULL_QUOTE_INPUT,
    )

    components = _volumetric_letters_components()
    template = {
        "template_code": "TPL-VOLUMETRIC-LETTERS",
        "components_json": json.dumps(components),
        "operations_json": "[]",
        "required_materials_json": "[]",
    }
    fallback_wc = {
        "CNC_ROUTER": 90.0,
        "LASER_CUTTING": 90.0,
        "ASSEMBLY": 80.0,
        "LED_ASSEMBLY": 60.0,
        "ELECTRICAL_WIRING": 60.0,
        "PAINTING": 70.0,
        "QC_INSPECTION": 50.0,
        "PACKAGING": 40.0,
        "PREPRESS": 50.0,
        RETURN_PROFILE_MACHINE_FORMING_CODE: {
            "rate_basis": "per_linear_meter",
            "rate_per_linear_meter": 5.0,
        },
        RETURN_PROFILE_FACE_BONDING_CODE: {
            "rate_basis": "per_linear_meter",
            "rate_per_linear_meter": 7.0,
        },
    }
    merged_wc = {**fallback_wc, **workcenter_rates}
    ctx = ComponentCostContext(
        material_rates=rates,
        workcenter_rates=merged_wc,
        quantity=1,
        quote_input=dict(FULL_QUOTE_INPUT),
    )
    out = build_execution_layers_from_components(template, ctx)
    kinds = sorted({e.get("kind") for e in out.get("errors") or []})
    missing = []
    for e in out.get("errors") or []:
        if e.get("kind") != ERR_MATERIAL_RATE_MISSING:
            continue
        detail = str(e.get("detail") or "")
        for code in (
            list(OWNER_CONFIRMED_ACTIVATED_CODES)
            + list(ESTIMATED_PRELIMINARY_ACTIVATED_CODES)
            + list(PRELIMINARY_COSTING_ALIAS_CODES)
        ):
            if code in detail:
                missing.append(code)

    report = {
        "is_valid": out.get("is_valid"),
        "error_kinds": kinds,
        "formula_unknown": ERR_FORMULA_UNKNOWN in kinds,
        "workcenter_rate_missing": ERR_WORKCENTER_RATE_MISSING in kinds,
        "material_rate_missing_codes": sorted(set(missing)),
        "led_module_formula": {
            "resolved": led_formula.resolved,
            "value": led_formula.value,
            "breakdown": led_formula.breakdown,
        },
        "profile_resolution": resolution_trace.profile_lateral.to_dict(),
        "psu_resolution": resolution_trace.led_psu_12v.to_dict(),
        "documented_preliminary_blockers": PRELIMINARY_BLOCKERS_DOCUMENTED,
        "total_material_cost": out.get("total_material_cost"),
        "total_operation_cost": out.get("total_operation_cost"),
        "labor_service_summary": _labor_ops_summary(out),
    }
    print(json.dumps(report, indent=2, default=str))
    unexpected = [
        c
        for c in OWNER_CONFIRMED_ACTIVATED_CODES
        if c in set(missing) and c not in PRELIMINARY_COSTING_ALIAS_CODES
    ]
    return 0 if not unexpected and not report["formula_unknown"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
