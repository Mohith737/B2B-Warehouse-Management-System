# backend/alembic/versions/004_create_supplier_metrics_history_table.py
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "supplier_metrics_history",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "supplier_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("suppliers.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("period_year", sa.Integer(), nullable=False),
        sa.Column("period_month", sa.Integer(), nullable=False),
        sa.Column(
            "total_pos",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "on_time_deliveries",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "total_po_lines",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "defect_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "avg_fulfilment_rate",
            sa.Numeric(precision=5, scale=4),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "computed_score",
            sa.Numeric(precision=5, scale=4),
            nullable=True,
        ),
        sa.Column("tier_at_period_end", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint(
            "supplier_id",
            "period_year",
            "period_month",
            name="uq_supplier_metrics_period",
        ),
    )
    op.create_index(
        "ix_supplier_metrics_supplier_id",
        "supplier_metrics_history",
        ["supplier_id"],
    )
    op.create_index(
        "ix_supplier_metrics_period",
        "supplier_metrics_history",
        ["period_year", "period_month"],
    )


def downgrade() -> None:
    op.drop_index("ix_supplier_metrics_period", table_name="supplier_metrics_history")
    op.drop_index(
        "ix_supplier_metrics_supplier_id", table_name="supplier_metrics_history"
    )
    op.drop_table("supplier_metrics_history")
