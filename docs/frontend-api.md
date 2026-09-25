# API для фронтенда

Базовый URL при локальном запуске: `http://localhost:8000`. Интерактивная схема: `/docs` (Swagger UI), `/openapi.json`.
Все примеры ниже — реальные ответы сервера на PostgreSQL (сценарий «Место у окна»); идентификаторы и время у вас будут другими.

Все метки времени — ISO 8601 в UTC (`...Z`). Ошибки домена имеют единый формат:

```json
{"detail": {"code": "machine_readable_code", "message": "текст для разработчика", "...": "доп. поля"}}
```

| code | HTTP | когда |
|---|---|---|
| `attempt_not_found`, `employee_not_found`, `scenario_not_found` | 404 | нет такого объекта |
| `step_mismatch` | 409 | `expected_step` устарел (двойной клик, вторая вкладка, повтор запроса); в ответе `current_step` |
| `timer_not_expired` | 409 | `choice_id: null` до дедлайна; в ответе `deadline` |
| `attempt_finished` | 409 | попытка уже завершена |
| `attempt_not_finished` | 409 | результат запрошен до финала |
| `choice_not_available` | 422 | такого варианта нет **или** он скрыт условием (ответ одинаковый, скрытые ветки не раскрываются) |
| `choice_required` | 422 | `choice_id: null` на шаге без таймера |
| `invalid_scenario` | 422 | некорректный граф в `POST /scenarios`; в ответе список `errors` |

Ошибки валидации тела запроса (FastAPI/Pydantic) приходят в стандартном формате FastAPI с `detail: [...]` и HTTP 422.

## Поток экрана

```
GET /scenarios ──► POST /attempts ──► [показ узла] ──► POST /attempts/{id}/choice ──┐
                                           ▲                                        │
                                           └──────────── следующий узел ◄───────────┘
                     перезагрузка страницы: GET /attempts/{id}  (догоняет истёкший таймер)
                     финал (status = finished): GET /attempts/{id}/result
```

Правила для клиента:

1. Храните `attempt_id` (например, в URL) и **всегда** отправляйте `expected_step` = `step` из последнего полученного состояния.
2. Таймер рисуйте от серверных полей: осталось `deadline − server_time` на момент ответа (не полагайтесь на часы устройства). `deadline: null` — у шага нет таймера.
3. Когда локальный отсчёт дошёл до нуля — отправьте `{"choice_id": null, "expected_step": step}`. Если сервер ответит `timer_not_expired` (часы клиента спешат), подождите до `deadline` из ответа и повторите.
4. Выбор, отправленный в момент дедлайна или позже, сервер засчитывает как тайм-аут (`last_step.timed_out: true`) — покажите игроку, что время вышло.
5. На `step_mismatch` сделайте `GET /attempts/{id}` и отрисуйте актуальное состояние.
6. Состояние не содержит эффектов, условий, переходов и объяснений — они видны только в результате после финала.

---

## 1. Каталог сценариев

```http
GET /scenarios
```

Ответ `200`:

```json
[
  {
    "id": "05a8f6cd-4b2d-4548-9624-d1cce3b62cb2",
    "title": "Конфликт из-за откинутого кресла",
    "description": "Пассажир в вагоне 3 конфликтует с соседом из-за откинутого кресла.",
    "version": 1
  },
  {
    "id": "5e5e6827-68bd-4b3e-ac1a-d23f14d7ac91",
    "title": "Место у окна",
    "description": "Мужчина занял место девушки у окна, перепутав вагон, а его чемодан перегораживает проход. Синтетический учебный сценарий.",
    "version": 1
  }
]
```

`version` растёт при изменении сценария. Уже начатые попытки продолжают идти по снимку той версии, с которой начались (`scenario_version` в состоянии).

## 2. Начать попытку

```http
POST /attempts
Content-Type: application/json

{
  "employee_id": "8893f501-1309-4468-b1fe-90962b83afcd",
  "scenario_id": "5e5e6827-68bd-4b3e-ac1a-d23f14d7ac91"
}
```

Ответ `201`:

```json
{
  "attempt_id": "ad243948-f9ab-4e14-94a0-8e0f1b9e7b4e",
  "scenario_id": "5e5e6827-68bd-4b3e-ac1a-d23f14d7ac91",
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
    "ending_summary": null
  },
  "node_shown_at": "2026-09-25T15:53:15.022209Z",
  "deadline": null,
  "server_time": "2026-09-25T15:53:15.022209Z",
  "last_step": null
}
```

`timer_seconds: null` и `deadline: null` — первый шаг без таймера, можно думать сколько угодно; `choice_id: null` здесь вернёт `choice_required`.

## 3. Сделать выбор

```http
POST /attempts/ad243948-f9ab-4e14-94a0-8e0f1b9e7b4e/choice
Content-Type: application/json

{
  "choice_id": "calm",
  "expected_step": 0
}
```

