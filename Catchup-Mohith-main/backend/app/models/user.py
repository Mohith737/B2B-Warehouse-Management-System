# /home/mohith/Catchup-Mohith/backend/app/models/user.py
from enum import Enum

import sqlalchemy
from backend.app.db.base import (
    Base,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column


class UserRole(str, Enum):
    WAREHOUSE_STAFF = "warehouse_staff"
    PROCUREMENT_MANAGER = "procurement_manager"
    ADMIN = "admin"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin, SoftDeleteMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        sqlalchemy.Enum(
            UserRole,
            name="userrole",
            create_constraint=True,
            values_callable=lambda enum_values: [item.value for item in enum_values],
        ),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    token_version: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} " f"role={self.role.value}>"
