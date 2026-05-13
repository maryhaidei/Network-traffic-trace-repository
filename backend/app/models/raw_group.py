from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RawGroup(Base):
    __tablename__ = "raw_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    name: Mapped[str] = mapped_column(String(120), unique=True, index=True, nullable=False)

    org: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    data_character: Mapped[str] = mapped_column(String(200), index=True, nullable=False)

    capture_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    capture_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)

    hardware_desc: Mapped[str] = mapped_column(String(300), nullable=False)
    software_desc: Mapped[str] = mapped_column(String(300), nullable=False)
    processing_degree: Mapped[str] = mapped_column(String(300), nullable=False)

    capture_points: Mapped[int] = mapped_column(Integer, index=True, nullable=False)  # 1 | 2

    schema_file_id: Mapped[int | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
    )
    description_file_id: Mapped[int | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )