"""Add employees.end_date for resignations / terminations (no hard delete).

Revision ID: s59_employee_end_date_lifecycle
Revises: s58_create_execution_task_help_requests
Create Date: 2026-07-27
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s59_employee_end_date_lifecycle"
down_revision: Union[str, Sequence[str], None] = "s58_create_execution_task_help_requests"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("employees", schema=None) as batch_op:
        batch_op.add_column(sa.Column("end_date", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("employees", schema=None) as batch_op:
        batch_op.drop_column("end_date")
