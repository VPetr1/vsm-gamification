import { listScenarios } from "../api/endpoints";
import { Empty, ErrorState, Loading } from "../components/States";
import { useApi } from "../hooks/useApi";
import { useStartScenario } from "../hooks/useStartScenario";
import { isCompetencyTag, tagLabel } from "../utils/labels";

export function CatalogPage() {
  const scenarios = useApi(listScenarios, "catalog");
  const { start, starting, error } = useStartScenario();

  return (
    <section>
      <h1>Сценарии</h1>
      <p className="lead">Рабочие ситуации проводника ВСМ. Решения меняют лояльность пассажиров и безопасность рейса.</p>
      {error && <ErrorState message={error} />}
      {scenarios.error && <ErrorState message={scenarios.error.message} onRetry={scenarios.reload} />}
      {!scenarios.data && !scenarios.error && <Loading />}
      {scenarios.data && scenarios.data.length === 0 && <Empty title="Опубликованных сценариев пока нет" />}
      {scenarios.data && scenarios.data.length > 0 && (
        <ul className="card-grid">
          {scenarios.data.map((s) => (
            <li key={s.id} className="card scenario-card">
              <h2>{s.title}</h2>
              <div className="chips">
                {s.tags.map((t) => (
                  <span key={t} className={`chip ${isCompetencyTag(t) ? "chip-good" : ""}`}>
                    {tagLabel(t)}
                  </span>
                ))}
              </div>
              <p>{s.description}</p>
              <div className="card-footer">
                <span className="muted small">
                  Версия {s.version}
                  {s.my_best_score !== null && ` · лучший результат ${s.my_best_score}`}
                </span>
                <button
                  type="button"
                  className="btn btn-primary"
                  disabled={starting !== null}
                  onClick={() => void start(s.id, s.in_progress_attempt_id)}
                >
                  {starting === s.id ? "Запуск…" : s.in_progress_attempt_id ? "Продолжить" : s.my_best_score !== null ? "Пройти ещё раз" : "Начать"}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
