# /home/mohith/Catchup-Mohith/backend/alembic/versions/011_seed_initial_admin_user.py
import logging
import os
from datetime import datetime, timezone

import sqlalchemy as sa

from alembic import op

logger = logging.getLogger(__name__)

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()

    result = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM users " "WHERE role = 'admin' AND deleted_at IS NULL"
        )
    )
    count = result.scalar()
    if count and count > 0:
        logger.info("Migration 011: admin user already exists, skipping seed.")
        return

    password = os.environ.get("INITIAL_ADMIN_PASSWORD", "")
    if not password:
        password = "REDACTED_SEE_ENV"
        logger.warning(
            "INITIAL_ADMIN_PASSWORD environment variable is not set. "
            "Using insecure fallback password. Change this immediately "
            "after first login."
        )
    elif password == "REDACTED_SEE_ENV":
        logger.warning(
            "INITIAL_ADMIN_PASSWORD is still set to the default value. "
            "Change this before going to production."
        )

    from passlib.context import CryptContext

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed = pwd_context.hash(password)

    admin_email = os.environ.get("INITIAL_ADMIN_EMAIL", "admin@stockbridge.local")

    now = datetime.now(timezone.utc)

    bind.execute(
        sa.text(
            "INSERT INTO users "
            "(email, hashed_password, full_name, role, is_active, "
            "token_version, created_at, updated_at) VALUES "
            "(:email, :hashed_password, :full_name, :role, :is_active, "
            ":token_version, :created_at, :updated_at)"
        ),
        {
            "email": admin_email,
            "hashed_password": hashed,
            "full_name": "System Administrator",
            "role": "admin",
            "is_active": True,
            "token_version": 0,
            "created_at": now,
            "updated_at": now,
        },
    )
    logger.info(f"Migration 011: admin user seeded with email={admin_email}")


def downgrade() -> None:
    admin_email = os.environ.get("INITIAL_ADMIN_EMAIL", "admin@stockbridge.local")
    bind = op.get_bind()
    bind.execute(
        sa.text("DELETE FROM users WHERE email = :email AND role = 'admin'"),
        {"email": admin_email},
    )
    logger.info(f"Migration 011 downgrade: removed admin with email={admin_email}")
