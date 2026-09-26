export type Employee = {
  id: string;
  full_name: string;
  depot: string;
  brigade: string;
};

export type ScenarioSummary = {
  id: string;
  title: string;
  description: string;
  version: number;
};

export type Choice = { id: string; text: string };

export type VisualCharacter = {
  id: string;
  name: string;
  figure: string;
  pose: "sitting" | "standing";
  position: "left" | "center" | "right";
  mood: "happy" | "calm" | "worried" | "upset" | "angry" | "scared";
};

export type NodeVisual = {
  speaker: string | null;
  characters: VisualCharacter[];
  props: string[];
};

export type NodeView = {
  node_id: string;
  text: string;
  timer_seconds: number | null;
  choices: Choice[];
  is_ending: boolean;
  ending_summary: string | null;
  visual?: NodeVisual | null;
};

export type LastStep = {
  step: number;
  node_id: string;
  choice_id: string | null;
  timed_out: boolean;
  loyalty_delta: number;
  safety_delta: number;
};

export type AttemptState = {
  attempt_id: string;
  scenario_id: string;
  scenario_title: string;
  scenario_version: number;
  loyalty: number;
  safety: number;
  status: "in_progress" | "finished";
  step: number;
  node: NodeView;
  node_shown_at: string;
  deadline: string | null;
  server_time: string;
  last_step: LastStep | null;
};

export type ResultStep = {
  step: number;
  node_id: string;
  situation: string;
  choice_id: string | null;
  choice_text: string | null;
  timed_out: boolean;
  loyalty_delta: number;
  safety_delta: number;
  loyalty_after: number | null;
  safety_after: number | null;
  explanation: string | null;
  lesson: string | null;
};

export type Scales = { loyalty: number; safety: number };

export type AttemptResult = {
  attempt_id: string;
  scenario_id: string;
  scenario_title: string;
  scenario_version: number;
  status: string;
  started_at: string;
  finished_at: string;
  initial: Scales;
  final: Scales;
  ending: { node_id: string; text: string; summary: string; outcome: string | null };
  steps: ResultStep[];
};
