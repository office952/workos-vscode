"""Seed script for `TPL-ACP-LIGHT-ROUTED` — first real production template.

Sprint #21.2 REWORK — canonical 6-component shape.

This seeds the hierarchical (Sprint #15 shape) template for the backlit
ACP routed panel, using:

- canonical family `panouri_acp_iluminate` (Sprint #20),
- canonical material codes seeded in Sprint #20 (`MAT-ACP-3MM`,
  `MAT-PLEXI-OPAL-3MM`, `MAT-PLEXI-OPAL-10MM`, `MAT-LED-MODULE`,
  `MAT-LED-PSU-12V`, `MAT-PROFIL-ALU`, `MAT-SURUBURI-GEN`,
  `MAT-ADEZIV-SILICON`, `MAT-CONSUMABILE-MONTAJ`),
- canonical workcenter codes seeded in Sprint #20 (`CNC_ROUTER`,
  `PANEL_CUTTING`, `LED_ASSEMBLY`, `ASSEMBLY`, `FINISHING`,
  `INSTALL_PREP`),
- formula-based lines (Sprint #21.1) with Sprint #21.1.5 handler
  upgrades (`passes` from template params, `path_length_key` per CNC op).

**Canonical component list (6, mandatory — see
`docs/spec/spec__product_template__tpl_acp_light_routed.md` §2):**

1. `comp_structura`          — STRUCTURA         — static
2. `comp_fata_acp_routata`   — FATA_ACP_ROUTATA  — formula-based (ACP + CNC)
3. `comp_difuzie_plexi`      — DIFUZIE_PLEXI     — formula-based (area + CNC)
4. `comp_iluminare`          — ILUMINARE         — formula-based (LED+PSU+mount)
5. `comp_relief_plexi_10mm`  — RELIEF_PLEXI_10MM — formula-based (area + CNC 4 passes)
6. `comp_finisaj`            — FINISAJ           — static

Guardrails honoured (Sprint #21.2 REWORK):

- NO commercial values invented — unit prices and workcenter rates
  come from the registries at cost-calculation time.
- Idempotent on `template_code` — re-running is safe.
- Additive-only — no other template is touched.
- Shape matches exactly what `CostEngineWithMaterialRates._cost_one_component`
  expects. Formula-based lines follow the Sprint #21.1 + #21.1.5 contract:
  `calculation_type="formula_based"`, `formula_id`, `formula_params`
  (with `passes` + `path_length_key` where applicable),
  `requires_quote_input`.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, List

from sqlalchemy import select

from core.database import db_manager
import models  # noqa: F401 - register all models with Base.metadata
from models.product_templates import Product_templates

logger = logging.getLogger(__name__)


TEMPLATE_CODE = "TPL-ACP-LIGHT-ROUTED"
FAMILY_ID = "panouri_acp_iluminate"
FAMILY_NAME = "Panouri ACP Iluminate"
DESCRIPTION = (
    "Panou ACP (Dibond) iluminat din spate, cu frezare CNC pentru "
    "personalizare, difuzor plexiglas opal 3mm si element de relief "
    "plexiglas 10mm (frezat in 4 treceri). Cantitatile care depind de "
    "comanda (arie ACP cu coeficient 1.42, arie difuzor, numar LED, "
    "sursa PSU, timpi frezare) sunt calculate prin formule la ofertare."
)


# ---------------------------------------------------------------------------
# Components (hierarchical shape consumed by CostEngine v2)
# ---------------------------------------------------------------------------
COMPONENTS: List[Dict[str, Any]] = [
    # -----------------------------------------------------------------
    # 1. comp_structura — STRUCTURA — all static
    # -----------------------------------------------------------------
    {
        "component_id": "comp_structura",
        "type": "STRUCTURA",
        "name": "Structura caseta (profil aluminiu + fixari)",
        "materials": [
            {
                "material_code": "MAT-PROFIL-ALU",
                "name": "Profil aluminiu structura",
                "quantity": 4.0,
                "unit": "ml",
            },
            {
                "material_code": "MAT-SURUBURI-GEN",
                "name": "Suruburi / prinderi",
                "quantity": 1.0,
                "unit": "set",
            },
            {
                "material_code": "MAT-ADEZIV-SILICON",
                "name": "Adeziv / silicon montaj",
                "quantity": 1.0,
                "unit": "buc",
            },
        ],
        "operations": [
            {
                "code": "ASSEMBLE_STRUCTURE",
                "name": "Asamblare corp caseta",
                "workcenter": "ASSEMBLY",
                "estimated_minutes": 30,
                "sequence": 1,
                "component_ref": "comp_structura",
            },
        ],
    },
    # -----------------------------------------------------------------
    # 2. comp_fata_acp_routata — FATA_ACP_ROUTATA — ACP + CNC routing
    # -----------------------------------------------------------------
    # ACP area rule (spec §2.2): front_face × 1.42 = base (1.00) +
    # return flanges + waste allowance (0.42). Encoded as TWO lines
    # because `relief_material_area` constrains coverage_pct to (0, 1].
    # Both lines sum to the canonical 1.42 coefficient the shop floor
    # uses to procure ACP, and their cost aggregates under the same
    # material_code, so the pricing result is identical to a single
    # 1.42-coverage line while respecting the handler contract.
    # CNC routing uses path_length_key="personalization_path_length_mm"
    # so this op never collides with the diffuser cut or the relief cut.
    {
        "component_id": "comp_fata_acp_routata",
        "type": "FATA_ACP_ROUTATA",
        "name": "Fata ACP cu frezare CNC personalizare",
        "materials": [
            {
                "material_code": "MAT-ACP-3MM",
                "name": "ACP / Dibond 3mm — panou de baza",
                "unit": "mp",
                "calculation_type": "formula_based",
                "formula_id": "relief_material_area",
                "formula_params": {"coverage_pct": 1.00},
                "requires_quote_input": ["front_face_area_m2"],
            },
            {
                "material_code": "MAT-ACP-3MM",
                "name": "ACP / Dibond 3mm — flanse intoarcere + adaos debitare",
                "unit": "mp",
                "calculation_type": "formula_based",
                "formula_id": "relief_material_area",
                "formula_params": {"coverage_pct": 0.42},
                "requires_quote_input": ["front_face_area_m2"],
            },
        ],
        "operations": [
            {
                "code": "CUT_ACP",
                "name": "Debitare panou ACP la dimensiune",
                "workcenter": "PANEL_CUTTING",
                "estimated_minutes": 10,
                "sequence": 1,
                "component_ref": "comp_fata_acp_routata",
            },
            {
                "code": "ROUTE_ACP",
                "name": "Frezare CNC personalizare ACP",
                "workcenter": "CNC_ROUTER",
                "sequence": 2,
                "component_ref": "comp_fata_acp_routata",
                "calculation_type": "formula_based",
                "formula_id": "cnc_time_from_path",
                "formula_params": {
                    "divisor_mm_per_min": 1500.0,
                    "passes": 1,
                    "path_length_key": "personalization_path_length_mm",
                },
                "requires_quote_input": [
                    "personalization_path_length_mm",
                ],
            },
        ],
    },
    # -----------------------------------------------------------------
    # 3. comp_difuzie_plexi — DIFUZIE_PLEXI — plexi opal diffuser
    # -----------------------------------------------------------------
    # Diffuser sheet area = bounding area + symmetric 50 mm margin.
    # Diffuser CNC cut uses path_length_key="diffuser_cut_path_length_mm".
    {
        "component_id": "comp_difuzie_plexi",
        "type": "DIFUZIE_PLEXI",
        "name": "Difuzor plexiglas opal 3mm",
        "materials": [
            {
                "material_code": "MAT-PLEXI-OPAL-3MM",
                "name": "Plexiglas opal 3mm",
                "unit": "mp",
                "calculation_type": "formula_based",
                "formula_id": "plexi_diffuser_area",
                "formula_params": {"margin_mm": 50.0},
                "requires_quote_input": ["personalization_bounding_area_m2"],
            },
        ],
        "operations": [
            {
                "code": "CUT_DIFFUSER",
                "name": "Debitare difuzor plexiglas",
                "workcenter": "PANEL_CUTTING",
                "sequence": 1,
                "component_ref": "comp_difuzie_plexi",
                "calculation_type": "formula_based",
                "formula_id": "cnc_time_from_path",
                "formula_params": {
                    "divisor_mm_per_min": 2000.0,
                    "passes": 1,
                    "path_length_key": "diffuser_cut_path_length_mm",
                },
                "requires_quote_input": ["diffuser_cut_path_length_mm"],
            },
        ],
    },
    # -----------------------------------------------------------------
    # 4. comp_iluminare — ILUMINARE — LED + PSU + assembly
    # -----------------------------------------------------------------
    # LED density 55/m2, watts_per_led=1.44, safety=1.2, PSU options
    # [60,100,200]. Worked example (front_face_area_m2=1.0, led_count=55):
    #   total = 55 * 1.44 * 1.2 = 95.04 W
    #   picked PSU = smallest >= 95.04 = 100 W → psu_count = ceil(95.04/100) = 1.
    # LED assembly: max(led_count/3, 15) minutes.
    {
        "component_id": "comp_iluminare",
        "type": "ILUMINARE",
        "name": "Iluminare LED backlit + sursa",
        "materials": [
            {
                "material_code": "MAT-LED-MODULE",
                "name": "Modul LED",
                "unit": "buc",
                "calculation_type": "formula_based",
                "formula_id": "led_count_from_area",
                "formula_params": {"leds_per_m2": 55.0},
                "requires_quote_input": ["front_face_area_m2"],
            },
            {
                "material_code": "MAT-LED-PSU-12V",
                "name": "Sursa alimentare LED 12V",
                "unit": "buc",
                "calculation_type": "formula_based",
                "formula_id": "led_psu_sizing",
                "formula_params": {
                    "watts_per_led": 1.44,
                    "safety_factor": 1.2,
                    "psu_options_w": [60.0, 100.0, 200.0],
                },
                "requires_quote_input": ["led_count"],
            },
            {
                "material_code": "MAT-CONSUMABILE-MONTAJ",
                "name": "Consumabile montaj LED",
                "quantity": 1.0,
                "unit": "set",
            },
        ],
        "operations": [
            {
                "code": "LED_MOUNT",
                "name": "Montaj module LED + sursa",
                "workcenter": "LED_ASSEMBLY",
                "sequence": 1,
                "component_ref": "comp_iluminare",
                "calculation_type": "formula_based",
                "formula_id": "led_assembly_time",
                "formula_params": {
                    "leds_per_minute": 3.0,
                    "min_minutes": 15.0,
                },
                "requires_quote_input": ["led_count"],
            },
        ],
    },
    # -----------------------------------------------------------------
    # 5. comp_relief_plexi_10mm — RELIEF_PLEXI_10MM — 10mm plexi relief
    # -----------------------------------------------------------------
    # Relief material area = 30% of front face.
    # Relief CNC cut at 4 PASSES (10mm plexi, ~3mm/pass + finishing pass).
    # Uses path_length_key="relief_cut_path_length_mm" so the relief path
    # is decoupled from ACP routing + diffuser cut.
    # Worked example: path=4000mm, divisor=2000, passes=4 → 8.0 min.
    {
        "component_id": "comp_relief_plexi_10mm",
        "type": "RELIEF_PLEXI_10MM",
        "name": "Relief plexiglas opal 10mm (frezat 4 treceri)",
        "materials": [
            {
                "material_code": "MAT-PLEXI-OPAL-10MM",
                "name": "Plexiglas opal 10mm",
                "unit": "mp",
                "calculation_type": "formula_based",
                "formula_id": "relief_material_area",
                "formula_params": {"coverage_pct": 0.30},
                "requires_quote_input": ["front_face_area_m2"],
            },
        ],
        "operations": [
            {
                "code": "CNC_RELIEF",
                "name": "Frezare CNC relief 10mm",
                "workcenter": "CNC_ROUTER",
                "sequence": 1,
                "component_ref": "comp_relief_plexi_10mm",
                "calculation_type": "formula_based",
                "formula_id": "cnc_time_from_path",
                "formula_params": {
                    "divisor_mm_per_min": 2000.0,
                    "passes": 4,
                    "path_length_key": "relief_cut_path_length_mm",
                },
                "requires_quote_input": ["relief_cut_path_length_mm"],
            },
        ],
    },
    # -----------------------------------------------------------------
    # 6. comp_finisaj — FINISAJ — finishing + pack/install prep
    # -----------------------------------------------------------------
    {
        "component_id": "comp_finisaj",
        "type": "FINISAJ",
        "name": "Finisare + pregatire montaj / ambalare",
        "materials": [
            {
                "material_code": "MAT-CONSUMABILE-MONTAJ",
                "name": "Consumabile finisare + ambalare",
                "quantity": 1.0,
                "unit": "set",
            },
        ],
        "operations": [
            {
                "code": "FINISH",
                "name": "Finisare / curatare",
                "workcenter": "FINISHING",
                "estimated_minutes": 10,
                "sequence": 1,
                "component_ref": "comp_finisaj",
            },
            {
                "code": "PACK",
                "name": "Pregatire montaj / ambalare",
                "workcenter": "INSTALL_PREP",
                "estimated_minutes": 15,
                "sequence": 2,
                "component_ref": "comp_finisaj",
            },
        ],
    },
]


def _template_payload() -> Dict[str, Any]:
    return {
        "template_code": TEMPLATE_CODE,
        "family_id": FAMILY_ID,
        "family_name": FAMILY_NAME,
        "description": DESCRIPTION,
        "components_json": json.dumps(COMPONENTS, ensure_ascii=False),
        "operations_json": None,  # v2 hierarchical — ops live inside components
        "required_materials_json": None,  # v2 hierarchical — mats live inside components
        "estimated_hours": None,
        "base_labor_rate": None,
        "base_margin_pct": None,
        "active": False,
        "notes": (
            "Prima template productiva reala (Sprint #21.2 REWORK). "
            "6 componente canonice (structura, fata ACP routata, difuzie "
            "plexi, iluminare, relief plexi 10mm, finisaj). Cantitatile "
            "variabile sunt rezolvate prin formule la ofertare; preturile "
            "materialelor si ratele workcenter-elor vin din registrele "
            "canonice, nu din acest seed."
        ),
    }


async def seed_tpl_acp_light_routed() -> Dict[str, Any]:
    """Seed `TPL-ACP-LIGHT-ROUTED` idempotently on `template_code`.

    On re-run, updates the existing row's `components_json` + metadata
    fields to match the current canonical shape defined here. This keeps
    the seed self-healing if the canonical shape ever changes (the spec
    is the source of truth — not the historical DB row). Idempotency is
    preserved: row count stays at 1; re-running with an already-current
    payload produces no observable state change.

    Returns a stats dict with keys `inserted` (0 or 1) and `skipped`
    (0 or 1), plus `template_code`.
    """
    inserted = 0
    skipped = 0

    async with db_manager.async_session_maker() as session:
        existing = await session.execute(
            select(Product_templates).where(
                Product_templates.template_code == TEMPLATE_CODE
            )
        )
        row = existing.scalar_one_or_none()
        payload = _template_payload()

        if row is None:
            session.add(Product_templates(**payload))
            inserted = 1
        else:
            # Keep canonical shape in sync without duplicating the row.
            for key, value in payload.items():
                if key == "template_code":
                    continue
                setattr(row, key, value)
            skipped = 1

        await session.commit()

    logger.info(
        "Seeded %s: inserted=%d skipped=%d",
        TEMPLATE_CODE,
        inserted,
        skipped,
    )
    return {
        "template_code": TEMPLATE_CODE,
        "inserted": inserted,
        "skipped": skipped,
    }


async def _main() -> None:
    await db_manager.init_db()
    stats = await seed_tpl_acp_light_routed()
    print(
        f"[seed_tpl_acp_light_routed] template={stats['template_code']} "
        f"inserted={stats['inserted']} skipped={stats['skipped']}"
    )


if __name__ == "__main__":
    asyncio.run(_main())