import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { listScenarios, startAttempt } from "../api/endpoints";
import type { ScenarioSummary } from "../api/types";
import { useSession } from "../auth/Session";
import { Empty, ErrorState, Loading } from "../components/States";

export function CatalogPage() {
  const { user } = useSession();
  const navigate = useNavigate();
  const [scenarios, setScenarios] = useState<ScenarioSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [starting, setStarting] = useState<string | null>(null);

  const load = () => {
    setError(null);
    listScenarios()
      .then(setScenarios)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : "Не удалось загрузить сценарии"));
  };
  useEffect(load, []);

  const start = async (scenarioId: string) => {
    if (!user || starting) return;
    setStarting(scenarioId);
    setError(null);
    try {
      const state = await startAttempt(user.id, scenarioId);
      navigate(`/attempts/${state.attempt_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось начать сценарий");
      setStarting(null);
    }
  };

  return (
    <section>
      <h1>Сценарии</h1>
      <p className="lead">Рабочие ситуации проводника ВСМ. Решения меняют лояльность пассажиров и безопасность рейса.</p>
      {error && <ErrorState message={error} onRetry={load} />}
      {!scenarios && !error && <Loading />}
      {scenarios && scenarios.length === 0 && <Empty title="Опубликованных сценариев пока нет" />}
      {scenarios && scenarios.length > 0 && (
        <ul className="card-grid">
          {scenarios.map((s) => (
            <li key={s.id} className="card scenario-card">
              <h2>{s.title}</h2>
              <p>{s.description}</p>
              <div className="card-footer">
                <span className="muted">Версия {s.version}</span>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={starting !== null}
                  onClick={() => void start(s.id)}
                >
                  {starting === s.id ? "Запуск…" : "Начать"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
