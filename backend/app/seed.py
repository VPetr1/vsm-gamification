"""Load built-in scenarios and a synthetic demo employee.

Run after migrations: python -m app.db_upgrade && python -m app.seed
A scenario whose data changed is updated in place with version + 1; attempts
already started keep their own snapshot.
"""

from sqlalchemy.orm import Session

from app.core.db import SessionLocal
from app.models.models import Employee, Scenario
from app.scenarios.library import builtin_scenarios
from app.scenarios.validator import validate_graph

DEMO_EMPLOYEE = {"full_name": "Тестовый Проводник", "depot": "Депо Восток", "brigade": "Бригада 1"}


def seed(db: Session) -> None:
    scenarios = builtin_scenarios()
    for data in scenarios:
        validate_graph(data["graph"])

    for data in scenarios:
        existing = db.query(Scenario).filter_by(title=data["title"]).first()
        if existing is None:
            db.add(Scenario(title=data["title"], description=data["description"], graph=data["graph"]))
        elif existing.graph != data["graph"] or existing.description != data["description"]:
            existing.graph = data["graph"]
            existing.description = data["description"]
            existing.version += 1

    if not db.query(Employee).filter_by(full_name=DEMO_EMPLOYEE["full_name"]).first():
        db.add(Employee(**DEMO_EMPLOYEE))
    db.commit()


def run() -> None:
    with SessionLocal() as db:
        seed(db)
    print("Seed complete.")


if __name__ == "__main__":
    run()
