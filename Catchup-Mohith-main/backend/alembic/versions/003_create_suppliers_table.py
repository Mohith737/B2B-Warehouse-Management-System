# /home/mohith/Catchup-Mohith/backend/alembic/versions/003_create_suppliers_table.py
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "suppliers",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column(
            "payment_terms_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("30"),
        ),
        sa.Column(
            "lead_time_days",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("7"),
        ),
        sa.Column(
            "credit_limit",
            sa.Numeric(precision=12, scale=2),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "current_tier",
            sa.String(20),
            nullable=False,
            server_default=sa.text("'Silver'"),
        ),
        sa.Column(
            "tier_locked",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column(
            "consecutive_on_time",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "consecutive_late",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
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
        sa.CheckConstraint(
            "current_tier IN ('Silver', 'Gold', 'Diamond')",
            name="ck_suppliers_tier",
        ),
    )
    op.create_index("ix_suppliers_email", "suppliers", ["email"], unique=True)
    op.create_index("ix_suppliers_deleted_at", "suppliers", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_suppliers_deleted_at", table_name="suppliers")
    op.drop_index("ix_suppliers_email", table_name="suppliers")
    op.drop_table("suppliers")
