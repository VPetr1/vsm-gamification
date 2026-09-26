# API для фронтенда

Браузер обращается к API на своём же адресе по префиксу `/api`: в Docker его проксирует nginx, при разработке — Vite.
Сам бэкенд обслуживает пути без префикса (`/attempts`, `/auth/login`), Swagger UI доступен на `http://localhost:8000/docs`.
Примеры ниже — реальные ответы Docker-сборки; идентификаторы и время у вас будут другими. Длинные ответы сокращены, это отмечено
значением `"…"`.

## Общие правила

- **Вход.** `POST /auth/login` ставит cookie `vsm_session` (HttpOnly, SameSite=Lax). Личность и роль берутся только из сессии:
  `employee_id` или роль в теле запроса ни на что не влияют. Без сессии — 401.
- **Время.** Все метки времени — ISO 8601 в UTC (`...Z`).
- **Ошибки домена** имеют единый формат `{"detail": {"code": "...", "message": "...", ...}}`:

| code | HTTP | когда |
|---|---|---|
| `unauthorized` | 401 | нет сессии или она истекла |
| `invalid_credentials` | 401 | неверный логин или пароль (одинаковый ответ для обоих случаев) |
| `forbidden` | 403 | действие только для методиста |
| `attempt_not_found`, `scenario_not_found` | 404 | нет объекта **или** он чужой / не опубликован |
| `step_mismatch` | 409 | устаревший `expected_step`; в ответе `current_step` |
| `timer_not_expired` | 409 | `choice_id: null` до дедлайна; в ответе `deadline` |
| `attempt_finished` / `attempt_not_finished` | 409 | действие не подходит к статусу попытки |
| `nothing_published` | 409 | сброс черновика, у которого нет опубликованной версии |
| `choice_not_available` | 422 | варианта нет **или** он скрыт условием (ответ одинаковый) |
| `choice_required` | 422 | `choice_id: null` на шаге без таймера |
| `invalid_scenario` | 422 | граф не прошёл проверку; в ответе список `errors` с путями |
| `bad_scope` | 422 | неизвестный уровень рейтинга |

## Правила экрана прохождения

1. `attempt_id` хранится в URL; после перезагрузки клиент делает `GET /api/attempts/{id}` и рисует серверное состояние.
2. Каждый выбор отправляется с `expected_step` = `step` из последнего ответа; на время запроса кнопки заблокированы.
3. Таймер считается от `deadline − server_time` на момент ответа плюс прошедшее время по монотонным часам; `deadline: null` — шаг без таймера.
4. На нуле клиент шлёт `{"choice_id": null, "expected_step": step}`. Ответ `timer_not_expired` не повторяется сразу:
   через секунду клиент перечитывает состояние через `GET`, который сам применяет просроченный тайм-аут. Цикла не возникает.
5. `step_mismatch` → перечитать состояние; `visibilitychange` и `online` → перечитать состояние.
6. Ошибка сети показывается как ошибка; результат не придумывается.
7. Состояние не содержит эффектов, условий, переходов и объяснений. После шага в `last_step` приходят фактические изменения шкал уже сделанного выбора,
   а подробный разбор — только после финала.

## 1. Демо-аккаунты и вход

```http
GET /api/auth/demo-accounts
```

Ответ `200`:

```json
[
  {
    "login": "provodnik",
    "full_name": "Алина Демидова",
    "role": "conductor",
    "brigade": "Бригада 1",
    "depot": "Депо Восток"
  },
  {
    "login": "kim",
    "full_name": "Дмитрий Ким",
    "role": "conductor",
    "brigade": "Бригада 2",
    "depot": "Депо Восток"
  },
  {
    "login": "belova",
    "full_name": "Ирина Белова",
    "role": "conductor",
    "brigade": "Бригада 2",
    "depot": "Депо Восток"
  },
  {
    "login": "orlova",
    "full_name": "Ольга Орлова",
    "role": "conductor",
    "brigade": "Бригада 1",
    "depot": "Депо Восток"
  },
  {
    "login": "sergeev",
    "full_name": "Павел Сергеев",
    "role": "conductor",
    "brigade": "Бригада 1",
    "depot": "Депо Восток"
  },
  {
    "login": "nazarov",
    "full_name": "Тимур Назаров",
    "role": "conductor",
    "brigade": "Бригада 3",
    "depot": "Депо Запад"
  },
  {
    "login": "metodist",
    "full_name": "Наталья Крылова",
    "role": "methodologist",
    "brigade": "",
    "depot": "Учебный центр"
  }
]
```

