"""One-off: price WI-TEST-ANNES-001 volumetric letters without ACM panel."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from sqlalchemy import select  # noqa: E402

from core.database import db_manager  # noqa: E402
from data_models.product_contracts import PricingContext, QuotePricing  # noqa: E402
from models.intake_requests import Intake_requests  # noqa: E402
from models.product_templates import Product_templates  # noqa: E402
from models.quotes import Quotes  # noqa: E402
from services.product_readiness_service import ProductReadinessService  # noqa: E402
from services.quote_orchestrator import QuoteOrchestrator  # noqa: E402
from services.quotes import QuotesService  # noqa: E402
from services.volumetric_quote_ready_policy import evaluate_volumetric_quote_ready  # noqa: E402

TEMPLATE = "TPL-VOLUMETRIC-LETTERS"
INTAKE_CODE = "WI-TEST-ANNES-001"
QUOTE_CODE = "QT-TEST-ANNES-001"

QUOTE_INPUT = {
    "width_mm": 4000,
    "height_mm": 700,
    "depth_mm": 80,
    "letter_face_area_m2": 1.55,
    "letter_perimeter_m": 21.0,
    "letter_count": 23,
    "return_depth_mm": 80,
    "selected_psu_watts": 100,
    "psu_watts": 100,
    "led_module_count": 210,
    "mounting_template_area_m2": 0,
    "paint_tube_count": 1,
    "paint_ral_code": "RAL 3020",
    "face_finish_type": "oracal_651",
    "face_vinyl_color_code": "010",
    "face_vinyl_roll_width_mm": 1260,
    "mounting_system": "direct_wall",
    "mounting_template_enabled": False,
    "back_bevel_enabled": False,
}

PRODUCT_SPEC = {
    **QUOTE_INPUT,
    "vector_file_name": "annes-store-volumetric.svg",
    "vector_file_type": "svg",
    "vector_analysis_status": "manual_review_approved",
    "vector_manual_review_approved": True,
    "vector_geometry_analyzed": True,
    "vector_geometry_confidence": "high",
    "geometry_source": "manual_confirmed",
    "geometry_confirmed_for_file_name": "annes-store-volumetric.svg",
    "confirmed_template_code": TEMPLATE,
    "return_finish_system": "standard",
    "return_color": "white",
    "face_vinyl_enabled": True,
    "face_vinyl_series": "651",
    "face_vinyl_color_code": "010",
    "face_vinyl_color_label": "White",
    "face_vinyl_roll_width_mm": 1260,
    "visual_chamfer_included": True,
    "illumination_family": "front_lit",
    "illumination_type": "frontlit",
    "lighting_system_type": "led_strip",
    "led_strip_density": "60_led_per_m",
    "light_color": "warm",
    "psu_selection_mode": "auto",
    "psu_configuration": [100],
    "psu_allocation_status": "ok",
    "total_led_watts": 55.0,
    "required_psu_watts": 66.0,
    "psu_total_capacity_watts": 100.0,
    "notes": "Litere albe Oracal 651; A rosu RAL 3020. Fara panou Alucobond.",
}


async def main() -> None:
    await db_manager.ensure_initialized()
    if not db_manager.async_session_maker:
        raise RuntimeError("No async_session_maker")

    async with db_manager.async_session_maker() as session:
        tpl = (
            await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == TEMPLATE
                )
            )
        ).scalar_one_or_none()
        if tpl is None:
            print(json.dumps({"error": "template not found"}))
            return

        intake = (
            await session.execute(
                select(Intake_requests).where(Intake_requests.code == INTAKE_CODE)
            )
        ).scalar_one_or_none()
        if intake is None:
            print(json.dumps({"error": "intake not found"}))
            return

        intake.status = "ready_for_quote"
        intake.confirmed_template_code = TEMPLATE
        intake.confirmed_template_name = "Litere volumetrice luminoase"
        intake.dimensions = "4000x700mm"
        intake.quantity = 1
        intake.product_spec_json = json.dumps(PRODUCT_SPEC)
        await session.commit()
        await session.refresh(intake)

        pricing = QuotePricing(margin_pct=25.0, discount_pct=0.0, vat_pct=19.0)
        user_config = {
            "product_id": TEMPLATE,
            "quantity": 1,
            "dimensions": {"width_mm": 4000, "height_mm": 700, "depth_mm": 80},
        }
        orchestrator = await QuoteOrchestrator.create_with_registry(db=session)
        tpl_dict = {
            "id": tpl.id,
            "template_code": tpl.template_code,
            "family_id": tpl.family_id,
            "family_name": tpl.family_name,
            "description": tpl.description,
            "components_json": tpl.components_json,
            "operations_json": tpl.operations_json,
            "required_materials_json": tpl.required_materials_json,
        }
        snapshot = orchestrator.build_snapshot(
            product_template=tpl_dict,
            user_config=user_config,
            pricing=pricing,
            pricing_context=PricingContext(),
            quote_input=QUOTE_INPUT,
        )
        snapshot.template_id = tpl.id

        readiness = await ProductReadinessService(session).evaluate(
            tpl.id, product_spec=PRODUCT_SPEC
        )
        readiness_dict = readiness.to_dict()
        quote_gate = evaluate_volumetric_quote_ready(
            template_code=tpl.template_code,
            template_active=bool(tpl.active),
            readiness_dict=readiness_dict,
            cost_blockers=list(snapshot.blocked_reasons or []),
            quote_input=QUOTE_INPUT,
            product_spec=PRODUCT_SPEC,
        )

        result: dict = {
            "intake_code": INTAKE_CODE,
            "status": snapshot.status,
            "blocked_reasons": list(snapshot.blocked_reasons or []),
            "net_eur": float(snapshot.price.net) if snapshot.price.net else None,
            "gross_eur": float(snapshot.price.gross) if snapshot.price.gross else None,
            "margin_pct": float(snapshot.pricing.margin_pct),
            "vat_pct": float(snapshot.pricing.vat_pct),
            "ready_for_quote": quote_gate.can_create_commercial_quote,
            "quote_gate_warnings": list(quote_gate.warnings or []),
            "quote_gate_blockers": list(quote_gate.blockers or []),
            "quote_input": QUOTE_INPUT,
        }

        cost_dict = snapshot.cost_result.to_dict() if snapshot.cost_result else {}
        breakdown = cost_dict.get("component_breakdown") or []
        if breakdown:
            result["line_items"] = [
                {
                    "label": li.get("label") or li.get("name") or li.get("component_id"),
                    "total": li.get("total") or li.get("line_total") or li.get("cost"),
                }
                for li in breakdown[:12]
            ]

        if snapshot.status == "priced" and snapshot.price.net is not None:
            quotes_service = QuotesService(session)
            existing = (
                await session.execute(
                    select(Quotes).where(Quotes.code == QUOTE_CODE)
                )
            ).scalar_one_or_none()
            valid_until = (datetime.now(timezone.utc) + timedelta(days=30)).date().isoformat()
            snapshot_dict = snapshot.to_dict()
            snapshot_dict["readiness_result"] = readiness_dict
            line_items_str = json.dumps(
                {"line_items": snapshot_dict, "readiness_result": readiness_dict},
                ensure_ascii=False,
            )
            quote_data = {
                "code": QUOTE_CODE,
                "intake_id": intake.id,
                "intake_code": intake.code,
                "client_name": intake.client_name,
                "status": "priced",
                "version": 1,
                "valid_until": valid_until,
                "line_items": line_items_str,
                "subtotal": float(snapshot.price.net),
                "grand_total": float(snapshot.price.gross),
                "margin_pct": float(snapshot.pricing.margin_pct),
                "discount_pct": float(snapshot.pricing.discount_pct),
                "vat": float(snapshot.pricing.vat_pct),
                "total_before_vat": float(snapshot.price.net),
                "notes": "Anne's Store — litere volumetrice 4000x700, fara panou Alucobond",
            }
            if existing:
                await quotes_service.update(existing.id, quote_data)
                result["quote_code"] = QUOTE_CODE
                result["quote_id"] = existing.id
                result["action"] = "updated"
            else:
                created = await quotes_service.create(quote_data)
                result["quote_code"] = QUOTE_CODE
                result["quote_id"] = created.id if created else None
                result["action"] = "created"

        out_path = os.path.join(_BACKEND_ROOT, "..", "annes-quote-result.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