Ответ `200`:

```json
{
  "attempt_id": "ad243948-f9ab-4e14-94a0-8e0f1b9e7b4e",
  "scenario_id": "5e5e6827-68bd-4b3e-ac1a-d23f14d7ac91",
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
    "ending_summary": null
  },
  "node_shown_at": "2026-09-25T15:53:15.031422Z",
  "deadline": "2026-09-25T15:53:35.031422Z",
  "server_time": "2026-09-25T15:53:15.031422Z",
  "last_step": {
    "step": 1,
    "node_id": "start",
    "choice_id": "calm",
    "timed_out": false
  }
}
```

Теперь у узла есть таймер: 20 секунд, `deadline` = `node_shown_at` + 20 с. `last_step` описывает только что применённый шаг.

Попытка тайм-аута раньше срока — состояние не меняется:

```http
POST /attempts/ad243948-f9ab-4e14-94a0-8e0f1b9e7b4e/choice
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
    "deadline": "2026-09-25T15:53:35.031422+00:00"
  }
}
```

Повтор уже применённого шага (двойной клик) — состояние не меняется, лога второго шага нет:

```http
POST /attempts/ad243948-f9ab-4e14-94a0-8e0f1b9e7b4e/choice
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

## 4. Тайм-аут

После наступления `deadline` клиент отправляет пустой выбор:

```http
POST /attempts/ad243948-f9ab-4e14-94a0-8e0f1b9e7b4e/choice
Content-Type: application/json

{
  "choice_id": null,
  "expected_step": 1
}
```

Ответ `200`:

```json
{
  "attempt_id": "ad243948-f9ab-4e14-94a0-8e0f1b9e7b4e",
  "scenario_id": "5e5e6827-68bd-4b3e-ac1a-d23f14d7ac91",
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
    "ending_summary": null
  },
  "node_shown_at": "2026-09-25T15:53:35.364172Z",
  "deadline": null,
  "server_time": "2026-09-25T15:53:35.364172Z",
  "last_step": {
    "step": 2,
    "node_id": "suitcase",
    "choice_id": null,
    "timed_out": true
  }
}
```

Тайм-аут применил эффекты и переход из `timeout` узла `suitcase`: лояльность 65 → 60, безопасность 80 → 60, переход в `trip`. Таймер следующего узла (если он есть) стартует с момента этого ответа.

## 5. Восстановление после перезагрузки

Игрок ушёл со страницы на шаге с таймером и вернулся через 21 секунду. `GET` сам применяет истёкший тайм-аут (ровно один раз, под блокировкой строки) и возвращает актуальный шаг:

```http
GET /attempts/f9057066-9d29-4a88-ba61-3307d6bd2f58
```

Ответ `200`:

```json
{
  "attempt_id": "f9057066-9d29-4a88-ba61-3307d6bd2f58",
  "scenario_id": "5e5e6827-68bd-4b3e-ac1a-d23f14d7ac91",
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
    "ending_summary": null
  },
  "node_shown_at": "2026-09-25T15:53:56.448548Z",
  "deadline": null,
  "server_time": "2026-09-25T15:53:56.448548Z",
  "last_step": {
    "step": 2,
    "node_id": "suitcase",
    "choice_id": null,
    "timed_out": true
  }
}
```

Если дедлайн ещё не наступил, `GET` ничего не меняет и возвращает текущий узел с тем же `deadline`.

## 6. Результат

Доступен после финала. В этой попытке после тайм-аута игрок выбрал `call_colleague`, `check`, `tactful`, `escort` (каждый запрос — с `expected_step` из предыдущего ответа), и последний выбор привёл в финал:

```http
POST /attempts/ad243948-f9ab-4e14-94a0-8e0f1b9e7b4e/choice
Content-Type: application/json

