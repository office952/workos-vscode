"""Product 001 — TPL-VOLUMETRIC-LETTERS preliminary costing registry prices.

Owner-confirmed purchase costs (accepted_override) and editable estimated defaults
(needs_review) for preliminary calculation only — not final commercial quote activation.

No prices in CostEngine. Idempotent seeds via patch_inventory_material_by_code.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from core.database import db_manager
from services.inventory_materials_admin_service import (
    get_inventory_material_by_code,
    patch_inventory_material_by_code,
)
from seeds.material_canonical_naming import canonical_name_for_code, source_notes_for_code
from services.volumetric_material_rate_resolver import (
    OWNER_CONFIRMED_PROFILE_LABOR_NOTES,
    PROFILE_DEPTH_MM_TO_VARIANT_CODE,
    PSU_WATTS_TO_VARIANT_CODE,
    TEMPLATE_PROFILE_CODE,
    TEMPLATE_PSU_CODE,
)

OWNER_CONFIRMED_VALID_FROM = datetime(2026, 6, 4, tzinfo=timezone.utc)
OWNER_CONFIRMED_VAT_PERCENT = 19.0
CHANGE_REASON = "Product 001 volumetric owner-confirmed purchase cost"
ESTIMATED_CHANGE_REASON = "Product 001 volumetric preliminary estimated cost"
SOURCE_NAME = "owner_confirmed_product_001_volumetric"
ESTIMATED_SOURCE_NAME = "preliminary_estimated_product_001_volumetric"
SOURCE_REVIEWED_BY = "seed_volumetric_owner_confirmed_prices"
PSU_MANUAL_FX_REFERENCE_RON_PER_EUR = 5.2
PSU_EUR_CHANGE_REASON = (
    "Product 001 PSU — owner manual EUR normalization "
    f"(reference {PSU_MANUAL_FX_REFERENCE_RON_PER_EUR} RON/EUR, commercially rounded)"
)


def _psu_eur_source_notes(*, watts: int, ron_reference: float, eur_value: float) -> str:
    """Owner-approved manual EUR pricing note — not live FX."""
    calculated = round(ron_reference / PSU_MANUAL_FX_REFERENCE_RON_PER_EUR, 2)
    return (
        "Owner-confirmed pricing (EUR) for template costing. "
        f"Supplier reference: {ron_reference:.0f} RON/buc purchase "
        "(procurement record — not converted automatically elsewhere). "
        f"Manual owner conversion at fixed reference "
        f"{PSU_MANUAL_FX_REFERENCE_RON_PER_EUR} RON/EUR — not live FX. "
        f"Calculated: {ron_reference:.0f}/{PSU_MANUAL_FX_REFERENCE_RON_PER_EUR}="
        f"{calculated:.2f} → commercially rounded {eur_value:.0f} EUR/buc. "
        f"Template code {TEMPLATE_PSU_CODE} resolves via "
        f"quote_input.selected_psu_watts or quote_input.psu_watts={watts}."
    )


class _PriceRow(TypedDict, total=False):
    code: str
    unit_cost: float
    currency: str
    name: Optional[str]
    source_notes: str


# Purchase cost only — no commercial markup in unit_cost.
OWNER_CONFIRMED_VOLUMETRIC_PRICES: List[_PriceRow] = [
    {
        "code": "MAT-ACP-FATA-LITERE",
        "unit_cost": 16.0,
        "currency": "EUR",
        "name": canonical_name_for_code(
            "MAT-ACP-FATA-LITERE",
            "PMMA / plexiglas acrilic 3 mm — față litere",
        ),
        "source_notes": source_notes_for_code(
            "MAT-ACP-FATA-LITERE",
            (
                "Owner-confirmed purchase: Plexiglas 3 mm face = 16 EUR/mp (purchase, no markup). "
                "Legacy code name references ACP; volumetric production uses plexi/acrylic face, "
                "not ACM/Bond panel (15 EUR/mp is a separate premount material). "
                "Waste: owner standard 20% — template formula_params may differ (e.g. waste_pct 0.15); "
                "do not fold waste into unit_cost."
            ),
        ),
    },
    {
        "code": "MAT-SPATE-PVC-LITERE",
        "unit_cost": 16.0,
        "currency": "EUR",
        "name": canonical_name_for_code("MAT-SPATE-PVC-LITERE", "PVC expandat 10 mm"),
        "source_notes": source_notes_for_code(
            "MAT-SPATE-PVC-LITERE",
            (
                "Owner-confirmed purchase: Forex 10 mm backing = 16 EUR/mp (purchase, no markup). "
                "Operational code MAT-SPATE-PVC-LITERE; spate literă = Forex 10 mm alias. "
                "Waste: owner standard 20% — template may use waste_pct 0.10 in formula_params."
            ),
        ),
    },
    {
        "code": "MAT-LED-MODULE",
        "unit_cost": 0.5,
        "currency": "EUR",
        "source_notes": (
            "Owner-confirmed purchase: LED module = 0.5 EUR/buc (purchase, no markup). "
            "TPL-VOLUMETRIC-LETTERS: count from letter_perimeter_m, module_length_mm=75, "
            "module_gap_mm=25, pitch=100 mm (formula led_per_letter perimeter mode)."
        ),
    },
    {
        "code": "MAT-SABLON-MONTAJ",
        "unit_cost": 6.0,
        "currency": "EUR",
        "name": canonical_name_for_code("MAT-SABLON-MONTAJ", "PVC expandat 3 mm — șablon montaj"),
        "source_notes": source_notes_for_code(
            "MAT-SABLON-MONTAJ",
            (
                "Owner-confirmed purchase: Forex 3 mm mounting template = 6 EUR/mp (purchase, no markup). "
                "Șablon montaj din PVC expandat 3 mm (alias Forex); CNC separat. "
                "Quantity from quote_input.mounting_template_area_m2 when mounting_template_material_type=forex."
            ),
        ),
    },
    {
        "code": "MAT-SABLON-HARTIE",
        "unit_cost": 5.0,
        "currency": "EUR",
        "name": canonical_name_for_code("MAT-SABLON-HARTIE", "Șablon hârtie"),
        "source_notes": source_notes_for_code(
            "MAT-SABLON-HARTIE",
            (
                "Owner-confirmed purchase: paper mounting template = 5 EUR/mp (purchase, no markup). "
                "Quantity from quote_input.mounting_template_area_m2 when mounting_template_material_type=paper. "
                "Stored excluding TVA; TVA configured separately."
            ),
        ),
    },
    {
        "code": "MAT-VOPSEA-RAL",
        "unit_cost": 10.0,
        "currency": "EUR",
        "name": "Vopsea RAL spray — tub",
        "source_notes": (
            "Owner-confirmed purchase: RAL spray tub. Owner reference 50 RON/tub. "
            "Manually converted at 5.2 RON/EUR = 9.61 EUR and commercially rounded to 10 EUR/tub. "
            "Not live FX. Charged quantity uses whole tubes only: ceil(estimated_paint_tubes). "
            "Material consumable only — PAINTING operation (4 EUR/ml service) is separate. "
            "Stored excluding TVA; TVA configured separately."
        ),
    },
    {
        "code": "MAT-VOPSEA-RAL-CANT-30MM",
        "unit_cost": 2.0,
        "currency": "EUR",
        "name": "Vopsire RAL cant 30 mm - material",
        "source_notes": (
            "Owner-confirmed purchase: return_cant RAL material 30 mm = 2 EUR/ml excluding TVA. "
            "Width-scoped material row for return_cant paint_application only. "
            "Material row remains separate from RETURN_CANT_RAL_PAINT_LABOR."
        ),
    },
    {
        "code": "MAT-VOPSEA-RAL-CANT-60MM",
        "unit_cost": 2.5,
        "currency": "EUR",
        "name": "Vopsire RAL cant 60 mm - material",
        "source_notes": (
            "Owner-confirmed purchase: return_cant RAL material 60 mm = 2.5 EUR/ml excluding TVA. "
            "Width-scoped material row for return_cant paint_application only. "
            "Material row remains separate from RETURN_CANT_RAL_PAINT_LABOR."
        ),
    },
    {
        "code": "MAT-VOPSEA-RAL-CANT-80MM",
        "unit_cost": 3.0,
        "currency": "EUR",
        "name": "Vopsire RAL cant 80 mm - material",
        "source_notes": (
            "Owner-confirmed purchase: return_cant RAL material 80 mm = 3 EUR/ml excluding TVA. "
            "Width-scoped material row for return_cant paint_application only. "
            "Material row remains separate from RETURN_CANT_RAL_PAINT_LABOR."
        ),
    },
    {
        "code": "MAT-VOPSEA-RAL-CANT-100MM",
        "unit_cost": 4.0,
        "currency": "EUR",
        "name": "Vopsire RAL cant 100 mm - material",
        "source_notes": (
            "Owner-confirmed purchase: return_cant RAL material 100 mm = 4 EUR/ml excluding TVA. "
            "Width-scoped material row for return_cant paint_application only. "
            "Material row remains separate from RETURN_CANT_RAL_PAINT_LABOR."
        ),
    },
    {
        "code": "MAT-ORACAL-651",
        "unit_cost": 9.0,
        "currency": "EUR",
        "name": canonical_name_for_code("MAT-ORACAL-651", "Folie autocolantă PVC — Oracal 651"),
        "source_notes": source_notes_for_code(
            "MAT-ORACAL-651",
            (
                "Owner-confirmed purchase: Oracal 651 = 9 EUR/mp excluding TVA. "
                "Quantity from quote_input.letter_face_area_m2 when face_finish_type=oracal_651."
            ),
        ),
    },
    {
        "code": "MAT-VINYL-PRINT",
        "unit_cost": 1.5,
        "currency": "EUR",
        "name": canonical_name_for_code(
            "MAT-VINYL-PRINT", "Folie autocolantă PVC — print față litere"
        ),
        "source_notes": (
            "Owner-confirmed purchase: autocolant pentru print = 1.5 EUR/mp excluding TVA. "
            "Serviciul print (8.5 EUR/mp) and laminarea (5 EUR/mp) are priced separately."
        ),
    },
    {
        "code": "MAT-VINYL-PRINT-LAMINATED",
        "unit_cost": 10.0,
        "currency": "EUR",
        "name": canonical_name_for_code(
            "MAT-VINYL-PRINT-LAMINATED",
            "Folie autocolantă PVC — print + laminare față litere",
        ),
        "source_notes": (
            "Owner-confirmed purchase: print + lamination combined = 10 EUR/mp excluding TVA. "
            "Quantity from letter_face_area_m2 when face_finish_type=printed_laminated_vinyl."
        ),
    },
    {
        "code": "MAT-ORACAL-641",
        "unit_cost": 6.5,
        "currency": "EUR",
        "name": "Folie autocolantă PVC — Oracal 641 Economy Cal",
        "source_notes": (
            "Owner-confirmed purchase: Oracal 641 = 6.5 EUR/mp excluding TVA. "
            "Economy-tier vinyl for face finish. "
            "Quantity from quote_input.letter_face_area_m2 when face_finish_type=oracal_641."
        ),
    },
    {
        "code": "MAT-ORACAL-8500",
        "unit_cost": 20.0,
        "currency": "EUR",
        "name": "Folie autocolantă PVC — Oracal 8500 Translucent Cal",
        "source_notes": (
            "Owner-confirmed purchase: Oracal 8500 = 20.0 EUR/mp excluding TVA. "
            "Translucent vinyl for backlit letter face finish. "
            "Quantity from quote_input.letter_face_area_m2 when face_finish_type=oracal_8500."
        ),
    },
    {
        "code": "MAT-LED-STRIP",
        "unit_cost": 2.0,
        "currency": "EUR",
        "source_notes": (
            "Owner-confirmed purchase: Bandă LED 12V strip = 2.0 EUR/ml excluding TVA. "
            "Quantity from finish_setup.total_led_strip_length_m when lighting_system_type=led_strip."
        ),
    },
    {
        "code": "MAT-PREMOUNT-BAR-STEEL",
        "unit_cost": 2.0,
        "currency": "EUR",
        "name": canonical_name_for_code(
            "MAT-PREMOUNT-BAR-STEEL", "Țeavă pătrată oțel 30×30×1.5 mm"
        ),
        "source_notes": source_notes_for_code(
            "MAT-PREMOUNT-BAR-STEEL",
            (
                "Owner-confirmed purchase: square steel tube 30×30×1.5 mm = 2 EUR/ml excluding TVA. "
                "Utilizare legacy: premount bars (steel_bars). "
                "Quantity from mounting_bar_total_length when mounting_system=steel_bars."
            ),
        ),
    },
    {
        "code": "MAT-PREMOUNT-BAR-ALUMINUM",
        "unit_cost": 3.5,
        "currency": "EUR",
        "name": canonical_name_for_code(
            "MAT-PREMOUNT-BAR-ALUMINUM", "Țeavă pătrată aluminiu 30×30×1.5 mm"
        ),
        "source_notes": source_notes_for_code(
            "MAT-PREMOUNT-BAR-ALUMINUM",
            (
                "Owner-confirmed purchase: aluminum tube 30×30×1.5 mm = 3.5 EUR/ml excluding TVA. "
                "Utilizare legacy: premount bars (aluminum_bars)."
            ),
        ),
    },
]

# Preliminary estimates — active for costing bridge, needs_owner_review (editable).
ESTIMATED_PRELIMINARY_PRICES: List[_PriceRow] = [
    {
        "code": "MAT-CONSUMABILE-MONTAJ",
        "unit_cost": 5.0,
        "currency": "EUR",
        "source_notes": (
            "Estimare temporară pentru calcul preliminar TPL-VOLUMETRIC-LETTERS; "
            "owner trebuie să confirme/modifice. Nu este owner-confirmed."
        ),
    },
]

# Depth-tier return/cant — one registry row per owner-confirmed depth (EUR/ml purchase).
OWNER_CONFIRMED_PROFILE_DEPTH_PRICES: List[_PriceRow] = [
    {
        "code": "MAT-PROFIL-LATERAL-LITERE-30MM",
        "unit_cost": 2.0,
        "currency": "EUR",
        "source_notes": (
            "Owner-confirmed purchase: aluminum return/cant 30 mm = 2 EUR/ml (purchase, no markup). "
            f"Template code {TEMPLATE_PROFILE_CODE} resolves via quote_input.return_depth_mm=30. "
            "Waste: owner standard 20% for aluminum return — use formula_params.extra_pct, not unit_cost."
        ),
    },
    {
        "code": "MAT-PROFIL-LATERAL-LITERE-60MM",
        "unit_cost": 3.0,
        "currency": "EUR",
        "source_notes": (
            "Owner-confirmed purchase: aluminum return/cant 60 mm = 3 EUR/ml (purchase, no markup). "
            f"Template code {TEMPLATE_PROFILE_CODE} resolves via quote_input.return_depth_mm=60."
        ),
    },
    {
        "code": "MAT-PROFIL-LATERAL-LITERE-80MM",
        "unit_cost": 4.0,
        "currency": "EUR",
        "source_notes": (
            "Owner-confirmed purchase: aluminum return/cant 80 mm = 4 EUR/ml (purchase, no markup). "
            f"Template code {TEMPLATE_PROFILE_CODE} resolves via quote_input.return_depth_mm=80."
        ),
    },
    {
        "code": "MAT-PROFIL-LATERAL-LITERE-100MM",
        "unit_cost": 5.0,
        "currency": "EUR",
        "source_notes": (
            "Owner-confirmed purchase: aluminum return/cant 100 mm = 5 EUR/ml (purchase, no markup). "
            f"Template code {TEMPLATE_PROFILE_CODE} resolves via quote_input.return_depth_mm=100."
        ),
    },
]

PROFILE_DEPTH_VARIANT_CODES = frozenset(PROFILE_DEPTH_MM_TO_VARIANT_CODE.values())

OWNER_CONFIRMED_PSU_WATTAGE_PRICES: List[_PriceRow] = [
    {
        "code": "MAT-LED-PSU-12V-60W",
        "unit_cost": 12.0,
        "currency": "EUR",
        "source_notes": _psu_eur_source_notes(
            watts=60, ron_reference=60.0, eur_value=12.0
        ),
    },
    {
        "code": "MAT-LED-PSU-12V-100W",
        "unit_cost": 16.0,
        "currency": "EUR",
        "source_notes": _psu_eur_source_notes(
            watts=100, ron_reference=80.0, eur_value=16.0
        ),
    },
    {
        "code": "MAT-LED-PSU-12V-160W",
        "unit_cost": 20.0,
        "currency": "EUR",
        "source_notes": _psu_eur_source_notes(
            watts=160, ron_reference=100.0, eur_value=20.0
        ),
    },
    {
        "code": "MAT-LED-PSU-12V-200W",
        "unit_cost": 40.0,
        "currency": "EUR",
        "source_notes": _psu_eur_source_notes(
            watts=200, ron_reference=200.0, eur_value=40.0
        ),
    },
]

PSU_WATTAGE_VARIANT_CODES = frozenset(PSU_WATTS_TO_VARIANT_CODE.values())

TEMPLATE_PROFILE_REFERENCE_NOTES = (
    "Operational template code for lateral return/cant — NOT a single purchase price. "
    "Select depth-tier variant by quote_input.return_depth_mm (30/60/80/100): "
    + ", ".join(
        f"{depth}mm→{code}" for depth, code in sorted(PROFILE_DEPTH_MM_TO_VARIANT_CODE.items())
    )
    + ". "
    + OWNER_CONFIRMED_PROFILE_LABOR_NOTES
)

TEMPLATE_PSU_REFERENCE_NOTES = (
    "Operational template code for LED PSU — NOT a single purchase price. "
    "Select wattage variant by quote_input.selected_psu_watts or quote_input.psu_watts "
    "(60|100|160|200): "
    + ", ".join(
        f"{watts}W→{code}" for watts, code in sorted(PSU_WATTS_TO_VARIANT_CODE.items())
    )
    + ". psu_count formula quantity still uses template formula_params; "
    "material unit_cost alias is separate from psu_count math."
)

# Generic template codes without single unit_cost (variant alias at quote time):
#   MAT-PROFIL-LATERAL-LITERE, MAT-LED-PSU-12V


def _already_applied(existing: Dict[str, Any], row: _PriceRow) -> bool:
    if str(existing.get("status") or "") != "active":
        return False
    if existing.get("unit_cost") != row["unit_cost"]:
        return False
    if str(existing.get("currency") or "").upper() != str(row["currency"]).upper():
        return False
    if str(existing.get("source_review_status") or "") != "accepted_override":
        return False
    return True


def _estimated_already_applied(existing: Dict[str, Any], row: _PriceRow) -> bool:
    if str(existing.get("status") or "") != "active":
        return False
    if existing.get("unit_cost") != row["unit_cost"]:
        return False
    if str(existing.get("currency") or "").upper() != str(row["currency"]).upper():
        return False
    if str(existing.get("source_review_status") or "") != "needs_review":
        return False
    return True


async def _apply_estimated_price_rows(
    session: Any,
    rows: List[_PriceRow],
    *,
    results: List[Dict[str, Any]],
) -> tuple[int, int, int]:
    patched = 0
    skipped = 0
    not_found = 0
    for row in rows:
        code = row["code"]
        existing = await get_inventory_material_by_code(session, code)
        if existing is None:
            not_found += 1
            results.append({"code": code, "action": "SKIPPED_NOT_FOUND"})
            continue
        if _estimated_already_applied(existing, row):
            skipped += 1
            results.append({"code": code, "action": "SKIPPED_ALREADY_APPLIED_ESTIMATED"})
            continue

        patch_kwargs: Dict[str, Any] = {
            "unit_cost": row["unit_cost"],
            "currency": row["currency"],
            "vat_percent": OWNER_CONFIRMED_VAT_PERCENT,
            "valid_from": OWNER_CONFIRMED_VALID_FROM,
            "status": "active",
            "source_name": ESTIMATED_SOURCE_NAME,
            "source_checked_at": OWNER_CONFIRMED_VALID_FROM,
            "source_notes": row["source_notes"],
            "source_review_status": "needs_review",
            "source_reviewed_at": OWNER_CONFIRMED_VALID_FROM,
            "source_reviewed_by": SOURCE_REVIEWED_BY,
            "change_reason": ESTIMATED_CHANGE_REASON,
            "changed_by": SOURCE_REVIEWED_BY,
            "snapshot_source": "seed_volumetric_owner_confirmed_prices",
        }
        if row.get("name"):
            patch_kwargs["name"] = row["name"]

        updated = await patch_inventory_material_by_code(session, code, **patch_kwargs)
        patched += 1
        results.append(
            {
                "code": code,
                "action": "PATCHED_ESTIMATED",
                "unit_cost": updated["unit_cost"] if updated else None,
                "source_review_status": "needs_review",
            }
        )
    return patched, skipped, not_found


async def _apply_price_rows(
    session: Any,
    rows: List[_PriceRow],
    *,
    results: List[Dict[str, Any]],
) -> tuple[int, int, int]:
    patched = 0
    skipped = 0
    not_found = 0
    for row in rows:
        code = row["code"]
        existing = await get_inventory_material_by_code(session, code)
        if existing is None:
            not_found += 1
            results.append({"code": code, "action": "SKIPPED_NOT_FOUND"})
            continue
        if _already_applied(existing, row):
            skipped += 1
            results.append({"code": code, "action": "SKIPPED_ALREADY_APPLIED"})
            continue

        change_reason = (
            PSU_EUR_CHANGE_REASON
            if str(code).startswith("MAT-LED-PSU-12V-")
            else CHANGE_REASON
        )
        patch_kwargs: Dict[str, Any] = {
            "unit_cost": row["unit_cost"],
            "currency": row["currency"],
            "vat_percent": OWNER_CONFIRMED_VAT_PERCENT,
            "valid_from": OWNER_CONFIRMED_VALID_FROM,
            "status": "active",
            "source_name": SOURCE_NAME,
            "source_checked_at": OWNER_CONFIRMED_VALID_FROM,
            "source_notes": row["source_notes"],
            "source_review_status": "accepted_override",
            "source_reviewed_at": OWNER_CONFIRMED_VALID_FROM,
            "source_reviewed_by": SOURCE_REVIEWED_BY,
            "change_reason": change_reason,
            "changed_by": SOURCE_REVIEWED_BY,
            "snapshot_source": "seed_volumetric_owner_confirmed_prices",
        }
        if row.get("name"):
            patch_kwargs["name"] = row["name"]

        updated = await patch_inventory_material_by_code(session, code, **patch_kwargs)
        patched += 1
        results.append(
            {
                "code": code,
                "action": "PATCHED",
                "unit_cost": updated["unit_cost"] if updated else None,
                "currency": updated["currency"] if updated else None,
                "status": updated["status"] if updated else None,
            }
        )
    return patched, skipped, not_found


async def seed_volumetric_owner_confirmed_prices() -> Dict[str, Any]:
    """Apply owner-confirmed volumetric material purchase prices. Idempotent."""
    results: List[Dict[str, Any]] = []
    patched = 0
    skipped = 0
    not_found = 0

    async with db_manager.async_session_maker() as session:
        p, s, n = await _apply_price_rows(
            session,
            OWNER_CONFIRMED_VOLUMETRIC_PRICES,
            results=results,
        )
        patched += p
        skipped += s
        not_found += n

        p, s, n = await _apply_price_rows(
            session,
            OWNER_CONFIRMED_PROFILE_DEPTH_PRICES,
            results=results,
        )
        patched += p
        skipped += s
        not_found += n

        p, s, n = await _apply_price_rows(
            session,
            OWNER_CONFIRMED_PSU_WATTAGE_PRICES,
            results=results,
        )
        patched += p
        skipped += s
        not_found += n

        p, s, n = await _apply_estimated_price_rows(
            session,
            ESTIMATED_PRELIMINARY_PRICES,
            results=results,
        )
        patched += p
        skipped += s
        not_found += n

        generic = await get_inventory_material_by_code(session, TEMPLATE_PROFILE_CODE)
        if generic is not None:
            notes = str(generic.get("source_notes") or "")
            if TEMPLATE_PROFILE_REFERENCE_NOTES[:40] not in notes:
                await patch_inventory_material_by_code(
                    session,
                    TEMPLATE_PROFILE_CODE,
                    source_notes=TEMPLATE_PROFILE_REFERENCE_NOTES,
                    source_name=SOURCE_NAME,
                    source_checked_at=OWNER_CONFIRMED_VALID_FROM,
                    source_review_status="accepted_override",
                    source_reviewed_at=OWNER_CONFIRMED_VALID_FROM,
                    source_reviewed_by=SOURCE_REVIEWED_BY,
                )
                results.append(
                    {"code": TEMPLATE_PROFILE_CODE, "action": "REFERENCE_NOTES_PATCHED"}
                )
            else:
                results.append(
                    {"code": TEMPLATE_PROFILE_CODE, "action": "REFERENCE_NOTES_SKIPPED"}
                )

        psu_generic = await get_inventory_material_by_code(session, TEMPLATE_PSU_CODE)
        if psu_generic is not None:
            psu_notes = str(psu_generic.get("source_notes") or "")
            if TEMPLATE_PSU_REFERENCE_NOTES[:40] not in psu_notes:
                await patch_inventory_material_by_code(
                    session,
                    TEMPLATE_PSU_CODE,
                    source_notes=TEMPLATE_PSU_REFERENCE_NOTES,
                    source_name=SOURCE_NAME,
                    source_checked_at=OWNER_CONFIRMED_VALID_FROM,
                    source_review_status="accepted_override",
                    source_reviewed_at=OWNER_CONFIRMED_VALID_FROM,
                    source_reviewed_by=SOURCE_REVIEWED_BY,
                )
                results.append(
                    {"code": TEMPLATE_PSU_CODE, "action": "REFERENCE_NOTES_PATCHED"}
                )
            else:
                results.append(
                    {"code": TEMPLATE_PSU_CODE, "action": "REFERENCE_NOTES_SKIPPED"}
                )

        await session.commit()

    return {
        "patched": patched,
        "skipped": skipped,
        "not_found": not_found,
        "results": results,
    }


VOLUMETRIC_TEMPLATE_MATERIAL_CODES = [
    "MAT-ACP-FATA-LITERE",
    "MAT-ORACAL-641",
    "MAT-ORACAL-651",
    "MAT-ORACAL-8500",
    "MAT-LED-STRIP",
    "MAT-VINYL-PRINT",
    "MAT-VINYL-PRINT-LAMINATED",
    "MAT-PROFIL-LATERAL-LITERE",
    "MAT-SPATE-PVC-LITERE",
    "MAT-LED-MODULE",
    "MAT-LED-PSU-12V",
    "MAT-VOPSEA-RAL",
    "MAT-SABLON-MONTAJ",
    "MAT-SABLON-HARTIE",
    "MAT-PREMOUNT-BAR-STEEL",
    "MAT-PREMOUNT-BAR-ALUMINUM",
    "MAT-CONSUMABILE-MONTAJ",
]

OWNER_CONFIRMED_ACTIVATED_CODES = frozenset(
    r["code"]
    for r in (
        OWNER_CONFIRMED_VOLUMETRIC_PRICES
        + OWNER_CONFIRMED_PROFILE_DEPTH_PRICES
        + OWNER_CONFIRMED_PSU_WATTAGE_PRICES
    )
)

ESTIMATED_PRELIMINARY_ACTIVATED_CODES = frozenset(
    r["code"] for r in ESTIMATED_PRELIMINARY_PRICES
)

PRELIMINARY_COSTING_ALIAS_CODES = frozenset({TEMPLATE_PROFILE_CODE, TEMPLATE_PSU_CODE})

OWNER_CONFIRMED_NOT_ACTIVATED: Dict[str, str] = {
    TEMPLATE_PROFILE_CODE: (
        "No single unit_cost — depth variants; quote_input.return_depth_mm required at pricing."
    ),
    TEMPLATE_PSU_CODE: (
        "No single unit_cost — wattage variants; quote_input.selected_psu_watts/psu_watts required."
    ),
}

PRELIMINARY_BLOCKERS_DOCUMENTED: Dict[str, str] = {
    "mounting_template_cnc_rate_basis": (
        "Șablon montaj CNC uses shared CNC_ROUTER hourly registry rate (perimeter_based_time); "
        "no owner-confirmed sablon-specific EUR/ml CNC rate — edit CNC_ROUTER in workcenter registry."
    ),
    "ready_for_quote_gates": (
        "Preliminary material + operation costing only; dossier/owner readiness gates unchanged."
    ),
}
