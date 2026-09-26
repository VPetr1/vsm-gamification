import { useCallback, useEffect } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ScaleBar } from "../components/ScaleBar";
import { ErrorState, Loading } from "../components/States";
import { useAttemptPlay } from "../hooks/useAttemptPlay";
import { CarriageScene } from "../scene/CarriageScene";
import { sceneFromState } from "../scene/fromState";
import { formatSeconds, signed } from "../utils/time";

export function PlayPage() {
  const { attemptId = "" } = useParams();
  const navigate = useNavigate();
  const onUnauthorized = useCallback(() => navigate("/login", { replace: true }), [navigate]);
  const play = useAttemptPlay(attemptId, onUnauthorized);
  const { state, pending, choose } = play;

  useEffect(() => {
    if (!state || state.status !== "in_progress") return;
    const onKey = (event: KeyboardEvent) => {
      if (event.altKey || event.ctrlKey || event.metaKey || pending) return;
      const target = event.target as HTMLElement | null;
      if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;
      const index = Number(event.key) - 1;
      const choice = state.node.choices[index];
      if (choice) {
        event.preventDefault();
        choose(choice.id);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [state, pending, choose]);

  if (play.loadError) {
    const message = play.loadError.status === 404 ? "Попытка не найдена или недоступна." : play.loadError.message;
    return (
      <div className="stack">
        <ErrorState message={message} onRetry={play.loadError.status === 404 ? undefined : play.retry} />
        <Link to="/scenarios" className="btn btn-secondary">
          К сценариям
        </Link>
      </div>
    );
  }
  if (!state) return <Loading label="Загружаем рейс…" />;

  const last = state.last_step;
  const finished = state.status === "finished";
  const timer = play.remainingMs;
  const timerLevel = timer === null ? "" : timer <= 5000 ? "timer-critical" : "timer-warn";
  const scene = sceneFromState(state);

  return (
    <div className="play">
      <div className="play-top">
        <div className="play-title">
          <span className="muted">Рейс 400 · шаг {state.step + (finished ? 0 : 1)}</span>
          <h1>{state.scenario_title}</h1>
        </div>
        <div className="scales">
          <ScaleBar
            kind="loyalty"
            label="Лояльность пассажиров"
            value={state.loyalty}
            delta={last?.loyalty_delta}
            animateKey={play.animateKey}
          />
          <ScaleBar
            kind="safety"
            label="Рейтинг безопасности"
            value={state.safety}
            delta={last?.safety_delta}
            animateKey={play.animateKey}
          />
        </div>
      </div>

      <div className="scene-wrap">
        <CarriageScene scene={scene} label={`Сцена в вагоне: ${state.node.text}`} />
        {timer !== null && (
          <div className={`timer ${timerLevel}`} role="timer" aria-live="off">
            <span className="timer-label">Критическое решение</span>
            <span className="timer-value">{formatSeconds(timer)} с</span>
          </div>
        )}
      </div>

      {last && (
        <p className={`reaction ${last.timed_out ? "reaction-timeout" : ""}`} aria-live="polite" key={play.animateKey}>
          {last.timed_out ? "Время вышло — ситуация развивалась без вашего решения." : "Решение принято."}{" "}
          <span className="muted">
            Лояльность {signed(last.loyalty_delta)}, безопасность {signed(last.safety_delta)}.
          </span>
        </p>
      )}

      {play.notice && (
        <div className="notice" role="alert">
          <span>{play.notice.text}</span>
          {play.notice.retry && (
            <button type="button" className="btn btn-secondary" onClick={play.retry}>
              Обновить состояние
            </button>
          )}
          <button type="button" className="btn btn-ghost" aria-label="Скрыть сообщение" onClick={play.dismissNotice}>
            ×
          </button>
        </div>
      )}

      <article className="dialog-card" aria-live="polite">
        {scene.characters.find((c) => c.speaking) && (
          <p className="speaker">{scene.characters.find((c) => c.speaking)?.name}</p>
        )}
        <p className="dialog-text">{state.node.text}</p>
      </article>

      {finished ? (
        <section className="ending card">
          <h2>Рейс завершён</h2>
          <p>{state.node.ending_summary}</p>
          <Link className="btn btn-primary btn-large" to={`/attempts/${state.attempt_id}/result`}>
            Разбор решений
          </Link>
        </section>
      ) : (
        <ol className="choices" aria-label="Варианты действий">
          {state.node.choices.map((choice, index) => (
            <li key={choice.id}>
              <button
                type="button"
                className="choice"
                disabled={pending}
                aria-busy={pending}
                onClick={() => choose(choice.id)}
              >
                <span className="choice-key" aria-hidden="true">
                  {index + 1}
                </span>
                <span>{choice.text}</span>
              </button>
            </li>
          ))}
        </ol>
      )}
      {pending && <p className="muted pending-note">Отправляем решение…</p>}
    </div>
  );
}
