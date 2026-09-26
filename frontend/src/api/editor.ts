import type { Obj } from "../editor/graphOps";
import { api } from "./client";

export type Draft = { title: string; description: string; tags: string[]; graph: Obj };

export type EditorView = {
  id: string;
  key: string | null;
  origin: string;
  version: number;
  published_at: string | null;
  updated_at: string | null;
  published: Draft | null;
  draft: Draft;
  has_unpublished_changes: boolean;
  errors: string[];
};

export type EditorItem = {
  id: string;
  title: string;
  version: number;
  published: boolean;
  has_unpublished_changes: boolean;
  origin: string;
  updated_at: string | null;
};

const path = (id: string) => `/editor/scenarios/${encodeURIComponent(id)}`;

export const listEditorScenarios = () => api<EditorItem[]>("/editor/scenarios");

export const createEditorScenario = (body: { title: string; description?: string; tags?: string[]; graph?: Obj }) =>
  api<EditorView>("/editor/scenarios", { method: "POST", body });

export const getEditorScenario = (id: string) => api<EditorView>(path(id));

export const saveDraft = (id: string, draft: Draft) => api<EditorView>(`${path(id)}/draft`, { method: "PUT", body: draft });

export const discardDraft = (id: string) => api<EditorView>(`${path(id)}/draft`, { method: "DELETE" });

export const publishScenario = (id: string) => api<EditorView>(`${path(id)}/publish`, { method: "POST" });
