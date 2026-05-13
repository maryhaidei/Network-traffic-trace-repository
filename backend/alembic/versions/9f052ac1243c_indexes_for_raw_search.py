"""indexes for raw search

Revision ID: 9f052ac1243c
Revises: bdba22b95b7e
Create Date: 2026-02-25 19:50:36.717867

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9f052ac1243c'
down_revision: Union[str, Sequence[str], None] = 'bdba22b95b7e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_raw_groups_capture_start ON raw_groups (capture_start)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_raw_groups_capture_end ON raw_groups (capture_end)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_raw_groups_org ON raw_groups (org)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_raw_groups_data_character ON raw_groups (data_character)")

    op.execute("CREATE INDEX IF NOT EXISTS ix_raw_traces_group_id ON raw_traces (group_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_raw_traces_t_min ON raw_traces (t_min)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_raw_traces_t_max ON raw_traces (t_max)")

def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_raw_traces_t_max")
    op.execute("DROP INDEX IF EXISTS ix_raw_traces_t_min")
    op.execute("DROP INDEX IF EXISTS ix_raw_traces_group_id")

    op.execute("DROP INDEX IF EXISTS ix_raw_groups_data_character")
    op.execute("DROP INDEX IF EXISTS ix_raw_groups_org")
    op.execute("DROP INDEX IF EXISTS ix_raw_groups_capture_end")
    op.execute("DROP INDEX IF EXISTS ix_raw_groups_capture_start")
