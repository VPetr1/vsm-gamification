import { Link } from "react-router-dom";
import { useSession } from "../auth/Session";

export function HomePage() {
  const { user } = useSession();
  return (
    <section className="stack">
      <h1>Здравствуйте, {user?.full_name}</h1>
      <p className="lead">Выберите рабочую ситуацию и примите решения: у критических шагов есть таймер.</p>
      <Link to="/scenarios" className="btn btn-primary btn-large">
        К сценариям
      </Link>
    </section>
  );
}
