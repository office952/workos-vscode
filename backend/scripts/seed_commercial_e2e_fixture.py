"""
seed_commercial_e2e_fixture.py — BUILD-COMMERCIAL-E2E-FIXTURE

Creates a deterministic dev-db fixture for Playwright commercial spine E2E:
  TPL-VOLUMETRIC-LETTERS intake → priced quote (db source) → ready for UI convert.

Scope boundaries (enforced):
  - Does NOT modify CostEngine, pricing semantics, or status lifecycle rules.
  - Does NOT activate unsupported templates.
  - Does NOT touch WI-SMOKE-P001 baseline intake.
  - Only INSERTS/updates E2E-scoped rows (WI-E2E-COMMERCIAL-001, QT-E2E-COMMERCIAL-001,
    WI-E2E-GEOMETRY-SMOKE-001, and related WARN/FINISH-DISPLAY fixtures).
  - Deletes only orders linked to the E2E fixture quote (idempotent re-run).

Usage:
    cd backend
    python scripts/seed_commercial_e2e_fixture.py

Output:
    Writes frontend/e2e/.commercial-fixture.json manifest and prints JSON summary.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

_BACKEND_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)

from sqlalchemy import delete, select  # noqa: E402

from core.database import db_manager  # noqa: E402
from data_models.product_contracts import PricingContext, QuotePricing  # noqa: E402
from models.execution_plan import ExecutionPlan  # noqa: E402
from models.execution_reality import ExecutionReality  # noqa: E402
from models.intake_requests import Intake_requests  # noqa: E402
from models.orders import Orders  # noqa: E402
from models.product_templates import Product_templates  # noqa: E402
from models.quotes import Quotes  # noqa: E402
from services.product_readiness_service import ProductReadinessService  # noqa: E402
from services.quote_orchestrator import QuoteOrchestrator  # noqa: E402
from services.quotes import QuotesService  # noqa: E402
from services.volumetric_quote_ready_policy import evaluate_volumetric_quote_ready  # noqa: E402

logger = logging.getLogger(__name__)

FIXTURE_INTAKE_CODE = "WI-E2E-COMMERCIAL-001"
FIXTURE_QUOTE_CODE = "QT-E2E-COMMERCIAL-001"
FIXTURE_WARN_INTAKE_CODE = "WI-E2E-COMMERCIAL-WARN-001"
FIXTURE_WARN_QUOTE_CODE = "QT-E2E-COMMERCIAL-WARN-001"
FIXTURE_FINISH_DISPLAY_INTAKE_CODE = "WI-E2E-WORKINTAKE-V2-FINISH-DISPLAY-001"
FIXTURE_GEOMETRY_SMOKE_INTAKE_CODE = "WI-E2E-GEOMETRY-SMOKE-001"
FIXTURE_CLIENT = "E2E Commercial Spine Client"
TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"

# Three-layer Cadru / Litere / Emblema — matches live WARN/FINISH-DISPLAY tablet layout.
LAYERS_CADRU_LITERE_EMBLEMA: list[Dict[str, Any]] = [
    {
        "id": "Cadru",
        "label": "Cadru",
        "element_count": 10,
        "suggested_role": "metal_frame",
        "confirmed_role": "metal_frame",
    },
    {
        "id": "Litere_x0020_volumetrice",
        "label": "Litere_x0020_volumetrice",
        "element_count": 2,
        "suggested_role": "volumetric_letters",
        "confirmed_role": "volumetric_letters",
    },
    {
        "id": "Emblema",
        "label": "Emblema",
        "element_count": 510,
        "suggested_role": "unknown",
        "confirmed_role": "unknown",
    },
]

LAYERS_LITERE_DIBOND_CADRU: list[Dict[str, Any]] = [
    {
        "id": "LITERE",
        "label": "LITERE",
        "element_count": 2,
        "suggested_role": "volumetric_letters",
        "confirmed_role": "volumetric_letters",
    },
    {
        "id": "DIBOND",
        "label": "DIBOND",
        "element_count": 1,
        "suggested_role": "support_panel",
        "confirmed_role": "support_panel",
    },
    {
        "id": "CADRU",
        "label": "CADRU",
        "element_count": 1,
        "suggested_role": "metal_frame",
        "confirmed_role": "metal_frame",
    },
]

PRIMARY_LITERE_VOLUMETRICE_ID = "Litere_x0020_volumetrice"
PRIMARY_LITERE_VOLUMETRICE_NAME = "Litere_x0020_volumetrice"
PRIMARY_LITERE_ID = "LITERE"
PRIMARY_LITERE_NAME = "LITERE"

MANIFEST_PATH = (
    Path(_BACKEND_ROOT).parent / "frontend" / "e2e" / ".commercial-fixture.json"
)

BASE_QUOTE_INPUT: Dict[str, Any] = {
    "width_mm": 4800,
    "height_mm": 600,
    "depth_mm": 60,
    "letter_face_area_m2": 2.88,
    "letter_perimeter_m": 18.0,
    "letter_count": 9,
    "return_depth_mm": 60,
    "selected_psu_watts": 100,
    "psu_watts": 100,
    "led_module_count": 180,
    "mounting_template_area_m2": 2.88,
    "paint_tube_count": 3,
    "paint_ral_code": "RAL 9005",
    "face_finish_type": "none",
    "mounting_system": "direct_wall",
    "mounting_template_enabled": True,
    "back_bevel_enabled": False,
}

PRODUCT_SPEC_BASE: Dict[str, Any] = {
    **BASE_QUOTE_INPUT,
    "vector_file_type": "svg",
    "vector_analysis_status": "manual_review_approved",
    "vector_manual_review_approved": True,
    "vector_geometry_analyzed": True,
    "vector_geometry_confidence": "high",
    "geometry_source": "svg_suggestion_confirmed",
    "confirmed_template_code": TEMPLATE_CODE,
}

SVG_LAYER_MAPPINGS_CADRU_LITERE: Dict[str, str] = {
    "Layer_x0020_1": TEMPLATE_CODE,
    "Litere_x0020_Volumetrice": TEMPLATE_CODE,
    "Structura_x0020_metalca": "support_bars",
    "Cadru": "support_bars",
    "Litere_x0020_volumetrice": TEMPLATE_CODE,
}

SVG_LAYER_MAPPINGS_LITERE_DIBOND: Dict[str, str] = {
    "LITERE": TEMPLATE_CODE,
    "DIBOND": "support_bars",
    "CADRU": "support_bars",
    "Litere_x0020_Volumetrice": TEMPLATE_CODE,
    "Structura_x0020_metalca": "support_bars",
}


def _layers_summary_cadru_litere() -> list[Dict[str, Any]]:
    return [
        {
            "layer_name": "Cadru",
            "mapping_status": "mapped_manual",
            "mapped_by": "manual",
            "mapped_target": "support_bars",
            "detected_kind": "metal_frame",
        },
        {
            "layer_name": "Litere_x0020_volumetrice",
            "mapping_status": "mapped_manual",
            "mapped_by": "manual",
            "mapped_target": TEMPLATE_CODE,
            "mapped_template_code": TEMPLATE_CODE,
            "detected_kind": "volumetric_letters",
        },
        {
            "layer_name": "Emblema",
            "mapping_status": "unmapped",
        },
    ]


def _layers_summary_litere_dibond() -> list[Dict[str, Any]]:
    return [
        {
            "layer_name": "LITERE",
            "mapping_status": "mapped_manual",
            "mapped_by": "manual",
            "mapped_target": TEMPLATE_CODE,
            "mapped_template_code": TEMPLATE_CODE,
            "detected_kind": "volumetric_letters",
        },
        {
            "layer_name": "DIBOND",
            "mapping_status": "mapped_manual",
            "mapped_by": "manual",
            "mapped_target": "support_bars",
            "detected_kind": "support_panel",
        },
        {
            "layer_name": "CADRU",
            "mapping_status": "mapped_manual",
            "mapped_by": "manual",
            "mapped_target": "support_bars",
            "detected_kind": "metal_frame",
        },
    ]


def _enrich_parsed_vector_spec(
    base: Dict[str, Any],
    *,
    file_name: str,
    layers: list[Dict[str, Any]],
    primary_id: str,
    primary_name: str,
    svg_layer_mappings: Dict[str, str],
    layers_summary: list[Dict[str, Any]],
    viewbox: str,
    width_mm: float,
    height_mm: float,
    file_size_bytes: int = 2048,
    selected_at: str = "2026-01-01T00:00:00.000Z",
) -> Dict[str, Any]:
    """Attach parsed SVG/layer tablet fields — idempotent fixture enrichment."""
    return {
        **base,
        "vector_file_name": file_name,
        "vector_file_mime": "image/svg+xml",
        "vector_file_extension": "svg",
        "vector_file_selected_at": selected_at,
        "vector_file_size_bytes": file_size_bytes,
        "vector_svg_viewbox": viewbox,
        "vector_svg_width": f"{width_mm}mm",
        "vector_svg_height": f"{height_mm}mm",
        "width_mm": width_mm,
        "height_mm": height_mm,
        "letter_height_mm": height_mm,
        "vector_parse_status": "parsed",
        "vector_svg_analyzed": True,
        "vector_metrics_source": "svg_analysis",
        "vector_layer_alignment_status": "aligned",
        "vector_layer_mapping_status": "mapped",
        "vector_detected_layer_count": len(layers),
        "vector_detected_layers": layers,
        "vector_detected_layers_summary": layers_summary,
        "vector_primary_letters_layer_id": primary_id,
        "vector_primary_letters_layer_name": primary_name,
        "vector_layer_mapping_confirmed": True,
        "geometry_confirmed_for_file_name": file_name,
        "svg_layer_mappings": svg_layer_mappings,
        "vector_file_present": True,
        "vector_file_source": "server_upload",
    }


COMMERCIAL_E2E_PARSED_SPEC: Dict[str, Any] = _enrich_parsed_vector_spec(
    PRODUCT_SPEC_BASE,
    file_name="e2e-volumetric-letters.svg",
    layers=LAYERS_CADRU_LITERE_EMBLEMA,
    primary_id=PRIMARY_LITERE_VOLUMETRICE_ID,
    primary_name=PRIMARY_LITERE_VOLUMETRICE_NAME,
    svg_layer_mappings=SVG_LAYER_MAPPINGS_CADRU_LITERE,
    layers_summary=_layers_summary_cadru_litere(),
    viewbox="0 0 365.97667 80.08659",
    width_mm=BASE_QUOTE_INPUT["width_mm"],
    height_mm=BASE_QUOTE_INPUT["height_mm"],
)

WARN_E2E_PARSED_SPEC: Dict[str, Any] = _enrich_parsed_vector_spec(
    PRODUCT_SPEC_BASE,
    file_name="pbl-color.svg",
    layers=LAYERS_CADRU_LITERE_EMBLEMA,
    primary_id=PRIMARY_LITERE_VOLUMETRICE_ID,
    primary_name=PRIMARY_LITERE_VOLUMETRICE_NAME,
    svg_layer_mappings=SVG_LAYER_MAPPINGS_CADRU_LITERE,
    layers_summary=_layers_summary_cadru_litere(),
    viewbox="0 0 365.97667 80.08659",
    width_mm=3499.999085,
    height_mm=414.40878,
    file_size_bytes=61347,
    selected_at="2026-06-11T19:59:13.630934+00:00",
)

# Back-compat alias for pricing helpers that referenced PRODUCT_SPEC.
PRODUCT_SPEC: Dict[str, Any] = COMMERCIAL_E2E_PARSED_SPEC

# WorkIntake V2 → QuoteWizard finish-display smoke: prerequisites complete, colors left for UI.
WORKINTAKE_V2_FINISH_DISPLAY_SPEC: Dict[str, Any] = {
    **_enrich_parsed_vector_spec(
        PRODUCT_SPEC_BASE,
        file_name="pbl-color.svg",
        layers=LAYERS_CADRU_LITERE_EMBLEMA,
        primary_id=PRIMARY_LITERE_VOLUMETRICE_ID,
        primary_name=PRIMARY_LITERE_VOLUMETRICE_NAME,
        svg_layer_mappings=SVG_LAYER_MAPPINGS_CADRU_LITERE,
        layers_summary=_layers_summary_cadru_litere(),
        viewbox="0 0 365.97667 80.08659",
        width_mm=3499.999085,
        height_mm=414.40878,
        file_size_bytes=61347,
        selected_at="2026-01-01T00:00:00.000Z",
    ),
    "return_depth_mm": 80,
    "depth_mm": 80,
    "return_finish_system": "standard",
    "return_color": "white",
    "face_vinyl_enabled": False,
    "visual_chamfer_included": True,
    "illumination_family": "front_lit",
    "illumination_type": "frontlit",
    "lighting_system_type": "led_strip",
    "led_strip_density": "60_led_per_m",
    "light_color": "warm",
    "psu_selection_mode": "auto",
    "psu_configuration": [100],
    "psu_allocation_status": "ok",
    "total_led_watts": 50.0,
    "required_psu_watts": 60.0,
    "psu_total_capacity_watts": 100.0,
    "selected_psu_watts": 100,
}

# Canonical geometry smoke fixture (derived from backup IR-MQ3C869E — not IR-M3Q8C69E typo).
GEOMETRY_SMOKE_E2E_SPEC: Dict[str, Any] = {
    **_enrich_parsed_vector_spec(
        PRODUCT_SPEC_BASE,
        file_name="workos-geometry-smoke.svg",
        layers=LAYERS_LITERE_DIBOND_CADRU,
        primary_id=PRIMARY_LITERE_ID,
        primary_name=PRIMARY_LITERE_NAME,
        svg_layer_mappings=SVG_LAYER_MAPPINGS_LITERE_DIBOND,
        layers_summary=_layers_summary_litere_dibond(),
        viewbox="0 0 1000 200",
        width_mm=1000.0,
        height_mm=200.0,
        file_size_bytes=330,
        selected_at="2026-06-07T10:21:53.444Z",
    ),
    "vector_geometry_parser_version": "mvp-1",
    "vector_suggested_assembly_width_mm": 1000.0,
    "vector_suggested_assembly_height_mm": 200.0,
    "vector_suggested_letter_layer_width_mm": 500.0,
    "vector_suggested_letter_layer_height_mm": 160.0,
    "vector_suggested_support_width_mm": 1000.0,
    "vector_suggested_support_height_mm": 200.0,
    "vector_suggested_support_area_m2": 0.2,
    "vector_suggested_frame_width_mm": 980.0,
    "vector_suggested_frame_height_mm": 180.0,
    "vector_suggested_letter_element_count": 2.0,
    "letter_count": 2,
    "letter_perimeter_m": 12.0,
    "letter_face_area_m2": 0.8,
    "mounting_template_area_m2": 0.2,
    "vector_fast_ask_applied_at": "2026-06-07T08:43:46.963Z",
    "vector_geometry_warnings": [
        "Aria suportului este estimare bounding-box, nu contur real.",
        "Număr elemente ≠ număr litere — confirmă manual înainte de aplicare.",
        "Perimetrul și aria literelor nu pot fi calculate sigur în MVP. Confirmă manual.",
    ],
    "volume_finish": "paint_after_face_miter_bond",
    "face_finish": "oracal_651",
    "face_finish_type": "oracal_651",
    "mounting_template_enabled": True,
    "intake_input_pathway": "vector",
    "vector_file_source": "local_manual",
}

def _inject_operations_missing_warning(readiness_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic ack-pending warning without hard blockers (unit/E2E ack path)."""
    out = dict(readiness_dict)
    tech = dict(out.get("technical_readiness") or {})
    warnings = list(tech.get("warnings") or [])
    if "operations_missing" not in warnings:
        warnings.append("operations_missing")
    tech["warnings"] = warnings
    tech.setdefault("status", "needs_review")
    tech.setdefault("blockers", [])
    out["technical_readiness"] = tech
    if str(out.get("overall_status") or "") not in {"blocked", "draft"}:
        out["overall_status"] = "needs_review"
    return out