```http
GET /api/scenarios
```

Ответ `401`:

```json
{
  "detail": {
    "code": "unauthorized",
    "message": "нужно войти в систему"
  }
}
```

```http
POST /api/auth/login
Content-Type: application/json

{
  "login": "orlova",
  "password": "vsm-demo"
}
```

Ответ `200`:

```json
{
  "id": "6545432b-eb05-4175-ac98-c64066dd851e",
  "login": "orlova",
  "full_name": "Ольга Орлова",
  "role": "conductor",
  "brigade": "Бригада 1",
  "depot": "Депо Восток"
}
```

## 2. Каталог

Только опубликованные сценарии; `my_best_score` и `in_progress_attempt_id` — прогресс текущего пользователя.

```http
GET /api/scenarios
```

Ответ `200`:

```json
[
  {
    "id": "cf8ee6c4-e91e-4505-b18f-28f649ebe058",
    "title": "Конфликт из-за откинутого кресла",
    "description": "Пассажир в вагоне 3 конфликтует с соседом из-за откинутого кресла. Синтетический учебный сценарий.",
    "tags": [
      "communication",
      "safety",
      "stress_resistance",
      "конфликт"
    ],
    "version": 1,
    "my_best_score": 48,
    "in_progress_attempt_id": null
  },
  {
    "id": "7a081f00-b8d8-4941-9098-fdd4981874c2",
    "title": "Место у окна",
    "description": "Мужчина занял место девушки у окна, перепутав вагон, а его чемодан перегораживает проход. Синтетический учебный сценарий; объяснения — методические, не официальный регламент.",
    "tags": [
      "communication",
      "safety",
      "stress_resistance",
      "конфликт",
      "багаж"
    ],
    "version": 1,
    "my_best_score": 85,
    "in_progress_attempt_id": null
  }
]
```

## 3. Начало попытки

`visual` — вычисленные на сервере метаданные сцены: кто присутствует, их настроение, видимые предметы. Условий в ответе нет.

```http
POST /api/attempts
Content-Type: application/json

{
  "scenario_id": "7a081f00-b8d8-4941-9098-fdd4981874c2"
}
```

Ответ `201`:

```json
{
  "attempt_id": "64a116e9-8b1d-44c0-bcda-9e46f9adb953",
  "scenario_id": "7a081f00-b8d8-4941-9098-fdd4981874c2",
  "scenario_title": "Место у окна",
  "scenario_version": 1,
  "loyalty": 60,
  "safety": 80,
  "status": "in_progress",
  "step": 0,
  "node": {
    "node_id": "start",
    "text": "Вагон 5. К вам подходит девушка: «В моём кресле 7А сидит мужчина и не хочет вставать». Мужчина устроился у окна, его большой чемодан стоит прямо в проходе.",
    "timer_seconds": null,
    "choices": [
      {
        "id": "calm",
        "text": "Подойти, представиться и спокойно выяснить, что произошло"
      },
      {
        "id": "order",
        "text": "Строго потребовать от мужчины немедленно освободить чужое место"
      },
      {
        "id": "ignore",
        "text": "Сказать девушке, что разберётесь позже, и продолжить обход"
      }
    ],
    "is_ending": false,
    "ending_summary": null,
    "visual": {
      "speaker": "woman",
      "characters": [
        {
          "id": "man",
          "name": "Пассажир у окна",
          "figure": "man",
          "pose": "sitting",
          "position": "left",
          "mood": "calm"
        },
        {
          "id": "woman",
          "name": "Пассажирка с билетом на 7А",
          "figure": "woman",
          "pose": "standing",
          "position": "right",
          "mood": "upset"
        }
      ],
      "props": [
        "suitcase"
      ]
    }
  },
  "node_shown_at": "2026-09-26T10:35:09.346440Z",
  "deadline": null,
  "server_time": "2026-09-26T10:35:09.346440Z",
  "last_step": null
}
```

