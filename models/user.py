from flask_login import UserMixin
from sqlalchemy import Integer, String
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from extensions import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    # =========================================================
    # PRIMARY KEY
    # =========================================================
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    # =========================================================
    # BASIC USER INFORMATION
    # =========================================================
    username: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        nullable=False
    )

    email: Mapped[str] = mapped_column(
        String(250),
        unique=True,
        nullable=False
    )

    # =========================================================
    # PASSWORD
    # Nullable because Google OAuth users
    # may not have a password
    # =========================================================
    password_hash: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True
    )

    # =========================================================
    # GOOGLE OAUTH
    # =========================================================
    google_id: Mapped[str | None] = mapped_column(
        String(255),
        unique=True,
        nullable=True
    )

    auth_provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="local"
    )

    profile_picture: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    # =========================================================
    # RELATIONSHIP
    # =========================================================
    applications: Mapped[list["JobApplication"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # =========================================================
    # REPRESENTATION
    # =========================================================
    def __repr__(self):
        return f"<User {self.username}>"
