import { useState } from "react";
import { ConditionBuilder } from "./ConditionBuilder";
import { ID_PATTERN, type Obj } from "./graphOps";

const ACHIEVEMENTS = [
  { id: "diplomat", title: "Дипломат" },
  { id: "safe_passage", title: "Безопасный проход" },
];

type Props = { graph: Obj; onChange: (graph: Obj) => void };

export function GraphSettings({ graph, onChange }: Props) {
  const [newFlag, setNewFlag] = useState("");
  const [flagError, setFlagError] = useState<string | null>(null);
  const initial = (graph.initial as Obj) ?? {};
  const flags = (graph.flags as Obj) ?? {};
  const awards = (graph.awards as Obj[] | undefined) ?? [];
  const characters = ((graph.visual as Obj | undefined)?.characters as Obj | undefined) ?? {};
  const nodeIds = Object.keys((graph.nodes as Obj) ?? {});
  const flagNames = Object.keys(flags);

  const set = (key: string, value: Obj[string] | undefined) => {
    const next = { ...graph };
    if (value === undefined) delete next[key];
    else next[key] = value;
    onChange(next);
  };
  const setCharacters = (next: Obj) => set("visual", Object.keys(next).length ? { ...((graph.visual as Obj) ?? {}), characters: next } : undefined);

  return (
    <details className="card graph-settings" open>
      <summary>
        <strong>Настройки сценария</strong>
      </summary>
      <div className="field-row">
        <label className="field">
          <span>Стартовый узел</span>
          <select value={(graph.start_node as string) ?? ""} onChange={(e) => set("start_node", e.target.value)}>
            {nodeIds.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
        </label>
        {(["loyalty", "safety"] as const).map((scale) => (
          <label className="field" key={scale}>
            <span>Начальная {scale === "loyalty" ? "лояльность" : "безопасность"}</span>
            <input
              type="number"
              min={0}
              max={100}
              value={typeof initial[scale] === "number" ? (initial[scale] as number) : 50}
              onChange={(e) => set("initial", { ...initial, [scale]: Number(e.target.value) })}
            />
          </label>
        ))}
      </div>

      <fieldset className="mini-fieldset">
        <legend>Флаги попытки</legend>
        <ul className="flag-list">
          {flagNames.map((f) => (
            <li key={f}>
              <code>{f}</code>
              <button
                type="button"
                className="btn btn-ghost small"
                onClick={() => {
                  const next = { ...flags };
                  delete next[f];
                  set("flags", next);
                }}
              >
                Удалить
              </button>
            </li>
          ))}
        </ul>
        <div className="inline">
          <input
            aria-label="Новый флаг"
            placeholder="например, was_rude"
            value={newFlag}
            onChange={(e) => {
              setNewFlag(e.target.value);
              setFlagError(null);
            }}
          />
          <button
            type="button"
            className="btn btn-secondary small"
            onClick={() => {
              if (!ID_PATTERN.test(newFlag)) return setFlagError("Латинские буквы, цифры и _.");
              if (newFlag in flags) return setFlagError("Такой флаг уже есть.");
              set("flags", { ...flags, [newFlag]: false });
              setNewFlag("");
            }}
          >
            Добавить флаг
          </button>
        </div>
        {flagError && <p className="field-error small">{flagError}</p>}
      </fieldset>

      <fieldset className="mini-fieldset">
        <legend>Достижения за сценарий</legend>
        <p className="muted small">Выдаются на финале, если условие верно для итогового состояния.</p>
        {awards.map((a, i) => (
          <div key={i} className="clause-block">
            <select
              aria-label="Достижение"
              value={(a.achievement as string) ?? ""}
              onChange={(e) => set("awards", awards.map((x, j) => (j === i ? { ...x, achievement: e.target.value } : x)))}
            >
              {ACHIEVEMENTS.map((ach) => (
                <option key={ach.id} value={ach.id}>
                  {ach.title}
                </option>
              ))}
            </select>
            <ConditionBuilder
              value={a.when}
              flags={flagNames}
              emptyLabel="Добавьте условие"
              onChange={(when) => set("awards", awards.map((x, j) => (j === i ? { ...x, when: when ?? {} } : x)))}
            />
            <button type="button" className="btn btn-ghost small" onClick={() => set("awards", awards.filter((_, j) => j !== i))}>
              Удалить
            </button>
          </div>
        ))}
        <button
          type="button"
          className="btn btn-ghost small"
          onClick={() => set("awards", [...awards, { achievement: "diplomat", when: { scale: "loyalty", op: ">=", value: 70 } }])}
        >
          + достижение
        </button>
      </fieldset>

      <fieldset className="mini-fieldset">
        <legend>Персонажи сцены</legend>
        {Object.entries(characters).map(([id, raw]) => {
          const c = raw as Obj;
          const replace = (patch: Obj) => setCharacters({ ...characters, [id]: { ...c, ...patch } });
          return (
            <div key={id} className="clause-block">
              <code>{id}</code>
              <input aria-label="Имя" value={(c.name as string) ?? ""} onChange={(e) => replace({ name: e.target.value })} />
              <select aria-label="Фигура" value={(c.figure as string) ?? "passenger"} onChange={(e) => replace({ figure: e.target.value })}>
                <option value="man">мужчина</option>
                <option value="woman">женщина</option>
                <option value="passenger">пассажир</option>
              </select>
              <select aria-label="Поза" value={(c.pose as string) ?? "standing"} onChange={(e) => replace({ pose: e.target.value })}>
                <option value="standing">стоит</option>
                <option value="sitting">сидит</option>
              </select>
              <select aria-label="Место" value={(c.position as string) ?? "center"} onChange={(e) => replace({ position: e.target.value })}>
                <option value="left">слева</option>
                <option value="center">в центре</option>
                <option value="right">справа</option>
              </select>
              <button
                type="button"
                className="btn btn-ghost small"
                onClick={() => {
                  const next = { ...characters };
                  delete next[id];
                  setCharacters(next);
                }}
              >
                Удалить
              </button>
            </div>
          );
        })}
        <button
          type="button"
          className="btn btn-ghost small"
          onClick={() => {
            let i = Object.keys(characters).length + 1;
            while (`person${i}` in characters) i += 1;
            setCharacters({ ...characters, [`person${i}`]: { name: "Пассажир", figure: "passenger", pose: "standing", position: "center" } });
          }}
        >
          + персонаж
        </button>
      </fieldset>
    </details>
  );
}