## 4. Выбор

```http
POST /api/attempts/64a116e9-8b1d-44c0-bcda-9e46f9adb953/choice
Content-Type: application/json

{
  "choice_id": "calm",
  "expected_step": 0
}
```

Ответ `200`:

```json
{
  "attempt_id": "64a116e9-8b1d-44c0-bcda-9e46f9adb953",
  "scenario_id": "7a081f00-b8d8-4941-9098-fdd4981874c2",
  "scenario_title": "Место у окна",
  "scenario_version": 1,
  "loyalty": 65,
  "safety": 80,
  "status": "in_progress",
  "step": 1,
  "node": {
    "node_id": "suitcase",
    "text": "Поезд набирает скорость. По проходу идёт пассажирка с горячим чаем, следом едет тележка сервиса. Чемодан мужчины перегораживает проход — решать нужно сейчас.",
    "timer_seconds": 20,
    "choices": [
      {
        "id": "stow_together",
        "text": "Вежливо попросить мужчину помочь и вместе убрать чемодан в багажное отделение"
      },
      {
        "id": "stow_yourself",
        "text": "Самому откатить чемодан к багажному отделению, предупредив владельца"
      },
      {
        "id": "leave_it",
        "text": "Оставить чемодан: сначала выяснить, чьё это место"
      }
    ],
    "is_ending": false,
    "ending_summary": null,
    "visual": {
      "speaker": null,
      "characters": [
        {
          "id": "man",
          "name": "Пассажир у окна",
          "figure": "man",
          "pose": "sitting",
          "position": "left",
          "mood": "calm"
        },
        {
          "id": "woman",
          "name": "Пассажирка с билетом на 7А",
          "figure": "woman",
          "pose": "standing",
          "position": "right",
          "mood": "worried"
        }
      ],
      "props": [
        "suitcase"
      ]
    }
  },
  "node_shown_at": "2026-09-26T10:35:09.372021Z",
  "deadline": "2026-09-26T10:35:29.372021Z",
  "server_time": "2026-09-26T10:35:09.372021Z",
  "last_step": {
    "step": 1,
    "node_id": "start",
    "choice_id": "calm",
    "timed_out": false,
    "loyalty_delta": 5,
    "safety_delta": 0
  }
}
```

Ранний тайм-аут и повтор шага не меняют состояние:

```http
POST /api/attempts/64a116e9-8b1d-44c0-bcda-9e46f9adb953/choice
Content-Type: application/json

{
  "choice_id": null,
  "expected_step": 1
}
```

Ответ `409`:

```json
{
  "detail": {
    "code": "timer_not_expired",
    "message": "timeout requested before the deadline",
    "deadline": "2026-09-26T10:35:29.372021+00:00"
  }
}
```

```http
POST /api/attempts/64a116e9-8b1d-44c0-bcda-9e46f9adb953/choice
Content-Type: application/json

{
  "choice_id": "calm",
  "expected_step": 0
}
```

Ответ `409`:

```json
{
  "detail": {
    "code": "step_mismatch",
    "message": "expected step 0, but the attempt is at step 1",
    "current_step": 1
  }
}
```

## 5. Тайм-аут

```http
POST /api/attempts/64a116e9-8b1d-44c0-bcda-9e46f9adb953/choice
Content-Type: application/json

{
  "choice_id": null,
  "expected_step": 1
}
```

Ответ `200`:

```json
{
  "attempt_id": "64a116e9-8b1d-44c0-bcda-9e46f9adb953",
  "scenario_id": "7a081f00-b8d8-4941-9098-fdd4981874c2",
  "scenario_title": "Место у окна",
  "scenario_version": 1,
  "loyalty": 60,
  "safety": 60,
  "status": "in_progress",
  "step": 2,
  "node": {
    "node_id": "trip",
    "text": "Пассажирка споткнулась о чемодан, чай разлился по полу. Она не пострадала, но испугана, а в проходе скользко.",
    "timer_seconds": null,
    "choices": [
      {
        "id": "help_alone",
        "text": "Убедиться, что пассажирка в порядке, самому убрать чемодан и вытереть пол"
      },
      {
        "id": "call_colleague",
        "text": "Позвать коллегу на уборку, а самому заняться пассажиркой и чемоданом"
      },
      {
        "id": "back_to_dispute",
        "text": "Вернуться к спору о месте — пол вытрут позже"
      }
    ],
    "is_ending": false,
    "ending_summary": null,
    "visual": {
      "speaker": null,
      "characters": [
        {
          "id": "man",
          "name": "Пассажир у окна",
          "figure": "man",
          "pose": "sitting",
          "position": "left",
          "mood": "worried"
        },
        {
          "id": "woman",
          "name": "Пассажирка с билетом на 7А",
          "figure": "woman",
          "pose": "standing",
          "position": "right",
          "mood": "scared"
        }
      ],
      "props": [
        "suitcase",
        "spill"
      ]
    }
  },
  "node_shown_at": "2026-09-26T10:35:29.815132Z",
  "deadline": null,
  "server_time": "2026-09-26T10:35:29.815132Z",
  "last_step": {
    "step": 2,
    "node_id": "suitcase",
    "choice_id": null,
    "timed_out": true,
    "loyalty_delta": -5,
    "safety_delta": -20
  }
}
```

## 6. Восстановление после перезагрузки

Игрок вернулся через 21 секунду после старта критического шага; `GET` применил тайм-аут ровно один раз.

```http
GET /api/attempts/a31b4b22-aedb-4630-9cb0-b6dcda54cd3f
```

Ответ `200`:

```json
{
  "attempt_id": "a31b4b22-aedb-4630-9cb0-b6dcda54cd3f",
  "scenario_id": "7a081f00-b8d8-4941-9098-fdd4981874c2",
  "scenario_title": "Место у окна",
  "scenario_version": 1,
  "loyalty": 60,
  "safety": 60,
  "status": "in_progress",
  "step": 2,
  "node": {
    "node_id": "trip",
    "text": "Пассажирка споткнулась о чемодан, чай разлился по полу. Она не пострадала, но испугана, а в проходе скользко.",
    "timer_seconds": null,
    "choices": [
      {
        "id": "help_alone",
        "text": "Убедиться, что пассажирка в порядке, самому убрать чемодан и вытереть пол"
      },
      {
        "id": "call_colleague",
        "text": "Позвать коллегу на уборку, а самому заняться пассажиркой и чемоданом"
      },
      {
        "id": "back_to_dispute",
        "text": "Вернуться к спору о месте — пол вытрут позже"
      }
    ],
    "is_ending": false,
    "ending_summary": null,
    "visual": {
      "speaker": null,
      "characters": [
        {
          "id": "man",
          "name": "Пассажир у окна",
          "figure": "man",
          "pose": "sitting",
          "position": "left",
          "mood": "worried"
        },
        {
          "id": "woman",
          "name": "Пассажирка с билетом на 7А",
          "figure": "woman",
          "pose": "standing",
          "position": "right",
          "mood": "scared"
        }
      ],
      "props": [
        "suitcase",
        "spill"
      ]
    }
  },
  "node_shown_at": "2026-09-26T10:35:50.948160Z",
  "deadline": null,
  "server_time": "2026-09-26T10:35:50.948160Z",
  "last_step": {
    "step": 2,
    "node_id": "suitcase",
    "choice_id": null,
    "timed_out": true,
    "loyalty_delta": -5,
    "safety_delta": -20
  }
}
```

