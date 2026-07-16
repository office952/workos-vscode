"""Temporary local read-only commercial price rules for volumetric letters v2 (Step 7G).

NOT the official Pricing Registry (Step 7I). No workcenter_rates, no rate_per_hour,
no CostEngine totals, no invented RON prices except owner-documented exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from schemas.commercial_price_proposal import CommercialBasisType

PILOT_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"

Criticality = Literal["critical", "optional"]


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
    warnings: tuple[str, ...] = field(default_factory=tuple)


# Owner-documented exception: hartie (paper) sablon montaj — 5 EUR/m² when selected.
SABLON_HARTIE_DOCUMENTED_EUR_M2 = 5.0

# Step 8 dev bridge — interim RON commercial unit prices for live V6 QA only.
# NOT production Pricing Registry (Step 7I). Owner must replace before official rollout.
DEV_BRIDGE_DEBITARE_FATA_RON_ML = 25.0
DEV_BRIDGE_MODELARE_CANT_RON_ML = 30.0
DEV_BRIDGE_DEBITARE_SPATE_RON_M2 = 20.0
DEV_BRIDGE_LED_MODULE_RON_BUC = 5.0
DEV_BRIDGE_PSU_RON_BUC = 150.0
DEV_BRIDGE_FINISH_RON_M2 = 35.0
DEV_BRIDGE_SABLON_FOREX_RON_M2 = 15.0

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
        source="commercial_rules_volumetric_v2:face_perimeter_ml",
        criticality="critical",
        documented_unit_price=DEV_BRIDGE_DEBITARE_FATA_RON_ML,
        documented_unit_price_currency="RON",
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
        source="commercial_rules_volumetric_v2:return_profile_ml",
        criticality="critical",
        documented_unit_price=DEV_BRIDGE_MODELARE_CANT_RON_ML,
        documented_unit_price_currency="RON",
        warnings=("Technical inputs: letter_perimeter_m, return_depth_mm — not minutes.",),
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
        source="commercial_rules_volumetric_v2:back_m2_dev_bridge",
        criticality="critical",
        documented_unit_price=DEV_BRIDGE_DEBITARE_SPATE_RON_M2,
        documented_unit_price_currency="RON",
        warnings=(
            "Step 8 dev bridge: interim m² basis until owner formalizes ml vs m² in Pricing Registry.",
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
        source="commercial_rules_volumetric_v2:letter_led_module_count",
        criticality="critical",
        module_gate="sistem_led",
        documented_unit_price=DEV_BRIDGE_LED_MODULE_RON_BUC,
        documented_unit_price_currency="RON",
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
        source="commercial_rules_volumetric_v2:psu_piece_dev_bridge",
        criticality="critical",
        module_gate="sistem_led",
        documented_unit_price=DEV_BRIDGE_PSU_RON_BUC,
        documented_unit_price_currency="RON",
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
        line_code="sablon_montaj",
        label="Șablon montaj",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        pricing_rule_code="VOL_V2_SABLON_M2",
        basis_type="m2",
        quantity_paths=("finish_setup.mounting_template_area_m2", "mounting_template_area_m2"),
        unit="m2",
        source="commercial_rules_volumetric_v2:sablon_m2",
        criticality="critical",
        module_gate="finisaje",
    ),
    CommercialRuleDefinition(
        line_code="sablon_montaj_hartie",
        label="Șablon montaj — hârtie (documentat)",
        module_code="finisaje",
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
        module_gate="finisaje",
    ),
    CommercialRuleDefinition(
        line_code="sablon_montaj_forex",
        label="Șablon montaj — Forex",
        module_code="finisaje",
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
        module_gate="finisaje",
        warnings=("Step 8 dev bridge: interim Forex sablon price until owner approves in 7I.",),
    ),
    CommercialRuleDefinition(
        line_code="ambalare",
        label="Ambalare",
        module_code="finisaje",
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
    ),
    CommercialRuleDefinition(
        line_code="montaj",
        label="Montaj șantier",
        module_code="finisaje",
        component_code=None,
        pricing_rule_code="VOL_V2_SITE_MOUNT_FUTURE",
        basis_type="fixed",
        quantity_paths=(),
        unit="locatie",
        source="commercial_rules_volumetric_v2:site_mount_future_optional",
        criticality="optional",
        owner_decision_required=True,
        owner_decision_code="MONTAJ_COMMERCIAL_RULE",
        owner_decision_detail=(
            "Site installation was selected but no owner-confirmed commercial șantier tariff exists "
            "in Pricing Registry. Configure at /inventory/pricing. Confirmare remains disabled. "
            "Do not use internal labor minutes or employee cost as commercial montaj price."
        ),
        always_include=False,
    ),
)

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

VOLUMETRIC_V2_COMMERCIAL_RULES_WITH_ACM: tuple[CommercialRuleDefinition, ...] = (
    *VOLUMETRIC_V2_COMMERCIAL_RULES,
    *ACM_STRUCTURA_COMMERCIAL_RULES,
)

# Linked-child logo commercial rule *templates* (expanded per segment in CPP).
# Body construction reuses the same owner-documented DEV_BRIDGE commercial classes as letters.
# Print / laminate / application stay fail-closed until owner configures commercial tariffs
# (do NOT copy EIC internal rates into CPP).
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
        source="commercial_rules_volumetric_v2:logo_face_perimeter_ml",
        criticality="critical",
        documented_unit_price=DEV_BRIDGE_DEBITARE_FATA_RON_ML,
        documented_unit_price_currency="RON",
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
        source="commercial_rules_volumetric_v2:logo_return_perimeter_ml",
        criticality="critical",
        documented_unit_price=DEV_BRIDGE_MODELARE_CANT_RON_ML,
        documented_unit_price_currency="RON",
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
        source="commercial_rules_volumetric_v2:logo_back_m2_dev_bridge",
        criticality="critical",
        documented_unit_price=DEV_BRIDGE_DEBITARE_SPATE_RON_M2,
        documented_unit_price_currency="RON",
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
        source="commercial_rules_volumetric_v2:logo_led_module_count",
        criticality="critical",
        documented_unit_price=DEV_BRIDGE_LED_MODULE_RON_BUC,
        documented_unit_price_currency="RON",
    ),
)

RULES_BY_TEMPLATE: dict[str, tuple[CommercialRuleDefinition, ...]] = {
    PILOT_TEMPLATE: VOLUMETRIC_V2_COMMERCIAL_RULES_WITH_ACM,
    "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1": ACM_STRUCTURA_COMMERCIAL_RULES,
}

CRITICAL_MODULE_CODES = frozenset(
    {
        "debitare_fata",
        "modelare_cant",
        "debitare_spate",
        "sistem_led",
        "finisaje",
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
