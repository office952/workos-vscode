"""Step 7E.1 — Quote 4 payload / intake linkage repair dry-run.

Default: read-only plan + in-memory validation. NO DB writes.
Optional --apply: NOT executed in Step 7E.1 (requires owner GO + backup).

Usage:
  python scripts/step7e1_quote4_payload_repair_dryrun.py
  python scripts/step7e1_quote4_payload_repair_dryrun.py --quote-id 4
  python scripts/step7e1_quote4_payload_repair_dryrun.py --apply  # DO NOT RUN without owner GO
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))

from sqlalchemy import select

from core.database import db_manager
from models.intake_requests import Intake_requests
from models.intake_v6_workspace import IntakeV6WorkspaceRecord
from models.product_template_module_links import ProductTemplateModuleLink
from models.quotes import Quotes
from models.workcenter_rates import Workcenter_rates
from routers.quotes import _resolve_volumetric_quote_input_for_intake
from services.aggregate_cost_bom_adapter import AggregateCostBomBuilderService
from services.product_system_cost_simulation_service import ProductSystemCostSimulationService
from services.quote4_workspace_quote_input_mapper import (
    audit_wc_assembly_rate,
    build_intake_linkage_repair_plan,
    build_product_spec_proposal,
    build_proposed_line_items_enrichment,
    build_workspace_payload_patches,
    map_workspace_to_quote_input,
)
from services.volumetric_finish_assignment_service import normalize_volumetric_quote_input_from_finish_assignments


def _status_val(v: Any) -> Any:
    return v.value if hasattr(v, "value") else v


def _parse_line_items(raw: str | None) -> list[dict[str, Any]]:
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def _field_sources(provenance: list) -> dict[str, str]:
    return {p.key: p.source_path for p in provenance if p.value is not None and p.value != ""}


async def run_dry_run(*, quote_id: int = 4, apply: bool = False) -> dict[str, Any]:
    if apply:
        raise SystemExit(
            "ERROR: --apply is NOT permitted in Step 7E.1. "
            "Owner GO required. Run dry-run only."
        )

    report: dict[str, Any] = {
        "step": "7E.1",
        "mode": "dry_run",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "apply_executed": False,
    }

    await db_manager.ensure_initialized()
    async with db_manager.async_session_maker() as db:
        quote = await db.scalar(select(Quotes).where(Quotes.id == quote_id))
        if not quote:
            report["error"] = f"quote_{quote_id}_not_found"
            return report

        report["quote_before"] = {
            "id": quote.id,
            "code": quote.code,
            "status": quote.status,
            "grand_total": quote.grand_total,
            "intake_id": quote.intake_id,
            "intake_code": quote.intake_code,
            "margin_pct": quote.margin_pct,
            "line_items_raw": quote.line_items,
        }

        workspace_id = None
        if quote.intake_code and str(quote.intake_code).startswith("IV6-"):
            workspace_id = str(quote.intake_code)[4:]

        ws = None
        if workspace_id:
            ws = await db.scalar(
                select(IntakeV6WorkspaceRecord).where(IntakeV6WorkspaceRecord.id == workspace_id)
            )

        payload: dict[str, Any] = {}
        if ws and ws.payload_json:
            try:
                payload = json.loads(ws.payload_json)
            except (TypeError, ValueError):
                payload = {}
            if not isinstance(payload, dict):
                payload = {}

        report["workspace_audit"] = {
            "workspace_id": ws.id if ws else None,
            "workspace_code": ws.workspace_code if ws else None,
            "template_code": ws.template_code if ws else None,
            "status": ws.status if ws else None,
            "readiness_status": ws.readiness_status if ws else None,
            "payload_keys": sorted(payload.keys()) if payload else [],
            "intake_request_code_in_payload": payload.get("intake_request_code"),
        }

        # Module links for volum aluminum derivation
        module_links = (
            await db.execute(
                select(ProductTemplateModuleLink).where(
                    ProductTemplateModuleLink.parent_template_code == (ws.template_code if ws else "TPL-VOLUMETRIC-LETTERS_v2")
                )
            )
        ).scalars().all()
        module_codes = [link.module_template_code for link in module_links if link.module_template_code]

        line_items = _parse_line_items(quote.line_items)
        quantity = None
        for item in line_items:
            if isinstance(item, dict) and item.get("quantity"):
                quantity = int(item["quantity"])
                break

        mapping = map_workspace_to_quote_input(
            payload,
            quantity=quantity,
            module_link_codes=module_codes,
        )
        product_spec_confirmed = build_product_spec_proposal(payload, include_unconfirmed_groups=False)
        product_spec_all = build_product_spec_proposal(payload, include_unconfirmed_groups=True)

        normalized_quote_input = normalize_volumetric_quote_input_from_finish_assignments(
            mapping.quote_input,
            product_spec=product_spec_confirmed if product_spec_confirmed.get("letterGroupFinishAssignments") else product_spec_all,
        )

        report["proposed_quote_input"] = {
            "raw_mapped": mapping.quote_input,
            "normalized_with_product_spec": normalized_quote_input,
            "field_sources": _field_sources(mapping.field_provenance),
            "missing_fields": mapping.missing_fields,
            "blockers": mapping.blockers,
            "aliases_applied": mapping.aliases_applied,
            "finish_groups_summary": mapping.finish_groups_summary,
            "non_invented_confirmation": "All values sourced from workspace payload or product_template_module_links",
        }

        report["proposed_line_items"] = build_proposed_line_items_enrichment(
            line_items,
            normalized_quote_input,
            template_code=ws.template_code if ws else "TPL-VOLUMETRIC-LETTERS_v2",
            workspace_id=workspace_id or "",
        )

        report["proposed_workspace_payload_patches"] = build_workspace_payload_patches(payload)

        # Intake linkage
        existing_intake = None
        if quote.intake_id:
            row = await db.scalar(select(Intake_requests).where(Intake_requests.id == quote.intake_id))
            if row:
                existing_intake = {
                    "id": row.id,
                    "code": row.code,
                    "status": row.status,
                    "product_spec_json": bool(row.product_spec_json),
                    "quantity": row.quantity,
                }
        elif payload.get("intake_request_code"):
            row = await db.scalar(
                select(Intake_requests).where(Intake_requests.code == payload["intake_request_code"]).limit(1)
            )
            if row:
                existing_intake = {
                    "id": row.id,
                    "code": row.code,
                    "status": row.status,
                    "product_spec_json": bool(row.product_spec_json),
                    "quantity": row.quantity,
                }
        else:
            # Heuristic: IR-MQZVC33K from workspace history / orphan row
            row = await db.scalar(select(Intake_requests).where(Intake_requests.code == "IR-MQZVC33K").limit(1))
            if row:
                existing_intake = {
                    "id": row.id,
                    "code": row.code,
                    "status": row.status,
                    "product_spec_json": bool(row.product_spec_json),
                    "quantity": row.quantity,
                    "note": "orphan_candidate_not_linked_to_quote_4",
                }

        client = payload.get("client") if isinstance(payload.get("client"), dict) else {}
        report["intake_linkage_repair_plan"] = build_intake_linkage_repair_plan(
            quote_id=quote_id,
            quote_intake_id=quote.intake_id,
            quote_intake_code=quote.intake_code,
            workspace_id=workspace_id or "",
            workspace_code=ws.workspace_code if ws else "",
            template_code=ws.template_code if ws else "TPL-VOLUMETRIC-LETTERS_v2",
            client_name=str(client.get("client_name") or quote.client_name or ""),
            quantity=quantity or int(mapping.quote_input.get("quantity") or 1),
            existing_intake_row=existing_intake,
            product_spec_proposal=product_spec_all,
        )

        # WC_ASSEMBLY audit
        wc_rows = (await db.execute(select(Workcenter_rates))).scalars().all()
        wc_dicts = [
            {
                "code": r.code,
                "rate_per_hour": r.rate_per_hour,
                "status": r.status,
                "is_active": r.is_active,
            }
            for r in wc_rows
        ]
        report["wc_assembly_audit"] = audit_wc_assembly_rate(wc_dicts)

        # In-memory readiness (no DB write)
        template_code = ws.template_code if ws else "TPL-VOLUMETRIC-LETTERS_v2"
        in_memory: dict[str, Any] = {}

        bom_service = AggregateCostBomBuilderService(db)
        bom = await bom_service.build_preview(
            template_code,
            workspace_id=workspace_id,
            quote_input=normalized_quote_input,
        )
        if bom:
            in_memory["cost_bom"] = {
                "bom_status": _status_val(bom.bom_status),
                "missing_pricing_count": len(bom.missing_pricing or []),
                "missing_geometry": list(bom.missing_geometry or [])[:10],
                "missing_pricing": [
                    {"code": m.code, "reason": m.reason, "module": m.module_code}
                    for m in (bom.missing_pricing or [])[:10]
                ],
                "aggregate_cost_source": not bom.source_context.uses_parent_bom_as_structural_truth,
            }

        template_id = payload.get("product_binding", {}).get("template_id") if isinstance(payload.get("product_binding"), dict) else None
        if template_id:
            sim_service = ProductSystemCostSimulationService(db)
            sim = await sim_service.simulate(
                template_id=int(template_id),
                quantity=quantity or 1,
                quote_input=normalized_quote_input,
                pricing={"margin_pct": quote.margin_pct or 0},
                intake_id=existing_intake.get("id") if existing_intake else quote.intake_id,
                simulation_context={
                    "source": "step7e1_repair_dryrun",
                    "no_persist": True,
                    "quote_id": quote_id,
                },
            )
            in_memory["simulation"] = {
                "status": sim.status,
                "cost_engine_version": sim.cost_engine_version,
                "total_cost": (sim.cost_result or {}).get("total_cost"),
                "blocked_reasons": sim.blocked_reasons[:15],
                "blockers": sim.blockers[:15],
                "no_persist": sim.trace.get("no_persist"),
            }
            qg = (sim.readiness or {}).get("quote_gate") or {}
            in_memory["simulation"]["simulate_ready"] = qg.get("simulate_ready")
            in_memory["simulation"]["can_create_commercial_quote"] = qg.get("can_create_commercial_quote")

        report["in_memory_readiness_after_proposed_repair"] = in_memory

        # SQL plan (not executed)
        report["sql_update_plan"] = {
            "executed": False,
            "statements": [
                "-- 1. Backfill intake_requests.product_spec_json (if empty) OR link existing row",
                f"-- UPDATE intake_requests SET product_spec_json=..., status='ready_for_quote' WHERE id={existing_intake.get('id') if existing_intake else '<TBD>'};",
                f"-- 2. UPDATE quotes SET intake_id={existing_intake.get('id') if existing_intake else '<new_id>'}, line_items=<enriched_json> WHERE id={quote_id} AND status='draft' AND grand_total=0;",
                "-- 3. Optional workspace payload patches (client.width_mm sync, letter_face_area_m2 alias)",
                f"-- UPDATE intake_v6_workspaces SET payload_json=... WHERE id='{workspace_id}';",
                "-- 4. WC_ASSEMBLY rate via Pricing Registry admin (NOT script)",
                "-- DO NOT: POST /api/v1/entities/quotes/4/price",
            ],
        }

        # Remaining blockers synthesis
        remaining = list(mapping.blockers)
        remaining.extend(mapping.missing_fields)
        if mapping.finish_groups_summary.get("confirmed", 0) == 0:
            remaining.append("finish_groups_0_confirmed_requires_owner_confirmation")
        if not report["wc_assembly_audit"].get("wc_assembly_rate_valid"):
            remaining.append("WC_ASSEMBLY_rate_missing_or_zero")
        if report["wc_assembly_audit"].get("all_workcenter_rates_null"):
            remaining.append("all_workcenter_rates_null_in_registry")
        if quote.intake_id is None:
            remaining.append("quote_intake_id_null")
        if not product_spec_confirmed.get("letterGroupFinishAssignments"):
            remaining.append("product_spec_no_confirmed_finish_assignments")

        sim_total = (in_memory.get("simulation") or {}).get("total_cost")
        if sim_total is not None and float(sim_total or 0) <= 0:
            remaining.append("simulation_total_cost_zero_or_blocked")

        report["remaining_blockers_after_proposed_repair"] = sorted(set(remaining))

        # Verdict
        if remaining:
            if any(b in remaining for b in (
                "finish_groups_unconfirmed",
                "finish_groups_0_confirmed_requires_owner_confirmation",
                "product_spec_no_confirmed_finish_assignments",
            )):
                report["verdict"] = "NEEDS_OWNER_INPUT"
            else:
                report["verdict"] = "NEEDS_OWNER_INPUT" if len(remaining) <= 3 else "BLOCKED"
        else:
            report["verdict"] = "READY_FOR_APPLY_REPAIR"

        # Safety after
        quote_after = await db.scalar(select(Quotes).where(Quotes.id == quote_id))
        report["quote_after"] = {
            "status": quote_after.status if quote_after else None,
            "grand_total": quote_after.grand_total if quote_after else None,
        }
        report["db_unchanged"] = (
            report["quote_before"]["status"] == report["quote_after"]["status"]
            and report["quote_before"]["grand_total"] == report["quote_after"]["grand_total"]
        )
        report["safety"] = {
            "db_writes": False,
            "price_endpoint_called": False,
            "reprice_executed": False,
            "apply_executed": False,
        }

    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Step 7E.1 Quote 4 payload repair dry-run")
    parser.add_argument("--quote-id", type=int, default=4)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="NOT RUN in Step 7E.1 — requires owner GO + backup + transaction",
    )
    args = parser.parse_args()
    result = asyncio.run(run_dry_run(quote_id=args.quote_id, apply=args.apply))
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
