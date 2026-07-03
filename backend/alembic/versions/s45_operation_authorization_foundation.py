"""Operation authorization foundation — explicit employees + mapping extensions.

Adds operation_employee_authorizations junction table and extends
operation_resource_requirements with hybrid authorization metadata.

Revision ID: s45_operation_authorization_foundation
Revises: s44_field_installation_reporting
Create Date: 2026-06-10
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s45_operation_authorization_foundation"
down_revision: Union[str, Sequence[str], None] = "s44_field_installation_reporting"
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
    if not _column_exists("operation_resource_requirements", "authorization_mode"):
        op.add_column(
            "operation_resource_requirements",
            sa.Column(
                "authorization_mode",
                sa.String(),
                nullable=False,
                server_default=sa.text("'hybrid'"),
            ),
        )
    if not _column_exists("operation_resource_requirements", "default_resource_code"):
        op.add_column(
            "operation_resource_requirements",
            sa.Column("default_resource_code", sa.String(), nullable=True),
        )
    if not _column_exists("operation_resource_requirements", "product_system_aliases"):
        op.add_column(
            "operation_resource_requirements",
            sa.Column("product_system_aliases", sa.Text(), nullable=True),
        )

    if not _table_exists("operation_employee_authorizations"):
        op.create_table(
            "operation_employee_authorizations",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("operation_code", sa.String(), nullable=False),
            sa.Column("employee_id", sa.Integer(), nullable=False),
            sa.Column("authorization_type", sa.String(), nullable=False, server_default=sa.text("'explicit'")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
            sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "operation_code",
                "employee_id",
                name="uq_operation_employee_authorization",
            ),
        )
        op.create_index(
            "ix_operation_employee_authorizations_operation_code",
            "operation_employee_authorizations",
            ["operation_code"],
            unique=False,
        )
        op.create_index(
            "ix_operation_employee_authorizations_employee_id",
            "operation_employee_authorizations",
            ["employee_id"],
            unique=False,
        )


def downgrade() -> None:
    if _table_exists("operation_employee_authorizations"):
        op.drop_index("ix_operation_employee_authorizations_employee_id", table_name="operation_employee_authorizations")
        op.drop_index("ix_operation_employee_authorizations_operation_code", table_name="operation_employee_authorizations")
        op.drop_table("operation_employee_authorizations")

    if _column_exists("operation_resource_requirements", "product_system_aliases"):
        op.drop_column("operation_resource_requirements", "product_system_aliases")
    if _column_exists("operation_resource_requirements", "default_resource_code"):
        op.drop_column("operation_resource_requirements", "default_resource_code")
    if _column_exists("operation_resource_requirements", "authorization_mode"):
        op.drop_column("operation_resource_requirements", "authorization_mode")
