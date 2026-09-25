"""Populate the database with one demo employee and the demo scenario.

Run with: python -m app.seed
"""

from app.core.db import Base, SessionLocal, engine
from app.models.models import Employee, Scenario
from app.scenarios.demo_scenario import DEMO_SCENARIO
from app.scenarios.validator import validate_graph


def run() -> None:
    Base.metadata.create_all(bind=engine)
    validate_graph(DEMO_SCENARIO["graph"])

    db = SessionLocal()
    try:
        if not db.query(Scenario).filter_by(title=DEMO_SCENARIO["title"]).first():
            db.add(
                Scenario(
                    title=DEMO_SCENARIO["title"],
                    description=DEMO_SCENARIO["description"],
                    graph=DEMO_SCENARIO["graph"],
                )
            )
        if not db.query(Employee).filter_by(full_name="Тестовый Проводник").first():
            db.add(Employee(full_name="Тестовый Проводник", depot="Депо Восток", brigade="Бригада 1"))
        db.commit()
    finally:
        db.close()

    print("Seed complete.")


if __name__ == "__main__":
    run()
