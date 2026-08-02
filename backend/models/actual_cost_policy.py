"""Persistent facts for Actual Cost Policy Runtime V1.

These tables store standard role/skill cost policy and frozen execution actuals.
They intentionally never store employee salary or client tariff data.
"""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, UniqueConstraint

from core.database import Base


class RoleSkillLaborCostPolicy(Base):
    __tablename__ = "role_skill_labor_cost_policies"
    __table_args__ = (
        UniqueConstraint(
            "role_code",
            "skill_code",
            "effective_from",
            name="uq_role_skill_labor_policy_start",
        ),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_code = Column(String, nullable=False, index=True)
    skill_code = Column(String, nullable=True, index=True)
    standard_internal_rate = Column(Float, nullable=False)
    rate_unit = Column(String, nullable=False, default="hour")
    currency = Column(String, nullable=False)
    effective_from = Column(DateTime(timezone=True), nullable=False, index=True)
    effective_to = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, nullable=False, default=True)
    provenance = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now, onupdate=datetime.now)
    version = Column(Integer, nullable=False, default=1)


class ActualLaborCostLine(Base):
    __tablename__ = "actual_labor_cost_lines"
    __table_args__ = (
        UniqueConstraint("order_id", "session_ref", name="uq_actual_labor_cost_line_session"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False, index=True)
    task_id = Column(String, nullable=False)
    session_ref = Column(String, nullable=False)
    employee_id = Column(Integer, nullable=False)
    role_code = Column(String, nullable=False)
    skill_code = Column(String, nullable=True)
    duration_seconds = Column(Integer, nullable=False)
    rate_used = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    labor_cost_amount = Column(Float, nullable=False)
    policy_id = Column(Integer, nullable=False)
    policy_version = Column(Integer, nullable=False)
    computed_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    freeze_status = Column(String, nullable=False, default="frozen")


class ExecutionJobClosure(Base):
    __tablename__ = "execution_job_closures"
    __table_args__ = ({"extend_existing": True},)

    order_id = Column(Integer, primary_key=True)
    status = Column(String, nullable=False, default="open")
    closed_at = Column(DateTime(timezone=True), nullable=True)
    closed_by = Column(String, nullable=True)
    reopen_at = Column(DateTime(timezone=True), nullable=True)
    reopen_by = Column(String, nullable=True)
    reopen_reason = Column(String, nullable=True)
    checklist_json = Column(Text, nullable=False, default="{}")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now, onupdate=datetime.now)


class ExecutionJobClosureEvent(Base):
    __tablename__ = "execution_job_closure_events"
    __table_args__ = ({"extend_existing": True},)

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, nullable=False, index=True)
    event_type = Column(String, nullable=False)
    actor_id = Column(String, nullable=False)
    reason = Column(String, nullable=True)
    checklist_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.now)
