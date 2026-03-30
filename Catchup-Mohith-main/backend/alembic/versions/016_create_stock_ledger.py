# backend/alembic/versions/016_create_stock_ledger.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stock_ledger",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id"),
            nullable=False,
        ),
        sa.Column(
            "quantity_change",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
        ),
        sa.Column("change_type", sa.String(length=50), nullable=False),
        sa.Column("reference_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "balance_after",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "change_type IN ('grn_receipt', 'po_reservation', "
            "'manual_adjustment', 'reorder_auto', "
            "'backorder_fulfillment')",
            name="ck_stock_ledger_change_type",
        ),
    )
    op.create_index("ix_stock_ledger_product_id", "stock_ledger", ["product_id"])
    op.create_index("ix_stock_ledger_change_type", "stock_ledger", ["change_type"])
    op.create_index("ix_stock_ledger_reference_id", "stock_ledger", ["reference_id"])
    op.create_index("ix_stock_ledger_created_at", "stock_ledger", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_stock_ledger_created_at", table_name="stock_ledger")
    op.drop_index("ix_stock_ledger_reference_id", table_name="stock_ledger")
    op.drop_index("ix_stock_ledger_change_type", table_name="stock_ledger")
    op.drop_index("ix_stock_ledger_product_id", table_name="stock_ledger")
    op.drop_table("stock_ledger")
