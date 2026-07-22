"""AI Operational Defaults V1 — typed application registry (no DB table).

Conservative, configurable, quantity-based. Time is not the primary basis.
Precedence: MEASURED_REALITY > OWNER_CONFIRMED > CATALOG > AI_DECISION > LEGACY.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

DecisionDomain = Literal["packaging", "electrical", "led", "labor", "service"]
Confidence = Literal["LOW", "MEDIUM", "HIGH"]

VL = "TPL-VOLUMETRIC-LETTERS_v2"
LOGO = "TPL-VOLUMETRIC-LOGO_v1"
ACM = "TPL-ACM-BOXED-MOUNTING-SUPPORT_v1"
VOLUM_AL = "TPL-VOLUM-ALUMINIU_v1"

SOURCE_PRECEDENCE: tuple[str, ...] = (
    "MEASURED_REALITY",
    "OWNER_CONFIRMED",
    "CATALOG",
    "AI_DECISION",
    "LEGACY",
)


@dataclass(frozen=True)
class AiOperationalDefault:
    decision_id: str
    domain: DecisionDomain
    target_type: str  # catalog_code | commercial_line | operation
    target_code: str
    display_name_ro: str
    formula: str
    unit: str
    default_value: float
    minimum: float
    maximum: Optional[float]
    currency: str
    quantity_key: Optional[str]
    confidence: Confidence
    rationale_ro: str
    review_trigger: str
    applies_to_templates: tuple[str, ...]
    demotes_blockers: tuple[str, ...] = ()
    calibration_hooks: tuple[str, ...] = (
        "observed_actual_cost",
        "actual_operation_count",
        "observed_time",
        "variance",
        "sample_count",
    )
    status: str = "active"
    configurable: bool = True
    decision_source: str = "AI_DECISION"


# --- Packaging: size bands (EUR / product) — not time ---
AI_PACK_SMALL = AiOperationalDefault(
    decision_id="AI_PACK_SMALL",
    domain="packaging",
    target_type="catalog_code",
    target_code="PACKAGING",
    display_name_ro="Ambalare — produs mic",
    formula="max(minimum, band_small) when face_area_m2 < 0.5",
    unit="EUR/produs",
    default_value=25.0,
    minimum=20.0,
    maximum=60.0,
    currency="EUR",
    quantity_key="letter_face_area_m2",
    confidence="MEDIUM",
    rationale_ro=(
        "Ambalare pe categorie de mărime (mp față), nu pe minute. "
        "Valoare conservatoare pentru litere/logo mici."
    ),
    review_trigger="observed_packaging_cost_sample_count>=20",
    applies_to_templates=(VL, LOGO, ACM, VOLUM_AL),
    demotes_blockers=("AMBALARE_COMMERCIAL_RULE", "MISSING_OWNER_FORMULA"),
)

AI_PACK_MEDIUM = AiOperationalDefault(
    decision_id="AI_PACK_MEDIUM",
    domain="packaging",
    target_type="catalog_code",
    target_code="PACKAGING",
    display_name_ro="Ambalare — produs mediu",
    formula="max(minimum, band_medium) when 0.5 <= face_area_m2 < 2.0",
    unit="EUR/produs",
    default_value=45.0,
    minimum=30.0,
    maximum=100.0,
    currency="EUR",
    quantity_key="letter_face_area_m2",
    confidence="MEDIUM",
    rationale_ro="Bandă medie mp față; configurabilă; fără timp ca bază.",
    review_trigger="observed_packaging_cost_sample_count>=20",
    applies_to_templates=(VL, LOGO, ACM, VOLUM_AL),
    demotes_blockers=("AMBALARE_COMMERCIAL_RULE", "MISSING_OWNER_FORMULA"),
)

AI_PACK_LARGE = AiOperationalDefault(
    decision_id="AI_PACK_LARGE",
    domain="packaging",
    target_type="catalog_code",
    target_code="PACKAGING",
    display_name_ro="Ambalare — produs mare",
    formula="max(minimum, band_large) when face_area_m2 >= 2.0",
    unit="EUR/produs",
    default_value=80.0,
    minimum=50.0,
    maximum=200.0,
    currency="EUR",
    quantity_key="letter_face_area_m2",
    confidence="MEDIUM",
    rationale_ro="Bandă mare / oversized; nu plat pentru toate produsele.",
    review_trigger="observed_packaging_cost_sample_count>=20",
    applies_to_templates=(VL, LOGO, ACM, VOLUM_AL),
    demotes_blockers=("AMBALARE_COMMERCIAL_RULE", "MISSING_OWNER_FORMULA"),
)

AI_PACK_FRAGILE_ADDON = AiOperationalDefault(
    decision_id="AI_PACK_FRAGILE_ADDON",
    domain="packaging",
    target_type="catalog_code",
    target_code="PACKAGING",
    display_name_ro="Ambalare — supliment fragil / iluminat",
    formula="band_resolved + fragile_addon when illuminated/electrical",
    unit="EUR/produs",
    default_value=25.0,
    minimum=15.0,
    maximum=80.0,
    currency="EUR",
    quantity_key="letter_led_module_count",
    confidence="MEDIUM",
    rationale_ro="Protecție suplimentară pentru produse iluminate / fragile.",
    review_trigger="fragility_claim_rate_review",
    applies_to_templates=(VL, LOGO),
    demotes_blockers=("AMBALARE_COMMERCIAL_RULE",),
)

# --- Electrical: min + per PSU (not minutes) ---
AI_ELEC_MIN = AiOperationalDefault(
    decision_id="AI_ELEC_MIN_PRODUCT",
    domain="electrical",
    target_type="catalog_code",
    target_code="ELECTRICAL_WIRING",
    display_name_ro="Electric — minim pe produs",
    formula="max(minimum, AI_ELEC_MIN + AI_ELEC_PER_PSU × psu_count)",
    unit="EUR/produs",
    default_value=30.0,
    minimum=30.0,
    maximum=120.0,
    currency="EUR",
    quantity_key="produs",
    confidence="MEDIUM",
    rationale_ro="Setup electric minim pe produs; fără minute/lucrător.",
    review_trigger="electrical_job_sample_count>=15",
    applies_to_templates=(VL, LOGO),
    demotes_blockers=("OPERATION_ONLY",),
)

AI_ELEC_PER_PSU = AiOperationalDefault(
    decision_id="AI_ELEC_PER_PSU",
    domain="electrical",
    target_type="catalog_code",
    target_code="ELECTRICAL_WIRING",
    display_name_ro="Electric — per sursă alimentare",
    formula="per_psu × psu_count (added to product minimum)",
    unit="EUR/buc",
    default_value=15.0,
    minimum=10.0,
    maximum=40.0,
    currency="EUR",
    quantity_key="psu_count",
    confidence="MEDIUM",
    rationale_ro="Complexitate electrică pe număr de PSU, nu pe timp.",
    review_trigger="electrical_job_sample_count>=15",
    applies_to_templates=(VL, LOGO),
    demotes_blockers=("OPERATION_ONLY",),
)

# --- LED: per module (not led_assembly_time) ---
AI_LED_PER_MODULE = AiOperationalDefault(
    decision_id="AI_LED_PER_MODULE",
    domain="led",
    target_type="catalog_code",
    target_code="LED_ASSEMBLY",
    display_name_ro="Montaj LED — per modul",
    formula="letter_led_module_count × rate_per_module",
    unit="EUR/module",
    default_value=0.35,
    minimum=0.20,
    maximum=1.50,
    currency="EUR",
    quantity_key="letter_led_module_count",
    confidence="MEDIUM",
    rationale_ro=(
        "Cost pe modul LED confirmat ca quantity key. "
        "Nu folosim led_assembly_time / productivitate inventată."
    ),
    review_trigger="led_install_sample_count>=30",
    applies_to_templates=(VL, LOGO),
    demotes_blockers=("LED_ASSEMBLY_TIME_NOT_BOUND",),
)

# --- ACM shell labor ops without formula ---
AI_ACM_PANEL_LABOR = AiOperationalDefault(
    decision_id="AI_ACM_PANEL_LABOR_M2",
    domain="labor",
    target_type="operation",
    target_code="FOLD_CASSETTE",
    display_name_ro="Manoperă panou ACM — pe mp",
    formula="panel_area_m2 × rate_per_m2 (FOLD/MOUNT shell)",
    unit="EUR/mp",
    default_value=12.0,
    minimum=8.0,
    maximum=30.0,
    currency="EUR",
    quantity_key="panel_area_m2",
    confidence="LOW",
    rationale_ro=(
        "Fallback pentru FOLD_CASSETTE / MOUNT_ACM_PANEL fără formulă. "
        "Nu deblochează tratamente față."
    ),
    review_trigger="acm_shell_labor_sample_count>=20",
    applies_to_templates=(ACM,),
    demotes_blockers=("OPERATION_ONLY",),
)

AI_OPERATIONAL_DEFAULTS: tuple[AiOperationalDefault, ...] = (
    AI_PACK_SMALL,
    AI_PACK_MEDIUM,
    AI_PACK_LARGE,
    AI_PACK_FRAGILE_ADDON,
    AI_ELEC_MIN,
    AI_ELEC_PER_PSU,
    AI_LED_PER_MODULE,
    AI_ACM_PANEL_LABOR,
)

# Representative decision used when resolving packaging band (UI primary row)
PACKAGING_RESOLVER_ID = "AI_PACK_PRODUCT_BAND"


@dataclass
class PackagingBandResult:
    decision_id: str
    band: str
    value: float
    minimum: float
    fragile_addon: float = 0.0


def resolve_packaging_band(
    *,
    face_area_m2: Optional[float],
    illuminated: bool,
    overrides: dict[str, float],
) -> PackagingBandResult:
    """Pick size band; apply optional fragile addon. No time inputs."""
    area = face_area_m2 if face_area_m2 is not None else 1.0  # medium default when unknown
    if area < 0.5:
        base = AI_PACK_SMALL
        band = "SMALL"
    elif area < 2.0:
        base = AI_PACK_MEDIUM
        band = "MEDIUM"
    else:
        base = AI_PACK_LARGE
        band = "LARGE"
    value = float(overrides.get(base.decision_id, base.default_value))
    minimum = base.minimum
    fragile = 0.0
    if illuminated:
        fragile = float(
            overrides.get(AI_PACK_FRAGILE_ADDON.decision_id, AI_PACK_FRAGILE_ADDON.default_value)
        )
    return PackagingBandResult(
        decision_id=PACKAGING_RESOLVER_ID,
        band=band,
        value=max(minimum, value) + fragile,
        minimum=minimum,
        fragile_addon=fragile,
    )


def defaults_for_template(template_code: str) -> list[AiOperationalDefault]:
    code = str(template_code or "").strip()
    needle = code.upper()
    out: list[AiOperationalDefault] = []
    for d in AI_OPERATIONAL_DEFAULTS:
        if any(str(t).upper() == needle for t in d.applies_to_templates):
            out.append(d)
    return out
