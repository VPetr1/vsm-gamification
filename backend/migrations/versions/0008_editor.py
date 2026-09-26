"""Scenario drafts for the editor, publication metadata, title in the attempt snapshot.

Revision ID: 0008
Revises: 0007
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("scenarios") as batch:
        batch.alter_column("graph", existing_type=sa.JSON(), nullable=True)
        batch.add_column(sa.Column("draft", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("key", sa.String(100), nullable=True))
        batch.add_column(sa.Column("origin", sa.String(20), nullable=False, server_default="api"))
        batch.add_column(sa.Column("published_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))
        batch.create_unique_constraint("uq_scenarios_key", ["key"])
    op.execute("UPDATE scenarios SET published_at = created_at")

    with op.batch_alter_table("attempts") as batch:
        batch.add_column(sa.Column("scenario_title", sa.String(300), nullable=False, server_default=""))
    op.execute(
        "UPDATE attempts SET scenario_title = (SELECT scenarios.title FROM scenarios WHERE scenarios.id = attempts.scenario_id)"
    )


def downgrade() -> None:
    with op.batch_alter_table("attempts") as batch:
        batch.drop_column("scenario_title")
    with op.batch_alter_table("scenarios") as batch:
        batch.drop_constraint("uq_scenarios_key", type_="unique")
        batch.drop_column("updated_at")
        batch.drop_column("published_at")
        batch.drop_column("origin")
        batch.drop_column("key")
        batch.drop_column("draft")
        batch.alter_column("graph", existing_type=sa.JSON(), nullable=False)
