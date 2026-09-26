import { useEffect, useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../api/client";
import { discardDraft, getEditorScenario, publishScenario, saveDraft, type Draft, type EditorView } from "../api/editor";
import { useAuth } from "../auth/AuthContext";
import { ErrorState, Loading } from "../components/States";
import { GraphSettings } from "../editor/GraphSettings";
import { errorNodeId, freeId, referencesTo, renameNode, type Obj } from "../editor/graphOps";
import { NodeEditor } from "../editor/NodeEditor";

export function EditorPage() {
  const { scenarioId = "" } = useParams();
  const { sessionLost } = useAuth();
  const [view, setView] = useState<EditorView | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<{ kind: "ok" | "error"; text: string } | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const accept = (v: EditorView) => {
    setView(v);
    setDraft(structuredClone(v.draft));
    setDirty(false);
    setSelected((current) => (current && current in (v.draft.graph.nodes as Obj) ? current : ((v.draft.graph.start_node as string) ?? null)));
  };

  const fail = (err: unknown, fallback: string) => {
    if (err instanceof ApiError && err.status === 401) return sessionLost();
    if (err instanceof ApiError && err.code === "invalid_scenario") {
      setView((v) => (v ? { ...v, errors: (err.detail.errors as string[]) ?? v.errors } : v));
      setMessage({ kind: "error", text: "Публикация невозможна: исправьте ошибки ниже." });
      return;
    }
    setMessage({ kind: "error", text: err instanceof ApiError ? err.message : fallback });
  };

  useEffect(() => {
    getEditorScenario(scenarioId)
      .then(accept)
      .catch((err: unknown) => {
        if (err instanceof ApiError && err.status === 401) sessionLost();
        else setLoadError(err instanceof ApiError ? err.message : "Не удалось открыть сценарий");
      });
  }, [scenarioId, sessionLost]);

  useEffect(() => {
    if (!dirty) return;
    const warn = (e: BeforeUnloadEvent) => e.preventDefault();
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  const graph = draft?.graph;
  const nodes = (graph?.nodes as Obj | undefined) ?? {};
  const nodeIds = Object.keys(nodes);
  const flags = Object.keys((graph?.flags as Obj | undefined) ?? {});
  const characters = Object.keys((((graph?.visual as Obj | undefined)?.characters as Obj) ?? {}) as Obj);
  const errorsByNode = useMemo(() => {
    const map: Record<string, string[]> = {};
    for (const e of view?.errors ?? []) {
      const id = errorNodeId(e) ?? "__graph__";
      (map[id] ??= []).push(e);
    }
    return map;
  }, [view]);

  if (loadError) return <ErrorState message={loadError} />;
  if (!view || !draft || !graph) return <Loading />;

  const change = (next: Draft) => {
    setDraft(next);
    setDirty(true);
    setMessage(null);
  };
  const setGraph = (g: Obj) => change({ ...draft, graph: g });
  const setNode = (id: string, node: Obj) => setGraph({ ...graph, nodes: { ...nodes, [id]: node } });

  const save = async () => {
    setBusy(true);
    try {
      accept(await saveDraft(view.id, draft));
      setMessage({ kind: "ok", text: "Черновик сохранён. Проверка выполнена." });
    } catch (err) {
      fail(err, "Не удалось сохранить");
    } finally {
      setBusy(false);
    }
  };

  const publish = async () => {
    setBusy(true);
    try {
      if (dirty) accept(await saveDraft(view.id, draft));
      const published = await publishScenario(view.id);
      accept(published);
      setMessage({ kind: "ok", text: `Опубликована версия ${published.version}. Начатые прохождения остаются на своей версии.` });
    } catch (err) {
      fail(err, "Не удалось опубликовать");
    } finally {
      setBusy(false);
    }
  };

  const discard = async () => {
    if (!window.confirm("Отменить все неопубликованные правки?")) return;
    setBusy(true);
    try {
      accept(await discardDraft(view.id));
      setMessage({ kind: "ok", text: "Черновик сброшен до опубликованной версии." });
    } catch (err) {
      fail(err, "Не удалось сбросить черновик");
    } finally {
      setBusy(false);
    }
  };

  const exportJson = () => {
    const blob = new Blob([JSON.stringify(draft, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${draft.title || "scenario"}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const importJson = async (file: File) => {
    try {
      const data = JSON.parse(await file.text()) as Partial<Draft>;
      if (!data.graph || typeof data.graph !== "object") throw new Error("в файле нет поля graph");
      change({
        title: data.title ?? draft.title,
        description: data.description ?? draft.description,
        tags: Array.isArray(data.tags) ? data.tags : draft.tags,
        graph: data.graph,
      });
      setSelected((data.graph.start_node as string) ?? null);
      setMessage({ kind: "ok", text: "JSON загружен в черновик. Сохраните, чтобы проверить." });
    } catch (err) {
      setMessage({ kind: "error", text: `Импорт не удался: ${err instanceof Error ? err.message : "ошибка"}` });
    }
  };

  const addNode = () => {
    const id = freeId(nodeIds, "node");
    setGraph({ ...graph, nodes: { ...nodes, [id]: { text: "Новая ситуация", choices: [{ id: "a", text: "Вариант", next_node: id }] } } });
    setSelected(id);
  };

  const deleteNode = (id: string) => {
    const refs = referencesTo(graph, id).filter((r) => r !== id);
    const warning = refs.length ? `На узел ссылаются: ${refs.join(", ")}. Проверка покажет эти ссылки как ошибки. ` : "";
    if (!window.confirm(`${warning}Удалить узел «${id}»?`)) return;
    const next = { ...nodes };
    delete next[id];
    setGraph({ ...graph, nodes: next });
    setSelected((graph.start_node as string) === id ? Object.keys(next)[0] ?? null : (graph.start_node as string));
  };

  const graphErrors = [...(errorsByNode.__graph__ ?? [])];

  return (
    <div className="editor">
      <div className="editor-toolbar card">
        <div>
          <Link to="/editor" className="small">
            ← Все сценарии
          </Link>
          <p className="muted small">
            {view.published ? `Опубликована версия ${view.version}` : "Ещё не опубликован"}
            {view.has_unpublished_changes || dirty ? " · есть неопубликованные правки" : ""}
            {dirty ? " · не сохранено" : ""}
          </p>
        </div>
        <div className="toolbar-actions">
          <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => void save()}>
            Сохранить и проверить
          </button>
          <button type="button" className="btn btn-primary" disabled={busy} onClick={() => void publish()}>
            Опубликовать
          </button>
          <button type="button" className="btn btn-ghost" onClick={exportJson}>
            Экспорт JSON
          </button>
          <label className="btn btn-ghost file-button">
            Импорт JSON
            <input
              type="file"
              accept="application/json,.json"
              className="sr-only"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) void importJson(file);
                e.target.value = "";
              }}
            />
          </label>
          {view.published && view.has_unpublished_changes && (
            <button type="button" className="btn btn-ghost danger" disabled={busy} onClick={() => void discard()}>
              Сбросить черновик
            </button>
          )}
        </div>
      </div>

      {message && (
        <p className={message.kind === "ok" ? "notice notice-ok" : "notice"} role={message.kind === "ok" ? "status" : "alert"}>
          {message.text}
        </p>
      )}

      {view.errors.length > 0 && (
        <section className="card errors-card" aria-labelledby="errors-title">
          <h2 id="errors-title">Проверка: {view.errors.length} ошибок</h2>
          <ul className="error-list">
            {view.errors.map((e) => {
              const node = errorNodeId(e);
              return (
                <li key={e}>
                  {node && node in nodes ? (
                    <button type="button" className="link-button" onClick={() => setSelected(node)}>
                      {e}
                    </button>
                  ) : (
                    e
                  )}
                </li>
              );
            })}
          </ul>
        </section>
      )}
      {view.errors.length === 0 && !dirty && <p className="muted small">Проверка пройдена: ошибок нет.</p>}

      <section className="card">
        <div className="field-row">
          <label className="field wide">
            <span>Название</span>
            <input value={draft.title} onChange={(e) => change({ ...draft, title: e.target.value })} />
          </label>
          <label className="field wide">
            <span>Теги (через запятую; компетенции: communication, safety, first_aid, stress_resistance)</span>
            <input
              value={draft.tags.join(", ")}
              onChange={(e) => change({ ...draft, tags: e.target.value.split(",").map((t) => t.trim()).filter(Boolean) })}
            />
          </label>
        </div>
        <label className="field wide">
          <span>Описание</span>
          <textarea rows={2} value={draft.description} onChange={(e) => change({ ...draft, description: e.target.value })} />
        </label>
        {graphErrors.length > 0 && <p className="field-error small">{graphErrors.length} ошибок уровня сценария — см. список выше.</p>}
      </section>

      <GraphSettings graph={graph} onChange={setGraph} />

      <div className="editor-body">
        <nav className="card node-list" aria-label="Узлы сценария">
          <h2>Узлы</h2>
          <ul>
            {nodeIds.map((id) => {
              const node = nodes[id] as Obj;
              return (
                <li key={id}>
                  <button type="button" className={selected === id ? "is-selected" : ""} aria-current={selected === id} onClick={() => setSelected(id)}>
                    <span>{id}</span>
                    <span className="node-tags">
                      {graph.start_node === id && <span className="chip">старт</span>}
                      {node.is_ending === true && <span className="chip chip-good">финал</span>}
                      {typeof node.timer_seconds === "number" && <span className="chip chip-warn">таймер</span>}
                      {errorsByNode[id] && <span className="chip chip-bad">{errorsByNode[id].length}</span>}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
          <button type="button" className="btn btn-secondary" onClick={addNode}>
            + узел
          </button>
        </nav>

        {selected && nodes[selected] ? (
          <NodeEditor
            key={selected}
            nodeId={selected}
            node={nodes[selected] as Obj}
            nodeIds={nodeIds}
            flags={flags}
            characters={characters}
            errors={errorsByNode[selected] ?? []}
            onChange={(node) => setNode(selected, node)}
            onRename={(to) => {
              if (to in nodes) return "Узел с таким идентификатором уже есть.";
              setGraph(renameNode(graph, selected, to));
              setSelected(to);
              return null;
            }}
            onDelete={() => deleteNode(selected)}
          />
        ) : (
          <p className="muted">Выберите узел слева.</p>
        )}
      </div>
    </div>
  );
}
