"""CostEngine company config + aggregated base-config endpoint.

`GET /api/v1/cost-engine/base-config` is the ONLY endpoint CostEngine
consumers should use to pull labour + overhead inputs. It performs NO
product-level math."""
import logging
from typing import List, Optional

from core.database import get_db
from dependencies.auth import get_current_user
from dependencies.permissions import require_permission
from schemas.auth import UserResponse
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from services.cost_engine_config import CostEngineConfigService
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/cost-engine",
    tags=["cost-engine"],
    dependencies=[Depends(get_current_user)],
)


class CostEngineConfigData(BaseModel):
    moneda_implicita: Optional[str] = None
    ore_productive_luna_firma: Optional[float] = None
    overhead_profile_name: Optional[str] = None
    metoda_overhead: Optional[str] = None
    cost_ora_manopera_default: Optional[float] = None
    allow_manual_override: Optional[bool] = None


class CostEngineConfigResponse(BaseModel):
    id: int
    moneda_implicita: str
    ore_productive_luna_firma: Optional[float] = None
    overhead_profile_name: str
    metoda_overhead: str
    cost_ora_manopera_default: Optional[float] = None
    allow_manual_override: bool

    class Config:
        from_attributes = True


class CostEngineBaseConfigResponse(BaseModel):
    currency: str
    total_productive_hours_month: float
    average_labour_hour_cost: float
    monthly_overhead_cost: float
    overhead_hour_cost: float
    valid: bool
    warnings: List[str]
    overhead_profile_name: Optional[str] = None
    metoda_overhead: Optional[str] = None
    cost_ora_manopera_default: Optional[float] = None
    allow_manual_override: Optional[bool] = None


@router.get("/config", response_model=CostEngineConfigResponse)
async def get_config(db: AsyncSession = Depends(get_db)):
    svc = CostEngineConfigService(db)
    row = await svc.get_or_create()
    return row


@router.put("/config", response_model=CostEngineConfigResponse)
async def update_config(data: CostEngineConfigData, db: AsyncSession = Depends(get_db), _user: UserResponse = Depends(require_permission("cost_engine.update"))):
    svc = CostEngineConfigService(db)
    row = await svc.update(data.model_dump(exclude_none=True))
    return row


@router.get("/base-config", response_model=CostEngineBaseConfigResponse)
async def get_base_config(db: AsyncSession = Depends(get_db)):
    """Return the aggregated CostEngine input config (labour + overhead)."""
    svc = CostEngineConfigService(db)
    result = await svc.compute_base_config()
    return result