"""Operation-owned machine requirement contracts (demand only).

Owner FACE_CNC_CUT_MACHINE_REQUIREMENT decisions:
  capability = CNC_ROUTER_CUTTING (CAPABILITY_CODES / CUT_FACE)
  resource_mode = MACHINE_BOUND
  batch_eligible = true (may participate in future MACHINE_RUN)

Does not select machine_id. Does not create reservations or runs.
machine_exclusive is implied by MACHINE_BOUND — not a separate stamp.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from data.product_process.catalogs import (
    CAPABILITY_CODES,
    PROCESS_TO_PRICED_OPERATION,
)

ResourceMode = Literal[
    "MACHINE_BOUND",
    "MANUAL_WORKSPACE",
    "PERSON_DRIVEN",
    "HYBRID",
    "FIELD",
]

# Process → priced op already maps CUT_FACE → face_cnc_cut.
_FACE_CNC_PROCESS = "CUT_FACE"
_FACE_CNC_CAPABILITY = "CNC_ROUTER_CUTTING"


@dataclass(frozen=True)
class OperationMachineRequirementContract:
    """Technical machine demand declared for one priced operation."""

    operation_code: str
    machine_capability_code: str
    resource_mode: ResourceMode
    batch_eligible: bool
    process_code: str | None = None
    notes: str = ""


def _assert_capability(code: str) -> str:
    if code not in CAPABILITY_CODES:
        raise ValueError(f"capability_not_in_catalog:{code}")
    return code


FACE_CNC_CUT_MACHINE_REQUIREMENT = OperationMachineRequirementContract(
    operation_code=PROCESS_TO_PRICED_OPERATION[_FACE_CNC_PROCESS],
    machine_capability_code=_assert_capability(_FACE_CNC_CAPABILITY),
    resource_mode="MACHINE_BOUND",
    batch_eligible=True,
    process_code=_FACE_CNC_PROCESS,
    notes=(
        "Owner FACE_CNC_CUT package: capability from process CUT_FACE; "
        "batch_eligible means may participate in a future shared CNC run only."
    ),
)

_BY_OPERATION: dict[str, OperationMachineRequirementContract] = {
    FACE_CNC_CUT_MACHINE_REQUIREMENT.operation_code: FACE_CNC_CUT_MACHINE_REQUIREMENT,
}


def get_operation_machine_requirement_contract(
    operation_code: str | None,
) -> OperationMachineRequirementContract | None:
    code = str(operation_code or "").strip()
    if not code:
        return None
    return _BY_OPERATION.get(code)


def machine_exclusive_implied(resource_mode: str | None) -> bool:
    """MACHINE_BOUND implies exclusive machine interval — no separate stamp."""
    return (resource_mode or "").strip() == "MACHINE_BOUND"
