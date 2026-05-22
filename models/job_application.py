from datetime import date, datetime, UTC

from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    DateTime,
    Date,
    Boolean
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from extensions import db


class JobApplication(db.Model):
    __tablename__ = "applications"

    # =========================================================
    # PRIMARY KEY
    # =========================================================
    application_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True
    )

    # =========================================================
    # BASIC INFORMATION
    # =========================================================
    company_name: Mapped[str] = mapped_column(
        String(250),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(250),
        nullable=False
    )

    application_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Job"
    )

    # =========================================================
    # LOCATION / WORK
    # =========================================================
    location: Mapped[str] = mapped_column(
        String(250),
        nullable=False
    )

    office_address: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    maps_link: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    work_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="Unknown"
    )

    # =========================================================
    # APPLICATION DETAILS
    # =========================================================
    applied_via: Mapped[str] = mapped_column(
        String(250),
        nullable=False
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    priority: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="Medium"
    )

    # =========================================================
    # DATES
    # =========================================================
    date_applied: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False
    )

    follow_up_date: Mapped[date] = mapped_column(
        Date,
        nullable=True
    )

    last_checked: Mapped[date] = mapped_column(
        Date,
        nullable=True
    )

    # =========================================================
    # LINKS / NOTES
    # =========================================================
    application_link: Mapped[str] = mapped_column(
        String(500),
        nullable=True
    )

    notes: Mapped[str] = mapped_column(
        String(1000),
        nullable=True
    )

    salary: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    # =========================================================
    # CONTACT DETAILS
    # =========================================================
    contact_name: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    contact_email: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )

    contact_phone: Mapped[str] = mapped_column(
        String(50),
        nullable=True
    )

    # =========================================================
    # ARCHIVE
    # =========================================================
    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    # =========================================================
    # TIMESTAMPS
    # =========================================================
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC)
    )

    # =========================================================
    # RELATIONSHIP
    # =========================================================
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    user = relationship(
        "User",
        back_populates="applications"
    )

    # =========================================================
    # VALID STATUSES
    # =========================================================
    VALID_STATUSES = [
        "Applied",
        "Interview",
        "Rejected",
        "Offer",
        "Withdrawn",
        "Other"
    ]