"""vector asset registry and svg metrics

Revision ID: s40_vector_asset_registry_svg_metrics
Revises: s39_commercial_markup_policies_foundation
Create Date: 2026-06-03 00:00:00.000000
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "s40_vector_asset_registry_svg_metrics"
down_revision = "s39_commercial_markup_policies_foundation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vector_assets",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column("asset_code", sa.String(), nullable=False),
        sa.Column("owner_type", sa.String(), nullable=False, server_default="standalone"),
        sa.Column("owner_id", sa.Integer(), nullable=True),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("bucket_name", sa.String(), nullable=False),
        sa.Column("object_key", sa.String(), nullable=False),
        sa.Column("source_format", sa.String(), nullable=False, server_default="svg"),
        sa.Column("content_type_reported", sa.String(), nullable=True),
        sa.Column("file_size_bytes", sa.Integer(), nullable=True),
        sa.Column("content_sha256", sa.String(), nullable=True),
        sa.Column("parse_status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("parse_warnings_json", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("parse_error_code", sa.String(), nullable=True),
        sa.Column("parse_error_detail", sa.Text(), nullable=True),
        sa.Column("bbox_w_mm", sa.Float(), nullable=True),
        sa.Column("bbox_h_mm", sa.Float(), nullable=True),
        sa.Column("area_mm2_approx", sa.Float(), nullable=True),
        sa.Column("perimeter_mm_approx", sa.Float(), nullable=True),
        sa.Column("metrics_version", sa.String(), nullable=False, server_default="v1"),
        sa.Column("created_by", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.CheckConstraint(
            "owner_type IN ('intake_request','product_template','standalone')",
            name="ck_vector_assets_owner_type",
        ),
        sa.CheckConstraint("source_format = 'svg'", name="ck_vector_assets_source_format_svg"),
        sa.CheckConstraint("parse_status IN ('pending','parsed','failed')", name="ck_vector_assets_parse_status"),
        sa.CheckConstraint(
            "file_size_bytes IS NULL OR file_size_bytes BETWEEN 1 AND 500000",
            name="ck_vector_assets_file_size_bytes",
        ),
    )
    op.create_index("ix_vector_assets_asset_code", "vector_assets", ["asset_code"], unique=True)
    op.create_index("ix_vector_assets_object_key", "vector_assets", ["object_key"], unique=True)
    op.create_index("ix_vector_assets_owner", "vector_assets", ["owner_type", "owner_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_vector_assets_owner", table_name="vector_assets")
    op.drop_index("ix_vector_assets_object_key", table_name="vector_assets")
    op.drop_index("ix_vector_assets_asset_code", table_name="vector_assets")
    op.drop_table("vector_assets")
