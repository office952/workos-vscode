"""Add formal manager reporting link on employees.

Revision ID: s51_employee_manager_employee_id
Revises: s50_employee_payment_records
Create Date: 2026-06-12
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s51_employee_manager_employee_id"
down_revision: Union[str, Sequence[str], None] = "s50_employee_payment_records"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("employees", schema=None) as batch_op:
        batch_op.add_column(sa.Column("manager_employee_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_employees_manager_employee_id",
            "employees",
            ["manager_employee_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_employees_manager_employee_id", ["manager_employee_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("employees", schema=None) as batch_op:
        batch_op.drop_index("ix_employees_manager_employee_id")
        batch_op.drop_constraint("fk_employees_manager_employee_id", type_="foreignkey")
        batch_op.drop_column("manager_employee_id")
