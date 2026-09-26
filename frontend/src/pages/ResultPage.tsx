import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { getResult, startAttempt } from "../api/endpoints";
import type { AttemptResult } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { ErrorState, Loading } from "../components/States";
import { CompetencyList } from "../components/Progress";
import { OUTCOME_LABEL } from "../utils/labels";
import { formatDateTime, signed } from "../utils/time";


function Delta({ label, value }: { label: string; value: number }) {
  if (value === 0) return <span className="chip">{label}: 0</span>;
  return <span className={`chip ${value > 0 ? "chip-good" : "chip-bad"}`}>{`${label}: ${signed(value)}`}</span>;
}

export function ResultPage() {
  const { attemptId = "" } = useParams();
  const navigate = useNavigate();
  const { sessionLost } = useAuth();
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [error, setError] = useState<ApiError | null>(null);
  const [restarting, setRestarting] = useState(false);

  const load = () => {
    setError(null);
    getResult(attemptId)
      .then(setResult)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) sessionLost();
        else if (err instanceof ApiError && err.code === "attempt_not_finished") navigate(`/attempts/${attemptId}`, { replace: true });
        else setError(err instanceof ApiError ? err : new ApiError(0, "unknown", "Не удалось загрузить разбор"));
      });
  };
  useEffect(load, [attemptId]);

  const replay = async () => {
    if (!result) return;
    setRestarting(true);
    try {
      const state = await startAttempt(result.scenario_id);
      navigate(`/attempts/${state.attempt_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err : null);
      setRestarting(false);
    }
  };

  if (error) return <ErrorState message={error.message} onRetry={load} />;
  if (!result) return <Loading label="Готовим разбор…" />;

  return (
    <div className="result stack">
      <header className="result-head">
        <span className="muted">
          {result.scenario_title} · версия {result.scenario_version} · {formatDateTime(result.finished_at)}
        </span>
        <h1>Разбор рейса</h1>
      </header>

      <section className={`card ending-card outcome-${result.ending.outcome ?? "none"}`}>
        {result.ending.outcome && <span className="badge">{OUTCOME_LABEL[result.ending.outcome] ?? result.ending.outcome}</span>}
        <p className="ending-text">{result.ending.text}</p>
        <p>{result.ending.summary}</p>
        <div className="finals">
          <div>
            <span className="muted">Лояльность пассажиров</span>
            <strong>
              {result.initial.loyalty} → {result.final.loyalty}
            </strong>
          </div>
          <div>
            <span className="muted">Рейтинг безопасности</span>
            <strong>
              {result.initial.safety} → {result.final.safety}
            </strong>
          </div>
        </div>
      </section>

      {result.reward && (
        <section className="card reward">
          <h2>Награды</h2>
          <div className="finals">
            <div>
              <span className="muted">Результат рейса</span>
              <strong>{result.reward.score}</strong>
            </div>
            <div>
              <span className="muted">Опыт</span>
              <strong>+{result.reward.xp_gained}</strong>
            </div>
            <div>
              <span className="muted">Лучший результат</span>
              <strong>{result.reward.best_score}</strong>
            </div>
          </div>
          <p className="muted small">
            Результат — среднее двух шкал на финале. Опыт начисляется только за улучшение лучшего результата в этом
            сценарии.
          </p>
          {result.reward.achievements.length > 0 && (
            <div className="chips">
              {result.reward.achievements.map((a) => (
                <span key={a.id} className="chip chip-good">
                  ★ {a.title}
                </span>
              ))}
            </div>
          )}
        </section>
      )}

      <section className="card">
        <h2>Компетенции в этом рейсе</h2>
        <p className="muted small">Набрано из максимально доступного среди вариантов, которые вы видели.</p>
        <CompetencyList items={result.competencies.map((c) => ({ ...c, description: undefined }))} />
      </section>

      <section>
        <h2>Решения и последствия</h2>
        <ol className="timeline">
          {result.steps.map((step) => (
            <li key={step.step} className={`timeline-item ${step.timed_out ? "is-timeout" : ""}`}>
              <p className="muted">Шаг {step.step}</p>
              <p className="situation">{step.situation}</p>
              <p className="decision">
                {step.timed_out ? <strong>Время вышло — решение не принято</strong> : <strong>{step.choice_text}</strong>}
              </p>
              <div className="chips">
                <Delta label="Лояльность" value={step.loyalty_delta} />
                <Delta label="Безопасность" value={step.safety_delta} />
                {step.assessment.map((a) => (
                  <span key={a.id} className={`chip ${a.earned === a.max ? "chip-good" : "chip-warn"}`}>
                    {a.title}: {a.earned}/{a.max}
                  </span>
                ))}
              </div>
              {step.explanation && <p>{step.explanation}</p>}
              {step.lesson && (
                <p className="lesson">
                  <span>Как лучше:</span> {step.lesson}
                </p>
              )}
            </li>
          ))}
        </ol>
      </section>

      <div className="actions">
        <button type="button" className="btn btn-primary" onClick={() => void replay()} disabled={restarting}>
          {restarting ? "Запуск…" : "Пройти ещё раз"}
        </button>
        <Link to="/scenarios" className="btn btn-secondary">
          К сценариям
        </Link>
      </div>
    </div>
  );
}
