import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError } from "../api/client";
import { createEditorScenario, listEditorScenarios } from "../api/editor";
import type { Obj } from "../editor/graphOps";
import { Empty, ErrorState, Loading } from "../components/States";
import { useApi } from "../hooks/useApi";
import { formatDateTime } from "../utils/time";

export function EditorListPage() {
  const list = useApi(listEditorScenarios, "editor-list");
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const create = async (body: { title: string; description?: string; tags?: string[]; graph?: Obj }) => {
    setBusy(true);
    setError(null);
    try {
      const view = await createEditorScenario(body);
      navigate(`/editor/${view.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Не удалось создать сценарий");
      setBusy(false);
    }
  };

  const submit = (e: FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return setError("Введите название.");
    void create({ title: title.trim() });
  };

  const importFile = async (file: File) => {
    try {
      const data = JSON.parse(await file.text()) as { title?: string; description?: string; tags?: string[]; graph?: Obj };
      if (!data.graph || typeof data.graph !== "object") throw new Error("В файле нет поля graph.");
      await create({
        title: data.title?.trim() || file.name.replace(/\.json$/i, ""),
        description: data.description ?? "",
        tags: Array.isArray(data.tags) ? data.tags : [],
        graph: data.graph,
      });
    } catch (err) {
      setError(err instanceof Error ? `Импорт не удался: ${err.message}` : "Импорт не удался");
    }
  };

  return (
    <div className="stack">
      <h1>Редактор сценариев</h1>
      <p className="lead">
        Черновики видит только методист. Публикация создаёт новую версию; уже начатые прохождения продолжают свою.
      </p>
      <section className="card">
        <form className="inline wrap" onSubmit={submit}>
          <label className="field">
            <span>Новый сценарий</span>
            <input value={title} placeholder="Название" onChange={(e) => setTitle(e.target.value)} />
          </label>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            Создать черновик
          </button>
          <label className="btn btn-secondary file-button">
            Импорт JSON
            <input
              type="file"
              accept="application/json,.json"
              className="sr-only"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void importFile(file);
                e.target.value = "";
              }}
            />
          </label>
        </form>
        {error && (
          <p className="field-error" role="alert">
            {error}
          </p>
        )}
      </section>

      {list.error && <ErrorState message={list.error.message} onRetry={list.reload} />}
      {!list.data && !list.error && <Loading />}
      {list.data && list.data.length === 0 && <Empty title="Сценариев пока нет" />}
      {list.data && list.data.length > 0 && (
        <section className="card">
          <div className="table-wrap">
            <table className="table">
              <thead>
                <tr>
                  <th scope="col">Сценарий</th>
                  <th scope="col">Статус</th>
                  <th scope="col">Изменён</th>
                </tr>
              </thead>
              <tbody>
                {list.data.map((s) => (
                  <tr key={s.id}>
                    <td>
                      <Link to={`/editor/${s.id}`}>{s.title}</Link>
                    </td>
                    <td>
                      {s.published ? <span className="chip chip-good">опубликован, v{s.version}</span> : <span className="chip">черновик</span>}
                      {s.published && s.has_unpublished_changes && <span className="chip chip-warn">есть неопубликованные правки</span>}
                    </td>
                    <td className="small">{s.updated_at ? formatDateTime(s.updated_at) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </div>
  );
}
