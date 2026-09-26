import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { listEmployees } from "../api/endpoints";
import type { Employee } from "../api/types";
import { useSession } from "../auth/Session";
import { Empty, ErrorState, Loading } from "../components/States";

export function LoginPage() {
  const { signIn } = useSession();
  const navigate = useNavigate();
  const [employees, setEmployees] = useState<Employee[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = () => {
    setError(null);
    listEmployees()
      .then(setEmployees)
      .catch((err: unknown) => setError(err instanceof ApiError ? err.message : "Не удалось загрузить профили"));
  };
  useEffect(load, []);

  return (
    <div className="login">
      <h1>Рейс 400</h1>
      <p className="lead">Тренажёр проводника ВСМ. Выберите демонстрационный профиль.</p>
      {error && <ErrorState message={error} onRetry={load} />}
      {!error && !employees && <Loading />}
      {employees && employees.length === 0 && <Empty title="Демо-профилей пока нет" />}
      {employees && employees.length > 0 && (
        <ul className="profile-grid">
          {employees.map((e) => (
            <li key={e.id}>
              <button
                type="button"
                className="profile-card"
                onClick={() => {
                  signIn(e);
                  navigate("/");
                }}
              >
                <span className="avatar" aria-hidden="true">
                  {e.full_name.slice(0, 1)}
                </span>
                <span className="profile-name">{e.full_name}</span>
                <span className="muted">{[e.brigade, e.depot].filter(Boolean).join(" · ")}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