## 7. Финал и разбор

```http
POST /api/attempts/64a116e9-8b1d-44c0-bcda-9e46f9adb953/choice
Content-Type: application/json

{
  "choice_id": "escort",
  "expected_step": 5
}
```

Ответ `200`:

```json
{
  "attempt_id": "64a116e9-8b1d-44c0-bcda-9e46f9adb953",
  "scenario_id": "7a081f00-b8d8-4941-9098-fdd4981874c2",
  "scenario_title": "Место у окна",
  "scenario_version": 1,
  "loyalty": 85,
  "safety": 75,
  "status": "finished",
  "step": 6,
  "node": {
    "node_id": "end_calm",
    "text": "Мужчина благодарит за помощь и уходит в свой вагон, девушка спокойно занимает место у окна. Проход свободен, в вагоне тихо.",
    "timer_seconds": null,
    "choices": [],
    "is_ending": true,
    "ending_summary": "Спокойное разрешение: вы проверили факты, обеспечили безопасность прохода и сохранили уважение обоих пассажиров.",
    "visual": {
      "speaker": null,
      "characters": [
        {
          "id": "man",
          "name": "Пассажир у окна",
          "figure": "man",
          "pose": "sitting",
          "position": "left",
          "mood": "happy"
        },
        {
          "id": "woman",
          "name": "Пассажирка с билетом на 7А",
          "figure": "woman",
          "pose": "standing",
          "position": "right",
          "mood": "happy"
        }
      ],
      "props": []
    }
  },
  "node_shown_at": "2026-09-26T10:35:29.884346Z",
  "deadline": null,
  "server_time": "2026-09-26T10:35:29.884346Z",
  "last_step": {
    "step": 6,
    "node_id": "resolution",
    "choice_id": "escort",
    "timed_out": false,
    "loyalty_delta": 5,
    "safety_delta": 0
  }
}
```

```http
GET /api/attempts/64a116e9-8b1d-44c0-bcda-9e46f9adb953/result
```

Ответ `200`:

