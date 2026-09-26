import { Link } from "react-router-dom";
import { getHistory, getProfile } from "../api/endpoints";
import { AchievementGrid, CompetencyList, LevelBar, RecommendationCard } from "../components/Progress";
import { Empty, ErrorState, Loading } from "../components/States";
import { useApi } from "../hooks/useApi";
import { useStartScenario } from "../hooks/useStartScenario";
import { OUTCOME_LABEL } from "../utils/labels";
import { formatDateTime } from "../utils/time";

export function ProfilePage() {
  const profile = useApi(getProfile, "profile");
  const history = useApi(getHistory, "history");
  const { start, starting, error: startError } = useStartScenario();

  if (profile.error) return <ErrorState message={profile.error.message} onRetry={profile.reload} />;
  if (!profile.data) return <Loading />;
  const p = profile.data;

  return (
    <div className="stack">
      <header>
        <p className="muted">
          {p.brigade ? `${p.brigade} · ` : ""}
          {p.depot}
        </p>
        <h1>{p.full_name}</h1>
      </header>

      <section className="card">
        <LevelBar xp={p.xp} level={p.level} />
      </section>

      <div className="home-grid">
        <section className="card">
          <h2>Оценки компетенций</h2>
          <p className="muted small">
            Считается по последнему завершённому прохождению каждого сценария: набранные баллы из максимально
            доступных. Повторное прохождение заменяет прежний результат, а не добавляет к нему.
          </p>
          <CompetencyList items={p.competencies} weakestId={p.weakest?.id} />
          {p.weakest ? (
            <p>
              Слабая оценённая компетенция: <strong>{p.weakest.title}</strong> ({p.weakest.percent}%).
            </p>
          ) : p.competencies.some((c) => c.percent !== null) ? (
            <p className="muted">Все оценённые решения приняты верно — слабых компетенций нет.</p>
          ) : (
            <p className="muted">Оценок пока нет — завершите первый сценарий.</p>
          )}
        </section>
        <div className="stack">
          {startError && <ErrorState message={startError} />}
          {p.recommendation && (
            <RecommendationCard rec={p.recommendation} onStart={(id) => void start(id)} busy={starting !== null} />
          )}
          <section className="card">
            <h2>Достижения</h2>
            <AchievementGrid items={p.achievements} />
          </section>
        </div>
      </div>

      <section className="card">
        <h2>История рейсов</h2>
        {history.error && <ErrorState message={history.error.message} onRetry={history.reload} />}
        {!history.data && !history.error && <Loading />}
        {history.data && history.data.length === 0 && <Empty title="Вы ещё не проходили сценарии" />}
        {history.data && history.data.length > 0 && (
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Сценарий</th>
                  <th scope="col">Дата</th>
                  <th scope="col">Итог</th>
                  <th scope="col">Результат</th>
                  <th scope="col">Опыт</th>
                  <th scope="col">Компетенции</th>
                </tr>
              </thead>
              <tbody>
                {history.data.map((h) => (
                  <tr key={h.attempt_id}>
                    <td>
                      {h.scenario_title} <span className="muted small">в.{h.scenario_version}</span>
                    </td>
                    <td>{formatDateTime(h.finished_at ?? h.started_at)}</td>
                    <td>
                      {h.status === "in_progress" ? (
                        <Link to={`/attempts/${h.attempt_id}`}>Продолжить</Link>
                      ) : (
                        <Link to={`/attempts/${h.attempt_id}/result`}>
                          {h.outcome ? OUTCOME_LABEL[h.outcome] ?? h.outcome : "Разбор"}
                        </Link>
                      )}
                    </td>
                    <td>{h.score ?? "—"}</td>
                    <td>{h.xp_gained === null ? "—" : `+${h.xp_gained}`}</td>
                    <td className="small">
                      {h.competencies.length === 0
                        ? "—"
                        : h.competencies.map((c) => `${c.title}: ${c.earned}/${c.max}`).join(", ")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
