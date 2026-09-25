"""Bring the database schema to the latest Alembic revision.

Run with: python -m app.db_upgrade
"""

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from app.core.config import settings

BASELINE_REVISION = "0001"
ALEMBIC_INI = Path(__file__).resolve().parent.parent / "alembic.ini"


def alembic_config(url: str) -> Config:
    cfg = Config(str(ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", url.replace("%", "%%"))
    return cfg


def upgrade(url: str | None = None) -> None:
    url = url or settings.database_url
    engine = create_engine(url)
    try:
        tables = set(inspect(engine).get_table_names())
    finally:
        engine.dispose()

    cfg = alembic_config(url)
    if "attempts" in tables and "alembic_version" not in tables:
        # Created by the pre-Alembic create_all(): its schema equals the baseline revision.
        command.stamp(cfg, BASELINE_REVISION)
    command.upgrade(cfg, "head")


if __name__ == "__main__":
    upgrade()
