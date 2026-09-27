import type { AttemptState } from "../api/types";
import type { SceneModel } from "./types";

/** Visual metadata is optional; a scenario without it gets an empty but valid carriage. */
export function sceneFromState(state: AttemptState): SceneModel {
  const visual = state.node.visual;
  if (!visual) return { background: "standard", characters: [], props: [] };
  return {
    background: visual.background ?? "standard",
    characters: visual.characters.map((c) => ({ ...c, speaking: c.id === visual.speaker })),
    props: visual.props,
  };
}
