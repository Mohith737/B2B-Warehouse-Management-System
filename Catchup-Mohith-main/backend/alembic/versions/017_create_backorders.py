# backend/alembic/versions/017_create_backorders.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "backorders",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "original_po_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("purchase_orders.id"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id"),
            nullable=False,
        ),
        sa.Column(
            "quantity_ordered",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
        ),
        sa.Column(
            "quantity_received",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
        ),
        sa.Column(
            "quantity_outstanding",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'open'"),
        ),
        sa.Column(
            "grn_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("grns.id"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "status IN ('open', 'closed')",
            name="ck_backorders_status",
        ),
    )
    op.create_index("ix_backorders_original_po_id", "backorders", ["original_po_id"])
    op.create_index("ix_backorders_product_id", "backorders", ["product_id"])
    op.create_index("ix_backorders_grn_id", "backorders", ["grn_id"])
    op.create_index("ix_backorders_status", "backorders", ["status"])


def downgrade() -> None:
    op.drop_index("ix_backorders_status", table_name="backorders")
    op.drop_index("ix_backorders_grn_id", table_name="backorders")
    op.drop_index("ix_backorders_product_id", table_name="backorders")
    op.drop_index("ix_backorders_original_po_id", table_name="backorders")
    op.drop_table("backorders")
