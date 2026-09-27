import json

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect, text

import app.models.models  # noqa: F401
from app.core.db import Base
from app.db_upgrade import alembic_config, upgrade


def _schema_diff(url: str) -> list:
    engine = create_engine(url)
    try:
        with engine.connect() as conn:
            return compare_metadata(MigrationContext.configure(conn), Base.metadata)
    finally:
        engine.dispose()


def test_migrations_on_empty_db_match_models(tmp_path):
    url = f"sqlite:///{tmp_path / 'fresh.db'}"
    upgrade(url)
    assert _schema_diff(url) == []


def test_pre_alembic_database_is_stamped_then_upgraded(tmp_path):
    url = f"sqlite:///{tmp_path / 'legacy.db'}"
    # Reproduce a database made by the old create_all(): baseline tables, no alembic_version.
    command.upgrade(alembic_config(url), "0001")
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE alembic_version"))
    engine.dispose()

    upgrade(url)

    engine = create_engine(url)
    try:
        assert "alembic_version" in inspect(engine).get_table_names()
    finally:
        engine.dispose()
    assert _schema_diff(url) == []


def _insert_legacy_rows(url: str) -> None:
    """Rows as the pre-migration code wrote them: an attempt with two logged steps."""
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO employees VALUES ('e1', 'Синтетический Проводник', '', '', '2026-09-25 10:00:00')"))
        conn.execute(
            text("INSERT INTO scenarios VALUES ('s1', 'demo', '', :graph, '2026-09-25 10:00:00')"),
            {"graph": '{"start_node": "n1", "nodes": {}}'},
        )
        conn.execute(
            text(
                "INSERT INTO attempts VALUES ('a1', 'e1', 's1', 'n3', 55, 50, 'in_progress', NULL, "
                "'2026-09-25 10:02:00', '2026-09-25 10:00:00', NULL)"
            )
        )
        conn.execute(text("INSERT INTO choice_logs VALUES ('l2', 'a1', 'n2', 'c2', 0, 0, 0, '2026-09-25 10:02:00')"))
        conn.execute(text("INSERT INTO choice_logs VALUES ('l1', 'a1', 'n1', 'c1', 0, 5, 0, '2026-09-25 10:01:00')"))
    engine.dispose()


def test_upgrade_backfills_steps_for_existing_attempts(tmp_path):
    url = f"sqlite:///{tmp_path / 'data.db'}"
    command.upgrade(alembic_config(url), "0001")
    _insert_legacy_rows(url)

    upgrade(url)

    engine = create_engine(url)
    with engine.connect() as conn:
        assert conn.execute(text("SELECT step FROM attempts WHERE id = 'a1'")).scalar() == 2
        steps = conn.execute(text("SELECT id, step FROM choice_logs ORDER BY step")).all()
    engine.dispose()
    assert [tuple(r) for r in steps] == [("l1", 1), ("l2", 2)]


def test_upgrade_freezes_a_snapshot_for_attempts_already_in_progress(tmp_path):
    url = f"sqlite:///{tmp_path / 'data.db'}"
    command.upgrade(alembic_config(url), "0001")
    _insert_legacy_rows(url)

    upgrade(url)

    engine = create_engine(url)
    with engine.connect() as conn:
        row = conn.execute(text("SELECT graph_snapshot, scenario_version, flags FROM attempts WHERE id = 'a1'")).one()
        version = conn.execute(text("SELECT version FROM scenarios WHERE id = 's1'")).scalar()
    engine.dispose()
    assert json.loads(row.graph_snapshot) == {"start_node": "n1", "nodes": {}}
    assert (row.scenario_version, version) == (1, 1)
    assert json.loads(row.flags) == {}


def test_upgrade_rescores_finished_attempts_relative_to_the_scenario(tmp_path):
    """Seat recline: raw results 38..58. Old scores 48, 58, 38 become 50, 100, 0; XP and bests follow."""
    from app.scenarios.library import load_scenario

    url = f"sqlite:///{tmp_path / 'data.db'}"
    command.upgrade(alembic_config(url), "0009")
    graph = json.dumps(load_scenario("seat_recline")["graph"])
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO employees (id, full_name, depot, brigade, created_at) VALUES ('e1', 'Анна', 'Д', 'Б', '2026-09-25 10:00:00')"))
        conn.execute(text("INSERT INTO scenarios (id, title, description, created_at, tags) VALUES ('s1', 'Кресло', '', '2026-09-25 10:00:00', '[]')"))
        for aid, loyalty, safety, old, minute in [("a1", 40, 55, 48, 1), ("a2", 60, 55, 58, 2), ("a3", 35, 40, 38, 3)]:
            conn.execute(
                text(
                    "INSERT INTO attempts (id, employee_id, scenario_id, current_node, loyalty, safety, status, node_shown_at,"
                    " started_at, finished_at, flags, graph_snapshot, score, xp_gained)"
                    " VALUES (:id, 'e1', 's1', 'end', :l, :s, 'finished', :t, :t, :t, '{}', :g, :old, 0)"
                ),
                {"id": aid, "l": loyalty, "s": safety, "t": f"2026-09-25 10:0{minute}:00", "g": graph, "old": old},
            )
        conn.execute(text("INSERT INTO scenario_bests VALUES ('b1', 'e1', 's1', 58, 'a2', '2026-09-25 10:02:00')"))
    engine.dispose()

    upgrade(url)

    engine = create_engine(url)
    with engine.connect() as conn:
        rows = conn.execute(text("SELECT id, score, xp_gained FROM attempts ORDER BY id")).all()
        best = conn.execute(text("SELECT best_score, attempt_id FROM scenario_bests")).one()
    engine.dispose()
    assert [tuple(r) for r in rows] == [("a1", 50, 50), ("a2", 100, 50), ("a3", 0, 0)]
    assert tuple(best) == (100, "a2")


def test_downgrade_drops_scenario_achievements_the_old_schema_cannot_hold(tmp_path):
    url = f"sqlite:///{tmp_path / 'data.db'}"
    upgrade(url)
    engine = create_engine(url)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO employees (id, full_name, depot, brigade, created_at, role, is_synthetic, failed_logins)"
                          " VALUES ('e1', 'Анна', 'Д', 'Б', '2026-09-25 10:00:00', 'conductor', 0, 0)"))
        for aid in ("first_trip", "s:" + "x" * 36 + ":calm_carriage"):
            conn.execute(text("INSERT INTO employee_achievements (id, employee_id, achievement_id, awarded_at)"
                              " VALUES (:id, 'e1', :aid, '2026-09-25 10:00:00')"), {"id": aid[:36], "aid": aid})
    engine.dispose()

    command.downgrade(alembic_config(url), "0009")

    engine = create_engine(url)
    with engine.connect() as conn:
        left = conn.execute(text("SELECT achievement_id FROM employee_achievements")).scalars().all()
    engine.dispose()
    assert left == ["first_trip"]
