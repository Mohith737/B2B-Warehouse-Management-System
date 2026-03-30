# backend/alembic/versions/015_create_grn_lines.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "grn_lines",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "grn_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("grns.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "product_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("products.id"),
            nullable=False,
        ),
        sa.Column(
            "quantity_received",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
        ),
        sa.Column(
            "unit_cost",
            sa.Numeric(precision=12, scale=4),
            nullable=False,
        ),
        sa.Column("barcode_scanned", sa.String(length=100), nullable=True),
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
        sa.UniqueConstraint(
            "grn_id",
            "product_id",
            name="uq_grn_lines_grn_product",
        ),
    )
    op.create_index("ix_grn_lines_grn_id", "grn_lines", ["grn_id"])
    op.create_index("ix_grn_lines_product_id", "grn_lines", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_grn_lines_product_id", table_name="grn_lines")
    op.drop_index("ix_grn_lines_grn_id", table_name="grn_lines")
    op.drop_table("grn_lines")
