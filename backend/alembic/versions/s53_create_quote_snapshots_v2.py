"""create quote_snapshots_v2 table for dual quote snapshot persistence

Revision ID: s53_create_quote_snapshots_v2
Revises: s52_add_intake_v3_workspaces
Create Date: 2026-06-30 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s53_create_quote_snapshots_v2"
down_revision = "s52_add_intake_v3_workspaces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quote_snapshots_v2",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("snapshot_code", sa.String(), nullable=False),
        sa.Column("snapshot_version", sa.String(), nullable=False, server_default="1.0.0"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("quote_id", sa.Integer(), nullable=True),
        sa.Column("workspace_id", sa.String(length=36), nullable=True),
        sa.Column("template_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("readiness", sa.String(), nullable=False),
        sa.Column("frozen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("frozen_by", sa.String(), nullable=True),
        sa.Column("snapshot_json", sa.Text(), nullable=False),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("superseded_by_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.create_index("ix_quote_snapshots_v2_snapshot_code", "quote_snapshots_v2", ["snapshot_code"], unique=True)
    op.create_index("ix_quote_snapshots_v2_quote_id", "quote_snapshots_v2", ["quote_id"], unique=False)
    op.create_index("ix_quote_snapshots_v2_workspace_id", "quote_snapshots_v2", ["workspace_id"], unique=False)
    op.create_index("ix_quote_snapshots_v2_status", "quote_snapshots_v2", ["status"], unique=False)
    op.create_index(
        "ix_quote_snapshots_v2_quote_id_version",
        "quote_snapshots_v2",
        ["quote_id", "version"],
        unique=False,
    )
    op.create_index(
        "ix_quote_snapshots_v2_workspace_id_version",
        "quote_snapshots_v2",
        ["workspace_id", "version"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_quote_snapshots_v2_workspace_id_version", table_name="quote_snapshots_v2")
    op.drop_index("ix_quote_snapshots_v2_quote_id_version", table_name="quote_snapshots_v2")
    op.drop_index("ix_quote_snapshots_v2_status", table_name="quote_snapshots_v2")
    op.drop_index("ix_quote_snapshots_v2_workspace_id", table_name="quote_snapshots_v2")
    op.drop_index("ix_quote_snapshots_v2_quote_id", table_name="quote_snapshots_v2")
    op.drop_index("ix_quote_snapshots_v2_snapshot_code", table_name="quote_snapshots_v2")
    op.drop_table("quote_snapshots_v2")