def _build_live_readiness_snapshot(
    readiness_dict: Dict[str, Any],
    quote_gate: Any,
    *,
    template_id: int,
) -> Dict[str, Any]:
    """Persist real ProductReadiness + volumetric quote_gate — no E2E overlay."""
    quote_gate_dict = quote_gate.to_dict()
    requires_ack = bool(quote_gate_dict.get("requires_acknowledgement"))
    return {
        **readiness_dict,
        "entity_id": f"blueprint:{template_id}",
        "blueprint_id": f"template:{template_id}",
        "quote_gate": quote_gate_dict,
        "ready_for_quote": bool(quote_gate_dict.get("ready_for_quote")),
        "policy": {
            "authority": "backend",
            "requires_warning_acknowledgement": requires_ack,
            "quote_gate": "enforced",
        },
        "contract_version": "2026-05-15",
        "source": "backend",
    }


async def _ensure_prerequisites() -> None:
    """Idempotent volumetric commercial prerequisites for dev/local DB."""
    from seeds.seed_active_template_scope import seed_active_template_scope
    from seeds.seed_build4_templates import seed_build4_templates
    from seeds.seed_tpl_volumetric_letters_dossier import seed_tpl_volumetric_letters_dossier
    from seeds.seed_volumetric_owner_confirmed_prices import seed_volumetric_owner_confirmed_prices
    from seeds.seed_volumetric_workcenter_rates import seed_volumetric_operations_and_rates

    await seed_build4_templates()
    await seed_volumetric_operations_and_rates()
    await seed_volumetric_owner_confirmed_prices()
    await seed_tpl_volumetric_letters_dossier()
    await seed_active_template_scope()


