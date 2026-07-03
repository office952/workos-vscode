from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from datetime import datetime, date, timedelta

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from services.quotes import QuotesService
from services.quote_orchestrator import QuoteOrchestrator
from services.intake_product_spec_loader import load_intake_product_spec
from services.product_readiness_service import ProductReadinessService
from services.volumetric_finish_assignment_service import (
    normalize_volumetric_quote_input_from_finish_assignments,
)
from services.volumetric_material_rate_resolver import is_volumetric_template_code
from services.aggregate_cost_bom_price_bridge import is_aggregate_cost_template
from services.volumetric_quote_ready_policy import evaluate_volumetric_quote_ready
from data_models.product_contracts import PricingContext, QuotePricing
from validators.status_lifecycle import validate_status, validate_transition
from services.company_commercial_settings_service import get_default_vat_pct
from services.quote_legacy_revision import build_legacy_revision_source_from_quote
from services.quote_send_log import (
    append_commercial_delivery_log,
    assert_send_log_status_allowed,
    build_send_log_entry,
    extract_commercial_delivery_log,
    validate_send_log_payload,
)

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/quotes",
    tags=["quotes"],
    dependencies=[Depends(get_current_user)],
)

SUPPORTED_QUERY_OPERATORS = ["$eq"]

# Quote commercial revision — repricing via POST /{id}/price (orchestrator only).
QUOTE_REVISION_ELIGIBLE_STATUSES = frozenset(
    {"draft", "priced", "sent", "viewed", "negotiating"}
)
QUOTE_REVISION_MAX_DISCOUNT_PCT = 50.0

READINESS_CRITICAL_SECTION_KEYS = [
    "technical_readiness",
    "costengine_readiness",
    "document_output_readiness",
    "execution_preparation_readiness",
]


def _parse_query_or_400(raw_query: Optional[str]) -> Optional[Dict[str, Any]]:
    if not raw_query:
        return None
    try:
        parsed = json.loads(raw_query)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid query JSON format")

    if not isinstance(parsed, dict):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_query_shape",
                "message": "Query must be a JSON object",
            },
        )

    for _field, value in parsed.items():
        if isinstance(value, dict):
            operator = next(
                (k for k in value.keys() if isinstance(k, str) and k.startswith("$")),
                "object_value",
            )
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "unsupported_query_operator",
                    "operator": operator,
                    "supported_operators": SUPPORTED_QUERY_OPERATORS,
                },
            )

    return parsed


def _collect_readiness_blocking_codes(readiness_result: Dict[str, Any]) -> List[str]:
    codes: List[str] = []

    top_level_blockers = readiness_result.get("blockers", [])
    if isinstance(top_level_blockers, list):
        codes.extend(str(code) for code in top_level_blockers if code)

    for section_key in READINESS_CRITICAL_SECTION_KEYS:
        section = readiness_result.get(section_key)
        if not isinstance(section, dict):
            codes.append(f"{section_key}_missing")
            continue

        section_status = str(section.get("status") or "").strip()
        if section_status and section_status != "ready":
            codes.append(f"{section_key}:{section_status}")

        section_blockers = section.get("blockers", [])
        if isinstance(section_blockers, list):
            codes.extend(str(code) for code in section_blockers if code)

        section_warnings = section.get("warnings", [])
        if isinstance(section_warnings, list):
            codes.extend(str(code) for code in section_warnings if code)

    if not codes:
        codes.append("readiness_not_ready")

    # Preserve order and remove duplicates.
    deduped = list(dict.fromkeys(codes))
    return deduped


async def _intake_linkage_fields_for_quote(
    db: AsyncSession,
    intake_id: Optional[int],
) -> Dict[str, Any]:
    """Resolve intake linkage fields for quote persistence (mirrors /from-intake)."""
    if intake_id is None:
        return {}

    from services.intake_requests import Intake_requestsService

    intake = await Intake_requestsService(db).get_by_id(intake_id)
    if intake is None:
        return {}

    fields: Dict[str, Any] = {
        "intake_id": intake.id,
        "intake_code": intake.code,
    }
    if intake.client_id is not None:
        fields["client_id"] = intake.client_id
    if intake.contact_person:
        fields["contact_person"] = intake.contact_person
    if intake.client_name:
        fields["_intake_client_name"] = intake.client_name
    return fields


async def _apply_settings_vat_to_pricing(
    db: AsyncSession, pricing_obj: QuotePricing
) -> None:
    """Override client-supplied VAT with company Settings (canonical source)."""
    pricing_obj.vat_pct = await get_default_vat_pct(db)


def _validate_revision_pricing(pricing_obj: QuotePricing) -> None:
    """Conservative discount guard for revision — no pricing formula changes."""
    discount = float(pricing_obj.discount_pct or 0.0)
    if discount < 0:
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_discount", "message": "Discountul nu poate fi negativ."},
        )
    if discount > QUOTE_REVISION_MAX_DISCOUNT_PCT:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_discount",
                "message": f"Discountul depășește limita de {QUOTE_REVISION_MAX_DISCOUNT_PCT:g}%.",
            },
        )


def _revision_source_from_payload(
    payload: QuotePriceRequest,
    *,
    legacy_reconstructed: bool = False,
) -> Dict[str, Any]:
    source = {
        "product_template": payload.product_template,
        "user_config": payload.user_config,
        "quote_input": payload.quote_input,
        "pricing": payload.pricing,
    }
    if legacy_reconstructed:
        source["legacy_reconstructed"] = True
    return source


def _payload_has_revision_inputs(payload: QuotePriceRequest) -> bool:
    if not isinstance(payload.product_template, dict):
        return False
    if payload.product_template.get("id") in (None, ""):
        return False
    if not isinstance(payload.user_config, dict):
        return False
    if not payload.user_config:
        return False
    return True


async def _resolve_revision_price_payload(
    db: AsyncSession,
    quote_obj: Any,
    payload: QuotePriceRequest,
    *,
    is_revision: bool,
) -> tuple[QuotePriceRequest, bool]:
    """Fill missing product_template/user_config from legacy snapshot when safe."""
    if _payload_has_revision_inputs(payload):
        return payload, False

    legacy = await build_legacy_revision_source_from_quote(db, quote_obj)
    if not legacy.ok:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "legacy_revision_source_missing",
                "missing_fields": legacy.missing_fields,
                "message": legacy.message,
            },
        )

    src = legacy.source or {}
    incoming_pricing = payload.pricing if isinstance(payload.pricing, dict) else {}
    stored_pricing = src.get("pricing") if isinstance(src.get("pricing"), dict) else {}
    merged_pricing = {**stored_pricing, **incoming_pricing}

    merged = QuotePriceRequest(
        product_template=src.get("product_template"),
        user_config=src.get("user_config"),
        quote_input=src.get("quote_input"),
        product_spec_json=src.get("product_spec_json"),
        pricing=merged_pricing or None,
        pricing_context=payload.pricing_context,
        client_name=(payload.client_name or getattr(quote_obj, "client_name", None)),
        intake_id=payload.intake_id or getattr(quote_obj, "intake_id", None),
    )
    return merged, legacy.legacy_reconstructed


