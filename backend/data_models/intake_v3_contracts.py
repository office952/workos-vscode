"""Intake V3 architecture contracts — version constants and operational reference rules.

Pure data/constants module. No DB access, no CostEngine, no execution plan mutation.
"""

from __future__ import annotations

from typing import Final, Literal, TypedDict

# ---------------------------------------------------------------------------
# Schema versioning (in-memory / documentation; no DB migration in this build)
# ---------------------------------------------------------------------------

INTAKE_V3_SCHEMA_VERSION: Final[str] = "3"
INTAKE_V3_CONTRACT_VERSION: Final[str] = "2026-06-17"

PILOT_TEMPLATE_CODE: Final[str] = "TPL-VOLUMETRIC-LETTERS"

# Namespace for future persistence inside intake_requests.product_spec_json without migration.
INTAKE_V3_JSON_NAMESPACE: Final[str] = "intake_v3"

# ---------------------------------------------------------------------------
# Readiness blocker / warning codes (stable contract surface)
# ---------------------------------------------------------------------------

BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH: Final[str] = "MISSING_FACE_VINYL_ROLL_WIDTH"
BLOCKER_MISSING_RETURN_DEPTH: Final[str] = "MISSING_RETURN_DEPTH"
BLOCKER_UNCONFIRMED_LETTER_MODEL: Final[str] = "UNCONFIRMED_LETTER_MODEL"
BLOCKER_MISSING_DIMENSIONS: Final[str] = "MISSING_DIMENSIONS"
BLOCKER_MISSING_FINISH_ASSIGNMENT: Final[str] = "MISSING_FINISH_ASSIGNMENT"
BLOCKER_MISSING_LETTER_COUNT: Final[str] = "MISSING_LETTER_COUNT"
BLOCKER_MISSING_CUT_CONTOUR_MODEL: Final[str] = "MISSING_CUT_CONTOUR_MODEL"
BLOCKER_CUT_CONTOUR_COUNT_MISMATCH: Final[str] = "CUT_CONTOUR_COUNT_MISMATCH"
BLOCKER_INNER_HOLE_WITHOUT_PARENT_LETTER: Final[str] = "INNER_HOLE_WITHOUT_PARENT_LETTER"
BLOCKER_LETTER_WITHOUT_OUTER_CONTOUR: Final[str] = "LETTER_WITHOUT_OUTER_CONTOUR"
BLOCKER_MISSING_FACE_FINISH_CONFIRMATION: Final[str] = "MISSING_FACE_FINISH_CONFIRMATION"
BLOCKER_MISSING_RETURN_FINISH_CONFIRMATION: Final[str] = "MISSING_RETURN_FINISH_CONFIRMATION"
BLOCKER_MISSING_BACKING_FINISH_CONFIRMATION: Final[str] = "MISSING_BACKING_FINISH_CONFIRMATION"
BLOCKER_MISSING_RETURN_PAINT_COLOR: Final[str] = "MISSING_RETURN_PAINT_COLOR"
BLOCKER_MISSING_GROUP_FINISH_ASSIGNMENT: Final[str] = "MISSING_GROUP_FINISH_ASSIGNMENT"
BLOCKER_UNSUPPORTED_FINISH_MODE: Final[str] = "UNSUPPORTED_FINISH_MODE"
BLOCKER_MISSING_LAYER_FINISH_ASSIGNMENT: Final[str] = "MISSING_LAYER_FINISH_ASSIGNMENT"
BLOCKER_UNCONFIRMED_LAYER_FINISH: Final[str] = "UNCONFIRMED_LAYER_FINISH"
BLOCKER_PENDING_LAYER_FINISH: Final[str] = "PENDING_LAYER_FINISH"
BLOCKER_MISSING_PRINTED_ARTWORK_SETUP: Final[str] = "MISSING_PRINTED_ARTWORK_SETUP"
BLOCKER_MISSING_PRINTED_ARTWORK_PRINT_METHOD: Final[str] = "MISSING_PRINTED_ARTWORK_PRINT_METHOD"
BLOCKER_MISSING_PRINTED_ARTWORK_LAMINATE_TYPE: Final[str] = "MISSING_PRINTED_ARTWORK_LAMINATE_TYPE"
BLOCKER_MISSING_PRINTED_ARTWORK_CONTOUR_DECISION: Final[str] = "MISSING_PRINTED_ARTWORK_CONTOUR_DECISION"
BLOCKER_UNCONFIRMED_PRINTED_ARTWORK: Final[str] = "UNCONFIRMED_PRINTED_ARTWORK"
BLOCKER_UNCONFIRMED_LIGHTING_PLAN: Final[str] = "UNCONFIRMED_LIGHTING_PLAN"
BLOCKER_MISSING_LIGHTING_ILLUMINATION_MODE: Final[str] = "MISSING_LIGHTING_ILLUMINATION_MODE"
BLOCKER_MISSING_LED_MODULE_POWER: Final[str] = "MISSING_LED_MODULE_POWER"
BLOCKER_MISSING_LED_MODULE_COUNT: Final[str] = "MISSING_LED_MODULE_COUNT"
BLOCKER_MISSING_LED_LIGHT_COLOR: Final[str] = "MISSING_LED_LIGHT_COLOR"
BLOCKER_MISSING_LED_SYSTEM: Final[str] = "MISSING_LED_SYSTEM"
BLOCKER_MISSING_PSU_PLAN: Final[str] = "MISSING_PSU_PLAN"
BLOCKER_INSUFFICIENT_PSU_CAPACITY: Final[str] = "INSUFFICIENT_PSU_CAPACITY"

