"""Intake V5 — end-to-end service for TPL-VOLUMETRIC-LETTERS.

Pure BOM calculation + quote/order/task flow using existing tables.
All prices come from inventory_materials and workcenter_rates registries.
"""

from __future__ import annotations

import json
import logging
import math
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.intake_v5_project import IntakeV5Project
from models.quotes import Quotes
from models.orders import Orders
from models.execution_plan import ExecutionPlan
from schemas.intake_v5 import (
    BomMaterialRow,
    BomOperationRow,
    BomResult,
    BomTaskRow,
    IntakeV5Inputs,
)

logger = logging.getLogger(__name__)

TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS_v2"

REQUIRED_MATERIAL_CODES = [
    "MAT-ACP-FATA-LITERE",
    "MAT-SPATE-PVC-LITERE",
    "MAT-PROFIL-LATERAL-LITERE-30MM",
    "MAT-PROFIL-LATERAL-LITERE-60MM",
    "MAT-PROFIL-LATERAL-LITERE-80MM",
    "MAT-PROFIL-LATERAL-LITERE-100MM",
    "MAT-ORACAL-641",
    "MAT-ORACAL-651",
    "MAT-ORACAL-8500",
    "MAT-VINYL-PRINT",
    "MAT-VINYL-PRINT-LAMINATED",
    "MAT-LED-MODULE",
    "MAT-LED-STRIP",
    "MAT-LED-PSU-12V-60W",
    "MAT-LED-PSU-12V-100W",
    "MAT-LED-PSU-12V-160W",
    "MAT-LED-PSU-12V-200W",
    "MAT-VOPSEA-RAL",
    "MAT-SABLON-MONTAJ",
    "MAT-SABLON-HARTIE",
    "MAT-PREMOUNT-BAR-STEEL",
    "MAT-PREMOUNT-BAR-ALUMINUM",
    "MAT-CONSUMABILE-MONTAJ",
]

REQUIRED_WORKCENTER_CODES = [
    "PREPRESS",
    "CNC_ROUTER",
    "RETURN_PROFILE_MACHINE_FORMING",
    "RETURN_PROFILE_FACE_BONDING",
    "PAINTING",
    "FACE_VINYL_APPLICATION_LABOR",
    "LARGE_FORMAT_PRINT",
    "LAMINATION",
    "LED_ASSEMBLY",
    "ELECTRICAL_WIRING",
    "PACKAGING",
]

FORM_FIELD_DEFINITIONS = [
    {"key": "width_mm", "label": "Lățime lucrare", "section": "geometry", "input_type": "number", "unit": "mm", "source": "svg_analysis_or_manual"},
    {"key": "height_mm", "label": "Înălțime lucrare", "section": "geometry", "input_type": "number", "unit": "mm", "source": "svg_analysis_or_manual"},
    {"key": "letter_count", "label": "Număr litere", "section": "geometry", "input_type": "number", "unit": "buc", "source": "svg_analysis_or_manual"},
    {"key": "letter_face_area_m2", "label": "Suprafață față", "section": "geometry", "input_type": "number", "unit": "mp", "source": "svg_analysis_or_manual"},
    {"key": "letter_perimeter_m", "label": "Perimetru litere", "section": "geometry", "input_type": "number", "unit": "m", "source": "svg_analysis_or_manual"},
    {"key": "face_finish_type", "label": "Finisaj față", "section": "finish", "input_type": "select", "variant_key": "face_finish_type", "source": "product_system_dossier"},
    {"key": "return_depth_mm", "label": "Adâncime cant", "section": "finish", "input_type": "select", "variant_key": "return_depth_mm", "unit": "mm", "source": "product_system_dossier"},
    {"key": "return_finish_type", "label": "Finisaj cant", "section": "finish", "input_type": "select", "variant_key": "return_finish_type", "source": "product_system_dossier"},
    {"key": "lighting_system_type", "label": "Sistem iluminare", "section": "lighting", "input_type": "select", "variant_key": "lighting_system_type", "source": "product_system_dossier"},
    {"key": "selected_psu_watts", "label": "Sursă LED", "section": "lighting", "input_type": "select", "variant_key": "selected_psu_watts", "unit": "W", "source": "product_system_dossier"},
    {"key": "back_bevel_enabled", "label": "Șanfren spate", "section": "structure", "input_type": "checkbox", "variant_key": "back_bevel_enabled", "source": "product_system_dossier"},
    {"key": "mounting_system", "label": "Sistem montaj", "section": "structure", "input_type": "select", "variant_key": "mounting_system", "source": "product_system_dossier"},
    {"key": "mounting_template_enabled", "label": "Șablon montaj", "section": "structure", "input_type": "checkbox", "variant_key": "mounting_template_enabled", "source": "product_system_dossier"},
    {"key": "mounting_template_material_type", "label": "Material șablon", "section": "structure", "input_type": "select", "variant_key": "mounting_template_material_type", "source": "product_system_dossier"},
    {"key": "mounting_template_area_m2", "label": "Suprafață șablon", "section": "structure", "input_type": "number", "unit": "mp", "source": "svg_document_area_or_manual"},
]

