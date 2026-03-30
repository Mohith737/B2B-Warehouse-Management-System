# /home/mohith/Catchup-Mohith/backend/alembic/versions/013_create_po_lines.py
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def _has_index(indexes: Sequence[dict], name: str) -> bool:
    return any(idx.get("name") == name for idx in indexes)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("po_lines"):
        op.create_table(
            "po_lines",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("gen_random_uuid()"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column(
                "po_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("purchase_orders.id", ondelete="CASCADE"),
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
                server_default=sa.text("0"),
            ),
            sa.Column(
                "unit_price",
                sa.Numeric(precision=12, scale=4),
                nullable=False,
            ),
            sa.Column(
                "line_total",
                sa.Numeric(precision=12, scale=4),
                nullable=False,
                server_default=sa.text("0"),
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
        )

    columns = {col["name"] for col in inspector.get_columns("po_lines")}
    if "line_total" not in columns:
        op.add_column(
            "po_lines",
            sa.Column(
                "line_total",
                sa.Numeric(precision=12, scale=4),
                nullable=False,
                server_default=sa.text("0"),
            ),
        )

    indexes = inspector.get_indexes("po_lines")
    if not _has_index(indexes, "ix_po_lines_po_id"):
        op.create_index("ix_po_lines_po_id", "po_lines", ["po_id"])
    if not _has_index(indexes, "ix_po_lines_product_id"):
        op.create_index("ix_po_lines_product_id", "po_lines", ["product_id"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("po_lines"):
        return

    columns = {col["name"] for col in inspector.get_columns("po_lines")}
    if "line_total" in columns:
        op.drop_column("po_lines", "line_total")
