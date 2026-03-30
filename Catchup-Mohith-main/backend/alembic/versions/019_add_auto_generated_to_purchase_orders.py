# backend/alembic/versions/019_add_auto_generated_to_purchase_orders.py
from alembic import op
import sqlalchemy as sa

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "purchase_orders",
        sa.Column(
            "auto_generated",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.create_index(
        "ix_purchase_orders_auto_generated",
        "purchase_orders",
        ["auto_generated"],
    )


def downgrade() -> None:
    op.drop_index("ix_purchase_orders_auto_generated", table_name="purchase_orders")
    op.drop_column("purchase_orders", "auto_generated")
