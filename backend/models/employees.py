"""Employees model — canonical source for labour cost inputs in CostEngine.

Canonical rules (see `/workspace/workos_foundation_log.md`):
- This table is a DATA SOURCE, it does NOT perform cost calculations.
- Only employees with `employee_type='productive'` contribute to `cost_ora_manopera`.
- `cost_ora_calculat = cost_lunar_firma / ore_productive_luna` (calculated on read).
- Productive hours for CostEngine come from Company Calendar − approved leave
  (not manual `ore_productive_luna`), clipped to employment interval
  (`data_angajare` / `end_date`). Missing `cost_lunar_firma` on a productive
  contributor ⇒ invalid.
- Never hard-delete: resignations set `end_date` + status `ended`/`inactive`.
"""
from core.database import Base
from datetime import datetime
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text


class Employees(Base):
    __tablename__ = "employees"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=True)
    department = Column(String, nullable=True)  # a.k.a. workcenter
    # active | on_leave | sick | training | inactive | ended
    status = Column(String, nullable=False, default="active")
    employee_type = Column(String, nullable=False, default="productive")  # productive | indirect | administrative | management

    user_id = Column(String(255), nullable=True)         # optional link to users.id (OIDC sub)
    manager_employee_id = Column(
        Integer,
        ForeignKey("employees.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )  # formal direct manager (employee row), not user role
    cost_lunar_firma = Column(Float, nullable=True)      # total monthly company cost (CostEngine) — NOT internal pay
    monthly_internal_pay_amount = Column(Float, nullable=True)  # internal monthly pay for tranșe 15/30 (Plăți angajați)
    salary_currency = Column(String, nullable=False, default="RON")
    salary_period = Column(String, nullable=False, default="monthly")
    ore_lucru_luna = Column(Float, nullable=True)        # nominal hours of work per month
    ore_productive_luna = Column(Float, nullable=True)   # effective productive hours per month

    skills = Column(Text, nullable=True)                 # legacy JSON mirror; canonical = employee_skill_authorizations
    machines = Column(Text, nullable=True)               # legacy JSON mirror; canonical = employee_resource_authorizations
    data_angajare = Column(DateTime(timezone=True), nullable=True)  # hire / start_date
    end_date = Column(DateTime(timezone=True), nullable=True)  # resignation / termination — never hard-delete
    observatii = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
