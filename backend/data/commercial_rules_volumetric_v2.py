"""Temporary local read-only commercial price rules for volumetric letters v2 (Step 7G).

NOT the official Pricing Registry (Step 7I). No workcenter_rates, no rate_per_hour,
no CostEngine totals, no invented RON prices except owner-documented exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Literal

from schemas.commercial_price_proposal import CommercialBasisType

PILOT_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"

Criticality = Literal["critical", "optional"]

# Commercial product ownership (F7F). TPL-VOLUMETRIC-LETTERS is letters-only; the ACM panel is a
# separate commercial product. Step 3 presents one subtotal per product plus one complete total.
CommercialProductKey = Literal["letters", "acm_panel"]
COMMERCIAL_PRODUCT_LABELS: dict[str, str] = {
    "letters": "Litere volumetrice",
    "acm_panel": "Panou ACM",
}


@dataclass(frozen=True)
class CommercialRuleDefinition:
    line_code: str
    label: str
    module_code: str
    component_code: str | None
    pricing_rule_code: str
    basis_type: CommercialBasisType
    quantity_paths: tuple[str, ...]
    unit: str
    source: str
    criticality: Criticality = "critical"
    owner_decision_required: bool = False
    owner_decision_code: str | None = None
    owner_decision_detail: str | None = None
    documented_unit_price: float | None = None
    documented_unit_price_currency: str | None = None
    # Mapping-only: existing Pricing Registry / workcenter_rates code (not a duplicate tariff).
    registry_pricing_code: str | None = None
    material_gate_path: str | None = None
    material_gate_value: str | None = None
    module_gate: str | None = None
    always_include: bool = False
    commercial_product_key: CommercialProductKey = "letters"
    warnings: tuple[str, ...] = field(default_factory=tuple)


# Owner-documented exception: hartie (paper) sablon montaj — 5 EUR/m² when selected.
SABLON_HARTIE_DOCUMENTED_EUR_M2 = 5.0

# F7H — native EUR commercial catalog for volumetric letters + ACM.
# Legacy Step 8 RON DEV_BRIDGE constants retired from the commercial path (not renamed to EUR).
# Rates below are OWNER_DOCUMENTED EUR registry sources, or unpublished (None) fail-closed.
# Final commercial level remains deferred to the dedicated final pricing pass.

# Owner-documented CNC face cut — seed_volumetric_workcenter_rates CNC_ROUTER (1.5 EUR/ml).
FACE_CNC_COMMERCIAL_EUR_ML = 1.5
FACE_CNC_REGISTRY_CODE = "CNC_ROUTER"
# Owner-documented return profile machine forming — RETURN_PROFILE_MACHINE_FORMING (5 EUR/ml).
# Bonding (RETURN_PROFILE_FACE_BONDING) remains a separate registry op, not fused here.
RETURN_PROFILE_COMMERCIAL_EUR_ML = 5.0
RETURN_PROFILE_REGISTRY_CODE = "RETURN_PROFILE_MACHINE_FORMING"
# Back cut commercial sell EUR/m² — NOT_FOUND in Owner EUR catalog (CNC registry is ml-based).
# Unpublished: fail-closed until Owner publishes a commercial EUR/m² (or ml) rate.
BACK_CNC_COMMERCIAL_EUR_M2: float | None = None
# LED module / PSU commercial sell EUR — NOT_FOUND as client sell rates.
# LED_ASSEMBLY 0.05 EUR is install labor, not module sell price — do not reuse as sell.
LED_MODULE_COMMERCIAL_EUR_BUC: float | None = None
PSU_COMMERCIAL_EUR_BUC: float | None = None

# Retained only for non-commercial / legacy finish flat line until separately retired.
DEV_BRIDGE_FINISH_RON_M2 = 35.0
DEV_BRIDGE_SABLON_FOREX_RON_M2 = 15.0

# Presentation currency for the volumetric letters + ACM commercial pilot (F7H).
# Scoped — does not change global app defaults or unrelated RON products.
VOLUMETRIC_PRESENTATION_CURRENCY = "EUR"
VOLUMETRIC_PRESENTATION_TEMPLATE_PREFIXES = (
    "TPL-VOLUMETRIC-LETTERS",
    "TPL-ACM-BOXED-MOUNTING",
)

# --- F7E G1 — return-cant Oracal wrap / RAL paint, face Oracal (Lead GO 2026-08-03) ---
# Face finish tokens handled by dedicated rules below — must not double-charge the flat
# finisaje_colantare_vopsire line (AGENT-B-F001 fix: "Fără finisaj" must not charge).
FACE_FINISH_NONE_VALUES = frozenset({"none", ""})
FACE_FINISH_ORACAL_TOKENS = frozenset({"oracal_641", "oracal_651", "oracal_8500"})

# --- F7F Owner commercial law activation (Owner decision 2026-08-03) ---
# Every rate below is a classified commercial_price_rule sourced from an explicit Owner
# decision. Tax-exclusive. No EUR->RON conversion is performed here and none is implied.
OWNER_COMMERCIAL_LAW_SOURCE = "owner_commercial_decision:f7f_2026_08_03"

# Face print + laminate — Owner F7F: 10 EUR/m2 tax-exclusive.
FACE_PRINT_LAMINATE_EUR_M2 = 10.0
# Canonical + documented-alias tokens the Owner print+laminate rate covers.
FACE_FINISH_PRINT_LAMINATE_TOKENS = frozenset({"print_laminate", "printed_laminated_vinyl"})
# Commercially relevant face selections with no owner-priced CPP rule — fail closed
# (COMMERCIAL_RULE_MISSING). Never silently priced at the flat finisaje_colantare_vopsire rate.
# "printed_vinyl" (print without laminate) is deliberately NOT covered by the Owner
# print+laminate rate — a separate Owner decision is required for unlaminated print.
FACE_FINISH_UNPRICED_COMMERCIAL_TOKENS = frozenset({"printed_vinyl"})

# Vinyl material rates, EUR/m2, tax-exclusive. Series-level: same series, same rate for every
# colour code (Owner F7F: "all colors same series same rate; no color-tier"). The same series
# rate applies to face and to return-cant wrap — it is one material.
# Owner F7F set Oracal 651 = 5 EUR/m2 (supersedes the F7E seed-derived 9.0).
ORACAL_651_MATERIAL_EUR_M2 = 5.0
# Oracal 641 was NOT part of the Owner F7F rate list. The F7E value derived from the
# seed_volumetric_owner_confirmed_prices.py MAT-ORACAL-641 purchase row is retained unchanged;
# it is reported to the Owner as an open commercial decision, not re-derived here.
ORACAL_641_MATERIAL_EUR_M2 = 6.5
# Oracal 8500 is priced by SKU + CONFIRMED roll width (Owner F7F). Never guess a width and
# never fall back to the cheaper or the more expensive tier — fail closed instead.
ORACAL_8500_MATERIAL_EUR_M2_BY_ROLL_WIDTH_MM: dict[int, float] = {
    1000: 17.0,
    1260: 13.5,
}
# Kept as the canonical accepted-width set so the blocker message can name the real options.
ORACAL_8500_SUPPORTED_ROLL_WIDTH_MM = tuple(sorted(ORACAL_8500_MATERIAL_EUR_M2_BY_ROLL_WIDTH_MM))

# Backwards-compatible aliases (face-scoped names used by the F7E rule rows).
FACE_ORACAL_641_EUR_M2 = ORACAL_641_MATERIAL_EUR_M2
FACE_ORACAL_651_EUR_M2 = ORACAL_651_MATERIAL_EUR_M2

# Vinyl application labour — Owner F7F: 3 EUR/m2, charged ONCE on the actual applied surface.
# Not on waste, not on stock cant, not when no vinyl is selected, never duplicated for the same
# token. Face and cant may carry separate application lines only because they are distinct
# proven surfaces (face area vs developed wrap area).
VINYL_APPLICATION_EUR_M2 = 3.0

# ACM sheet commercial material — Owner F7F, EUR/m2 tax-exclusive.
# "oglinda" is a REPLACEMENT rate (40), never 15 + a 25 surcharge, and never both.
ACM_SHEET_VARIANT_STANDARD = "standard"
ACM_SHEET_VARIANT_COLORAT = "colorat"
ACM_SHEET_MIRROR_VARIANTS = frozenset({"oglinda_gold", "oglinda_antracit"})
ACM_SHEET_MATERIAL_EUR_M2_BY_VARIANT: dict[str, float] = {
    ACM_SHEET_VARIANT_STANDARD: 15.0,
    ACM_SHEET_VARIANT_COLORAT: 15.0,
    "oglinda_gold": 40.0,
    "oglinda_antracit": 40.0,
}
# Absent variant = not yet captured by the operator. The owner-confirmed default sheet for this
# template is the standard 3 mm bond (MAT-ACM-BOND-3MM @ 15 EUR/m2), so an absent variant keeps
# the standard rate. An UNKNOWN token is a different thing and fails closed.
ACM_SHEET_VARIANT_WHEN_ABSENT = ACM_SHEET_VARIANT_STANDARD
# Mirror gold / anthracite are interior by default. Exterior needs a proven supplier SKU.
ACM_SHEET_ENVIRONMENT_INTERIOR = "interior"
ACM_SHEET_ENVIRONMENT_EXTERIOR = "exterior"

# Return-cant Oracal wrap material, resolved by series (same seed rows as face; cant wrap does
# not offer 8500). Canonical intake tokens per canonicalFinishEnumMap.ts cant_oracal_wrap
# ("oracal_wrapped", "oracal_651", "vinyl") plus the 641 aliases already recognized by
# services/return_cant_product_truth_bridge.py (VINYL_FINISH_TO_SERIES) to reach MAT-ORACAL-641.
CANT_ORACAL_WRAP_SERIES_BY_RETURN_FINISH_TYPE: dict[str, str] = {
    "oracal_wrapped": "651",
    "oracal_651": "651",
    "651": "651",
    "vinyl": "651",
    "oracal_641": "641",
    "641": "641",
}
CANT_ORACAL_MATERIAL_EUR_M2_BY_SERIES: dict[str, float] = {
    "641": ORACAL_641_MATERIAL_EUR_M2,
    "651": ORACAL_651_MATERIAL_EUR_M2,
}

# Return-cant RAL paint material, depth-tiered EUR/ml (seed_volumetric_owner_confirmed_prices.py
# MAT-VOPSEA-RAL-CANT-*MM). Canonical intake tokens per canonicalFinishEnumMap.ts cant_ral_paint.
CANT_RAL_PAINT_GATE_VALUES = frozenset({"ral_paint", "painted", "paint"})
CANT_RAL_PAINT_MATERIAL_EUR_ML_BY_DEPTH_MM: dict[int, float] = {
    30: 2.0,
    60: 2.5,
    80: 3.0,
    100: 4.0,
}
# RAL commercial minimum — Owner historically documented "100 lei pe culoare RAL"
# (LEGACY_RON in canonicalFinishEnumMap cant_ral_minimum_policy). F7H retires the RON
# numeric floor from CPP (cross-currency mix was a defect). EUR minimum is configurable
# and unpublished until Owner publishes an EUR floor in the final pricing pass.
# When None: no top-up is invented; material+labor stay native EUR.
CANT_RAL_PAINT_MINIMUM_EUR_PER_COLOR: float | None = None
# Legacy constant retained for docs/history references only — never used in F7H CPP math.
CANT_RAL_PAINT_MINIMUM_RON_PER_COLOR = 100.0
RAL_MINIMUM_TOP_UP_LINE_CODE = "finisaje_cant_ral_minimum_top_up"
RAL_MINIMUM_TOP_UP_RULE_CODE = "VOL_V2_CANT_RAL_MINIMUM_TOP_UP_EUR"

VOLUMETRIC_V2_COMMERCIAL_RULES: tuple[CommercialRuleDefinition, ...] = (
    CommercialRuleDefinition(
        line_code="debitare_fata",
        label="Debitare față litere",
        module_code="debitare_fata",
        component_code="comp_face_litere",
        pricing_rule_code="VOL_V2_FACE_CNC_ML",
        basis_type="ml",
        quantity_paths=("quote_geometry.letter_perimeter_m", "letter_perimeter_m"),
        unit="ml",
        source="owner_commercial_decision:f7h_cnc_router_eur_ml",
        criticality="critical",
        documented_unit_price=FACE_CNC_COMMERCIAL_EUR_ML,
        documented_unit_price_currency="EUR",
        registry_pricing_code=FACE_CNC_REGISTRY_CODE,
        warnings=(
            "F7H: commercial EUR/ml from Owner-documented CNC_ROUTER registry rate (1.5 EUR/ml). "
            "Legacy RON DEV_BRIDGE 25 was retired, not renamed.",
        ),
    ),
    CommercialRuleDefinition(
        line_code="modelare_cant_aluminiu",
        label="Modelare cant aluminiu",
        module_code="modelare_cant",
        component_code="comp_lateral_litere",
        pricing_rule_code="VOL_V2_RETURN_PROFILE_ML",
        basis_type="ml",
        quantity_paths=("quote_geometry.letter_perimeter_m", "letter_perimeter_m"),
        unit="ml",
        source="owner_commercial_decision:f7h_return_profile_forming_eur_ml",
        criticality="critical",
        documented_unit_price=RETURN_PROFILE_COMMERCIAL_EUR_ML,
        documented_unit_price_currency="EUR",
        registry_pricing_code=RETURN_PROFILE_REGISTRY_CODE,
        warnings=(
            "Technical inputs: letter_perimeter_m, return_depth_mm — not minutes.",
            "F7H: commercial EUR/ml from Owner-documented RETURN_PROFILE_MACHINE_FORMING (5 EUR/ml). "
            "Legacy RON DEV_BRIDGE 30 was retired, not renamed. Bonding stays a separate op.",
        ),
    ),
    CommercialRuleDefinition(
        line_code="debitare_spate",
        label="Debitare spate litere",
        module_code="debitare_spate",
        component_code="comp_spate_litere",
        pricing_rule_code="VOL_V2_BACK_CNC_M2_DEV_BRIDGE",
        basis_type="m2",
        quantity_paths=("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
        unit="m2",
        source="commercial_rules_volumetric_v2:back_m2_unpublished_eur",
        criticality="critical",
        documented_unit_price=BACK_CNC_COMMERCIAL_EUR_M2,
        documented_unit_price_currency="EUR",
        owner_decision_required=True,
        owner_decision_code="DEBITARE_SPATE_COMMERCIAL_EUR_M2",
        owner_decision_detail=(
            "F7H: no Owner-documented commercial EUR/m² sell rate for back CNC was found "
            "(CNC_ROUTER is EUR/ml). Basis stays m². Configure EUR/m² at commercial registry "
            "before this line can price. Fail-closed — no invented rate, no RON rename."
        ),
        warnings=(
            "F7H unpublished commercial EUR/m² — fail-closed until Owner publishes the rate. "
            "m² basis preserved (not changed to ml for uniformity).",
        ),
    ),
    CommercialRuleDefinition(
        line_code="sistem_led_module",
        label="Sistem LED — module",
        module_code="sistem_led",
        component_code="comp_led_litere",
        pricing_rule_code="VOL_V2_LED_MODULE_PIECE",
        basis_type="piece",
        # Prefer letter-only count so linked-logo LED is not double-counted under letters.
        quantity_paths=(
            "finish_setup.letter_led_module_count",
            "letter_led_module_count",
            "finish_setup.led_module_count",
            "led_module_count",
        ),
        unit="buc",
        source="commercial_rules_volumetric_v2:letter_led_module_unpublished_eur",
        criticality="critical",
        module_gate="sistem_led",
        documented_unit_price=LED_MODULE_COMMERCIAL_EUR_BUC,
        documented_unit_price_currency="EUR",
        owner_decision_required=True,
        owner_decision_code="LED_MODULE_COMMERCIAL_EUR_BUC",
        owner_decision_detail=(
            "F7H: no Owner-documented commercial EUR/buc sell rate for LED modules was found. "
            "LED_ASSEMBLY 0.05 EUR is install labor, not module sell price. Fail-closed."
        ),
    ),
    CommercialRuleDefinition(
        line_code="sursa_led",
        label="Sursă LED (PSU)",
        module_code="sistem_led",
        component_code="comp_led_litere",
        pricing_rule_code="VOL_V2_LED_PSU_PIECE",
        basis_type="piece",
        quantity_paths=(),
        unit="buc",
        source="commercial_rules_volumetric_v2:psu_unpublished_eur",
        criticality="critical",
        module_gate="sistem_led",
        documented_unit_price=PSU_COMMERCIAL_EUR_BUC,
        documented_unit_price_currency="EUR",
        owner_decision_required=True,
        owner_decision_code="PSU_COMMERCIAL_EUR_BUC",
        owner_decision_detail=(
            "F7H: no Owner-documented commercial EUR/buc sell rate for PSU was found. "
            "Fail-closed until published in commercial registry. "
            "Commercial sells one PSU unit; selected_psu_watts is reference only."
        ),
        warnings=("Commercial sells one PSU unit; selected_psu_watts is reference only.",),
    ),
    CommercialRuleDefinition(
        line_code="finisaje_colantare_vopsire",
        label="Finisaje — colantare / vopsire",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_FINISH_M2_OR_MINIMUM",
        basis_type="m2",
        quantity_paths=("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
        unit="m2",
        source="commercial_rules_volumetric_v2:finish_area_m2",
        criticality="critical",
        documented_unit_price=DEV_BRIDGE_FINISH_RON_M2,
        documented_unit_price_currency="RON",
        warnings=("Unconfirmed finish groups may require owner review before numeric pricing.",),
    ),
    CommercialRuleDefinition(
        line_code="finisaje_cant_oracal_material",
        label="Finisaje — autocolant Oracal cant (material)",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_CANT_ORACAL_MATERIAL_M2",
        basis_type="m2",
        quantity_paths=(),
        unit="m2",
        source="commercial_rules_volumetric_v2:cant_oracal_wrap_material",
        criticality="critical",
        module_gate="finisaje",
        warnings=(
            "Quantity = letter_perimeter_m x return_depth_mm (developed wrap area, m2). "
            "Series (641/651) resolved from finish_setup.return_finish_type; same series/color "
            "stays one commercial line.",
        ),
    ),
    CommercialRuleDefinition(
        line_code="finisaje_cant_oracal_labor",
        label="Finisaje — aplicare autocolant cant",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_CANT_VINYL_APPLICATION_M2",
        basis_type="m2",
        quantity_paths=(),
        unit="m2",
        source=f"{OWNER_COMMERCIAL_LAW_SOURCE}:vinyl_application",
        criticality="critical",
        module_gate="finisaje",
        documented_unit_price=VINYL_APPLICATION_EUR_M2,
        documented_unit_price_currency="EUR",
        warnings=(
            "Owner F7F: aplicare autocolant 3 EUR/mp pe suprafata efectiv aplicata. "
            "Cantul este o suprafata distincta de fata (arie desfasurata perimetru x adancime).",
        ),
    ),
    CommercialRuleDefinition(
        line_code="finisaje_cant_ral_material",
        label="Finisaje — vopsit RAL cant (material)",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_CANT_RAL_MATERIAL_ML",
        basis_type="ml",
        quantity_paths=("quote_geometry.letter_perimeter_m", "letter_perimeter_m"),
        unit="ml",
        source="commercial_rules_volumetric_v2:cant_ral_paint_material",
        criticality="critical",
        module_gate="finisaje",
        warnings=(
            "F7H: RAL material is EUR. Commercial minimum/top-up is EUR-only when "
            "CANT_RAL_PAINT_MINIMUM_EUR_PER_COLOR is published; legacy 100 RON/color is not "
            "converted or applied as EUR.",
        ),
    ),
    CommercialRuleDefinition(
        line_code="finisaje_cant_ral_labor",
        label="Finisaje — vopsit RAL cant (manoperă)",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_CANT_RAL_LABOR_ML",
        basis_type="ml",
        quantity_paths=("quote_geometry.letter_perimeter_m", "letter_perimeter_m"),
        unit="ml",
        source="commercial_rules_volumetric_v2:cant_ral_paint_labor",
        criticality="critical",
        module_gate="finisaje",
        registry_pricing_code="RETURN_CANT_RAL_PAINT_LABOR",
    ),
    CommercialRuleDefinition(
        line_code="finisaje_oracal_641_material",
        label="Finisaje — Oracal 641 față (material)",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_FACE_ORACAL_641_MATERIAL_M2",
        basis_type="m2",
        quantity_paths=("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
        unit="m2",
        source="commercial_rules_volumetric_v2:face_oracal_641_material",
        criticality="critical",
        documented_unit_price=FACE_ORACAL_641_EUR_M2,
        documented_unit_price_currency="EUR",
        material_gate_path="finish_setup.face_finish_type",
        material_gate_value="oracal_641",
        module_gate="finisaje",
    ),
    CommercialRuleDefinition(
        line_code="finisaje_oracal_651_material",
        label="Finisaje — Oracal 651 față (material)",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_FACE_ORACAL_651_MATERIAL_M2",
        basis_type="m2",
        quantity_paths=("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
        unit="m2",
        source="commercial_rules_volumetric_v2:face_oracal_651_material",
        criticality="critical",
        documented_unit_price=FACE_ORACAL_651_EUR_M2,
        documented_unit_price_currency="EUR",
        material_gate_path="finish_setup.face_finish_type",
        material_gate_value="oracal_651",
        module_gate="finisaje",
    ),
    CommercialRuleDefinition(
        line_code="finisaje_oracal_8500_material",
        label="Finisaje — Oracal 8500 față (material)",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_FACE_ORACAL_8500_MATERIAL_M2",
        basis_type="m2",
        quantity_paths=("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
        unit="m2",
        source=f"{OWNER_COMMERCIAL_LAW_SOURCE}:face_oracal_8500_material_by_roll_width",
        criticality="critical",
        # Resolved at build time from the confirmed roll width (1000 -> 17, 1260 -> 13.5).
        # Never defaulted: an unconfirmed width blocks with COMMERCIAL_CONFIGURATION_INCOMPLETE.
        documented_unit_price=None,
        documented_unit_price_currency="EUR",
        material_gate_path="finish_setup.face_finish_type",
        material_gate_value="oracal_8500",
        module_gate="finisaje",
        warnings=(
            "Owner F7F: tarif pe SKU + latime rola confirmata "
            f"({'/'.join(str(w) for w in ORACAL_8500_SUPPORTED_ROLL_WIDTH_MM)} mm). "
            "Fara latime confirmata nu se estimeaza niciun pret.",
        ),
    ),
    CommercialRuleDefinition(
        line_code="finisaje_print_laminate_material",
        label="Finisaje — print + laminare față (material)",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_FACE_PRINT_LAMINATE_MATERIAL_M2",
        basis_type="m2",
        quantity_paths=("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
        unit="m2",
        source=f"{OWNER_COMMERCIAL_LAW_SOURCE}:face_print_laminate_material",
        criticality="critical",
        documented_unit_price=FACE_PRINT_LAMINATE_EUR_M2,
        documented_unit_price_currency="EUR",
        module_gate="finisaje",
        warnings=("Owner F7F: print + laminare 10 EUR/mp, fara TVA.",),
    ),
    CommercialRuleDefinition(
        line_code="finisaje_aplicare_autocolant_fata",
        label="Finisaje — aplicare autocolant față",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_FACE_VINYL_APPLICATION_M2",
        basis_type="m2",
        quantity_paths=("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
        unit="m2",
        source=f"{OWNER_COMMERCIAL_LAW_SOURCE}:vinyl_application",
        criticality="critical",
        documented_unit_price=VINYL_APPLICATION_EUR_M2,
        documented_unit_price_currency="EUR",
        module_gate="finisaje",
        warnings=(
            "Owner F7F: aplicare autocolant 3 EUR/mp, o singura data pe suprafata fetei. "
            "Nu se aplica pe deseu, pe cant stoc sau cand nu exista folie.",
        ),
    ),
    CommercialRuleDefinition(
        line_code="sablon_montaj",
        label="Șablon montaj",
        module_code="sablon_montaj",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_SABLON_M2",
        basis_type="m2",
        quantity_paths=("finish_setup.mounting_template_area_m2", "mounting_template_area_m2"),
        unit="m2",
        source="commercial_rules_volumetric_v2:sablon_m2",
        criticality="critical",
        module_gate="sablon_montaj",
    ),
    CommercialRuleDefinition(
        line_code="sablon_montaj_hartie",
        label="Șablon montaj — hârtie (documentat)",
        module_code="sablon_montaj",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_SABLON_HARTIE_EUR_M2",
        basis_type="m2",
        quantity_paths=("finish_setup.mounting_template_area_m2", "mounting_template_area_m2"),
        unit="m2",
        source="commercial_rules_volumetric_v2:sablon_hartie_documented",
        criticality="critical",
        documented_unit_price=SABLON_HARTIE_DOCUMENTED_EUR_M2,
        documented_unit_price_currency="EUR",
        material_gate_path="finish_setup.mounting_template_material_type",
        material_gate_value="paper",
        module_gate="sablon_montaj",
    ),
    CommercialRuleDefinition(
        line_code="sablon_montaj_forex",
        label="Șablon montaj — Forex",
        module_code="sablon_montaj",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_SABLON_FOREX_DEV_BRIDGE",
        basis_type="m2",
        quantity_paths=("finish_setup.mounting_template_area_m2", "mounting_template_area_m2"),
        unit="m2",
        source="commercial_rules_volumetric_v2:sablon_forex_dev_bridge",
        criticality="critical",
        documented_unit_price=DEV_BRIDGE_SABLON_FOREX_RON_M2,
        documented_unit_price_currency="RON",
        material_gate_path="finish_setup.mounting_template_material_type",
        material_gate_value="forex",
        module_gate="sablon_montaj",
        warnings=("Step 8 dev bridge: interim Forex sablon price until owner approves in 7I.",),
    ),
    CommercialRuleDefinition(
        line_code="ambalare",
        label="Ambalare",
        module_code="ambalare_livrare_montaj",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_PACKAGING_PENDING",
        basis_type="fixed",
        quantity_paths=(),
        unit="set",
        source="commercial_rules_volumetric_v2:packaging_rule_pending",
        criticality="optional",
        owner_decision_required=True,
        owner_decision_code="AMBALARE_COMMERCIAL_RULE",
        owner_decision_detail="Commercial packaging rule (fixed/set) not yet owner-defined.",
        module_gate="ambalare_livrare_montaj",
    ),
    CommercialRuleDefinition(
        line_code="montaj",
        label="Montaj șantier",
        module_code="structura_suport",
        component_code=None,
        pricing_rule_code="VOL_V2_SITE_INSTALLATION_STANDARD",
        basis_type="fixed",
        quantity_paths=(),
        unit="locatie",
        source="commercial_rules_volumetric_v2:site_installation_standard",
        criticality="optional",
        owner_decision_required=True,
        owner_decision_code="MONTAJ_COMMERCIAL_RULE",
        owner_decision_detail=(
            "Site installation was selected but SITE_INSTALLATION_STANDARD is missing or unusable "
            "in Pricing Registry. Configure 200 EUR fixed per locatie/job at /inventory/pricing. "
            "Travel outside Bucharest is not included and must be priced separately later. "
            "Confirmare remains disabled. Do not use internal labor minutes or hourly rates."
        ),
        registry_pricing_code="SITE_INSTALLATION_STANDARD",
        always_include=False,
    ),
)

# Owner-confirmed commercial tariff: standard site installation (M1 Bucharest base / M2 same base).
# Fixed once per job/location — not per letter, not per logo. Travel outside Bucharest is out of scope.
SITE_INSTALLATION_STANDARD_CODE = "SITE_INSTALLATION_STANDARD"
SITE_INSTALLATION_STANDARD_EUR = 200.0

# Owner-confirmed ACM boxed mounting commercial lines (structura_suport) — EUR/lm and EUR/mp.
ACM_BOXED_PANEL_CUT_EUR_LM = 1.5
ACM_BOXED_V_GROOVE_EUR_LM = 3.0
ACM_BOXED_ASSEMBLY_EUR_M2 = 15.0
ACM_BOXED_ASSEMBLY_MIN_EUR = 20.0
ACM_BOXED_MAT_ACM_EUR_M2 = 15.0
ACM_BOXED_SURUBURI_EUR_SET = 5.0

ACM_STRUCTURA_COMMERCIAL_RULES: tuple[CommercialRuleDefinition, ...] = (
    CommercialRuleDefinition(
        line_code="acm_panel_cut",
        label="Debitare panou ACM",
        module_code="structura_suport",
        component_code="comp_acm_panel_face",
        pricing_rule_code="ACM_BOXED_PANEL_CUT_LM",
        basis_type="ml",
        quantity_paths=("panel_perimeter_m",),
        unit="ml",
        source="commercial_rules_volumetric_v2:acm_panel_cut_owner_eur_lm",
        documented_unit_price=ACM_BOXED_PANEL_CUT_EUR_LM,
        documented_unit_price_currency="EUR",
        module_gate="structura_suport",
    ),
    CommercialRuleDefinition(
        line_code="acm_v_groove",
        label="Frezare V-groove ACM",
        module_code="structura_suport",
        component_code="comp_casetted_returns",
        pricing_rule_code="ACM_BOXED_V_GROOVE_LM",
        basis_type="ml",
        quantity_paths=("fold_length_m",),
        unit="ml",
        source="commercial_rules_volumetric_v2:acm_v_groove_owner_eur_lm",
        documented_unit_price=ACM_BOXED_V_GROOVE_EUR_LM,
        documented_unit_price_currency="EUR",
        module_gate="structura_suport",
    ),
    CommercialRuleDefinition(
        line_code="acm_panel_face_material",
        label="Material ACM față panou",
        module_code="structura_suport",
        component_code="comp_acm_panel_face",
        pricing_rule_code="ACM_BOXED_MAT_FACE_M2",
        basis_type="m2",
        quantity_paths=("panel_area_m2",),
        unit="m2",
        source="commercial_rules_volumetric_v2:acm_mat_face_owner_eur_m2",
        documented_unit_price=ACM_BOXED_MAT_ACM_EUR_M2,
        documented_unit_price_currency="EUR",
        module_gate="structura_suport",
    ),
    CommercialRuleDefinition(
        line_code="acm_return_strip_material",
        label="Material ACM canturi / întoarceri",
        module_code="structura_suport",
        component_code="comp_casetted_returns",
        pricing_rule_code="ACM_BOXED_MAT_RETURN_M2",
        basis_type="m2",
        quantity_paths=("return_strip_area_m2",),
        unit="m2",
        source="commercial_rules_volumetric_v2:acm_mat_return_owner_eur_m2",
        documented_unit_price=ACM_BOXED_MAT_ACM_EUR_M2,
        documented_unit_price_currency="EUR",
        module_gate="structura_suport",
    ),
    CommercialRuleDefinition(
        line_code="acm_boxed_assembly",
        label="Asamblare suport ACM casetat",
        module_code="structura_suport",
        component_code="comp_mounting_fasteners",
        pricing_rule_code="ACM_BOXED_ASSEMBLY_M2_MIN",
        basis_type="m2",
        quantity_paths=("panel_area_m2",),
        unit="m2",
        source="commercial_rules_volumetric_v2:acm_assembly_owner_eur_m2_min",
        documented_unit_price=ACM_BOXED_ASSEMBLY_EUR_M2,
        documented_unit_price_currency="EUR",
        module_gate="structura_suport",
        warnings=(
            f"Minimum commercial charge {ACM_BOXED_ASSEMBLY_MIN_EUR} EUR/product when area × rate is lower.",
        ),
    ),
    CommercialRuleDefinition(
        line_code="acm_fasteners",
        label="Suruburi / prinderi standard ACM",
        module_code="structura_suport",
        component_code="comp_mounting_fasteners",
        pricing_rule_code="ACM_BOXED_SURUBURI_SET",
        basis_type="set",
        quantity_paths=(),
        unit="set",
        source="commercial_rules_volumetric_v2:acm_suruburi_owner_eur_set",
        documented_unit_price=ACM_BOXED_SURUBURI_EUR_SET,
        documented_unit_price_currency="EUR",
        module_gate="structura_suport",
    ),
)

# Letters↔ACM composition connection — owner sheet (mirror FE lettersAcmCompositionConnectionPrices).
LETTERS_ACM_SABLON_PROCESS_EUR_M2 = 20.0
LETTERS_ACM_FASTEN_FOREX_EUR_M2 = 8.0
LETTERS_ACM_ELECTRIC_PSU_EUR_BUC = 35.0
LETTERS_ACM_CABLE_5M_EUR_BUC = 6.0
LETTERS_ACM_LIGHT_TEST_EUR_BUC = 8.0
LETTERS_ACM_ATTACH_BODY_EUR_M2 = 12.0
LETTERS_ACM_PACK_EUR_M2 = 10.0
LETTERS_ACM_PACK_MIN_EUR = 15.0

LETTERS_ACM_COMPOSITION_CONNECTION_RULES: tuple[CommercialRuleDefinition, ...] = (
    CommercialRuleDefinition(
        line_code="letters_acm_conn_sablon_process",
        label="Proces șablon pe Alucobond (material+cutter+transfer+aplicare)",
        module_code="sablon_montaj",
        component_code="comp_finisaj_litere",
        pricing_rule_code="LETTERS_ACM_SABLON_PROCESS_M2",
        basis_type="m2",
        quantity_paths=("letters_layer_outbox_m2", "finish_setup.letters_layer_outbox_m2"),
        unit="m2",
        source="commercial_rules_volumetric_v2:letters_acm_sablon_20_eur_m2",
        documented_unit_price=LETTERS_ACM_SABLON_PROCESS_EUR_M2,
        documented_unit_price_currency="EUR",
        always_include=True,
        warnings=(
            "Owner-locked 20 EUR/mp on letters-layer outbox integral. "
            "Suppresses legacy sablon_montaj_* split under ACM composition.",
        ),
    ),
    CommercialRuleDefinition(
        line_code="letters_acm_conn_fasten_forex",
        label="Prindere Forex pe bond (autoforante)",
        module_code="structura_suport",
        component_code=None,
        pricing_rule_code="LETTERS_ACM_FASTEN_FOREX_M2",
        basis_type="m2",
        quantity_paths=("letters_layer_outbox_m2",),
        unit="m2",
        source="commercial_rules_volumetric_v2:letters_acm_fasten_forex",
        documented_unit_price=LETTERS_ACM_FASTEN_FOREX_EUR_M2,
        documented_unit_price_currency="EUR",
        always_include=True,
        criticality="optional",
    ),
    CommercialRuleDefinition(
        line_code="letters_acm_conn_electric_psu",
        label="Electrică în carcasa bond + legare transformator",
        module_code="structura_suport",
        component_code=None,
        pricing_rule_code="LETTERS_ACM_ELECTRIC_PSU_BUC",
        basis_type="piece",
        quantity_paths=(),
        unit="buc",
        source="commercial_rules_volumetric_v2:letters_acm_electric_psu",
        documented_unit_price=LETTERS_ACM_ELECTRIC_PSU_EUR_BUC,
        documented_unit_price_currency="EUR",
        always_include=True,
        criticality="optional",
    ),
    CommercialRuleDefinition(
        line_code="letters_acm_conn_cable_5m",
        label="Cablu alimentare 5 m 220V (2×1.5) + atasare",
        module_code="structura_suport",
        component_code=None,
        pricing_rule_code="LETTERS_ACM_CABLE_5M_BUC",
        basis_type="piece",
        quantity_paths=(),
        unit="buc",
        source="commercial_rules_volumetric_v2:letters_acm_cable_5m",
        documented_unit_price=LETTERS_ACM_CABLE_5M_EUR_BUC,
        documented_unit_price_currency="EUR",
        always_include=True,
        criticality="optional",
    ),
    CommercialRuleDefinition(
        line_code="letters_acm_conn_light_test",
        label="Test lumină",
        module_code="structura_suport",
        component_code=None,
        pricing_rule_code="LETTERS_ACM_LIGHT_TEST_BUC",
        basis_type="piece",
        quantity_paths=(),
        unit="buc",
        source="commercial_rules_volumetric_v2:letters_acm_light_test",
        documented_unit_price=LETTERS_ACM_LIGHT_TEST_EUR_BUC,
        documented_unit_price_currency="EUR",
        always_include=True,
        criticality="optional",
    ),
    CommercialRuleDefinition(
        line_code="letters_acm_conn_attach_body",
        label="Prindere corp pe Forex (autoforante fine vopsite)",
        module_code="structura_suport",
        component_code=None,
        pricing_rule_code="LETTERS_ACM_ATTACH_BODY_M2",
        basis_type="m2",
        quantity_paths=("letters_layer_outbox_m2",),
        unit="m2",
        source="commercial_rules_volumetric_v2:letters_acm_attach_body",
        documented_unit_price=LETTERS_ACM_ATTACH_BODY_EUR_M2,
        documented_unit_price_currency="EUR",
        always_include=True,
        criticality="optional",
    ),
    CommercialRuleDefinition(
        line_code="letters_acm_conn_pack",
        label="Impachetare ansamblu Litere + Alucobond",
        module_code="ambalare_livrare_montaj",
        component_code=None,
        pricing_rule_code="LETTERS_ACM_PACK_M2_MIN",
        basis_type="m2",
        quantity_paths=("letters_layer_outbox_m2",),
        unit="m2",
        source="commercial_rules_volumetric_v2:letters_acm_pack_min",
        documented_unit_price=LETTERS_ACM_PACK_EUR_M2,
        documented_unit_price_currency="EUR",
        always_include=True,
        criticality="optional",
        warnings=(
            f"Minimum commercial charge {LETTERS_ACM_PACK_MIN_EUR} EUR when area × rate is lower.",
        ),
    ),
)

def _own_commercial_product(
    rules: tuple[CommercialRuleDefinition, ...],
    product_key: CommercialProductKey,
) -> tuple[CommercialRuleDefinition, ...]:
    """Assign commercial product ownership to a whole rule family (F7F product separation)."""
    return tuple(replace(rule, commercial_product_key=product_key) for rule in rules)


# The ACM structura rows and the Litere<->ACM connection sheet are all work on the bond panel
# body, so they belong to the "Panou ACM" commercial product, not to the letters product.
ACM_STRUCTURA_COMMERCIAL_RULES = _own_commercial_product(ACM_STRUCTURA_COMMERCIAL_RULES, "acm_panel")
LETTERS_ACM_COMPOSITION_CONNECTION_RULES = _own_commercial_product(
    LETTERS_ACM_COMPOSITION_CONNECTION_RULES, "acm_panel"
)

VOLUMETRIC_V2_COMMERCIAL_RULES_WITH_ACM: tuple[CommercialRuleDefinition, ...] = (
    *VOLUMETRIC_V2_COMMERCIAL_RULES,
    *ACM_STRUCTURA_COMMERCIAL_RULES,
    *LETTERS_ACM_COMPOSITION_CONNECTION_RULES,
)

# Linked-child logo commercial rule *templates* (expanded per segment in CPP).
# Body construction reuses the same F7H EUR commercial classes as letters (not EIC).
# Print / laminate / application stay fail-closed until owner configures commercial tariffs.
LOGO_LINKED_CHILD_COMMERCIAL_RULE_TEMPLATES: tuple[CommercialRuleDefinition, ...] = (
    CommercialRuleDefinition(
        line_code="logo_face_cnc",
        label="Debitare față logo volumetric",
        module_code="debitare_fata",
        component_code="comp_logo_face",
        pricing_rule_code="VOL_V2_LOGO_FACE_CNC_ML",
        basis_type="ml",
        quantity_paths=(),
        unit="ml",
        source="owner_commercial_decision:f7h_cnc_router_eur_ml",
        criticality="critical",
        documented_unit_price=FACE_CNC_COMMERCIAL_EUR_ML,
        documented_unit_price_currency="EUR",
        registry_pricing_code=FACE_CNC_REGISTRY_CODE,
    ),
    CommercialRuleDefinition(
        line_code="logo_return_cant",
        label="Modelare cant / volum logo",
        module_code="modelare_cant",
        component_code="comp_logo_return",
        pricing_rule_code="VOL_V2_LOGO_RETURN_PROFILE_ML",
        basis_type="ml",
        quantity_paths=(),
        unit="ml",
        source="owner_commercial_decision:f7h_return_profile_forming_eur_ml",
        criticality="critical",
        documented_unit_price=RETURN_PROFILE_COMMERCIAL_EUR_ML,
        documented_unit_price_currency="EUR",
        registry_pricing_code=RETURN_PROFILE_REGISTRY_CODE,
    ),
    CommercialRuleDefinition(
        line_code="logo_back_cnc",
        label="Debitare spate logo (Forex/PVC individual)",
        module_code="debitare_spate",
        component_code="comp_logo_back",
        pricing_rule_code="VOL_V2_LOGO_BACK_CNC_M2_DEV_BRIDGE",
        basis_type="m2",
        quantity_paths=(),
        unit="m2",
        source="commercial_rules_volumetric_v2:logo_back_m2_unpublished_eur",
        criticality="critical",
        documented_unit_price=BACK_CNC_COMMERCIAL_EUR_M2,
        documented_unit_price_currency="EUR",
        owner_decision_required=True,
        owner_decision_code="DEBITARE_SPATE_COMMERCIAL_EUR_M2",
        owner_decision_detail=(
            "F7H: logo back CNC commercial EUR/m² unpublished — same Owner gap as letters."
        ),
    ),
    CommercialRuleDefinition(
        line_code="logo_print",
        label="Print față logo",
        module_code="finisaje",
        component_code="comp_logo_finish",
        pricing_rule_code="VOL_V2_LOGO_PRINT_M2",
        basis_type="m2",
        quantity_paths=(),
        unit="m2",
        source="commercial_rules_volumetric_v2:logo_print_maps_LARGE_FORMAT_PRINT",
        criticality="critical",
        owner_decision_required=False,
        owner_decision_code="LOGO_PRINT_COMMERCIAL_RULE",
        owner_decision_detail=(
            "Logo print maps to existing registry LARGE_FORMAT_PRINT; "
            "fail-closed if registry row inactive/missing or EUR→RON conversion unavailable."
        ),
        documented_unit_price=None,
        registry_pricing_code="LARGE_FORMAT_PRINT",
    ),
    CommercialRuleDefinition(
        line_code="logo_laminate",
        label="Laminare față logo",
        module_code="finisaje",
        component_code="comp_logo_finish",
        pricing_rule_code="VOL_V2_LOGO_LAMINATE_M2",
        basis_type="m2",
        quantity_paths=(),
        unit="m2",
        source="commercial_rules_volumetric_v2:logo_laminate_maps_LAMINATION",
        criticality="critical",
        owner_decision_required=False,
        owner_decision_code="LOGO_LAMINATE_COMMERCIAL_RULE",
        owner_decision_detail=(
            "Logo laminate maps to existing registry LAMINATION "
            "(not SVC-LAMINATION-SERVICE stub); fail-closed if unavailable."
        ),
        documented_unit_price=None,
        registry_pricing_code="LAMINATION",
    ),
    CommercialRuleDefinition(
        line_code="logo_application",
        label="Aplicare folie logo",
        module_code="finisaje",
        component_code="comp_logo_finish",
        pricing_rule_code="VOL_V2_LOGO_APPLICATION_M2",
        basis_type="m2",
        quantity_paths=(),
        unit="m2",
        source="commercial_rules_volumetric_v2:logo_application_maps_FACE_VINYL_APPLICATION_LABOR",
        criticality="critical",
        owner_decision_required=False,
        owner_decision_code="LOGO_APPLICATION_COMMERCIAL_RULE",
        owner_decision_detail=(
            "Logo application maps to existing registry FACE_VINYL_APPLICATION_LABOR; "
            "fail-closed if unavailable."
        ),
        documented_unit_price=None,
        registry_pricing_code="FACE_VINYL_APPLICATION_LABOR",
    ),
    CommercialRuleDefinition(
        line_code="logo_led_modules",
        label="Sistem LED — module logo",
        module_code="sistem_led",
        component_code="comp_logo_lighting",
        pricing_rule_code="VOL_V2_LOGO_LED_MODULE_PIECE",
        basis_type="piece",
        quantity_paths=(),
        unit="buc",
        source="commercial_rules_volumetric_v2:logo_led_module_unpublished_eur",
        criticality="critical",
        documented_unit_price=LED_MODULE_COMMERCIAL_EUR_BUC,
        documented_unit_price_currency="EUR",
        owner_decision_required=True,
        owner_decision_code="LED_MODULE_COMMERCIAL_EUR_BUC",
        owner_decision_detail=(
            "F7H: logo LED module commercial EUR/buc unpublished — same Owner gap as letters."
        ),
    ),
)


def volumetric_presentation_currency(template_code: str | None) -> str | None:
    """EUR presentation for volumetric letters + ACM pilot only; None = no forced presentation."""
    code = (template_code or "").strip()
    if not code:
        return None
    for prefix in VOLUMETRIC_PRESENTATION_TEMPLATE_PREFIXES:
        if code.startswith(prefix):
            return VOLUMETRIC_PRESENTATION_CURRENCY
    return None


RULES_BY_TEMPLATE: dict[str, tuple[CommercialRuleDefinition, ...]] = {
    PILOT_TEMPLATE: VOLUMETRIC_V2_COMMERCIAL_RULES_WITH_ACM,
    "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1": (
        *ACM_STRUCTURA_COMMERCIAL_RULES,
        *LETTERS_ACM_COMPOSITION_CONNECTION_RULES,
    ),
}

CRITICAL_MODULE_CODES = frozenset(
    {
        "debitare_fata",
        "modelare_cant",
        "debitare_spate",
        "sistem_led",
        "finisaje",
        "sablon_montaj",
        "ambalare_livrare_montaj",
        "structura_suport",
    }
)

FORBIDDEN_HOURLY_TOKENS = frozenset(
    {
        "rate_per_hour",
        "workcenter_rate",
        "estimated_minutes",
        "duration_minutes",
        "hours",
        "time_cost",
        "labor_hour",
        "per_hour",
    }
)
