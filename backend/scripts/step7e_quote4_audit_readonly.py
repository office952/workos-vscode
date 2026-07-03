"""Step 7E read-only audit for quote 4 — no DB writes, no /price."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import db_manager
from models.quotes import Quotes
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_templates import Product_templates
from services.product_definition_builder_service import ProductDefinitionBuilderService
from services.aggregate_cost_bom_adapter import AggregateCostBomBuilderService
from services.product_system_cost_simulation_service import ProductSystemCostSimulationService
from services.intake_product_spec_loader import load_intake_product_spec
from routers.quotes import _resolve_volumetric_quote_input_for_intake


def _summarize_payload(payload: dict) -> dict:
    finish = payload.get("finish") if isinstance(payload.get("finish"), dict) else {}
    geom = payload.get("quote_geometry") if isinstance(payload.get("quote_geometry"), dict) else {}
    svg = payload.get("svg_source") if isinstance(payload.get("svg_source"), dict) else {}
    return {
        "finish_keys": sorted(finish.keys()),
        "mounting_system": finish.get("mounting_system"),
        "lighting_system_type": finish.get("lighting_system_type"),
        "illuminated": finish.get("illuminated"),
        "selected_psu_watts": finish.get("selected_psu_watts"),
        "quote_geometry_keys": sorted(geom.keys()),
        "letter_count": geom.get("letter_count"),
        "letter_face_area_m2": geom.get("letter_face_area_m2"),
        "letter_perimeter_m": geom.get("letter_perimeter_m"),
        "return_depth_mm": geom.get("return_depth_mm"),
        "svg_file_name": svg.get("file_name"),
        "width_mm": geom.get("width_mm") or payload.get("width_mm"),
        "height_mm": geom.get("height_mm") or payload.get("height_mm"),
    }


def _extract_quote_input_from_line_items(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return {}
    if not isinstance(parsed, dict):
        return {}
    if isinstance(parsed.get("quote_input"), dict):
        return parsed["quote_input"]
    # Shape B wrapper
    inner = parsed.get("line_items")
    if isinstance(inner, dict) and isinstance(inner.get("quote_input"), dict):
        return inner["quote_input"]
    return {}


def _status_val(v):
    return v.value if hasattr(v, "value") else v


async def run_audit() -> dict:
    report: dict = {}
    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        # A. Quote 4 read-only
        q_row = await db.scalar(select(Quotes).where(Quotes.id == 4))
        if not q_row:
            return {"error": "quote_4_not_found"}
        report["quote_before"] = {
            "id": q_row.id,
            "code": q_row.code,
            "status": q_row.status,
            "grand_total": q_row.grand_total,
            "intake_id": q_row.intake_id,
            "intake_code": q_row.intake_code,
            "margin_pct": q_row.margin_pct,
        }
        line_items_raw = q_row.line_items
        quote_input_from_li = _extract_quote_input_from_line_items(line_items_raw)
        report["quote_input_from_line_items"] = quote_input_from_li

        workspace_id = None
        payload_summary = {}
        if q_row.intake_code and str(q_row.intake_code).startswith("IV6-"):
            workspace_id = str(q_row.intake_code)[4:]
        ws = None
        if workspace_id:
            ws = await db.scalar(
                select(IntakeV6WorkspaceRecord).where(
                    IntakeV6WorkspaceRecord.id == workspace_id
                )
            )
        if ws:
            payload = json.loads(ws.payload_json or "{}")
            payload_summary = _summarize_payload(payload if isinstance(payload, dict) else {})
            report["workspace"] = {
                "workspace_id": ws.id,
                "workspace_code": ws.workspace_code,
                "template_code": ws.template_code,
                "status": ws.status,
                "readiness_status": ws.readiness_status,
                "payload_summary": payload_summary,
            }

        template_code = ws.template_code if ws else "TPL-VOLUMETRIC-LETTERS_v2"
        tpl = await db.scalar(
            select(Product_templates).where(Product_templates.template_code == template_code)
        )
        template_id = tpl.id if tpl else None
        report["template"] = {
            "template_id": template_id,
            "template_code": template_code,
            "active": bool(tpl.active) if tpl else None,
        }

        product_spec = await load_intake_product_spec(db, q_row.intake_id)
        resolved_quote_input = await _resolve_volumetric_quote_input_for_intake(
            db,
            intake_id=q_row.intake_id,
            quote_input=quote_input_from_li or {},
            product_spec_json=product_spec,
        )
        report["resolved_quote_input"] = resolved_quote_input

        # B. ProductDefinition preview
        pd_service = ProductDefinitionBuilderService(db)
        pd = await pd_service.build_preview(template_code, workspace_id=workspace_id)
        if pd:
            report["product_definition"] = {
                "readiness_status": _status_val(pd.validation.readiness_status) if pd.validation else None,
                "selected_modules": [
                    {"code": m.module_code, "state": m.state} for m in pd.selected_modules
                ],
                "optional_modules": [
                    {"code": m.module_code, "state": m.state} for m in pd.optional_modules
                ],
                "inactive_modules": [
                    {"code": m.module_code, "state": m.state} for m in pd.inactive_modules
                ],
                "missing_required_fields": pd.validation.missing_required_fields if pd.validation else [],
                "unresolved_warnings": pd.validation.unresolved_warnings if pd.validation else [],
                "invalid_combinations": pd.validation.invalid_combinations if pd.validation else [],
                "provenance": [p.model_dump() for p in (pd.provenance or [])[:8]],
                "source_context": pd.source_context.model_dump() if pd.source_context else {},
            }

        # C. Aggregate Cost BOM preview
        bom_service = AggregateCostBomBuilderService(db)
        bom = await bom_service.build_preview(
            template_code,
            workspace_id=workspace_id,
            quote_input=resolved_quote_input,
        )
        if bom:
            skipped = [
                s.model_dump() if hasattr(s, "model_dump") else dict(s)
                for s in (bom.skipped_items or [])
            ]
            comp_flat = [s for s in skipped if "comp_flat_legacy" in str(s.get("item_id", s.get("component_id", "")))]
            report["cost_bom"] = {
                "bom_status": _status_val(bom.bom_status) if bom.bom_status else None,
                "source": "v2_aggregate",
                "uses_parent_bom_as_structural_truth": (
                    bom.source_context.uses_parent_bom_as_structural_truth if bom.source_context else None
                ),
                "aggregate_cost_source": not (
                    bom.source_context.uses_parent_bom_as_structural_truth if bom.source_context else True
                ),
                "costable_materials_count": len(bom.costable_materials or []),
                "costable_operations_count": len(bom.costable_operations or []),
                "missing_pricing_count": len(bom.missing_pricing or []),
                "missing_geometry_count": len(bom.missing_geometry or []),
                "missing_pricing": [m.model_dump() for m in (bom.missing_pricing or [])[:20]],
                "missing_geometry": list(bom.missing_geometry or [])[:20],
                "pricing_blockers": [b.model_dump() for b in (bom.pricing_blockers or [])[:20]],
                "missing_inventory_materials": list(bom.missing_inventory_materials or [])[:20],
                "skipped_items": skipped,
                "comp_flat_legacy_in_skipped": len(comp_flat) > 0,
                "comp_flat_legacy_in_costable": any(
                    c.component_id == "comp_flat_legacy"
                    for c in (bom.costable_components or [])
                ),
                "comp_auto_1_in_costable": any(
                    c.component_id == "comp_auto_1" for c in (bom.costable_components or [])
                ),
                "externalization_requirements": [
                    e.model_dump() for e in (bom.externalization_requirements or [])[:5]
                ],
            }

        # D. Dry-run simulation (no persist)
        sim_result = None
        if template_id:
            sim_service = ProductSystemCostSimulationService(db)
            sim_result = await sim_service.simulate(
                template_id=template_id,
                quantity=1,
                quote_input=resolved_quote_input,
                pricing={"margin_pct": q_row.margin_pct or 0},
                intake_id=q_row.intake_id,
                simulation_context={
                    "source": "step7e_quote4_dry_run",
                    "reason": "owner dry-run validation",
                    "quote_id": 4,
                    "no_persist": True,
                },
            )
            report["simulation"] = {
                "available": True,
                "safe_no_persist": bool(sim_result.trace.get("no_persist")),
                "status": sim_result.status,
                "cost_engine_version": sim_result.cost_engine_version,
                "blocked_reasons": sim_result.blocked_reasons,
                "blockers": sim_result.blockers,
                "warnings": sim_result.warnings[:15],
                "total_cost": (sim_result.cost_result or {}).get("total_cost"),
                "parent_total_cost": (sim_result.cost_result or {}).get("parent_total_cost"),
                "trace": sim_result.trace,
                "readiness": sim_result.readiness,
                "component_breakdown_count": len(sim_result.component_breakdown or []),
            }
        else:
            report["simulation"] = {"available": False, "reason": "template_id_missing"}

        # Quote 4 after (read-only confirm)
        q_after = await db.scalar(select(Quotes).where(Quotes.id == 4))
        report["quote_after"] = {
            "status": q_after.status if q_after else None,
            "grand_total": q_after.grand_total if q_after else None,
        }
        report["db_unchanged"] = (
            report["quote_before"]["status"] == report["quote_after"]["status"]
            and report["quote_before"]["grand_total"] == report["quote_after"]["grand_total"]
        )

        # Parity helpers
        if pd and bom:
            pd_active = {
                m.module_code
                for m in (pd.selected_modules + pd.optional_modules)
                if m.state in ("always_on", "active", "conditional_active")
            }
            bom_modules = {m.module_code for m in (bom.active_modules or [])}
            report["parity"] = {
                "pd_active_modules": sorted(pd_active),
                "bom_active_modules": sorted(bom_modules),
                "modules_match": pd_active == bom_modules,
            }

    return report


if __name__ == "__main__":
    result = asyncio.run(run_audit())
    print(json.dumps(result, indent=2, default=str))
