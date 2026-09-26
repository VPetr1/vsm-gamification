# Архитектура

## Компоненты

```mermaid
flowchart LR
    subgraph Browser["Браузер"]
        SPA["React SPA<br/>каталог · прохождение · разбор<br/>профиль · рейтинг · редактор"]
    end
    subgraph Docker["docker compose"]
        NGINX["nginx<br/>статика SPA + прокси /api"]
        subgraph API["FastAPI (backend)"]
            ROUTES["api/*<br/>auth · scenarios · attempts<br/>me · leaderboard · editor"]
            SERVICES["services/*<br/>attempts · rewards · competency<br/>profile · editor · auth"]
            ENGINE["scenarios/engine<br/>conditions · validator · visual"]
            RULES["gamification/*<br/>уровни · достижения · компетенции"]
        end
        DB[("PostgreSQL<br/>Alembic 0001–0008")]
    end
    SPA -- "/api, cookie vsm_session" --> NGINX
    NGINX -- "proxy_pass" --> ROUTES
    ROUTES --> SERVICES
    SERVICES --> ENGINE
    SERVICES --> RULES
    SERVICES --> DB
    HR["HR / LMS (интеграция)"] -. "REST + OpenAPI" .-> ROUTES
```

- **Один origin.** SPA и API отдаются с одного адреса, cookie сессии first-party, CORS выключен (включается списком `CORS_ORIGINS`).
- **Движок не знает про HTTP и конкретные сценарии.** Весь контент — JSON-граф; новые сценарии, достижения по условиям и
  визуальные метаданные добавляются данными (редактор, импорт JSON, файлы в `backend/app/scenarios/data`).
- **Горизонтальное масштабирование.** Бэкенд без состояния в памяти: сессии, попытки и награды — в PostgreSQL. Корректность при
  нескольких экземплярах обеспечивают блокировки строк и уникальные индексы, а не память процесса.

## Шаг сценария

```mermaid
sequenceDiagram
    participant C as Клиент
    participant A as API
    participant S as services/attempts
    participant E as Движок
    participant R as services/rewards
    participant D as PostgreSQL
    C->>A: POST /attempts/{id}/choice {choice_id | null, expected_step}
    A->>A: сессия → сотрудник (не из тела запроса)
    A->>S: submit_choice
    S->>D: SELECT attempt FOR UPDATE (только своя попытка)
    S->>E: apply_choice
    E->>E: статус, expected_step → 409 при несовпадении
    E->>E: now ≥ deadline ? тайм-аут : видимый вариант (условие до шага)
    E->>E: оценка компетенций по видимым вариантам
    E->>E: effects → clamp 0..100 → set_flags → переход
    alt финальный узел
        S->>R: apply_rewards (блокировка сотрудника)
        R->>D: результат, лучший результат, опыт, достижения, уведомления
    end
    S->>D: INSERT choice_logs (UNIQUE attempt_id, step) + COMMIT
    A-->>C: состояние: узел, visual, шкалы, step, deadline, server_time, last_step
```

`GET /attempts/{id}` выполняет ту же транзакцию для просроченного таймера, поэтому восстановленная страница показывает реальный
исход, а награды не дублируются.

## Данные

| Таблица | Назначение |
|---|---|
| `employees` | вымышленные сотрудники: бригада, депо, логин, хэш пароля, роль, признак синтетических данных |
| `auth_sessions` | сессии: SHA-256 токена, срок действия |
| `scenarios` | опубликованная версия (граф, теги, версия), черновик редактора, ключ встроенного сценария |
| `attempts` | попытка: снимок графа и версии, шкалы, флаги, шаг, итоги компетенций, результат и полученный опыт |
| `choice_logs` | шаг попытки: решение или тайм-аут, фактические изменения, оценка компетенций; `UNIQUE(attempt_id, step)` |
| `scenario_bests` | лучший результат сотрудника по сценарию; опыт = их сумма |
| `employee_achievements` | достижения; `UNIQUE(employee_id, achievement_id)` |
| `notifications` | внутренние уведомления |

## Структура репозитория

```
backend/
  app/api/            HTTP-роуты, зависимости авторизации, коды ошибок
  app/services/       сценарии использования: попытки, награды, компетенции, профиль, редактор, вход
  app/scenarios/      движок, условия, валидатор, визуальные метаданные, встроенные сценарии (data/*.json)
  app/gamification/   правила уровней, достижений и компетенций
  migrations/         Alembic
  tests/              pytest (SQLite + отдельный тест гонки на PostgreSQL)
frontend/
  src/pages/          страницы
  src/hooks/          прохождение (useAttemptPlay), загрузка данных
  src/scene/          SVG-вагон, персонажи и настроения
  src/editor/         формы редактора, конструктор условий, операции над графом
docs/                 архитектура, формат сценария, API, правила оценки, маршрут демонстрации
```
