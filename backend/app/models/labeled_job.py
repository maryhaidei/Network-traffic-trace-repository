from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.models.base import Base

class LabeledJob(Base):
    __tablename__ = "labeled_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="queued")
    kind: Mapped[str] = mapped_column(String(20), nullable=False)  # qos | mac_new | any

    raw_trace_id: Mapped[int] = mapped_column(ForeignKey("raw_traces.id"), nullable=False)
    group_id: Mapped[int] = mapped_column(ForeignKey("raw_groups.id"), nullable=False)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    t_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    t_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    tool_info: Mapped[str | None] = mapped_column(String(200), nullable=True)
    error_text: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)