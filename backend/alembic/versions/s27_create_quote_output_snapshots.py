"""
Create quote_output_snapshots table.

BUILD 10 — Quote Output Snapshot Candidate + Approval Foundation.
Isolated table — does NOT modify quotes, orders, or any existing snapshot tables.
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 's27_create_quote_output_snapshots'
down_revision = 's26_order_readiness_snapshot'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'quote_output_snapshots',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True, nullable=False),
        sa.Column('quote_id', sa.Integer(), nullable=False, index=True),
        sa.Column('quote_code', sa.String(), nullable=True),
        sa.Column('snapshot_code', sa.String(), nullable=False, unique=True, index=True),
        sa.Column('snapshot_type', sa.String(), nullable=False, server_default='quote_output_candidate'),
        sa.Column('status', sa.String(), nullable=False, server_default='draft'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('source_template_id', sa.Integer(), nullable=True),
        sa.Column('source_template_code', sa.String(), nullable=True),
        sa.Column('source_dossier_id', sa.Integer(), nullable=True),
        sa.Column('source_dossier_version', sa.Integer(), nullable=True),
        sa.Column('source_output_block_versions_json', sa.Text(), nullable=True),
        sa.Column('rendered_sections_json', sa.Text(), nullable=True),
        sa.Column('commercial_summary_json', sa.Text(), nullable=True),
        sa.Column('warnings_json', sa.Text(), nullable=True),
        sa.Column('blockers_json', sa.Text(), nullable=True),
        sa.Column('variables_used_json', sa.Text(), nullable=True),
        sa.Column('trace_json', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('approved_by', sa.String(), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('archived_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('superseded_by_snapshot_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('quote_output_snapshots')