"""Intake V4 → TPL-VOLUMETRIC-LETTERS template option contract (read-only adapter).

Maps operator-discovered V4 finish/geometry choices to template-owned options,
material intents, BLK-18 pricing codes, and production preview keys.
Does NOT mutate ProductSystem storage or create parallel template truth.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from typing import Any, Literal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.intake_v4_workspace import IntakeV4WorkspaceRecord
from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from schemas.intake_v4 import (
    PILOT_V4_TEMPLATE_CODE,
    IntakeV4FinishSetup,
    IntakeV4TemplateContractCanonicalRow,
    IntakeV4TemplateContractIssue,
    IntakeV4TemplateFormContractField,
    IntakeV4TemplateFormContractResponse,
    IntakeV4WorkspacePayload,
)
from services.intake_v4_ral_paint_rules_service import (
    RAL_PAINT_SPRAY_MATERIAL_CODE,
    estimate_intake_v4_ral_paint_spray,
)

TemplateOptionStatus = Literal["aligned", "partial", "missing", "provisional"]

# Dossier variant keys — source: seed_tpl_volumetric_letters_dossier._variants()
DOSSIER_VARIANT_KEYS = frozenset(
    {
        "back_bevel_enabled",
        "face_finish_type",
        "mounting_template_enabled",
        "mounting_system",
        "mounting_bar_profile",
        "return_depth_mm",
        "selected_psu_watts",
        "return_finish_type",
        "lighting_system_type",
        "light_color",
        "led_module_power_w",
        "mounting_template_material_type",
        "face_vinyl_roll_width_mm",
        "emblem_lighting_mode",
    }
)

# V4 UI face finish → template face_finish_type (dossier allowed_values)
V4_FACE_FINISH_TO_TEMPLATE: dict[str, tuple[str, TemplateOptionStatus]] = {
    "none": ("none", "aligned"),
    "oracal_651": ("oracal_651", "aligned"),
    "oracal_641": ("oracal_641", "aligned"),  # priced as 651; now a dossier allowed_value
    "oracal_8500": ("oracal_8500", "aligned"),
    "print_laminate": ("printed_laminated_vinyl", "aligned"),
}

V4_RETURN_FINISH_TO_TEMPLATE: dict[str, tuple[str, TemplateOptionStatus]] = {
    "oracal_wrapped": ("oracal_651", "partial"),  # return vinyl via operation flags, not dossier variant
    "ral_paint": ("paint_after_face_miter_bond", "partial"),  # volume_finish in quote_input
    "standard_aluminum": ("none", "partial"),
    "white_aluminum": ("none", "partial"),
    "black_aluminum": ("none", "partial"),
    "mirror_silver": ("none", "partial"),
    "gold_aluminum": ("none", "partial"),
    "same_as_face": ("oracal_651", "partial"),
    "none": ("none", "aligned"),
}

RETURN_DEPTH_ALLOWED = frozenset({30, 60, 80, 100})
PSU_WATTS_ALLOWED = frozenset({60, 100, 160, 200})

FALLBACK_DOSSIER_VARIANTS: list[dict[str, Any]] = [
    {
        "variant_key": "back_bevel_enabled",
        "name": "Sanfren spate Forex",
        "allowed_values": [False, True],
        "default_value": False,
        "description": "Forex back bevel option owned by the volumetric template.",
    },
    {
        "variant_key": "face_finish_type",
        "name": "Finisaj fata plexi",
        "allowed_values": ["none", "oracal_651", "oracal_641", "oracal_8500", "printed_vinyl", "printed_laminated_vinyl"],
        "default_value": "none",
        "description": "Canonical face finish variants from the dossier.",
    },
    {
        "variant_key": "mounting_template_enabled",
        "name": "Sablon montaj Forex",
        "allowed_values": [True, False],
        "default_value": True,
        "description": "Template-owned mounting template decision.",
    },
    {
        "variant_key": "mounting_system",
        "name": "Sistem montaj / premontaj",
        "allowed_values": ["direct_wall", "steel_bars", "aluminum_bars", "acm_panel"],
        "default_value": "direct_wall",
        "description": "Template-owned mounting system decision.",
    },
    {
        "variant_key": "mounting_bar_profile",
        "name": "Profil bare premontaj",
        "allowed_values": ["30x30x1.5"],
        "default_value": "30x30x1.5",
        "description": "Template-owned mounting bar profile.",
    },
    {
        "variant_key": "return_depth_mm",
        "name": "Adancime cant / profil lateral",
        "allowed_values": sorted(RETURN_DEPTH_ALLOWED),
        "default_value": 60,
        "description": "Variant-priced return profile depth.",
    },
    {
        "variant_key": "selected_psu_watts",
        "name": "Putere sursa LED",
        "allowed_values": sorted(PSU_WATTS_ALLOWED),
        "default_value": 100,
        "description": "Single template-owned PSU wattage variant for pricing.",
    },
    {
        "variant_key": "return_finish_type",
        "name": "Finisaj cant / volum",
        "allowed_values": ["white_aluminum", "black_aluminum", "gold_aluminum", "mirror_silver", "ral_paint", "oracal_wrapped"],
        "default_value": "white_aluminum",
        "description": "Cant/return finish material — maps to material intent at handoff.",
    },
    {
        "variant_key": "lighting_system_type",
        "name": "Sistem iluminare LED",
        "allowed_values": ["led_modules", "led_strip"],
        "default_value": "led_modules",
        "description": "LED system type — led_modules standard, led_strip alternative.",
    },
    {
        "variant_key": "light_color",
        "name": "Culoare lumina LED",
        "allowed_values": ["warm", "neutral", "cool"],
        "default_value": "warm",
        "description": "LED light color temperature.",
    },
    {
        "variant_key": "led_module_power_w",
        "name": "Putere modul LED",
        "allowed_values": [0.75, 1.0, 1.44],
        "default_value": 0.75,
        "description": "LED module wattage for power/PSU sizing.",
    },
    {
        "variant_key": "mounting_template_material_type",
        "name": "Material sablon montaj",
        "allowed_values": ["forex", "paper"],
        "default_value": "forex",
        "description": "Mounting template material — forex (CNC) or paper (print).",
    },
    {
        "variant_key": "face_vinyl_roll_width_mm",
        "name": "Latime rola vinyl fata",
        "allowed_values": [1000, 1260],
        "default_value": 1000,
        "description": "Vinyl roll width for face finish application.",
    },
    {
        "variant_key": "emblem_lighting_mode",
        "name": "Mod iluminare emblema",
        "allowed_values": ["area_lit", "excluded"],
        "default_value": "area_lit",
        "description": "Emblem lighting mode — area_lit or excluded.",
    },
]

DOSSIER_TO_V4_FIELD: dict[str, tuple[str | None, Literal["canonical", "mapped", "adapter_only", "missing_in_v4"], str]] = {
    "back_bevel_enabled": (
        "back_bevel_enabled",
        "canonical",
        "V4 captures the template boolean and keeps it aligned with backing_mode.",
    ),
    "face_finish_type": (
        "face_finish_type",
        "mapped",
        "V4 includes extra discovered values that must map back to dossier allowed_values.",
    ),
    "mounting_template_enabled": (
        "mounting_template_enabled",
        "canonical",
        "Template-owned field captured by Intake V4.",
    ),
    "mounting_system": (
        "mounting_system",
        "canonical",
        "Template-owned field captured by Intake V4.",
    ),
    "mounting_bar_profile": (
        "mounting_bar_profile",
        "canonical",
        "Required when mounting_system uses premount bars.",
    ),
    "return_depth_mm": (
        "return_depth_mm",
        "canonical",
        "V4 field matches the dossier variant.",
    ),
    "selected_psu_watts": (
        "selected_psu_watts",
        "canonical",
        "V4 captures the single template-owned PSU wattage while retaining psu_configuration for load planning.",
    ),
    "return_finish_type": (
        "return_finish_type",
        "canonical",
        "Cant/return finish material now dossier-owned.",
    ),
    "lighting_system_type": (
        "lighting_system_type",
        "canonical",
        "LED system type now dossier-owned.",
    ),
    "light_color": (
        "light_color",
        "canonical",
        "LED light color temperature now dossier-owned.",
    ),
    "led_module_power_w": (
        "led_module_power_w",
        "canonical",
        "LED module wattage now dossier-owned.",
    ),
    "mounting_template_material_type": (
        "mounting_template_material_type",
        "canonical",
        "Mounting template material now dossier-owned.",
    ),
    "face_vinyl_roll_width_mm": (
        "face_vinyl_roll_width_mm",
        "canonical",
        "Vinyl roll width now dossier-owned.",
    ),
    "emblem_lighting_mode": (
        "emblem_lighting_mode",
        "canonical",
        "Emblem lighting mode now dossier-owned.",
    ),
}

# All former adapter-only fields (return_finish_type, lighting_system_type) are now
# dossier-owned variants. No adapter-only fields remain.
V4_ADAPTER_ONLY_FORM_FIELDS: list[IntakeV4TemplateFormContractField] = []

# Material breakdown key → registry (BLK-18) — mirrors intake_v4_material_breakdown_service
MATERIAL_INTENT_REGISTRY: dict[str, str] = {
    "plexiglas_face": "MAT-ACP-FATA-LITERE",
    "forex_backing": "MAT-SPATE-PVC-LITERE",
    "face_vinyl": "MAT-ORACAL-651",
    "face_vinyl_651": "MAT-ORACAL-651",
    "face_vinyl_8500": "MAT-ORACAL-8500",
    "edge_cant_oracal_651": "MAT-ORACAL-651",
    "print_vinyl": "MAT-VINYL-PRINT",
    "laminated_vinyl": "MAT-VINYL-PRINT-LAMINATED",
    "return_material": "MAT-PROFIL-LATERAL-LITERE",
    "ral_paint_spray": RAL_PAINT_SPRAY_MATERIAL_CODE,
    "led_modules": "MAT-LED-MODULE",
    "led_psu": "MAT-LED-PSU-12V",
}

# Production handoff material job keys (preview layer — local mapping table)
MATERIAL_JOB_KEYS: dict[str, str] = {
    "plexiglas_face": "face_plexiglas_cutting",
    "forex_backing": "forex_backing_cutting",
    "face_vinyl": "oracal_vinyl_cutting",
    "print_vinyl": "print_vinyl_artwork",
    "laminated_vinyl": "laminate_vinyl_artwork",
    "return_material": "return_profile_material",
    "led_modules": "led_modules_install",
    "led_psu": "psu_electrical",
}

# Dossier priced operations → preview operation group (provisional local names in preview service)
DOSSIER_OPERATION_TO_PREVIEW_GROUP: dict[str, str] = {
    "vector_prep": "preflight_qc",
    "face_cnc_cut": "cnc_cutting",
    "back_cut": "cnc_cutting",
    "side_forming": "return_forming",
    "return_face_bonding": "return_bonding",
    "vinyl_application": "vinyl_print_finish",
    "painting": "return_forming",
    "led_install_letters": "led_electrical",
    "electrical_letters": "led_electrical",
    "packaging_letters": "preflight_qc",
    "mounting_template_cnc_cut": "cnc_cutting",
    "qc_letters": "preflight_qc",
}


@dataclass(frozen=True)
class CanonicalOptionRow:
    """One row of the mandatory canonical matrix."""

    discovered_option: str
    blueprint_rule: str
    template_option: str
    material_intent: str
    pricing_code_blk18: str
    costengine_field: str
    production_material_job: str
    production_operation_group: str
    future_task_seed: str
    status: TemplateOptionStatus
    notes: str = ""


@dataclass
class TemplateOptionContractIssue:
    code: str
    severity: Literal["blocking", "warning", "info"]
    message: str
    source: str
    option_key: str | None = None


@dataclass
class TemplateOptionContractResult:
    template_code: str
    canonical_rows: list[CanonicalOptionRow] = field(default_factory=list)
    warnings: list[TemplateOptionContractIssue] = field(default_factory=list)
    blockers: list[TemplateOptionContractIssue] = field(default_factory=list)
    discovered_v4_values: dict[str, Any] = field(default_factory=dict)


def get_canonical_mapping_catalog() -> list[CanonicalOptionRow]:
    """Static canonical matrix for TPL-VOLUMETRIC-LETTERS (audit + tests)."""
    depth_rows = [
        (30, "MAT-PROFIL-LATERAL-LITERE-30MM"),
        (60, "MAT-PROFIL-LATERAL-LITERE-60MM"),
        (80, "MAT-PROFIL-LATERAL-LITERE-80MM"),
        (100, "MAT-PROFIL-LATERAL-LITERE-100MM"),
    ]
    psu_rows = [
        (60, "MAT-LED-PSU-12V-60W"),
        (100, "MAT-LED-PSU-12V-100W"),
        (160, "MAT-LED-PSU-12V-160W"),
        (200, "MAT-LED-PSU-12V-200W"),
    ]
    rows: list[CanonicalOptionRow] = [
        CanonicalOptionRow(
            discovered_option="Plexiglas față 3 mm",
            blueprint_rule="comp_face_litere / MAT-ACP-FATA-LITERE",
            template_option="implicit (no thickness variant in dossier)",
            material_intent="plexiglas_face",
            pricing_code_blk18="MAT-ACP-FATA-LITERE",
            costengine_field="letter_face_area_m2",
            production_material_job="face_plexiglas_cutting",
            production_operation_group="cnc_cutting",
            future_task_seed="cnc_face_cut",
            status="aligned",
        ),
        CanonicalOptionRow(
            discovered_option="Plexiglas față grosimi viitoare 4/5/6/8/10 mm",
            blueprint_rule="not in BUILD4 template",
            template_option="missing",
            material_intent="missing",
            pricing_code_blk18="missing",
            costengine_field="—",
            production_material_job="—",
            production_operation_group="—",
            future_task_seed="—",
            status="missing",
            notes="discovered_but_not_template_owned — do not treat as final",
        ),
        CanonicalOptionRow(
            discovered_option="Forex backing 10 mm",
            blueprint_rule="comp_spate_litere / MAT-SPATE-PVC-LITERE",
            template_option="implicit backing",
            material_intent="forex_backing",
            pricing_code_blk18="MAT-SPATE-PVC-LITERE",
            costengine_field="letter_face_area_m2 (backing area)",
            production_material_job="forex_backing_cutting",
            production_operation_group="cnc_cutting",
            future_task_seed="cnc_back_cut",
            status="aligned",
        ),
        CanonicalOptionRow(
            discovered_option="Oracal 651 față",
            blueprint_rule="face_finish_type=oracal_651",
            template_option="face_finish_type: oracal_651",
            material_intent="face_vinyl",
            pricing_code_blk18="MAT-ORACAL-651",
            costengine_field="face_finish_type",
            production_material_job="oracal_vinyl_cutting",
            production_operation_group="vinyl_print_finish",
            future_task_seed="vinyl_application",
            status="aligned",
        ),
        CanonicalOptionRow(
            discovered_option="Oracal 8500 fata iluminata/translucenta",
            blueprint_rule="face_finish_type=oracal_8500",
            template_option="face_finish_type: oracal_8500",
            material_intent="face_vinyl_8500",
            pricing_code_blk18="MAT-ORACAL-8500",
            costengine_field="face_finish_type",
            production_material_job="oracal_vinyl_cutting",
            production_operation_group="vinyl_print_finish",
            future_task_seed="vinyl_application",
            status="aligned",
            notes="Owner price is separate from Oracal 651 in Intake V4 material breakdown.",
        ),
        CanonicalOptionRow(
            discovered_option="Print fata",
            blueprint_rule="face_finish_type=printed_vinyl",
            template_option="face_finish_type: printed_vinyl",
            material_intent="print_vinyl",
            pricing_code_blk18="MAT-VINYL-PRINT",
            costengine_field="face_finish_type",
            production_material_job="print_vinyl_artwork",
            production_operation_group="vinyl_print_finish",
            future_task_seed="vinyl_application",
            status="aligned",
        ),
        CanonicalOptionRow(
            discovered_option="Laminare print",
            blueprint_rule="face_finish_type=printed_laminated_vinyl",
            template_option="face_finish_type: printed_laminated_vinyl",
            material_intent="laminated_vinyl",
            pricing_code_blk18="MAT-VINYL-PRINT-LAMINATED",
            costengine_field="face_finish_type",
            production_material_job="laminate_vinyl_artwork",
            production_operation_group="vinyl_print_finish",
            future_task_seed="vinyl_application",
            status="aligned",
        ),
        CanonicalOptionRow(
            discovered_option="Policromie / artwork",
            blueprint_rule="artwork execution_type separate_emblem | print paths",
            template_option="partial (artwork not in dossier variants)",
            material_intent="artwork_* rows",
            pricing_code_blk18="MAT-ACP-FATA-LITERE + profile",
            costengine_field="geometry + finish flags",
            production_material_job="artwork_*",
            production_operation_group="vinyl_print_finish / cnc_cutting",
            future_task_seed="vector_prep",
            status="partial",
        ),
    ]
    for depth, reg_code in depth_rows:
        rows.append(
            CanonicalOptionRow(
                discovered_option=f"Cant/lateral {depth} mm",
                blueprint_rule=f"return_depth_mm={depth}",
                template_option=f"return_depth_mm: {depth}",
                material_intent="return_material",
                pricing_code_blk18=reg_code,
                costengine_field="return_depth_mm",
                production_material_job="return_profile_material",
                production_operation_group="return_forming / return_bonding",
                future_task_seed="return_profile_forming",
                status="aligned",
            )
        )
    rows.append(
        CanonicalOptionRow(
            discovered_option="LED module",
            blueprint_rule="illumination + led_module_count formula",
            template_option="derived (not dossier variant)",
            material_intent="led_modules",
            pricing_code_blk18="MAT-LED-MODULE",
            costengine_field="led_module_count",
            production_material_job="led_modules_install",
            production_operation_group="led_electrical",
            future_task_seed="led_installation",
            status="aligned",
        )
    )
    rows.append(
        CanonicalOptionRow(
            discovered_option="LED pitch",
            blueprint_rule="100 mm module pitch (dossier derived)",
            template_option="derived_primitives.led_module_count",
            material_intent="led_modules qty",
            pricing_code_blk18="MAT-LED-MODULE",
            costengine_field="led_module_count",
            production_material_job="led_modules_install",
            production_operation_group="led_electrical",
            future_task_seed="led_installation",
            status="partial",
            notes="V4 uses 250 mm pitch in breakdown — differs from dossier 100 mm CostEngine formula",
        )
    )
    for watts, reg_code in psu_rows:
        rows.append(
            CanonicalOptionRow(
                discovered_option=f"PSU {watts}W",
                blueprint_rule=f"selected_psu_watts={watts}",
                template_option=f"selected_psu_watts: {watts}",
                material_intent="led_psu",
                pricing_code_blk18=reg_code,
                costengine_field="selected_psu_watts",
                production_material_job="psu_electrical",
                production_operation_group="led_electrical",
                future_task_seed="electrical_wiring",
                status="aligned",
            )
        )
    op_rows = [
        ("Prepress", "vector_prep", "preflight_qc", "vector_prep"),
        ("CNC face", "face_cnc_cut", "cnc_cutting", "cnc_face_cut"),
        ("CNC backing", "back_cut", "cnc_cutting", "cnc_back_cut"),
        ("Vinyl cutting", "vinyl_application", "vinyl_print_finish", "vinyl_application"),
        ("Print/lamination operation", "vinyl_application", "vinyl_print_finish", "vinyl_application"),
        ("Return forming", "side_forming", "return_forming", "return_profile_forming"),
        ("Return bonding", "return_face_bonding", "return_bonding", "return_face_bonding"),
        ("LED assembly", "led_install_letters", "led_electrical", "led_installation"),
        ("Electrical wiring", "electrical_letters", "led_electrical", "electrical_wiring"),
        ("Assembly", "assembly_letters", "assembly", "letter_assembly_no_shared_support"),
        ("Packaging / installation prep", "packaging_letters", "preflight_qc", "stretch_wrap_and_delivery_mounting_package"),
    ]
    for label, op_code, group, seed in op_rows:
        st: TemplateOptionStatus = "partial" if op_code == "assembly_letters" else "aligned"
        if op_code == "assembly_letters":
            notes = "assembly_letters internal calibration — preview uses catalog doc codes"
        else:
            notes = ""
        rows.append(
            CanonicalOptionRow(
                discovered_option=label,
                blueprint_rule=f"operation_keys: {op_code}",
                template_option=op_code,
                material_intent="—",
                pricing_code_blk18="workcenter_rates",
                costengine_field="operation formula gates",
                production_material_job="—",
                production_operation_group=group,
                future_task_seed=seed,
                status=st,
                notes=notes,
            )
        )
    rows.extend(
        [
            CanonicalOptionRow(
                discovered_option="Montaj direct pe perete",
                blueprint_rule="mounting_system=direct_wall",
                template_option="mounting_system: direct_wall",
                material_intent="—",
                pricing_code_blk18="—",
                costengine_field="mounting_system",
                production_material_job="—",
                production_operation_group="—",
                future_task_seed="premount_bars (inactive)",
                status="missing",
                notes="V4 form does not capture — QuoteWizard default only",
            ),
            CanonicalOptionRow(
                discovered_option="Montaj pe structură (bare oțel/aluminiu)",
                blueprint_rule="mounting_system=steel_bars|aluminum_bars",
                template_option="mounting_system variants",
                material_intent="MAT-PREMOUNT-BAR-*",
                pricing_code_blk18="MAT-PREMOUNT-BAR-STEEL / ALUMINUM",
                costengine_field="mounting_bar_*",
                production_material_job="—",
                production_operation_group="assembly",
                future_task_seed="premount_bars",
                status="missing",
                notes="Not in Intake V4 UI — template-owned but form gap",
            ),
        ]
    )
    rows = [
        replace(
            row,
            notes="Captured in Intake V4 template options; direct mount has no material job.",
        )
        if row.costengine_field == "mounting_system"
        else replace(
            row,
            notes=(
                "Captured in Intake V4 template options; premount material/task alignment "
                "remains provisional."
            ),
        )
        if row.costengine_field == "mounting_bar_*"
        else row
        for row in rows
    ]
    return rows


def _issue(
    code: str,
    *,
    severity: Literal["blocking", "warning", "info"] = "warning",
    message: str,
    source: str,
    option_key: str | None = None,
) -> TemplateOptionContractIssue:
    return TemplateOptionContractIssue(
        code=code,
        severity=severity,
        message=message,
        source=source,
        option_key=option_key,
    )


def _collect_face_finish_values(setup: IntakeV4FinishSetup) -> set[str]:
    values: set[str] = set()
    if setup.face_finish_type:
        values.add(setup.face_finish_type.strip().lower())
    for group in setup.letter_group_finishes:
        if group.face_finish_type:
            values.add(group.face_finish_type.strip().lower())
    return values


def _collect_return_finish_values(setup: IntakeV4FinishSetup) -> set[str]:
    values: set[str] = set()
    if setup.return_finish_type:
        values.add(setup.return_finish_type.strip().lower())
    for group in setup.letter_group_finishes:
        if group.return_finish_type:
            values.add(group.return_finish_type.strip().lower())
    for art in setup.artwork_finishes:
        if art.return_finish_type:
            values.add(art.return_finish_type.strip().lower())
    return values


def _collect_return_depths(setup: IntakeV4FinishSetup) -> set[int]:
    depths: set[int] = set()
    if setup.return_depth_mm is not None:
        depths.add(int(setup.return_depth_mm))
    for group in setup.letter_group_finishes:
        if group.return_depth_mm is not None:
            depths.add(int(group.return_depth_mm))
    for art in setup.artwork_finishes:
        if art.return_depth_mm is not None:
            depths.add(int(art.return_depth_mm))
    return depths


def _ral_paint_tube_estimate_available(payload: IntakeV4WorkspacePayload) -> bool:
    setup = payload.finish_setup
    if setup is None:
        return False
    geometry: dict[str, Any] = {}
    if isinstance(payload.path_geometry_summary, dict):
        geometry.update(payload.path_geometry_summary)
    if isinstance(payload.quote_geometry, dict):
        geometry.update(payload.quote_geometry)
    estimate = estimate_intake_v4_ral_paint_spray(
        finish_setup=setup.model_dump(mode="json"),
        geometry=geometry,
        analysis=payload.svg_analysis_json if isinstance(payload.svg_analysis_json, dict) else {},
        default_return_finish=setup.return_finish_type,
    )
    return estimate is not None and estimate.charged_tubes > 0


def _json_loads(raw: str | None, default: Any) -> Any:
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return default


def _canonical_row_response(row: CanonicalOptionRow) -> IntakeV4TemplateContractCanonicalRow:
    return IntakeV4TemplateContractCanonicalRow(
        discovered_option=row.discovered_option,
        blueprint_rule=row.blueprint_rule,
        template_option=row.template_option,
        material_intent=row.material_intent,
        pricing_code_blk18=row.pricing_code_blk18,
        costengine_field=row.costengine_field,
        production_material_job=row.production_material_job,
        production_operation_group=row.production_operation_group,
        future_task_seed=row.future_task_seed,
        status=row.status,
        notes=row.notes,
    )


def _issue_response(issue: TemplateOptionContractIssue) -> IntakeV4TemplateContractIssue:
    return IntakeV4TemplateContractIssue(
        code=issue.code,
        severity=issue.severity,
        message=issue.message,
        source=issue.source,
        option_key=issue.option_key,
    )


def _variant_fields_from_dossier(
    variants: list[dict[str, Any]],
    *,
    source: str,
) -> list[IntakeV4TemplateFormContractField]:
    fields: list[IntakeV4TemplateFormContractField] = []
    seen: set[str] = set()
    for variant in variants:
        key = str(variant.get("variant_key") or "").strip()
        if not key:
            continue
        seen.add(key)
        v4_field_key, status, note = DOSSIER_TO_V4_FIELD.get(
            key,
            (None, "missing_in_v4", "Dossier variant has no explicit Intake V4 field mapping yet."),
        )
        current_owner: Literal[
            "product_system_dossier", "intake_v4_hardcoded_form", "quote_wizard_default"
        ] = "intake_v4_hardcoded_form"
        if status == "missing_in_v4":
            current_owner = "quote_wizard_default"
        fields.append(
            IntakeV4TemplateFormContractField(
                field_key=key,
                label=str(variant.get("name") or key),
                owner="product_system_dossier",
                current_runtime_owner=current_owner,
                alignment_status=status,
                allowed_values=list(variant.get("allowed_values") or []),
                default_value=variant.get("default_value"),
                v4_field_key=v4_field_key,
                source=source,
                notes=[note, str(variant.get("description") or "").strip()],
            )
        )
    for fallback in FALLBACK_DOSSIER_VARIANTS:
        key = str(fallback.get("variant_key") or "")
        if key in seen:
            continue
        v4_field_key, status, note = DOSSIER_TO_V4_FIELD[key]
        current_owner = "intake_v4_hardcoded_form"
        if status == "missing_in_v4":
            current_owner = "quote_wizard_default"
        fields.append(
            IntakeV4TemplateFormContractField(
                field_key=key,
                label=str(fallback.get("name") or key),
                owner="product_system_dossier",
                current_runtime_owner=current_owner,
                alignment_status=status,
                allowed_values=list(fallback.get("allowed_values") or []),
                default_value=fallback.get("default_value"),
                v4_field_key=v4_field_key,
                source="static_contract_fallback",
                notes=[note, str(fallback.get("description") or "").strip()],
            )
        )
    fields.extend(V4_ADAPTER_ONLY_FORM_FIELDS)
    return fields


async def get_template_form_contract_for_workspace(
    db: AsyncSession,
    workspace_id: str,
) -> IntakeV4TemplateFormContractResponse:
    record_result = await db.execute(
        select(IntakeV4WorkspaceRecord).where(IntakeV4WorkspaceRecord.id == workspace_id)
    )
    record = record_result.scalar_one_or_none()
    if record is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "workspace_not_found", "workspace_id": workspace_id},
        )

    payload_raw = _json_loads(record.payload_json, {})
    payload = IntakeV4WorkspacePayload.model_validate(payload_raw)
    template_code = record.template_code or payload.product_binding.template_code

    template_result = await db.execute(
        select(Product_templates).where(Product_templates.template_code == template_code)
    )
    template = template_result.scalar_one_or_none()

    dossier_result = await db.execute(
        select(ProductBlueprintDossier).where(ProductBlueprintDossier.template_code == template_code)
    )
    dossier = dossier_result.scalar_one_or_none()
    variants = FALLBACK_DOSSIER_VARIANTS
    dossier_source: Literal["product_blueprint_dossier", "static_contract_fallback"] = (
        "static_contract_fallback"
    )
    dossier_status: str | None = None
    if dossier is not None:
        parsed_variants = _json_loads(dossier.variants_json, [])
        if isinstance(parsed_variants, list):
            variants = [v for v in parsed_variants if isinstance(v, dict)]
            dossier_source = "product_blueprint_dossier"
        dossier_status = dossier.status

    contract = evaluate_v4_template_option_contract(payload)
    alignment_status: Literal["aligned", "partial", "blocked"] = "partial"
    if contract.blockers:
        alignment_status = "blocked"
    elif not contract.warnings:
        alignment_status = "aligned"

    return IntakeV4TemplateFormContractResponse(
        workspace_id=workspace_id,
        template_code=template_code,
        alignment_status=alignment_status,
        template_active=bool(template.active) if template is not None else False,
        dossier_status=dossier_status,
        dossier_source=dossier_source,
        variant_fields=_variant_fields_from_dossier(variants, source=dossier_source),
        canonical_rows=[_canonical_row_response(row) for row in contract.canonical_rows],
        warnings=[_issue_response(issue) for issue in contract.warnings],
        blockers=[_issue_response(issue) for issue in contract.blockers],
        discovered_v4_values=contract.discovered_v4_values,
    )


def evaluate_v4_template_option_contract(
    payload: IntakeV4WorkspacePayload,
) -> TemplateOptionContractResult:
    """Evaluate persisted V4 payload against TPL-VOLUMETRIC-LETTERS contract."""
    result = TemplateOptionContractResult(
        template_code=payload.product_binding.template_code,
        canonical_rows=get_canonical_mapping_catalog(),
    )

    if payload.product_binding.template_code != PILOT_V4_TEMPLATE_CODE:
        result.blockers.append(
            _issue(
                "unsupported_template",
                severity="blocking",
                message="Workspace template is outside V4 pilot contract scope.",
                source="product_binding.template_code",
            )
        )
        return result

    setup = payload.finish_setup
    if setup is None:
        result.warnings.append(
            _issue(
                "form_option_not_template_backed",
                message="Finish setup missing — cannot validate template option mapping.",
                source="finish_setup",
            )
        )
        return result

    result.discovered_v4_values = {
        "face_finish_types": sorted(_collect_face_finish_values(setup)),
        "return_finish_types": sorted(_collect_return_finish_values(setup)),
        "return_depths_mm": sorted(_collect_return_depths(setup)),
        "illuminated": setup.illuminated,
        "psu_configuration": list(setup.psu_configuration or []),
        "selected_psu_watts": setup.selected_psu_watts,
        "lighting_system_type": setup.lighting_system_type,
        "back_bevel_enabled": setup.back_bevel_enabled,
        "mounting_template_enabled": setup.mounting_template_enabled,
        "mounting_system": setup.mounting_system,
        "mounting_bar_profile": setup.mounting_bar_profile,
        "letter_group_finish_count": len(setup.letter_group_finishes),
        "letter_group_finish_pricing_mode": (
            "per_group_handoff" if setup.letter_group_finishes else "global_finish"
        ),
    }

    # Face finish mapping
    for face_val in _collect_face_finish_values(setup):
        mapping = V4_FACE_FINISH_TO_TEMPLATE.get(face_val)
        if mapping is None:
            result.warnings.append(
                _issue(
                    "template_option_missing",
                    message=f"Face finish '{face_val}' has no template option mapping.",
                    source="finish_setup.face_finish_type",
                    option_key=face_val,
                )
            )
        elif mapping[1] == "partial":
            result.warnings.append(
                _issue(
                    "discovered_option_not_canonicalized",
                    message=(
                        f"Face finish '{face_val}' maps to template '{mapping[0]}' with partial alignment — "
                        "not a dossier allowed_value."
                    ),
                    source="finish_setup.face_finish_type",
                    option_key=face_val,
                )
            )

    # Return finish mapping
    for ret_val in _collect_return_finish_values(setup):
        mapping = V4_RETURN_FINISH_TO_TEMPLATE.get(ret_val)
        if mapping is None:
            result.warnings.append(
                _issue(
                    "form_option_not_template_backed",
                    message=f"Return finish '{ret_val}' is not template-owned.",
                    source="finish_setup.return_finish_type",
                    option_key=ret_val,
                )
            )
        elif mapping[1] == "partial" and ret_val == "ral_paint" and not _ral_paint_tube_estimate_available(payload):
            result.warnings.append(
                _issue(
                    "template_pricing_code_missing",
                    message="RAL paint return requires paint_tube_count in quote_input — V4 does not auto-fill.",
                    source="finish_setup.return_finish_type",
                    option_key="ral_paint",
                )
            )

    # Return depth
    for depth in _collect_return_depths(setup):
        if depth not in RETURN_DEPTH_ALLOWED:
            result.warnings.append(
                _issue(
                    "template_material_intent_missing",
                    message=f"Return depth {depth} mm is outside dossier allowed_values.",
                    source="finish_setup.return_depth_mm",
                    option_key=str(depth),
                )
            )

    # PSU — V4 proposes array; template expects selected_psu_watts single value
    if setup.illuminated is not False:
        if setup.selected_psu_watts is not None and int(setup.selected_psu_watts) not in PSU_WATTS_ALLOWED:
            result.warnings.append(
                _issue(
                    "template_pricing_code_missing",
                    message=(
                        f"Selected PSU {setup.selected_psu_watts}W is outside dossier "
                        "selected_psu_watts allowed_values."
                    ),
                    source="finish_setup.selected_psu_watts",
                    option_key=str(setup.selected_psu_watts),
                )
            )
        psu_list = setup.psu_configuration or []
        for watts in psu_list:
            if int(watts) not in PSU_WATTS_ALLOWED:
                result.warnings.append(
                    _issue(
                        "template_pricing_code_missing",
                        message=f"PSU {watts}W is outside dossier selected_psu_watts allowed_values.",
                        source="finish_setup.psu_configuration",
                        option_key=str(watts),
                    )
                )
        if psu_list and len(psu_list) > 1:
            result.warnings.append(
                _issue(
                    "discovered_option_not_canonicalized",
                    message=(
                        "V4 psu_configuration is multi-unit array; template dossier expects "
                        "single selected_psu_watts for CostEngine variant pricing."
                    ),
                    source="finish_setup.psu_configuration",
                )
            )
        if setup.lighting_system_type and setup.lighting_system_type.strip().lower() == "led_strip":
            result.warnings.append(
                _issue(
                    "form_option_not_template_backed",
                    message="LED strip is not in dossier variants — template assumes led_modules.",
                    source="finish_setup.lighting_system_type",
                    option_key="led_strip",
                )
            )

    # Mounting — not captured in V4 form (catalog gap, informational)
    result.warnings.append(
        _issue(
            "discovered_option_not_canonicalized",
            severity="info",
            message=(
                "mounting_system / mounting_template_enabled are template-owned but not captured "
                "in Intake V4 form — QuoteWizard defaults apply after handoff."
            ),
            source="intake_v4_form_gap",
            option_key="mounting_system",
        )
    )

    result.warnings = [
        warning for warning in result.warnings if warning.source != "intake_v4_form_gap"
    ]
    if setup.back_bevel_enabled is None:
        result.warnings.append(
            _issue(
                "discovered_option_not_canonicalized",
                severity="info",
                message="Back bevel intent is derived from backing_mode until persisted explicitly.",
                source="finish_setup.back_bevel_enabled",
                option_key="back_bevel_enabled",
            )
        )
    if setup.mounting_template_enabled is None:
        result.warnings.append(
            _issue(
                "discovered_option_not_canonicalized",
                severity="info",
                message="Mounting template intent is not saved in Intake V4 yet.",
                source="finish_setup.mounting_template_enabled",
                option_key="mounting_template_enabled",
            )
        )
    elif setup.mounting_template_enabled and setup.mounting_template_area_m2 is None:
        result.warnings.append(
            _issue(
                "template_material_intent_missing",
                message="Mounting template is enabled but area is not available for material intent.",
                source="finish_setup.mounting_template_area_m2",
                option_key="mounting_template_area_m2",
            )
        )
    if not setup.mounting_system:
        result.warnings.append(
            _issue(
                "discovered_option_not_canonicalized",
                severity="info",
                message="Mounting system is template-owned but not saved in Intake V4 yet.",
                source="finish_setup.mounting_system",
                option_key="mounting_system",
            )
        )
    elif setup.mounting_system in {"steel_bars", "aluminum_bars"} and not setup.mounting_bar_profile:
        result.warnings.append(
            _issue(
                "template_material_intent_missing",
                message="Mounting bars selected but bar profile is missing.",
                source="finish_setup.mounting_bar_profile",
                option_key="mounting_bar_profile",
            )
        )

    # Multi-group finish is canonicalized by the V4 per-group pricing handoff.
    return result


def collect_template_contract_handoff_issues(
    payload: IntakeV4WorkspacePayload,
) -> list[TemplateOptionContractIssue]:
    """Issues suitable for merging into production handoff preview warnings."""
    contract = evaluate_v4_template_option_contract(payload)
    return contract.blockers + [w for w in contract.warnings if w.severity != "info"]


async def validate_finish_setup_against_dossier(
    db: AsyncSession,
    template_code: str,
    finish: IntakeV4FinishSetup,
) -> list[str]:
    """Validate submitted finish values against dossier allowed_values.

    Returns a list of warning strings (empty = pass).
    Non-blocking — caller decides whether to reject or log.
    """
    dossier_result = await db.execute(
        select(ProductBlueprintDossier).where(
            ProductBlueprintDossier.template_code == template_code
        )
    )
    dossier = dossier_result.scalar_one_or_none()
    variants = FALLBACK_DOSSIER_VARIANTS
    if dossier is not None:
        parsed = _json_loads(dossier.variants_json, [])
        if isinstance(parsed, list):
            variants = [v for v in parsed if isinstance(v, dict)]

    warnings: list[str] = []
    variant_map: dict[str, set] = {}
    for v in variants:
        key = v.get("variant_key")
        allowed = v.get("allowed_values")
        if key and isinstance(allowed, list) and allowed:
            variant_map[key] = set(allowed)

    # Validate return_depth_mm
    depth = finish.return_depth_mm
    if depth is not None and "return_depth_mm" in variant_map:
        if depth not in variant_map["return_depth_mm"]:
            warnings.append(
                f"return_depth_mm={depth} nu este în valorile permise dossier: {sorted(variant_map['return_depth_mm'])}"
            )

    # Validate selected_psu_watts
    psu = finish.selected_psu_watts
    if psu is not None and "selected_psu_watts" in variant_map:
        if psu not in variant_map["selected_psu_watts"]:
            warnings.append(
                f"selected_psu_watts={psu} nu este în valorile permise dossier: {sorted(variant_map['selected_psu_watts'])}"
            )

    # Validate face_finish_type (mapped — V4 values may differ from dossier canonical)
    face = finish.face_finish_type
    if face is not None and "face_finish_type" in variant_map:
        allowed_face = variant_map["face_finish_type"]
        # V4 UI values that map to canonical dossier values
        v4_to_dossier = {
            "oracal_641": "oracal_651",
            "print_laminate": "printed_laminated_vinyl",
        }
        canonical = v4_to_dossier.get(face, face)
        if canonical not in allowed_face:
            warnings.append(
                f"face_finish_type='{face}' (canonical '{canonical}') nu este în dossier: {sorted(allowed_face)}"
            )

    # Validate mounting_system
    ms = finish.mounting_system
    if ms is not None and "mounting_system" in variant_map:
        if ms not in variant_map["mounting_system"]:
            warnings.append(
                f"mounting_system='{ms}' nu este în valorile permise dossier: {sorted(variant_map['mounting_system'])}"
            )

    return warnings
