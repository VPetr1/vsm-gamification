"""Competency assessment per step and per attempt; scenario tags.

Revision ID: 0007
Revises: 0006
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None

scenarios = sa.table("scenarios", sa.column("tags", sa.JSON))


def upgrade() -> None:
    with op.batch_alter_table("choice_logs") as batch:
        batch.add_column(sa.Column("assessment", sa.JSON(), nullable=True))
    with op.batch_alter_table("attempts") as batch:
        batch.add_column(sa.Column("assessment", sa.JSON(), nullable=True))
    with op.batch_alter_table("scenarios") as batch:
        batch.add_column(sa.Column("tags", sa.JSON(), nullable=True))
    op.get_bind().execute(scenarios.update().values(tags=[]))
    with op.batch_alter_table("scenarios") as batch:
        batch.alter_column("tags", existing_type=sa.JSON(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("scenarios") as batch:
        batch.drop_column("tags")
    with op.batch_alter_table("attempts") as batch:
        batch.drop_column("assessment")
    with op.batch_alter_table("choice_logs") as batch:
        batch.drop_column("assessment")