WARNING_LIGHTING_MANUAL_OVERRIDE: Final[str] = "LIGHTING_MANUAL_OVERRIDE"
WARNING_LIGHTING_LOW_RESERVE_PERCENT: Final[str] = "LIGHTING_LOW_RESERVE_PERCENT"
WARNING_LIGHTING_CUSTOM_COLOR: Final[str] = "LIGHTING_CUSTOM_COLOR"
WARNING_LIGHTING_PSU_PACKED_AT_PACKAGING: Final[str] = "LIGHTING_PSU_PACKED_AT_PACKAGING"

WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH: Final[str] = "RAW_CONFIRMED_LETTER_COUNT_MISMATCH"
WARNING_LOW_RAW_ANALYSIS_CONFIDENCE: Final[str] = "LOW_RAW_ANALYSIS_CONFIDENCE"
WARNING_IGNORED_OBJECTS_PRESENT: Final[str] = "IGNORED_OBJECTS_PRESENT"
WARNING_UNKNOWN_CONTOUR_ROLES_PRESENT: Final[str] = "UNKNOWN_CONTOUR_ROLES_PRESENT"
WARNING_MANY_COLORS_DETECTED: Final[str] = "MANY_COLORS_DETECTED"
WARNING_POSSIBLE_GUIDES_DETECTED: Final[str] = "POSSIBLE_GUIDES_DETECTED"
WARNING_LETTER_CUSTOM_FINISH_ADVANCED_MODE: Final[str] = "LETTER_CUSTOM_FINISH_ADVANCED_MODE"
WARNING_RETURN_PAINT_REQUIRES_FACE_PROTECTION: Final[str] = "RETURN_PAINT_REQUIRES_FACE_PROTECTION"
WARNING_FACE_VINYL_AFTER_RETURN_PAINTING: Final[str] = "FACE_VINYL_AFTER_RETURN_PAINTING"
WARNING_NO_SHARED_SUPPORT_PSU_PACKED: Final[str] = "NO_SHARED_SUPPORT_PSU_PACKED"
WARNING_MATERIAL_ESTIMATE_ONLY: Final[str] = "MATERIAL_ESTIMATE_ONLY"

