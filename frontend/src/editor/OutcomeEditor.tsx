import { ConditionBuilder } from "./ConditionBuilder";
import type { Json, Obj } from "./graphOps";

export const COMPETENCIES = [
  { id: "communication", title: "Коммуникация" },
  { id: "safety", title: "Безопасность" },
  { id: "first_aid", title: "Первая помощь" },
  { id: "stress_resistance", title: "Стрессоустойчивость" },
];

type Props = {
  outcome: Obj;
  nodeIds: string[];
  flags: string[];
  onChange: (next: Obj) => void;
};

function withKey(obj: Obj, key: string, value: Json | undefined): Obj {
  const next = { ...obj };
  if (value === undefined || (typeof value === "object" && value !== null && !Array.isArray(value) && Object.keys(value).length === 0)) {
    delete next[key];
  } else {
    next[key] = value;
  }
  return next;
}

function NumberMap({
  label,
  entries,
  value,
  min,
  max,
  onChange,
}: {
  label: string;
  entries: { id: string; title: string }[];
  value: Obj;
  min: number;
  max: number;
  onChange: (next: Obj) => void;
}) {
  return (
    <fieldset className="mini-fieldset">
      <legend>{label}</legend>
      <div className="number-grid">
        {entries.map((e) => (
          <label key={e.id} className="small">
            {e.title}
            <input
              type="number"
              min={min}
              max={max}
              value={typeof value[e.id] === "number" ? (value[e.id] as number) : ""}
              placeholder="0"
              onChange={(ev) => {
                const next = { ...value };
                if (ev.target.value === "") delete next[e.id];
                else next[e.id] = Number(ev.target.value);
                onChange(next);
              }}
            />
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function OutcomeEditor({ outcome, nodeIds, flags, onChange }: Props) {
  const effects = (outcome.effects as Obj) ?? {};
  const setFlags = (outcome.set_flags as Obj) ?? {};
  const assessment = (outcome.assessment as Obj) ?? {};
  const transitions = (outcome.transitions as Obj[] | undefined) ?? null;

  return (
    <div className="outcome">
      <NumberMap
        label="Эффекты на шкалы"
        entries={[
          { id: "loyalty", title: "Лояльность" },
          { id: "safety", title: "Безопасность" },
        ]}
        value={effects}
        min={-100}
        max={100}
        onChange={(next) => onChange(withKey(outcome, "effects", next))}
      />
      <NumberMap
        label="Оценка компетенций (0–10)"
        entries={COMPETENCIES}
        value={assessment}
        min={0}
        max={10}
        onChange={(next) => onChange(withKey(outcome, "assessment", next))}
      />

      <fieldset className="mini-fieldset">
        <legend>Установить флаги</legend>
        {flags.length === 0 && <p className="muted small">Флаги объявляются в настройках сценария.</p>}
        <div className="flag-grid">
          {flags.map((flag) => (
            <label key={flag} className="small inline">
              {flag}
              <select
                value={flag in setFlags ? String(setFlags[flag]) : ""}
                onChange={(e) => {
                  const next = { ...setFlags };
                  if (e.target.value === "") delete next[flag];
                  else next[flag] = e.target.value === "true";
                  onChange(withKey(outcome, "set_flags", next));
                }}
              >
                <option value="">не менять</option>
                <option value="true">включить</option>
                <option value="false">выключить</option>
              </select>
            </label>
          ))}
        </div>
      </fieldset>

      <label className="small block">
        Объяснение для разбора
        <textarea
          rows={2}
          value={(outcome.explanation as string) ?? ""}
          onChange={(e) => onChange(withKey(outcome, "explanation", e.target.value || undefined))}
        />
      </label>

      <fieldset className="mini-fieldset">
        <legend>Куда ведёт</legend>
        <label className="small inline">
          <input
            type="radio"
            checked={transitions === null}
            onChange={() => {
              const { transitions: _t, ...rest } = outcome;
              onChange({ ...rest, next_node: nodeIds[0] ?? "" });
            }}
          />
          Один переход
        </label>
        <label className="small inline">
          <input
            type="radio"
            checked={transitions !== null}
            onChange={() => {
              const { next_node, ...rest } = outcome;
              onChange({ ...rest, transitions: [{ next_node: (next_node as string) ?? nodeIds[0] ?? "" }] });
            }}
          />
          Условные переходы
        </label>
        {transitions === null ? (
          <select
            aria-label="Следующий узел"
            value={(outcome.next_node as string) ?? ""}
            onChange={(e) => onChange({ ...outcome, next_node: e.target.value })}
          >
            {!nodeIds.includes(outcome.next_node as string) && <option value={(outcome.next_node as string) ?? ""}>— выберите —</option>}
            {nodeIds.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        ) : (
          <ol className="transitions">
            {transitions.map((t, i) => {
              const last = i === transitions.length - 1;
              const replace = (nt: Obj) => onChange({ ...outcome, transitions: transitions.map((x, j) => (j === i ? nt : x)) });
              return (
                <li key={i}>
                  {last ? (
                    <span className="small muted">Иначе (по умолчанию)</span>
                  ) : (
                    <ConditionBuilder
                      value={t.condition}
                      flags={flags}
                      emptyLabel="Добавьте условие"
                      onChange={(c) => replace(withKey(t, "condition", c))}
                    />
                  )}
                  <label className="small inline">
                    → узел
                    <select value={(t.next_node as string) ?? ""} onChange={(e) => replace({ ...t, next_node: e.target.value })}>
                      {!nodeIds.includes(t.next_node as string) && <option value="">— выберите —</option>}
                      {nodeIds.map((id) => (
                        <option key={id} value={id}>
                          {id}
                        </option>
                      ))}
                    </select>
                  </label>
                  {!last && (
                    <button
                      type="button"
                      className="btn btn-ghost small"
                      onClick={() => onChange({ ...outcome, transitions: transitions.filter((_, j) => j !== i) })}
                    >
                      Удалить
                    </button>
                  )}
                </li>
              );
            })}
          </ol>
        )}
        {transitions !== null && (
          <button
            type="button"
            className="btn btn-ghost small"
            onClick={() =>
              onChange({
                ...outcome,
                transitions: [
                  ...transitions.slice(0, -1),
                  { condition: { scale: "loyalty", op: ">=", value: 70 }, next_node: nodeIds[0] ?? "" },
                  transitions[transitions.length - 1],
                ],
              })
            }
          >
            + условный переход
          </button>
        )}
      </fieldset>
    </div>
  );
}
