import type { ReactNode } from "react";
import { BrowserRouter, Link, Navigate, Route, Routes, useLocation } from "react-router-dom";
import { SessionProvider, useSession } from "./auth/Session";
import { Layout } from "./components/Layout";
import { CatalogPage } from "./pages/CatalogPage";
import { HomePage } from "./pages/HomePage";
import { LoginPage } from "./pages/LoginPage";
import { PlayPage } from "./pages/PlayPage";
import { ResultPage } from "./pages/ResultPage";

function RequireUser({ children }: { children: ReactNode }) {
  const { user } = useSession();
  const location = useLocation();
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
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
    <SessionProvider>
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
            <Route path="*" element={<NotFound />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </SessionProvider>
  );
}