READINESS_BLOCKER_CODES: Final[frozenset[str]] = frozenset(
    {
        BLOCKER_MISSING_FACE_VINYL_ROLL_WIDTH,
        BLOCKER_MISSING_RETURN_DEPTH,
        BLOCKER_UNCONFIRMED_LETTER_MODEL,
        BLOCKER_MISSING_DIMENSIONS,
        BLOCKER_MISSING_FINISH_ASSIGNMENT,
        BLOCKER_MISSING_LETTER_COUNT,
        BLOCKER_MISSING_CUT_CONTOUR_MODEL,
        BLOCKER_CUT_CONTOUR_COUNT_MISMATCH,
        BLOCKER_INNER_HOLE_WITHOUT_PARENT_LETTER,
        BLOCKER_LETTER_WITHOUT_OUTER_CONTOUR,
        BLOCKER_MISSING_FACE_FINISH_CONFIRMATION,
        BLOCKER_MISSING_RETURN_FINISH_CONFIRMATION,
        BLOCKER_MISSING_BACKING_FINISH_CONFIRMATION,
        BLOCKER_MISSING_RETURN_PAINT_COLOR,
        BLOCKER_MISSING_GROUP_FINISH_ASSIGNMENT,
        BLOCKER_UNSUPPORTED_FINISH_MODE,
        BLOCKER_MISSING_LAYER_FINISH_ASSIGNMENT,
        BLOCKER_UNCONFIRMED_LAYER_FINISH,
        BLOCKER_PENDING_LAYER_FINISH,
        BLOCKER_MISSING_PRINTED_ARTWORK_SETUP,
        BLOCKER_MISSING_PRINTED_ARTWORK_PRINT_METHOD,
        BLOCKER_MISSING_PRINTED_ARTWORK_LAMINATE_TYPE,
        BLOCKER_MISSING_PRINTED_ARTWORK_CONTOUR_DECISION,
        BLOCKER_UNCONFIRMED_PRINTED_ARTWORK,
        BLOCKER_UNCONFIRMED_LIGHTING_PLAN,
        BLOCKER_MISSING_LIGHTING_ILLUMINATION_MODE,
        BLOCKER_MISSING_LED_MODULE_POWER,
        BLOCKER_MISSING_LED_MODULE_COUNT,
        BLOCKER_MISSING_LED_LIGHT_COLOR,
        BLOCKER_MISSING_LED_SYSTEM,
        BLOCKER_MISSING_PSU_PLAN,
        BLOCKER_INSUFFICIENT_PSU_CAPACITY,
    }
)

VECTOR_MODEL_WARNING_CODES: Final[frozenset[str]] = frozenset(
    {
        WARNING_RAW_CONFIRMED_LETTER_COUNT_MISMATCH,
        WARNING_LOW_RAW_ANALYSIS_CONFIDENCE,
        WARNING_IGNORED_OBJECTS_PRESENT,
        WARNING_UNKNOWN_CONTOUR_ROLES_PRESENT,
        WARNING_MANY_COLORS_DETECTED,
        WARNING_POSSIBLE_GUIDES_DETECTED,
    }
)

FINISH_MATERIAL_WARNING_CODES: Final[frozenset[str]] = frozenset(
    {
        WARNING_LETTER_CUSTOM_FINISH_ADVANCED_MODE,
        WARNING_RETURN_PAINT_REQUIRES_FACE_PROTECTION,
        WARNING_FACE_VINYL_AFTER_RETURN_PAINTING,
        WARNING_NO_SHARED_SUPPORT_PSU_PACKED,
        WARNING_MATERIAL_ESTIMATE_ONLY,
        WARNING_LIGHTING_MANUAL_OVERRIDE,
        WARNING_LIGHTING_LOW_RESERVE_PERCENT,
        WARNING_LIGHTING_CUSTOM_COLOR,
        WARNING_LIGHTING_PSU_PACKED_AT_PACKAGING,
    }
)

SUPPORT_MODE_NO_SHARED: Final[str] = "no_shared_support"
SUPPORT_MODE_SHARED_PENDING: Final[str] = "shared_support_pending"

WARNING_SHARED_SUPPORT_PENDING: Final[str] = "SHARED_SUPPORT_PENDING"

