"""Temporary local read-only internal cost rules for volumetric letters v2 (Step 7H).

NOT the official Pricing Registry (Step 7I). No rate_per_hour, no minutes×rate totals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from schemas.estimated_internal_cost import InternalBasisType

PILOT_TEMPLATE = "TPL-VOLUMETRIC-LETTERS_v2"

# Step 8 dev bridge — interim RON operation unit costs for live freeze QA only.
# NOT production registry (7I). Owner must replace before official rollout.
DEV_BRIDGE_DEBITARE_FATA_RON_ML = 15.0
DEV_BRIDGE_MODELARE_CANT_RON_ML = 18.0
DEV_BRIDGE_DEBITARE_SPATE_RON_M2 = 12.0  # interim owner decision: m² basis for dev QA
DEV_BRIDGE_LED_INSTALL_RON_BUC = 2.0
DEV_BRIDGE_PSU_RON_BUC = 0.45
DEV_BRIDGE_FINISH_RON_M2 = 20.0
DEV_BRIDGE_SABLON_CNC_RON_M2 = 8.0

Criticality = Literal["critical", "optional"]
LineKind = Literal["operation", "consumable", "overhead"]
LogoRateStatus = Literal["active", "inactive"]


@dataclass(frozen=True)
class LogoInternalOperationRate:
    operation_code: str
    unit: str
    internal_unit_cost: float
    currency: str
    source: str
    rule_code: str
    status: LogoRateStatus = "active"


# Owner-approved canonical internal rates for linked-logo artwork operations (EIC only).
LOGO_ARTWORK_INTERNAL_OPERATION_RATES: tuple[LogoInternalOperationRate, ...] = (
    LogoInternalOperationRate(
        operation_code="logo_face_print",
        unit="m2",
        internal_unit_cost=35.0,
        currency="RON",
        source="internal_cost_rules_volumetric_v2:logo_face_print_m2",
        rule_code="INT_LOGO_FACE_PRINT_M2",
    ),
    LogoInternalOperationRate(
        operation_code="logo_face_laminate",
        unit="m2",
        internal_unit_cost=35.0,
        currency="RON",
        source="internal_cost_rules_volumetric_v2:logo_face_laminate_m2",
        rule_code="INT_LOGO_FACE_LAMINATE_M2",
    ),
)

LOGO_ARTWORK_INTERNAL_OPERATION_RATE_BY_CODE: dict[str, LogoInternalOperationRate] = {
    rate.operation_code: rate for rate in LOGO_ARTWORK_INTERNAL_OPERATION_RATES
}

if len(LOGO_ARTWORK_INTERNAL_OPERATION_RATE_BY_CODE) != len(LOGO_ARTWORK_INTERNAL_OPERATION_RATES):
    raise ValueError("Duplicate logo internal operation rate operation_code entries are forbidden.")
if "logo_finish_application" in LOGO_ARTWORK_INTERNAL_OPERATION_RATE_BY_CODE:
    raise ValueError("logo_finish_application must not receive a numeric internal rate in this catalog.")


@dataclass(frozen=True)
class InternalOperationRule:
    line_code: str
    label: str
    module_code: str
    component_code: str | None
    rule_code: str
    basis_type: InternalBasisType
    quantity_paths: tuple[str, ...]
    unit: str
    source: str
    criticality: Criticality = "critical"
    internal_unit_cost: float | None = None
    owner_decision_required: bool = False
    owner_decision_code: str | None = None
    owner_decision_detail: str | None = None
    module_gate: str | None = None
    material_gate_path: str | None = None
    material_gate_value: str | None = None
    always_include: bool = False
    warnings: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class InternalConsumableRule:
    line_code: str
    label: str
    module_code: str
    rule_code: str
    basis_type: InternalBasisType
    quantity_paths: tuple[str, ...]
    unit: str
    source: str
    criticality: Criticality = "optional"
    internal_unit_cost: float | None = None
    owner_decision_required: bool = True
    owner_decision_code: str | None = None
    owner_decision_detail: str | None = None


@dataclass(frozen=True)
class InternalOverheadRule:
    line_code: str
    label: str
    rule_code: str
    basis_type: InternalBasisType = "percentage"
    placeholder_percent: float | None = None
    source: str = "internal_cost_rules_volumetric_v2:overhead_placeholder"
    owner_decision_required: bool = True
    owner_decision_code: str = "OVERHEAD_ALLOCATION_PENDING"
    owner_decision_detail: str = "Internal overhead allocation not owner-defined."


@dataclass(frozen=True)
class CapacityHintRule:
    code: str
    label: str
    formula_id: str
    formula_params: dict
    source: str
    module_code: str | None = None
    purpose: str = "capacity"


INTERNAL_QC_OPERATION_CODES = frozenset({"qc_letters", "qc_internal_check", "qc_banner"})

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

VOLUMETRIC_V2_OPERATION_RULES: tuple[InternalOperationRule, ...] = (
    InternalOperationRule(
        line_code="debitare_fata",
        label="Debitare față — cost intern operație",
        module_code="debitare_fata",
        component_code="comp_face_litere",
        rule_code="INT_VOL_V2_FACE_CNC_ML",
        basis_type="ml",
        quantity_paths=("quote_geometry.letter_perimeter_m", "letter_perimeter_m"),
        unit="ml",
        source="internal_cost_rules_volumetric_v2:face_cnc_ml",
        internal_unit_cost=DEV_BRIDGE_DEBITARE_FATA_RON_ML,
    ),
    InternalOperationRule(
        line_code="modelare_cant",
        label="Modelare cant — cost intern operație",
        module_code="modelare_cant",
        component_code="comp_lateral_litere",
        rule_code="INT_VOL_V2_RETURN_ML",
        basis_type="ml",
        quantity_paths=("quote_geometry.letter_perimeter_m", "letter_perimeter_m"),
        unit="ml",
        source="internal_cost_rules_volumetric_v2:return_profile_ml",
        internal_unit_cost=DEV_BRIDGE_MODELARE_CANT_RON_ML,
        warnings=("Technical: letter_perimeter_m, return_depth_mm — not hourly.",),
    ),
    InternalOperationRule(
        line_code="debitare_spate",
        label="Debitare spate — cost intern operație",
        module_code="debitare_spate",
        component_code="comp_spate_litere",
        rule_code="INT_VOL_V2_BACK_M2_DEV_BRIDGE",
        basis_type="m2",
        quantity_paths=("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
        unit="m2",
        source="internal_cost_rules_volumetric_v2:back_m2_dev_bridge",
        internal_unit_cost=DEV_BRIDGE_DEBITARE_SPATE_RON_M2,
        warnings=(
            "Step 8 dev bridge: interim m² basis until owner formalizes ml vs m² in 7I.",
        ),
    ),
    InternalOperationRule(
        line_code="sistem_led_install",
        label="Sistem LED — instalare internă",
        module_code="sistem_led",
        component_code="comp_led_litere",
        rule_code="INT_VOL_V2_LED_INSTALL_PIECE",
        basis_type="piece",
        quantity_paths=("finish_setup.led_module_count", "led_module_count"),
        unit="buc",
        source="internal_cost_rules_volumetric_v2:led_install_piece",
        module_gate="sistem_led",
        internal_unit_cost=DEV_BRIDGE_LED_INSTALL_RON_BUC,
    ),
    InternalOperationRule(
        line_code="sursa_led",
        label="Sursă LED — cost intern piece",
        module_code="sistem_led",
        component_code="comp_led_litere",
        rule_code="INT_VOL_V2_PSU_PIECE",
        basis_type="piece",
        quantity_paths=("finish_setup.selected_psu_watts", "selected_psu_watts"),
        unit="buc",
        source="internal_cost_rules_volumetric_v2:psu_piece",
        module_gate="sistem_led",
        internal_unit_cost=DEV_BRIDGE_PSU_RON_BUC,
    ),
    InternalOperationRule(
        line_code="finisaje_ops",
        label="Finisaje — operații interne",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        rule_code="INT_VOL_V2_FINISH_M2",
        basis_type="m2",
        quantity_paths=("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
        unit="m2",
        source="internal_cost_rules_volumetric_v2:finish_m2",
        internal_unit_cost=DEV_BRIDGE_FINISH_RON_M2,
    ),
    InternalOperationRule(
        line_code="sablon_montaj_cnc",
        label="Șablon montaj — CNC intern",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        rule_code="INT_VOL_V2_SABLON_M2",
        basis_type="m2",
        quantity_paths=("finish_setup.mounting_template_area_m2", "mounting_template_area_m2"),
        unit="m2",
        source="internal_cost_rules_volumetric_v2:sablon_cnc_m2",
        module_gate="finisaje",
        internal_unit_cost=DEV_BRIDGE_SABLON_CNC_RON_M2,
    ),
    InternalOperationRule(
        line_code="sablon_montaj_forex",
        label="Șablon montaj Forex — cost intern material/op",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        rule_code="INT_VOL_V2_SABLON_FOREX_PENDING",
        basis_type="m2",
        quantity_paths=("finish_setup.mounting_template_area_m2", "mounting_template_area_m2"),
        unit="m2",
        source="internal_cost_rules_volumetric_v2:sablon_forex_pending",
        material_gate_path="finish_setup.mounting_template_material_type",
        material_gate_value="forex",
        module_gate="finisaje",
        owner_decision_required=True,
        owner_decision_code="INTERNAL_SABLON_FOREX_COST",
        owner_decision_detail="Forex sablon internal operation cost not owner-approved.",
    ),
    InternalOperationRule(
        line_code="ambalare",
        label="Ambalare — cost intern",
        module_code="finisaje",
        component_code="comp_finisaj_litere",
        rule_code="INT_VOL_V2_PACKAGING_PENDING",
        basis_type="fixed",
        quantity_paths=(),
        unit="set",
        source="internal_cost_rules_volumetric_v2:packaging_pending",
        criticality="optional",
        owner_decision_required=True,
        owner_decision_code="INTERNAL_AMBALARE_RULE",
        owner_decision_detail="Packaging internal rule not owner-defined.",
    ),
    InternalOperationRule(
        line_code="montaj",
        label="Montaj șantier — future/optional",
        module_code="finisaje",
        component_code=None,
        rule_code="INT_VOL_V2_SITE_MOUNT_FUTURE",
        basis_type="fixed",
        quantity_paths=(),
        unit="locatie",
        source="internal_cost_rules_volumetric_v2:site_mount_future",
        criticality="optional",
        owner_decision_required=True,
        owner_decision_code="INTERNAL_MONTAJ_RULE",
        owner_decision_detail="Site mounting internal rule is future scope.",
        always_include=True,
    ),
)

VOLUMETRIC_V2_CONSUMABLE_RULES: tuple[InternalConsumableRule, ...] = (
    InternalConsumableRule(
        line_code="finisaje_consumables",
        label="Consumabile finisaj (RAL/vinyl)",
        module_code="finisaje",
        rule_code="INT_VOL_V2_FINISH_CONSUMABLES",
        basis_type="fixed",
        quantity_paths=("quote_geometry.letter_face_area_m2", "letter_face_area_m2"),
        unit="m2",
        source="internal_cost_rules_volumetric_v2:finish_consumables_placeholder",
        owner_decision_code="INTERNAL_CONSUMABLES_RULE",
        owner_decision_detail="Consumables quantification pending owner calibration.",
    ),
)

VOLUMETRIC_V2_OVERHEAD_RULES: tuple[InternalOverheadRule, ...] = (
    InternalOverheadRule(
        line_code="internal_overhead",
        label="Overhead intern (placeholder)",
        rule_code="INT_VOL_V2_OVERHEAD_PLACEHOLDER",
    ),
)

VOLUMETRIC_V2_CAPACITY_HINT_RULES: tuple[CapacityHintRule, ...] = (
    CapacityHintRule(
        code="face_cnc_capacity",
        label="Debitare față — estimare timp capacitate",
        formula_id="perimeter_based_time",
        formula_params={"perimeter_key": "letter_perimeter_m", "passes": 1, "min_minutes": 5},
        source="formula_handlers:perimeter_based_time",
        module_code="debitare_fata",
        purpose="capacity",
    ),
    CapacityHintRule(
        code="return_profile_capacity",
        label="Modelare cant — estimare timp capacitate",
        formula_id="perimeter_based_time",
        formula_params={"perimeter_key": "letter_perimeter_m", "passes": 2, "min_minutes": 10},
        source="formula_handlers:perimeter_based_time",
        module_code="modelare_cant",
        purpose="sanity_check",
    ),
)

RULES_BY_TEMPLATE: dict[str, dict[str, tuple]] = {
    PILOT_TEMPLATE: {
        "operations": VOLUMETRIC_V2_OPERATION_RULES,
        "consumables": VOLUMETRIC_V2_CONSUMABLE_RULES,
        "overhead": VOLUMETRIC_V2_OVERHEAD_RULES,
        "capacity": VOLUMETRIC_V2_CAPACITY_HINT_RULES,
    },
}

CRITICAL_MODULE_CODES = frozenset(
    {
        "debitare_fata",
        "modelare_cant",
        "debitare_spate",
        "sistem_led",
        "finisaje",
    }
)