```json
{
  "attempt_id": "64a116e9-8b1d-44c0-bcda-9e46f9adb953",
  "scenario_id": "7a081f00-b8d8-4941-9098-fdd4981874c2",
  "scenario_title": "Место у окна",
  "scenario_version": 1,
  "status": "finished",
  "started_at": "2026-09-26T10:35:09.346440Z",
  "finished_at": "2026-09-26T10:35:29.884346Z",
  "initial": {
    "loyalty": 60,
    "safety": 80
  },
  "final": {
    "loyalty": 85,
    "safety": 75
  },
  "ending": {
    "node_id": "end_calm",
    "text": "Мужчина благодарит за помощь и уходит в свой вагон, девушка спокойно занимает место у окна. Проход свободен, в вагоне тихо.",
    "summary": "Спокойное разрешение: вы проверили факты, обеспечили безопасность прохода и сохранили уважение обоих пассажиров.",
    "outcome": "calm_resolution"
  },
  "steps": [
    {
      "step": 1,
      "node_id": "start",
      "situation": "Вагон 5. К вам подходит девушка: «В моём кресле 7А сидит мужчина и не хочет вставать». Мужчина устроился у окна, его большой чемодан стоит прямо в проходе.",
      "choice_id": "calm",
      "choice_text": "Подойти, представиться и спокойно выяснить, что произошло",
      "timed_out": false,
      "loyalty_delta": 5,
      "safety_delta": 0,
      "loyalty_after": 65,
      "safety_after": 80,
      "explanation": "Спокойный тон и готовность выслушать обе стороны снижают напряжение: пассажиры настроены на диалог, а не на спор.",
      "lesson": "Лучший первый шаг — подойти, представиться и спокойно выслушать обе стороны: так вы получаете факты и снижаете напряжение, никого заранее не обвиняя.",
      "assessment": [
        {
          "id": "communication",
          "title": "Коммуникация",
          "earned": 2,
          "max": 2
        },
        {
          "id": "safety",
          "title": "Безопасность",
          "earned": 1,
          "max": 1
        }
      ]
    },
    {
      "step": 2,
      "node_id": "suitcase",
      "situation": "Поезд набирает скорость. По проходу идёт пассажирка с горячим чаем, следом едет тележка сервиса. Чемодан мужчины перегораживает проход — решать нужно сейчас.",
      "choice_id": null,
      "choice_text": null,
      "timed_out": true,
      "loyalty_delta": -5,
      "safety_delta": -20,
      "loyalty_after": 60,
      "safety_after": 60,
      "explanation": "Время вышло: пассажирка споткнулась о чемодан. В критической ситуации промедление опаснее любой неидеальной реакции.",
      "lesson": "В учебной модели свободный проход — приоритет: по нему ходят пассажиры и персонал, и он нужен при эвакуации. Сначала устраните угрозу, спор о месте подождёт.",
      "assessment": [
        {
          "id": "communication",
          "title": "Коммуникация",
          "earned": 0,
          "max": 1
        },
        {
          "id": "safety",
          "title": "Безопасность",
          "earned": 0,
          "max": 2
        },
        {
          "id": "stress_resistance",
          "title": "Стрессоустойчивость",
          "earned": 0,
          "max": 2
        }
      ]
    },
    "…"
  ],
  "competencies": [
    {
      "id": "communication",
      "title": "Коммуникация",
      "description": "Тон, деэскалация, работа с обеими сторонами конфликта.",
      "earned": 8,
      "max": 9,
      "percent": 89
    },
    {
      "id": "safety",
      "title": "Безопасность",
      "description": "Своевременное устранение угроз в салоне и проходе.",
      "earned": 3,
      "max": 5,
      "percent": 60
    },
    {
      "id": "first_aid",
      "title": "Первая помощь",
      "description": "Действия при ухудшении самочувствия пассажира.",
      "earned": 0,
      "max": 0,
      "percent": null
    },
    {
      "id": "stress_resistance",
      "title": "Стрессоустойчивость",
      "description": "Учебный показатель: качество действий в шагах с таймером. Не психологическая оценка.",
      "earned": 0,
      "max": 2,
      "percent": 0
    }
  ],
  "reward": {
    "score": 80,
    "xp_gained": 0,
    "best_score": 85,
    "achievements": [
      {
        "id": "diplomat",
        "title": "Дипломат"
      }
    ]
  }
}
```

До финала разбор недоступен:

```http
GET /api/attempts/a31b4b22-aedb-4630-9cb0-b6dcda54cd3f/result
```

Ответ `409`:

```json
{
  "detail": {
    "code": "attempt_not_finished",
    "message": "the result is available after the attempt is finished"
  }
}
```

## 8. Профиль, история, рейтинг, уведомления

```http
GET /api/me/profile
```

Ответ `200`:

```json
{
  "full_name": "Ольга Орлова",
  "role": "conductor",
  "brigade": "Бригада 1",
  "depot": "Депо Восток",
  "xp": 133,
  "level": {
    "number": 3,
    "title": "Опытный проводник",
    "min_xp": 120,
    "next_min_xp": 200
  },
  "achievements": [
    {
      "id": "first_trip",
      "title": "Первый рейс",
      "description": "Завершите первый сценарий.",
      "earned": true,
      "awarded_at": "2026-09-24T10:17:58.176628Z",
      "attempt_id": "340eeeb0-1b40-4683-8c98-c23dcd7a8fcb"
    },
    "…"
  ],
  "stats": {
    "finished_attempts": 3,
    "scenarios_completed": 2,
    "scenarios_published": 2
  },
  "competencies": [
    {
      "id": "communication",
      "title": "Коммуникация",
      "description": "Тон, деэскалация, работа с обеими сторонами конфликта.",
      "earned": 9,
      "max": 11,
      "percent": 82
    },
    {
      "id": "safety",
      "title": "Безопасность",
      "description": "Своевременное устранение угроз в салоне и проходе.",
      "earned": 4,
      "max": 6,
      "percent": 67
    },
    "…"
  ],
  "weakest": {
    "id": "stress_resistance",
    "title": "Стрессоустойчивость",
    "percent": 25
  },
  "recommendation": {
    "scenario_id": "7a081f00-b8d8-4941-9098-fdd4981874c2",
    "title": "Место у окна",
    "kind": "replay",
    "reason": "В последнем прохождении «Место у окна» по компетенции «Стрессоустойчивость» набрано 0 из 2.",
    "goal": "Цель: больше 0 из 2 баллов по компетенции «Стрессоустойчивость»."
  },
  "aggregation": "последнее завершённое прохождение каждого сценария; сумма набранных и максимальных баллов"
}
```

