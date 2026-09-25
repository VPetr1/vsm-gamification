"""Scenario versions and an immutable graph snapshot per attempt.

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("scenarios") as batch:
        batch.add_column(sa.Column("version", sa.Integer(), nullable=False, server_default="1"))

    with op.batch_alter_table("attempts") as batch:
        batch.add_column(sa.Column("scenario_version", sa.Integer(), nullable=False, server_default="1"))
        batch.add_column(sa.Column("graph_snapshot", sa.JSON(), nullable=True))

    # Attempts started before this migration freeze the graph as it is now.
    op.execute(
        "UPDATE attempts SET graph_snapshot = (SELECT scenarios.graph FROM scenarios WHERE scenarios.id = attempts.scenario_id)"
    )

    with op.batch_alter_table("attempts") as batch:
        batch.alter_column("graph_snapshot", existing_type=sa.JSON(), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("attempts") as batch:
        batch.drop_column("graph_snapshot")
        batch.drop_column("scenario_version")
    with op.batch_alter_table("scenarios") as batch:
        batch.drop_column("version")
