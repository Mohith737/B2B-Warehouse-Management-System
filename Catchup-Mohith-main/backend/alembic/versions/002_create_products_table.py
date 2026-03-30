# /home/mohith/Catchup-Mohith/backend/alembic/versions/002_create_products_table.py
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "products",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("sku", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("unit_of_measure", sa.String(50), nullable=False),
        sa.Column(
            "current_stock",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "reorder_point",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "low_stock_threshold_override",
            sa.Numeric(precision=12, scale=4),
            nullable=True,
        ),
        sa.Column(
            "reorder_quantity",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.Column("barcode", sa.String(100), nullable=True),
        sa.Column(
            "version",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_products_sku", "products", ["sku"], unique=True)
    op.create_index(
        "ix_products_barcode",
        "products",
        ["barcode"],
        unique=True,
        postgresql_where=sa.text("barcode IS NOT NULL"),
    )
    op.create_index("ix_products_deleted_at", "products", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_products_deleted_at", table_name="products")
    op.drop_index("ix_products_barcode", table_name="products")
    op.drop_index("ix_products_sku", table_name="products")
    op.drop_table("products")
