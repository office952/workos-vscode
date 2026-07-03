import json
import logging
from typing import Any, Dict, List, Optional

from datetime import datetime, date, timezone

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from services.orders import OrdersService
from services.quotes import QuotesService
from services.order_snapshot_service import OrderSnapshotService
from services.order_output_snapshot_reference_service import OrderOutputSnapshotReferenceService
from services.company_commercial_settings_service import get_eur_to_ron_rate
from services.order_currency_conversion_service import (
    convert_quote_totals_to_order_base,
    extract_currency_from_quote_snapshot,
)
from services.order_immutability_service import assert_order_financial_fields_mutable
from data_models.product_contracts import (
    CostLine,
    CostResult,
    CostValidation,
    OrderFinalPrice,
    OrderSnapshot,
    ProductComponent,
    ProductDefinition,
    ProductDimensions,
    ProductLayer,
    ProductMaterial,
    ProductProcess,
    ProductValidationResult,
    QuoteCalculationSnapshot,
    QuotePrice,
    QuotePricing,
    iso_now,
)
from validators.status_lifecycle import validate_status, validate_transition

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/entities/orders",
    tags=["orders"],
    dependencies=[Depends(get_current_user)],
)

SUPPORTED_QUERY_OPERATORS = ["$eq"]


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


# ---------- Pydantic Schemas ----------
class OrdersData(BaseModel):
    """Entity data schema (for create/update)"""
    code: str
    quote_id: int = None
    quote_code: str = None
    client_id: int = None
    client_name: str
    contact_person: str = None
    status: str
    product_summary: str = None
    total_amount: float = None
    locked_at: str = None
    promised_delivery: str = None
    job_id: str = None
    payment_status: str = None
    snapshot_version: int = None
    snapshot_line_items: str = None
    notes: str = None


class OrdersUpdateData(BaseModel):
    """Update entity data (partial updates allowed)"""
    code: Optional[str] = None
    quote_id: Optional[int] = None
    quote_code: Optional[str] = None
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    contact_person: Optional[str] = None
    status: Optional[str] = None
    product_summary: Optional[str] = None
    total_amount: Optional[float] = None
    locked_at: Optional[str] = None
    promised_delivery: Optional[str] = None
    job_id: Optional[str] = None
    payment_status: Optional[str] = None
    snapshot_version: Optional[int] = None
    snapshot_line_items: Optional[str] = None
    notes: Optional[str] = None


class OrdersResponse(BaseModel):
    """Entity response schema"""
    id: int
    code: str
    quote_id: Optional[int] = None
    quote_code: Optional[str] = None
    client_id: Optional[int] = None
    client_name: str
    contact_person: Optional[str] = None
    status: str
    product_summary: Optional[str] = None
    total_amount: Optional[float] = None
    locked_at: Optional[str] = None
    promised_delivery: Optional[str] = None
    job_id: Optional[str] = None
    payment_status: Optional[str] = None
    snapshot_version: Optional[int] = None
    snapshot_line_items: Optional[str] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    readiness_snapshot: Optional[dict] = None

    class Config:
        from_attributes = True


class OrdersListResponse(BaseModel):
    """List response schema"""
    items: List[OrdersResponse]
    total: int
    skip: int
    limit: int


class OrdersBatchCreateRequest(BaseModel):
    """Batch create request"""
    items: List[OrdersData]


class OrdersBatchUpdateItem(BaseModel):
    """Batch update item"""
    id: int
    updates: OrdersUpdateData


class OrdersBatchUpdateRequest(BaseModel):
    """Batch update request"""
    items: List[OrdersBatchUpdateItem]


class OrdersBatchDeleteRequest(BaseModel):
    """Batch delete request"""
    ids: List[int]


# ---------- Routes ----------
@router.get("", response_model=OrdersListResponse)
async def query_orderss(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Query orderss with filtering, sorting, and pagination"""
    logger.debug(f"Querying orderss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")
    
    service = OrdersService(db)
    try:
        query_dict = _parse_query_or_400(query)
        
        result = await service.get_list(
            skip=skip, 
            limit=limit,
            query_dict=query_dict,
            sort=sort,
        )
        logger.debug(f"Found {result['total']} orderss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying orderss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all", response_model=OrdersListResponse)
async def query_orderss_all(
    query: str = Query(None, description="Query conditions (JSON string)"),
    sort: str = Query(None, description="Sort field (prefix with '-' for descending)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=2000, description="Max number of records to return"),
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    # Query orderss with filtering, sorting, and pagination without user limitation
    logger.debug(f"Querying orderss: query={query}, sort={sort}, skip={skip}, limit={limit}, fields={fields}")

    service = OrdersService(db)
    try:
        query_dict = _parse_query_or_400(query)

        result = await service.get_list(
            skip=skip,
            limit=limit,
            query_dict=query_dict,
            sort=sort
        )
        logger.debug(f"Found {result['total']} orderss")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error querying orderss: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/{id}", response_model=OrdersResponse)
async def get_orders(
    id: int,
    fields: str = Query(None, description="Comma-separated list of fields to return"),
    db: AsyncSession = Depends(get_db),
):
    """Get a single orders by ID"""
    logger.debug(f"Fetching orders with id: {id}, fields={fields}")
    
    service = OrdersService(db)
    try:
        result = await service.get_by_id(id)
        if not result:
            logger.warning(f"Orders with id {id} not found")
            raise HTTPException(status_code=404, detail="Orders not found")
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching orders {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("", response_model=OrdersResponse, status_code=201)
async def create_orders(
    data: OrdersData,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("order.create")),
):
    """Create a new orders"""
    logger.debug(f"Creating new orders with data: {data}")

    # AUDIT FIX (Task 10): Validate status against canonical lifecycle
    try:
        validate_status("orders", data.status)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    service = OrdersService(db)
    try:
        result = await service.create(data.model_dump())
        if not result:
            raise HTTPException(status_code=400, detail="Failed to create orders")
        
        logger.info(f"Orders created successfully with id: {result.id}")
        return result
    except ValueError as e:
        logger.error(f"Validation error creating orders: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating orders: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/batch", response_model=List[OrdersResponse], status_code=201)
async def create_orderss_batch(
    request: OrdersBatchCreateRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("order.create")),
):
    """Create multiple orderss in a single request"""
    logger.debug(f"Batch creating {len(request.items)} orderss")
    
    service = OrdersService(db)
    results = []
    
    try:
        for item_data in request.items:
            result = await service.create(item_data.model_dump())
            if result:
                results.append(result)
        
        logger.info(f"Batch created {len(results)} orderss successfully")
        return results
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch create: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch create failed: {str(e)}")


@router.put("/batch", response_model=List[OrdersResponse])
async def update_orderss_batch(
    request: OrdersBatchUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("order.update")),
):
    """Update multiple orderss in a single request"""
    logger.debug(f"Batch updating {len(request.items)} orderss")
    
    service = OrdersService(db)
    results = []
    
    try:
        pending: list[tuple[int, dict]] = []
        for item in request.items:
            # Only include non-None values for partial updates
            update_dict = {k: v for k, v in item.updates.model_dump().items() if v is not None}
            current = await service.get_by_id(item.id)
            if current:
                assert_order_financial_fields_mutable(current, update_dict)
            pending.append((item.id, update_dict))

        for item_id, update_dict in pending:
            result = await service.update(item_id, update_dict)
            if result:
                results.append(result)

        logger.info(f"Batch updated {len(results)} orderss successfully")
        return results
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch update: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch update failed: {str(e)}")


@router.put("/{id}", response_model=OrdersResponse)
async def update_orders(
    id: int,
    data: OrdersUpdateData,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("order.update")),
):
    """Update an existing orders"""
    logger.debug(f"Updating orders {id} with data: {data}")

    service = OrdersService(db)
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}

    current = await service.get_by_id(id)
    if not current:
        logger.warning(f"Orders with id {id} not found for update")
        raise HTTPException(status_code=404, detail="Orders not found")

    # AUDIT FIX (Task 10): Validate status transition against canonical lifecycle
    if data.status is not None:
        try:
            validate_status("orders", data.status)
            validate_transition("orders", current.status, data.status)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

    assert_order_financial_fields_mutable(current, update_dict)

    try:
        result = await service.update(id, update_dict)
        logger.info(f"Orders {id} updated successfully")
        return result
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error updating orders {id}: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating orders {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.delete("/batch")
async def delete_orderss_batch(
    request: OrdersBatchDeleteRequest,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("order.cancel")),
):
    """Delete multiple orderss by their IDs"""
    logger.debug(f"Batch deleting {len(request.ids)} orderss")
    
    service = OrdersService(db)
    deleted_count = 0
    
    try:
        for item_id in request.ids:
            success = await service.delete(item_id)
            if success:
                deleted_count += 1
        
        logger.info(f"Batch deleted {deleted_count} orderss successfully")
        return {"message": f"Successfully deleted {deleted_count} orderss", "deleted_count": deleted_count}
    except Exception as e:
        await db.rollback()
        logger.error(f"Error in batch delete: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Batch delete failed: {str(e)}")


@router.delete("/{id}")
async def delete_orders(
    id: int,
    db: AsyncSession = Depends(get_db),
    _user: UserResponse = Depends(require_permission("order.cancel")),
):
    """Delete a single orders by ID"""
    logger.debug(f"Deleting orders with id: {id}")
    
    service = OrdersService(db)
    try:
        success = await service.delete(id)
        if not success:
            logger.warning(f"Orders with id {id} not found for deletion")
            raise HTTPException(status_code=404, detail="Orders not found")
        
        logger.info(f"Orders {id} deleted successfully")
        return {"message": "Orders deleted successfully", "id": id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting orders {id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# ---------- Canonical Order-from-Quote Endpoint (WorkOS foundation) ----------
#
# Sprint #10 — Flow Hardening:
#   The rebuild below reconstructs a QuoteCalculationSnapshot that was previously
#   produced by a *priced* quote (so all numerics and units MUST already be
#   present). We do NOT invent defaults. Missing required field => 422 with
#   the explicit dotted field path. Genuinely optional fields stay None / empty.
#
# Field contract for the JSON dict `d`:
#   REQUIRED (422 on missing):
#     - status
#     - product_definition.product_id, product_type, quantity
#     - product_definition.layers[i].layer_id, layer_type, thickness_mm
#     - product_definition.layers[i].material.material_id, unit
#     - product_definition.layers[i].components[j].component_id, type, quantity, unit
#     - product_definition.layers[i].processes[j].process_id, type, estimated_time_minutes
#     - cost_result.currency, materials_cost, labour_cost, machine_cost,
#         external_cost, overhead_cost, total_cost, estimated_time_minutes, is_valid
#     - cost_result.breakdown[i].type, name, quantity, unit, unit_cost, total
#     - pricing.margin_pct, discount_pct, vat_pct
#     - price.net, gross, final
#   OPTIONAL fields stay None / empty — NO silent numeric defaults, NO silent
#   unit-string defaults, NO silent list substitutions for these:
#     - product_definition.dimensions (only required if referenced)
#     - product_definition.validation (informational)
#     - product_definition.layers[i].finish, material.name
#     - product_definition.layers[i].processes[j].machine_type
#     - cost_result.validation
#     - blocked_reasons (defaults to an empty list — this is a legitimate
#       empty collection, not a missing value).


class _SnapshotFieldMissing(Exception):
    """Raised when a REQUIRED field is absent in the serialized snapshot.

    This is NOT a fallback — the caller converts it into a 422 HTTPException
    with the exact dotted field path.
    """

    def __init__(self, field_path: str):
        super().__init__(field_path)
        self.field_path = field_path


def _require(d: dict, key: str, path: str):
    """Return `d[key]` if present and not None; otherwise raise _SnapshotFieldMissing.

    Treats absent keys and explicit None values as missing. An empty string is
    also treated as missing for REQUIRED string fields (e.g. `material_id`).
    Numeric zero is accepted — a zero cost is legitimate data. An empty list
    is accepted where lists are required; it conveys "no items" explicitly
    without inventing content.
    """
    if not isinstance(d, dict) or key not in d:
        raise _SnapshotFieldMissing(path)
    val = d[key]
    if val is None:
        raise _SnapshotFieldMissing(path)
    return val


def _require_str(d: dict, key: str, path: str) -> str:
    val = _require(d, key, path)
    if not isinstance(val, str) or val == "":
        raise _SnapshotFieldMissing(path)
    return val


def _require_number(d: dict, key: str, path: str) -> float:
    val = _require(d, key, path)
    try:
        return float(val)
    except (TypeError, ValueError):
        raise _SnapshotFieldMissing(path)


def _require_int(d: dict, key: str, path: str) -> int:
    val = _require(d, key, path)
    try:
        return int(val)
    except (TypeError, ValueError):
        raise _SnapshotFieldMissing(path)


def _require_list(d: dict, key: str, path: str) -> list:
    val = _require(d, key, path)
    if not isinstance(val, list):
        raise _SnapshotFieldMissing(path)
    return val


def _require_dict(d: dict, key: str, path: str) -> dict:
    val = _require(d, key, path)
    if not isinstance(val, dict):
        raise _SnapshotFieldMissing(path)
    return val


def _rebuild_snapshot_from_dict(d: dict) -> QuoteCalculationSnapshot:
    """Reconstruct QuoteCalculationSnapshot dataclass tree from its dict form.

    Strict rules (Sprint #10):
      - Zero silent fallbacks: any missing REQUIRED field raises
        HTTPException(422, detail={"error": "invalid_quote_snapshot",
        "missing_field": "<dotted.path>"}).
      - Optional fields remain None / empty when absent; we do NOT substitute
        silent defaults for missing numerics, unit strings, or list contents.
    """
    if not isinstance(d, dict):
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_quote_snapshot", "missing_field": "<root>"},
        )

    try:
        # ---- product_definition (REQUIRED root object) ----
        pd_d = _require_dict(d, "product_definition", "product_definition")
        product_id = _require_str(pd_d, "product_id", "product_definition.product_id")
        product_type = _require_str(pd_d, "product_type", "product_definition.product_type")
        quantity = _require_int(pd_d, "quantity", "product_definition.quantity")

        # Dimensions: optional object; if present each numeric must parse
        dimensions = ProductDimensions()
        if "dimensions" in pd_d and pd_d["dimensions"] is not None:
            dims_d = pd_d["dimensions"]
            if not isinstance(dims_d, dict):
                raise _SnapshotFieldMissing("product_definition.dimensions")
            dimensions = ProductDimensions(
                width_mm=float(dims_d["width_mm"]) if "width_mm" in dims_d and dims_d["width_mm"] is not None else 0,
                height_mm=float(dims_d["height_mm"]) if "height_mm" in dims_d and dims_d["height_mm"] is not None else 0,
                depth_mm=float(dims_d["depth_mm"]) if "depth_mm" in dims_d and dims_d["depth_mm"] is not None else 0,
            )

        # Layers: REQUIRED list (may be empty only if the snapshot really had no layers;
        # the key itself must be present)
        layers_raw = _require_list(pd_d, "layers", "product_definition.layers")
        layers: list = []
        for li, layer_d in enumerate(layers_raw):
            if not isinstance(layer_d, dict):
                raise _SnapshotFieldMissing(f"product_definition.layers[{li}]")
            layer_path = f"product_definition.layers[{li}]"

            layer_id = _require_str(layer_d, "layer_id", f"{layer_path}.layer_id")
            layer_type = _require_str(layer_d, "layer_type", f"{layer_path}.layer_type")
            thickness_mm = _require_number(layer_d, "thickness_mm", f"{layer_path}.thickness_mm")

            mat_d = _require_dict(layer_d, "material", f"{layer_path}.material")
            material = ProductMaterial(
                material_id=_require_str(mat_d, "material_id", f"{layer_path}.material.material_id"),
                name=mat_d.get("name") if isinstance(mat_d.get("name"), str) else "",
                unit=_require_str(mat_d, "unit", f"{layer_path}.material.unit"),
            )

            components_raw = _require_list(layer_d, "components", f"{layer_path}.components")
            components: list = []
            for ci, c in enumerate(components_raw):
                if not isinstance(c, dict):
                    raise _SnapshotFieldMissing(f"{layer_path}.components[{ci}]")
                comp_path = f"{layer_path}.components[{ci}]"
                components.append(
                    ProductComponent(
                        component_id=_require_str(c, "component_id", f"{comp_path}.component_id"),
                        type=_require_str(c, "type", f"{comp_path}.type"),
                        quantity=_require_number(c, "quantity", f"{comp_path}.quantity"),
                        unit=_require_str(c, "unit", f"{comp_path}.unit"),
                    )
                )

            processes_raw = _require_list(layer_d, "processes", f"{layer_path}.processes")
            processes: list = []
            for pi, p in enumerate(processes_raw):
                if not isinstance(p, dict):
                    raise _SnapshotFieldMissing(f"{layer_path}.processes[{pi}]")
                proc_path = f"{layer_path}.processes[{pi}]"
                processes.append(
                    ProductProcess(
                        process_id=_require_str(p, "process_id", f"{proc_path}.process_id"),
                        type=_require_str(p, "type", f"{proc_path}.type"),
                        machine_type=p.get("machine_type") if isinstance(p.get("machine_type"), str) else None,
                        estimated_time_minutes=_require_number(
                            p, "estimated_time_minutes", f"{proc_path}.estimated_time_minutes"
                        ),
                    )
                )

            finish_val = layer_d.get("finish")
            layers.append(
                ProductLayer(
                    layer_id=layer_id,
                    layer_type=layer_type,
                    material=material,
                    thickness_mm=thickness_mm,
                    finish=finish_val if isinstance(finish_val, str) else "",
                    components=components,
                    processes=processes,
                )
            )

        # Validation block on product_definition is informational; if present,
        # pass through as-is; if absent, leave default.
        validation = ProductValidationResult()
        if "validation" in pd_d and pd_d["validation"] is not None:
            val_d = pd_d["validation"]
            if not isinstance(val_d, dict):
                raise _SnapshotFieldMissing("product_definition.validation")
            validation = ProductValidationResult(
                is_valid=bool(val_d.get("is_valid", True)),
                missing_fields=list(val_d["missing_fields"]) if isinstance(val_d.get("missing_fields"), list) else [],
                warnings=list(val_d["warnings"]) if isinstance(val_d.get("warnings"), list) else [],
            )

        pd = ProductDefinition(
            product_id=product_id,
            product_type=product_type,
            quantity=quantity,
            dimensions=dimensions,
            layers=layers,
            validation=validation,
        )

        # ---- cost_result (REQUIRED) ----
        cr_d = _require_dict(d, "cost_result", "cost_result")
        currency = _require_str(cr_d, "currency", "cost_result.currency")
        materials_cost = _require_number(cr_d, "materials_cost", "cost_result.materials_cost")
        labour_cost = _require_number(cr_d, "labour_cost", "cost_result.labour_cost")
        machine_cost = _require_number(cr_d, "machine_cost", "cost_result.machine_cost")
        external_cost = _require_number(cr_d, "external_cost", "cost_result.external_cost")
        overhead_cost = _require_number(cr_d, "overhead_cost", "cost_result.overhead_cost")
        total_cost = _require_number(cr_d, "total_cost", "cost_result.total_cost")
        estimated_time_minutes = _require_number(
            cr_d, "estimated_time_minutes", "cost_result.estimated_time_minutes"
        )
        if "is_valid" not in cr_d or cr_d["is_valid"] is None:
            raise _SnapshotFieldMissing("cost_result.is_valid")
        cr_is_valid = bool(cr_d["is_valid"])

        breakdown_raw = _require_list(cr_d, "breakdown", "cost_result.breakdown")
        breakdown: list = []
        for bi, b in enumerate(breakdown_raw):
            if not isinstance(b, dict):
                raise _SnapshotFieldMissing(f"cost_result.breakdown[{bi}]")
            bp = f"cost_result.breakdown[{bi}]"
            breakdown.append(
                CostLine(
                    type=_require_str(b, "type", f"{bp}.type"),
                    name=_require_str(b, "name", f"{bp}.name"),
                    quantity=_require_number(b, "quantity", f"{bp}.quantity"),
                    unit=_require_str(b, "unit", f"{bp}.unit"),
                    unit_cost=_require_number(b, "unit_cost", f"{bp}.unit_cost"),
                    total=_require_number(b, "total", f"{bp}.total"),
                )
            )

        cost_validation = CostValidation()
        if "validation" in cr_d and cr_d["validation"] is not None:
            cr_val_d = cr_d["validation"]
            if not isinstance(cr_val_d, dict):
                raise _SnapshotFieldMissing("cost_result.validation")
            cost_validation = CostValidation(
                missing_cost_data=list(cr_val_d["missing_cost_data"])
                if isinstance(cr_val_d.get("missing_cost_data"), list)
                else [],
                warnings=list(cr_val_d["warnings"]) if isinstance(cr_val_d.get("warnings"), list) else [],
            )

        cost_result = CostResult(
            is_valid=cr_is_valid,
            currency=currency,
            materials_cost=materials_cost,
            labour_cost=labour_cost,
            machine_cost=machine_cost,
            external_cost=external_cost,
            overhead_cost=overhead_cost,
            total_cost=total_cost,
            estimated_time_minutes=estimated_time_minutes,
            breakdown=breakdown,
            validation=cost_validation,
        )

        # ---- pricing (REQUIRED) ----
        pricing_d = _require_dict(d, "pricing", "pricing")
        pricing = QuotePricing(
            margin_pct=_require_number(pricing_d, "margin_pct", "pricing.margin_pct"),
            discount_pct=_require_number(pricing_d, "discount_pct", "pricing.discount_pct"),
            vat_pct=_require_number(pricing_d, "vat_pct", "pricing.vat_pct"),
        )

        # ---- price (REQUIRED) ----
        price_d = _require_dict(d, "price", "price")
        price = QuotePrice(
            net=_require_number(price_d, "net", "price.net"),
            gross=_require_number(price_d, "gross", "price.gross"),
            final=_require_number(price_d, "final", "price.final"),
        )

        # ---- status (REQUIRED) ----
        status = _require_str(d, "status", "status")

        # ---- blocked_reasons (legitimately optional, empty list is valid) ----
        blocked_reasons: list = []
        if "blocked_reasons" in d and d["blocked_reasons"] is not None:
            if not isinstance(d["blocked_reasons"], list):
                raise _SnapshotFieldMissing("blocked_reasons")
            blocked_reasons = list(d["blocked_reasons"])

    except _SnapshotFieldMissing as exc:
        raise HTTPException(
            status_code=422,
            detail={"error": "invalid_quote_snapshot", "missing_field": exc.field_path},
        )

    return QuoteCalculationSnapshot(
        product_definition=pd,
        cost_result=cost_result,
        pricing=pricing,
        price=price,
        status=status,
        blocked_reasons=blocked_reasons,
    )



@router.post("/from-quote/{quote_id}", status_code=201)
async def create_order_from_quote(
    quote_id: int,
    acknowledge_readiness_warnings: bool = Body(False),
    readiness_warning_acknowledgement_reason: Optional[str] = Body(None),
    quote_output_snapshot_id: Optional[int] = Body(None),
    acknowledge_missing_document_snapshot: bool = Body(False),
    document_snapshot_acknowledgement_reason: Optional[str] = Body(None),
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_permission("order.create_from_quote")),
):
    """Create an Order from an existing priced Quote, snapshotting readiness_result."""
    logger.info(f"POST /api/v1/entities/orders/from-quote/{quote_id} invoked")

    quotes_service = QuotesService(db)
    orders_service = OrdersService(db)

    quote = await quotes_service.get_by_id(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="quote_not_found")
    # Allow conversion from "priced" (direct) or "accepted" (after client acceptance flow)
    _allowed_conversion_statuses = ("priced", "accepted")
    if quote.status not in _allowed_conversion_statuses:
        raise HTTPException(status_code=422, detail={"error": "quote_not_priced", "quote_status": quote.status})
    if not quote.line_items:
        raise HTTPException(status_code=422, detail={"error": "quote_snapshot_missing"})

    # Duplicate conversion guard: a quote can have a single canonical order.
    # Preserve historical duplicates as read-only artifacts; do not mutate them.
    existing_orders_result = await orders_service.get_list(
        skip=0,
        limit=1,
        query_dict={"quote_id": quote_id},
        sort="id",
    )
    existing_orders = existing_orders_result.get("items", [])
    if existing_orders:
        existing_order = existing_orders[0]
        raise HTTPException(
            status_code=409,
            detail={
                "error": "order_already_exists_for_quote",
                "quote_id": quote_id,
                "existing_order_id": existing_order.id,
                "existing_order_code": existing_order.code,
            },
        )

    component_breakdown = None
    execution_handoff: dict[str, Any] = {}
    try:
        wrapper_dict = json.loads(quote.line_items)
    except Exception as e:
        logger.error(f"Failed to parse quote.line_items JSON: {e}", exc_info=True)
        raise HTTPException(status_code=422, detail={"error": "quote_snapshot_invalid"})

    if isinstance(wrapper_dict, dict):
        cb = wrapper_dict.get("component_breakdown")
        if isinstance(cb, list) and len(cb) > 0:
            component_breakdown = cb
        for key in (
            "quote_input",
            "product_spec_json",
            "delivery_type",
            "face_vinyl_handoff",
            "plexiglass_face_nesting",
            "forex_backing_nesting",
            "flat_material_nesting_summary",
            "real_offcut_measurement_required",
            "post_cut_offcut_measurement_tasks",
            "offcut_inventory_intake",
        ):
            value = wrapper_dict.get(key)
            if value is not None:
                execution_handoff[key] = value

    snapshot_dict = wrapper_dict
    if isinstance(snapshot_dict, dict) and "line_items" in snapshot_dict:
        inner = snapshot_dict["line_items"]
        if isinstance(inner, dict):
            snapshot_dict = inner

    try:
        snapshot = _rebuild_snapshot_from_dict(snapshot_dict)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to rebuild snapshot: {e}", exc_info=True)
        raise HTTPException(status_code=422, detail={"error": "quote_snapshot_rebuild_failed"})

    # --- Extract readiness from quote snapshot ---
    readiness_result = snapshot_dict.get("readiness_result")
    readiness_warnings = []
    readiness_blockers = []
    readiness_blocked = False
    
    quote_gate = readiness_result.get("quote_gate") if isinstance(readiness_result, dict) else None
    uses_volumetric_quote_gate = isinstance(quote_gate, dict) and "can_create_commercial_quote" in quote_gate

    if readiness_result:
        overall_status = readiness_result.get("overall_status")
        ready_for_quote = readiness_result.get("ready_for_quote", False)

        # Volumetric commercial path: trust quote_gate.can_create_commercial_quote
        # (warning-only needs_review does not block when policy allows creation).
        if uses_volumetric_quote_gate:
            if overall_status == "blocked" or not quote_gate.get("can_create_commercial_quote"):
                readiness_blocked = True
                if isinstance(quote_gate.get("blockers"), list):
                    readiness_blockers.extend(quote_gate["blockers"])
        elif overall_status == "blocked" or not ready_for_quote:
            readiness_blocked = True
        
        # Collect blockers from top-level and canonical sections
        top_level_blockers = readiness_result.get("blockers", [])
        if isinstance(top_level_blockers, list):
            readiness_blockers.extend(top_level_blockers)
        
        _canonical_blocker_sections = [
            "technical_readiness",
            "costengine_readiness",
            "document_output_readiness",
            "visual_prompt_readiness",
            "execution_preparation_readiness",
        ]
        for section_key in _canonical_blocker_sections:
            section = readiness_result.get(section_key)
            if isinstance(section, dict):
                section_blockers = section.get("blockers", [])
                if isinstance(section_blockers, list):
                    readiness_blockers.extend(section_blockers)
        
        # Check for warnings across ALL canonical readiness sections.
        # Do NOT depend on overall_status == "warnings" — the canonical status
        # for warnings is "needs_review". Collect warnings from all sections
        # regardless of overall_status value.
        _canonical_warning_sections = [
            "technical_readiness",
            "costengine_readiness",
            "document_output_readiness",
            "visual_prompt_readiness",
            "execution_preparation_readiness",
        ]
        for section_key in _canonical_warning_sections:
            section = readiness_result.get(section_key)
            if isinstance(section, dict):
                section_warnings = section.get("warnings", [])
                if isinstance(section_warnings, list):
                    readiness_warnings.extend(section_warnings)
        
        # Also check top-level warnings list if present
        top_level_warnings = readiness_result.get("warnings", [])
        if isinstance(top_level_warnings, list):
            readiness_warnings.extend(top_level_warnings)
    
    # --- Enforce blocker gate at order creation ---
    if readiness_blocked:
        logger.warning(f"Order blocked due to product readiness: {readiness_blockers}")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "readiness_blocked_prevents_order",
                "blockers": readiness_blockers,
                "readiness_result": readiness_result,
            },
        )
    
    # --- Enforce warning acknowledgement gate ---
    # Acknowledgement is required when:
    # 1. warnings exist in any readiness section, AND
    # 2. policy.requires_warning_acknowledgement is true (or warnings exist without policy override)
    policy = readiness_result.get("policy", {}) if readiness_result else {}
    policy_requires_ack = policy.get("requires_warning_acknowledgement", True)  # default True if not specified
    requires_ack = bool(readiness_warnings) and bool(policy_requires_ack)
    if requires_ack and not acknowledge_readiness_warnings:
        logger.info(f"Order requires warning acknowledgement; {len(readiness_warnings)} warnings present")
        raise HTTPException(
            status_code=422,
            detail={
                "error": "readiness_warning_acknowledgement_required",
                "warnings": readiness_warnings,
                "readiness_result": readiness_result,
            },
        )
    
    # --- Build readiness_snapshot ---
    readiness_snapshot = {
        "source": "backend",
        "snapshot_type": "product_readiness_at_order_acceptance",
        "snapshot_at": datetime.now(timezone.utc).isoformat(),
        "readiness_result": readiness_result or {
            "entity_type": "order",
            "entity_id": "unknown",
            "overall_status": "unavailable",
            "ready_for_quote": False,
            "contract_version": "2026-05-15",
            "policy": {},
            "source": "backend",
        },
        "warnings_acknowledged": bool(readiness_warnings) and acknowledge_readiness_warnings,
        "warnings_acknowledged_at": datetime.now(timezone.utc).isoformat() if (bool(readiness_warnings) and acknowledge_readiness_warnings) else None,
        "warnings_acknowledgement_reason": readiness_warning_acknowledgement_reason if acknowledge_readiness_warnings else None,
    }

    try:
        order_snapshot: OrderSnapshot = OrderSnapshotService().create_from_quote(
            snapshot,
            component_breakdown=component_breakdown,
        )
    except ValueError as e:
        logger.warning(f"OrderSnapshotService rejected snapshot: {e}")
        raise HTTPException(status_code=422, detail={"error": "order_snapshot_rejected", "reason": str(e)})
    except Exception as e:
        logger.error(f"OrderSnapshotService failure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"order_snapshot_error: {e}")

    order_snapshot_dict = order_snapshot.to_dict()
    for key, value in execution_handoff.items():
        order_snapshot_dict[key] = value
    source_currency = extract_currency_from_quote_snapshot(snapshot)
    try:
        eur_to_ron_rate = await get_eur_to_ron_rate(db)
        currency_handoff = convert_quote_totals_to_order_base(
            gross_amount=float(order_snapshot.final_price.gross),
            net_amount=float(order_snapshot.final_price.net),
            source_currency=source_currency,
            eur_to_ron_rate=eur_to_ron_rate,
        )
    except ValueError as exc:
        code = str(exc)
        if code in {"eur_to_ron_rate_missing", "eur_to_ron_rate_invalid"}:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": code,
                    "message": "Setați cursul EUR/RON în Setări înainte de conversia ofertei în comandă.",
                },
            ) from exc
        raise HTTPException(status_code=422, detail={"error": "currency_conversion_failed", "reason": code}) from exc

    order_snapshot_dict["commercial_currency_handoff"] = currency_handoff.to_dict()
    order_snapshot_dict["final_price"] = {
        "net": currency_handoff.base_total_net if currency_handoff.base_total_net is not None else currency_handoff.base_total_ron,
        "gross": currency_handoff.base_total_ron,
    }

    order_code = f"ORD-{int(datetime.utcnow().timestamp())}-{quote_id}"
    order_data = {
        "code": order_code,
        "quote_id": quote_id,
        "quote_code": quote.code,
        "client_name": quote.client_name,
        "contact_person": quote.contact_person,
        "status": "locked",
        "payment_status": "pending",
        "total_amount": currency_handoff.base_total_ron,
        "locked_at": iso_now(),
        "snapshot_version": 1,
        "snapshot_line_items": json.dumps(order_snapshot_dict),
        "readiness_snapshot": readiness_snapshot,
    }

    try:
        order_obj = await orders_service.create(order_data)
    except Exception as e:
        logger.error(f"Order persistence failure: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"persistence_error: {e}")

    if not order_obj:
        raise HTTPException(status_code=500, detail="order_persistence_failed")

    # BUILD 26.18 — canonical snapshot/order_id contract:
    # persist the DB row id into snapshot.order_id so execution gate BLK-09
    # can cross-check row<->snapshot references without coercion failures.
    order_snapshot_dict["order_id"] = int(order_obj.id)
    order_obj.snapshot_line_items = json.dumps(order_snapshot_dict)

    # --- BUILD 12: Document snapshot reference integration ---
    document_snapshot_reference = None
    document_snapshot_warning = None
    try:
        doc_ref_service = OrderOutputSnapshotReferenceService(db)
        user_email = None
        if current_user and isinstance(current_user, dict):
            user_email = current_user.get("email") or current_user.get("sub")
        elif hasattr(current_user, "email"):
            user_email = current_user.email

        doc_result = await doc_ref_service.evaluate_and_create_reference(
            order_id=order_obj.id,
            quote_id=quote_id,
            explicit_snapshot_id=quote_output_snapshot_id,
            acknowledge_missing=acknowledge_missing_document_snapshot,
            acknowledgement_reason=document_snapshot_acknowledgement_reason,
            accepted_by=user_email,
        )
        document_snapshot_reference = doc_result.get("document_snapshot_reference")
        document_snapshot_warning = doc_result.get("document_snapshot_warning")
        doc_error = doc_result.get("error")

        # Document snapshot errors are non-blocking for order creation
        # but are reported as warnings in the response.
        if doc_error and doc_error not in (
            "document_snapshot_missing_not_acknowledged",
        ):
            logger.warning(
                f"Document snapshot reference issue for order {order_obj.id}: {doc_error}"
            )
            if not document_snapshot_warning:
                document_snapshot_warning = {
                    "code": doc_error,
                    "detail": doc_result.get("error_detail"),
                }
    except Exception as e:
        logger.error(f"Document snapshot reference creation failed: {e}", exc_info=True)
        document_snapshot_warning = {
            "code": "DOCUMENT_SNAPSHOT_REFERENCE_ERROR",
            "message": str(e),
        }

    await db.commit()

    return {
        "order_id": order_obj.id,
        "order_code": order_obj.code,
        "snapshot": order_snapshot_dict,
        "readiness_snapshot": readiness_snapshot,
        "commercial_currency_handoff": currency_handoff.to_dict(),
        "document_snapshot_reference": document_snapshot_reference,
        "document_snapshot_warning": document_snapshot_warning,
    }

@router.get("/{order_id}/document-snapshot-reference")
async def get_order_document_snapshot_reference(
    order_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get the document snapshot reference for an order."""
    logger.info(f"GET /api/v1/entities/orders/{order_id}/document-snapshot-reference")
    doc_ref_service = OrderOutputSnapshotReferenceService(db)
    reference = await doc_ref_service.get_by_order_id(order_id)
    if not reference:
        return {
            "order_id": order_id,
            "has_document_snapshot": False,
            "reference": None,
        }
    return {
        "order_id": order_id,
        "has_document_snapshot": True,
        "reference": reference,
    }


@router.get("/quote-acceptance-guard/{quote_id}")
async def quote_acceptance_guard(
    quote_id: int,
    db: AsyncSession = Depends(get_db),
):
    """
    Evaluate whether a quote is ready for acceptance/order conversion.
    Returns eligibility status including document snapshot readiness.
    Non-blocking: always returns 200 with status info.
    """
    logger.info(f"GET /api/v1/entities/orders/quote-acceptance-guard/{quote_id}")

    # Check quote exists and is in acceptable state
    quotes_service = QuotesService(db)
    quote = await quotes_service.get_by_id(quote_id)
    if not quote:
        raise HTTPException(status_code=404, detail="quote_not_found")

    guards = []
    overall_status = "eligible"

    # Guard 1: Quote must be in accepted/priced state
    quote_status = getattr(quote, "status", None)
    if quote_status not in ("accepted", "priced", "sent"):
        guards.append({
            "guard": "quote_status",
            "status": "blocked",
            "detail": f"Quote status '{quote_status}' is not eligible for order conversion",
            "required_status": ["accepted", "priced", "sent"],
        })
        overall_status = "blocked"

    # Guard 2: Document snapshot eligibility
    doc_ref_service = OrderOutputSnapshotReferenceService(db)
    doc_eligibility = await doc_ref_service.check_quote_document_eligibility(quote_id)
    doc_status = doc_eligibility.get("status", "unknown")

    if doc_status == "eligible":
        guards.append({
            "guard": "document_snapshot",
            "status": "eligible",
            "snapshot_id": doc_eligibility.get("snapshot_id"),
            "detail": "Approved document snapshot available",
        })
    elif doc_status == "missing":
        guards.append({
            "guard": "document_snapshot",
            "status": "warning",
            "detail": "No approved document snapshot found — acknowledgement required",
            "requires_acknowledgement": True,
        })
        if overall_status != "blocked":
            overall_status = "needs_acknowledgement"
    elif doc_status == "pending_review":
        guards.append({
            "guard": "document_snapshot",
            "status": "warning",
            "detail": "Document snapshot exists but is pending review",
            "requires_acknowledgement": True,
        })
        if overall_status != "blocked":
            overall_status = "needs_acknowledgement"
    else:
        guards.append({
            "guard": "document_snapshot",
            "status": "info",
            "detail": f"Document snapshot status: {doc_status}",
        })

    # Guard 3: Readiness check (delegate to existing readiness logic)
    try:
        from services.product_readiness_service import ProductReadinessService
        readiness_svc = ProductReadinessService()
        product_family = getattr(quote, "product_family", None)
        if product_family:
            readiness_result = readiness_svc.evaluate_readiness(
                product_family=product_family,
                parameters=getattr(quote, "parameters", {}),
            )
            has_blockers = any(
                item.get("severity") == "blocker"
                for item in readiness_result.get("items", [])
            )
            has_warnings = any(
                item.get("severity") == "warning"
                for item in readiness_result.get("items", [])
            )
            if has_blockers:
                guards.append({
                    "guard": "product_readiness",
                    "status": "blocked",
                    "detail": "Product readiness has blockers",
                    "blockers": [
                        i for i in readiness_result.get("items", [])
                        if i.get("severity") == "blocker"
                    ],
                })
                overall_status = "blocked"
            elif has_warnings:
                guards.append({
                    "guard": "product_readiness",
                    "status": "warning",
                    "detail": "Product readiness has warnings",
                    "warnings": [
                        i for i in readiness_result.get("items", [])
                        if i.get("severity") == "warning"
                    ],
                    "requires_acknowledgement": True,
                })
                if overall_status != "blocked":
                    overall_status = "needs_acknowledgement"
            else:
                guards.append({
                    "guard": "product_readiness",
                    "status": "eligible",
                    "detail": "Product readiness OK",
                })
        else:
            guards.append({
                "guard": "product_readiness",
                "status": "info",
                "detail": "No product family on quote — readiness check skipped",
            })
    except Exception as e:
        logger.warning(f"Readiness guard evaluation failed: {e}")
        guards.append({
            "guard": "product_readiness",
            "status": "info",
            "detail": "Readiness evaluation unavailable",
        })

    return {
        "quote_id": quote_id,
        "overall_status": overall_status,
        "guards": guards,
    }
