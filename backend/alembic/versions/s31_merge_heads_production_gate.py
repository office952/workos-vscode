"""Merge 3 Alembic heads into single production-ready chain.

Revision ID: s31_merge_heads_production_gate
Revises: s27_create_quote_output_snapshots, s30_execution_reality_invalidation_fields, 77f253fbb300
Create Date: 2026-05-19

This is a merge-only migration. It does NOT alter schema, add tables,
add columns, or modify data. Its sole purpose is to unify the 3 parallel
Alembic heads into a single linear chain so that `alembic upgrade head`
resolves to exactly one target revision.

Heads before merge:
  - s27_create_quote_output_snapshots (Branch A: main product/quote chain)
  - s30_execution_reality_invalidation_fields (Branch B: quote docs + stock + reality)
  - 77f253fbb300 (Branch C: orphan materials_json addition)

After this migration, the single head is: s31_merge_heads_production_gate
"""

from typing import Sequence, Union

from alembic import op  # noqa: F401
import sqlalchemy as sa  # noqa: F401


# revision identifiers, used by Alembic.
revision: str = "s31_merge_heads_production_gate"
down_revision: Union[str, Sequence[str], None] = (
    "s27_create_quote_output_snapshots",
    "s30_execution_reality_invalidation_fields",
    "77f253fbb300",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge only — no schema changes."""
    pass


def downgrade() -> None:
    """Merge only — no schema changes."""
    pass