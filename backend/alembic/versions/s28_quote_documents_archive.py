"""BUILD 15 — Create quote_documents_archive table.

Revision ID: s28_quote_documents_archive
Revises: 1588bf4744d8
Create Date: 2026-05-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "s28_quote_documents_archive"
down_revision: Union[str, Sequence[str], None] = "1588bf4744d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create quote_documents_archive table."""
    op.create_table(
        "quote_documents_archive",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("quote_id", sa.Integer(), nullable=False),
        sa.Column("quote_code", sa.String(), nullable=False),
        sa.Column("quote_version", sa.Integer(), nullable=False),
        sa.Column("document_type", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("content_hash", sa.String(), nullable=True),
        sa.Column("generated_by", sa.String(), nullable=True),
        sa.Column("source_snapshot_id", sa.Integer(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_quote_documents_archive_quote_id"),
        "quote_documents_archive",
        ["quote_id"],
        unique=False,
    )


def downgrade() -> None:
    """Drop quote_documents_archive table."""
    op.drop_index(
        op.f("ix_quote_documents_archive_quote_id"),
        table_name="quote_documents_archive",
    )
    op.drop_table("quote_documents_archive")