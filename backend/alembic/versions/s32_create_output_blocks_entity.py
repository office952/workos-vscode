"""Create output_blocks table for BUILD 27.06 OutputBlock entity contract.

Revision ID: s32_create_output_blocks_entity
Revises: s31_merge_heads_production_gate
Create Date: 2026-05-27
"""

from alembic import op
import sqlalchemy as sa


revision = "s32_create_output_blocks_entity"
down_revision = "s31_merge_heads_production_gate"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("output_blocks"):
        op.create_table(
            "output_blocks",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("block_id", sa.String(), nullable=False),
            sa.Column("block_type", sa.String(), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("purpose", sa.Text(), nullable=True),
            sa.Column("audience", sa.String(), nullable=False),
            sa.Column("document_type", sa.String(), nullable=False),
            sa.Column("source_fields", sa.Text(), nullable=False),
            sa.Column("variables", sa.Text(), nullable=False),
            sa.Column("template_text", sa.Text(), nullable=False),
            sa.Column("conditions", sa.Text(), nullable=True),
            sa.Column("approval_status", sa.String(), nullable=False, server_default="draft"),
            sa.Column("version", sa.String(), nullable=False, server_default="v1"),
            sa.Column("owner_role", sa.String(), nullable=True),
            sa.Column("reviewer_role", sa.String(), nullable=True),
            sa.Column("snapshot_policy", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("output_blocks")}
    if "ix_output_blocks_block_id" not in existing_indexes:
        op.create_index("ix_output_blocks_block_id", "output_blocks", ["block_id"], unique=True)
    if "ix_output_blocks_approval_status" not in existing_indexes:
        op.create_index("ix_output_blocks_approval_status", "output_blocks", ["approval_status"], unique=False)
    if "ix_output_blocks_block_type" not in existing_indexes:
        op.create_index("ix_output_blocks_block_type", "output_blocks", ["block_type"], unique=False)
    if "ix_output_blocks_document_type" not in existing_indexes:
        op.create_index("ix_output_blocks_document_type", "output_blocks", ["document_type"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("output_blocks"):
        existing_indexes = {idx["name"] for idx in inspector.get_indexes("output_blocks")}
        if "ix_output_blocks_document_type" in existing_indexes:
            op.drop_index("ix_output_blocks_document_type", table_name="output_blocks")
        if "ix_output_blocks_block_type" in existing_indexes:
            op.drop_index("ix_output_blocks_block_type", table_name="output_blocks")
        if "ix_output_blocks_approval_status" in existing_indexes:
            op.drop_index("ix_output_blocks_approval_status", table_name="output_blocks")
        if "ix_output_blocks_block_id" in existing_indexes:
            op.drop_index("ix_output_blocks_block_id", table_name="output_blocks")
        op.drop_table("output_blocks")