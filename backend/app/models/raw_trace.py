from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class RawTrace(Base):
    __tablename__ = "raw_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("raw_groups.id", ondelete="CASCADE"), index=True, nullable=False)
    point: Mapped[str] = mapped_column(String(10), nullable=False, default="Single")  # A | B | Single
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id", ondelete="CASCADE"), index=True, nullable=False)

    t_min: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    t_max: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    packets_count: Mapped[int | None] = mapped_column(Integer, nullable=True)

    capture_series: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    part_index: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )