from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from models.inventory_materials import Inventory_materials
from models.product_templates import Product_templates
from services.inventory_sheet_service import InventorySheetContractError, build_inventory_sheet_payload
from services.fiscal_lookup_service import run_fiscal_lookup
from services.smartbill_client import normalize_tax_id

router = APIRouter(
    prefix="/api/v1/intake-assist",
    tags=["intake_assist"],
    dependencies=[Depends(get_current_user)],
)


class IntakeDimensions(BaseModel):
    width: float | None = None
    height: float | None = None
    depth: float | None = None
    unit: str = "mm"


class ProductTemplateAssistItem(BaseModel):
    id: str
    name: str
    family: str
    category: str | None = None
    status: Literal["active", "draft", "deprecated", "inactive", "unknown"]
    description: str | None = None
    supported_intake_fields: list[str]
    requires_review: bool
    warnings: list[str]


class ProductTemplateAssistListResponse(BaseModel):
    source: Literal["backend"] = "backend"
    items: list[ProductTemplateAssistItem]
    warnings: list[str] = Field(default_factory=list)
    contract_version: str = "2026-05-14"


class ProductTemplateSuggestionRequest(BaseModel):
    intake_id: str | None = None
    title: str | None = None
    description: str | None = None
    requested_product_type: str | None = None
    dimensions: IntakeDimensions | None = None
    quantity: int = 1
    finish_notes: str | None = None
    mounting_notes: str | None = None


class ProductTemplateSuggestionItem(BaseModel):
    template_id: str
    template_name: str
    family: str
    confidence: Literal["high", "medium", "low"]
    match_reasons: list[str]
    missing_inputs: list[str]
    warnings: list[str]
    requires_operator_confirmation: bool = True


class ProductTemplateSuggestionResponse(BaseModel):
    source: Literal["backend"] = "backend"
    suggestions: list[ProductTemplateSuggestionItem]
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    contract_version: str = "2026-05-14"


class MaterialSheetAssistRequest(BaseModel):
    product_template_id: str | None = None
    material_category: str | None = None
    dimensions: IntakeDimensions | None = None
    quantity: int = 1
    constraints: dict[str, Any] | None = None


class MaterialSheetFormat(BaseModel):
    type: Literal["none", "sheet", "roll", "linear", "piece", "unknown"]
    width: float | None = None
    height: float | None = None
    unit: Literal["mm", "cm", "m", "unknown"] = "unknown"
    usable_width: float | None = None
    usable_height: float | None = None
    thickness: float | None = None
    thickness_unit: Literal["mm", "cm", "m", "unknown"] = "unknown"
    verified: bool = False
    source: Literal["manual", "supplier", "imported", "unknown"] = "unknown"


class MaterialSheetAssistItem(BaseModel):
    material_id: str
    material_name: str
    category: str
    status: Literal["active", "missing_price", "needs_owner_input", "unknown"]
    unit: Literal["sqm", "pcs", "ml", "sheet", "unknown"]
    sheet_format: MaterialSheetFormat | None = None
    fit_status: Literal["fits", "fits_rotated", "does_not_fit", "unknown"] = "unknown"
    fit_reason: str = ""
    warnings: list[str] = Field(default_factory=list)
    requires_review: bool = True


