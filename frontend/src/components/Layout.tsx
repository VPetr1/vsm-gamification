import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useSession } from "../auth/Session";

export function Layout() {
  const { user, signOut } = useSession();
  const navigate = useNavigate();
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
          </nav>
          {user && (
            <div className="user-box">
              <span className="user-name">{user.full_name}</span>
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => {
                  signOut();
                  navigate("/login");
                }}
              >
                Выйти
              </button>
            </div>
          )}
        </div>
      </header>
      <main id="main" className="container main">
        <Outlet />
      </main>
      <footer className="app-footer container">
        Учебный тренажёр. Сценарии и люди вымышлены; объяснения — методические, а не официальный регламент ВСМ.
      </footer>
    </div>
  );
}
