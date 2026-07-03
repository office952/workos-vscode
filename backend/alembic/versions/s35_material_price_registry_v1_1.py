"""Material Price Registry v1.1 additive schema.

Revision ID: s35_material_price_registry_v1_1
Revises: s34_add_workcenter_rate_basis_fields
Create Date: 2026-06-02

Adds:
- inventory_materials: currency, vat_percent, valid_from, supplier_id
- inventory_material_price_history table
- pricing-governance indexes (feature-owned only)
"""

from alembic import op
import sqlalchemy as sa


revision = "s35_material_price_registry_v1_1"
down_revision = "s34_add_workcenter_rate_basis_fields"
branch_labels = None
depends_on = None


def _column_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {c["name"] for c in inspector.get_columns(table_name)}


def _index_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {idx["name"] for idx in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("inventory_materials"):
        return

    inv_cols = _column_names(inspector, "inventory_materials")

    if "currency" not in inv_cols:
        op.add_column("inventory_materials", sa.Column("currency", sa.String(), nullable=True))

    if "vat_percent" not in inv_cols:
        op.add_column("inventory_materials", sa.Column("vat_percent", sa.Float(), nullable=True))

    if "valid_from" not in inv_cols:
        op.add_column(
            "inventory_materials",
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
        )

    if "supplier_id" not in inv_cols:
        op.add_column("inventory_materials", sa.Column("supplier_id", sa.Integer(), nullable=True))

    # Add FK in batch mode for SQLite compatibility.
    fks = {fk.get("name") for fk in inspector.get_foreign_keys("inventory_materials")}
    if "fk_inventory_materials_supplier_id" not in fks:
        with op.batch_alter_table("inventory_materials", recreate="always") as batch_op:
            batch_op.create_foreign_key(
                "fk_inventory_materials_supplier_id",
                "suppliers",
                ["supplier_id"],
                ["id"],
                ondelete="RESTRICT",
            )

    if not inspector.has_table("inventory_material_price_history"):
        op.create_table(
            "inventory_material_price_history",
            sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
            sa.Column("material_id", sa.Integer(), sa.ForeignKey("inventory_materials.id"), nullable=False),
            sa.Column("unit_cost", sa.Float(), nullable=True),
            sa.Column("currency", sa.String(), nullable=True),
            sa.Column("vat_percent", sa.Float(), nullable=True),
            sa.Column("valid_from", sa.DateTime(timezone=True), nullable=True),
            sa.Column("changed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("changed_by", sa.String(), nullable=True),
            sa.Column("change_reason", sa.String(), nullable=True),
            sa.Column("snapshot_source", sa.String(), nullable=True),
        )

    inv_indexes = _index_names(sa.inspect(bind), "inventory_materials")
    if "ix_inventory_materials_supplier_id" not in inv_indexes:
        op.create_index("ix_inventory_materials_supplier_id", "inventory_materials", ["supplier_id"], unique=False)

    hist_indexes = _index_names(sa.inspect(bind), "inventory_material_price_history")
    if "ix_inventory_material_price_history_material_changed" not in hist_indexes:
        op.create_index(
            "ix_inventory_material_price_history_material_changed",
            "inventory_material_price_history",
            ["material_id", "changed_at"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if inspector.has_table("inventory_material_price_history"):
        hist_indexes = _index_names(inspector, "inventory_material_price_history")
        if "ix_inventory_material_price_history_material_changed" in hist_indexes:
            op.drop_index("ix_inventory_material_price_history_material_changed", table_name="inventory_material_price_history")
        op.drop_table("inventory_material_price_history")

    if inspector.has_table("inventory_materials"):
        inv_indexes = _index_names(inspector, "inventory_materials")
        if "ix_inventory_materials_supplier_id" in inv_indexes:
            op.drop_index("ix_inventory_materials_supplier_id", table_name="inventory_materials")

        inv_cols = _column_names(inspector, "inventory_materials")
        with op.batch_alter_table("inventory_materials", recreate="always") as batch_op:
            fks = {fk.get("name") for fk in inspector.get_foreign_keys("inventory_materials")}
            if "fk_inventory_materials_supplier_id" in fks:
                batch_op.drop_constraint("fk_inventory_materials_supplier_id", type_="foreignkey")

        inspector = sa.inspect(bind)
        inv_cols = _column_names(inspector, "inventory_materials")
        if "supplier_id" in inv_cols:
            op.drop_column("inventory_materials", "supplier_id")
        if "valid_from" in inv_cols:
            op.drop_column("inventory_materials", "valid_from")
        if "vat_percent" in inv_cols:
            op.drop_column("inventory_materials", "vat_percent")
        if "currency" in inv_cols:
            op.drop_column("inventory_materials", "currency")
