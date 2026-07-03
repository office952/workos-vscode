"""Operational Workforce & Resource Registry foundation.

Extends employees with optional user link and explicit salary metadata.
Creates machines registry (if missing), M2M authorizations, operation
resource requirements, and field-installation team scaffolding.

Revision ID: s43_operational_resource_registry
Revises: s42_intake_persistence_handoff
Create Date: 2026-06-09
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s43_operational_resource_registry"
down_revision: Union[str, Sequence[str], None] = "s42_intake_persistence_handoff"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _column_exists(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(c["name"] == column_name for c in inspector.get_columns(table_name))


def upgrade() -> None:
    # --- Extend employees (global workforce record) ---
    if not _column_exists("employees", "user_id"):
        op.add_column("employees", sa.Column("user_id", sa.String(length=255), nullable=True))
    if not _column_exists("employees", "salary_currency"):
        op.add_column(
            "employees",
            sa.Column("salary_currency", sa.String(), nullable=False, server_default=sa.text("'RON'")),
        )
    if not _column_exists("employees", "salary_period"):
        op.add_column(
            "employees",
            sa.Column("salary_period", sa.String(), nullable=False, server_default=sa.text("'monthly'")),
        )

    # --- Machines / tools / work areas (canonical resource registry) ---
    if not _table_exists("machines"):
        op.create_table(
            "machines",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("machine_code", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("machine_type", sa.String(), nullable=False),
            sa.Column(
                "resource_kind",
                sa.String(),
                nullable=False,
                server_default=sa.text("'machine'"),
            ),
            sa.Column("workcenter_code", sa.String(), nullable=True),
            sa.Column(
                "operational_status",
                sa.String(),
                nullable=False,
                server_default=sa.text("'active'"),
            ),
            sa.Column("is_available", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
            sa.Column("manufacturer", sa.String(), nullable=True),
            sa.Column("model", sa.String(), nullable=True),
            sa.Column("year_acquired", sa.Integer(), nullable=True),
            sa.Column("capabilities", sa.Text(), nullable=True),
            sa.Column("capacity_metadata", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("machine_code"),
        )
        op.create_index("ix_machines_machine_code", "machines", ["machine_code"], unique=True)
    elif not _column_exists("machines", "resource_kind"):
        op.add_column(
            "machines",
            sa.Column(
                "resource_kind",
                sa.String(),
                nullable=False,
                server_default=sa.text("'machine'"),
            ),
        )

    # --- Employee authorizations (many-to-many, canonical codes) ---
    if not _table_exists("employee_skill_authorizations"):
        op.create_table(
            "employee_skill_authorizations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("employee_id", sa.Integer(), nullable=False),
            sa.Column("skill_code", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("employee_id", "skill_code", name="uq_employee_skill"),
        )
        op.create_index(
            "ix_employee_skill_authorizations_employee_id",
            "employee_skill_authorizations",
            ["employee_id"],
            unique=False,
        )

    if not _table_exists("employee_workcenter_authorizations"):
        op.create_table(
            "employee_workcenter_authorizations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("employee_id", sa.Integer(), nullable=False),
            sa.Column("workcenter_code", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("employee_id", "workcenter_code", name="uq_employee_workcenter"),
        )
        op.create_index(
            "ix_employee_workcenter_authorizations_employee_id",
            "employee_workcenter_authorizations",
            ["employee_id"],
            unique=False,
        )

    if not _table_exists("employee_resource_authorizations"):
        op.create_table(
            "employee_resource_authorizations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("employee_id", sa.Integer(), nullable=False),
            sa.Column("resource_code", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("employee_id", "resource_code", name="uq_employee_resource"),
        )
        op.create_index(
            "ix_employee_resource_authorizations_employee_id",
            "employee_resource_authorizations",
            ["employee_id"],
            unique=False,
        )

    # --- Operation -> resource requirements (Product Systems linkage prep) ---
    if not _table_exists("operation_resource_requirements"):
        op.create_table(
            "operation_resource_requirements",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("operation_code", sa.String(), nullable=False),
            sa.Column("required_skill_codes", sa.Text(), nullable=True),
            sa.Column("allowed_workcenter_codes", sa.Text(), nullable=True),
            sa.Column("allowed_resource_codes", sa.Text(), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("operation_code"),
        )
        op.create_index(
            "ix_operation_resource_requirements_operation_code",
            "operation_resource_requirements",
            ["operation_code"],
            unique=True,
        )

    # --- Field installation teams (montaj teren — multi-employee, no scheduling) ---
    if not _table_exists("field_installation_teams"):
        op.create_table(
            "field_installation_teams",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("installation_ref", sa.String(), nullable=False),
            sa.Column("status", sa.String(), nullable=False, server_default=sa.text("'draft'")),
            sa.Column("site_address", sa.Text(), nullable=True),
            sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_field_installation_teams_installation_ref",
            "field_installation_teams",
            ["installation_ref"],
            unique=False,
        )

    if not _table_exists("field_installation_team_members"):
        op.create_table(
            "field_installation_team_members",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("team_id", sa.Integer(), nullable=False),
            sa.Column("employee_id", sa.Integer(), nullable=False),
            sa.Column("role_on_site", sa.String(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(["team_id"], ["field_installation_teams.id"], ondelete="CASCADE"),
            sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("team_id", "employee_id", name="uq_field_installation_team_member"),
        )


def downgrade() -> None:
    if _table_exists("field_installation_team_members"):
        op.drop_table("field_installation_team_members")
    if _table_exists("field_installation_teams"):
        op.drop_table("field_installation_teams")
    if _table_exists("operation_resource_requirements"):
        op.drop_table("operation_resource_requirements")
    if _table_exists("employee_resource_authorizations"):
        op.drop_table("employee_resource_authorizations")
    if _table_exists("employee_workcenter_authorizations"):
        op.drop_table("employee_workcenter_authorizations")
    if _table_exists("employee_skill_authorizations"):
        op.drop_table("employee_skill_authorizations")
    if _column_exists("machines", "resource_kind"):
        op.drop_column("machines", "resource_kind")
    if _column_exists("employees", "salary_period"):
        op.drop_column("employees", "salary_period")
    if _column_exists("employees", "salary_currency"):
        op.drop_column("employees", "salary_currency")
    if _column_exists("employees", "user_id"):
        op.drop_column("employees", "user_id")
