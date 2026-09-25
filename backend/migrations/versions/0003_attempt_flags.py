"""Per-attempt flags set by actions.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

attempts = sa.table("attempts", sa.column("flags", sa.JSON))


def upgrade() -> None:
    with op.batch_alter_table("attempts") as batch:
        batch.add_column(sa.Column("flags", sa.JSON(), nullable=True))
    op.get_bind().execute(attempts.update().values(flags={}))
    with op.batch_alter_table("attempts") as batch:
        batch.alter_column("flags", existing_type=sa.JSON(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("attempts") as batch:
        batch.drop_column("flags")
