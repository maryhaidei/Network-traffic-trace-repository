from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class LabeledTraceSource(Base):
    __tablename__ = "labeled_trace_sources"
    __table_args__ = (
        UniqueConstraint("labeled_trace_id", "raw_trace_id", name="uq_labeled_trace_source_pair"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    labeled_trace_id: Mapped[int] = mapped_column(
        ForeignKey("labeled_traces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    raw_trace_id: Mapped[int] = mapped_column(
        ForeignKey("raw_traces.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )