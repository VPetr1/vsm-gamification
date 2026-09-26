import { useState } from "react";
import { ConditionBuilder } from "./ConditionBuilder";
import { freeId, ID_PATTERN, type Obj } from "./graphOps";
import { OutcomeEditor } from "./OutcomeEditor";
import { VisualEditor } from "./VisualEditor";

type Props = {
  nodeId: string;
  node: Obj;
  nodeIds: string[];
  flags: string[];
  characters: string[];
  errors: string[];
  onChange: (node: Obj) => void;
  onRename: (to: string) => string | null;
  onDelete: () => void;
};

const OUTCOMES = [
  { id: "calm_resolution", title: "Спокойное разрешение" },
  { id: "resolved_with_dissatisfaction", title: "Разрешено с недовольством" },
  { id: "escalated_to_senior", title: "Передано старшему" },
];

export function NodeEditor({ nodeId, node, nodeIds, flags, characters, errors, onChange, onRename, onDelete }: Props) {
  const [idDraft, setIdDraft] = useState(nodeId);
  const [idError, setIdError] = useState<string | null>(null);
  const isEnding = node.is_ending === true;
  const choices = (node.choices as Obj[] | undefined) ?? [];
  const hasTimer = typeof node.timer_seconds === "number";
  const set = (key: string, value: unknown) => {
    const next = { ...node } as Obj;
    if (value === undefined) delete next[key];
    else next[key] = value as Obj[string];
    onChange(next);
  };

  return (
    <section className="card node-editor" aria-labelledby="node-heading">
      <div className="node-editor-head">
        <h2 id="node-heading">Узел «{nodeId}»</h2>
        <button type="button" className="btn btn-ghost small danger" onClick={onDelete}>
          Удалить узел
        </button>
      </div>
      {errors.length > 0 && (
        <ul className="error-list" aria-label="Ошибки в узле">
          {errors.map((e) => (
            <li key={e}>{e}</li>
          ))}
        </ul>
      )}

      <div className="field-row">
        <label className="field">
          <span>Идентификатор</span>
          <input
            value={idDraft}
            onChange={(e) => {
              setIdDraft(e.target.value);
              setIdError(null);
            }}
            onBlur={() => {
              if (idDraft === nodeId) return;
              if (!ID_PATTERN.test(idDraft)) {
                setIdError("Латинские буквы, цифры и _, начиная с буквы.");
                return;
              }
              const problem = onRename(idDraft);
              if (problem) setIdError(problem);
            }}
            aria-invalid={idError ? true : undefined}
          />
          {idError && <span className="field-error small">{idError}</span>}
        </label>
        <label className="field inline-check">
          <input
            type="checkbox"
            checked={isEnding}
            onChange={(e) => {
              if (e.target.checked) {
                onChange({ text: node.text ?? "", is_ending: true, ending_summary: "", outcome: "calm_resolution" });
              } else {
                onChange({ text: node.text ?? "", choices: [{ id: "a", text: "Вариант", next_node: nodeIds[0] ?? nodeId }] });
              }
            }}
          />
          <span>Финал</span>
        </label>
      </div>

      <label className="field wide">
        <span>Текст ситуации</span>
        <textarea rows={3} value={(node.text as string) ?? ""} onChange={(e) => set("text", e.target.value)} />
      </label>

      {isEnding ? (
        <>
          <label className="field wide">
            <span>Итог для разбора</span>
            <textarea rows={2} value={(node.ending_summary as string) ?? ""} onChange={(e) => set("ending_summary", e.target.value)} />
          </label>
          <label className="field">
            <span>Тип финала</span>
            <select value={(node.outcome as string) ?? ""} onChange={(e) => set("outcome", e.target.value || undefined)}>
              <option value="">не указан</option>
              {OUTCOMES.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.title}
                </option>
              ))}
            </select>
          </label>
        </>
      ) : (
        <>
          <label className="field wide">
            <span>Как лучше поступить (урок для разбора)</span>
            <textarea rows={2} value={(node.debrief as string) ?? ""} onChange={(e) => set("debrief", e.target.value || undefined)} />
          </label>

          <fieldset className="mini-fieldset">
            <legend>Таймер</legend>
            <label className="small inline">
              <input
                type="checkbox"
                checked={hasTimer}
                onChange={(e) => {
                  const next = { ...node } as Obj;
                  if (e.target.checked) {
                    next.timer_seconds = 20;
                    next.timeout = { next_node: nodeIds.find((id) => id !== nodeId) ?? nodeId };
                  } else {
                    delete next.timer_seconds;
                    delete next.timeout;
                  }
                  onChange(next);
                }}
              />
              Критический шаг с таймером
            </label>
            {hasTimer && (
              <>
                <label className="small inline">
                  Секунд (5–600)
                  <input
                    type="number"
                    min={5}
                    max={600}
                    value={node.timer_seconds as number}
                    onChange={(e) => set("timer_seconds", Number(e.target.value))}
                  />
                </label>
                <p className="small muted">Что произойдёт, если время выйдет:</p>
                <OutcomeEditor
                  outcome={(node.timeout as Obj) ?? { next_node: "" }}
                  nodeIds={nodeIds}
                  flags={flags}
                  onChange={(timeout) => set("timeout", timeout)}
                />
              </>
            )}
          </fieldset>

          <h3>Варианты действий</h3>
          <ol className="choice-editors">
            {choices.map((choice, index) => {
              const replace = (next: Obj) => set("choices", choices.map((c, i) => (i === index ? next : c)));
              return (
                <li key={index} className="choice-editor">
                  <div className="field-row">
                    <label className="field">
                      <span>ID варианта</span>
                      <input value={(choice.id as string) ?? ""} onChange={(e) => replace({ ...choice, id: e.target.value })} />
                    </label>
                    <label className="field wide">
                      <span>Текст кнопки</span>
                      <input value={(choice.text as string) ?? ""} onChange={(e) => replace({ ...choice, text: e.target.value })} />
                    </label>
                  </div>
                  <div className="small">
                    <span className="muted">Показывать, только если:</span>
                    <ConditionBuilder
                      value={choice.condition}
                      flags={flags}
                      emptyLabel="Всегда доступен"
                      onChange={(condition) => {
                        const next = { ...choice };
                        if (condition === undefined) delete next.condition;
                        else next.condition = condition;
                        replace(next);
                      }}
                    />
                  </div>
                  <OutcomeEditor outcome={choice} nodeIds={nodeIds} flags={flags} onChange={replace} />
                  <button
                    type="button"
                    className="btn btn-ghost small danger"
                    onClick={() => set("choices", choices.filter((_, i) => i !== index))}
                  >
                    Удалить вариант
                  </button>
                </li>
              );
            })}
          </ol>
          <button
            type="button"
            className="btn btn-secondary"
            onClick={() =>
              set("choices", [
                ...choices,
                {
                  id: freeId(choices.map((c) => c.id as string), "choice"),
                  text: "Новый вариант",
                  next_node: nodeIds.find((id) => id !== nodeId) ?? nodeId,
                },
              ])
            }
          >
            + вариант (развилка)
          </button>
        </>
      )}

      <VisualEditor node={node} characters={characters} flags={flags} onChange={onChange} />
    </section>
  );
}
