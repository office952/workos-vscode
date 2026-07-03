"""Operational Workforce & Resource Registry ORM models.

Canonical many-to-many authorizations and operation resource mappings.
Machines table doubles as the unified resource registry (machine/tool/work_area).
"""
from datetime import datetime

from core.database import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint


class MachineRegistry(Base):
    __tablename__ = "machines"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True, autoincrement=True, nullable=False)
    machine_code = Column(String, nullable=False, unique=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    machine_type = Column(String, nullable=False)
    resource_kind = Column(String, nullable=False, default="machine")  # machine | tool | work_area
    workcenter_code = Column(String, nullable=True)
    operational_status = Column(String, nullable=False, default="active")
    is_available = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    manufacturer = Column(String, nullable=True)
    model = Column(String, nullable=True)
    year_acquired = Column(Integer, nullable=True)
    capabilities = Column(Text, nullable=True)
    capacity_metadata = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)


class EmployeeSkillAuthorization(Base):
    __tablename__ = "employee_skill_authorizations"
    __table_args__ = (
        UniqueConstraint("employee_id", "skill_code", name="uq_employee_skill"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    skill_code = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now)


class EmployeeWorkcenterAuthorization(Base):
    __tablename__ = "employee_workcenter_authorizations"
    __table_args__ = (
        UniqueConstraint("employee_id", "workcenter_code", name="uq_employee_workcenter"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    workcenter_code = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now)


class EmployeeResourceAuthorization(Base):
    __tablename__ = "employee_resource_authorizations"
    __table_args__ = (
        UniqueConstraint("employee_id", "resource_code", name="uq_employee_resource"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_code = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now)


class OperationResourceRequirement(Base):
    __tablename__ = "operation_resource_requirements"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    operation_code = Column(String, nullable=False, unique=True, index=True)
    required_skill_codes = Column(Text, nullable=True)
    allowed_workcenter_codes = Column(Text, nullable=True)
    allowed_resource_codes = Column(Text, nullable=True)
    authorization_mode = Column(String, nullable=False, default="hybrid")  # skill | explicit | hybrid
    default_resource_code = Column(String, nullable=True)
    product_system_aliases = Column(Text, nullable=True)  # JSON list of ProductSystem/dossier codes
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)


class OperationEmployeeAuthorization(Base):
    __tablename__ = "operation_employee_authorizations"
    __table_args__ = (
        UniqueConstraint("operation_code", "employee_id", name="uq_operation_employee_authorization"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    operation_code = Column(String, nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True)
    authorization_type = Column(String, nullable=False, default="explicit")
    created_at = Column(DateTime(timezone=True), default=datetime.now)


class FieldInstallationTeam(Base):
    __tablename__ = "field_installation_teams"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    installation_ref = Column(String, nullable=False, index=True)
    status = Column(String, nullable=False, default="draft")
    site_address = Column(Text, nullable=True)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    client_observations = Column(Text, nullable=True)
    reporting_json = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)


class FieldInstallationTeamMember(Base):
    __tablename__ = "field_installation_team_members"
    __table_args__ = (
        UniqueConstraint("team_id", "employee_id", name="uq_field_installation_team_member"),
        {"extend_existing": True},
    )

    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    team_id = Column(Integer, ForeignKey("field_installation_teams.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    role_on_site = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
