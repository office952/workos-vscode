"""CNC material process profiles — stock, pricing keys, and machining rules per material.

Links shared CNC operations to inventory materials without mixing material rows
with operation rows. Preview-only: never consumes stock or invents prices.

Operational volumetric codes (MAT-ACP-FATA-LITERE, MAT-SPATE-PVC-LITERE) are the
current inventory linkage — not hypothetical MAT-PLEXIGLAS-3MM until owner migrates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Sequence

from services.shared_cnc_operation_model import (
    CncMaterialSource,
    DEFAULT_CNC_PRICING_RATE_KEY,
    DEFAULT_DEPTH_PER_PASS_MM,
    FOREX_10MM_CUTTING_PASSES_OWNER,
    build_cutting_service_cnc_operation_rows,
)

StockMappingStatus = Literal["mapped", "pending_mapping"]
MaterialPricingStatus = Literal["missing_rate", "pending_mapping", "configured_preview"]

CLIENT_SUPPLIED_MATERIAL_WARNING = (
    "Material adus de client — nu se consumă stoc intern. Calitatea, planeitatea, "
    "fisurile, defectele ascunse și compatibilitatea CNC trebuie verificate înainte "
    "de producție. Clientul trebuie să asigure material suplimentar pentru prindere, "
    "test și pierderi."
)


@dataclass(frozen=True)
class CncMaterialProcessProfile:
    material_key: str
    material_family: str
    material_name: str
    thickness_mm: float
    stock_material_key: str | None
    stock_unit: str
    standard_sheet_width_mm: float | None = None
    standard_sheet_height_mm: float | None = None
    default_waste_factor: float | None = None
    pricing_material_rate_key: str | None = None
    stock_mapping_status: StockMappingStatus = "pending_mapping"
    material_pricing_status: MaterialPricingStatus = "pending_mapping"
    allowed_operations: tuple[str, ...] = ()
    cutting_depth_per_pass_mm: float = DEFAULT_DEPTH_PER_PASS_MM
    cutting_passes: int = 1
    owner_pass_override: bool = False
    bevel_allowed: bool = False
    bevel_default: bool = False
    compatible_machine_keys: tuple[str, ...] = ()
    required_skill_keys: tuple[str, ...] = ()
    cutting_operation_pricing_rate_key: str = DEFAULT_CNC_PRICING_RATE_KEY
    bevel_operation_pricing_rate_key: str | None = None
    operation_pricing_status: MaterialPricingStatus = "missing_rate"
    notes: str = ""


@dataclass
class CncMaterialCostPreviewRow:
    row_type: Literal["material"] = "material"
    material_key: str = ""
    display_name: str = ""
    quantity: float = 0.0
    unit: str = "m2"
    stock_material_key: str | None = None
    material_source: CncMaterialSource = CncMaterialSource.INTERNAL_STOCK
    pricing_status: str = "missing_rate"
    stock_mapping_status: StockMappingStatus = "pending_mapping"
    pricing_material_rate_key: str | None = None
    unit_price: float | None = None
    estimated_cost: float | None = None
    consumes_stock_now: bool = False
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "row_type": self.row_type,
            "material_key": self.material_key,
            "display_name": self.display_name,
            "quantity": self.quantity,
            "unit": self.unit,
            "stock_material_key": self.stock_material_key,
            "material_source": self.material_source.value,
            "pricing_status": self.pricing_status,
            "stock_mapping_status": self.stock_mapping_status,
            "pricing_material_rate_key": self.pricing_material_rate_key,
            "unit_price": self.unit_price,
            "estimated_cost": self.estimated_cost,
            "consumes_stock_now": self.consumes_stock_now,
            "warnings": list(self.warnings),
        }


# Operational inventory codes — aligned with intake_v4_material_breakdown_service.MATERIAL_REGISTRY_CODES
PLEXIGLAS_3MM_PROFILE = CncMaterialProcessProfile(
    material_key="plexiglas_3mm",
    material_family="plexiglas",
    material_name="Plexiglas 3 mm",
    thickness_mm=3.0,
    stock_material_key="MAT-ACP-FATA-LITERE",
    stock_unit="m2",
    standard_sheet_width_mm=2050.0,
    standard_sheet_height_mm=3050.0,
    default_waste_factor=None,
    pricing_material_rate_key="inventory_materials:MAT-ACP-FATA-LITERE",
    stock_mapping_status="mapped",
    material_pricing_status="pending_mapping",
    allowed_operations=("cutting", "bevel"),
    cutting_depth_per_pass_mm=DEFAULT_DEPTH_PER_PASS_MM,
    cutting_passes=1,
    owner_pass_override=False,
    bevel_allowed=True,
    bevel_default=True,
    compatible_machine_keys=("cnc_router",),
    required_skill_keys=("cnc_operator",),
    cutting_operation_pricing_rate_key=DEFAULT_CNC_PRICING_RATE_KEY,
    bevel_operation_pricing_rate_key=DEFAULT_CNC_PRICING_RATE_KEY,
    operation_pricing_status="missing_rate",
    notes=(
        "Față litere volumetrice; șanfren față obligatoriu în TPL-VOLUMETRIC-LETTERS. "
        "Cod stoc operațional MAT-ACP-FATA-LITERE (PMMA 3 mm — cod legacy ACP în nume)."
    ),
)

FOREX_10MM_PROFILE = CncMaterialProcessProfile(
    material_key="forex_10mm",
    material_family="forex",
    material_name="Forex 10 mm",
    thickness_mm=10.0,
    stock_material_key="MAT-SPATE-PVC-LITERE",
    stock_unit="m2",
    standard_sheet_width_mm=2050.0,
    standard_sheet_height_mm=3050.0,
    default_waste_factor=None,
    pricing_material_rate_key="inventory_materials:MAT-SPATE-PVC-LITERE",
    stock_mapping_status="mapped",
    material_pricing_status="pending_mapping",
    allowed_operations=("cutting", "bevel"),
    cutting_depth_per_pass_mm=DEFAULT_DEPTH_PER_PASS_MM,
    cutting_passes=FOREX_10MM_CUTTING_PASSES_OWNER,
    owner_pass_override=True,
    bevel_allowed=True,
    bevel_default=False,
    compatible_machine_keys=("cnc_router",),
    required_skill_keys=("cnc_operator",),
    cutting_operation_pricing_rate_key=DEFAULT_CNC_PRICING_RATE_KEY,
    bevel_operation_pricing_rate_key=DEFAULT_CNC_PRICING_RATE_KEY,
    operation_pricing_status="missing_rate",
    notes=(
        "Backing litere volumetrice. Debitare 10 mm folosește regula owner: 5 treceri. "
        "Cod stoc MAT-SPATE-PVC-LITERE (PVC expandat 10 mm / Forex — cod istoric)."
    ),
)

CNC_MATERIAL_PROCESS_PROFILES: dict[str, CncMaterialProcessProfile] = {
    PLEXIGLAS_3MM_PROFILE.material_key: PLEXIGLAS_3MM_PROFILE,
    FOREX_10MM_PROFILE.material_key: FOREX_10MM_PROFILE,
}

VOLUMETRIC_LETTER_CNC_PROFILE_KEYS: tuple[str, ...] = (
    PLEXIGLAS_3MM_PROFILE.material_key,
    FOREX_10MM_PROFILE.material_key,
)


def get_material_process_profile(material_key: str) -> CncMaterialProcessProfile | None:
    return CNC_MATERIAL_PROCESS_PROFILES.get(material_key)


def build_material_cost_preview_row(
    profile: CncMaterialProcessProfile,
    quantity: float,
    unit: str,
    *,
    material_source: CncMaterialSource,
    unit_price: float | None = None,
    display_name_suffix: str | None = None,
) -> CncMaterialCostPreviewRow | None:
    """Build a material cost preview row. Returns None for client-supplied (no internal material row)."""
    if material_source == CncMaterialSource.CLIENT_SUPPLIED:
        return None

    if quantity <= 0:
        return None

    display = profile.material_name
    if display_name_suffix:
        display = f"{profile.material_name} / {display_name_suffix}"

    pricing_status = profile.material_pricing_status
    estimated_cost: float | None = None
    if unit_price is not None and unit_price > 0:
        estimated_cost = round(quantity * unit_price, 4)
        pricing_status = "configured_preview"

    warnings: list[str] = []
    if profile.stock_mapping_status == "pending_mapping":
        warnings.append("stock_mapping_pending")
    if pricing_status in {"missing_rate", "pending_mapping"}:
        warnings.append("material_price_missing")

    return CncMaterialCostPreviewRow(
        material_key=profile.material_key,
        display_name=display,
        quantity=round(quantity, 4),
        unit=unit,
        stock_material_key=profile.stock_material_key,
        material_source=material_source,
        pricing_status=pricing_status,
        stock_mapping_status=profile.stock_mapping_status,
        pricing_material_rate_key=profile.pricing_material_rate_key,
        unit_price=unit_price,
        estimated_cost=estimated_cost,
        consumes_stock_now=False,
        warnings=warnings,
    )


def build_cutting_service_preview_bundle(
    *,
    material_source: CncMaterialSource,
    material_key: str,
    area_m2: float | None,
    perimeter_ml: float | None,
    bevel_enabled: bool = False,
    configured_material_unit_price: float | None = None,
    configured_rate_eur_per_ml_pass: float | None = None,
) -> tuple[list[CncMaterialCostPreviewRow], list, list[str]]:
    """Foundation bundle for TPL-CNC-CUTTING-SERVICE — material + CNC operation previews."""
    profile = get_material_process_profile(material_key)
    warnings: list[str] = []
    material_rows: list[CncMaterialCostPreviewRow] = []

    if material_source == CncMaterialSource.CLIENT_SUPPLIED:
        warnings.append(CLIENT_SUPPLIED_MATERIAL_WARNING)
    elif profile is None:
        warnings.append(f"unknown_material_profile:{material_key}")
    elif area_m2 is not None and area_m2 > 0:
        row = build_material_cost_preview_row(
            profile,
            area_m2,
            profile.stock_unit,
            material_source=material_source,
            unit_price=configured_material_unit_price,
        )
        if row is not None:
            material_rows.append(row)

    if profile is None:
        return material_rows, [], warnings

    op_rows, op_warnings = build_cutting_service_cnc_operation_rows(
        material_source=material_source,
        perimeter_ml=perimeter_ml,
        thickness_mm=profile.thickness_mm,
        material_family=profile.material_family,
        material_name=profile.material_name,
        cutting_enabled=True,
        bevel_enabled=bevel_enabled and profile.bevel_allowed,
        passes_override=profile.cutting_passes if profile.owner_pass_override else None,
        owner_pass_override=profile.owner_pass_override,
        configured_rate_eur_per_ml_pass=configured_rate_eur_per_ml_pass,
    )
    for row in op_rows:
        row.material_key = profile.material_key
        row.consumes_stock_now = False
        row.creates_task_now = False

    warnings.extend(op_warnings)
    return material_rows, op_rows, warnings


def material_rows_to_schema_dicts(rows: Sequence[CncMaterialCostPreviewRow]) -> list[dict[str, Any]]:
    return [row.to_dict() for row in rows]
