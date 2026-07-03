"""add intake v3 workspaces draft persistence table

Revision ID: s52_add_intake_v3_workspaces
Revises: s51_employee_manager_employee_id
Create Date: 2026-06-18 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s52_add_intake_v3_workspaces"
down_revision = "s51_employee_manager_employee_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "intake_v3_workspaces",
        sa.Column("id", sa.String(length=36), primary_key=True, nullable=False),
        sa.Column("workspace_code", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("template_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="draft"),
        sa.Column("payload_json", sa.Text(), nullable=False),
        sa.Column("preview_snapshot_json", sa.Text(), nullable=True),
        sa.Column("readiness_status", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", sa.String(), nullable=True),
        sa.Column("updated_by_user_id", sa.String(), nullable=True),
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
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_intake_v3_workspaces_workspace_code", "intake_v3_workspaces", ["workspace_code"], unique=True)
    op.create_index("ix_intake_v3_workspaces_template_code", "intake_v3_workspaces", ["template_code"], unique=False)
    op.create_index("ix_intake_v3_workspaces_status", "intake_v3_workspaces", ["status"], unique=False)
    op.create_index("ix_intake_v3_workspaces_created_at", "intake_v3_workspaces", ["created_at"], unique=False)
    op.create_index(
        "ix_intake_v3_workspaces_created_by_user_id",
        "intake_v3_workspaces",
        ["created_by_user_id"],
        unique=False,
    )
    op.create_index("ix_intake_v3_workspaces_archived_at", "intake_v3_workspaces", ["archived_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_intake_v3_workspaces_archived_at", table_name="intake_v3_workspaces")
    op.drop_index("ix_intake_v3_workspaces_created_by_user_id", table_name="intake_v3_workspaces")
    op.drop_index("ix_intake_v3_workspaces_created_at", table_name="intake_v3_workspaces")
    op.drop_index("ix_intake_v3_workspaces_status", table_name="intake_v3_workspaces")
    op.drop_index("ix_intake_v3_workspaces_template_code", table_name="intake_v3_workspaces")
    op.drop_index("ix_intake_v3_workspaces_workspace_code", table_name="intake_v3_workspaces")
    op.drop_table("intake_v3_workspaces")