# ────────────────────────────────────────────────────────────────────────────
# Material price + workcenter rate loaders
# ────────────────────────────────────────────────────────────────────────────

async def _load_material_prices(db: AsyncSession) -> dict[str, dict[str, Any]]:
    """Load all active material prices as {code: {unit_cost, currency, name}}."""
    from models.inventory_materials import Inventory_materials

    rows = (await db.execute(
        select(Inventory_materials).where(Inventory_materials.status == "active")
    )).scalars().all()

    result: dict[str, dict[str, Any]] = {}
    for r in rows:
        result[r.code] = {
            "unit_cost": r.unit_cost or 0.0,
            "currency": r.currency or "EUR",
            "name": r.name or r.code,
        }
    return result


async def _load_workcenter_rates(db: AsyncSession) -> dict[str, dict[str, Any]]:
    """Load active workcenter rates with their unit basis."""
    from models.workcenter_rates import Workcenter_rates

    rows = (await db.execute(
        select(Workcenter_rates).where(Workcenter_rates.status == "active")
    )).scalars().all()

    result: dict[str, dict[str, Any]] = {}
    for r in rows:
        rate = r.rate_per_hour if r.rate_basis == "per_hour" else r.rate_per_linear_meter
        result[r.code] = {
            "rate": rate or 0.0,
            "basis": r.rate_basis,
            "currency": r.currency or "EUR",
            "label": r.label or r.code,
        }
    return result


# ────────────────────────────────────────────────────────────────────────────
# Pure BOM calculation
# ────────────────────────────────────────────────────────────────────────────

