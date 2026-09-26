import { Link } from "react-router-dom";
import { getHistory, getProfile } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";
import { CompetencyList, LevelBar, RecommendationCard } from "../components/Progress";
import { Empty, ErrorState, Loading } from "../components/States";
import { useApi } from "../hooks/useApi";
import { useStartScenario } from "../hooks/useStartScenario";

export function HomePage() {
  const { user } = useAuth();
  const profile = useApi(getProfile, "profile");
  const history = useApi(getHistory, "history");
  const { start, starting, error: startError } = useStartScenario();

  if (profile.error) return <ErrorState message={profile.error.message} onRetry={profile.reload} />;
  if (!profile.data) return <Loading />;
  const p = profile.data;
  const unfinished = (history.data ?? []).filter((h) => h.status === "in_progress");

  return (
    <div className="home">
      <section className="hero card">
        <p className="muted">
          {user?.brigade ? `${user.brigade} · ` : ""}
          {user?.depot}
        </p>
        <h1>Здравствуйте, {p.full_name}</h1>
        <LevelBar xp={p.xp} level={p.level} />
        <p className="muted small">
          Пройдено сценариев: {p.stats.scenarios_completed} из {p.stats.scenarios_published} · рейсов завершено:{" "}
          {p.stats.finished_attempts} · достижений: {p.achievements.filter((a) => a.earned).length} из {p.achievements.length}
        </p>
      </section>

      {startError && <ErrorState message={startError} />}

      <div className="home-grid">
        {p.recommendation ? (
          <RecommendationCard rec={p.recommendation} onStart={(id) => void start(id)} busy={starting !== null} />
        ) : (
          <Empty title="Опубликованных сценариев пока нет">
            <p>Методист может опубликовать сценарий в редакторе.</p>
          </Empty>
        )}

        <section className="card">
          <h2>Компетенции</h2>
          <CompetencyList items={p.competencies} weakestId={p.weakest?.id} />
          <Link to="/profile" className="btn btn-secondary">
            Профиль и история
          </Link>
        </section>
      </div>

      {unfinished.length > 0 && (
        <section className="card">
          <h2>Незавершённые рейсы</h2>
          <ul className="plain-list">
            {unfinished.map((h) => (
              <li key={h.attempt_id}>
                <Link to={`/attempts/${h.attempt_id}`}>{h.scenario_title}</Link>
                <span className="muted small"> — продолжить с места остановки</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
