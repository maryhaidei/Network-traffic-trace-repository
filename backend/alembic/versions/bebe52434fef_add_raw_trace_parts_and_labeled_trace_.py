"""add raw trace parts and labeled trace sources

Revision ID: bebe52434fef
Revises: fd5c5194ff0e
Create Date: 2026-03-22 23:36:17.787244

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bebe52434fef'
down_revision: Union[str, Sequence[str], None] = 'fd5c5194ff0e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "raw_traces",
        sa.Column("capture_series", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "raw_traces",
        sa.Column("part_index", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_raw_traces_capture_series",
        "raw_traces",
        ["capture_series"],
        unique=False,
    )
    op.create_index(
        "ix_raw_traces_part_index",
        "raw_traces",
        ["part_index"],
        unique=False,
    )

    op.execute("DROP TABLE IF EXISTS labeled_trace_sources CASCADE;")
    op.execute("DROP TABLE IF EXISTS labeled_traces CASCADE;")

    op.create_table(
        "labeled_traces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("description_file_id", sa.Integer(), nullable=True),
        sa.Column("software_desc", sa.String(length=255), nullable=True),
        sa.Column("t_from", sa.DateTime(timezone=True), nullable=True),
        sa.Column("t_to", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["group_id"], ["raw_groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["description_file_id"], ["files.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.UniqueConstraint("file_id"),
    )
    op.create_index("ix_labeled_traces_kind", "labeled_traces", ["kind"], unique=False)
    op.create_index("ix_labeled_traces_group_id", "labeled_traces", ["group_id"], unique=False)
    op.create_index("ix_labeled_traces_file_id", "labeled_traces", ["file_id"], unique=False)

    op.create_table(
        "labeled_trace_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("labeled_trace_id", sa.Integer(), nullable=False),
        sa.Column("raw_trace_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["labeled_trace_id"],
            ["labeled_traces.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["raw_trace_id"],
            ["raw_traces.id"],
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "labeled_trace_id",
            "raw_trace_id",
            name="uq_labeled_trace_source_pair",
        ),
    )
    op.create_index(
        "ix_labeled_trace_sources_labeled_trace_id",
        "labeled_trace_sources",
        ["labeled_trace_id"],
        unique=False,
    )
    op.create_index(
        "ix_labeled_trace_sources_raw_trace_id",
        "labeled_trace_sources",
        ["raw_trace_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        "ix_labeled_trace_sources_raw_trace_id",
        table_name="labeled_trace_sources",
    )
    op.drop_index(
        "ix_labeled_trace_sources_labeled_trace_id",
        table_name="labeled_trace_sources",
    )
    op.drop_table("labeled_trace_sources")

    op.drop_index("ix_labeled_traces_file_id", table_name="labeled_traces")
    op.drop_index("ix_labeled_traces_group_id", table_name="labeled_traces")
    op.drop_index("ix_labeled_traces_kind", table_name="labeled_traces")
    op.drop_table("labeled_traces")

    op.drop_index("ix_raw_traces_part_index", table_name="raw_traces")
    op.drop_index("ix_raw_traces_capture_series", table_name="raw_traces")
    op.drop_column("raw_traces", "part_index")
    op.drop_column("raw_traces", "capture_series")