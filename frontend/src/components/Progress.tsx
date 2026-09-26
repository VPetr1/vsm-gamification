import type { AchievementState, CompetencyScore, Level, Recommendation } from "../api/types";
import { formatDateTime } from "../utils/time";

export function LevelBar({ xp, level }: { xp: number; level: Level }) {
  const span = level.next_min_xp === null ? 1 : level.next_min_xp - level.min_xp;
  const progress = level.next_min_xp === null ? 100 : Math.round(((xp - level.min_xp) / span) * 100);
  return (
    <div className="level">
      <div className="level-head">
        <span className="level-badge">Уровень {level.number}</span>
        <strong>{level.title}</strong>
        <span className="muted">{xp} опыта</span>
      </div>
      <div
        className="level-track"
        role="progressbar"
        aria-label="Прогресс до следующего уровня"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={progress}
      >
        <div className="level-fill" style={{ width: `${progress}%` }} />
      </div>
      <p className="muted small">
        {level.next_min_xp === null
          ? "Максимальный уровень."
          : `До следующего уровня: ${level.next_min_xp - xp} опыта. Опыт — сумма лучших результатов по сценариям.`}
      </p>
    </div>
  );
}

export function CompetencyList({ items, weakestId }: { items: CompetencyScore[]; weakestId?: string | null }) {
  return (
    <ul className="competencies">
      {items.map((c) => (
        <li key={c.id} className={c.id === weakestId ? "is-weakest" : undefined}>
          <div className="competency-head">
            <span className="competency-title">
              {c.title}
              {c.id === weakestId && <span className="chip chip-warn">слабая</span>}
            </span>
            <span className="competency-value">
              {c.percent === null ? (
                <span className="muted">нет данных</span>
              ) : (
                <>
                  <strong>{c.percent}%</strong>
                  <span className="muted small">
                    {" "}
                    {c.earned} из {c.max}
                  </span>
                </>
              )}
            </span>
          </div>
          <div className={`competency-track ${c.percent === null ? "is-empty" : ""}`} aria-hidden="true">
            {c.percent !== null && <div style={{ width: `${c.percent}%` }} />}
          </div>
          {c.description && <p className="muted small">{c.description}</p>}
        </li>
      ))}
    </ul>
  );
}

export function RecommendationCard({
  rec,
  onStart,
  busy,
}: {
  rec: Recommendation;
  onStart: (scenarioId: string) => void;
  busy: boolean;
}) {
  return (
    <section className="card recommendation" aria-labelledby="rec-title">
      <span className="badge badge-teal">Рекомендуемая тренировка</span>
      <h2 id="rec-title">{rec.title}</h2>
      <p>
        <span className="muted">Почему: </span>
        {rec.reason}
      </p>
      {rec.goal && <p className="goal">{rec.goal}</p>}
      <button type="button" className="btn btn-primary" disabled={busy} onClick={() => onStart(rec.scenario_id)}>
        {busy ? "Запуск…" : rec.kind === "replay" ? "Пройти ещё раз" : "Начать тренировку"}
      </button>
    </section>
  );
}

export function AchievementGrid({ items }: { items: AchievementState[] }) {
  return (
    <ul className="achievements">
      {items.map((a) => (
        <li key={a.id} className={`achievement ${a.earned ? "is-earned" : "is-locked"}`}>
          <span className="achievement-icon" aria-hidden="true">
            {a.earned ? "★" : "☆"}
          </span>
          <div>
            <p className="achievement-title">{a.title}</p>
            <p className="muted small">{a.description}</p>
            <p className="small">{a.earned && a.awarded_at ? `Получено ${formatDateTime(a.awarded_at)}` : "Ещё не получено"}</p>
          </div>
        </li>
      ))}
    </ul>
  );
}
