import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { ErrorBoundary } from "./ErrorBoundary";
import { NotificationsBell } from "./NotificationsBell";

export function Layout() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  return (
    <div className="app">
      <a className="skip-link" href="#main">
        К содержимому
      </a>
      <header className="app-header">
        <div className="container header-row">
          <NavLink to="/" className="brand" aria-label="Рейс 400 — на главную">
            <span className="brand-mark" aria-hidden="true" />
            Рейс 400
          </NavLink>
          <nav className="main-nav" aria-label="Основная навигация">
            <NavLink to="/" end>
              Главная
            </NavLink>
            <NavLink to="/scenarios">Сценарии</NavLink>
            <NavLink to="/profile">Профиль</NavLink>
            <NavLink to="/leaderboard">Рейтинг</NavLink>
            {user?.role === "methodologist" && <NavLink to="/editor">Редактор</NavLink>}
          </nav>
          {user && (
            <div className="user-box">
              <NotificationsBell />
              <span className="user-name">
                {user.full_name}
                <span className="role-tag">{user.role === "methodologist" ? "методист" : "проводник"}</span>
              </span>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  void signOut().finally(() => navigate("/login"));
                }}
              >
                Выйти
              </button>
            </div>
          )}
        </div>
      </header>
      <main id="main" className="container main">
        <ErrorBoundary key={location.pathname}>
          <Outlet />
        </ErrorBoundary>
      </main>
      <footer className="app-footer container">
        Учебный тренажёр. Сценарии и люди вымышлены; объяснения — методические, а не официальный регламент ВСМ.
      </footer>
    </div>
  );
}
