"""BUILD 16: Add stock_movements table for inventory operational loop.

Revision ID: s29_stock_movements
Revises: s28_quote_documents_archive
Create Date: 2026-05-18
"""

from alembic import op
import sqlalchemy as sa

revision = "s29_stock_movements"
down_revision = "s28_quote_documents_archive"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_movements",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("material_id", sa.Integer(), nullable=False),
        sa.Column("source_type", sa.String(), nullable=False),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("order_id", sa.Integer(), nullable=True),
        sa.Column("task_id", sa.String(), nullable=True),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(), nullable=False),
        sa.Column("movement_type", sa.String(), nullable=False),
        sa.Column("old_stock", sa.Float(), nullable=False),
        sa.Column("new_stock", sa.Float(), nullable=False),
        sa.Column("performed_by", sa.String(), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.String(), nullable=True),
        sa.Column("idempotency_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_stock_movements_idempotency"),
    )
    op.create_index(op.f("ix_stock_movements_id"), "stock_movements", ["id"])
    op.create_index(op.f("ix_stock_movements_material_id"), "stock_movements", ["material_id"])


def downgrade() -> None:
    op.drop_constraint("uq_stock_movements_idempotency", "stock_movements", type_="unique")
    op.drop_index(op.f("ix_stock_movements_material_id"), table_name="stock_movements")
    op.drop_index(op.f("ix_stock_movements_id"), table_name="stock_movements")
    op.drop_table("stock_movements")