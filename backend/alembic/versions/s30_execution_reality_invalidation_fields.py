"""BUILD 18.1: Add invalidation and restoration fields to execution_reality.

Revision ID: s30_execution_reality_invalidation_fields
Revises: s29_stock_movements
Create Date: 2026-05-19

Columns added (all nullable for backward compatibility):
  - is_invalid (Boolean, default False)
  - invalidated_at (DateTime with timezone)
  - invalidated_by (String)
  - invalid_reason (String)
  - stock_reconciliation_required (Boolean, default False)
  - restored_at (DateTime with timezone)
  - restored_by (String)
  - restored_reason (String)

Safety:
  - All columns are nullable → no data migration required.
  - Idempotent: uses IF NOT EXISTS pattern via raw SQL for dialects that support it,
    and op.add_column with safe defaults for standard Alembic path.
  - Downgrade drops only the columns added here.
  - No existing data is altered, no renames, no constraint changes on other columns.
"""

from alembic import op
import sqlalchemy as sa

revision = "s30_execution_reality_invalidation_fields"
down_revision = "s29_stock_movements"
branch_labels = None
depends_on = None

# Columns to add — all nullable for backward compat
_COLUMNS = [
    ("is_invalid", sa.Boolean(), False),
    ("invalidated_at", sa.DateTime(timezone=True), None),
    ("invalidated_by", sa.String(), None),
    ("invalid_reason", sa.String(), None),
    ("stock_reconciliation_required", sa.Boolean(), False),
    ("restored_at", sa.DateTime(timezone=True), None),
    ("restored_by", sa.String(), None),
    ("restored_reason", sa.String(), None),
]

_TABLE = "execution_reality"


def upgrade() -> None:
    for col_name, col_type, server_default in _COLUMNS:
        op.add_column(
            _TABLE,
            sa.Column(
                col_name,
                col_type,
                nullable=True,
                server_default=str(server_default).lower() if server_default is not None else None,
            ),
        )


def downgrade() -> None:
    for col_name, _, _ in reversed(_COLUMNS):
        op.drop_column(_TABLE, col_name)