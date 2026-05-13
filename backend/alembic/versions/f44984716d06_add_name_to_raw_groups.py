"""add name to raw groups

Revision ID: f44984716d06
Revises: bebe52434fef
Create Date: 2026-05-13 20:58:53.642613

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f44984716d06'
down_revision: Union[str, Sequence[str], None] = 'bebe52434fef'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE raw_groups
        ADD COLUMN IF NOT EXISTS name VARCHAR(120)
    """)

    op.execute("""
        UPDATE raw_groups
        SET name = 'Группа ' || id
        WHERE name IS NULL
    """)

    op.execute("""
        ALTER TABLE raw_groups
        ALTER COLUMN name SET NOT NULL
    """)

    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS ix_raw_groups_name
        ON raw_groups(name)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_raw_groups_name")
    op.execute("ALTER TABLE raw_groups DROP COLUMN IF EXISTS name")