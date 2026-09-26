import type { ReactNode } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./auth/AuthContext";
import { Layout } from "./components/Layout";
import { CatalogPage } from "./pages/CatalogPage";
import { EditorListPage } from "./pages/EditorListPage";
import { EditorPage } from "./pages/EditorPage";
import { HomePage } from "./pages/HomePage";
import { LeaderboardPage } from "./pages/LeaderboardPage";
import { LoginPage } from "./pages/LoginPage";
import { PlayPage } from "./pages/PlayPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ResultPage } from "./pages/ResultPage";
import { Loading } from "./components/States";

function RequireUser({ children }: { children: ReactNode }) {
  const { user, checking } = useAuth();
  const location = useLocation();
  if (checking) return <Loading label="Проверяем вход…" />;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return <>{children}</>;
}

function RequireRole({ role, children }: { role: "methodologist"; children: ReactNode }) {
  const { user } = useAuth();
  if (user?.role !== role) {
    return (
      <section className="stack">
        <h1>Нет доступа</h1>
        <p className="lead">Раздел доступен только методисту.</p>
        <Link to="/" className="btn btn-secondary">
          На главную
        </Link>
      </section>
    );
  }
  return <>{children}</>;
}

function NotFound() {
  return (
    <section className="stack">
      <h1>Страница не найдена</h1>
      <Link to="/" className="btn btn-secondary">
        На главную
      </Link>
    </section>
  );
}

export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            element={
              <RequireUser>
                <Layout />
              </RequireUser>
            }
          >
            <Route index element={<HomePage />} />
            <Route path="scenarios" element={<CatalogPage />} />
            <Route path="attempts/:attemptId" element={<PlayPage />} />
            <Route path="attempts/:attemptId/result" element={<ResultPage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="leaderboard" element={<LeaderboardPage />} />
            <Route
              path="editor"
              element={
                <RequireRole role="methodologist">
                  <EditorListPage />
                </RequireRole>
              }
            />
            <Route
              path="editor/:scenarioId"
              element={
                <RequireRole role="methodologist">
                  <EditorPage />
                </RequireRole>
              }
            />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