{
  "choice_id": "escort",
  "expected_step": 5
}
```

Ответ `200`:

```json
{
  "attempt_id": "ad243948-f9ab-4e14-94a0-8e0f1b9e7b4e",
  "scenario_id": "5e5e6827-68bd-4b3e-ac1a-d23f14d7ac91",
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
    "ending_summary": "Спокойное разрешение: вы проверили факты, обеспечили безопасность прохода и сохранили уважение обоих пассажиров."
  },
  "node_shown_at": "2026-09-25T15:53:35.405056Z",
  "deadline": null,
  "server_time": "2026-09-25T15:53:35.405056Z",
  "last_step": {
    "step": 6,
    "node_id": "resolution",
    "choice_id": "escort",
    "timed_out": false
  }
}
```

```http
GET /attempts/ad243948-f9ab-4e14-94a0-8e0f1b9e7b4e/result
```

Ответ `200`:

```json
{
  "attempt_id": "ad243948-f9ab-4e14-94a0-8e0f1b9e7b4e",
  "scenario_id": "5e5e6827-68bd-4b3e-ac1a-d23f14d7ac91",
  "scenario_title": "Место у окна",
  "scenario_version": 1,
  "status": "finished",
  "started_at": "2026-09-25T15:53:15.022209Z",
  "finished_at": "2026-09-25T15:53:35.405056Z",
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
      "lesson": "Лучший первый шаг — подойти, представиться и спокойно выслушать обе стороны: так вы получаете факты и снижаете напряжение, никого заранее не обвиняя."
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
      "lesson": "Свободный проход — требование безопасности: по нему ходят пассажиры и персонал, через него проходит эвакуация. Сначала устраните угрозу, спор о месте подождёт."
    },
    {
      "step": 3,
      "node_id": "trip",
      "situation": "Пассажирка споткнулась о чемодан, чай разлился по полу. Она не пострадала, но испугана, а в проходе скользко.",
      "choice_id": "call_colleague",
      "choice_text": "Позвать коллегу на уборку, а самому заняться пассажиркой и чемоданом",
      "timed_out": false,
      "loyalty_delta": 5,
      "safety_delta": 10,
      "loyalty_after": 65,
      "safety_after": 70,
      "explanation": "Разделить работу с коллегой — правильно: опасность устранена быстрее. Просьба о помощи не штрафуется.",
      "lesson": "После инцидента: убедитесь, что никто не пострадал, устраните опасность и не стесняйтесь позвать коллегу — это не штрафуется."
    },
    {
      "step": 4,
      "node_id": "tickets",
      "situation": "Мужчина настаивает: «У меня билет на 7А, я никуда не пойду». Девушка протягивает свой билет — тоже на место 7А. Соседи наблюдают.",
      "choice_id": "check",
      "choice_text": "Попросить оба билета и сверить все реквизиты",
      "timed_out": false,
      "loyalty_delta": 5,
      "safety_delta": 5,
      "loyalty_after": 70,
      "safety_after": 75,
      "explanation": "Проверка документов — основа решения: без неё любое действие — догадка. Обе стороны видят, что вы разбираетесь по существу.",
      "lesson": "Спор о месте решается проверкой билетов. Обещания и пересадки без проверки лишь переносят конфликт."
    },
    {
      "step": 5,
      "node_id": "wagon_error",
      "situation": "Вы сверяете билеты: у девушки — вагон 5, место 7А; у мужчины — вагон 6, место 7А. Мужчина перепутал вагон: места одинаковые, номер вагона он не заметил.",
      "choice_id": "tactful",
      "choice_text": "Вполголоса объяснить мужчине ошибку и предложить проводить его в вагон 6",
      "timed_out": false,
      "loyalty_delta": 10,
      "safety_delta": 0,
      "loyalty_after": 80,
      "safety_after": 75,
      "explanation": "Тактичное объяснение позволяет пассажиру сохранить лицо — он охотно исправляет ошибку.",
      "lesson": "Ошибку пассажира лучше объяснять тактично и без свидетелей: человек сохраняет лицо и охотнее идёт навстречу."
    },
    {
      "step": 6,
      "node_id": "resolution",
      "situation": "Мужчина понимает, что ошибся вагоном, и собирается переходить в вагон 6. Как он отреагирует, зависит от того, как с ним обращались до этого.",
      "choice_id": "escort",
      "choice_text": "Помочь собрать вещи и лично проводить мужчину в вагон 6",
      "timed_out": false,
      "loyalty_delta": 5,
      "safety_delta": 0,
      "loyalty_after": 85,
      "safety_after": 75,
      "explanation": "Личное сопровождение показывает заботу даже о пассажире, который ошибся.",
      "lesson": "Итог складывается из всей цепочки: тон общения, безопасность прохода и выполненные обещания. Для спокойного финала нужны лояльность и безопасность не ниже 70 и отсутствие резкости, игнорирования и пустых обещаний."
    }
  ]
}
```

- `loyalty_delta` / `safety_delta` — **фактическое** изменение после ограничения шкал диапазоном 0–100 (эффект +20 при значении 95 даст +5).
- `explanation` — почему решение так повлияло на шкалы; `lesson` — как было правильно поступить в этой ситуации.
- `ending.outcome` — машинный код финала: `calm_resolution`, `resolved_with_dissatisfaction`, `escalated_to_senior`.

До финала результат недоступен:

```http
GET /attempts/f9057066-9d29-4a88-ba61-3307d6bd2f58/result
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

## 7. Служебные эндпойнты

- `POST /employees` `{"full_name": "...", "depot": "...", "brigade": "..."}` → 201 (демо-данные синтетические, реальные ПДН не использовать).
- `GET /employees` — список.
- `POST /scenarios` `{"title": "...", "description": "...", "graph": {...}}` → 201 или 422 `invalid_scenario`, формат графа — [scenario-format.md](scenario-format.md).
- `GET /health` → `{"status": "ok"}`.
