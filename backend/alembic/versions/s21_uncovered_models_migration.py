"""Sprint #21 — Alembic migration for uncovered models.

AUDIT FIX (Task 14): Creates tables for models that were defined in
`app/backend/models/` but never had corresponding Alembic migrations:
  1. employees
  2. cost_engine_config
  3. execution_observation_config
  4. execution_plan
  5. execution_reality
  6. product_families
  7. recurring_payments

Note: auth models (users, oidc_states, sessions) are excluded from Alembic
per env.py `alembic_include_object` — they are managed by the platform.

This migration is idempotent: if `init_db()` auto-created tables via ORM
metadata in earlier environments, the migration detects and skips creation.

Revision ID: s21_uncovered_models
Revises: s20_workcenter_rates
Create Date: 2026-05-12

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "s21_uncovered_models"
down_revision: Union[str, Sequence[str], None] = "s20_workcenter_rates"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(table_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return table_name in inspector.get_table_names()


def _index_exists(table_name: str, index_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if table_name not in inspector.get_table_names():
        return False
    return any(i["name"] == index_name for i in inspector.get_indexes(table_name))


def upgrade() -> None:
    """Upgrade schema (idempotent)."""

    # --- 1. employees ---
    if not _table_exists("employees"):
        op.create_table(
            "employees",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column("role", sa.String(), nullable=True),
            sa.Column("department", sa.String(), nullable=True),
            sa.Column(
                "status",
                sa.String(),
                nullable=False,
                server_default=sa.text("'active'"),
            ),
            sa.Column(
                "employee_type",
                sa.String(),
                nullable=False,
                server_default=sa.text("'productive'"),
            ),
            sa.Column("cost_lunar_firma", sa.Float(), nullable=True),
            sa.Column("ore_lucru_luna", sa.Float(), nullable=True),
            sa.Column("ore_productive_luna", sa.Float(), nullable=True),
            sa.Column("skills", sa.Text(), nullable=True),
            sa.Column("machines", sa.Text(), nullable=True),
            sa.Column("data_angajare", sa.DateTime(timezone=True), nullable=True),
            sa.Column("observatii", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index("ix_employees_id", "employees", ["id"], unique=False)

    # --- 2. cost_engine_config ---
    if not _table_exists("cost_engine_config"):
        op.create_table(
            "cost_engine_config",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column(
                "moneda_implicita",
                sa.String(),
                nullable=False,
                server_default=sa.text("'RON'"),
            ),
            sa.Column("ore_productive_luna_firma", sa.Float(), nullable=True),
            sa.Column(
                "overhead_profile_name",
                sa.String(),
                nullable=False,
                server_default=sa.text("'default'"),
            ),
            sa.Column(
                "metoda_overhead",
                sa.String(),
                nullable=False,
                server_default=sa.text("'pe_ora_productiva'"),
            ),
            sa.Column("cost_ora_manopera_default", sa.Float(), nullable=True),
            sa.Column(
                "allow_manual_override",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_cost_engine_config_id", "cost_engine_config", ["id"], unique=False
        )

    # --- 3. execution_observation_config ---
    if not _table_exists("execution_observation_config"):
        op.create_table(
            "execution_observation_config",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column(
                "warning_time_delta_pct",
                sa.Float(),
                nullable=False,
                server_default=sa.text("15.0"),
            ),
            sa.Column(
                "critical_time_delta_pct",
                sa.Float(),
                nullable=False,
                server_default=sa.text("35.0"),
            ),
            sa.Column(
                "warning_time_delta_minutes",
                sa.Float(),
                nullable=False,
                server_default=sa.text("30.0"),
            ),
            sa.Column(
                "critical_time_delta_minutes",
                sa.Float(),
                nullable=False,
                server_default=sa.text("120.0"),
            ),
            sa.Column(
                "is_active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_execution_observation_config_id",
            "execution_observation_config",
            ["id"],
            unique=False,
        )

    # --- 4. execution_plan ---
    if not _table_exists("execution_plan"):
        op.create_table(
            "execution_plan",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("order_code", sa.String(), nullable=False),
            sa.Column("snapshot_version", sa.Integer(), nullable=False),
            sa.Column("tasks_json", sa.String(), nullable=False),
            sa.Column("total_estimated_time_minutes", sa.Float(), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_execution_plan_id", "execution_plan", ["id"], unique=False
        )
        op.create_index(
            "ix_execution_plan_order_id",
            "execution_plan",
            ["order_id"],
            unique=False,
        )

    # --- 5. execution_reality ---
    if not _table_exists("execution_reality"):
        op.create_table(
            "execution_reality",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("order_id", sa.Integer(), nullable=False),
            sa.Column("order_code", sa.String(), nullable=False),
            sa.Column(
                "tasks_json",
                sa.String(),
                nullable=False,
                server_default=sa.text("'[]'"),
            ),
            sa.Column(
                "total_actual_time_minutes",
                sa.Float(),
                nullable=False,
                server_default=sa.text("0.0"),
            ),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_execution_reality_id", "execution_reality", ["id"], unique=False
        )
        op.create_index(
            "ix_execution_reality_order_id",
            "execution_reality",
            ["order_id"],
            unique=True,
        )

    # --- 6. product_families ---
    if not _table_exists("product_families"):
        op.create_table(
            "product_families",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("family_id", sa.String(), nullable=False),
            sa.Column("label", sa.String(), nullable=False),
            sa.Column("category", sa.String(), nullable=True),
            sa.Column(
                "active",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("true"),
            ),
            sa.Column(
                "default_template_id",
                sa.Integer(),
                sa.ForeignKey("product_templates.id"),
                nullable=True,
            ),
            sa.Column("description", sa.String(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("family_id", name="uq_product_families_family_id"),
        )
        op.create_index(
            "ix_product_families_id", "product_families", ["id"], unique=False
        )
        op.create_index(
            "ix_product_families_family_id",
            "product_families",
            ["family_id"],
            unique=True,
        )

    # --- 7. recurring_payments ---
    if not _table_exists("recurring_payments"):
        op.create_table(
            "recurring_payments",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("name", sa.String(), nullable=False),
            sa.Column(
                "category",
                sa.String(),
                nullable=False,
                server_default=sa.text("'alte_costuri'"),
            ),
            sa.Column("amount", sa.Float(), nullable=True),
            sa.Column(
                "currency",
                sa.String(),
                nullable=False,
                server_default=sa.text("'RON'"),
            ),
            sa.Column(
                "periodicity",
                sa.String(),
                nullable=False,
                server_default=sa.text("'lunar'"),
            ),
            sa.Column("supplier", sa.String(), nullable=True),
            sa.Column("due_day", sa.Integer(), nullable=True),
            sa.Column(
                "status",
                sa.String(),
                nullable=False,
                server_default=sa.text("'active'"),
            ),
            sa.Column(
                "include_in_overhead",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column(
                "include_in_machine_cost",
                sa.Boolean(),
                nullable=False,
                server_default=sa.text("false"),
            ),
            sa.Column("linked_machine_id", sa.String(), nullable=True),
            sa.Column("observatii", sa.Text(), nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.func.now(),
            ),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_recurring_payments_id", "recurring_payments", ["id"], unique=False
        )


def downgrade() -> None:
    """Downgrade schema."""
    for table in [
        "recurring_payments",
        "product_families",
        "execution_reality",
        "execution_plan",
        "execution_observation_config",
        "cost_engine_config",
        "employees",
    ]:
        if _table_exists(table):
            op.drop_table(table)