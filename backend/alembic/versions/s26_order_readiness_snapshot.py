"""
Add readiness_snapshot JSON column to orders table.
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 's26_order_readiness_snapshot'
down_revision = 's25_smartbill_integration_settings'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('orders', sa.Column('readiness_snapshot', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('orders', 'readiness_snapshot')
