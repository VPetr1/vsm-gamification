import { api } from "./client";
import type {
  AttemptResult,
  AttemptState,
  DemoAccount,
  HistoryItem,
  Leaderboard,
  Me,
  Notifications,
  Profile,
  ScenarioSummary,
} from "./types";

export const demoAccounts = () => api<DemoAccount[]>("/auth/demo-accounts");

export const signIn = (login: string, password: string) =>
  api<Me>("/auth/login", { method: "POST", body: { login, password } });

export const signOut = () => api<void>("/auth/logout", { method: "POST" });

export const me = () => api<Me>("/auth/me");

export const listScenarios = () => api<ScenarioSummary[]>("/scenarios");

export const startAttempt = (scenarioId: string) =>
  api<AttemptState>("/attempts", { method: "POST", body: { scenario_id: scenarioId } });

export const getAttempt = (attemptId: string) => api<AttemptState>(`/attempts/${encodeURIComponent(attemptId)}`);

export const submitChoice = (attemptId: string, choiceId: string | null, expectedStep: number) =>
  api<AttemptState>(`/attempts/${encodeURIComponent(attemptId)}/choice`, {
    method: "POST",
    body: { choice_id: choiceId, expected_step: expectedStep },
  });

export const getResult = (attemptId: string) => api<AttemptResult>(`/attempts/${encodeURIComponent(attemptId)}/result`);

export const getProfile = () => api<Profile>("/me/profile");

export const getHistory = () => api<HistoryItem[]>("/me/attempts");

export const getLeaderboard = (scope: Leaderboard["scope"]) => api<Leaderboard>(`/leaderboard?scope=${scope}`);

export const getNotifications = () => api<Notifications>("/me/notifications");

export const markNotificationRead = (id: string) =>
  api<void>(`/me/notifications/${encodeURIComponent(id)}/read`, { method: "POST" });

export const markAllNotificationsRead = () => api<void>("/me/notifications/read-all", { method: "POST" });