class MaterialSheetAssistResponse(BaseModel):
    source: Literal["backend"] = "backend"
    assist_available: bool
    items: list[MaterialSheetAssistItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    contract_version: str = "2026-05-14"


class FiscalLookupRequest(BaseModel):
    provider: Literal["anaf", "smartbill", "auto"] = "auto"
    country: Literal["RO"] = "RO"
    tax_id: str | None = None
    cui: str | None = None


class FiscalLookupNormalized(BaseModel):
    tax_id: str
    company_name: str
    registration_number: str | None = None
    address: str | None = None
    city: str | None = None
    county: str | None = None
    country: Literal["RO"] = "RO"
    vat_payer: bool
    source: Literal["anaf", "smartbill"] = "anaf"


class FiscalLookupResponse(BaseModel):
    available: bool
    provider: Literal["anaf", "smartbill"]
    status: Literal[
        "not_configured",
        "invalid_input",
        "found",
        "not_found",
        "provider_timeout",
        "provider_error",
        "rate_limited",
    ]
    message: str
    normalized: FiscalLookupNormalized | None = None
    warnings: list[str]
    requires_operator_confirmation: bool = False


def _template_status(tpl: Product_templates) -> Literal["active", "draft", "deprecated", "inactive", "unknown"]:
    if tpl.active is True:
        return "active"
    if tpl.active is False:
        return "inactive"
    return "unknown"


def _extract_material_codes(required_materials_json: str | None) -> list[str]:
    if not required_materials_json:
        return []
    try:
        raw = json.loads(required_materials_json)
    except Exception:
        return []
    if not isinstance(raw, list):
        return []

    out: list[str] = []
    for row in raw:
        if not isinstance(row, dict):
            continue
        code = row.get("materialCode") or row.get("material_code")
        if isinstance(code, str) and code.strip():
            out.append(code.strip())
    return out


def _apply_template_filters(query: Select[Any], family_id: str | None, q: str | None) -> Select[Any]:
    if family_id:
        query = query.where(Product_templates.family_id == family_id)
    if q:
        like = f"%{q}%"
        query = query.where(
            Product_templates.template_code.ilike(like)
            | Product_templates.family_name.ilike(like)
            | Product_templates.description.ilike(like)
        )
    return query


def _normalized_material_status(raw: str | None) -> Literal["active", "missing_price", "needs_owner_input", "unknown"]:
    status = (raw or "unknown").lower()
    if status not in {"active", "missing_price", "needs_owner_input"}:
        return "unknown"
    return status


def _normalized_inventory_unit(raw: str | None) -> Literal["sqm", "pcs", "ml", "sheet", "unknown"]:
    unit_map = {
        "mp": "sqm",
        "m2": "sqm",
        "buc": "pcs",
        "pcs": "pcs",
        "ml": "ml",
        "sheet": "sheet",
    }
    return unit_map.get((raw or "").lower(), "unknown")


def _normalized_sheet_unit(raw: str | None) -> Literal["mm", "cm", "m", "unknown"]:
    unit = (raw or "unknown").lower().strip()
    if unit in {"mm", "cm", "m"}:
        return unit  # type: ignore[return-value]
    return "unknown"


def _normalized_sheet_type(raw: str | None) -> Literal["none", "sheet", "roll", "linear", "piece", "unknown"]:
    value = (raw or "unknown").lower().strip()
    if value in {"none", "sheet", "roll", "linear", "piece", "unknown"}:
        return value  # type: ignore[return-value]
    return "unknown"


def _normalized_format_source(raw: str | None) -> Literal["manual", "supplier", "imported", "unknown"]:
    value = (raw or "unknown").lower().strip()
    if value in {"manual", "supplier", "imported", "unknown"}:
        return value  # type: ignore[return-value]
    return "unknown"


def _is_sheet_format_configured(mat: Inventory_materials) -> bool:
    if _normalized_sheet_type(mat.sheet_format_type) != "sheet":
        return False
    if mat.sheet_width is None or mat.sheet_height is None:
        return False
    if mat.sheet_width <= 0 or mat.sheet_height <= 0:
        return False
    return _normalized_sheet_unit(mat.sheet_unit) != "unknown"


@router.get("/product-templates", response_model=ProductTemplateAssistListResponse)
async def list_product_templates_assist(
    family_id: str | None = None,
    q: str | None = None,
    include_inactive: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    query = select(Product_templates)
    query = _apply_template_filters(query, family_id=family_id, q=q)
    if not include_inactive:
        query = query.where(Product_templates.active == True)  # noqa: E712
    query = query.order_by(Product_templates.id.desc()).limit(max(1, min(limit, 200)))

    rows = (await db.execute(query)).scalars().all()
    items: list[ProductTemplateAssistItem] = []
    for tpl in rows:
        items.append(
            ProductTemplateAssistItem(
                id=str(tpl.id),
                name=tpl.template_code,
                family=tpl.family_name,
                category=tpl.family_id,
                status=_template_status(tpl),
                description=tpl.description,
                supported_intake_fields=[
                    "product_family",
                    "description",
                    "dimensions",
                    "quantity",
                    "delivery_type",
                ],
                requires_review=True,
                warnings=[],
            )
        )

    return ProductTemplateAssistListResponse(items=items)


@router.post("/product-template-suggestions", response_model=ProductTemplateSuggestionResponse)
async def suggest_product_templates_assist(
    body: ProductTemplateSuggestionRequest,
    db: AsyncSession = Depends(get_db),
):
    query = select(Product_templates).where(Product_templates.active == True)  # noqa: E712

    # Suggestions are strictly read-only and based on existing registry metadata.
    if body.requested_product_type:
        query = query.where(Product_templates.family_id == body.requested_product_type)

    templates = (await db.execute(query.order_by(Product_templates.id.desc()).limit(100))).scalars().all()

    text_tokens = " ".join(
        part for part in [body.title or "", body.description or "", body.requested_product_type or ""] if part
    ).lower()

    suggestions: list[ProductTemplateSuggestionItem] = []
    for tpl in templates:
        reasons: list[str] = []
        score = 0

        family_id = (tpl.family_id or "").lower()
        family_name = (tpl.family_name or "").lower()
        template_code = (tpl.template_code or "").lower()

        if body.requested_product_type and body.requested_product_type.lower() == family_id:
            score += 4
            reasons.append("requested_product_type matches template family_id")

        if family_name and family_name in text_tokens:
            score += 2
            reasons.append("family_name found in intake text")

        if template_code and template_code in text_tokens:
            score += 1
            reasons.append("template_code found in intake text")

        if score <= 0:
            continue

        missing_inputs: list[str] = []
        if not body.dimensions or body.dimensions.width is None or body.dimensions.height is None:
            missing_inputs.append("dimensions.width")
            missing_inputs.append("dimensions.height")

        confidence: Literal["high", "medium", "low"]
        if score >= 4:
            confidence = "high"
        elif score >= 2:
            confidence = "medium"
        else:
            confidence = "low"

        suggestions.append(
            ProductTemplateSuggestionItem(
                template_id=str(tpl.id),
                template_name=tpl.template_code,
                family=tpl.family_name,
                confidence=confidence,
                match_reasons=reasons,
                missing_inputs=missing_inputs,
                warnings=[],
                requires_operator_confirmation=True,
            )
        )

    if not suggestions:
        return ProductTemplateSuggestionResponse(
            suggestions=[],
            warnings=["Template suggestion requires backend mapping not yet configured."],
            blockers=[],
        )

    return ProductTemplateSuggestionResponse(suggestions=suggestions[:10], warnings=[], blockers=[])


@router.post("/material-sheet-assist", response_model=MaterialSheetAssistResponse)
async def get_material_sheet_assist(
    body: MaterialSheetAssistRequest,
    db: AsyncSession = Depends(get_db),
):
    materials_query = select(Inventory_materials)
    if body.material_category:
        materials_query = materials_query.where(Inventory_materials.category == body.material_category)

    if body.product_template_id:
        try:
            template_id = int(body.product_template_id)
        except ValueError:
            template_id = None
        if template_id is not None:
            tpl = (await db.execute(select(Product_templates).where(Product_templates.id == template_id))).scalar_one_or_none()
            if tpl is not None:
                material_codes = _extract_material_codes(tpl.required_materials_json)
                if material_codes:
                    materials_query = materials_query.where(Inventory_materials.code.in_(material_codes))

    materials = (await db.execute(materials_query.order_by(Inventory_materials.id.desc()).limit(100))).scalars().all()

    try:
        payload = build_inventory_sheet_payload(
            materials=list(materials),
            dimensions=body.dimensions.model_dump() if body.dimensions else None,
            constraints=body.constraints,
        )
    except InventorySheetContractError as exc:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "inventory_sheet_contract_error",
                "code": exc.code,
                "field": exc.field,
                "message": exc.message,
            },
        ) from exc

    return MaterialSheetAssistResponse(**payload)


@router.post("/fiscal-lookup", response_model=FiscalLookupResponse)
async def fiscal_lookup_boundary(body: FiscalLookupRequest, db: AsyncSession = Depends(get_db)):
    raw_tax_id = body.tax_id or body.cui or ""
    normalized_tax_id = normalize_tax_id(raw_tax_id, country=body.country)
    if not normalized_tax_id:
        return FiscalLookupResponse(
            available=False,
            provider="anaf",
            status="invalid_input",
            message="Invalid tax_id format. Expected RO CUI (with or without RO prefix).",
            warnings=["Fiscal lookup input validation failed."],
        )

    result, resolved_provider = await run_fiscal_lookup(
        provider=body.provider,
        country=body.country,
        tax_id=normalized_tax_id,
        db=db,
    )

    return FiscalLookupResponse(
        available=result.status == "found",
        provider=resolved_provider,
        status=result.status,
        message=result.message,
        normalized=FiscalLookupNormalized(**result.normalized) if result.normalized else None,
        warnings=result.warnings,
        requires_operator_confirmation=result.status == "found",
    )
