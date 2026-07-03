"""Read-only Intake V6 modular form contract endpoints."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from dependencies.auth import get_current_user
from schemas.intake_v6_modular_form import IntakeV6ModularFormContract
from services.intake_v6_modular_form_contract_service import (
    IntakeV6ModularFormContractService,
    get_intake_v6_modular_form_contract_service,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/intake-v6",
    tags=["intake-v6-modular-form"],
    dependencies=[Depends(get_current_user)],
)


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


def _service() -> IntakeV6ModularFormContractService:
    return get_intake_v6_modular_form_contract_service()


@router.get("/form-contract/{template_code}", response_model=IntakeV6ModularFormContract)
async def get_modular_form_contract(template_code: str) -> IntakeV6ModularFormContract:
    """Return modular Intake V6 form contract derived from mini-module registry (read-only)."""
    contract = _service().get_for_template(template_code)
    if contract is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope("form_contract_not_found", template_code=template_code),
        )
    return contract
