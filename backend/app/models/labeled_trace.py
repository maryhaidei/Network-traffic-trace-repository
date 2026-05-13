from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class LabeledTrace(Base):
    __tablename__ = "labeled_traces"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)  # qos | mac_intensity

    group_id: Mapped[int] = mapped_column(
        ForeignKey("raw_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    file_id: Mapped[int] = mapped_column(
        ForeignKey("files.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    description_file_id: Mapped[int | None] = mapped_column(
        ForeignKey("files.id", ondelete="SET NULL"),
        nullable=True,
    )

    software_desc: Mapped[str | None] = mapped_column(String(255), nullable=True)
    t_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    t_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    group = relationship("RawGroup")
    file_object = relationship("FileObject", foreign_keys=[file_id])
    description_file = relationship("FileObject", foreign_keys=[description_file_id])
    creator = relationship("User")