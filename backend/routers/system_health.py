"""
BUILD 20 — System Environment Readiness Endpoint.

GET /api/v1/system/environment-readiness

Read-only, admin-only endpoint that returns environment safety status.
Does NOT expose secrets, tokens, or connection strings.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from dependencies.permissions import require_permission
from core.startup_safety import run_startup_safety_checks, CheckStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/system", tags=["system"])


class SafetyCheckResponse(BaseModel):
    name: str
    status: CheckStatus
    message: str


class EnvironmentReadinessResponse(BaseModel):
    environment: str
    overall_status: CheckStatus
    checks: List[SafetyCheckResponse]


@router.get(
    "/environment-readiness",
    response_model=EnvironmentReadinessResponse,
    dependencies=[Depends(require_permission("settings.view"))],
)
async def get_environment_readiness() -> EnvironmentReadinessResponse:
    """
    Return environment readiness report.

    Admin-only. Does not expose secrets.
    Returns PASS/WARNING/BLOCKED for each safety check.
    """
    report = run_startup_safety_checks()
    return EnvironmentReadinessResponse(
        environment=report.environment,
        overall_status=report.overall_status,
        checks=[
            SafetyCheckResponse(
                name=c.name,
                status=c.status,
                message=c.message,
            )
            for c in report.checks
        ],
    )