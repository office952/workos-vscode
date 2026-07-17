"""Product System planning-duration contracts (operational minutes only).

TE2E-028B — Product System owns reusable duration formula definitions and
per-operation duration mode. ProductAggregate evaluates; Plan consumes.
Not a commercial or CostEngine/EIC authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Mapping

from services.active_template_scope import normalize_template_code
from services.formula_handlers import FormulaId

PlanningDurationMode = Literal["static", "formula", "none"]

# Letters template codes used in seeds / Order Snapshot V2 fixtures.
_LETTERS_TEMPLATE_CODES = frozenset(
    {
        "TPL-VOLUMETRIC-LETTERS",
        "TPL-VOLUMETRIC-LETTERS_V2",
    }
)


@dataclass(frozen=True)
class PlanningDurationContract:
    """Reusable Product System duration contract for one operation."""

    operation_code: str
    duration_mode: PlanningDurationMode
    formula_id: str | None = None
    formula_params: Mapping[str, Any] | None = None
    required_inputs: tuple[str, ...] = ()
    units: str = "min"
    notes: str = ""


# TE2E-028B Letters-only proof: vector prep duration from letter count.
# Uses approved FormulaId.COUNT_BASED_TIME — not a quantity/commercial formula.
LETTERS_VECTOR_PREP_DURATION = PlanningDurationContract(
    operation_code="vector_prep",
    duration_mode="formula",
    formula_id=FormulaId.COUNT_BASED_TIME.value,
    formula_params={"minutes_per_letter": 2.0},
    required_inputs=("letter_count",),
    units="min",
    notes=(
        "Operational planning duration for Pregătire vector / font. "
        "Commercial quantity formula on the same op remains letter_count_material."
    ),
)

_LETTERS_DURATION_BY_OP: dict[str, PlanningDurationContract] = {
    LETTERS_VECTOR_PREP_DURATION.operation_code: LETTERS_VECTOR_PREP_DURATION,
}


def is_letters_planning_template(template_code: str | None) -> bool:
    return normalize_template_code(template_code) in _LETTERS_TEMPLATE_CODES


def get_planning_duration_contract(
    template_code: str | None,
    operation_code: str | None,
) -> PlanningDurationContract | None:
    """Return Product System duration contract when declared for template+op."""
    if not is_letters_planning_template(template_code):
        return None
    code = str(operation_code or "").strip()
    if not code:
        return None
    return _LETTERS_DURATION_BY_OP.get(code)
