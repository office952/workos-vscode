"""Pydantic schemas for Intake V5."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Form inputs — what the operator fills in
# ---------------------------------------------------------------------------
class IntakeV5Inputs(BaseModel):
    """All inputs needed to compute a volumetric-letters BOM."""

    svg_analysis: Optional[dict[str, Any]] = Field(
        None,
        description="Analiză SVG folosită pentru auto-fill și audit template v2",
    )

    width_mm: Optional[float] = Field(None, gt=0, description="Lățime totală lucrare (mm)")
    height_mm: Optional[float] = Field(None, gt=0, description="Înălțime totală lucrare (mm)")

    letter_count: int = Field(..., ge=1, description="Număr litere")
    letter_face_area_m2: float = Field(..., gt=0, description="Suprafață totală față litere (mp)")
    letter_perimeter_m: float = Field(..., gt=0, description="Perimetru total litere (m)")

    face_finish_type: Literal[
        "none", "oracal_641", "oracal_651", "oracal_8500",
        "printed_vinyl", "printed_laminated_vinyl",
    ] = "oracal_651"

    return_depth_mm: Literal[30, 60, 80, 100] = 60

    return_finish_type: Literal[
        "white_aluminum", "black_aluminum", "gold_aluminum",
        "mirror_silver", "ral_paint", "oracal_wrapped",
    ] = "white_aluminum"

    illuminated: bool = True
    lighting_system_type: Literal["led_modules", "led_strip"] = "led_modules"
    selected_psu_watts: Literal[60, 100, 160, 200] = 100

    backing_enabled: bool = True
    back_bevel_enabled: bool = False

    mounting_system: Literal[
        "direct_wall", "steel_bars", "aluminum_bars", "acm_panel",
    ] = "direct_wall"

    mounting_template_enabled: bool = True
    mounting_template_area_m2: Optional[float] = Field(None, gt=0, description="Suprafață șablon montaj (mp)")
    mounting_template_material_type: Literal["forex", "paper"] = "forex"
    mounting_bar_count: int = Field(2, ge=0, description="Număr bare premontaj")
    mounting_bar_length_m: Optional[float] = Field(None, gt=0, description="Lungime per bară premontaj (m)")

    paint_tube_count: int = Field(0, ge=0, description="Tuburi vopsea RAL (când ral_paint)")


# ---------------------------------------------------------------------------
# BOM rows
# ---------------------------------------------------------------------------
class BomMaterialRow(BaseModel):
    code: str
    name: str
    qty: float
    unit: str
    unit_cost: float
    total: float
    notes: str = ""


class BomOperationRow(BaseModel):
    code: str
    name: str
    qty: float
    unit: str
    rate: float
    total: float
    notes: str = ""


class BomTaskRow(BaseModel):
    sequence: int
    code: str
    name: str
    workcenter: str
    estimated_minutes: float
    depends_on: list[str] = []


class BomResult(BaseModel):
    materials: list[BomMaterialRow]
    operations: list[BomOperationRow]
    tasks: list[BomTaskRow]
    material_total_eur: float
    operation_total_eur: float
    grand_total_eur: float
    currency: str = "EUR"
    notes: list[str] = []


# ---------------------------------------------------------------------------
# API request / response
# ---------------------------------------------------------------------------
class IntakeV5CreateRequest(BaseModel):
    client_name: str = Field(..., min_length=1)
    job_title: str = ""
    inputs: IntakeV5Inputs


class IntakeV5UpdateRequest(BaseModel):
    client_name: Optional[str] = None
    job_title: Optional[str] = None
    inputs: Optional[IntakeV5Inputs] = None


class IntakeV5ProjectResponse(BaseModel):
    id: int
    code: str
    template_code: str
    status: str
    client_name: str
    job_title: Optional[str]
    inputs: IntakeV5Inputs
    bom: Optional[BomResult]
    material_total_eur: Optional[float]
    operation_total_eur: Optional[float]
    grand_total_eur: Optional[float]
    quote_id: Optional[int]
    order_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class IntakeV5ListItem(BaseModel):
    id: int
    code: str
    status: str
    client_name: str
    job_title: Optional[str]
    grand_total_eur: Optional[float]
    quote_id: Optional[int]
    order_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True
