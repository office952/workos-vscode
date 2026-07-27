"""CostEngine company-level config service.

This module is READ-MOSTLY for the CostEngine: it loads the singleton
config row and aggregates live inputs from employees + recurring payments
into a `CostEngineBaseConfig` dict. It DOES NOT compute product cost.

Productive hours are calculated from Company Calendar − approved leave
(not manual per-employee `ore_productive_luna`).
"""
import logging
from datetime import date
from typing import Any, Dict, List, Optional

from models.cost_engine_config import CostEngineConfig
from services.employee_productive_hours import compute_productive_hours_by_employee
from services.employees import EmployeesService, is_valid_for_cost_engine
from services.recurring_payments import (
    RecurringPaymentsService,
    monthly_equivalent,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def load_base_currency(db: AsyncSession) -> str:
    """Return the canonical base currency from CostEngine settings (moneda_implicita)."""
    cfg = await CostEngineConfigService(db).get_or_create()
    raw = str(cfg.moneda_implicita or "RON").strip().upper()
    return raw or "RON"


class CostEngineConfigService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self) -> CostEngineConfig:
        """Return the singleton config row (id=1), creating it on first use."""
        result = await self.db.execute(select(CostEngineConfig).order_by(CostEngineConfig.id.asc()))
        row = result.scalars().first()
        if row is not None:
            return row
        row = CostEngineConfig(
            moneda_implicita="EUR",
            overhead_profile_name="default",
            metoda_overhead="pe_ora_productiva",
            allow_manual_override=False,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def update(self, update_data: Dict[str, Any]) -> CostEngineConfig:
        row = await self.get_or_create()
        for k, v in update_data.items():
            if hasattr(row, k) and k not in {"id", "created_at", "updated_at"}:
                setattr(row, k, v)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def compute_base_config(
        self,
        *,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Aggregate live inputs into the canonical `CostEngineBaseConfig` dict.

        NOTE: This is strictly an input-builder for CostEngine; the dict it
        returns contains NO product-specific math. A downstream consumer
        (CostEngine) is the sole authority to turn these inputs into an
        actual cost per product.

        Productive hours = Company Calendar workdays × 8 − approved leave × 8
        for the target month (defaults to current calendar month).
        """
        cfg = await self.get_or_create()
        warnings: List[str] = []
        today = date.today()
        target_year = int(year or today.year)
        target_month = int(month or today.month)

        employees_svc = EmployeesService(self.db)
        payments_svc = RecurringPaymentsService(self.db)

        # Effective-date capacity: productive employees with employment overlap
        # in the target month (hire/end dates), not only status==active today.
        month_contributors = await employees_svc.get_productive_contributors_for_month(
            target_year, target_month
        )

        # Per-row validity check. Invalid rows are EXCLUDED from the aggregates
        # and reported as warnings — never silently treated as zero.
        valid_employees = []
        for emp in month_contributors:
            # Mid-month leavers still contribute clipped hours; require cost.
            if emp.employee_type == "productive" and (
                emp.cost_lunar_firma is None or float(emp.cost_lunar_firma or 0) <= 0
            ):
                warnings.append(
                    f"employee_invalid:id={emp.id}:missing_cost_lunar_firma"
                )
                continue
            if emp.status == "active" and not is_valid_for_cost_engine(emp):
                warnings.append(
                    f"employee_invalid:id={emp.id}:missing_cost_lunar_firma"
                )
                continue
            valid_employees.append(emp)

        hours_by_id = await compute_productive_hours_by_employee(
            self.db,
            [e.id for e in valid_employees],
            year=target_year,
            month=target_month,
        )

        total_productive_hours = sum(float(hours_by_id.get(e.id, 0.0)) for e in valid_employees)
        total_productive_cost = sum(
            float(e.cost_lunar_firma or 0) for e in valid_employees
        )

        if total_productive_hours <= 0:
            average_labour_hour_cost: Optional[float] = None
            overhead_hour_cost: Optional[float] = None
            warnings.append("no_productive_hours_available")
        else:
            average_labour_hour_cost = round(total_productive_cost / total_productive_hours, 4)

        overhead_rows = await payments_svc.get_overhead_contributors()
        monthly_overhead_cost = round(sum(monthly_equivalent(r) for r in overhead_rows), 2)

        if total_productive_hours > 0:
            overhead_hour_cost = round(monthly_overhead_cost / total_productive_hours, 4)

        # Validity: we need productive hours AND a real labour rate to feed CostEngine.
        valid = (
            total_productive_hours > 0
            and average_labour_hour_cost is not None
            and average_labour_hour_cost > 0
        )

        return {
            "currency": cfg.moneda_implicita or "RON",
            "total_productive_hours_month": round(total_productive_hours, 2),
            "average_labour_hour_cost": average_labour_hour_cost or 0.0,
            "monthly_overhead_cost": monthly_overhead_cost,
            "overhead_hour_cost": overhead_hour_cost if total_productive_hours > 0 else 0.0,
            "valid": valid,
            "warnings": warnings,
            # Supplemental, for UI read-only display:
            "overhead_profile_name": cfg.overhead_profile_name,
            "metoda_overhead": cfg.metoda_overhead,
            "cost_ora_manopera_default": cfg.cost_ora_manopera_default,
            "allow_manual_override": bool(cfg.allow_manual_override),
            "productive_hours_source": "company_calendar_minus_approved_leave_clipped_employment",
            "productive_hours_year": target_year,
            "productive_hours_month": target_month,
        }
