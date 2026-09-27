import { useState } from "react";
import { ConditionBuilder } from "./ConditionBuilder";
import { AutoTextarea } from "../components/AutoTextarea";
import { ACHIEVEMENT_ICONS } from "../utils/achievements";
import { freeId, ID_PATTERN, type Obj } from "./graphOps";
import { BACKGROUNDS, COLORS, FIGURES, GENDERS, POSES, POSITIONS, type Option } from "./sceneOptions";

type Patch = { [key: string]: Obj[string] | undefined };

function Select({ label, value, options, onChange, empty }: { label: string; value: string; options: Option[]; onChange: (v: string) => void; empty?: string }) {
  return (
    <select aria-label={label} title={label} value={value} onChange={(e) => onChange(e.target.value)}>
      {empty !== undefined && <option value="">{empty}</option>}
      {options.map((o) => (
        <option key={o.id} value={o.id}>
          {o.title}
        </option>
      ))}
    </select>
  );
}

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
  const custom = (graph.achievements as Obj[] | undefined) ?? [];
  const graphVisual = (graph.visual as Obj | undefined) ?? {};
  const characters = (graphVisual.characters as Obj | undefined) ?? {};
  const nodeIds = Object.keys((graph.nodes as Obj) ?? {});
  const flagNames = Object.keys(flags);

  const set = (key: string, value: Obj[string] | undefined) => {
    const next = { ...graph };
    if (value === undefined) delete next[key];
    else next[key] = value;
    onChange(next);
  };
  const setVisual = (patch: Patch) => {
    const next = Object.fromEntries(
      Object.entries({ ...graphVisual, ...patch }).filter(([, v]) => v !== undefined && v !== "" && !(typeof v === "object" && v !== null && Object.keys(v).length === 0)),
    ) as Obj;
    set("visual", Object.keys(next).length ? next : undefined);
  };
  const setCharacters = (next: Obj) => setVisual({ characters: next });
  const setCustom = (next: Obj[]) => set("achievements", next.length ? next : undefined);

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
        <legend>Свои достижения</legend>
        <p className="muted small">Придумайте достижение для этого сценария: название, описание, значок и условие на итоговое состояние.</p>
        {custom.map((a, i) => {
          const replace = (patch: Obj) => setCustom(custom.map((x, j) => (j === i ? { ...x, ...patch } : x)));
          return (
            <div key={i} className="clause-block custom-achievement">
              <div className="inline wrap">
                <select aria-label="Значок" value={(a.icon as string) ?? "medal"} onChange={(e) => replace({ icon: e.target.value })}>
                  {ACHIEVEMENT_ICONS.map((icon) => (
                    <option key={icon.id} value={icon.id}>
                      {icon.glyph} {icon.title}
                    </option>
                  ))}
                </select>
                <input aria-label="Название достижения" placeholder="Название" value={(a.title as string) ?? ""} onChange={(e) => replace({ title: e.target.value })} />
                <code className="small">{a.id as string}</code>
              </div>
              <AutoTextarea
                aria-label="Описание достижения"
                placeholder="За что выдаётся"
                minRows={1}
                value={(a.description as string) ?? ""}
                onChange={(e) => replace({ description: e.target.value })}
              />
              <ConditionBuilder
                value={a.when}
                flags={flagNames}
                emptyLabel="Добавьте условие"
                onChange={(when) => replace({ when: when ?? {} })}
              />
              <button type="button" className="btn btn-ghost small" onClick={() => setCustom(custom.filter((_, j) => j !== i))}>
                Удалить
              </button>
            </div>
          );
        })}
        <button
          type="button"
          className="btn btn-ghost small"
          onClick={() =>
            setCustom([
              ...custom,
              {
                id: freeId(custom.map((a) => a.id as string), "achievement"),
                title: "Новое достижение",
                description: "",
                icon: "star",
                when: { scale: "loyalty", op: ">=", value: 70 },
              },
            ])
          }
        >
          + своё достижение
        </button>
      </fieldset>

      <fieldset className="mini-fieldset">
        <legend>Сцена</legend>
        <label className="small inline">
          Фон по умолчанию
          <Select label="Фон" value={(graphVisual.background as string) ?? ""} options={BACKGROUNDS} empty="стандартный" onChange={(v) => setVisual({ background: v || undefined })} />
        </label>
      </fieldset>

      <fieldset className="mini-fieldset">
        <legend>Персонажи сцены</legend>
        {Object.entries(characters).map(([id, raw]) => {
          const c = raw as Obj;
          const replace = (patch: Patch) =>
            setCharacters({
              ...characters,
              [id]: Object.fromEntries(Object.entries({ ...c, ...patch }).filter(([, v]) => v !== undefined)) as Obj,
            });
          return (
            <div key={id} className="clause-block">
              <code>{id}</code>
              <input aria-label="Имя" value={(c.name as string) ?? ""} onChange={(e) => replace({ name: e.target.value })} />
              <Select label="Роль" value={(c.figure as string) ?? "passenger"} options={FIGURES} onChange={(v) => replace({ figure: v })} />
              <Select label="Род (для подписи настроения)" value={(c.gender as string) ?? ""} options={GENDERS} empty="по роли" onChange={(v) => replace({ gender: v || undefined })} />
              <Select label="Цвет одежды" value={(c.color as string) ?? ""} options={COLORS} empty="цвет роли" onChange={(v) => replace({ color: v || undefined })} />
              <Select label="Поза" value={(c.pose as string) ?? "standing"} options={POSES} onChange={(v) => replace({ pose: v })} />
              <Select label="Место" value={(c.position as string) ?? "center"} options={POSITIONS} onChange={(v) => replace({ position: v })} />
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
