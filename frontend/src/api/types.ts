export type Role = "conductor" | "methodologist";

export type Me = {
  id: string;
  login: string | null;
  full_name: string;
  role: Role;
  brigade: string;
  depot: string;
};

export type DemoAccount = {
  login: string;
  full_name: string;
  role: Role;
  brigade: string;
  depot: string;
};

export type ScenarioSummary = {
  id: string;
  title: string;
  description: string;
  tags: string[];
  version: number;
  my_best_score: number | null;
  in_progress_attempt_id: string | null;
};

export type CompetencyScore = {
  id: string;
  title: string;
  description?: string;
  earned: number;
  max: number;
  percent: number | null;
};

export type Level = { number: number; title: string; min_xp: number; next_min_xp: number | null };

export type AchievementState = {
  id: string;
  title: string;
  description: string;
  earned: boolean;
  awarded_at: string | null;
  attempt_id: string | null;
};

export type Recommendation = {
  scenario_id: string;
  title: string;
  kind: "start" | "weak_new" | "new" | "replay";
  reason: string;
  goal: string | null;
};

export type Profile = {
  full_name: string;
  role: Role;
  brigade: string;
  depot: string;
  xp: number;
  level: Level;
  achievements: AchievementState[];
  stats: { finished_attempts: number; scenarios_completed: number; scenarios_published: number };
  competencies: CompetencyScore[];
  weakest: { id: string; title: string; percent: number } | null;
  recommendation: Recommendation | null;
  aggregation: string;
};

export type HistoryItem = {
  attempt_id: string;
  scenario_id: string;
  scenario_title: string;
  scenario_version: number;
  status: "in_progress" | "finished";
  started_at: string;
  finished_at: string | null;
  score: number | null;
  xp_gained: number | null;
  outcome: string | null;
  synthetic: boolean;
  competencies: CompetencyScore[];
};

export type LeaderboardEntry = {
  rank: number;
  name: string;
  brigade: string;
  depot: string;
  level: number;
  level_title: string;
  xp: number;
  completed: number;
  is_me: boolean;
  synthetic: boolean;
};

export type Leaderboard = { scope: "brigade" | "depot" | "company"; scope_label: string; entries: LeaderboardEntry[] };

export type NotificationItem = {
  id: string;
  kind: string;
  title: string;
  body: string;
  link: string | null;
  created_at: string;
  read: boolean;
};

export type Notifications = { unread: number; items: NotificationItem[] };

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
  assessment: { id: string; title: string; earned: number; max: number }[];
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
  competencies: CompetencyScore[];
  reward: { score: number; xp_gained: number; best_score: number; achievements: { id: string; title: string }[] } | null;
};