```http
GET /api/me/attempts
```

Ответ `200`:

```json
[
  {
    "attempt_id": "a31b4b22-aedb-4630-9cb0-b6dcda54cd3f",
    "scenario_id": "7a081f00-b8d8-4941-9098-fdd4981874c2",
    "scenario_title": "Место у окна",
    "scenario_version": 1,
    "status": "in_progress",
    "started_at": "2026-09-26T10:35:29.910119Z",
    "finished_at": null,
    "score": null,
    "xp_gained": null,
    "outcome": null,
    "synthetic": false,
    "competencies": []
  },
  "…"
]
```

```http
GET /api/leaderboard?scope=brigade
```

Ответ `200`:

```json
{
  "scope": "brigade",
  "scope_label": "Бригада 1, Депо Восток",
  "entries": [
    {
      "rank": 1,
      "name": "Павел Сергеев",
      "brigade": "Бригада 1",
      "depot": "Депо Восток",
      "level": 3,
      "level_title": "Опытный проводник",
      "xp": 151,
      "completed": 2,
      "is_me": false,
      "synthetic": true
    },
    {
      "rank": 2,
      "name": "Ольга Орлова",
      "brigade": "Бригада 1",
      "depot": "Депо Восток",
      "level": 3,
      "level_title": "Опытный проводник",
      "xp": 133,
      "completed": 2,
      "is_me": true,
      "synthetic": true
    },
    {
      "rank": 3,
      "name": "Алина Демидова",
      "brigade": "Бригада 1",
      "depot": "Депо Восток",
      "level": 2,
      "level_title": "Проводник",
      "xp": 58,
      "completed": 1,
      "is_me": false,
      "synthetic": false
    }
  ]
}
```

```http
GET /api/me/notifications
```

Ответ `200`:

```json
{
  "unread": 5,
  "items": [
    {
      "id": "a42ce8bf-193e-47fa-9f4e-07a5e0d0d720",
      "kind": "achievement",
      "title": "Достижение «Дипломат»",
      "body": "Выполните условия деэскалации, заданные в сценарии.",
      "link": "/attempts/64a116e9-8b1d-44c0-bcda-9e46f9adb953/result",
      "created_at": "2026-09-26T10:35:29.884346Z",
      "read": false
    },
    {
      "id": "b4c8ffa3-90e8-41af-bba5-231d803214a1",
      "kind": "level_up",
      "title": "Новый уровень: Проводник",
      "body": "Опыт: 85.",
      "link": "/profile",
      "created_at": "2026-09-24T10:17:58.176628Z",
      "read": false
    },
    "…"
  ]
}
```

## 9. Редактор (только методист)

```http
GET /api/editor/scenarios
```

Ответ `403`:

```json
{
  "detail": {
    "code": "forbidden",
    "message": "доступно только методисту"
  }
}
```

```http
GET /api/editor/scenarios
```

Ответ `200`:

