"""Owner read-only Product / Price / Tasking proof — GET only, zero writes."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from dependencies.auth import get_current_user
from schemas.owner_readonly_volumetric_proof import OwnerReadonlyVolumetricProof
from services.owner_readonly_volumetric_proof_service import build_owner_readonly_volumetric_proof
from services.template_architecture_scope import require_canonical_template_code

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/product-system",
    tags=["owner-readonly-proof"],
    dependencies=[Depends(get_current_user)],
)


def _error_envelope(error: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"error": error}
    body.update(kwargs)
    return body


@router.get(
    "/owner-readonly-proof/{template_code}",
    response_model=OwnerReadonlyVolumetricProof,
)
async def get_owner_readonly_volumetric_proof(
    template_code: str,
    workspace_id: str = Query(..., description="Intake V6 workspace id"),
    db: AsyncSession = Depends(get_db),
) -> OwnerReadonlyVolumetricProof:
    """
    Compose Intake → ProductDefinition → modular task_rules → live materials → Build 4C preview.

    Read-only. Does not persist snapshots, ExecutionPlan, or execution_tasks.
    Does not invent a new tasking system — projects Aggregate.task_contract only.
    """
    identity = require_canonical_template_code(template_code)
    if identity.resolution_type == "rejected_alias":
        raise HTTPException(
            status_code=422,
            detail=_error_envelope(
                "template_identity_not_canonical",
                requested_template_code=identity.requested_template_code,
            ),
        )

    proof = await build_owner_readonly_volumetric_proof(
        db,
        template_code=identity.canonical_template_code,
        workspace_id=workspace_id,
    )
    if proof is None:
        raise HTTPException(
            status_code=404,
            detail=_error_envelope(
                "owner_proof_unavailable",
                template_code=template_code,
                workspace_id=workspace_id,
                hint="Volumetric letters workspace required",
            ),
        )
    logger.info(
        "GET owner-readonly-proof template=%s workspace=%s chain_ok=%s",
        proof.template_code,
        workspace_id,
        proof.chain_ok,
    )
    return proof
