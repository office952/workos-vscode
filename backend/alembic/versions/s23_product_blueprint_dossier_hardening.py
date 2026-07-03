"""Sprint #23 — Product Blueprint Dossier Phase B Hardening.

Creates the product_blueprint_dossier table (if not exists) and adds
FK constraint on template_id -> product_templates.id with ON DELETE RESTRICT.

This migration is idempotent: if the table already exists (from
Base.metadata.create_all() in dev), it adds only the FK constraint.

Revision ID: s23_dossier_hardening
Revises: s22_materials_capture
Create Date: 2026-05-12
"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "s23_dossier_hardening"
down_revision: Union[str, Sequence[str], None] = "s22_materials_capture"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _fk_exists(table_name: str, fk_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    fks = inspector.get_foreign_keys(table_name)
    return any(fk.get("name") == fk_name for fk in fks)


def upgrade() -> None:
    # Step 1: Create table if it does not exist (idempotent for dev environments)
    if not _table_exists("product_blueprint_dossier"):
        op.create_table(
            "product_blueprint_dossier",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("template_id", sa.Integer(), nullable=False),
            sa.Column("template_code", sa.String(), nullable=False),
            sa.Column("dossier_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("status", sa.String(), nullable=False, server_default="draft"),
            sa.Column("sections_json", sa.String(), nullable=True),
            sa.Column("variants_json", sa.String(), nullable=True),
            sa.Column("layers_json", sa.String(), nullable=True),
            sa.Column("task_rules_json", sa.String(), nullable=True),
            sa.Column("time_assumptions_json", sa.String(), nullable=True),
            sa.Column("costengine_mapping_json", sa.String(), nullable=True),
            sa.Column("quote_readiness_json", sa.String(), nullable=True),
            sa.Column("output_blocks_json", sa.String(), nullable=True),
            sa.Column("visual_prompt_blocks_json", sa.String(), nullable=True),
            sa.Column("production_notes_json", sa.String(), nullable=True),
            sa.Column("qc_checkpoints_json", sa.String(), nullable=True),
            sa.Column("risks_json", sa.String(), nullable=True),
            sa.Column("completion_state_json", sa.String(), nullable=True),
            sa.Column("owner_role", sa.String(), nullable=True),
            sa.Column("reviewer_role", sa.String(), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        )
        op.create_index("ix_product_blueprint_dossier_id", "product_blueprint_dossier", ["id"])
        op.create_index(
            "ix_product_blueprint_dossier_template_id",
            "product_blueprint_dossier",
            ["template_id"],
            unique=True,
        )

    # Step 2: Add FK constraint (idempotent — skip if already present)
    fk_name = "fk_dossier_template_id"
    if not _fk_exists("product_blueprint_dossier", fk_name):
        with op.batch_alter_table("product_blueprint_dossier") as batch_op:
            batch_op.create_foreign_key(
                fk_name,
                "product_templates",
                ["template_id"],
                ["id"],
                ondelete="RESTRICT",
            )


def downgrade() -> None:
    # Remove FK constraint first, then drop table
    fk_name = "fk_dossier_template_id"
    if _table_exists("product_blueprint_dossier"):
        if _fk_exists("product_blueprint_dossier", fk_name):
            with op.batch_alter_table("product_blueprint_dossier") as batch_op:
                batch_op.drop_constraint(fk_name, type_="foreignkey")
        op.drop_table("product_blueprint_dossier")