def _template_dict(tpl: Product_templates) -> Dict[str, Any]:
    return {
        "id": tpl.id,
        "template_code": tpl.template_code,
        "family_id": tpl.family_id,
        "family_name": tpl.family_name,
        "description": tpl.description,
        "components_json": tpl.components_json,
        "operations_json": tpl.operations_json,
        "required_materials_json": tpl.required_materials_json,
        "estimated_hours": tpl.estimated_hours,
        "base_labor_rate": tpl.base_labor_rate,
        "base_margin_pct": tpl.base_margin_pct,
        "active": bool(tpl.active),
    }


def _serialize_line_items(snapshot, *, readiness_result: Dict[str, Any]) -> str:
    snapshot_dict = snapshot.to_dict()
    snapshot_dict["readiness_result"] = readiness_result
    breakdown_payload = None
    try:
        breakdown_json = getattr(snapshot, "component_breakdown_json", None)
        if breakdown_json:
            parsed = (
                json.loads(breakdown_json)
                if isinstance(breakdown_json, str)
                else breakdown_json
            )
            if isinstance(parsed, list) and len(parsed) > 0:
                breakdown_payload = parsed
    except Exception as exc:
        logger.warning("component_breakdown_json parse failed: %s", exc)

    wrapper: Dict[str, Any] = {
        "line_items": snapshot_dict,
        "readiness_result": readiness_result,
    }
    if breakdown_payload is not None:
        wrapper["component_breakdown"] = breakdown_payload
    warnings = getattr(snapshot, "cost_warnings", None)
    if isinstance(warnings, list) and len(warnings) > 0:
        wrapper["cost_warnings"] = warnings
    return json.dumps(wrapper)