# Pricing adapter must never emit commercial price keys.
PRICING_ADAPTER_FORBIDDEN_KEYS: Final[frozenset[str]] = frozenset(
    {"total_price", "unit_price", "margin", "tva", "vat", "commercial_total", "sell_price"}
)

# Thresholds for raw analysis warnings (pure service logic).
LOW_RAW_ANALYSIS_CONFIDENCE_THRESHOLD: Final[float] = 0.5
MANY_COLORS_DETECTED_THRESHOLD: Final[int] = 10

# ---------------------------------------------------------------------------
# Owner operational rules — documented truth; NOT enforced in execution this build.
# Future build: AUDIT/FIX — Volumetric execution task order and electrical source handling
# ---------------------------------------------------------------------------

OwnerOperationalRuleId = Literal[
    "face_vinyl_after_assembly_and_back",
    "return_vinyl_before_side_forming",
    "no_shared_support_psu_at_packaging",
    "shared_support_electrical_task_allowed",
]

OWNER_OPERATIONAL_RULES: Final[tuple[OwnerOperationalRuleId, ...]] = (
    "face_vinyl_after_assembly_and_back",
    "return_vinyl_before_side_forming",
    "no_shared_support_psu_at_packaging",
    "shared_support_electrical_task_allowed",
)

REFERENCE_TASK_ORDER_NO_SHARED_SUPPORT: Final[tuple[str, ...]] = (
    "Verificare grafică / vectorizare",
    "Debitare față plexiglas",
    "Colantare cant — Oracal 651 / 055m Int / 60 mm",
    "Modelare canturi aluminiu 60 mm",
    "Lipire canturi pe fețele literelor",
    "Debitare spate Forex 10 mm",
    "Montaj LED",
    "Cablare internă LED / lăsat cablu pentru conectare",
    "Asamblare litere volumetrice / montaj spate",
    "Colantare fețe litere — Oracal 8500 / 527 Pastel blue",
    "Verificare finală lucrare",
    "Ambalare / predare — include sursele calculate",
)


class OwnerOperationalRule(TypedDict):
    rule_id: OwnerOperationalRuleId
    summary: str
    enforced_in_execution: bool
    future_build: str


OWNER_OPERATIONAL_RULE_DETAILS: Final[tuple[OwnerOperationalRule, ...]] = (
    {
        "rule_id": "face_vinyl_after_assembly_and_back",
        "summary": (
            "Colantarea fețelor literelor se face după asamblarea literelor "
            "și montarea spatelui, nu imediat după debitarea feței."
        ),
        "enforced_in_execution": False,
        "future_build": "AUDIT/FIX — Volumetric execution task order and electrical source handling",
    },
    {
        "rule_id": "return_vinyl_before_side_forming",
        "summary": (
            "Colantarea cantului (Oracal 651) se face pe banda plată înainte de modelarea cantului."
        ),
        "enforced_in_execution": False,
        "future_build": "AUDIT/FIX — Volumetric execution task order and electrical source handling",
    },
    {
        "rule_id": "no_shared_support_psu_at_packaging",
        "summary": (
            "Fără suport comun (bare/ACM/casetă/structură): nu există task separat "
            "Cablare/surse pe suport; sursele calculate se pun la Ambalare/predare."
        ),
        "enforced_in_execution": False,
        "future_build": "AUDIT/FIX — Volumetric execution task order and electrical source handling",
    },
    {
        "rule_id": "shared_support_electrical_task_allowed",
        "summary": (
            "Cu suport comun montat în atelier, cablarea/sursele pe suport "
            "poate deveni task separat în același order."
        ),
        "enforced_in_execution": False,
        "future_build": "AUDIT/FIX — Volumetric execution task order and electrical source handling",
    },
)

# Locked reference case for contract tests and documentation (HUB MEDIA PRODUCTION).
HUB_MEDIA_PRODUCTION_LETTER_MODEL: Final[dict[str, int]] = {
    "letter_count": 18,
    "cut_contour_count": 27,
    "inner_hole_count": 9,
}
