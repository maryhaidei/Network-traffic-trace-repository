"""add labeled traces

Revision ID: fd5c5194ff0e
Revises: 9f052ac1243c
Create Date: 2026-03-18 22:14:10.619940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fd5c5194ff0e'
down_revision: Union[str, Sequence[str], None] = '9f052ac1243c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "labeled_traces",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("raw_trace_id", sa.Integer(), nullable=False),
        sa.Column("file_id", sa.Integer(), nullable=False),
        sa.Column("software_desc", sa.String(length=255), nullable=True),
        sa.Column("t_from", sa.DateTime(), nullable=True),
        sa.Column("t_to", sa.DateTime(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["raw_trace_id"], ["raw_traces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.UniqueConstraint("file_id"),
    )
    op.create_index("ix_labeled_traces_id", "labeled_traces", ["id"])
    op.create_index("ix_labeled_traces_kind", "labeled_traces", ["kind"])
    op.create_index("ix_labeled_traces_raw_trace_id", "labeled_traces", ["raw_trace_id"])
    op.create_index("ix_labeled_traces_file_id", "labeled_traces", ["file_id"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_labeled_traces_file_id", table_name="labeled_traces")
    op.drop_index("ix_labeled_traces_raw_trace_id", table_name="labeled_traces")
    op.drop_index("ix_labeled_traces_kind", table_name="labeled_traces")
    op.drop_index("ix_labeled_traces_id", table_name="labeled_traces")
    op.drop_table("labeled_traces")
