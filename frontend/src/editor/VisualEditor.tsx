import { ConditionBuilder } from "./ConditionBuilder";
import type { Obj } from "./graphOps";

export const MOODS = [
  { id: "happy", title: "доволен" },
  { id: "calm", title: "спокоен" },
  { id: "worried", title: "встревожен" },
  { id: "scared", title: "напуган" },
  { id: "upset", title: "расстроен" },
  { id: "angry", title: "раздражён" },
];

export const PROPS = [
  { id: "suitcase", title: "чемодан в проходе" },
  { id: "spill", title: "пролитый напиток" },
];

type Props = {
  node: Obj;
  characters: string[];
  flags: string[];
  onChange: (node: Obj) => void;
};

/** Optional scene metadata of a node; the play screen works without it. */
export function VisualEditor({ node, characters, flags, onChange }: Props) {
  const visual = (node.visual as Obj | undefined) ?? {};
  const moods = (visual.moods as Obj[] | undefined) ?? [];
  const props = (visual.props as Obj[] | undefined) ?? [];

  const setVisual = (next: Obj) => {
    const cleaned = Object.fromEntries(
      Object.entries(next).filter(([, v]) => v !== undefined && v !== "" && !(Array.isArray(v) && v.length === 0)),
    ) as Obj;
    const nextNode = { ...node };
    if (Object.keys(cleaned).length === 0) delete nextNode.visual;
    else nextNode.visual = cleaned;
    onChange(nextNode);
  };

  return (
    <details className="visual-editor">
      <summary>Визуальные метаданные (необязательно)</summary>
      {characters.length === 0 && <p className="muted small">Добавьте персонажей в настройках сценария.</p>}
      <label className="small inline">
        Говорит
        <select value={(visual.speaker as string) ?? ""} onChange={(e) => setVisual({ ...visual, speaker: e.target.value || undefined } as Obj)}>
          <option value="">никто / рассказчик</option>
          {characters.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>
      </label>

      <fieldset className="mini-fieldset">
        <legend>Настроение персонажей</legend>
        <p className="muted small">Без указания настроение считается по шкале лояльности. Первое подходящее правило побеждает.</p>
        {moods.map((m, i) => {
          const replace = (next: Obj) => setVisual({ ...visual, moods: moods.map((x, j) => (j === i ? next : x)) });
          return (
            <div key={i} className="clause-block">
              <select aria-label="Персонаж" value={(m.character as string) ?? ""} onChange={(e) => replace({ ...m, character: e.target.value })}>
                {characters.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <select aria-label="Настроение" value={(m.mood as string) ?? "calm"} onChange={(e) => replace({ ...m, mood: e.target.value })}>
                {MOODS.map((mood) => (
                  <option key={mood.id} value={mood.id}>
                    {mood.title}
                  </option>
                ))}
              </select>
              <ConditionBuilder
                value={m.when}
                flags={flags}
                emptyLabel="всегда"
                onChange={(when) => {
                  const next = { ...m };
                  if (when === undefined) delete next.when;
                  else next.when = when;
                  replace(next);
                }}
              />
              <button type="button" className="btn btn-ghost small" onClick={() => setVisual({ ...visual, moods: moods.filter((_, j) => j !== i) })}>
                Удалить
              </button>
            </div>
          );
        })}
        {characters.length > 0 && (
          <button
            type="button"
            className="btn btn-ghost small"
            onClick={() => setVisual({ ...visual, moods: [...moods, { character: characters[0], mood: "calm" }] })}
          >
            + настроение
          </button>
        )}
      </fieldset>

      <fieldset className="mini-fieldset">
        <legend>Предметы в сцене</legend>
        {props.map((p, i) => {
          const replace = (next: Obj) => setVisual({ ...visual, props: props.map((x, j) => (j === i ? next : x)) });
          return (
            <div key={i} className="clause-block">
              <select aria-label="Предмет" value={(p.id as string) ?? "suitcase"} onChange={(e) => replace({ ...p, id: e.target.value })}>
                {PROPS.map((prop) => (
                  <option key={prop.id} value={prop.id}>
                    {prop.title}
                  </option>
                ))}
              </select>
              <ConditionBuilder
                value={p.when}
                flags={flags}
                emptyLabel="всегда"
                onChange={(when) => {
                  const next = { ...p };
                  if (when === undefined) delete next.when;
                  else next.when = when;
                  replace(next);
                }}
              />
              <button type="button" className="btn btn-ghost small" onClick={() => setVisual({ ...visual, props: props.filter((_, j) => j !== i) })}>
                Удалить
              </button>
            </div>
          );
        })}
        <button type="button" className="btn btn-ghost small" onClick={() => setVisual({ ...visual, props: [...props, { id: "suitcase" }] })}>
          + предмет
        </button>
      </fieldset>
    </details>
  );
}
