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
