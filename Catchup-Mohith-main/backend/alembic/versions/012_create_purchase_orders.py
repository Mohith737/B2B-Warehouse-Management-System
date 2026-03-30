# /home/mohith/Catchup-Mohith/backend/alembic/versions/012_create_purchase_orders.py
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def _has_index(indexes: Sequence[dict], name: str) -> bool:
    return any(idx.get("name") == name for idx in indexes)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not inspector.has_table("purchase_orders"):
        op.create_table(
            "purchase_orders",
            sa.Column(
                "id",
                postgresql.UUID(as_uuid=True),
                server_default=sa.text("gen_random_uuid()"),
                primary_key=True,
                nullable=False,
            ),
            sa.Column("po_number", sa.String(50), nullable=False),
            sa.Column(
                "supplier_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("suppliers.id"),
                nullable=False,
            ),
            sa.Column(
                "created_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id"),
                nullable=False,
            ),
            sa.Column(
                "status",
                sa.String(30),
                nullable=False,
                server_default=sa.text("'draft'"),
            ),
            sa.Column(
                "total_amount",
                sa.Numeric(precision=12, scale=2),
                nullable=False,
                server_default=sa.text("0"),
            ),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("expected_delivery_date", sa.Date(), nullable=True),
            sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("shipped_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("received_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
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
            sa.CheckConstraint(
                "status IN ('draft', 'submitted', 'acknowledged', "
                "'shipped', 'received', 'closed', 'cancelled')",
                name="ck_purchase_orders_status",
            ),
        )

    columns = {col["name"] for col in inspector.get_columns("purchase_orders")}
    if "cancelled_at" not in columns:
        op.add_column(
            "purchase_orders",
            sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        )

    indexes = inspector.get_indexes("purchase_orders")
    if not _has_index(indexes, "ix_purchase_orders_po_number"):
        op.create_index(
            "ix_purchase_orders_po_number",
            "purchase_orders",
            ["po_number"],
            unique=True,
        )
    if not _has_index(indexes, "ix_purchase_orders_supplier_id"):
        op.create_index(
            "ix_purchase_orders_supplier_id",
            "purchase_orders",
            ["supplier_id"],
        )
    if not _has_index(indexes, "ix_purchase_orders_created_by"):
        op.create_index(
            "ix_purchase_orders_created_by",
            "purchase_orders",
            ["created_by"],
        )
    if not _has_index(indexes, "ix_purchase_orders_status"):
        op.create_index(
            "ix_purchase_orders_status",
            "purchase_orders",
            ["status"],
        )
    if not _has_index(indexes, "ix_purchase_orders_deleted_at"):
        op.create_index(
            "ix_purchase_orders_deleted_at",
            "purchase_orders",
            ["deleted_at"],
        )


def downgrade() -> None:
    op.drop_index("ix_purchase_orders_status", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_supplier_id", table_name="purchase_orders")
    op.drop_index("ix_purchase_orders_created_by", table_name="purchase_orders")
    op.drop_table("purchase_orders")