def calculate_bom(
    inputs: IntakeV5Inputs,
    material_prices: dict[str, dict[str, Any]],
    workcenter_rates: dict[str, dict[str, Any]],
) -> BomResult:
    """Pure function — compute materials, operations, tasks from inputs + prices."""

    materials: list[BomMaterialRow] = []
    operations: list[BomOperationRow] = []
    tasks: list[BomTaskRow] = []
    notes: list[str] = []

    face_area = inputs.letter_face_area_m2
    perimeter = inputs.letter_perimeter_m
    letter_count = inputs.letter_count
    document_area = (
        (inputs.width_mm * inputs.height_mm) / 1_000_000
        if inputs.width_mm and inputs.height_mm
        else None
    )

    def _price(code: str) -> tuple[float, str]:
        info = material_prices.get(code, {})
        return info.get("unit_cost", 0.0), info.get("name", code)

    def _rate(wc_code: str, expected_basis: str) -> float:
        info = workcenter_rates.get(wc_code)
        if not info:
            notes.append(f"⚠ Rată lipsă pentru {wc_code}")
            return 0.0
        if info.get("basis") != expected_basis:
            notes.append(
                f"⚠ Basis rată nealiniat pentru {wc_code}: "
                f"{info.get('basis')} în DB, așteptat {expected_basis}"
            )
        return info.get("rate", 0.0)

    def _add_mat(code: str, name: str, qty: float, unit: str, note: str = ""):
        cost, db_name = _price(code)
        if cost == 0:
            notes.append(f"⚠ Preț lipsă pentru {code}")
        materials.append(BomMaterialRow(
            code=code, name=db_name or name, qty=round(qty, 4),
            unit=unit, unit_cost=cost, total=round(qty * cost, 2), notes=note,
        ))

    def _add_op(
        code: str,
        name: str,
        wc: str,
        qty: float,
        unit: str,
        expected_basis: str,
        note: str = "",
    ):
        rate = _rate(wc, expected_basis)
        if rate == 0:
            notes.append(f"⚠ Rată lipsă pentru {wc}")
        operations.append(BomOperationRow(
            code=code, name=name, qty=round(qty, 4),
            unit=unit, rate=rate, total=round(qty * rate, 2), notes=note,
        ))

    # ── MATERIALS ──

    # 1. Față plexiglas 3mm
    face_qty = face_area * 1.15  # 15% waste
    _add_mat("MAT-ACP-FATA-LITERE", "plexiglas 3mm PMMA - opal", face_qty, "mp")

    # 2. Spate Forex 10mm
    if inputs.backing_enabled:
        back_qty = face_area * 1.10  # 10% waste
        _add_mat("MAT-SPATE-PVC-LITERE", "Forex 10 mm — spate litere", back_qty, "mp")

    # 3. Profil lateral (variant pe adâncime)
    profile_code = f"MAT-PROFIL-LATERAL-LITERE-{inputs.return_depth_mm}MM"
    profile_qty = perimeter * 1.10  # 10% extra
    _add_mat(profile_code, f"Profil aluminiu cant {inputs.return_depth_mm} mm", profile_qty, "ml")

    # 4. Vinyl/folie față
    if inputs.face_finish_type != "none":
        vinyl_qty = face_area * 1.15  # 15% waste
        vinyl_map = {
            "oracal_641": ("MAT-ORACAL-641", "Oracal 641 Economy Cal"),
            "oracal_651": ("MAT-ORACAL-651", "Oracal 651 Intermediate Cal"),
            "oracal_8500": ("MAT-ORACAL-8500", "Oracal 8500 Translucent Cal"),
            "printed_vinyl": ("MAT-VINYL-PRINT", "Autocolant print"),
            "printed_laminated_vinyl": ("MAT-VINYL-PRINT-LAMINATED", "Autocolant print + laminare"),
        }
        vcode, vname = vinyl_map[inputs.face_finish_type]
        _add_mat(vcode, vname, vinyl_qty, "mp")

    # 5. LED
    if inputs.illuminated:
        if inputs.lighting_system_type == "led_modules":
            led_count = math.ceil(perimeter * 1000 / 100)  # pitch 100mm
            _add_mat("MAT-LED-MODULE", "Module LED 12V", led_count, "buc")
            total_watts = led_count * 1.5
        else:
            strip_length = perimeter
            _add_mat("MAT-LED-STRIP", "Bandă LED 12V", strip_length, "ml")
            total_watts = strip_length * 14.4

        psu_count = max(1, math.ceil(total_watts / inputs.selected_psu_watts))
        psu_code = f"MAT-LED-PSU-12V-{inputs.selected_psu_watts}W"
        _add_mat(psu_code, f"Sursă LED 12V {inputs.selected_psu_watts}W", psu_count, "buc")

    # 6. Vopsea RAL
    if inputs.return_finish_type == "ral_paint" and inputs.paint_tube_count > 0:
        _add_mat("MAT-VOPSEA-RAL", "Vopsea RAL spray — tub", inputs.paint_tube_count, "buc")

    # 7. Bare premontaj
    if inputs.mounting_system == "steel_bars":
        bar_length = inputs.mounting_bar_length_m or (
            (inputs.width_mm / 1000) if inputs.width_mm else 1.0
        )
        bar_length *= inputs.mounting_bar_count
        _add_mat("MAT-PREMOUNT-BAR-STEEL", "Bară premontaj oțel 30×30×1.5", bar_length, "ml")
    elif inputs.mounting_system == "aluminum_bars":
        bar_length = inputs.mounting_bar_length_m or (
            (inputs.width_mm / 1000) if inputs.width_mm else 1.0
        )
        bar_length *= inputs.mounting_bar_count
        _add_mat("MAT-PREMOUNT-BAR-ALUMINUM", "Bară premontaj aluminiu 30×30×1.5", bar_length, "ml")
    elif inputs.mounting_system == "acm_panel":
        notes.append("Panoul ACM se calculează ca template separat; nu se inventează preț în litere v2.")

    # 8. Șablon montaj
    if inputs.mounting_template_enabled:
        template_area = inputs.mounting_template_area_m2 or document_area or face_area
        template_code = (
            "MAT-SABLON-HARTIE"
            if inputs.mounting_template_material_type == "paper"
            else "MAT-SABLON-MONTAJ"
        )
        template_name = (
            "Șablon montaj hârtie"
            if inputs.mounting_template_material_type == "paper"
            else "Șablon montaj Forex 3 mm"
        )
        _add_mat(template_code, template_name, template_area * 1.05, "mp")

    # 9. Consumabile montaj
    _add_mat("MAT-CONSUMABILE-MONTAJ", "Consumabile montaj (set)", 1, "set")

    # ── OPERATIONS ──

    # 1. Prepress
    _add_op("vector_prep", "Pregătire vector / prepress", "PREPRESS",
            letter_count, "buc", "per_piece")

    # 2. CNC față (2 passes: 1 cut + 1 bevel)
    cnc_face_qty = perimeter * 2
    _add_op("face_cnc_cut", "Tăiere CNC față plexiglas", "CNC_ROUTER",
            cnc_face_qty, "ml", "per_linear_meter", "2 treceri (tăiere + șanfren)")

    # 3. CNC spate
    if inputs.backing_enabled:
        back_passes = 3 + (2 if inputs.back_bevel_enabled else 0)
        cnc_back_qty = perimeter * back_passes
        _add_op("back_cut", "Tăiere CNC spate Forex", "CNC_ROUTER",
            cnc_back_qty, "ml", "per_linear_meter", f"{back_passes} treceri")

    # 4. Modelare cant
    _add_op("side_forming", "Modelare cant profil", "RETURN_PROFILE_MACHINE_FORMING",
            perimeter, "ml", "per_linear_meter")

    # 5. Lipire cant
    _add_op("return_face_bonding", "Lipire cant pe față", "RETURN_PROFILE_FACE_BONDING",
            perimeter, "ml", "per_linear_meter")

    # 6. Vopsire
    if inputs.return_finish_type == "ral_paint":
        _add_op("painting", "Vopsire RAL", "PAINTING", perimeter, "ml", "per_linear_meter")

    # 7. Aplicare vinyl
    if inputs.face_finish_type != "none":
        _add_op("vinyl_application", "Aplicare folie față", "FACE_VINYL_APPLICATION_LABOR",
                face_area, "mp", "per_square_meter")

    # 8. Print service
    if inputs.face_finish_type in ("printed_vinyl", "printed_laminated_vinyl"):
        _add_op("print_service", "Serviciu print", "LARGE_FORMAT_PRINT",
                face_area, "mp", "per_square_meter")

    # 9. Laminare
    if inputs.face_finish_type == "printed_laminated_vinyl":
        _add_op("lamination", "Laminare print", "LAMINATION", face_area, "mp", "per_square_meter")

    # 10-11. LED assembly + electrical
    if inputs.illuminated:
        if inputs.lighting_system_type == "led_modules":
            led_qty = math.ceil(perimeter * 1000 / 100)
        else:
            led_qty = math.ceil(perimeter)  # LED strip pieces
        _add_op("led_install", "Montaj LED", "LED_ASSEMBLY", led_qty, "buc", "per_piece")
        _add_op("electrical", "Cablaj electric", "ELECTRICAL_WIRING", letter_count, "buc", "per_piece")

    # 12. Șablon montaj
    if inputs.mounting_template_enabled and inputs.mounting_template_material_type == "forex":
        _add_op("mounting_template_cnc_cut", "Debitare șablon montaj", "CNC_ROUTER",
                perimeter, "ml", "per_linear_meter")

    # 13. Ambalare
    _add_op("packaging", "Ambalare + șablon", "PACKAGING", face_area, "mp", "per_square_meter")

    # ── TASKS (production sequence) ──

    seq = 0

    def _task(code: str, name: str, wc: str, minutes: float, deps: list[str] | None = None):
        nonlocal seq
        seq += 1
        tasks.append(BomTaskRow(
            sequence=seq, code=code, name=name, workcenter=wc,
            estimated_minutes=minutes, depends_on=deps or [],
        ))

    _task("vector_prep", "Pregătire vector / prepress", "PREPRESS",
          letter_count * 5.0)

    _task("face_cnc_cut", "Tăiere CNC față plexiglas", "CNC_ROUTER",
          perimeter * 3.0, ["vector_prep"])

    if inputs.backing_enabled:
        _task("back_cut", "Tăiere CNC spate Forex", "CNC_ROUTER",
              perimeter * 3.0, ["vector_prep"])

    _task("side_forming", "Modelare cant profil", "RETURN_PROFILE_MACHINE_FORMING",
          perimeter * 2.0, ["vector_prep"])

    _task("return_face_bonding", "Lipire cant pe față", "RETURN_PROFILE_FACE_BONDING",
          perimeter * 3.0, ["face_cnc_cut", "side_forming"])

    if inputs.return_finish_type == "ral_paint":
        _task("painting", "Vopsire RAL", "PAINTING",
              perimeter * 2.0, ["return_face_bonding"])

    if inputs.face_finish_type != "none":
        deps = ["painting"] if inputs.return_finish_type == "ral_paint" else ["return_face_bonding"]
        _task("vinyl_application", "Aplicare folie față", "FACE_VINYL_APPLICATION",
              face_area * 15.0, deps)

    if inputs.illuminated:
        back_dep = ["back_cut"] if inputs.backing_enabled else ["vector_prep"]
        _task("led_install", "Montaj LED", "LED_ASSEMBLY",
              (math.ceil(perimeter * 1000 / 100) if inputs.lighting_system_type == "led_modules"
               else perimeter) * 0.5,
              back_dep)
        _task("electrical", "Cablaj electric", "ELECTRICAL_WIRING",
              letter_count * 5.0, ["led_install"])

    if inputs.mounting_template_enabled:
        _task("mounting_template", "Pregătire șablon montaj", "CNC_ROUTER",
              perimeter * 1.5, ["vector_prep"])

    assembly_deps = [t.code for t in tasks if t.code in (
        "return_face_bonding", "vinyl_application", "electrical", "painting", "mounting_template",
    )]
    _task("assembly_qc", "Asamblare + QC", "ASSEMBLY",
          30.0 + letter_count * 2.0, assembly_deps or ["return_face_bonding"])

    _task("packaging", "Ambalare", "PACKAGING",
          face_area * 10.0, ["assembly_qc"])

    # ── TOTALS ──

    mat_total = round(sum(m.total for m in materials), 2)
    op_total = round(sum(o.total for o in operations), 2)

    return BomResult(
        materials=materials,
        operations=operations,
        tasks=tasks,
        material_total_eur=mat_total,
        operation_total_eur=op_total,
        grand_total_eur=round(mat_total + op_total, 2),
        notes=notes,
    )


