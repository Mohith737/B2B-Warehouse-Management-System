# backend/alembic/versions/018_create_email_failure_log.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "email_failure_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column("email_type", sa.String(length=50), nullable=False),
        sa.Column(
            "to_emails",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "retry_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "resolved",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
        sa.Column("workflow_id", sa.String(length=255), nullable=True),
        sa.Column("activity_id", sa.String(length=255), nullable=True),
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
    )
    op.create_index(
        "ix_email_failure_log_email_type", "email_failure_log", ["email_type"]
    )
    op.create_index("ix_email_failure_log_resolved", "email_failure_log", ["resolved"])
    op.create_index(
        "ix_email_failure_log_created_at", "email_failure_log", ["created_at"]
    )


def downgrade() -> None:
    op.drop_index("ix_email_failure_log_created_at", table_name="email_failure_log")
    op.drop_index("ix_email_failure_log_resolved", table_name="email_failure_log")
    op.drop_index("ix_email_failure_log_email_type", table_name="email_failure_log")
    op.drop_table("email_failure_log")
