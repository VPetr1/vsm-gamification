import { useEffect, useState, type FormEvent } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { demoAccounts } from "../api/endpoints";
import type { DemoAccount } from "../api/types";
import { useAuth } from "../auth/AuthContext";
import { Empty, ErrorState, Loading } from "../components/States";

const ROLE_LABEL = { conductor: "Проводник", methodologist: "Методист" } as const;

export function LoginPage() {
  const { user, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";

  const [accounts, setAccounts] = useState<DemoAccount[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string>("");
  const [password, setPassword] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    setLoadError(null);
    demoAccounts()
      .then(setAccounts)
      .catch((err: unknown) => setLoadError(err instanceof ApiError ? err.message : "Не удалось загрузить профили"));
  };
  useEffect(load, []);

  if (user) return <Navigate to={from} replace />;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!selected) {
      setFormError("Выберите профиль.");
      return;
    }
    if (!password) {
      setFormError("Введите пароль.");
      return;
    }
    setSubmitting(true);
    setFormError(null);
    try {
      await signIn(selected, password);
      navigate(from, { replace: true });
    } catch (err) {
      setFormError(err instanceof ApiError && err.code === "invalid_credentials" ? "Неверный пароль." : err instanceof ApiError ? err.message : "Не удалось войти.");
      setSubmitting(false);
    }
  };

  return (
    <div className="login">
      <h1>Рейс 400</h1>
      <p className="lead">Тренажёр проводника ВСМ. Выберите демонстрационный профиль и войдите.</p>
      {loadError && <ErrorState message={loadError} onRetry={load} />}
      {!loadError && !accounts && <Loading />}
      {accounts && accounts.length === 0 && (
        <Empty title="Демо-профилей нет">
          <p>Запустите заполнение демо-данными: python -m app.seed</p>
        </Empty>
      )}
      {accounts && accounts.length > 0 && (
        <form onSubmit={(e) => void submit(e)} className="stack" noValidate>
          <fieldset className="profile-fieldset">
            <legend className="sr-only">Демо-профиль</legend>
            <ul className="profile-grid">
              {accounts.map((a) => (
                <li key={a.login}>
                  <label className={`profile-card ${selected === a.login ? "is-selected" : ""}`}>
                    <input
                      type="radio"
                      name="login"
                      value={a.login}
                      checked={selected === a.login}
                      onChange={() => {
                        setSelected(a.login);
                        setFormError(null);
                      }}
                      className="sr-only"
                    />
                    <span className="avatar" aria-hidden="true">
                      {a.full_name.slice(0, 1)}
                    </span>
                    <span className="profile-name">{a.full_name}</span>
                    <span className="muted">
                      {ROLE_LABEL[a.role]}
                      {a.brigade ? ` · ${a.brigade}` : ""} · {a.depot}
                    </span>
                  </label>
                </li>
              ))}
            </ul>
          </fieldset>
          <div className="field">
            <label htmlFor="password">Пароль демо-аккаунта</label>
            <input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setFormError(null);
              }}
              aria-invalid={formError ? true : undefined}
              aria-describedby="password-hint"
            />
            <p id="password-hint" className="muted small">
              Пароль общий для всех демо-аккаунтов и задаётся при запуске (см. README).
            </p>
          </div>
          {formError && (
            <p className="field-error" role="alert">
              {formError}
            </p>
          )}
          <button type="submit" className="btn btn-primary btn-large" disabled={submitting}>
            {submitting ? "Входим…" : "Войти"}
          </button>
        </form>
      )}
    </div>
  );
}
