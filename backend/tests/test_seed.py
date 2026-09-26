from app.models.models import Attempt, Employee, Scenario
from app.seed import seed


def test_seed_is_idempotent_and_versions_changed_scenarios(session_factory):
    with session_factory() as db:
        seed(db)
        seed(db)
        titles = sorted(s.title for s in db.query(Scenario))
        assert titles == ["Конфликт из-за откинутого кресла", "Место у окна", "Пассажиру стало плохо"]
        assert {s.version for s in db.query(Scenario)} == {1}
        assert db.query(Employee).count() == 7
        assert db.query(Employee).filter_by(role="methodologist").count() == 1
        synthetic = db.query(Attempt).filter_by(is_synthetic=True).count()
        assert synthetic == 11  # a second seed run added none
        assert db.query(Attempt).filter_by(is_synthetic=False).count() == 0

        window = db.query(Scenario).filter_by(title="Место у окна").one()
        window.graph = {**window.graph, "start_node": "tickets"}
        db.commit()

        seed(db)
        db.refresh(window)
        assert window.version == 2
        assert window.graph["start_node"] == "start"
