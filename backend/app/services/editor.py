"""Methodologist editor: drafts are saved freely, validated on demand and on publish.

Publishing copies the draft into the published fields and bumps the version. Attempts that are
already running keep their own graph snapshot, and drafts are never visible in the catalog.
"""

import copy
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Employee, Notification, Role, Scenario
from app.scenarios.errors import ScenarioError
from app.scenarios.validator import collect_errors

TEMPLATE_GRAPH = {
    "initial": {"loyalty": 50, "safety": 50},
    "flags": {},
    "start_node": "start",
    "nodes": {
        "start": {
            "text": "Опишите ситуацию, с которой сталкивается проводник.",
            "choices": [{"id": "a", "text": "Первый вариант действия", "next_node": "end"}],
        },
        "end": {"text": "Чем закончилась ситуация.", "is_ending": True, "ending_summary": "Краткий итог для разбора."},
    },
}


def _published(s: Scenario) -> dict | None:
    if s.version < 1 or s.graph is None:
        return None
    return {"title": s.title, "description": s.description, "tags": s.tags or [], "graph": s.graph}


def _draft(s: Scenario) -> dict:
    return s.draft if s.draft is not None else copy.deepcopy(_published(s))


def draft_errors(draft: dict) -> list[str]:
    errors = []
    if not str(draft.get("title", "")).strip():
        errors.append("title: название обязательно")
    return errors + collect_errors(draft.get("graph"))


def view(s: Scenario) -> dict:
    draft = _draft(s)
    return {
        "id": s.id,
        "key": s.key,
        "origin": s.origin,
        "version": s.version,
        "published_at": s.published_at,
        "updated_at": s.updated_at,
        "published": _published(s),
        "draft": draft,
        "has_unpublished_changes": s.draft is not None,
        "errors": draft_errors(draft),
    }


def list_items(db: Session) -> list[dict]:
    items = []
    for s in db.scalars(select(Scenario).order_by(Scenario.created_at, Scenario.title)):
        draft = _draft(s)
        items.append(
            {
                "id": s.id,
                "title": draft["title"],
                "version": s.version,
                "published": s.version >= 1,
                "has_unpublished_changes": s.draft is not None,
                "origin": s.origin,
                "updated_at": s.updated_at,
            }
        )
    return items


def get(db: Session, scenario_id: str) -> Scenario:
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        raise ScenarioError("scenario_not_found", "scenario not found")
    return scenario


def create(db: Session, title: str, description: str, tags: list[str], graph: dict | None, now: datetime) -> Scenario:
    scenario = Scenario(
        title=title,
        description=description,
        tags=[],
        graph=None,
        version=0,
        origin="editor",
        draft={"title": title, "description": description, "tags": tags, "graph": graph or copy.deepcopy(TEMPLATE_GRAPH)},
        created_at=now,
        updated_at=now,
    )
    db.add(scenario)
    db.commit()
    return scenario


def save_draft(db: Session, scenario: Scenario, draft: dict, now: datetime) -> Scenario:
    scenario.draft = draft
    scenario.updated_at = now
    db.commit()
    return scenario


def discard_draft(db: Session, scenario: Scenario, now: datetime) -> Scenario:
    if scenario.version < 1:
        raise ScenarioError("nothing_published", "у сценария нет опубликованной версии, к которой можно вернуться")
    scenario.draft = None
    scenario.updated_at = now
    db.commit()
    return scenario


def publish(db: Session, scenario: Scenario, now: datetime) -> Scenario:
    draft = _draft(scenario)
    errors = draft_errors(draft)
    if errors:
        raise ScenarioError("invalid_scenario", f"в сценарии {len(errors)} ошибок", errors=errors)
    first = scenario.version < 1
    scenario.title = draft["title"].strip()
    scenario.description = draft.get("description", "")
    scenario.tags = draft.get("tags", [])
    scenario.graph = copy.deepcopy(draft["graph"])
    scenario.version = 1 if first else scenario.version + 1
    scenario.origin = "editor"
    scenario.draft = None
    scenario.published_at = scenario.updated_at = now
    for conductor_id in db.scalars(select(Employee.id).where(Employee.role == Role.conductor.value)):
        db.add(
            Notification(
                employee_id=conductor_id,
                kind="scenario_published",
                title=f"{'Новый сценарий' if first else 'Обновлён сценарий'}: «{scenario.title}»",
                body=f"Версия {scenario.version} доступна в каталоге.",
                link="/scenarios",
                created_at=now,
            )
        )
    db.commit()
    return scenario
