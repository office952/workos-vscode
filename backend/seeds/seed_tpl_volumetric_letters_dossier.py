"""TPL-VOLUMETRIC-LETTERS — template-level Blueprint Dossier seed.

Creates or updates one product_blueprint_dossier row for the active volumetric
letters template. Documents allowed production/offer options and production rules
without storing quote-specific selected values.

Idempotent — safe to re-run. Does not modify pricing, CostEngine, or other templates.

Source: ProductSystem onboarding playbook + volumetric costing/input contract audits.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401
from models.product_blueprint_dossier import ProductBlueprintDossier
from models.product_templates import Product_templates
from seeds.seed_build9_output_blocks import _volumetric_letters_output_blocks

logger = logging.getLogger(__name__)

TEMPLATE_CODE = "TPL-VOLUMETRIC-LETTERS"
FAMILY_ID = "litere_volumetrice"
DOSSIER_VERSION = 2
SOURCE_NOTES = (
    "Generated from ProductSystem template onboarding / volumetric costing audits. "
    "Owner-confirmed production rules as of build 46c8260+. Work Intake alignment "
    "build — task order, vector gate, RAL/Oracal metadata. Template-level only."
)


def _costengine_mapping() -> Dict[str, Any]:
    """Structural CostEngine mapping — no commercial prices."""
    return {
        "version": "27.09N",
        "template_code": TEMPLATE_CODE,
        "family_id": FAMILY_ID,
        "status": "approved_structural_mapping",
        "quote_ready": False,
        "pricing_ready": True,
        "inputs": {
            "required": [
                "width_mm",
                "height_mm",
                "depth_mm",
                "letter_face_area_m2",
                "letter_perimeter_m",
                "letter_count",
                "return_depth_mm",
                "selected_psu_watts",
                "paint_tube_count",
            ],
            "optional": [
                "psu_watts",
                "led_module_count",
                "back_bevel_enabled",
                "face_finish_type",
                "face_vinyl_color_code",
                "face_vinyl_roll_width_mm",
                "paint_ral_code",
                "mounting_template_enabled",
                "mounting_template_area_m2",
            ],
            "conditional": {
                "mounting_template_area_m2": "required when mounting_template_enabled=true",
            },
        },
        "derived_primitives": {
            "led_module_count": "ceil(letter_perimeter_m * 1000 / 100)",
            "paint_tube_quantity": "ceil(paint_tube_count)",
        },
        "material_keys": [
            "MAT-ACP-FATA-LITERE",
            "MAT-SPATE-PVC-LITERE",
            "MAT-PROFIL-LATERAL-LITERE",
            "MAT-LED-MODULE",
            "MAT-LED-PSU-12V",
            "MAT-VOPSEA-RAL",
            "MAT-SABLON-MONTAJ",
            "MAT-ORACAL-651",
            "MAT-VINYL-PRINT",
            "MAT-VINYL-PRINT-LAMINATED",
            "MAT-CONSUMABILE-MONTAJ",
        ],
        "operation_keys": [
            "vector_prep",
            "face_cnc_cut",
            "back_cut",
            "side_forming",
            "return_face_bonding",
            "led_install_letters",
            "electrical_letters",
            "painting",
            "vinyl_application",
            "packaging_letters",
            "mounting_template_cnc_cut",
            "qc_letters",
        ],
        "cost_basis_refs": {
            "material_unit_cost_ref": "inventory_materials_registry",
            "operation_rate_ref": "workcenter_rates_registry",
            "variant_profile_ref": "MAT-PROFIL-LATERAL-LITERE-{depth}MM",
            "variant_psu_ref": "MAT-LED-PSU-12V-{watts}W",
            "notes": "Rates exclude TVA; base currency from Settings.",
        },
        "option_modifiers": {
            "back_bevel_enabled": "back_cut pass_count +2 when true",
            "face_finish_type": "gates Oracal/vinyl materials + vinyl_application",
            "mounting_template_enabled": "gates MAT-SABLON-MONTAJ + mounting_template_cnc_cut",
        },
        "readiness_notes": [
            "Preliminary simulate-cost allowed without vector file.",
            "Final quote requires vector/file per quote_readiness_json.",
            "QC (qc_letters) is internal-only — no quote cost.",
        ],
    }


def _variants() -> List[Dict[str, Any]]:
    return [
        {
            "variant_key": "back_bevel_enabled",
            "name": "Șanfren spate Forex",
            "allowed_values": [False, True],
            "default_value": False,
            "description": "Forex 10 mm back: 3 cut passes default; +2 bevel passes when enabled.",
        },
        {
            "variant_key": "face_finish_type",
            "name": "Finisaj față plexi",
            "allowed_values": [
                "none",
                "oracal_651",
                "oracal_641",
                "oracal_8500",
                "printed_vinyl",
                "printed_laminated_vinyl",
            ],
            "default_value": "none",
            "description": (
                "Oracal 641 priced as 651; Oracal 8500 translucent captured with "
                "separate production metadata (color, roll width)."
            ),
        },
        {
            "variant_key": "mounting_template_enabled",
            "name": "Șablon montaj Forex",
            "allowed_values": [True, False],
            "default_value": True,
            "description": "Requires mounting_template_area_m2 when enabled.",
        },
        {
            "variant_key": "return_depth_mm",
            "name": "Adâncime cant / profil lateral",
            "allowed_values": [30, 60, 80, 100],
            "default_value": 60,
            "description": "Variant-priced profile material — quote_input required at pricing.",
        },
        {
            "variant_key": "selected_psu_watts",
            "name": "Putere sursă LED",
            "allowed_values": [60, 100, 160, 200],
            "default_value": 100,
            "description": "Variant-priced PSU — quote_input required at pricing.",
        },
        {
            "variant_key": "return_finish_type",
            "name": "Finisaj cant / volum",
            "allowed_values": [
                "white_aluminum",
                "black_aluminum",
                "gold_aluminum",
                "mirror_silver",
                "ral_paint",
                "oracal_wrapped",
            ],
            "default_value": "white_aluminum",
            "description": "Cant/return finish material — maps to material intent at handoff.",
        },
        {
            "variant_key": "lighting_system_type",
            "name": "Sistem iluminare LED",
            "allowed_values": ["led_modules", "led_strip"],
            "default_value": "led_modules",
            "description": "LED system type — led_modules is standard; led_strip is alternative.",
        },
        {
            "variant_key": "light_color",
            "name": "Culoare lumină LED",
            "allowed_values": ["warm", "neutral", "cool"],
            "default_value": "warm",
            "description": "LED light color temperature.",
        },
        {
            "variant_key": "led_module_power_w",
            "name": "Putere modul LED",
            "allowed_values": [0.75, 1.0, 1.44],
            "default_value": 0.75,
            "description": "LED module wattage — affects power consumption and PSU sizing.",
        },
        {
            "variant_key": "mounting_template_material_type",
            "name": "Material șablon montaj",
            "allowed_values": ["forex", "paper"],
            "default_value": "forex",
            "description": "Mounting template material — forex (CNC cut) or paper (print).",
        },
        {
            "variant_key": "face_vinyl_roll_width_mm",
            "name": "Lățime rolă vinyl față",
            "allowed_values": [1000, 1260],
            "default_value": 1000,
            "description": "Vinyl roll width for face finish application.",
        },
        {
            "variant_key": "emblem_lighting_mode",
            "name": "Mod iluminare emblemă",
            "allowed_values": ["area_lit", "excluded"],
            "default_value": "area_lit",
            "description": "Emblem/artwork lighting mode — area_lit calculates by area, excluded skips.",
        },
    ]


def _task_rules() -> Dict[str, Any]:
    return {
        "rules": [
            {
                "task_name": "vector_file_verification",
                "task_type": "READINESS_GATE",
                "trigger_condition": "always",
                "required_or_optional": "required",
                "sequence": 0,
                "internal_only": True,
                "description": (
                    "Verificare fișier/vector înainte de prepress: fișier prezent (SVG/DXF/DWG), "
                    "tip acceptat, analiză SVG dacă suportată, sau confirmare manuală pentru "
                    "DWG/DXF/alt tip. Nu se inventează geometrie din fișiere neanalizate. "
                    "letters_vector_file_required — readiness gate, not CostEngine priced."
                ),
            },
            {
                "task_name": "vector_prep",
                "task_type": "file_preparation",
                "trigger_condition": "always",
                "required_or_optional": "required",
                "sequence": 1,
                "priced_operation": "vector_prep",
                "description": "Pregătire grafică / prepress înainte de CNC.",
            },
            {
                "task_name": "cnc_face_cut",
                "task_type": "cnc_routing",
                "trigger_condition": "always",
                "required_or_optional": "required",
                "sequence": 2,
                "priced_operation": "face_cnc_cut",
                "description": "Debitare CNC față plexiglas + șanfren față (2 passes total).",
            },
            {
                "task_name": "cnc_back_cut",
                "task_type": "cnc_routing",
                "trigger_condition": "back_bevel_enabled false: 3 passes; true: 5 passes",
                "required_or_optional": "required",
                "sequence": 3,
                "priced_operation": "back_cut",
                "quote_input_trigger": "back_bevel_enabled",
                "description": "Debitare spate Forex; șanfren spate opțional.",
            },
            {
                "task_name": "return_profile_forming",
                "task_type": "edge_bending",
                "trigger_condition": "letter_perimeter_m present",
                "required_or_optional": "required",
                "sequence": 4,
                "priced_operation": "side_forming",
            },
            {
                "task_name": "return_face_bonding",
                "task_type": "volumetric_letter_assembly",
                "trigger_condition": "letter_perimeter_m present",
                "required_or_optional": "required",
                "sequence": 5,
                "priced_operation": "return_face_bonding",
            },
            {
                "task_name": "painting",
                "task_type": "volumetric_letter_assembly",
                "trigger_condition": "letter_perimeter_m present",
                "required_or_optional": "required",
                "sequence": 6,
                "priced_operation": "painting",
                "description": (
                    "Vopsire / finisare RAL — include paint_ral_code metadata when present. "
                    "MAT-VOPSEA-RAL tubes priced separately."
                ),
            },
            {
                "task_name": "vinyl_application",
                "task_type": "vinyl_cutting",
                "trigger_condition": "face_finish_type not none",
                "required_or_optional": "optional",
                "sequence": 7,
                "priced_operation": "vinyl_application",
                "quote_input_trigger": "face_finish_type",
                "description": (
                    "Aplicare autocolant când face_finish_type != none. "
                    "Oracal metadata: face_vinyl_color_code, face_vinyl_roll_width_mm."
                ),
            },
            {
                "task_name": "led_installation",
                "task_type": "led_assembly",
                "trigger_condition": "led_module_count derived from perimeter",
                "required_or_optional": "required",
                "sequence": 8,
                "priced_operation": "led_install_letters",
            },
            {
                "task_name": "electrical_wiring",
                "task_type": "led_wiring",
                "trigger_condition": "per letter_count",
                "required_or_optional": "required",
                "sequence": 9,
                "priced_operation": "electrical_letters",
            },
            {
                "task_name": "mounting_template",
                "task_type": "cnc_routing",
                "trigger_condition": "mounting_template_enabled=true",
                "required_or_optional": "optional",
                "sequence": 10,
                "priced_operation": "mounting_template_cnc_cut",
                "quote_input_trigger": "mounting_template_enabled",
                "description": "Pregătire șablon montaj Forex.",
            },
            {
                "task_name": "qc_internal_check",
                "task_type": "quality_control",
                "trigger_condition": "always",
                "required_or_optional": "required",
                "sequence": 13,
                "internal_only": True,
                "priced_operation": "qc_letters",
                "description": "QC intern — fără cost quote.",
            },
            {
                "task_name": "packaging",
                "task_type": "packaging",
                "trigger_condition": "always",
                "required_or_optional": "required",
                "sequence": 14,
                "priced_operation": "packaging_letters",
            },
        ]
    }


def _readiness_blocks() -> List[Dict[str, Any]]:
    """Internal documentation blocks referenced by readiness / production."""
    return [
        {
            "block_id": "geometry_summary",
            "block_type": "internal_documentation",
            "title": "Geometrie și input-uri core",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "Input-uri obligatorii: width_mm, height_mm, depth_mm, letter_face_area_m2, "
                "letter_perimeter_m, letter_count, return_depth_mm, selected_psu_watts, "
                "paint_tube_count. mounting_template_area_m2 când mounting_template_enabled=true. "
                "Geometria nu se inventează din intake — vector/manual/SVG."
            ),
            "variables": [],
        },
        {
            "block_id": "material_stack",
            "block_type": "internal_documentation",
            "title": "Stivă materiale",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "VIZUAL FAȚĂ: plexiglas 3mm PMMA - opal; opțional Oracal/vinyl. "
                "VOLUM ALUMINIU: profil lateral variantă depth. "
                "CAPAC SPATE: Forex 10 mm. SISTEM LED: module + PSU. "
                "FINISAJ: vopsea RAL tuburi întregi + consumabile. "
                "MONTAJ: sablon Forex opțional; bare oțel/aluminiu opțional."
            ),
            "variables": [],
        },
        {
            "block_id": "operation_stack",
            "block_type": "internal_documentation",
            "title": "Lanț operații",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "PREPRESS, CNC față/spate, forming, bonding, LED, electrical, painting, "
                "vinyl application (dacă finisaj), packaging, CNC șablon (dacă activ), QC intern."
            ),
            "variables": [],
        },
        {
            "block_id": "finish_options",
            "block_type": "internal_documentation",
            "title": "Opțiuni finisaj față",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "none | oracal_651 | printed_vinyl | printed_laminated_vinyl. "
                "Oracal 8500: film translucid — capturat în intake, tratat ca 651 la preț; "
                "metadata producție: cod culoare, nume, lucios/mat, lățime rolă."
            ),
            "variables": [],
        },
        {
            "block_id": "mounting_options",
            "block_type": "internal_documentation",
            "title": "Opțiuni șablon montaj",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "Șablon Forex opțional pentru montaj (mounting_template_enabled). "
                "Structurile metalice/premontaj sunt instrumentate în template separat."
            ),
            "variables": [],
        },
        {
            "block_id": "readiness_requirements",
            "block_type": "internal_documentation",
            "title": "Cerințe readiness",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "Simulare preliminară permisă fără vector. Ofertă finală: fișier vector obligatoriu. "
                "Opțiuni capturate dar neprețuite → warning, nu cost zero inventat."
            ),
            "variables": [],
        },
    ]


def _output_blocks() -> Dict[str, Any]:
    return {
        "short_description": (
            "Litere volumetrice 3D luminoase — față plexi, cant aluminiu, spate Forex, "
            "LED, finisaj și opțiuni montaj (Product 001)."
        ),
        "blocks": _readiness_blocks() + _volumetric_letters_output_blocks(),
    }


def _sections() -> Dict[str, Any]:
    return {
        "template_identity": {
            "template_code": TEMPLATE_CODE,
            "family_id": FAMILY_ID,
            "family_name": "Litere volumetrice luminoase",
            "purpose": (
                "Template pentru litere volumetrice luminoase cu față plexiglas 3mm PMMA - opal, "
                "cant aluminiu, spate Forex, LED, finisaj și opțiuni de montaj."
            ),
            "owner_valid_active": True,
            "source_notes": SOURCE_NOTES,
        },
        "components": [
            {"id": "comp_face_litere", "label": "VIZUAL FAȚĂ", "role": "față plexiglas 3mm PMMA - opal, CNC, vinyl opțional"},
            {"id": "comp_lateral_litere", "label": "VOLUM ALUMINIU", "role": "profil lateral, forming, bonding"},
            {"id": "comp_spate_litere", "label": "CAPAC SPATE", "role": "Forex 10 mm, CNC spate, back bevel opțional"},
            {"id": "comp_led_litere", "label": "SISTEM LED", "role": "module + PSU + cablaj"},
            {"id": "comp_finisaj_litere", "label": "FINISAJ", "role": "vopsire, sablon, packaging, QC intern"},
        ],
        "cnc_rules": {
            "face_plexi_3mm": {"cut_passes": 1, "bevel_passes": 1, "total_passes": 2},
            "back_forex_10mm": {
                "base_cut_passes": 3,
                "optional_bevel_passes": 2,
                "quote_input_key": "back_bevel_enabled",
                "total_passes_false": 3,
                "total_passes_true": 5,
            },
            "rate_basis_note": "CNC priced per ml/pass in Pricing Registry — not in dossier.",
        },
        "allowed_sections": [
            "variants",
            "task_rules",
            "output_blocks",
            "costengine_mapping",
            "quote_readiness",
            "production_notes",
            "qc_checkpoints",
        ],
    }


def _quote_readiness() -> Dict[str, Any]:
    return {
        "preliminary_simulation_without_vector": True,
        "final_quote_requires_vector_file": True,
        "vector_accepted_formats": ["SVG", "DXF", "DWG", "AI", "EPS"],
        "vector_analysis_policy": {
            "svg": "automatic_layer_analysis_when_provided",
            "dxf": "attached_unanalyzed_requires_manual_review_or_conversion",
            "dwg": "attached_source_only_no_auto_analysis",
            "pdf_vector": "not_implemented",
            "geometry_from_unparsed_file": False,
            "manual_review_field": "vector_manual_review_approved",
        },
        "captured_unpriced_options_policy": "warn_not_zero_cost",
        "production_metadata_recommended": [
            "face_vinyl_color_code",
            "face_vinyl_roll_width_mm",
            "paint_ral_code",
        ],
        "separate_template_products": ["metal_premount_structure"],
    }


def _production_notes() -> Dict[str, Any]:
    return {
        "notes": [
            "Colantare Oracal 651/8500 pe față plexi: la final sau înainte de montaj pe perete.",
            "Volum aluminiu: Oracal înainte de modelare SAU vopsire RAL după lipire pe șanfren față.",
            "Șanfren față necesar pentru lipire volum–față; șanfren spate Forex opțional (back_bevel_enabled).",
            "Fișier vector/producție: DWG acceptat ca atașament sursă; DXF/SVG preferate pentru analiză. "
            "DWG/DXF neanalizate necesită vector_manual_review_approved sau conversie SVG înainte de prepress.",
        ],
        "source": SOURCE_NOTES,
    }


def _qc_checkpoints() -> Dict[str, Any]:
    return {
        "checkpoints": [
            {
                "checkpoint_name": "vector_review",
                "what_to_verify": "Font, dimensiuni, spacing din fișier vector",
                "blocking_if_failed": True,
                "stage": "prepress",
            },
            {
                "checkpoint_name": "illumination_test",
                "what_to_verify": "Uniformitate LED per literă",
                "blocking_if_failed": True,
                "stage": "finisaj",
            },
            {
                "checkpoint_name": "qc_internal_final",
                "what_to_verify": "Control calitate intern — aliniament, finisaj, lipituri",
                "blocking_if_failed": False,
                "stage": "qc",
                "description": "Internal-only — nu adaugă cost ofertă.",
            },
        ]
    }


def _visual_prompt_blocks() -> Dict[str, Any]:
    return {
        "prompt": (
            "Litere volumetrice 3D cu față plexi, cant aluminiu, spate Forex, "
            "iluminare LED pe spate, finisaj RAL/vinyl opțional."
        ),
        "style": "production_reference",
    }


def _dossier_payload() -> Dict[str, Any]:
    return {
        "template_code": TEMPLATE_CODE,
        "dossier_version": DOSSIER_VERSION,
        "status": "approved",
        "owner_role": "product_owner",
        "reviewer_role": "technical_reviewer",
        "reviewed_at": datetime.now(timezone.utc),
        "sections_json": json.dumps(_sections(), ensure_ascii=False),
        "variants_json": json.dumps(_variants(), ensure_ascii=False),
        "task_rules_json": json.dumps(_task_rules(), ensure_ascii=False),
        "costengine_mapping_json": json.dumps(_costengine_mapping(), ensure_ascii=False),
        "quote_readiness_json": json.dumps(_quote_readiness(), ensure_ascii=False),
        "output_blocks_json": json.dumps(_output_blocks(), ensure_ascii=False),
        "visual_prompt_blocks_json": json.dumps(_visual_prompt_blocks(), ensure_ascii=False),
        "production_notes_json": json.dumps(_production_notes(), ensure_ascii=False),
        "qc_checkpoints_json": json.dumps(_qc_checkpoints(), ensure_ascii=False),
    }


async def seed_tpl_volumetric_letters_dossier() -> Dict[str, Any]:
    """Create or update the volumetric letters blueprint dossier."""
    result: Dict[str, Any] = {
        "template_code": TEMPLATE_CODE,
        "action": None,
        "dossier_id": None,
        "skipped": False,
    }

    async with db_manager.async_session_maker() as session:
        tpl = (
            await session.execute(
                select(Product_templates).where(
                    Product_templates.template_code == TEMPLATE_CODE
                )
            )
        ).scalar_one_or_none()

        if tpl is None:
            result["skipped"] = True
            result["error"] = "template_not_found"
            logger.warning("Template %s not found — dossier seed skipped", TEMPLATE_CODE)
            return result

        if tpl.active is False:
            result["skipped"] = True
            result["error"] = "template_inactive"
            logger.warning("Template %s inactive — dossier seed skipped", TEMPLATE_CODE)
            return result

        existing = (
            await session.execute(
                select(ProductBlueprintDossier).where(
                    ProductBlueprintDossier.template_id == tpl.id
                )
            )
        ).scalar_one_or_none()

        payload = _dossier_payload()
        payload["template_id"] = tpl.id

        if existing is None:
            row = ProductBlueprintDossier(**payload)
            session.add(row)
            await session.commit()
            await session.refresh(row)
            result["action"] = "created"
            result["dossier_id"] = row.id
            logger.info("Created blueprint dossier id=%s for %s", row.id, TEMPLATE_CODE)
            return result

        prior_status = str(existing.status or "").strip().lower()
        target_status = str(payload.get("status") or "").strip().lower()
        if prior_status == "deprecated" and target_status == "approved":
            result["status_repaired_from_deprecated"] = True
            logger.warning(
                "Repairing dossier id=%s for %s: status deprecated -> approved (v%s)",
                existing.id,
                TEMPLATE_CODE,
                payload.get("dossier_version"),
            )

        for key, value in payload.items():
            if key != "template_id":
                setattr(existing, key, value)
        await session.commit()
        await session.refresh(existing)
        result["action"] = "updated"
        result["dossier_id"] = existing.id
        result["status"] = existing.status
        logger.info("Updated blueprint dossier id=%s for %s", existing.id, TEMPLATE_CODE)
        return result


if __name__ == "__main__":
    import asyncio

    logging.basicConfig(level=logging.INFO)

    async def _main() -> None:
        await db_manager.init_db()
        out = await seed_tpl_volumetric_letters_dossier()
        print(json.dumps(out, indent=2, default=str))

    asyncio.run(_main())
