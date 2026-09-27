"""Achievements defined in scenarios; attempt score relative to the scenario's worst and best ending.

Revision ID: 0010
Revises: 0009
"""
import json

from alembic import op
import sqlalchemy as sa

from app.scenarios.scoring import attempt_score

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("employee_achievements") as batch:
        batch.alter_column("achievement_id", type_=sa.String(120), existing_type=sa.String(50), existing_nullable=False)
        batch.add_column(sa.Column("title", sa.String(120), nullable=True))
        batch.add_column(sa.Column("description", sa.Text(), nullable=True))
        batch.add_column(sa.Column("icon", sa.String(20), nullable=True))

    # Re-score finished attempts and replay XP per employee and scenario in finishing order,
    # so score, xp_gained and scenario_bests follow the same rules as new attempts.
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, employee_id, scenario_id, loyalty, safety, graph_snapshot FROM attempts"
            " WHERE status = 'finished' AND score IS NOT NULL ORDER BY finished_at, id"
        )
    ).all()
    best: dict[tuple[str, str], tuple[int, str]] = {}
    for row in rows:
        graph = row.graph_snapshot if isinstance(row.graph_snapshot, dict) else json.loads(row.graph_snapshot)
        score = attempt_score(graph, row.loyalty, row.safety)
        key = (row.employee_id, row.scenario_id)
        previous = best.get(key, (0, None))[0]
        conn.execute(
            sa.text("UPDATE attempts SET score = :score, xp_gained = :gained WHERE id = :id"),
            {"score": score, "gained": max(0, score - previous), "id": row.id},
        )
        if key not in best or score > previous:
            best[key] = (score, row.id)
    for (employee_id, scenario_id), (score, attempt_id) in best.items():
        conn.execute(
            sa.text(
                "UPDATE scenario_bests SET best_score = :score, attempt_id = :attempt"
                " WHERE employee_id = :employee AND scenario_id = :scenario"
            ),
            {"score": score, "attempt": attempt_id, "employee": employee_id, "scenario": scenario_id},
        )


def downgrade() -> None:
    # Scores stay in the relative scale; only the schema is reverted.
    with op.batch_alter_table("employee_achievements") as batch:
        batch.drop_column("icon")
        batch.drop_column("description")
        batch.drop_column("title")
        batch.alter_column("achievement_id", type_=sa.String(50), existing_type=sa.String(120), existing_nullable=False)
