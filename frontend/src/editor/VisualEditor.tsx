import { ConditionBuilder } from "./ConditionBuilder";
import type { Obj } from "./graphOps";
import { BACKGROUNDS, MOODS, POSES, POSITIONS, PROPS } from "./sceneOptions";

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
  const cast = visual.cast as Obj[] | undefined;

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

      <label className="small inline">
        Фон
        <select value={(visual.background as string) ?? ""} onChange={(e) => setVisual({ ...visual, background: e.target.value || undefined } as Obj)}>
          <option value="">как в сценарии</option>
          {BACKGROUNDS.map((b) => (
            <option key={b.id} value={b.id}>
              {b.title}
            </option>
          ))}
        </select>
      </label>

      <fieldset className="mini-fieldset">
        <legend>Кто в кадре</legend>
        <label className="small inline">
          <input
            type="checkbox"
            checked={cast !== undefined}
            onChange={(e) => {
              const next = { ...visual };
              if (e.target.checked) next.cast = characters.map((c) => ({ character: c }));
              else delete next.cast;
              setVisual(next);
            }}
          />
          Выбрать персонажей для этого узла (иначе в кадре все)
        </label>
        {cast?.map((rule, i) => {
          const replace = (patch: Obj) => {
            const next = { ...rule, ...patch };
            for (const key of Object.keys(patch)) if (patch[key] === "") delete next[key];
            setVisual({ ...visual, cast: cast.map((x, j) => (j === i ? next : x)) });
          };
          return (
            <div key={i} className="clause-block">
              <select aria-label="Персонаж в кадре" value={(rule.character as string) ?? ""} onChange={(e) => replace({ character: e.target.value })}>
                {characters.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
              <select aria-label="Поза в узле" value={(rule.pose as string) ?? ""} onChange={(e) => replace({ pose: e.target.value })}>
                <option value="">поза по умолчанию</option>
                {POSES.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.title}
                  </option>
                ))}
              </select>
              <select aria-label="Место в узле" value={(rule.position as string) ?? ""} onChange={(e) => replace({ position: e.target.value })}>
                <option value="">место по умолчанию</option>
                {POSITIONS.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.title}
                  </option>
                ))}
              </select>
              <ConditionBuilder
                value={rule.when}
                flags={flags}
                emptyLabel="всегда"
                onChange={(when) => {
                  const next = { ...rule };
                  if (when === undefined) delete next.when;
                  else next.when = when;
                  setVisual({ ...visual, cast: cast.map((x, j) => (j === i ? next : x)) });
                }}
              />
              <button type="button" className="btn btn-ghost small" onClick={() => setVisual({ ...visual, cast: cast.filter((_, j) => j !== i) })}>
                Убрать
              </button>
            </div>
          );
        })}
        {cast !== undefined && characters.length > 0 && (
          <button type="button" className="btn btn-ghost small" onClick={() => setVisual({ ...visual, cast: [...cast, { character: characters[0] }] })}>
            + персонаж в кадр
          </button>
        )}
      </fieldset>

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
