"""Add basis-aware fields to workcenter_rates for linear-meter pricing.

Revision ID: s34_add_workcenter_rate_basis_fields
Revises: s33_rendered_output_snapshots
Create Date: 2026-05-31

Additive migration only:
- rate_basis (default per_hour, non-null)
- rate_per_linear_meter (nullable)
- is_active (default false, non-null)
- approval_reference (nullable)

No seed/data writes are performed beyond safe backfill for new non-null columns.
"""

from alembic import op
import sqlalchemy as sa


revision = "s34_add_workcenter_rate_basis_fields"
down_revision = "s33_rendered_output_snapshots"
branch_labels = None
depends_on = None


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {c["name"] for c in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("workcenter_rates"):
        return

    cols = _column_names(inspector, "workcenter_rates")

    if "rate_basis" not in cols:
        op.add_column(
            "workcenter_rates",
            sa.Column("rate_basis", sa.String(), nullable=False, server_default="per_hour"),
        )

    if "rate_per_linear_meter" not in cols:
        op.add_column(
            "workcenter_rates",
            sa.Column("rate_per_linear_meter", sa.Float(), nullable=True),
        )

    if "is_active" not in cols:
        op.add_column(
            "workcenter_rates",
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        )

    if "approval_reference" not in cols:
        op.add_column(
            "workcenter_rates",
            sa.Column("approval_reference", sa.String(), nullable=True),
        )

    # Backfill activation parity with legacy status for existing rows.
    op.execute(
        """
        UPDATE workcenter_rates
        SET is_active = CASE WHEN status = 'active' THEN TRUE ELSE FALSE END
        WHERE is_active IS NULL OR is_active != CASE WHEN status = 'active' THEN TRUE ELSE FALSE END
        """
    )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("workcenter_rates"):
        return

    cols = _column_names(inspector, "workcenter_rates")

    if "approval_reference" in cols:
        op.drop_column("workcenter_rates", "approval_reference")
    if "is_active" in cols:
        op.drop_column("workcenter_rates", "is_active")
    if "rate_per_linear_meter" in cols:
        op.drop_column("workcenter_rates", "rate_per_linear_meter")
    if "rate_basis" in cols:
        op.drop_column("workcenter_rates", "rate_basis")
