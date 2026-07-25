"""BUILD 9 — Seed output_blocks_json for all 6 Build 4 product templates.

Populates the output_blocks_json field in product_blueprint_dossier for each
of the 6 advertising production templates created in Build 4.

Templates covered:
  1. TPL-BANNER-STANDARD      — Banner publicitar
  2. TPL-PLEXI-PLATE          — Placa plexiglass
  3. TPL-VINYL-STICKER        — Autocolant / sticker
  4. TPL-LIGHTBOX-STANDARD    — Caseta luminoasa
  5. TPL-VOLUMETRIC-LETTERS   — Litere volumetrice
  6. TPL-MESH-EXTERNALIZED    — Mesh externalizat

Rules:
  - Idempotent — re-running is safe (upsert on template_code match).
  - Only updates output_blocks_json — no other dossier fields touched.
  - Each template gets 3-5 output blocks covering:
    * product_description (client-facing)
    * technical_specifications (internal)
    * production_notes (internal)
    * commercial_terms (client-facing, offer)
    * externalization_note (where applicable)
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List

from sqlalchemy import select, update

from core.database import db_manager
import models  # noqa: F401
from models.product_blueprint_dossier import ProductBlueprintDossier

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Output blocks definitions per template
# ---------------------------------------------------------------------------

def _banner_output_blocks() -> List[Dict[str, Any]]:
    return [
        {
            "block_id": "banner-desc-01",
            "block_type": "product_description",
            "title": "Descriere Banner Publicitar",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Banner publicitar PVC {{product_name}} — imprimare ecosolvent/UV "
                "format mare. Dimensiuni: {{width_mm}}mm x {{height_mm}}mm. "
                "Material: PVC 510g/mp sau mesh (la cerere)."
            ),
            "variables": [
                {"name": "product_name", "source_field": "identity.product_name", "required": True, "missing_behavior": "render_with_warning"},
                {"name": "width_mm", "source_field": "quote_context.dimensions.width_mm", "required": False, "missing_behavior": "render_with_warning"},
                {"name": "height_mm", "source_field": "quote_context.dimensions.height_mm", "required": False, "missing_behavior": "render_with_warning"},
            ],
        },
        {
            "block_id": "banner-tech-01",
            "block_type": "technical_specifications",
            "title": "Specificații Tehnice Banner",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "Tip imprimare: ecosolvent/UV. Role disponibile: 1100/1350/1600mm. "
                "Finisare: tiv termosudat (30mm standard), capse la {{caps_spacing}}cm. "
                "Rezoluție print: 720-1440 dpi."
            ),
            "variables": [
                {"name": "caps_spacing", "source_field": "quote_context.selected_options.caps_spacing_cm", "required": False, "missing_behavior": "use_approved_fallback"},
            ],
        },
        {
            "block_id": "banner-prod-01",
            "block_type": "production_notes",
            "title": "Note Producție Banner",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "1. Verificare fișier grafic (rezoluție, bleed, culori CMYK)\n"
                "2. Selectare rolă conform lățime optimă\n"
                "3. Print + uscare 24h\n"
                "4. Tăiere la dimensiune finală\n"
                "5. Tiv termosudat pe margini\n"
                "6. Montaj capse conform spacing specificat\n"
                "7. Control calitate final"
            ),
            "variables": [],
        },
        {
            "block_id": "banner-commercial-01",
            "block_type": "commercial_terms",
            "title": "Condiții Comerciale Banner",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Termen execuție: 3-5 zile lucrătoare. "
                "Garanție: 2 ani outdoor (condiții normale). "
                "Livrare: ridicare din atelier sau curier (cost suplimentar)."
            ),
            "variables": [],
        },
    ]


def _plexi_output_blocks() -> List[Dict[str, Any]]:
    return [
        {
            "block_id": "plexi-desc-01",
            "block_type": "product_description",
            "title": "Descriere Placă Plexiglass",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Placă plexiglas {{product_name}} — tăiere laser/CNC de precizie. "
                "Dimensiuni: {{width_mm}}mm x {{height_mm}}mm. "
                "Tip: {{plexi_type}}, grosime: {{thickness_mm}}mm."
            ),
            "variables": [
                {"name": "product_name", "source_field": "identity.product_name", "required": True, "missing_behavior": "render_with_warning"},
                {"name": "width_mm", "source_field": "quote_context.dimensions.width_mm", "required": False, "missing_behavior": "render_with_warning"},
                {"name": "height_mm", "source_field": "quote_context.dimensions.height_mm", "required": False, "missing_behavior": "render_with_warning"},
                {"name": "plexi_type", "source_field": "quote_context.selected_options.plexi_type", "required": False, "missing_behavior": "use_approved_fallback"},
                {"name": "thickness_mm", "source_field": "quote_context.selected_options.thickness_mm", "required": False, "missing_behavior": "use_approved_fallback"},
            ],
        },
        {
            "block_id": "plexi-tech-01",
            "block_type": "technical_specifications",
            "title": "Specificații Tehnice Plexiglass",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "Material: plexiglas extrudat/turnat. Grosimi: 3/5/10mm. "
                "Tăiere: laser CO2 (precizie ±0.1mm). "
                "Finisare muchii: flame polish sau șlefuire manuală. "
                "Opțiuni: print UV direct, aplicare vinyl, distanțiere inox."
            ),
            "variables": [],
        },
        {
            "block_id": "plexi-prod-01",
            "block_type": "production_notes",
            "title": "Note Producție Plexiglass",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "1. Verificare dimensiuni și toleranțe\n"
                "2. Programare CNC/laser\n"
                "3. Tăiere cu protecție folie\n"
                "4. Finisare muchii (flame polish dacă transparent)\n"
                "5. Aplicare print/vinyl (dacă specificat)\n"
                "6. Găurire pentru montaj (dacă specificat)\n"
                "7. Montaj distanțiere (dacă specificat)\n"
                "8. QC final — verificare claritate, zgârieturi"
            ),
            "variables": [],
        },
        {
            "block_id": "plexi-commercial-01",
            "block_type": "commercial_terms",
            "title": "Condiții Comerciale Plexiglass",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Termen execuție: 5-7 zile lucrătoare. "
                "Garanție: 3 ani (condiții normale de utilizare). "
                "Livrare: ambalaj protecție + ridicare/curier."
            ),
            "variables": [],
        },
    ]


def _vinyl_sticker_output_blocks() -> List[Dict[str, Any]]:
    return [
        {
            "block_id": "vinyl-desc-01",
            "block_type": "product_description",
            "title": "Descriere Autocolant/Sticker",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Autocolant/sticker {{product_name}} — print digital pe vinyl autoadeziv. "
                "Dimensiuni: {{width_mm}}mm x {{height_mm}}mm. "
                "Tip vinyl: {{vinyl_type}}. Laminare UV: inclusă."
            ),
            "variables": [
                {"name": "product_name", "source_field": "identity.product_name", "required": True, "missing_behavior": "render_with_warning"},
                {"name": "width_mm", "source_field": "quote_context.dimensions.width_mm", "required": False, "missing_behavior": "render_with_warning"},
                {"name": "height_mm", "source_field": "quote_context.dimensions.height_mm", "required": False, "missing_behavior": "render_with_warning"},
                {"name": "vinyl_type", "source_field": "quote_context.selected_options.vinyl_type", "required": False, "missing_behavior": "use_approved_fallback"},
            ],
        },
        {
            "block_id": "vinyl-tech-01",
            "block_type": "technical_specifications",
            "title": "Specificații Tehnice Vinyl",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "Vinyl: calandrat (3-5 ani) / turnat (7-10 ani). "
                "Laminare: matt/gloss UV (protecție UV + rezistență mecanică). "
                "Tăiere contur: plotter Summa/Graphtec (precizie ±0.5mm). "
                "Bandă transfer: inclusă pentru aplicare uscată."
            ),
            "variables": [],
        },
        {
            "block_id": "vinyl-prod-01",
            "block_type": "production_notes",
            "title": "Note Producție Vinyl",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "1. Verificare fișier (vectori, culori, bleed)\n"
                "2. Print pe vinyl selectat\n"
                "3. Laminare UV (matt sau gloss)\n"
                "4. Tăiere contur pe plotter\n"
                "5. Debitare/peliculare manuală\n"
                "6. Aplicare bandă transfer\n"
                "7. QC — verificare aderență, culori, contur"
            ),
            "variables": [],
        },
        {
            "block_id": "vinyl-commercial-01",
            "block_type": "commercial_terms",
            "title": "Condiții Comerciale Vinyl",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Termen execuție: 2-4 zile lucrătoare. "
                "Garanție: 3 ani outdoor (vinyl calandrat), 7 ani (vinyl turnat). "
                "Instrucțiuni aplicare incluse."
            ),
            "variables": [],
        },
    ]


def _lightbox_output_blocks() -> List[Dict[str, Any]]:
    return [
        {
            "block_id": "lightbox-desc-01",
            "block_type": "product_description",
            "title": "Descriere Casetă Luminoasă",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Casetă luminoasă LED {{product_name}} — cadru aluminiu, "
                "față plexiglas/policarbonat iluminată uniform cu module LED. "
                "Dimensiuni: {{width_mm}}mm x {{height_mm}}mm x {{depth_mm}}mm."
            ),
            "variables": [
                {"name": "product_name", "source_field": "identity.product_name", "required": True, "missing_behavior": "render_with_warning"},
                {"name": "width_mm", "source_field": "quote_context.dimensions.width_mm", "required": False, "missing_behavior": "render_with_warning"},
                {"name": "height_mm", "source_field": "quote_context.dimensions.height_mm", "required": False, "missing_behavior": "render_with_warning"},
                {"name": "depth_mm", "source_field": "quote_context.dimensions.depth_mm", "required": False, "missing_behavior": "render_with_warning"},
            ],
        },
        {
            "block_id": "lightbox-tech-01",
            "block_type": "technical_specifications",
            "title": "Specificații Tehnice Casetă Luminoasă",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "Cadru: profil aluminiu anodizat. Față: plexiglas opal 3-5mm. "
                "Iluminare: module LED SMD 2835/5050, 6500K sau 4000K. "
                "Surse: Mean Well (IP67 pentru exterior). "
                "Consum: ~8W/mp. Uniformitate: >85%."
            ),
            "variables": [],
        },
        {
            "block_id": "lightbox-prod-01",
            "block_type": "production_notes",
            "title": "Note Producție Casetă Luminoasă",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "1. Debitare profil aluminiu la dimensiuni\n"
                "2. Sudare/asamblare cadru\n"
                "3. Montaj panou spate (ACP/tablă)\n"
                "4. Instalare module LED + cablaj\n"
                "5. Conectare surse alimentare\n"
                "6. Test iluminare (uniformitate, consum)\n"
                "7. Montaj față plexiglas cu grafică\n"
                "8. Test final + certificat electric"
            ),
            "variables": [],
        },
        {
            "block_id": "lightbox-commercial-01",
            "block_type": "commercial_terms",
            "title": "Condiții Comerciale Casetă Luminoasă",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Termen execuție: 10-15 zile lucrătoare. "
                "Garanție: 3 ani (LED + sursă), 5 ani (structură). "
                "Montaj: disponibil la cerere (cost separat). "
                "Certificat conformitate electrică inclus."
            ),
            "variables": [],
        },
        {
            "block_id": "lightbox-electrical-01",
            "block_type": "technical_specifications",
            "title": "Cerințe Electrice",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "Alimentare: 220V AC → 12V/24V DC. "
                "Protecție: IP44 (interior) / IP67 (exterior). "
                "Conector: MC4 sau terminal block. "
                "Cablu alimentare: minim 3x1.5mm². "
                "Necesită priză dedicată cu împământare."
            ),
            "variables": [],
        },
    ]


def _volumetric_letters_output_blocks() -> List[Dict[str, Any]]:
    return [
        {
            "block_id": "letters-desc-01",
            "block_type": "product_description",
            "title": "Descriere Litere Volumetrice",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Litere volumetrice 3D {{product_name}} — față plexiglas 3mm PMMA - opal, "
                "bordură profil aluminiu, spate Forex 10 mm, iluminare LED opțională. "
                "Text: conform vector furnizat. Înălțime literă: {{height_mm}}mm."
            ),
            "variables": [
                {"name": "product_name", "source_field": "identity.product_name", "required": True, "missing_behavior": "render_with_warning"},
                {"name": "height_mm", "source_field": "quote_context.dimensions.height_mm", "required": False, "missing_behavior": "render_with_warning"},
            ],
        },
        {
            "block_id": "letters-tech-01",
            "block_type": "technical_specifications",
            "title": "Specificații Tehnice Litere Volumetrice",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "Față: plexiglas 3mm PMMA - opal tăiat (opțional vinyl/oracal); șanfren față configurabil. "
                "Bordură: profil aluminiu (adâncime 30–150 mm configurabilă). "
                "Spate litere: Forex 10 mm (nu panou ACM); șanfren spate configurabil. "
                "LED: module pe spate Forex; cablaj + sursă. "
                "Premontaj opțional: perete / structură metalică / panou ACM casetat (suport). "
                "Finisaj: vopsire RAL la cerere."
            ),
            "variables": [],
        },
        {
            "block_id": "letters-prod-01",
            "block_type": "production_notes",
            "title": "Note Producție Litere Volumetrice",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "1. Verificare vector (font, dimensiuni, spacing)\n"
                "2. Debitare CNC față + spate\n"
                "3. Îndoire/tăiere laterale profil\n"
                "4. Asamblare literă (lipire/sudare)\n"
                "5. Montaj LED + cablaj intern\n"
                "6. Vopsire RAL (dacă specificat)\n"
                "7. Test iluminare per literă\n"
                "8. Asamblare pe șablon montaj\n"
                "9. QC final — uniformitate, aliniament"
            ),
            "variables": [],
        },
        {
            "block_id": "letters-commercial-01",
            "block_type": "commercial_terms",
            "title": "Condiții Comerciale Litere Volumetrice",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Termen execuție: 15-20 zile lucrătoare. "
                "Garanție: 3 ani (LED), 5 ani (structură metalică). "
                "Montaj: disponibil la cerere cu echipă specializată. "
                "Șablon montaj inclus."
            ),
            "variables": [],
        },
    ]


def _mesh_externalized_output_blocks() -> List[Dict[str, Any]]:
    return [
        {
            "block_id": "mesh-desc-01",
            "block_type": "product_description",
            "title": "Descriere Mesh Externalizat",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Mesh publicitar {{product_name}} — print de înaltă calitate "
                "pe mesh perforat. Dimensiuni: {{width_mm}}mm x {{height_mm}}mm. "
                "Ideal pentru fațade, schele, garduri."
            ),
            "variables": [
                {"name": "product_name", "source_field": "identity.product_name", "required": True, "missing_behavior": "render_with_warning"},
                {"name": "width_mm", "source_field": "quote_context.dimensions.width_mm", "required": False, "missing_behavior": "render_with_warning"},
                {"name": "height_mm", "source_field": "quote_context.dimensions.height_mm", "required": False, "missing_behavior": "render_with_warning"},
            ],
        },
        {
            "block_id": "mesh-tech-01",
            "block_type": "technical_specifications",
            "title": "Specificații Tehnice Mesh",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "Material: mesh PVC perforat (270-340g/mp). "
                "Perforare: micro (1000x1000) sau standard (500x500). "
                "Print: UV/ecosolvent, rezoluție 360-720 dpi. "
                "Finisare: tiv + capse (spacing conform specificație)."
            ),
            "variables": [],
        },
        {
            "block_id": "mesh-ext-01",
            "block_type": "production_notes",
            "title": "Externalizare Producție Mesh",
            "document_type": "production_sheet",
            "audience": "internal",
            "approval_status": "approved",
            "template_text": (
                "⚠️ EXTERNALIZAT — NU se produce intern.\n"
                "1. Pregătire fișier grafic (profil culoare furnizor)\n"
                "2. Transmitere comandă la furnizor extern\n"
                "3. Recepție + QC (verificare culori, dimensiuni, defecte)\n"
                "4. Finisare internă: tiv/capse (dacă nu incluse de furnizor)\n"
                "5. Ambalare + livrare client"
            ),
            "variables": [],
        },
        {
            "block_id": "mesh-commercial-01",
            "block_type": "commercial_terms",
            "title": "Condiții Comerciale Mesh",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Termen execuție: 7-10 zile lucrătoare (include producție externă). "
                "Garanție: 2 ani outdoor. "
                "Livrare: transport inclus pentru comenzi > 50mp."
            ),
            "variables": [],
        },
        {
            "block_id": "mesh-ext-note-01",
            "block_type": "product_description",
            "title": "Notă Externalizare",
            "document_type": "offer",
            "audience": "client",
            "approval_status": "approved",
            "template_text": (
                "Producția mesh-ului este realizată de partenerul nostru specializat, "
                "cu control calitate efectuat intern înainte de livrare."
            ),
            "variables": [],
        },
    ]


# ---------------------------------------------------------------------------
# Template code -> output blocks mapping
# ---------------------------------------------------------------------------
TEMPLATE_OUTPUT_BLOCKS: Dict[str, List[Dict[str, Any]]] = {
    "TPL-BANNER-STANDARD": _banner_output_blocks(),
    "TPL-PLEXI-PLATE": _plexi_output_blocks(),
    "TPL-VINYL-STICKER": _vinyl_sticker_output_blocks(),
    "TPL-LIGHTBOX-STANDARD": _lightbox_output_blocks(),
    "TPL-VOLUMETRIC-LETTERS": _volumetric_letters_output_blocks(),
    "TPL-MESH-EXTERNALIZED": _mesh_externalized_output_blocks(),
}


# ---------------------------------------------------------------------------
# Seed runner
# ---------------------------------------------------------------------------

async def seed_output_blocks() -> Dict[str, Any]:
    """Seed output_blocks_json for all 6 Build 4 templates.

    Idempotent — updates existing dossiers, creates none.
    Returns summary of actions taken.
    """
    results = {"updated": [], "skipped": [], "missing_dossier": []}

    async with db_manager.session() as session:
        for template_code, blocks in TEMPLATE_OUTPUT_BLOCKS.items():
            # Find dossier by template_code
            query = select(ProductBlueprintDossier).where(
                ProductBlueprintDossier.template_code == template_code
            )
            result = await session.execute(query)
            dossier = result.scalar_one_or_none()

            if not dossier:
                results["missing_dossier"].append(template_code)
                logger.warning(f"No dossier found for {template_code} — skipping")
                continue

            # Update output_blocks_json
            blocks_json = json.dumps(blocks, ensure_ascii=False)
            stmt = (
                update(ProductBlueprintDossier)
                .where(ProductBlueprintDossier.id == dossier.id)
                .values(output_blocks_json=blocks_json)
            )
            await session.execute(stmt)
            results["updated"].append(template_code)
            logger.info(f"Updated output_blocks_json for {template_code} ({len(blocks)} blocks)")

        await session.commit()

    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    async def main():
        await db_manager.init_db()
        results = await seed_output_blocks()
        print(f"Seed results: {json.dumps(results, indent=2)}")

    asyncio.run(main())