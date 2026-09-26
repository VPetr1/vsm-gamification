import { useId, useState } from "react";
import { conditionToForm, formToCondition, SCALE_OPS, type Clause, type ConditionForm, type Json, type Obj } from "./graphOps";

type Props = {
  value: Json | undefined;
  flags: string[];
  onChange: (value: Obj | undefined) => void;
  emptyLabel?: string;
};

const SCALE_LABEL = { loyalty: "лояльность", safety: "безопасность" } as const;

/** Field / operator / value rows joined by "all" or "any"; anything more complex is edited as JSON. */
export function ConditionBuilder({ value, flags, onChange, emptyLabel = "Без условия" }: Props) {
  const form = conditionToForm(value);
  const [raw, setRaw] = useState(() => JSON.stringify(value ?? null, null, 2));
  const [rawError, setRawError] = useState<string | null>(null);
  const id = useId();

  if (!form) {
    return (
      <div className="condition condition-raw">
        <label htmlFor={`${id}-raw`} className="small">
          Сложное условие (JSON)
        </label>
        <textarea
          id={`${id}-raw`}
          rows={4}
          value={raw}
          onChange={(e) => {
            setRaw(e.target.value);
            try {
              const parsed = JSON.parse(e.target.value) as Json;
              setRawError(null);
              onChange(parsed === null ? undefined : (parsed as Obj));
            } catch {
              setRawError("Некорректный JSON");
            }
          }}
        />
        {rawError && <p className="field-error small">{rawError}</p>}
      </div>
    );
  }

  const update = (next: ConditionForm) => onChange(formToCondition(next));
  const setClause = (index: number, clause: Clause) =>
    update({ ...form, clauses: form.clauses.map((c, i) => (i === index ? clause : c)) });

  return (
    <div className="condition">
      {form.clauses.length === 0 && <span className="muted small">{emptyLabel}</span>}
      {form.clauses.length > 1 && (
        <label className="inline small">
          Выполняется, если
          <select value={form.mode} onChange={(e) => update({ ...form, mode: e.target.value as "all" | "any" })}>
            <option value="all">все условия (И)</option>
            <option value="any">любое условие (ИЛИ)</option>
          </select>
        </label>
      )}
      {form.clauses.map((clause, index) => (
        <div className="clause" key={index}>
          <select
            aria-label="Поле"
            value={clause.kind === "flag" ? `flag:${clause.flag}` : `scale:${clause.scale}`}
            onChange={(e) => {
              const [kind, name] = e.target.value.split(":");
              setClause(
                index,
                kind === "flag"
                  ? { kind: "flag", flag: name, negate: false }
                  : { kind: "scale", scale: name as "loyalty" | "safety", op: ">=", value: 50 },
              );
            }}
          >
            <optgroup label="Шкалы">
              <option value="scale:loyalty">лояльность</option>
              <option value="scale:safety">безопасность</option>
            </optgroup>
            <optgroup label="Флаги">
              {[...new Set([...flags, ...(clause.kind === "flag" ? [clause.flag] : [])])].map((f) => (
                <option key={f} value={`flag:${f}`}>
                  флаг {f}
                </option>
              ))}
            </optgroup>
          </select>
          {clause.kind === "flag" ? (
            <select
              aria-label="Оператор"
              value={clause.negate ? "unset" : "set"}
              onChange={(e) => setClause(index, { ...clause, negate: e.target.value === "unset" })}
            >
              <option value="set">установлен</option>
              <option value="unset">не установлен</option>
            </select>
          ) : (
            <>
              <select aria-label="Оператор" value={clause.op} onChange={(e) => setClause(index, { ...clause, op: e.target.value })}>
                {SCALE_OPS.map((op) => (
                  <option key={op} value={op}>
                    {op}
                  </option>
                ))}
              </select>
              <input
                aria-label={`Значение: ${SCALE_LABEL[clause.scale]}`}
                type="number"
                min={0}
                max={100}
                value={clause.value}
                onChange={(e) => setClause(index, { ...clause, value: Number(e.target.value) })}
              />
            </>
          )}
          <button
            type="button"
            className="btn btn-ghost small"
            aria-label="Удалить условие"
            onClick={() => update({ ...form, clauses: form.clauses.filter((_, i) => i !== index) })}
          >
            ✕
          </button>
        </div>
      ))}
      <button
        type="button"
        className="btn btn-ghost small"
        onClick={() =>
          update({
            ...form,
            clauses: [
              ...form.clauses,
              flags.length ? { kind: "flag", flag: flags[0], negate: false } : { kind: "scale", scale: "loyalty", op: ">=", value: 50 },
            ],
          })
        }
      >
        + условие
      </button>
    </div>
  );
}
