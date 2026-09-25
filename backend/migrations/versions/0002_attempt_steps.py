"""Step numbers for attempts and one log row per step.

Revision ID: 0002
Revises: 0001
"""
from collections import defaultdict

from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

attempts = sa.table("attempts", sa.column("id", sa.String), sa.column("step", sa.Integer))
choice_logs = sa.table(
    "choice_logs",
    sa.column("id", sa.String),
    sa.column("attempt_id", sa.String),
    sa.column("created_at", sa.DateTime),
    sa.column("step", sa.Integer),
)


def upgrade() -> None:
    with op.batch_alter_table("attempts") as batch:
        batch.add_column(sa.Column("step", sa.Integer(), nullable=False, server_default="0"))

    with op.batch_alter_table("choice_logs") as batch:
        batch.add_column(sa.Column("step", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("next_node", sa.String(100), nullable=True))
        batch.add_column(sa.Column("loyalty_after", sa.Integer(), nullable=True))
        batch.add_column(sa.Column("safety_after", sa.Integer(), nullable=True))

    # Existing logs get steps 1..n per attempt in chronological order; the attempt's step becomes n.
    conn = op.get_bind()
    rows = conn.execute(
        sa.select(choice_logs.c.id, choice_logs.c.attempt_id).order_by(
            choice_logs.c.attempt_id, choice_logs.c.created_at, choice_logs.c.id
        )
    ).all()
    counters: dict[str, int] = defaultdict(int)
    for log_id, attempt_id in rows:
        counters[attempt_id] += 1
        conn.execute(choice_logs.update().where(choice_logs.c.id == log_id).values(step=counters[attempt_id]))
    for attempt_id, count in counters.items():
        conn.execute(attempts.update().where(attempts.c.id == attempt_id).values(step=count))

    with op.batch_alter_table("choice_logs") as batch:
        batch.alter_column("step", existing_type=sa.Integer(), nullable=False)
        batch.create_unique_constraint("uq_choice_logs_attempt_step", ["attempt_id", "step"])


def downgrade() -> None:
    with op.batch_alter_table("choice_logs") as batch:
        batch.drop_constraint("uq_choice_logs_attempt_step", type_="unique")
        batch.drop_column("safety_after")
        batch.drop_column("loyalty_after")
        batch.drop_column("next_node")
        batch.drop_column("step")
    with op.batch_alter_table("attempts") as batch:
        batch.drop_column("step")