def _extract_commercial_delivery_log(raw: Optional[str]) -> List[Dict[str, Any]]:
    """Read existing send-log entries from line_items wrapper without mutating them."""
    if not raw or not str(raw).strip():
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict) and isinstance(parsed.get("commercial_delivery_log"), list):
            return list(parsed["commercial_delivery_log"])
    except Exception:
        return []
    return []


def _collect_revision_history(
    previous_line_items: Optional[str], previous_version: int
) -> List[Dict[str, Any]]:
    history: List[Dict[str, Any]] = []
    if previous_line_items:
        try:
            parsed = json.loads(previous_line_items)
            if isinstance(parsed, dict) and isinstance(parsed.get("revision_history"), list):
                history = list(parsed["revision_history"])
        except Exception:
            history = []
    history.append(
        {
            "version": previous_version,
            "archived_at": datetime.utcnow().isoformat() + "Z",
            "line_items": previous_line_items,
        }
    )
    return history


def _serialize_quote_line_items(
    snapshot_dict: Dict[str, Any],
    *,
    component_breakdown: Optional[List[Any]] = None,
    linked_module_results: Optional[List[Any]] = None,
    cost_warnings: Optional[List[Any]] = None,
    revision_source: Optional[Dict[str, Any]] = None,
    revision_history: Optional[List[Dict[str, Any]]] = None,
    quote_input: Optional[Dict[str, Any]] = None,
    product_spec_json: Optional[Dict[str, Any]] = None,
    delivery_type: Optional[str] = None,
    face_vinyl_handoff: Optional[Dict[str, Any]] = None,
    plexiglass_face_nesting: Optional[Dict[str, Any]] = None,
    forex_backing_nesting: Optional[Dict[str, Any]] = None,
    flat_material_nesting_summary: Optional[Dict[str, Any]] = None,
    real_offcut_measurement_required: Optional[bool] = None,
    post_cut_offcut_measurement_tasks: Optional[List[Any]] = None,
    offcut_inventory_intake: Optional[Dict[str, Any]] = None,
) -> str:
    """Persist snapshot as Shape B when breakdown or execution handoff metadata is present."""
    needs_wrapper = (
        (component_breakdown is not None and len(component_breakdown) > 0)
        or (linked_module_results is not None and len(linked_module_results) > 0)
        or revision_source is not None
        or (revision_history is not None and len(revision_history) > 0)
        or quote_input is not None
        or product_spec_json is not None
        or delivery_type is not None
        or face_vinyl_handoff is not None
        or plexiglass_face_nesting is not None
        or forex_backing_nesting is not None
        or flat_material_nesting_summary is not None
        or real_offcut_measurement_required is not None
        or post_cut_offcut_measurement_tasks is not None
        or offcut_inventory_intake is not None
    )
    if not needs_wrapper:
        return json.dumps(snapshot_dict)

    wrapper: Dict[str, Any] = {"line_items": snapshot_dict}
    if component_breakdown is not None and len(component_breakdown) > 0:
        wrapper["component_breakdown"] = component_breakdown
    if linked_module_results is not None and len(linked_module_results) > 0:
        wrapper["linked_module_results"] = linked_module_results
    if isinstance(cost_warnings, list) and len(cost_warnings) > 0:
        wrapper["cost_warnings"] = cost_warnings
    if revision_source is not None:
        wrapper["revision_source"] = revision_source
    if revision_history is not None and len(revision_history) > 0:
        wrapper["revision_history"] = revision_history
    if quote_input is not None:
        wrapper["quote_input"] = quote_input
    if product_spec_json is not None:
        wrapper["product_spec_json"] = product_spec_json
    if delivery_type is not None:
        wrapper["delivery_type"] = delivery_type
    if face_vinyl_handoff is not None:
        wrapper["face_vinyl_handoff"] = face_vinyl_handoff
    if plexiglass_face_nesting is not None:
        wrapper["plexiglass_face_nesting"] = plexiglass_face_nesting
    if forex_backing_nesting is not None:
        wrapper["forex_backing_nesting"] = forex_backing_nesting
    if flat_material_nesting_summary is not None:
        wrapper["flat_material_nesting_summary"] = flat_material_nesting_summary
    if real_offcut_measurement_required is not None:
        wrapper["real_offcut_measurement_required"] = real_offcut_measurement_required
    if post_cut_offcut_measurement_tasks is not None:
        wrapper["post_cut_offcut_measurement_tasks"] = post_cut_offcut_measurement_tasks
    if offcut_inventory_intake is not None:
        wrapper["offcut_inventory_intake"] = offcut_inventory_intake
    return json.dumps(wrapper)


def _template_to_quote_dict(template_obj: Any) -> Dict[str, Any]:
    return {
        "id": template_obj.id,
        "template_code": template_obj.template_code,
        "family_id": template_obj.family_id,
        "family_name": template_obj.family_name,
        "description": template_obj.description,
        "components_json": template_obj.components_json,
        "operations_json": template_obj.operations_json,
        "required_materials_json": template_obj.required_materials_json,
        "estimated_hours": template_obj.estimated_hours,
        "base_labor_rate": template_obj.base_labor_rate,
        "base_margin_pct": template_obj.base_margin_pct,
        "active": template_obj.active,
        "notes": template_obj.notes,
    }


def _extract_snapshot_component_breakdown(snapshot: Any) -> List[Any]:
    try:
        raw = getattr(snapshot, "component_breakdown_json", None)
        if raw:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(parsed, list):
                return parsed
    except Exception:
        return []
    breakdown = getattr(snapshot, "component_breakdown", None)
    return list(breakdown) if isinstance(breakdown, list) else []


def _cost_number(cost_result: Any, field_name: str) -> float:
    if isinstance(cost_result, dict):
        value = cost_result.get(field_name)
    else:
        value = getattr(cost_result, field_name, None)
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


async def _build_linked_module_quote_results(
    db: AsyncSession,
    *,
    orchestrator: QuoteOrchestrator,
    linked_modules: Any,
    quantity: int,
    pricing: QuotePricing,
    pricing_context: PricingContext,
) -> List[Dict[str, Any]]:
    if not isinstance(linked_modules, list):
        return []

    from services.product_templates import Product_templatesService

    template_service = Product_templatesService(db)
    results: List[Dict[str, Any]] = []
    for index, raw_module in enumerate(linked_modules):
        if not isinstance(raw_module, dict):
            continue
        module_code = str(raw_module.get("module_template_code") or "").strip()
        module_input = raw_module.get("input_payload") if isinstance(raw_module.get("input_payload"), dict) else {}
        if not module_code:
            results.append(
                {
                    "status": "blocked",
                    "blocked_reasons": ["linked_module_template_code_missing"],
                    "input_payload": dict(module_input),
                    "index": index,
                }
            )
            continue

        module_template = await template_service.get_by_field("template_code", module_code)
        if module_template is None:
            results.append(
                {
                    "module_template_code": module_code,
                    "status": "blocked",
                    "blocked_reasons": ["linked_module_template_not_found"],
                    "input_payload": dict(module_input),
                    "index": index,
                }
            )
            continue

        child_input = dict(module_input)
        child_input.pop("linked_modules", None)
        child_template = _template_to_quote_dict(module_template)
        child_user_config = {
            "product_id": module_code,
            "quantity": quantity,
            "dimensions": {
                "width_mm": child_input.get("width_mm", 0),
                "height_mm": child_input.get("height_mm", 0),
                "depth_mm": child_input.get("depth_mm", 0),
            },
        }
        child_snapshot = orchestrator.build_snapshot(
            product_template=child_template,
            user_config=child_user_config,
            pricing=pricing,
            pricing_context=pricing_context,
            quote_input=child_input,
        )
        child_snapshot.template_id = getattr(module_template, "id", None)
        child_dict = child_snapshot.to_dict()
        results.append(
            {
                "module_template_code": module_code,
                "template_code": module_code,
                "template_id": getattr(module_template, "id", None),
                "relation_type": raw_module.get("relation_type"),
                "pricing_mode": raw_module.get("pricing_mode"),
                "execution_mode": raw_module.get("execution_mode"),
                "input_payload": child_input,
                "status": child_snapshot.status,
                "blocked_reasons": list(child_snapshot.blocked_reasons or []),
                "cost_result": child_dict.get("cost_result", {}),
                "price": child_dict.get("price", {}),
                "snapshot": child_dict,
                "component_breakdown": _extract_snapshot_component_breakdown(child_snapshot),
                "index": index,
            }
        )
    return results


