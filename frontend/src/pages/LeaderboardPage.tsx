import { useState } from "react";
import { getLeaderboard } from "../api/endpoints";
import type { Leaderboard } from "../api/types";
import { Empty, ErrorState, Loading } from "../components/States";
import { useApi } from "../hooks/useApi";

const SCOPES: { id: Leaderboard["scope"]; label: string }[] = [
  { id: "brigade", label: "Бригада" },
  { id: "depot", label: "Депо" },
  { id: "company", label: "Компания" },
];

export function LeaderboardPage() {
  const [scope, setScope] = useState<Leaderboard["scope"]>("brigade");
  const board = useApi(() => getLeaderboard(scope), scope);

  return (
    <div className="stack">
      <h1>Рейтинг проводников</h1>
      <p className="lead">
        Место определяется опытом — суммой лучших результатов по сценариям. Повтор одного и того же рейса опыт не
        добавляет.
      </p>
      <div className="segmented" role="tablist" aria-label="Уровень рейтинга">
        {SCOPES.map((s) => (
          <button
            key={s.id}
            type="button"
            role="tab"
            aria-selected={scope === s.id}
            className={scope === s.id ? "is-active" : ""}
            onClick={() => setScope(s.id)}
          >
            {s.label}
          </button>
        ))}
      </div>
      {board.error && <ErrorState message={board.error.message} onRetry={board.reload} />}
      {!board.data && !board.error && <Loading />}
      {board.data && (
        <section className="card" aria-live="polite">
          <p className="muted">{board.data.scope_label}</p>
          {board.data.entries.length === 0 ? (
            <Empty title="В этом рейтинге пока никого нет" />
          ) : (
            <div className="table-wrap">
              <table className="table leaderboard">
                <thead>
                  <tr>
                    <th scope="col">Место</th>
                    <th scope="col">Проводник</th>
                    <th scope="col">Бригада, депо</th>
                    <th scope="col">Уровень</th>
                    <th scope="col">Опыт</th>
                    <th scope="col">Сценариев</th>
                  </tr>
                </thead>
                <tbody>
                  {board.data.entries.map((e) => (
                    <tr key={`${e.rank}-${e.name}`} className={e.is_me ? "is-me" : undefined}>
                      <td>
                        <span className={`rank rank-${e.rank <= 3 ? e.rank : "n"}`}>{e.rank}</span>
                      </td>
                      <td>
                        {e.name}
                        {e.is_me && <span className="chip chip-good">вы</span>}
                        {e.synthetic && (
                          <span className="chip" title="Результаты сгенерированы для демонстрации">
                            синтетические данные
                          </span>
                        )}
                      </td>
                      <td className="small">{[e.brigade, e.depot].filter(Boolean).join(", ")}</td>
                      <td>
                        {e.level} · {e.level_title}
                      </td>
                      <td>
                        <strong>{e.xp}</strong>
                      </td>
                      <td>{e.completed}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}
    </div>
  );
}