# ────────────────────────────────────────────────────────────────────────────
# Project CRUD
# ────────────────────────────────────────────────────────────────────────────

async def _next_code(db: AsyncSession) -> str:
    """Generate next IV5-NNN code."""
    result = await db.execute(
        select(func.count(IntakeV5Project.id))
    )
    count = result.scalar() or 0
    return f"IV5-{count + 1:03d}"


async def create_project(
    db: AsyncSession,
    client_name: str,
    job_title: str,
    inputs: IntakeV5Inputs,
) -> IntakeV5Project:
    prices = await _load_material_prices(db)
    rates = await _load_workcenter_rates(db)
    bom = calculate_bom(inputs, prices, rates)

    code = await _next_code(db)
    project = IntakeV5Project(
        code=code,
        template_code=TEMPLATE_CODE,
        status="draft",
        client_name=client_name,
        job_title=job_title or "",
        inputs_json=inputs.model_dump_json(),
        bom_json=bom.model_dump_json(),
        material_total_eur=bom.material_total_eur,
        operation_total_eur=bom.operation_total_eur,
        grand_total_eur=bom.grand_total_eur,
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


async def get_project(db: AsyncSession, project_id: int) -> IntakeV5Project:
    row = (await db.execute(
        select(IntakeV5Project).where(IntakeV5Project.id == project_id)
    )).scalar_one_or_none()
    if not row:
        raise HTTPException(404, detail="Proiect V5 nu există")
    return row


async def list_projects(db: AsyncSession) -> list[IntakeV5Project]:
    result = await db.execute(
        select(IntakeV5Project).order_by(IntakeV5Project.id.desc())
    )
    return list(result.scalars().all())


async def update_project(
    db: AsyncSession,
    project_id: int,
    client_name: str | None,
    job_title: str | None,
    inputs: IntakeV5Inputs | None,
) -> IntakeV5Project:
    project = await get_project(db, project_id)
    if project.status not in ("draft",):
        raise HTTPException(400, detail="Doar proiectele draft pot fi editate")

    if client_name is not None:
        project.client_name = client_name
    if job_title is not None:
        project.job_title = job_title
    if inputs is not None:
        prices = await _load_material_prices(db)
        rates = await _load_workcenter_rates(db)
        bom = calculate_bom(inputs, prices, rates)
        project.inputs_json = inputs.model_dump_json()
        project.bom_json = bom.model_dump_json()
        project.material_total_eur = bom.material_total_eur
        project.operation_total_eur = bom.operation_total_eur
        project.grand_total_eur = bom.grand_total_eur

    await db.commit()
    await db.refresh(project)
    return project


async def preview_bom(db: AsyncSession, inputs: IntakeV5Inputs) -> BomResult:
    """Calculate BOM without saving — live preview."""
    prices = await _load_material_prices(db)
    rates = await _load_workcenter_rates(db)
    return calculate_bom(inputs, prices, rates)


async def get_template_config(db: AsyncSession) -> dict[str, Any]:
    """Return the simplified V5 template contract plus pricing readiness."""
    from models.product_blueprint_dossier import ProductBlueprintDossier
    from services.canonical_template_contract_service import (
        get_canonical_template_contract_service,
    )

    dossier = (await db.execute(
        select(ProductBlueprintDossier).where(
            ProductBlueprintDossier.template_code == TEMPLATE_CODE
        )
    )).scalar_one_or_none()

    canonical = get_canonical_template_contract_service()
    variants = canonical.get_variants(TEMPLATE_CODE)
    required_inputs, optional_inputs = canonical.get_form_contract_keys(TEMPLATE_CODE)
    required_inputs_set = set(required_inputs)
    conditional_inputs: dict[str, Any] = {}
    variant_by_key = {
        item.get("variant_key"): item
        for item in variants
        if isinstance(item, dict) and item.get("variant_key")
    }
    form_fields = []
    for field in FORM_FIELD_DEFINITIONS:
        variant = variant_by_key.get(field.get("variant_key"))
        form_fields.append({
            **field,
            "required": field["key"] in required_inputs_set,
            "conditional_rule": conditional_inputs.get(field["key"]),
            "allowed_values": variant.get("allowed_values", []) if variant else [],
            "default_value": variant.get("default_value") if variant else None,
            "description": variant.get("description", "") if variant else "",
            "source": "canonical_template_contract",
        })

    prices = await _load_material_prices(db)
    rates = await _load_workcenter_rates(db)
    missing_materials = [
        code for code in REQUIRED_MATERIAL_CODES
        if code not in prices or not prices[code].get("unit_cost")
    ]
    missing_rates = [
        code for code in REQUIRED_WORKCENTER_CODES
        if code not in rates or not rates[code].get("rate")
    ]

    return {
        "template_code": TEMPLATE_CODE,
        "dossier_status": dossier.status if dossier else "missing",
        "dossier_version": dossier.dossier_version if dossier else None,
        "variants": variants,
        "costengine_mapping": {
            "inputs": {
                "required": sorted(required_inputs_set),
                "optional": optional_inputs,
                "conditional": conditional_inputs,
            }
        },
        "form_contract": {
            "authority": "canonical_template_contract",
            "generated_form_target": "intake-v5",
            "svg_source": "intake-v4/operator-ui",
            "fields": form_fields,
            "pricing_source": "inventory_materials + workcenter_rates",
        },
        "pricing_ready": not missing_materials and not missing_rates,
        "missing_materials": missing_materials,
        "missing_rates": missing_rates,
        "materials": [
            {"code": code, **prices[code]}
            for code in REQUIRED_MATERIAL_CODES
            if code in prices
        ],
        "workcenter_rates": [
            {"code": code, **rates[code]}
            for code in REQUIRED_WORKCENTER_CODES
            if code in rates
        ],
    }


# ────────────────────────────────────────────────────────────────────────────
# Flow actions: Quote → Order → Tasks
# ────────────────────────────────────────────────────────────────────────────

async def create_quote(db: AsyncSession, project_id: int) -> dict:
    """Create a Quote from the project's BOM."""
    project = await get_project(db, project_id)
    if project.quote_id:
        raise HTTPException(400, detail="Oferta deja creată")
    if project.status != "draft":
        raise HTTPException(400, detail="Proiectul trebuie să fie în stare draft")

    bom = BomResult.model_validate_json(project.bom_json)

    # Build line items for the quote
    line_items = []
    for m in bom.materials:
        line_items.append({
            "type": "material",
            "code": m.code,
            "description": m.name,
            "quantity": m.qty,
            "unit": m.unit,
            "unit_price": m.unit_cost,
            "total": m.total,
        })
    for o in bom.operations:
        line_items.append({
            "type": "operation",
            "code": o.code,
            "description": o.name,
            "quantity": o.qty,
            "unit": o.unit,
            "unit_price": o.rate,
            "total": o.total,
        })

    quote = Quotes(
        code=f"Q-{project.code}",
        intake_code=project.code,
        client_name=project.client_name,
        status="draft",
        version=1,
        line_items=json.dumps(line_items, ensure_ascii=False),
        subtotal=bom.grand_total_eur,
        total_before_vat=bom.grand_total_eur,
        vat=round(bom.grand_total_eur * 0.19, 2),
        grand_total=round(bom.grand_total_eur * 1.19, 2),
        notes=json.dumps({
            "source": "intake_v5",
            "project_id": project.id,
            "project_code": project.code,
            "template_code": TEMPLATE_CODE,
            "inputs": json.loads(project.inputs_json),
        }, ensure_ascii=False),
    )
    db.add(quote)
    await db.flush()

    project.quote_id = quote.id
    project.status = "quoted"
    await db.commit()
    await db.refresh(project)
    await db.refresh(quote)

    return {
        "quote_id": quote.id,
        "quote_code": quote.code,
        "grand_total": quote.grand_total,
        "status": quote.status,
        "line_items_count": len(line_items),
    }


async def create_order(db: AsyncSession, project_id: int) -> dict:
    """Convert quote to order."""
    project = await get_project(db, project_id)
    if project.order_id:
        raise HTTPException(400, detail="Comanda deja creată")
    if not project.quote_id:
        raise HTTPException(400, detail="Creați mai întâi oferta")

    quote = (await db.execute(
        select(Quotes).where(Quotes.id == project.quote_id)
    )).scalar_one_or_none()
    if not quote:
        raise HTTPException(404, detail="Oferta nu există")

    bom = BomResult.model_validate_json(project.bom_json)

    # Build production snapshot for task generation
    snapshot = {
        "source": "intake_v5",
        "project_id": project.id,
        "project_code": project.code,
        "template_code": TEMPLATE_CODE,
        "inputs": json.loads(project.inputs_json),
        "bom": json.loads(project.bom_json),
        "quote_id": quote.id,
        "quote_code": quote.code,
        "quote_grand_total": quote.grand_total,
    }

    order = Orders(
        code=f"ORD-{project.code}",
        quote_id=quote.id,
        quote_code=quote.code,
        client_name=project.client_name,
        status="confirmed",
        total_amount=quote.grand_total,
        payment_status="pending",
        snapshot_version=1,
        snapshot_line_items=json.dumps(snapshot, ensure_ascii=False),
        notes=json.dumps({
            "source": "intake_v5",
            "project_id": project.id,
        }, ensure_ascii=False),
    )
    db.add(order)
    await db.flush()

    quote.status = "accepted"
    project.order_id = order.id
    project.status = "ordered"
    await db.commit()
    await db.refresh(project)
    await db.refresh(order)

    return {
        "order_id": order.id,
        "order_code": order.code,
        "total_amount": order.total_amount,
        "status": order.status,
    }


async def generate_tasks(db: AsyncSession, project_id: int) -> dict:
    """Generate execution plan (tasks) from order."""
    project = await get_project(db, project_id)
    if not project.order_id:
        raise HTTPException(400, detail="Creați mai întâi comanda")

    # Check if execution plan already exists
    existing = (await db.execute(
        select(ExecutionPlan).where(ExecutionPlan.order_id == project.order_id)
    )).scalar_one_or_none()
    if existing:
        raise HTTPException(400, detail="Task-urile au fost deja generate")

    order = (await db.execute(
        select(Orders).where(Orders.id == project.order_id)
    )).scalar_one_or_none()
    if not order:
        raise HTTPException(404, detail="Comanda nu există")

    bom = BomResult.model_validate_json(project.bom_json)

    # Build execution tasks from BOM tasks
    exec_tasks = []
    for t in bom.tasks:
        exec_tasks.append({
            "task_code": f"{order.code}-T{t.sequence:02d}",
            "sequence": t.sequence,
            "code": t.code,
            "name": t.name,
            "workcenter": t.workcenter,
            "estimated_minutes": t.estimated_minutes,
            "depends_on": t.depends_on,
            "status": "pending",
            "assigned_to": None,
        })

    total_minutes = sum(t.estimated_minutes for t in bom.tasks)

    plan = ExecutionPlan(
        order_id=order.id,
        order_code=order.code,
        snapshot_version=1,
        tasks_json=json.dumps(exec_tasks, ensure_ascii=False),
        total_estimated_time_minutes=total_minutes,
    )
    db.add(plan)

    order.status = "in_production"
    project.status = "in_production"
    await db.commit()
    await db.refresh(plan)

    return {
        "execution_plan_id": plan.id,
        "order_code": order.code,
        "task_count": len(exec_tasks),
        "total_estimated_minutes": total_minutes,
        "tasks": exec_tasks,
    }
