"""Create rendered_output_snapshots table for BUILD 27.08.

Revision ID: s33_rendered_output_snapshots
Revises: s32_create_output_blocks_entity

Additive, idempotent migration for canonical rendered OutputBlock snapshots.
Does not modify quotes, orders, quote_output_snapshots, or order references.
"""

from alembic import op
import sqlalchemy as sa


revision = "s33_rendered_output_snapshots"
down_revision = "s32_create_output_blocks_entity"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("rendered_output_snapshots"):
        op.create_table(
            "rendered_output_snapshots",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("snapshot_uid", sa.String(), nullable=False),
            sa.Column("context", sa.String(), nullable=False),
            sa.Column("document_type", sa.String(), nullable=False),
            sa.Column("audience", sa.String(), nullable=False),
            sa.Column("snapshot_purpose", sa.String(), nullable=False),
            sa.Column("target_type", sa.String(), nullable=True),
            sa.Column("target_id", sa.String(), nullable=True),
            sa.Column("source_payload_json", sa.Text(), nullable=False),
            sa.Column("source_payload_hash", sa.String(), nullable=True),
            sa.Column("rendered_blocks_json", sa.Text(), nullable=False),
            sa.Column("warnings_json", sa.Text(), nullable=True),
            sa.Column("blockers_json", sa.Text(), nullable=True),
            sa.Column("status", sa.String(), nullable=False, server_default="created"),
            sa.Column("created_by", sa.String(), nullable=True),
            sa.Column("trace_json", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )

    existing_indexes = {idx["name"] for idx in inspector.get_indexes("rendered_output_snapshots")}
    if "ix_rendered_output_snapshots_snapshot_uid" not in existing_indexes:
        op.create_index(
            "ix_rendered_output_snapshots_snapshot_uid",
            "rendered_output_snapshots",
            ["snapshot_uid"],
            unique=True,
        )
    if "ix_rendered_output_snapshots_id" not in existing_indexes:
        op.create_index("ix_rendered_output_snapshots_id", "rendered_output_snapshots", ["id"], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if inspector.has_table("rendered_output_snapshots"):
        existing_indexes = {idx["name"] for idx in inspector.get_indexes("rendered_output_snapshots")}
        if "ix_rendered_output_snapshots_snapshot_uid" in existing_indexes:
            op.drop_index("ix_rendered_output_snapshots_snapshot_uid", table_name="rendered_output_snapshots")
        if "ix_rendered_output_snapshots_id" in existing_indexes:
            op.drop_index("ix_rendered_output_snapshots_id", table_name="rendered_output_snapshots")
        op.drop_table("rendered_output_snapshots")