def _apply_linked_module_results_to_snapshot(
    snapshot: Any,
    linked_module_results: List[Dict[str, Any]],
    pricing: QuotePricing,
) -> Dict[str, float]:
    if not linked_module_results:
        return {}

    linked_blockers: List[str] = []
    for index, module in enumerate(linked_module_results):
        if module.get("status") in {"blocked", "error"}:
            for reason in module.get("blocked_reasons") or ["linked_module_blocked"]:
                linked_blockers.append(f"linked_module[{index}]:{reason}")
    if linked_blockers:
        snapshot.status = "blocked"
        snapshot.blocked_reasons = list(snapshot.blocked_reasons or []) + linked_blockers
        setattr(snapshot, "linked_module_results", linked_module_results)
        return {}

    parent_cost = getattr(snapshot, "cost_result", None)
    if parent_cost is None:
        snapshot.status = "blocked"
        snapshot.blocked_reasons = list(snapshot.blocked_reasons or []) + [
            "linked_module_parent_cost_result_missing"
        ]
        setattr(snapshot, "linked_module_results", linked_module_results)
        return {}
    parent_total = _cost_number(parent_cost, "total_cost")
    linked_materials = sum(_cost_number(m.get("cost_result", {}), "materials_cost") for m in linked_module_results)
    linked_labour = sum(_cost_number(m.get("cost_result", {}), "labour_cost") for m in linked_module_results)
    linked_machine = sum(_cost_number(m.get("cost_result", {}), "machine_cost") for m in linked_module_results)
    linked_external = sum(_cost_number(m.get("cost_result", {}), "external_cost") for m in linked_module_results)
    linked_overhead = sum(_cost_number(m.get("cost_result", {}), "overhead_cost") for m in linked_module_results)
    linked_time = sum(_cost_number(m.get("cost_result", {}), "estimated_time_minutes") for m in linked_module_results)
    linked_total = sum(_cost_number(m.get("cost_result", {}), "total_cost") for m in linked_module_results)

    parent_cost.materials_cost = round(_cost_number(parent_cost, "materials_cost") + linked_materials, 2)
    parent_cost.labour_cost = round(_cost_number(parent_cost, "labour_cost") + linked_labour, 2)
    parent_cost.machine_cost = round(_cost_number(parent_cost, "machine_cost") + linked_machine, 2)
    parent_cost.external_cost = round(_cost_number(parent_cost, "external_cost") + linked_external, 2)
    parent_cost.overhead_cost = round(_cost_number(parent_cost, "overhead_cost") + linked_overhead, 2)
    parent_cost.estimated_time_minutes = round(_cost_number(parent_cost, "estimated_time_minutes") + linked_time, 2)
    parent_cost.total_cost = round(parent_total + linked_total, 2)
    snapshot.price = QuoteOrchestrator._apply_commercial(parent_cost.total_cost, pricing)
    setattr(snapshot, "linked_module_results", linked_module_results)
    return {
        "parent_total_cost": round(parent_total, 2),
        "linked_modules_total_cost": round(linked_total, 2),
        "composite_total_cost": round(parent_total + linked_total, 2),
    }


async def _resolve_volumetric_quote_input_for_intake(
    db: AsyncSession,
    *,
    intake_id: Optional[int],
    quote_input: Optional[dict],
    product_spec_json: Optional[dict] = None,
) -> dict[str, Any]:
    product_spec = (
        product_spec_json
        if isinstance(product_spec_json, dict)
        else await load_intake_product_spec(db, intake_id)
    )
    return normalize_volumetric_quote_input_from_finish_assignments(
        dict(quote_input or {}),
        product_spec=product_spec,
    )


async def _assert_commercial_quote_gate(
    db: AsyncSession,
    *,
    template_id: int,
    template_code: str,
    template_active: bool,
    quote_input: Optional[dict],
    intake_id: Optional[int],
    product_spec_json: Optional[dict] = None,
    cost_blockers: Optional[List[str]] = None,
) -> tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    """Enforce final commercial quote readiness. Raises HTTP 422 when blocked."""
    product_spec = (
        product_spec_json
        if isinstance(product_spec_json, dict)
        else await load_intake_product_spec(db, intake_id)
    )
    normalized_quote_input = normalize_volumetric_quote_input_from_finish_assignments(
        dict(quote_input or {}),
        product_spec=product_spec,
    )
    readiness = await ProductReadinessService(db).evaluate(
        template_id, product_spec=product_spec
    )
    readiness_dict = readiness.to_dict()
    quote_gate_dict: Optional[Dict[str, Any]] = None

    if is_volumetric_template_code(template_code):
        quote_gate = evaluate_volumetric_quote_ready(
            template_code=template_code,
            template_active=template_active,
            readiness_dict=readiness_dict,
            cost_blockers=list(cost_blockers or []),
            quote_input=normalized_quote_input,
            product_spec=product_spec,
        )
        quote_gate_dict = quote_gate.to_dict()
        if not quote_gate.can_create_commercial_quote:
            raise HTTPException(
                status_code=422,
                detail={
                    "status": "blocked",
                    "message": (
                        "Template-ul nu este pregătit pentru ofertă comercială. "
                        "Rezolvă blocker-ele de readiness."
                    ),
                    "blocked_reasons": quote_gate.blockers,
                    "quote_gate": quote_gate_dict,
                    "readiness_result": readiness_dict,
                },
            )
        return readiness_dict, quote_gate_dict

    if not readiness.ready_for_quote:
        blocking_codes = _collect_readiness_blocking_codes(readiness_dict)
        raise HTTPException(
            status_code=422,
            detail={
                "status": "blocked",
                "message": (
                    "Template-ul nu este pregătit pentru ofertă comercială. "
                    "Rezolvă blocker-ele de readiness."
                ),
                "blocked_reasons": [f"readiness_blocked:{code}" for code in blocking_codes],
                "readiness_result": readiness_dict,
            },
        )
    return readiness_dict, quote_gate_dict


# ---------- Pydantic Schemas ----------
class QuotesData(BaseModel):
    """Entity data schema (for create/update)"""
    code: str
    intake_id: int = None
    intake_code: str = None
    client_id: int = None
    client_name: str
    contact_person: str = None
    status: str
    version: int
    valid_until: str = None
    line_items: str = None
    subtotal: float = None
    discount: float = None
    discount_pct: float = None
    total_before_vat: float = None
    vat: float = None
    grand_total: float = None
    margin_pct: float = None
    notes: str = None
    assigned_to: str = None


class QuotesUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    code: Optional[str] = None
    intake_id: Optional[int] = None
    intake_code: Optional[str] = None
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    contact_person: Optional[str] = None
    status: Optional[str] = None
    version: Optional[int] = None
    valid_until: Optional[str] = None
    line_items: Optional[str] = None
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    discount_pct: Optional[float] = None
    total_before_vat: Optional[float] = None
    vat: Optional[float] = None
    grand_total: Optional[float] = None
    margin_pct: Optional[float] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None


class QuotesResponse(BaseModel):
    """Entity response schema"""
    id: int
    code: str
    intake_id: Optional[int] = None
    intake_code: Optional[str] = None
    client_id: Optional[int] = None
    client_name: str
    contact_person: Optional[str] = None
    status: str
    version: int
    valid_until: Optional[str] = None
    line_items: Optional[str] = None
    subtotal: Optional[float] = None
    discount: Optional[float] = None
    discount_pct: Optional[float] = None
    total_before_vat: Optional[float] = None
    vat: Optional[float] = None
    grand_total: Optional[float] = None
    margin_pct: Optional[float] = None
    notes: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class QuotesListResponse(BaseModel):
    """List response schema"""
    items: List[QuotesResponse]
    total: int
    skip: int
    limit: int


class QuotesBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[QuotesData]


class QuotesBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: QuotesUpdateData


class QuotesBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[QuotesBatchUpdateItem]


class QuotesBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=QuotesListResponse)
async def query_quotess(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query quotess with filtering, sorting, and pagination"""
    logger.debug(f"Querying quotess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = QuotesService(db)
    try:
        query_dict = _parse_query_or_400(query)
        
        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
        )
        logger.debug(f"Found {result['total']} quotess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying quotess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=QuotesListResponse)
async def query_quotess_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query quotess with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying quotess: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = QuotesService(db)
    try:
        query_dict = _parse_query_or_400(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} quotess")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying quotess: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=QuotesResponse)
async def get_quotes(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single quotes by ID"""
    logger.debug(f"Fetching quotes with id: {id}, fields={fields}")
    
    service = QuotesService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Quotes with id {id} not found")
            raise HTTPException(status_code=404, detail="Quotes not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching quotes {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=QuotesResponse, status_code=201)
async def create_quotes(
    data: QuotesData,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("quote.create")),
):
    """Create a new quotes"""
    logger.debug(f"Creating new quotes with data: {data}")

    # AUDIT FIX (Task 10): Validate status against canonical lifecycle
    try:
        validate_status("quotes", data.status)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    service = QuotesService(db)
    try:
        result = await service.create(data.model_dump())
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create quotes")
        
        logger.info(f"Quotes created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating quotes: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating quotes: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[QuotesResponse], status_code=201)
async def create_quotess_batch(
    request: QuotesBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("quote.create")),
):
    """Create multiple quotess in a single request"""
    logger.debug(f"Batch creating {len(request.items)} quotess")
    
    service = QuotesService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump())
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} quotess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[QuotesResponse])
async def update_quotess_batch(
    request: QuotesBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("quote.update")),
):
    """Update multiple quotess in a single request"""
    logger.debug(f"Batch updating {len(request.items)} quotess")
    
    service = QuotesService(db)
    results = []
    
    try:
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            result = await service.update(item.id, update_dict)
            if result:
                results.append(result)
        
        logger.info(f"Batch updated {len(results)} quotess successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=QuotesResponse)
async def update_quotes(
    id: int,
    data: QuotesUpdateData,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("quote.update")),
):
    """Update an existing quotes"""
    logger.debug(f"Updating quotes {id} with data: {data}")

    # AUDIT FIX (Task 10): Validate status transition against canonical lifecycle
    if data.status is not None:
        try:
            validate_status("quotes", data.status)
            # Fetch current status for transition validation
            service_check = QuotesService(db)
            current = await service_check.get_by_id(id)
            if current:
                validate_transition("quotes", current.status, data.status)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    service = QuotesService(db)
    try:
        # Only include non-None values for partial updates
        update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
        result = await service.update(id, update_dict)
        if not result:
            logger.warning(f"Quotes with id {id} not found for update")
            raise HTTPException(status_code=404, detail="Quotes not found")
        
        logger.info(f"Quotes {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating quotes {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating quotes {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_quotess_batch(
    request: QuotesBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("quote.delete")),
):
    """Delete multiple quotess by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} quotess")
    
    service = QuotesService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} quotess successfully")
        return {"message": f"Successfully deleted {deleted_count} quotess", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_quotes(
    id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("quote.delete")),
):
    """Delete a single quotes by ID"""
    logger.debug(f"Deleting quotes with id: {id}")
    
    service = QuotesService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Quotes with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Quotes not found")
        
        logger.info(f"Quotes {id} deleted successfully")
        return {"message": "Quotes deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting quotes {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ---------- Canonical Intake -> Quote Endpoint (Build Set 3A) ----------

# Allowed intake statuses for quote creation.
# From validators/status_lifecycle.py: intake_requests statuses are:
# ["new", "in_review", "needs_info", "ready_for_quote", "blocked", "cancelled"]
# Only "ready_for_quote" is permitted for quote creation.
INTAKE_STATUSES_ALLOWED_FOR_QUOTE = {"ready_for_quote"}


class FromIntakeResponse(BaseModel):
    """Response for POST /from-intake/{intake_id}"""
    quote_id: int
    quote_code: str
    intake_id: int
    intake_code: str
    status: str
    message: str


@router.post("/from-intake/{intake_id}", response_model=FromIntakeResponse, status_code=201)
async def create_quote_from_intake(
    intake_id: int,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("quote.create")),
):
    """Canonical endpoint: Create a draft Quote from a validated IntakeRequest.

    Build Set 3A — Intake -> Quote backend flow.

    Rules:
      - Requires authenticated user (enforced by router dependency).
      - Finds IntakeRequest by id; 404 if not found.
      - Validates intake status is in INTAKE_STATUSES_ALLOWED_FOR_QUOTE; 409 if not.
      - Creates Quote in status="draft" with intake link (intake_id + intake_code).
      - Does NOT calculate price (that is the /price endpoint's job).
      - Does NOT create Order.
      - Does NOT create ExecutionPlan.
      - Does NOT invent cost_result or product_definition.
      - Returns the created quote id/code.
    """
    logger.info(f"POST /from-intake/{intake_id} — creating draft quote from intake")

    # 1. Find IntakeRequest
    from services.intake_requests import Intake_requestsService
    intake_service = Intake_requestsService(db)
    intake = await intake_service.get_by_id(intake_id)

    if not intake:
        raise HTTPException(
            status_code=404,
            detail=f"IntakeRequest with id={intake_id} not found",
        )

    # 2. Validate intake status
    intake_status = intake.status
    if intake_status not in INTAKE_STATUSES_ALLOWED_FOR_QUOTE:
        raise HTTPException(
            status_code=409,
            detail=(
                f"IntakeRequest id={intake_id} has status='{intake_status}'. "
                f"Only statuses {sorted(INTAKE_STATUSES_ALLOWED_FOR_QUOTE)} are allowed for quote creation."
            ),
        )

    # 2.5. Duplicate draft quote guard: intake can have only one active draft quote.
    # Preserve historical duplicates as read-only artifacts; do not mutate them.
    quotes_service = QuotesService(db)
    existing_quotes_result = await quotes_service.get_list(
        skip=0,
        limit=1,
        query_dict={"intake_id": intake_id},
        sort="id",
    )
    existing_quotes = existing_quotes_result.get("items", [])
    if existing_quotes:
        existing_quote = existing_quotes[0]
        raise HTTPException(
            status_code=409,
            detail={
                "error": "quote_already_exists_for_intake",
                "intake_id": intake_id,
                "existing_quote_id": existing_quote.id,
                "existing_quote_code": existing_quote.code,
            },
        )

    # 3. Build draft quote payload — only permitted fields from intake
    now = datetime.utcnow()
    valid_until = (now + timedelta(days=30)).strftime("%Y-%m-%d")
    quote_code = f"Q-{intake.code}-{int(now.timestamp())}"

    # Line item from intake description/quantity (no price — that's for /price endpoint)
    line_item = {
        "productCode": "SRV-001",
        "description": intake.description or "",
        "quantity": intake.quantity or 1,
        "unit_price": 0,
        "total": 0,
    }

    quote_data = {
        "code": quote_code,
        "intake_id": intake.id,
        "intake_code": intake.code,
        "client_id": intake.client_id,
        "client_name": intake.client_name,
        "contact_person": intake.contact_person,
        "status": "draft",
        "version": 1,
        "valid_until": valid_until,
        "line_items": json.dumps([line_item]),
        "subtotal": 0.0,
        "discount": 0.0,
        "discount_pct": 0.0,
        "total_before_vat": 0.0,
        "vat": 0.0,
        "grand_total": 0.0,
        "margin_pct": 0.0,
        "notes": f"Draft generat automat din {intake.code}",
        "assigned_to": intake.assigned_to,
    }

    # 4. Persist quote
    try:
        quote_obj = await quotes_service.create(quote_data)
    except Exception as e:
        logger.error(f"Quote persistence failure from intake {intake_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"persistence_error: {e}")

    if not quote_obj:
        raise HTTPException(status_code=500, detail="quote_persistence_failed")

    logger.info(
        f"Draft quote created: id={quote_obj.id}, code={quote_code}, "
        f"from intake_id={intake_id}, intake_code={intake.code}"
    )

    return FromIntakeResponse(
        quote_id=quote_obj.id,
        quote_code=quote_code,
        intake_id=intake.id,
        intake_code=intake.code,
        status="draft",
        message=f"Draft quote created successfully from intake {intake.code}",
    )


# ---------- Canonical Pricing Endpoint (WorkOS foundation) ----------
class QuotePriceRequest(BaseModel):
    """Request payload for canonical quote pricing.

    Runs the QuoteOrchestrator pipeline:
    ProductSystemService -> CostEngineService -> commercial transform.
    If snapshot.status == 'blocked' -> HTTP 422 with blocked_reasons.
    If 'priced' -> persist Quote row (status='priced', version=1) and return
    { quote_id, snapshot }.

    Sprint #21.4 — `quote_input` is an OPTIONAL per-quote-instance payload
    (e.g. ``personalization_path_length_mm``, ``led_count``, ...) consumed
    by formula-based lines in the CostEngine v2 pipeline. It is forwarded
    verbatim to ``QuoteOrchestrator.build_snapshot()`` and surfaced to the
    engine via ``ComponentCostContext.quote_input``. Omitting this field
    preserves pre-Sprint-21.4 behaviour byte-for-byte for static/legacy
    templates.
    """
    product_template: Optional[dict] = None
    user_config: Optional[dict] = None
    pricing: Optional[dict] = None
    pricing_context: Optional[dict] = None
    client_name: Optional[str] = "Unknown Client"
    code: Optional[str] = None
    quote_input: Optional[dict] = None
    product_spec_json: Optional[dict] = None
    intake_id: Optional[int] = Field(
        default=None,
        description="Optional intake id for vector/file readiness context",
    )


@router.post("/price", status_code=201)
async def price_quote(
    payload: QuotePriceRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("quote.price")),
):
    """Canonical quote pricing endpoint. Delegates to QuoteOrchestrator.

    - Blocked snapshot -> HTTP 422 with {status, blocked_reasons}.
    - Priced snapshot  -> persist Quote row and return {quote_id, snapshot}.

    This endpoint MUST NOT contain cost or pricing formulas of its own.
    """
    logger.info("POST /api/v1/entities/quotes/price invoked")

    pricing_obj = QuotePricing(**payload.pricing) if payload.pricing else QuotePricing()
    _validate_revision_pricing(pricing_obj)
    await _apply_settings_vat_to_pricing(db, pricing_obj)
    pricing_ctx_obj = (
        PricingContext(**payload.pricing_context) if payload.pricing_context else PricingContext()
    )

    template_id_raw = None
    if isinstance(payload.product_template, dict):
        template_id_raw = payload.product_template.get("id")

    try:
        template_id = int(template_id_raw) if template_id_raw is not None else None
    except (TypeError, ValueError):
        template_id = None

    template_code = ""
    template_active = True
    if template_id is not None:
        from services.product_templates import Product_templatesService

        tpl = await Product_templatesService(db).get_by_id(template_id)
        if tpl:
            template_code = str(tpl.template_code or "")
            template_active = bool(tpl.active)

    # BLK-18 — Use the canonical `create_with_registry()` factory to load
    # material costs and workcenter rates from live registries via the
    # bridge functions (load_material_cost_dict / load_workcenter_rate_dict).
    # If the registries are empty (e.g. fresh environment) the orchestrator
    # simply falls back to the legacy v1 path — byte-for-byte identical
    # pre-BLK-18 behaviour. Registry read failures are caught inside the
    # factory and logged; they never break quote pricing.
    orchestrator = await QuoteOrchestrator.create_with_registry(db=db)
    resolved_quote_input = await _resolve_volumetric_quote_input_for_intake(
        db,
        intake_id=payload.intake_id,
        quote_input=payload.quote_input,
        product_spec_json=payload.product_spec_json,
    )
    aggregate_price_context = None
    if is_aggregate_cost_template(template_code):
        from services.aggregate_cost_bom_price_bridge import prepare_aggregate_price_context

        aggregate_price_context = await prepare_aggregate_price_context(
            db,
            template_code,
            quote_input=resolved_quote_input or payload.quote_input,
        )
    try:
        snapshot = orchestrator.build_snapshot(
            product_template=payload.product_template,
            user_config=payload.user_config,
            pricing=pricing_obj,
            pricing_context=pricing_ctx_obj,
            quote_input=resolved_quote_input or payload.quote_input,
            aggregate_price_context=aggregate_price_context,
        )
        snapshot.template_id = template_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"QuoteOrchestrator failure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"orchestrator_error: {e}")

    quote_input_for_pricing = resolved_quote_input or payload.quote_input or {}
    try:
        requested_quantity = int((payload.user_config or {}).get("quantity") or 1)
    except (TypeError, ValueError):
        requested_quantity = 1
    linked_module_results = await _build_linked_module_quote_results(
        db,
        orchestrator=orchestrator,
        linked_modules=quote_input_for_pricing.get("linked_modules") if isinstance(quote_input_for_pricing, dict) else [],
        quantity=max(requested_quantity, 1),
        pricing=pricing_obj,
        pricing_context=pricing_ctx_obj,
    )
    linked_cost_totals = _apply_linked_module_results_to_snapshot(
        snapshot,
        linked_module_results,
        pricing_obj,
    )

    if snapshot.status == "blocked":
        logger.warning(f"Quote blocked: reasons={snapshot.blocked_reasons}")
        raise HTTPException(
            status_code=422,
            detail={
                "status": "blocked",
                "blocked_reasons": list(snapshot.blocked_reasons),
            },
        )

    readiness_result_dict = None
    quote_gate_dict = None
    if template_id is not None:
        readiness_result_dict, quote_gate_dict = await _assert_commercial_quote_gate(
            db,
            template_id=template_id,
            template_code=template_code,
            template_active=template_active,
            quote_input=resolved_quote_input or payload.quote_input,
            intake_id=payload.intake_id,
            product_spec_json=payload.product_spec_json,
            cost_blockers=list(snapshot.blocked_reasons or []),
        )
        snapshot.readiness_result = readiness_result_dict
        if quote_gate_dict:
            requires_ack = bool(quote_gate_dict.get("requires_acknowledgement"))
            snapshot.readiness_result = {
                **(readiness_result_dict or {}),
                "quote_gate": quote_gate_dict,
                "ready_for_quote": bool(
                    quote_gate_dict.get("ready_for_quote", readiness_result_dict.get("ready_for_quote"))
                ),
                "policy": {
                    "authority": "backend",
                    "requires_warning_acknowledgement": requires_ack,
                    "quote_gate": "enforced",
                },
            }

    if snapshot.status != "priced":
        raise HTTPException(
            status_code=500,
            detail=f"unexpected_snapshot_status:{snapshot.status}",
        )

    # Persist Quote row — no cost math here, all values copied from snapshot.
    snapshot_dict = snapshot.to_dict()
    if linked_module_results:
        snapshot_dict["linked_module_results"] = linked_module_results
        if linked_cost_totals:
            snapshot_dict.setdefault("cost_result", {}).update(linked_cost_totals)
    quote_code = payload.code or f"Q-{int(datetime.utcnow().timestamp())}"

    # Sprint #10 — defense-in-depth: a `priced` snapshot MUST carry all
    # commercial values. If any of these are None, upstream validation
    # failed silently. No silent numeric fallbacks — fail loudly with 422.
    _required = {
        "snapshot.price.net": snapshot.price.net,
        "snapshot.price.gross": snapshot.price.gross,
        "snapshot.pricing.margin_pct": snapshot.pricing.margin_pct,
        "snapshot.pricing.discount_pct": snapshot.pricing.discount_pct,
        "snapshot.pricing.vat_pct": snapshot.pricing.vat_pct,
    }
    for _path, _val in _required.items():
        if _val is None:
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_quote_snapshot", "missing_field": _path},
            )

    # Sprint #18.5 — persist component_breakdown (CostEngine v2) into the
    # `line_items` column as Shape B wrapper when present; otherwise keep
    # Shape A (byte-for-byte identical pre-sprint serialization).
    #
    # Contract mirrors the frontend parser in
    # app/frontend/src/lib/dataStore.ts :: extractQuotePayload():
    #   Shape A (legacy)  →  json.dumps(snapshot_dict)
    #   Shape B (v2)      →  json.dumps({
    #                           "line_items":          snapshot_dict,
    #                           "component_breakdown": [ ... ],
    #                           "cost_warnings":       [ ... ] (optional)
    #                        })
    #
    # Dynamic attributes set by QuoteOrchestrator (Sprint #17):
    #   snap.component_breakdown_json : JSON string | None
    #   snap.cost_warnings            : list[dict]  | None
    #
    # Rules:
    # - NO cost math here. NO re-serialization of breakdown — reuse the
    #   JSON string produced by the orchestrator; only parse it to embed
    #   it as a JSON subtree (avoid double-encoded strings in DB).
    # - If the attribute is missing, None, or parses to an empty list,
    #   fall back to Shape A — zero regression for legacy and v1 flows.
    # - Failures in this block MUST NOT break quote persistence.
    _breakdown_payload = None
    try:
        _breakdown_json = getattr(snapshot, "component_breakdown_json", None)
        if _breakdown_json:
            _parsed = (
                json.loads(_breakdown_json)
                if isinstance(_breakdown_json, str)
                else _breakdown_json
            )
            if isinstance(_parsed, list) and len(_parsed) > 0:
                _breakdown_payload = _parsed
    except Exception as _e:
        logger.warning(
            f"component_breakdown_json parse failed; falling back to Shape A: {_e}"
        )
        _breakdown_payload = None

    _revision_source = _revision_source_from_payload(payload)
    from services.volumetric_flat_material_handoff_service import (
        build_volumetric_flat_material_handoff,
    )

    product_spec_json = await load_intake_product_spec(db, payload.intake_id)
    delivery_type: Optional[str] = None
    if payload.intake_id is not None:
        from services.intake_requests import Intake_requestsService

        intake_row = await Intake_requestsService(db).get_by_id(payload.intake_id)
        if intake_row is not None and intake_row.delivery_type:
            delivery_type = str(intake_row.delivery_type)
    quote_input_dict = await _resolve_volumetric_quote_input_for_intake(
        db,
        intake_id=payload.intake_id,
        quote_input=payload.quote_input,
    )
    flat_handoff = (
        await build_volumetric_flat_material_handoff(
            db,
            quote_input_dict,
            product_spec=product_spec_json,
        )
        if quote_input_dict
        else {}
    )
    _line_items_str = _serialize_quote_line_items(
        snapshot_dict,
        component_breakdown=_breakdown_payload,
        linked_module_results=linked_module_results,
        cost_warnings=getattr(snapshot, "cost_warnings", None),
        revision_source=_revision_source,
        quote_input=quote_input_dict if quote_input_dict else None,
        product_spec_json=product_spec_json,
        delivery_type=delivery_type,
        face_vinyl_handoff=flat_handoff.get("face_vinyl_handoff"),
        plexiglass_face_nesting=flat_handoff.get("plexiglass_face_nesting"),
        forex_backing_nesting=flat_handoff.get("forex_backing_nesting"),
        flat_material_nesting_summary=flat_handoff.get("flat_material_nesting_summary"),
        real_offcut_measurement_required=flat_handoff.get("real_offcut_measurement_required"),
        post_cut_offcut_measurement_tasks=flat_handoff.get("post_cut_offcut_measurement_tasks"),
        offcut_inventory_intake=flat_handoff.get("offcut_inventory_intake"),
    )

    intake_linkage = await _intake_linkage_fields_for_quote(db, payload.intake_id)
    intake_client_name = intake_linkage.pop("_intake_client_name", None)
    client_name = (payload.client_name or "").strip() or "Unknown Client"
    if client_name == "Unknown Client" and intake_client_name:
        client_name = intake_client_name

    quote_data = {
        "code": quote_code,
        "client_name": client_name,
        "status": "priced",
        "version": 1,
        "line_items": _line_items_str,
        "subtotal": float(snapshot.price.net),
        "grand_total": float(snapshot.price.gross),
        "margin_pct": float(snapshot.pricing.margin_pct),
        "discount_pct": float(snapshot.pricing.discount_pct),
        "vat": float(snapshot.pricing.vat_pct),
        "total_before_vat": float(snapshot.price.net),
        **intake_linkage,
    }
    service = QuotesService(db)
    try:
        quote_obj = await service.create(quote_data)
    except Exception as e:
        logger.error(f"Quote persistence failure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"persistence_error: {e}")

    if not quote_obj:
        raise HTTPException(status_code=500, detail="quote_persistence_failed")

    response_payload = {
        "quote_id": quote_obj.id,
        "quote_code": quote_obj.code,
        "quote_version": quote_obj.version,
        "revised": False,
        "snapshot": snapshot_dict,
    }
    if readiness_result_dict is not None:
        response_payload["readiness_result"] = readiness_result_dict
    return response_payload


@router.post("/{quote_id}/price", status_code=200)
async def price_existing_draft_quote(
    quote_id: int,
    payload: QuotePriceRequest,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_permission("quote.price")),
):
    """Price or revise an existing quote via QuoteOrchestrator.

    Contract:
    - draft: first-time in-place pricing (status → priced, version unchanged).
    - priced/sent/viewed/negotiating: commercial revision (version +1, status → priced).
    - accepted/rejected/expired: HTTP 422 (terminal / post-acceptance).
    - Preserves quote identity and intake linkage; archives prior line_items in revision_history.
    - Does NOT create orders or execution records.
    """
    logger.info(f"POST /api/v1/entities/quotes/{quote_id}/price invoked")

    service = QuotesService(db)
    quote_obj = await service.get_by_id(quote_id)
    if not quote_obj:
        raise HTTPException(status_code=404, detail="quote_not_found")

    current_status = str(quote_obj.status or "")
    if current_status not in QUOTE_REVISION_ELIGIBLE_STATUSES:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "quote_not_eligible_for_revision",
                "quote_id": quote_id,
                "quote_status": current_status,
                "message": (
                    "Revizia comercială este permisă doar pentru oferte neconvertite "
                    "(draft, priced, sent, viewed, negotiating)."
                ),
            },
        )

    is_revision = current_status != "draft"

    payload, legacy_reconstructed = await _resolve_revision_price_payload(
        db, quote_obj, payload, is_revision=is_revision
    )

    pricing_obj = QuotePricing(**payload.pricing) if payload.pricing else QuotePricing()
    _validate_revision_pricing(pricing_obj)
    await _apply_settings_vat_to_pricing(db, pricing_obj)
    pricing_ctx_obj = (
        PricingContext(**payload.pricing_context) if payload.pricing_context else PricingContext()
    )

    template_id_raw = None
    if isinstance(payload.product_template, dict):
        template_id_raw = payload.product_template.get("id")

    try:
        template_id = int(template_id_raw) if template_id_raw is not None else None
    except (TypeError, ValueError):
        template_id = None

    template_code = ""
    template_active = True
    intake_id = payload.intake_id or getattr(quote_obj, "intake_id", None)
    if template_id is not None:
        from services.product_templates import Product_templatesService

        tpl = await Product_templatesService(db).get_by_id(template_id)
        if tpl:
            template_code = str(tpl.template_code or "")
            template_active = bool(tpl.active)

    orchestrator = await QuoteOrchestrator.create_with_registry(db=db)
    resolved_quote_input = await _resolve_volumetric_quote_input_for_intake(
        db,
        intake_id=intake_id,
        quote_input=payload.quote_input,
        product_spec_json=payload.product_spec_json,
    )
    aggregate_price_context = None
    if is_aggregate_cost_template(template_code):
        from services.aggregate_cost_bom_price_bridge import prepare_aggregate_price_context

        aggregate_price_context = await prepare_aggregate_price_context(
            db,
            template_code,
            quote_input=resolved_quote_input or payload.quote_input,
        )
    try:
        snapshot = orchestrator.build_snapshot(
            product_template=payload.product_template,
            user_config=payload.user_config,
            pricing=pricing_obj,
            pricing_context=pricing_ctx_obj,
            quote_input=resolved_quote_input or payload.quote_input,
            aggregate_price_context=aggregate_price_context,
        )
        snapshot.template_id = template_id
    except Exception as e:
        logger.error(f"QuoteOrchestrator failure (in-place pricing): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"orchestrator_error: {e}")

    quote_input_for_pricing = resolved_quote_input or payload.quote_input or {}
    try:
        requested_quantity = int((payload.user_config or {}).get("quantity") or 1)
    except (TypeError, ValueError):
        requested_quantity = 1
    linked_module_results = await _build_linked_module_quote_results(
        db,
        orchestrator=orchestrator,
        linked_modules=quote_input_for_pricing.get("linked_modules") if isinstance(quote_input_for_pricing, dict) else [],
        quantity=max(requested_quantity, 1),
        pricing=pricing_obj,
        pricing_context=pricing_ctx_obj,
    )
    linked_cost_totals = _apply_linked_module_results_to_snapshot(
        snapshot,
        linked_module_results,
        pricing_obj,
    )

    if snapshot.status == "blocked":
        logger.warning(f"Quote blocked (in-place pricing): reasons={snapshot.blocked_reasons}")
        raise HTTPException(
            status_code=422,
            detail={
                "status": "blocked",
                "blocked_reasons": list(snapshot.blocked_reasons),
            },
        )

    readiness_result_dict = None
    quote_gate_dict = None
    if template_id is not None:
        readiness_result_dict, quote_gate_dict = await _assert_commercial_quote_gate(
            db,
            template_id=template_id,
            template_code=template_code,
            template_active=template_active,
            quote_input=resolved_quote_input or payload.quote_input,
            intake_id=intake_id,
            product_spec_json=payload.product_spec_json,
            cost_blockers=list(snapshot.blocked_reasons or []),
        )
        snapshot.readiness_result = readiness_result_dict
        if quote_gate_dict:
            requires_ack = bool(quote_gate_dict.get("requires_acknowledgement"))
            snapshot.readiness_result = {
                **(readiness_result_dict or {}),
                "quote_gate": quote_gate_dict,
                "ready_for_quote": bool(
                    quote_gate_dict.get("ready_for_quote", readiness_result_dict.get("ready_for_quote"))
                ),
                "policy": {
                    "authority": "backend",
                    "requires_warning_acknowledgement": requires_ack,
                    "quote_gate": "enforced",
                },
            }

    if snapshot.status != "priced":
        raise HTTPException(
            status_code=500,
            detail=f"unexpected_snapshot_status:{snapshot.status}",
        )

    snapshot_dict = snapshot.to_dict()
    if linked_module_results:
        snapshot_dict["linked_module_results"] = linked_module_results
        if linked_cost_totals:
            snapshot_dict.setdefault("cost_result", {}).update(linked_cost_totals)

    _required = {
        "snapshot.price.net": snapshot.price.net,
        "snapshot.price.gross": snapshot.price.gross,
        "snapshot.pricing.margin_pct": snapshot.pricing.margin_pct,
        "snapshot.pricing.discount_pct": snapshot.pricing.discount_pct,
        "snapshot.pricing.vat_pct": snapshot.pricing.vat_pct,
    }
    for _path, _val in _required.items():
        if _val is None:
            raise HTTPException(
                status_code=422,
                detail={"error": "invalid_quote_snapshot", "missing_field": _path},
            )

    _breakdown_payload = None
    try:
        _breakdown_json = getattr(snapshot, "component_breakdown_json", None)
        if _breakdown_json:
            _parsed = (
                json.loads(_breakdown_json)
                if isinstance(_breakdown_json, str)
                else _breakdown_json
            )
            if isinstance(_parsed, list) and len(_parsed) > 0:
                _breakdown_payload = _parsed
    except Exception as _e:
        logger.warning(
            f"component_breakdown_json parse failed for in-place pricing; falling back to Shape A: {_e}"
        )
        _breakdown_payload = None

    previous_line_items = quote_obj.line_items
    previous_version = int(quote_obj.version or 1)
    revision_history = (
        _collect_revision_history(previous_line_items, previous_version) if is_revision else None
    )
    revision_source = _revision_source_from_payload(
        payload, legacy_reconstructed=legacy_reconstructed
    )
    from services.volumetric_flat_material_handoff_service import (
        build_volumetric_flat_material_handoff,
    )

    revision_intake_id = payload.intake_id or getattr(quote_obj, "intake_id", None)
    product_spec_json = await load_intake_product_spec(db, revision_intake_id)
    delivery_type: Optional[str] = None
    if revision_intake_id is not None:
        from services.intake_requests import Intake_requestsService

        intake_row = await Intake_requestsService(db).get_by_id(revision_intake_id)
        if intake_row is not None and intake_row.delivery_type:
            delivery_type = str(intake_row.delivery_type)
    quote_input_dict = await _resolve_volumetric_quote_input_for_intake(
        db,
        intake_id=payload.intake_id,
        quote_input=payload.quote_input,
    )
    flat_handoff = (
        await build_volumetric_flat_material_handoff(
            db,
            quote_input_dict,
            product_spec=product_spec_json,
        )
        if quote_input_dict
        else {}
    )
    _line_items_str = _serialize_quote_line_items(
        snapshot_dict,
        component_breakdown=_breakdown_payload,
        linked_module_results=linked_module_results,
        cost_warnings=getattr(snapshot, "cost_warnings", None),
        revision_source=revision_source,
        revision_history=revision_history,
        quote_input=quote_input_dict if quote_input_dict else None,
        product_spec_json=product_spec_json,
        delivery_type=delivery_type,
        face_vinyl_handoff=flat_handoff.get("face_vinyl_handoff"),
        plexiglass_face_nesting=flat_handoff.get("plexiglass_face_nesting"),
        forex_backing_nesting=flat_handoff.get("forex_backing_nesting"),
        flat_material_nesting_summary=flat_handoff.get("flat_material_nesting_summary"),
        real_offcut_measurement_required=flat_handoff.get("real_offcut_measurement_required"),
        post_cut_offcut_measurement_tasks=flat_handoff.get("post_cut_offcut_measurement_tasks"),
        offcut_inventory_intake=flat_handoff.get("offcut_inventory_intake"),
    )
    if is_revision:
        preserved_delivery_log = _extract_commercial_delivery_log(previous_line_items)
        if preserved_delivery_log:
            try:
                wrapper = json.loads(_line_items_str)
                if isinstance(wrapper, dict):
                    wrapper["commercial_delivery_log"] = preserved_delivery_log
                    _line_items_str = json.dumps(wrapper)
            except json.JSONDecodeError as exc:
                logger.warning("Quote delivery log restoration skipped: %s", exc)

    try:
        validate_transition("quotes", current_status, "priced")
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    quote_obj.status = "priced"
    quote_obj.line_items = _line_items_str
    quote_obj.subtotal = float(snapshot.price.net)
    quote_obj.grand_total = float(snapshot.price.gross)
    quote_obj.margin_pct = float(snapshot.pricing.margin_pct)
    quote_obj.discount_pct = float(snapshot.pricing.discount_pct)
    quote_obj.vat = float(snapshot.pricing.vat_pct)
    quote_obj.total_before_vat = float(snapshot.price.net)
    if is_revision:
        quote_obj.version = previous_version + 1

    # Keep intake linkage and quote identity unchanged; only refresh client_name if explicitly provided.
    if payload.client_name:
        quote_obj.client_name = payload.client_name

    try:
        await db.commit()
        await db.refresh(quote_obj)
    except Exception as e:
        await db.rollback()
        logger.error(f"In-place quote persistence failure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"persistence_error: {e}")

    response_payload = {
        "quote_id": quote_obj.id,
        "quote_code": quote_obj.code,
        "quote_version": quote_obj.version,
        "revised": is_revision,
        "legacy_reconstructed": legacy_reconstructed,
        "snapshot": snapshot_dict,
    }
    if readiness_result_dict is not None:
        response_payload["readiness_result"] = readiness_result_dict
    return response_payload


class QuoteSendLogRequest(BaseModel):
    channel: str
    recipient: Optional[str] = None
    note: Optional[str] = None
    document_ref: Optional[str] = None


@router.post("/{quote_id}/send-log", status_code=200)
async def create_quote_send_log(
    quote_id: int,
    payload: QuoteSendLogRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(require_permission("quote.send")),
):
    """Persist assisted delivery log on quote (no external email delivery)."""
    logger.info(f"POST /api/v1/entities/quotes/{quote_id}/send-log invoked")

    service = QuotesService(db)
    quote_obj = await service.get_by_id(quote_id)
    if not quote_obj:
        raise HTTPException(status_code=404, detail="quote_not_found")

    current_status = str(quote_obj.status or "")
    status_changed, target_status = assert_send_log_status_allowed(current_status)
    validation = validate_send_log_payload(
        channel=payload.channel,
        recipient=payload.recipient,
        note=payload.note,
        document_ref=payload.document_ref,
    )

    prior_totals = (
        float(quote_obj.subtotal or 0),
        float(quote_obj.grand_total or 0),
        float(quote_obj.margin_pct or 0),
    )

    log_entry = build_send_log_entry(
        quote_obj=quote_obj,
        old_status=current_status,
        new_status=target_status,
        validation=validation,
        actor_id=getattr(user, "id", None),
        actor_email=getattr(user, "email", None),
    )

    try:
        new_line_items = append_commercial_delivery_log(quote_obj.line_items, log_entry)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    quote_obj.line_items = new_line_items

    if status_changed:
        try:
            validate_transition("quotes", current_status, target_status)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc))
        quote_obj.status = target_status

    try:
        await db.commit()
        await db.refresh(quote_obj)
    except Exception as exc:
        await db.rollback()
        logger.error(f"Quote send-log persistence failure: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"persistence_error: {exc}")

    after_totals = (
        float(quote_obj.subtotal or 0),
        float(quote_obj.grand_total or 0),
        float(quote_obj.margin_pct or 0),
    )
    if after_totals != prior_totals:
        logger.error(
            "Quote send-log unexpectedly modified totals quote_id=%s before=%s after=%s",
            quote_id,
            prior_totals,
            after_totals,
        )

    return {
        "quote_id": quote_obj.id,
        "quote_code": quote_obj.code,
        "status": quote_obj.status,
        "quote_version": quote_obj.version,
        "sent_at": log_entry["sent_at"],
        "status_changed": status_changed,
        "log_entry": log_entry,
    }