```json
[
  {
    "id": "cf8ee6c4-e91e-4505-b18f-28f649ebe058",
    "title": "Конфликт из-за откинутого кресла",
    "version": 1,
    "published": true,
    "has_unpublished_changes": false,
    "origin": "builtin",
    "updated_at": "2026-09-26T10:17:23.176628Z"
  },
  {
    "id": "7a081f00-b8d8-4941-9098-fdd4981874c2",
    "title": "Место у окна",
    "version": 1,
    "published": true,
    "has_unpublished_changes": false,
    "origin": "builtin",
    "updated_at": "2026-09-26T10:17:23.176628Z"
  }
]
```

```http
POST /api/editor/scenarios
Content-Type: application/json

{
  "title": "Пассажиру стало плохо",
  "tags": [
    "first_aid"
  ]
}
```

Ответ `201`:

```json
{
  "id": "b6d92e24-9a2d-4c0d-a2eb-c41d5b81bd5d",
  "key": null,
  "origin": "editor",
  "version": 0,
  "published_at": null,
  "updated_at": "2026-09-26T10:35:51.120296Z",
  "published": null,
  "draft": {
    "title": "Пассажиру стало плохо",
    "description": "",
    "tags": [
      "first_aid"
    ],
    "graph": "…"
  },
  "has_unpublished_changes": true,
  "errors": []
}
```

Черновик сохраняется даже с ошибками, ответ перечисляет их с путями:

```http
PUT /api/editor/scenarios/b6d92e24-9a2d-4c0d-a2eb-c41d5b81bd5d/draft
Content-Type: application/json

{
  "title": "Пассажиру стало плохо",
  "description": "",
  "tags": [
    "first_aid"
  ],
  "graph": "…"
}
```

Ответ `200`:

```json
{
  "id": "b6d92e24-9a2d-4c0d-a2eb-c41d5b81bd5d",
  "key": null,
  "origin": "editor",
  "version": 0,
  "published_at": null,
  "updated_at": "2026-09-26T10:35:51.128331Z",
  "published": null,
  "draft": {
    "title": "Пассажиру стало плохо",
    "description": "",
    "tags": [
      "first_aid"
    ],
    "graph": "…"
  },
  "has_unpublished_changes": true,
  "errors": [
    "nodes.start.choices[0].next_node: points to unknown node 'ghost'"
  ]
}
```

```http
POST /api/editor/scenarios/b6d92e24-9a2d-4c0d-a2eb-c41d5b81bd5d/publish
```

Ответ `422`:

```json
{
  "detail": {
    "code": "invalid_scenario",
    "message": "в сценарии 1 ошибок",
    "errors": [
      "nodes.start.choices[0].next_node: points to unknown node 'ghost'"
    ]
  }
}
```

```http
POST /api/editor/scenarios/b6d92e24-9a2d-4c0d-a2eb-c41d5b81bd5d/publish
```

Ответ `200`:

```json
{
  "id": "b6d92e24-9a2d-4c0d-a2eb-c41d5b81bd5d",
  "key": null,
  "origin": "editor",
  "version": 1,
  "published_at": "2026-09-26T10:35:51.139437Z",
  "updated_at": "2026-09-26T10:35:51.139437Z",
  "published": {
    "title": "Пассажиру стало плохо",
    "description": "",
    "tags": [
      "first_aid"
    ],
    "graph": "…"
  },
  "draft": {
    "title": "Пассажиру стало плохо",
    "description": "",
    "tags": [
      "first_aid"
    ],
    "graph": "…"
  },
  "has_unpublished_changes": false,
  "errors": []
}
```

## 10. Прочее

- `POST /auth/logout` → 204, cookie удаляется, сессия в БД стирается.
- `GET /auth/me` — текущий пользователь.
- `POST /me/notifications/{id}/read`, `POST /me/notifications/read-all` → 204.
- `DELETE /editor/scenarios/{id}/draft` — вернуть черновик к опубликованной версии.
- `POST /scenarios` (методист) — опубликовать граф сразу, без черновика (интеграционный путь); `GET /employees`, `POST /employees` — справочник, только методист.
- `GET /health` → `{"status": "ok"}`.