async def _load_template(session) -> Product_templates:
    row = (
        await session.execute(
            select(Product_templates).where(
                Product_templates.template_code == TEMPLATE_CODE
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise RuntimeError(
            f"{TEMPLATE_CODE} not found in DB — run volumetric seeds first."
        )
    if not row.active:
        raise RuntimeError(
            f"{TEMPLATE_CODE} is inactive — active template scope seed required."
        )
    return row


async def _ensure_intake(session) -> Intake_requests:
    existing = (
        await session.execute(
            select(Intake_requests).where(Intake_requests.code == FIXTURE_INTAKE_CODE)
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.status = "ready_for_quote"
        existing.product_family = "litere_volumetrice"
        existing.confirmed_template_code = TEMPLATE_CODE
        existing.confirmed_template_name = "Litere volumetrice luminoase"
        existing.product_spec_json = json.dumps(COMMERCIAL_E2E_PARSED_SPEC)
        existing.client_name = FIXTURE_CLIENT
        existing.description = "E2E commercial spine fixture — TPL-VOLUMETRIC-LETTERS"
        await session.commit()
        await session.refresh(existing)
        return existing

    intake = Intake_requests(
        code=FIXTURE_INTAKE_CODE,
        client_id=1,
        client_name=FIXTURE_CLIENT,
        contact_person="E2E Validator",
        channel="email",
        product_family="litere_volumetrice",
        description="E2E commercial spine fixture — TPL-VOLUMETRIC-LETTERS",
        dimensions="4800x600mm",
        quantity=1,
        status="ready_for_quote",
        assigned_to="e2e",
        priority="low",
        delivery_type="courier",
        confirmed_template_code=TEMPLATE_CODE,
        confirmed_template_name="Litere volumetrice luminoase",
        product_spec_json=json.dumps(COMMERCIAL_E2E_PARSED_SPEC),
        notes="Seeded by scripts/seed_commercial_e2e_fixture.py — do not use in production.",
    )
    session.add(intake)
    await session.commit()
    await session.refresh(intake)
    return intake


async def _reset_fixture_orders(session, quote_id: int) -> int:
    order_ids = (
        await session.execute(select(Orders.id).where(Orders.quote_id == quote_id))
    ).scalars().all()
    if order_ids:
        await session.execute(
            delete(ExecutionReality).where(ExecutionReality.order_id.in_(order_ids))
        )
        await session.execute(
            delete(ExecutionPlan).where(ExecutionPlan.order_id.in_(order_ids))
        )
    result = await session.execute(delete(Orders).where(Orders.quote_id == quote_id))
    await session.commit()
    return int(result.rowcount or 0)


async def _price_fixture_quote(
    session,
    *,
    intake: Intake_requests,
    tpl: Product_templates,
    existing_quote: Optional[Quotes],
    quote_code: str = FIXTURE_QUOTE_CODE,
    product_spec: Optional[Dict[str, Any]] = None,
    quote_input: Optional[Dict[str, Any]] = None,
    readiness_mutator: Optional[Any] = None,
    require_ack: bool = False,
) -> tuple[Quotes, Any]:
    fixture_spec = product_spec or COMMERCIAL_E2E_PARSED_SPEC
    fixture_quote_input = quote_input or BASE_QUOTE_INPUT
    pricing = QuotePricing(margin_pct=25.0, discount_pct=0.0, vat_pct=19.0)
    pricing_ctx = PricingContext()
    user_config = {
        "product_id": TEMPLATE_CODE,
        "quantity": 1,
        "dimensions": {
            "width_mm": BASE_QUOTE_INPUT["width_mm"],
            "height_mm": BASE_QUOTE_INPUT["height_mm"],
            "depth_mm": BASE_QUOTE_INPUT["depth_mm"],
        },
    }

    orchestrator = await QuoteOrchestrator.create_with_registry(db=session)
    snapshot = orchestrator.build_snapshot(
        product_template=_template_dict(tpl),
        user_config=user_config,
        pricing=pricing,
        pricing_context=pricing_ctx,
        quote_input=fixture_quote_input,
    )
    snapshot.template_id = tpl.id

    if snapshot.status == "blocked":
        raise RuntimeError(
            f"Fixture pricing blocked: {list(snapshot.blocked_reasons or [])}"
        )

    if snapshot.status != "priced":
        raise RuntimeError(f"Unexpected snapshot status: {snapshot.status}")

    if snapshot.price.net is None or snapshot.price.gross is None:
        raise RuntimeError("Priced snapshot missing commercial totals")

    readiness_eval = await ProductReadinessService(session).evaluate(
        tpl.id, product_spec=fixture_spec
    )
    readiness_dict = readiness_eval.to_dict()
    if readiness_mutator is not None:
        readiness_dict = readiness_mutator(readiness_dict)
    quote_gate = evaluate_volumetric_quote_ready(
        template_code=tpl.template_code,
        template_active=bool(tpl.active),
        readiness_dict=readiness_dict,
        cost_blockers=list(snapshot.blocked_reasons or []),
        quote_input=fixture_quote_input,
        product_spec=fixture_spec,
    )
    if not quote_gate.can_create_commercial_quote:
        raise RuntimeError(
            f"Fixture quote gate blocked ({quote_code}) — cannot seed without overlay. "
            f"blockers={list(quote_gate.blockers or [])}"
        )
    if require_ack and not quote_gate.requires_acknowledgement:
        raise RuntimeError(
            f"Fixture {quote_code} expected requires_acknowledgement=true, "
            f"got false (ack_pending={list(quote_gate.classified.get('acknowledgement_pending', []))})"
        )

    readiness_snapshot = _build_live_readiness_snapshot(
        readiness_dict,
        quote_gate,
        template_id=tpl.id,
    )
    line_items_str = _serialize_line_items(
        snapshot, readiness_result=readiness_snapshot
    )
    valid_until = (datetime.now(timezone.utc) + timedelta(days=30)).strftime("%Y-%m-%d")
    quotes_service = QuotesService(session)

    if existing_quote is not None:
        await quotes_service.update(
            existing_quote.id,
            {
                "code": quote_code,
                "intake_id": intake.id,
                "intake_code": intake.code,
                "client_name": intake.client_name or FIXTURE_CLIENT,
                "contact_person": intake.contact_person,
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
                "notes": f"E2E commercial fixture — {TEMPLATE_CODE}",
            },
        )
        refreshed = await quotes_service.get_by_id(existing_quote.id)
        if refreshed is None:
            raise RuntimeError("Failed to refresh fixture quote after update")
        return refreshed, quote_gate

    quote_data = {
        "code": quote_code,
        "intake_id": intake.id,
        "intake_code": intake.code,
        "client_id": intake.client_id,
        "client_name": intake.client_name or FIXTURE_CLIENT,
        "contact_person": intake.contact_person,
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
        "notes": f"E2E commercial fixture — {TEMPLATE_CODE}",
        "assigned_to": intake.assigned_to,
    }
    created = await quotes_service.create(quote_data)
    if created is None:
        raise RuntimeError("Fixture quote persistence failed")
    return created, quote_gate


async def _ensure_finish_display_intake(session) -> Intake_requests:
    """Intake-only fixture for WorkIntake V2 → QuoteWizard finish display E2E."""
    existing = (
        await session.execute(
            select(Intake_requests).where(
                Intake_requests.code == FIXTURE_FINISH_DISPLAY_INTAKE_CODE
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.status = "ready_for_quote"
        existing.product_family = "litere_volumetrice"
        existing.confirmed_template_code = TEMPLATE_CODE
        existing.confirmed_template_name = "Litere volumetrice luminoase"
        existing.product_spec_json = json.dumps(WORKINTAKE_V2_FINISH_DISPLAY_SPEC)
        existing.client_name = f"{FIXTURE_CLIENT} (Finish Display)"
        existing.description = (
            "E2E WorkIntake V2 finish display smoke — geometry/PSU pre-valid, colors in UI"
        )
        await session.commit()
        await session.refresh(existing)
        return existing

    intake = Intake_requests(
        code=FIXTURE_FINISH_DISPLAY_INTAKE_CODE,
        client_id=1,
        client_name=f"{FIXTURE_CLIENT} (Finish Display)",
        contact_person="E2E Validator",
        channel="email",
        product_family="litere_volumetrice",
        description=(
            "E2E WorkIntake V2 finish display smoke — geometry/PSU pre-valid, colors in UI"
        ),
        dimensions="4800x600mm",
        quantity=1,
        status="ready_for_quote",
        assigned_to="e2e",
        priority="low",
        delivery_type="courier",
        confirmed_template_code=TEMPLATE_CODE,
        confirmed_template_name="Litere volumetrice luminoase",
        product_spec_json=json.dumps(WORKINTAKE_V2_FINISH_DISPLAY_SPEC),
        notes="Seeded finish-display intake — WorkIntake V2 → QuoteWizard E2E only.",
    )
    session.add(intake)
    await session.commit()
    await session.refresh(intake)
    return intake


async def _ensure_warn_intake(session) -> Intake_requests:
    existing = (
        await session.execute(
            select(Intake_requests).where(Intake_requests.code == FIXTURE_WARN_INTAKE_CODE)
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.status = "ready_for_quote"
        existing.product_family = "litere_volumetrice"
        existing.confirmed_template_code = TEMPLATE_CODE
        existing.confirmed_template_name = "Litere volumetrice luminoase"
        existing.product_spec_json = json.dumps(WARN_E2E_PARSED_SPEC)
        existing.client_name = f"{FIXTURE_CLIENT} (WARN)"
        existing.description = "E2E commercial warn-ack fixture — operations_missing pending"
        await session.commit()
        await session.refresh(existing)
        return existing

    intake = Intake_requests(
        code=FIXTURE_WARN_INTAKE_CODE,
        client_id=1,
        client_name=f"{FIXTURE_CLIENT} (WARN)",
        contact_person="E2E Validator",
        channel="email",
        product_family="litere_volumetrice",
        description="E2E commercial warn-ack fixture — operations_missing pending",
        dimensions="4800x600mm",
        quantity=1,
        status="ready_for_quote",
        assigned_to="e2e",
        priority="low",
        delivery_type="courier",
        confirmed_template_code=TEMPLATE_CODE,
        confirmed_template_name="Litere volumetrice luminoase",
        product_spec_json=json.dumps(WARN_E2E_PARSED_SPEC),
        notes="Seeded warn-ack variant — acknowledgement required at convert.",
    )
    session.add(intake)
    await session.commit()
    await session.refresh(intake)
    return intake


async def _ensure_geometry_smoke_intake(session) -> Intake_requests:
    """Intake-only canonical geometry smoke (backup IR-MQ3C869E lineage)."""
    existing = (
        await session.execute(
            select(Intake_requests).where(
                Intake_requests.code == FIXTURE_GEOMETRY_SMOKE_INTAKE_CODE
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        existing.status = "in_review"
        existing.product_family = "litere_volumetrice"
        existing.confirmed_template_code = TEMPLATE_CODE
        existing.confirmed_template_name = "Litere volumetrice luminoase"
        existing.product_spec_json = json.dumps(GEOMETRY_SMOKE_E2E_SPEC)
        existing.client_name = f"{FIXTURE_CLIENT} (Geometry Smoke)"
        existing.description = (
            "E2E geometry smoke — 3 layers LITERE/DIBOND/CADRU, volumetric finish sample"
        )
        await session.commit()
        await session.refresh(existing)
        return existing

    intake = Intake_requests(
        code=FIXTURE_GEOMETRY_SMOKE_INTAKE_CODE,
        client_id=1,
        client_name=f"{FIXTURE_CLIENT} (Geometry Smoke)",
        contact_person="E2E Validator",
        channel="email",
        product_family="litere_volumetrice",
        description=(
            "E2E geometry smoke — 3 layers LITERE/DIBOND/CADRU, volumetric finish sample"
        ),
        dimensions="1000x200mm",
        quantity=1,
        status="in_review",
        assigned_to="e2e",
        priority="low",
        delivery_type="courier",
        confirmed_template_code=TEMPLATE_CODE,
        confirmed_template_name="Litere volumetrice luminoase",
        product_spec_json=json.dumps(GEOMETRY_SMOKE_E2E_SPEC),
        notes=(
            "Seeded geometry smoke — derived from backup IR-MQ3C869E "
            "(owner IR-M3Q8C69E typo); SVG in frontend/e2e/fixtures/workos-geometry-smoke.svg."
        ),
    )
    session.add(intake)
    await session.commit()
    await session.refresh(intake)
    return intake


async def seed() -> Dict[str, Any]:
    await db_manager.ensure_initialized()
    if not db_manager.async_session_maker:
        raise RuntimeError("No async_session_maker — check DATABASE_URL / dev DB.")

    await _ensure_prerequisites()

    async with db_manager.async_session_maker() as session:
        tpl = await _load_template(session)
        intake = await _ensure_intake(session)

        existing_quote = (
            await session.execute(
                select(Quotes).where(Quotes.code == FIXTURE_QUOTE_CODE)
            )
        ).scalar_one_or_none()

        deleted_orders = 0
        if existing_quote is not None:
            deleted_orders = await _reset_fixture_orders(session, existing_quote.id)

        quote, quote_gate = await _price_fixture_quote(
            session,
            intake=intake,
            tpl=tpl,
            existing_quote=existing_quote,
            product_spec=COMMERCIAL_E2E_PARSED_SPEC,
        )

        warn_intake = await _ensure_warn_intake(session)
        existing_warn_quote = (
            await session.execute(
                select(Quotes).where(Quotes.code == FIXTURE_WARN_QUOTE_CODE)
            )
        ).scalar_one_or_none()
        if existing_warn_quote is not None:
            await _reset_fixture_orders(session, existing_warn_quote.id)

        warn_quote, warn_gate = await _price_fixture_quote(
            session,
            intake=warn_intake,
            tpl=tpl,
            existing_quote=existing_warn_quote,
            quote_code=FIXTURE_WARN_QUOTE_CODE,
            product_spec=WARN_E2E_PARSED_SPEC,
            readiness_mutator=_inject_operations_missing_warning,
            require_ack=True,
        )

        finish_display_intake = await _ensure_finish_display_intake(session)
        geometry_smoke_intake = await _ensure_geometry_smoke_intake(session)

        manifest = {
            "fixture_version": "1",
            "seeded_at": datetime.now(timezone.utc).isoformat(),
            "intake_code": intake.code,
            "intake_id": intake.id,
            "quote_code": quote.code,
            "quote_id": quote.id,
            "quote_status": quote.status,
            "template_code": TEMPLATE_CODE,
            "grand_total": float(quote.grand_total or 0),
            "can_create_commercial_quote": quote_gate.can_create_commercial_quote,
            "live_gate_can_create_commercial_quote": quote_gate.can_create_commercial_quote,
            "requires_acknowledgement": quote_gate.requires_acknowledgement,
            "quote_gate_blockers": list(quote_gate.blockers or []),
            "quote_gate_warnings": list(quote_gate.warnings or []),
            "quote_gate_reason_codes": list(quote_gate.reason_codes or []),
            "readiness_overlay": None,
            "deleted_orders_on_reset": deleted_orders,
            "has_existing_order": False,
            "order_code": None,
            "order_id": None,
            "warn_fixture": {
                "intake_code": warn_intake.code,
                "intake_id": warn_intake.id,
                "quote_code": warn_quote.code,
                "quote_id": warn_quote.id,
                "can_create_commercial_quote": warn_gate.can_create_commercial_quote,
                "requires_acknowledgement": warn_gate.requires_acknowledgement,
                "quote_gate_ack_pending": list(
                    warn_gate.classified.get("acknowledgement_pending", [])
                ),
            },
            "finish_display_fixture": {
                "intake_code": finish_display_intake.code,
                "intake_id": finish_display_intake.id,
                "template_code": TEMPLATE_CODE,
                "product_spec_keys": sorted(WORKINTAKE_V2_FINISH_DISPLAY_SPEC.keys()),
            },
            "geometry_smoke_fixture": {
                "intake_code": geometry_smoke_intake.code,
                "intake_id": geometry_smoke_intake.id,
                "template_code": TEMPLATE_CODE,
                "layer_count": len(GEOMETRY_SMOKE_E2E_SPEC.get("vector_detected_layers") or []),
                "vector_file_name": GEOMETRY_SMOKE_E2E_SPEC.get("vector_file_name"),
                "source_backup_code": "IR-MQ3C869E",
            },
        }

        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        return manifest


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    try:
        result = asyncio.run(seed())
        print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
