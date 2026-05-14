"""add original filename to files

Revision ID: ce4ee8bdae9b
Revises: f44984716d06
Create Date: 2026-05-14 00:00:51.602658

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce4ee8bdae9b'
down_revision: Union[str, Sequence[str], None] = 'f44984716d06'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "files",
        sa.Column("original_filename", sa.String(length=255), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("files", "original_filename")
